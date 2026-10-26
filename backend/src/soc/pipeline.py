"""Run the full flow: read alerts, analyse them, write reports."""

import logging
from dataclasses import dataclass
from pathlib import Path

from .ai.analyzer import AnalysisError, analyze_alert
from .ai.client import AIClient, AIClientError
from .alert_reader import read_alerts
from .notify.base import Notifier, NotifyError
from .notify.message import format_message
from .report.markdown_report import write_report
from .state import ProcessedStore

logger = logging.getLogger(__name__)


@dataclass
class RunResult:
    processed: int = 0
    skipped: int = 0
    failed: int = 0
    notified: int = 0
    notify_failed: int = 0


def run_pipeline(
    alerts_path: str | Path,
    out_dir: str | Path,
    client: AIClient,
    store: ProcessedStore,
    min_level: int = 0,
    limit: int | None = None,
    dry_run: bool = False,
    notifier: Notifier | None = None,
    notify_min_level: int = 8,
) -> RunResult:
    """Process new alerts and return the counts.

    - Alerts already in `store` are skipped.
    - `limit` caps how many alerts are attempted in this run.
    - `dry_run` only prints what would happen and changes nothing.
    - One failing alert is counted and logged, and the run carries on.
    - With a `notifier`, alerts at or above `notify_min_level` are also sent as
      a message. A failed message never fails the alert: the alert is already
      saved, and redoing it would only cost another AI call.
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
            report_path = write_report(alert, assessment, out_dir)
        except (AnalysisError, AIClientError, OSError) as error:
            logger.error("Alert %s failed: %s", alert.id, error)
            result.failed += 1
            continue
        store.mark(alert.id)
        result.processed += 1

        if notifier is not None and alert.rule.level >= notify_min_level:
            try:
                notifier.send(format_message(alert, assessment, report_path))
                result.notified += 1
            except NotifyError as error:
                logger.error("Notification for alert %s failed: %s", alert.id, error)
                result.notify_failed += 1
    return result
