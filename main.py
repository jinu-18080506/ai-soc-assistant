"""Command-line entry point: process new alerts into incident reports.

Examples:
    python main.py --dry-run          show what would be processed
    python main.py --limit 2          process at most 2 new alerts
    python main.py --min-level 8      only alerts at level 8 or above
    python main.py --list-models      show the AI models your key can use
    python main.py --mock             force the fake AI (no key needed)

With AI_API_KEY and AI_MODEL set in .env a real AI is used; otherwise the
mock AI is used. Exit code is 0 on success, 1 if any alert failed, 2 if the
AI settings are incomplete.
"""

import argparse
import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "backend" / "src"))

from soc.ai.client import AIClientError, MockClient  # noqa: E402
from soc.ai.openai_compat import OpenAICompatClient  # noqa: E402
from soc.config import load_settings  # noqa: E402
from soc.pipeline import run_pipeline  # noqa: E402
from soc.state import ProcessedStore  # noqa: E402


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="AI SOC Assistant pipeline")
    parser.add_argument("--input", default="data/sample_alerts.jsonl", help="alerts file (JSON Lines)")
    parser.add_argument("--out", default="reports", help="folder for incident reports")
    parser.add_argument("--state", default=".state/processed.json", help="processed-alert store")
    parser.add_argument("--env-file", default=".env", help="settings file")
    parser.add_argument("--min-level", type=int, default=0, help="ignore alerts below this level")
    parser.add_argument("--limit", type=int, default=None, help="max alerts to process this run")
    parser.add_argument("--dry-run", action="store_true", help="show what would run, change nothing")
    parser.add_argument("--mock", action="store_true", help="use the fake AI even if a key is set")
    parser.add_argument("--list-models", action="store_true", help="list models for your key and exit")
    args = parser.parse_args(argv)

    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    settings = load_settings(args.env_file)

    if args.list_models:
        if not settings.api_key:
            print("AI_API_KEY is not set. Put it in .env first.")
            return 2
        client = OpenAICompatClient(settings.api_key, settings.base_url, settings.model or "unset")
        try:
            for name in client.list_models():
                print(name)
        except AIClientError as error:
            print(f"Could not list models: {error}")
            return 1
        print("\nPick a name containing 'flash' and put it in .env as AI_MODEL=<name>")
        return 0

    if args.mock or not settings.api_key:
        client = MockClient()
        print("Using the mock AI (reports are labelled [MOCK])")
    elif not settings.model:
        print("AI_API_KEY is set but AI_MODEL is empty. Run: python main.py --list-models")
        return 2
    else:
        client = OpenAICompatClient(settings.api_key, settings.base_url, settings.model)
        print(f"Using AI model: {settings.model}")

    result = run_pipeline(
        alerts_path=args.input,
        out_dir=args.out,
        client=client,
        store=ProcessedStore(args.state),
        min_level=args.min_level,
        limit=args.limit,
        dry_run=args.dry_run,
    )
    print(f"Processed {result.processed}, skipped {result.skipped}, failed {result.failed}")
    return 1 if result.failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
