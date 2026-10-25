"""Run the full flow: read alerts, analyse them, write reports."""

import logging
from dataclasses import dataclass
from pathlib import Path

from .ai.analyzer import AnalysisError, analyze_alert
from .ai.client import AIClient, AIClientError
from .alert_reader import read_alerts
from .report.markdown_report import write_report
from .state import ProcessedStore

logger = logging.getLogger(__name__)


@dataclass
class RunResult:
    processed: int = 0
    skipped: int = 0
    failed: int = 0


def run_pipeline(
    alerts_path: str | Path,
    out_dir: str | Path,
    client: AIClient,
    store: ProcessedStore,
    min_level: int = 0,
    limit: int | None = None,
    dry_run: bool = False,
) -> RunResult:
    """Process new alerts and return the counts.

    - Alerts already in `store` are skipped.
    - `limit` caps how many alerts are attempted in this run.
    - `dry_run` only prints what would happen and changes nothing.
    - One failing alert is counted and logged, and the run carries on.
    """
    result = RunResult()
    attempted = 0
    for alert in read_alerts(alerts_path, min_level):
        if store.is_processed(alert.id):
            result.skipped += 1
            continue
        if limit is not None and attempted >= limit:
            break
        attempted += 1

        if dry_run:
            print(f"Would process: [level {alert.rule.level}] {alert.rule.description}")
            continue

        try:
            assessment = analyze_alert(alert, client)
            write_report(alert, assessment, out_dir)
        except (AnalysisError, AIClientError, OSError) as error:
            logger.error("Alert %s failed: %s", alert.id, error)
            result.failed += 1
            continue
        store.mark(alert.id)
        result.processed += 1
    return result
