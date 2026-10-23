import json
from pathlib import Path

import pytest

from soc.ai.analyzer import AnalysisError, analyze_alert, build_prompt, parse_assessment
from soc.ai.client import MockClient
from soc.alert_reader import read_alerts
from soc.severity import Severity

SAMPLE = Path(__file__).resolve().parent.parent / "data" / "sample_alerts.jsonl"

VALID = {
    "summary": "Repeated SSH logins failed.",
    "risk_level": "high",
    "confidence": 80,
    "likely_false_positive": False,
    "investigation_steps": ["Check source IP"],
}


@pytest.fixture
def alerts():
    return read_alerts(SAMPLE)


def test_prompt_contains_alert_details(alerts):
    prompt = build_prompt(alerts[0])
    assert "Rule description: sshd: brute force attempt on multiple accounts" in prompt
    assert "Rule level: 10" in prompt
    assert "T1110" in prompt


def test_prompt_marks_log_as_untrusted(alerts):
    assert "untrusted" in build_prompt(alerts[0])


def test_prompt_truncates_very_long_logs(alerts):
    alert = alerts[0].model_copy(update={"full_log": "A" * 5000})
    prompt = build_prompt(alert)
    assert "A" * 1000 in prompt
    assert "A" * 1001 not in prompt


def test_parse_valid_json():
    assessment = parse_assessment(json.dumps(VALID))
    assert assessment.risk_level == Severity.HIGH
    assert assessment.confidence == 80


def test_parse_json_wrapped_in_code_fence():
    text = "```json\n" + json.dumps(VALID) + "\n```"
    assert parse_assessment(text).summary == "Repeated SSH logins failed."


@pytest.mark.parametrize("bad", ["not json at all", "{}", "[]", ""])
def test_parse_rejects_garbage(bad):
    with pytest.raises(AnalysisError):
        parse_assessment(bad)


def test_parse_rejects_unknown_risk_level():
    bad = {**VALID, "risk_level": "apocalyptic"}
    with pytest.raises(AnalysisError):
        parse_assessment(json.dumps(bad))


def test_parse_rejects_confidence_out_of_range():
    bad = {**VALID, "confidence": 150}
    with pytest.raises(AnalysisError):
        parse_assessment(json.dumps(bad))


def test_parse_rejects_empty_steps():
    bad = {**VALID, "investigation_steps": []}
    with pytest.raises(AnalysisError):
        parse_assessment(json.dumps(bad))


def test_mock_client_gives_valid_assessment_for_every_sample_alert(alerts):
    client = MockClient()
    for alert in alerts:
        assessment = analyze_alert(alert, client)
        assert assessment.summary.startswith("[MOCK]")


def test_mock_risk_follows_rule_level(alerts):
    client = MockClient()
    by_level = {a.rule.level: analyze_alert(a, client).risk_level for a in alerts}
    assert by_level[12] == Severity.CRITICAL
    assert by_level[10] == Severity.HIGH
    assert by_level[3] == Severity.LOW
