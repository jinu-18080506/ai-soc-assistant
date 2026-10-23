import json
from pathlib import Path

from soc.alert_reader import read_alerts

SAMPLE = Path(__file__).resolve().parent.parent / "data" / "sample_alerts.jsonl"


def make_alert(alert_id="1", level=5):
    return {
        "id": alert_id,
        "timestamp": "2026-10-20T09:15:32.123+0000",
        "rule": {"id": "100", "level": level, "description": "test rule"},
        "agent": {"id": "001", "name": "host-1"},
    }


def write_lines(path, lines):
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def test_sample_file_loads_all_alerts():
    assert len(read_alerts(SAMPLE)) == 6


def test_min_level_filters_alerts():
    alerts = read_alerts(SAMPLE, min_level=8)
    assert len(alerts) == 3
    assert all(alert.rule.level >= 8 for alert in alerts)


def test_wazuh_timezone_format_is_parsed(tmp_path):
    file = tmp_path / "alerts.jsonl"
    write_lines(file, [json.dumps(make_alert())])
    alert = read_alerts(file)[0]
    assert alert.timestamp.utcoffset().total_seconds() == 0


def test_bad_lines_are_skipped_not_fatal(tmp_path):
    file = tmp_path / "alerts.jsonl"
    write_lines(
        file,
        [
            "this is not json",
            json.dumps({"id": "x"}),  # missing required fields
            json.dumps(make_alert("good")),
        ],
    )
    alerts = read_alerts(file)
    assert [alert.id for alert in alerts] == ["good"]


def test_blank_lines_are_ignored(tmp_path):
    file = tmp_path / "alerts.jsonl"
    write_lines(file, ["", json.dumps(make_alert()), "   ", ""])
    assert len(read_alerts(file)) == 1


def test_level_above_15_is_rejected(tmp_path):
    file = tmp_path / "alerts.jsonl"
    write_lines(file, [json.dumps(make_alert(level=99))])
    assert read_alerts(file) == []
