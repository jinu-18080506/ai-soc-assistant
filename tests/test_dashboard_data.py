from pathlib import Path

import pytest

from dashboard.data import (
    alert_label,
    alerts_to_rows,
    filter_alerts,
    find_report,
    severity_counts,
)
from soc.ai.analyzer import analyze_alert
from soc.ai.client import MockClient
from soc.alert_reader import read_alerts
from soc.report.markdown_report import write_report

SAMPLE = Path(__file__).resolve().parent.parent / "data" / "sample_alerts.jsonl"
ALL = ["Critical", "High", "Medium", "Low"]


@pytest.fixture
def alerts():
    return read_alerts(SAMPLE)


def test_severity_counts_in_order(alerts):
    counts = severity_counts(alerts)
    assert list(counts) == ALL
    assert counts == {"Critical": 1, "High": 2, "Medium": 2, "Low": 1}


def test_rows_have_expected_columns(alerts):
    row = alerts_to_rows(alerts)[0]
    assert set(row) == {"Time", "Severity", "Level", "Host", "Rule", "MITRE"}
    assert row["Severity"] == "High" and row["MITRE"] == "T1110"


def test_row_shows_dash_when_no_mitre(alerts):
    rows = alerts_to_rows(alerts)
    assert rows[-1]["MITRE"] == "-"


def test_filter_by_severity(alerts):
    assert len(filter_alerts(alerts, ["Critical"])) == 1
    assert len(filter_alerts(alerts, ["Critical", "High"])) == 3
    assert filter_alerts(alerts, []) == []


@pytest.mark.parametrize(
    ("search", "expected"),
    [("powershell", 1), ("T1110", 1), ("UBUNTU-WEB-01", 4), ("203.0.113.45", 1), ("nothing-matches", 0), ("  ", 6)],
)
def test_filter_by_search(alerts, search, expected):
    assert len(filter_alerts(alerts, ALL, search)) == expected


def test_label_has_severity_and_rule(alerts):
    label = alert_label(alerts[0])
    assert "High" in label and alerts[0].rule.description in label


def test_find_report(alerts, tmp_path):
    assert find_report(alerts[0], tmp_path) is None
    write_report(alerts[0], analyze_alert(alerts[0], MockClient()), tmp_path)
    assert find_report(alerts[0], tmp_path) is not None
