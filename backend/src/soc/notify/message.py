"""Build the short plain-text message that is sent for an alert."""

from pathlib import Path

from ..ai.schemas import Assessment
from ..models import Alert
from ..severity import severity_for_level

MAX_LENGTH = 3500  # Telegram's limit is 4096; stay well under it


def format_message(alert: Alert, assessment: Assessment, report_path: Path | None = None) -> str:
    """Summarise an alert for a chat message.

    Plain text only (no Markdown or HTML), so text from logs or from the AI
    cannot change how the message is displayed. The raw log is left out on
    purpose; the report has it.
    """
    severity = severity_for_level(alert.rule.level).value.upper()
    mitre = ", ".join(alert.rule.mitre.id) or "none"
    lines = [
        f"{severity} alert (rule level {alert.rule.level})",
        alert.rule.description,
        f"Host: {alert.agent.name}   Time: {alert.timestamp.isoformat()}",
        f"MITRE ATT&CK: {mitre}",
        "",
        f"AI risk: {assessment.risk_level.value} (confidence {assessment.confidence}%)",
        assessment.summary,
    ]
    if report_path is not None:
        lines += ["", f"Report: {Path(report_path).name}"]
    text = "\n".join(lines)
    if len(text) > MAX_LENGTH:
        text = text[: MAX_LENGTH - 1] + "\u2026"
    return text
