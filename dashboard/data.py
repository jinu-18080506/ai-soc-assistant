"""Plain functions the dashboard uses. No Streamlit in here, so they are easy to test."""

from pathlib import Path

from soc.models import Alert
from soc.report.markdown_report import report_filename
from soc.severity import severity_for_level

SEVERITY_ORDER = ["Critical", "High", "Medium", "Low"]


def severity_of(alert: Alert) -> str:
    return severity_for_level(alert.rule.level).value


def severity_counts(alerts: list[Alert]) -> dict[str, int]:
    """How many alerts there are per severity, most serious first."""
    counts = {name: 0 for name in SEVERITY_ORDER}
    for alert in alerts:
        counts[severity_of(alert)] += 1
    return counts


def alert_label(alert: Alert) -> str:
    return f"{alert.timestamp:%Y-%m-%d %H:%M}  |  {severity_of(alert)}  |  {alert.rule.description}"


def alerts_to_rows(alerts: list[Alert]) -> list[dict]:
    """One simple dict per alert, ready for a table."""
    return [
        {
            "Time": f"{alert.timestamp:%Y-%m-%d %H:%M:%S}",
            "Severity": severity_of(alert),
            "Level": alert.rule.level,
            "Host": alert.agent.name,
            "Rule": alert.rule.description,
            "MITRE": ", ".join(alert.rule.mitre.id) or "-",
        }
        for alert in alerts
    ]


def filter_alerts(alerts: list[Alert], severities: list[str], search: str = "") -> list[Alert]:
    """Keep alerts with a chosen severity whose text matches the search words."""
    needle = search.strip().lower()
    kept = []
    for alert in alerts:
        if severity_of(alert) not in severities:
            continue
        if needle:
            haystack = " ".join(
                [
                    alert.rule.description,
                    alert.agent.name,
                    " ".join(alert.rule.mitre.id),
                    " ".join(alert.rule.groups),
                    alert.full_log or "",
                ]
            ).lower()
            if needle not in haystack:
                continue
        kept.append(alert)
    return kept


def find_report(alert: Alert, reports_dir: str | Path) -> Path | None:
    """The report file for this alert, or None if it has not been written yet."""
    path = Path(reports_dir) / report_filename(alert)
    return path if path.is_file() else None
