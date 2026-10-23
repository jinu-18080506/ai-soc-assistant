"""Write a Markdown incident report for one alert plus its AI assessment."""

import re
import sys
from pathlib import Path

from ..ai.analyzer import analyze_alert
from ..ai.client import MockClient
from ..alert_reader import read_alerts
from ..mitre import technique_links
from ..models import Alert
from ..ai.schemas import Assessment
from ..severity import severity_for_level


def _cell(text: str) -> str:
    """Make text safe inside a Markdown table cell."""
    return text.replace("|", "\\|").replace("\n", " ").strip()


def _code_block(text: str) -> str:
    """Wrap text in a code fence that the text itself cannot break out of.

    Log lines are untrusted. If one contains ``` it could end the block early,
    so the fence is made longer than any run of backticks in the text.
    """
    longest = max((len(run) for run in re.findall(r"`+", text)), default=0)
    fence = "`" * max(3, longest + 1)
    return f"{fence}text\n{text}\n{fence}"


def render_report(alert: Alert, assessment: Assessment) -> str:
    """Build the report text."""
    rule = alert.rule
    alert_severity = severity_for_level(rule.level).value
    mitre_lines = [
        f"- [{technique_id}]({url}) {name}".rstrip()
        for technique_id, name, url in technique_links(rule.mitre)
    ] or ["- None mapped"]
    steps = [f"{number}. {step}" for number, step in enumerate(assessment.investigation_steps, 1)]

    parts = [
        f"# Incident Report: {_cell(rule.description)}",
        "",
        f"**Severity:** {alert_severity} (rule level {rule.level})",
        "",
        "## Alert details",
        "",
        "| Field | Value |",
        "|-------|-------|",
        f"| Alert ID | {_cell(alert.id)} |",
        f"| Time | {alert.timestamp.isoformat()} |",
        f"| Rule | {_cell(rule.id)} |",
        f"| Host | {_cell(alert.agent.name)} ({_cell(alert.agent.ip or 'unknown IP')}) |",
        f"| Source | {_cell(alert.location or 'unknown')} |",
        f"| Groups | {_cell(', '.join(rule.groups) or 'none')} |",
        "",
        "## MITRE ATT&CK",
        "",
        *mitre_lines,
        "",
        "## Log",
        "",
        _code_block(alert.full_log or "(no log text)"),
        "",
        "## AI assessment",
        "",
        "> AI-generated. Verify before acting on it.",
        "",
        f"**Risk:** {assessment.risk_level.value}  ",
        f"**Confidence:** {assessment.confidence}%  ",
        f"**Likely false positive:** {'Yes' if assessment.likely_false_positive else 'No'}",
        "",
        assessment.summary,
        "",
        "## Investigation steps",
        "",
        *steps,
        "",
    ]
    return "\n".join(parts)


def report_filename(alert: Alert) -> str:
    """A filesystem-safe name such as 20261020-091532_5712_1760000001-100001.md"""
    stamp = alert.timestamp.strftime("%Y%m%d-%H%M%S")
    raw = f"{stamp}_{alert.rule.id}_{alert.id}"
    return re.sub(r"[^A-Za-z0-9_-]", "-", raw) + ".md"


def write_report(alert: Alert, assessment: Assessment, out_dir: str | Path) -> Path:
    """Save the report in `out_dir` (created if missing) and return its path."""
    folder = Path(out_dir)
    folder.mkdir(parents=True, exist_ok=True)
    path = folder / report_filename(alert)
    path.write_text(render_report(alert, assessment), encoding="utf-8")
    return path


def main() -> None:
    """Write a report for every alert in a file, using the mock AI."""
    if len(sys.argv) < 3:
        print("Usage: python -m soc.report.markdown_report <alerts.jsonl> <output_folder>")
        raise SystemExit(1)
    client = MockClient()
    alerts = read_alerts(sys.argv[1])
    for alert in alerts:
        path = write_report(alert, analyze_alert(alert, client), sys.argv[2])
        print(f"Wrote {path}")
    print(f"\n{len(alerts)} report(s) written")


if __name__ == "__main__":
    main()
