import io
import json
import urllib.error
from pathlib import Path

import pytest

from soc.ai.analyzer import analyze_alert
from soc.ai.client import MockClient
from soc.alert_reader import read_alerts
from soc.notify.base import NotifyError
from soc.notify.message import MAX_LENGTH, format_message
from soc.notify.telegram import TelegramNotifier

SAMPLE = Path(__file__).resolve().parent.parent / "data" / "sample_alerts.jsonl"
TOKEN = "123456:SECRET-token-abc"


@pytest.fixture
def alert():
    return read_alerts(SAMPLE)[0]


def assess(alert):
    return analyze_alert(alert, MockClient())


# ---- message formatting ----
def test_message_has_key_facts(alert):
    text = format_message(alert, assess(alert), Path("reports/r1.md"))
    assert "HIGH alert (rule level 10)" in text
    assert alert.rule.description in text
    assert "ubuntu-web-01" in text and "T1110" in text
    assert "Report: r1.md" in text


def test_message_leaves_out_raw_log(alert):
    assert "Failed password for root" not in format_message(alert, assess(alert))


def test_message_is_truncated(alert):
    long_assessment = assess(alert).model_copy(update={"summary": "x" * 10000})
    assert len(format_message(alert, long_assessment)) <= MAX_LENGTH


# ---- Telegram client ----
class FakeResponse:
    def __init__(self, payload):
        self._raw = json.dumps(payload).encode()

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False

    def read(self):
        return self._raw


class FakeOpener:
    def __init__(self, *items):
        self.items = list(items)
        self.requests = []

    def __call__(self, request, timeout=None):
        self.requests.append(request)
        item = self.items.pop(0)
        if isinstance(item, Exception):
            raise item
        return FakeResponse(item)


def http_error(code, body=""):
    return urllib.error.HTTPError("http://x", code, "err", {}, io.BytesIO(body.encode()))


def test_send_posts_to_send_message():
    opener = FakeOpener({"ok": True})
    TelegramNotifier(TOKEN, "42", opener=opener).send("hello")
    request = opener.requests[0]
    assert request.full_url.endswith("/sendMessage")
    body = json.loads(request.data)
    assert body["chat_id"] == "42" and body["text"] == "hello"
    assert "parse_mode" not in body  # plain text only


def test_send_without_chat_id_is_rejected():
    with pytest.raises(NotifyError, match="CHAT_ID"):
        TelegramNotifier(TOKEN, "", opener=FakeOpener()).send("hi")


def test_telegram_refusal_is_reported():
    opener = FakeOpener({"ok": False, "description": "chat not found"})
    with pytest.raises(NotifyError, match="refused"):
        TelegramNotifier(TOKEN, "42", opener=opener).send("hi")


def test_http_error_text_never_contains_token():
    opener = FakeOpener(http_error(401, f'{{"description":"bad token {TOKEN}"}}'))
    with pytest.raises(NotifyError) as info:
        TelegramNotifier(TOKEN, "42", opener=opener).send("hi")
    assert TOKEN not in str(info.value)
    assert "HTTP 401" in str(info.value)


def test_network_error_text_never_contains_token():
    opener = FakeOpener(urllib.error.URLError(f"failed for /bot{TOKEN}/sendMessage"))
    with pytest.raises(NotifyError) as info:
        TelegramNotifier(TOKEN, "42", opener=opener).send("hi")
    assert TOKEN not in str(info.value)


def test_token_not_in_repr():
    assert TOKEN not in repr(TelegramNotifier(TOKEN, "42"))


def test_find_chats_lists_unique_chats():
    updates = {
        "ok": True,
        "result": [
            {"message": {"chat": {"id": 42, "first_name": "Jinu"}}},
            {"message": {"chat": {"id": 42, "first_name": "Jinu"}}},
            {"channel_post": {"chat": {"id": -100, "title": "Alerts"}}},
            {"edited_message": {}},
        ],
    }
    chats = TelegramNotifier(TOKEN, opener=FakeOpener(updates)).find_chats()
    assert chats == [("-100", "Alerts"), ("42", "Jinu")]
