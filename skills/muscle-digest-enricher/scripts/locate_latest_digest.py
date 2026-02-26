from __future__ import annotations

from pathlib import Path


def main() -> int:
    root = Path(__file__).resolve().parents[3]
    digest_dir = root / "reports" / "weekly_digests"
    candidates = sorted(digest_dir.glob("weekly_muscle_digest_*.json"))

    if not candidates:
        print("No digest JSON found in reports/weekly_digests")
        return 1

    print(str(candidates[-1]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
