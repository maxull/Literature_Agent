from __future__ import annotations

import html
import re
import time
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from datetime import date, datetime
from typing import Any

import requests

from .models import Paper, SourceFetchResult
from .queries import build_pubmed_query


MONTH_MAP = {
    "jan": 1,
    "feb": 2,
    "mar": 3,
    "apr": 4,
    "may": 5,
    "jun": 6,
    "jul": 7,
    "aug": 8,
    "sep": 9,
    "oct": 10,
    "nov": 11,
    "dec": 12,
}


def _compact_error(exc: Exception) -> str:
    message = str(exc)
    resolve_match = re.search(r"Failed to resolve '[^']+'[^)]+\)", message)
    if resolve_match:
        return resolve_match.group(0)
    message = re.sub(r"with url: [^ )]+", "with url: [omitted]", message)
    message = re.sub(r"(https?://[^\s?]+)\?[^\s)]+", r"\1?...", message)
    if len(message) > 320:
        return message[:317] + "..."
    return message


def _parse_date(value: str | None, fallback_year: int | None = None) -> date:
    if not value:
        year = fallback_year or datetime.utcnow().year
        return date(year, 1, 1)

    value = value.strip()
    try:
        return datetime.strptime(value[:10], "%Y-%m-%d").date()
    except ValueError:
        pass

    match = re.match(r"^(\d{4})", value)
    if match:
        year = int(match.group(1))
        month = 1
        day = 1

        parts = value.replace("/", " ").split()
        if len(parts) >= 2:
            month_key = parts[1][:3].lower()
            month = MONTH_MAP.get(month_key, 1)
        if len(parts) >= 3 and parts[2].isdigit():
            day = max(1, min(28, int(parts[2])))
        return date(year, month, day)

    return date(fallback_year or datetime.utcnow().year, 1, 1)


def _strip_jats_tags(text: str) -> str:
    clean = re.sub(r"<[^>]+>", " ", text)
    clean = html.unescape(clean)
    clean = re.sub(r"\s+", " ", clean)
    return clean.strip()


@dataclass
class HTTPConfig:
    timeout_seconds: int
    retry_attempts: int


class BaseSourceClient:
    source_name = "base"

    def __init__(self, http: HTTPConfig) -> None:
        self.http = http

    def _get(self, url: str, params: dict[str, Any] | None = None) -> requests.Response:
        last_error: Exception | None = None
        for attempt in range(self.http.retry_attempts):
            try:
                response = requests.get(url, params=params, timeout=self.http.timeout_seconds)
                response.raise_for_status()
                return response
            except requests.RequestException as exc:
                last_error = exc
                if attempt + 1 < self.http.retry_attempts:
                    time.sleep(1.2**attempt)
        if last_error:
            raise last_error
        raise RuntimeError("HTTP request failed without captured exception")

    def fetch(self, start_date: date, end_date: date, max_results: int) -> SourceFetchResult:
        raise NotImplementedError


class PubMedClient(BaseSourceClient):
    source_name = "PubMed"
    esearch_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
    efetch_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"

    def fetch(self, start_date: date, end_date: date, max_results: int) -> SourceFetchResult:
        try:
            query = build_pubmed_query()
            search_params = {
                "db": "pubmed",
                "retmode": "json",
                "retmax": str(max_results),
                "sort": "pub date",
                "datetype": "pdat",
                "mindate": start_date.isoformat(),
                "maxdate": end_date.isoformat(),
                "term": query,
            }
            search_response = self._get(self.esearch_url, params=search_params).json()
            id_list = search_response.get("esearchresult", {}).get("idlist", [])
            if not id_list:
                return SourceFetchResult(source_name=self.source_name, papers=[])

            fetch_params = {
                "db": "pubmed",
                "id": ",".join(id_list),
                "retmode": "xml",
            }
            fetch_xml = self._get(self.efetch_url, params=fetch_params).text
            papers = self._parse_pubmed_xml(fetch_xml)
            return SourceFetchResult(source_name=self.source_name, papers=papers)
        except Exception as exc:  # noqa: BLE001
            return SourceFetchResult(source_name=self.source_name, papers=[], failure=_compact_error(exc))

    def _parse_pubmed_xml(self, xml_text: str) -> list[Paper]:
        root = ET.fromstring(xml_text)
        parsed: list[Paper] = []

        for article in root.findall(".//PubmedArticle"):
            pmid = article.findtext(".//PMID")
            title = (article.findtext(".//ArticleTitle") or "Untitled").strip()

            abstract_parts = [
                (node.text or "").strip()
                for node in article.findall(".//Abstract/AbstractText")
                if (node.text or "").strip()
            ]
            abstract = " ".join(abstract_parts)

            authors: list[str] = []
            for author in article.findall(".//Author"):
                lastname = (author.findtext("LastName") or "").strip()
                initials = (author.findtext("Initials") or "").strip()
                collab = (author.findtext("CollectiveName") or "").strip()
                if collab:
                    authors.append(collab)
                elif lastname:
                    joined = f"{lastname} {initials}".strip()
                    authors.append(joined)

            doi = None
            for aid in article.findall(".//ArticleId"):
                if aid.attrib.get("IdType") == "doi" and aid.text:
                    doi = aid.text.strip()
                    break

            journal = (article.findtext(".//Journal/Title") or "PubMed indexed").strip()
            pub_year = article.findtext(".//PubDate/Year")
            medline_date = article.findtext(".//PubDate/MedlineDate")
            pub_month = article.findtext(".//PubDate/Month")
            pub_day = article.findtext(".//PubDate/Day")

            date_str = None
            if pub_year:
                month = (pub_month or "Jan")
                day = (pub_day or "1")
                date_str = f"{pub_year} {month} {day}"
            elif medline_date:
                date_str = medline_date

            parsed_date = _parse_date(date_str)

            pub_types = {
                (node.text or "").strip().lower()
                for node in article.findall(".//PublicationType")
                if node.text
            }
            is_review = "review" in pub_types

            parsed.append(
                Paper(
                    title=title,
                    authors=authors,
                    abstract=abstract,
                    source="PubMed",
                    source_type="peer-reviewed",
                    venue=journal,
                    published_date=parsed_date,
                    year=parsed_date.year,
                    doi=doi,
                    pmid=pmid,
                    url=f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/" if pmid else None,
                    is_review=is_review,
                )
            )

        return parsed


class RxivClient(BaseSourceClient):
    def __init__(self, http: HTTPConfig, server: str) -> None:
        super().__init__(http)
        self.server = server
        self.source_name = server

    def fetch(self, start_date: date, end_date: date, max_results: int) -> SourceFetchResult:
        try:
            papers: list[Paper] = []
            cursor = 0
            while len(papers) < max_results:
                url = (
                    f"https://api.biorxiv.org/details/{self.server}/"
                    f"{start_date.isoformat()}/{end_date.isoformat()}/{cursor}"
                )
                response = self._get(url).json()
                collection = response.get("collection", [])
                if not collection:
                    break

                for item in collection:
                    doi = (item.get("doi") or "").strip() or None
                    title = (item.get("title") or "Untitled").strip()
                    abstract = (item.get("abstract") or "").strip()
                    authors_raw = item.get("authors") or ""
                    authors = [a.strip() for a in re.split(r";|,", authors_raw) if a.strip()]
                    posted_date = _parse_date(item.get("date"))
                    version = str(item.get("version", "")).strip() or None
                    is_review = "review" in title.lower()

                    url = None
                    if doi:
                        host = "www.biorxiv.org" if self.server == "biorxiv" else "www.medrxiv.org"
                        suffix = f"{doi}v{version}" if version else doi
                        url = f"https://{host}/content/{suffix}"

                    papers.append(
                        Paper(
                            title=title,
                            authors=authors,
                            abstract=abstract,
                            source=self.server,
                            source_type="preprint",
                            venue=self.server,
                            published_date=posted_date,
                            year=posted_date.year,
                            doi=doi,
                            preprint_id=doi,
                            url=url,
                            version=version,
                            is_review=is_review,
                        )
                    )

                    if len(papers) >= max_results:
                        break

                cursor += len(collection)
                if len(collection) == 0:
                    break

            return SourceFetchResult(source_name=self.source_name, papers=papers)
        except Exception as exc:  # noqa: BLE001
            return SourceFetchResult(source_name=self.source_name, papers=[], failure=_compact_error(exc))


class SportRxivClient(BaseSourceClient):
    source_name = "sportRxiv"
    api_url = "https://api.crossref.org/works"

    def fetch(self, start_date: date, end_date: date, max_results: int) -> SourceFetchResult:
        try:
            params = {
                "filter": f"from-pub-date:{start_date.isoformat()},until-pub-date:{end_date.isoformat()}",
                "query.container-title": "sportRxiv",
                "rows": str(max_results),
                "sort": "published",
                "order": "desc",
            }
            response = self._get(self.api_url, params=params).json()
            items = response.get("message", {}).get("items", [])
            papers: list[Paper] = []

            for item in items:
                title_list = item.get("title") or []
                title = (title_list[0] if title_list else "Untitled").strip()
                doi = (item.get("DOI") or "").strip() or None
                abstract = _strip_jats_tags(item.get("abstract") or "")

                authors: list[str] = []
                for author in item.get("author", []):
                    given = (author.get("given") or "").strip()
                    family = (author.get("family") or "").strip()
                    name = f"{given} {family}".strip()
                    if name:
                        authors.append(name)

                date_parts = (
                    item.get("published-print", {}).get("date-parts")
                    or item.get("published-online", {}).get("date-parts")
                    or [[datetime.utcnow().year, 1, 1]]
                )
                year, month, day = (date_parts[0] + [1, 1, 1])[:3]
                posted_date = date(int(year), int(month), int(day))

                papers.append(
                    Paper(
                        title=title,
                        authors=authors,
                        abstract=abstract,
                        source=self.source_name,
                        source_type="preprint",
                        venue=self.source_name,
                        published_date=posted_date,
                        year=posted_date.year,
                        doi=doi,
                        preprint_id=doi,
                        url=f"https://doi.org/{doi}" if doi else None,
                        is_review="review" in title.lower(),
                    )
                )

            return SourceFetchResult(source_name=self.source_name, papers=papers)
        except Exception as exc:  # noqa: BLE001
            return SourceFetchResult(source_name=self.source_name, papers=[], failure=_compact_error(exc))


class ArxivClient(BaseSourceClient):
    source_name = "arXiv"
    api_url = "http://export.arxiv.org/api/query"

    def fetch(self, start_date: date, end_date: date, max_results: int) -> SourceFetchResult:
        try:
            params = {
                "search_query": "all:\"skeletal muscle\" OR all:\"myogenesis\" OR all:\"sarcopenia\"",
                "start": "0",
                "max_results": str(max_results),
                "sortBy": "submittedDate",
                "sortOrder": "descending",
            }
            xml_text = self._get(self.api_url, params=params).text
            root = ET.fromstring(xml_text)

            ns = {"atom": "http://www.w3.org/2005/Atom"}
            papers: list[Paper] = []

            for entry in root.findall("atom:entry", ns):
                title = (entry.findtext("atom:title", default="", namespaces=ns) or "Untitled").strip()
                abstract = (entry.findtext("atom:summary", default="", namespaces=ns) or "").strip()
                published_text = (entry.findtext("atom:published", default="", namespaces=ns) or "").strip()
                published_date = _parse_date(published_text)
                if not (start_date <= published_date <= end_date):
                    continue

                authors = [
                    (node.findtext("atom:name", default="", namespaces=ns) or "").strip()
                    for node in entry.findall("atom:author", ns)
                ]
                authors = [name for name in authors if name]

                entry_id = (entry.findtext("atom:id", default="", namespaces=ns) or "").strip()
                arxiv_id = entry_id.split("/")[-1] if entry_id else None
                doi = None
                for node in entry.findall("atom:link", ns):
                    if node.attrib.get("title", "").lower() == "doi":
                        href = node.attrib.get("href", "")
                        doi = href.replace("https://doi.org/", "").strip() if href else None
                        break

                papers.append(
                    Paper(
                        title=title,
                        authors=authors,
                        abstract=abstract,
                        source=self.source_name,
                        source_type="preprint",
                        venue=self.source_name,
                        published_date=published_date,
                        year=published_date.year,
                        doi=doi,
                        arxiv_id=arxiv_id,
                        preprint_id=arxiv_id,
                        url=entry_id or None,
                        is_review="review" in title.lower(),
                    )
                )

            return SourceFetchResult(source_name=self.source_name, papers=papers)
        except Exception as exc:  # noqa: BLE001
            return SourceFetchResult(source_name=self.source_name, papers=[], failure=_compact_error(exc))
