"""Command-line entry point: process new alerts into incident reports.

Examples:
    python main.py --dry-run          show what would be processed
    python main.py --limit 2          process at most 2 new alerts
    python main.py --min-level 8      only alerts at level 8 or above

Exit code is 0 on success and 1 if any alert failed.
"""

import argparse
import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "backend" / "src"))

from soc.ai.client import MockClient  # noqa: E402
from soc.pipeline import run_pipeline  # noqa: E402
from soc.state import ProcessedStore  # noqa: E402


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="AI SOC Assistant pipeline")
    parser.add_argument("--input", default="data/sample_alerts.jsonl", help="alerts file (JSON Lines)")
    parser.add_argument("--out", default="reports", help="folder for incident reports")
    parser.add_argument("--state", default=".state/processed.json", help="processed-alert store")
    parser.add_argument("--min-level", type=int, default=0, help="ignore alerts below this level")
    parser.add_argument("--limit", type=int, default=None, help="max alerts to process this run")
    parser.add_argument("--dry-run", action="store_true", help="show what would run, change nothing")
    args = parser.parse_args(argv)

    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

    result = run_pipeline(
        alerts_path=args.input,
        out_dir=args.out,
        client=MockClient(),  # a real provider is added in a later stage
        store=ProcessedStore(args.state),
        min_level=args.min_level,
        limit=args.limit,
        dry_run=args.dry_run,
    )
    print(f"Processed {result.processed}, skipped {result.skipped}, failed {result.failed}")
    return 1 if result.failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
