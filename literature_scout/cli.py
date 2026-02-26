from __future__ import annotations

import argparse

from .config import load_config
from .pipeline import run_digest


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Weekly skeletal muscle literature scout")
    parser.add_argument(
        "--config",
        default="config.yaml",
        help="Path to YAML configuration file",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    config = load_config(args.config)
    output = run_digest(config)

    print(f"Report written: {output.report_path}")
    print(f"Sources searched: {', '.join(output.sources_searched)}")
    print(f"Candidates: {output.candidate_count}")
    print(f"Included: {output.included_count}")
    print(f"Summarized: {output.summarized_count}")
    if output.failures:
        print("Failures/issues:")
        for issue in output.failures:
            print(f"- {issue}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
