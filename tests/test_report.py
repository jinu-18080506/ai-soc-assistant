from soc.ai.client import MockClient
from soc.ai.analyzer import analyze_alert
from soc.alert_reader import read_alerts
from soc.report.markdown_report import (
    render_report,
    report_filename,
    write_report,
)
from pathlib import Path
import pytest

SAMPLE = Path(__file__).resolve().parent.parent / "data" / "sample_alerts.jsonl"


@pytest.fixture
def alerts():
    return read_alerts(SAMPLE)


def build(alert):
    return render_report(alert, analyze_alert(alert, MockClient()))


def test_report_has_main_sections(alerts):
    text = build(alerts[0])
    for heading in ("# Incident Report", "## Alert details", "## MITRE ATT&CK",
                    "## Log", "## AI assessment", "## Investigation steps"):
        assert heading in text


def test_report_shows_severity_and_mitre_link(alerts):
    text = build(alerts[0])
    assert "**Severity:** High (rule level 10)" in text
    assert "https://attack.mitre.org/techniques/T1110/" in text


def test_report_handles_alert_without_mitre(alerts):
    no_mitre = next(a for a in alerts if not a.rule.mitre.id)
    assert "- None mapped" in build(no_mitre)


def test_report_includes_log_text(alerts):
    assert "Failed password for root from 203.0.113.45" in build(alerts[0])


def test_pipe_in_description_does_not_break_table(alerts):
    alert = alerts[0].model_copy(update={"agent": alerts[0].agent.model_copy(update={"name": "a|b"})})
    assert "a\\|b" in build(alert)


def test_log_cannot_break_out_of_code_block(alerts):
    evil = "x\n```\n# Injected heading\n```"
    alert = alerts[0].model_copy(update={"full_log": evil})
    text = build(alert)
    # the fence around the log must be longer than the ``` inside the log
    assert "````text" in text


def test_filename_is_safe(alerts):
    name = report_filename(alerts[0])
    assert name.endswith(".md")
    assert "/" not in name and "\\" not in name and " " not in name
    assert name.startswith("20261020-091532_5712_")


def test_write_report_creates_folder_and_file(alerts, tmp_path):
    out = tmp_path / "nested" / "reports"
    path = write_report(alerts[0], analyze_alert(alerts[0], MockClient()), out)
    assert path.exists()
    assert path.read_text(encoding="utf-8").startswith("# Incident Report")
