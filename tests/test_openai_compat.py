import io
import json
import urllib.error

import pytest

from soc.ai.client import AIClientError
from soc.ai.openai_compat import OpenAICompatClient

KEY = "secret-key-xyz"


class FakeResponse:
    def __init__(self, payload):
        self._raw = json.dumps(payload).encode("utf-8")

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False

    def read(self):
        return self._raw


def http_error(code, body="boom"):
    return urllib.error.HTTPError("http://x", code, "err", {}, io.BytesIO(body.encode()))


class FakeOpener:
    """Returns the queued items in order; exceptions are raised."""

    def __init__(self, *items):
        self.items = list(items)
        self.requests = []

    def __call__(self, request, timeout=None):
        self.requests.append(request)
        item = self.items.pop(0)
        if isinstance(item, Exception):
            raise item
        return FakeResponse(item)


def make_client(opener, **kwargs):
    sleeps = []
    client = OpenAICompatClient(
        KEY, "https://api.example.com/v1", "flash-1",
        opener=opener, sleep=sleeps.append, **kwargs,
    )
    client.sleeps = sleeps
    return client


GOOD = {"choices": [{"message": {"content": "hello"}}]}


def test_complete_returns_text_and_sends_expected_request():
    opener = FakeOpener(GOOD)
    client = make_client(opener)
    assert client.complete("hi") == "hello"
    request = opener.requests[0]
    assert request.full_url == "https://api.example.com/v1/chat/completions"
    assert request.get_header("Authorization") == f"Bearer {KEY}"
    body = json.loads(request.data)
    assert body["model"] == "flash-1"
    assert body["messages"] == [{"role": "user", "content": "hi"}]


def test_retries_rate_limit_then_succeeds():
    opener = FakeOpener(http_error(429), GOOD)
    client = make_client(opener)
    assert client.complete("hi") == "hello"
    assert len(client.sleeps) == 1


def test_gives_up_after_retries():
    opener = FakeOpener(http_error(503), http_error(503), http_error(503))
    client = make_client(opener)
    with pytest.raises(AIClientError, match="Giving up"):
        client.complete("hi")


def test_client_errors_are_not_retried():
    opener = FakeOpener(http_error(400, "bad request"))
    client = make_client(opener)
    with pytest.raises(AIClientError, match="HTTP 400"):
        client.complete("hi")
    assert client.sleeps == []


def test_network_error_is_retried_then_reported():
    err = urllib.error.URLError("no route")
    client = make_client(FakeOpener(err, err, err))
    with pytest.raises(AIClientError, match="Network error"):
        client.complete("hi")


def test_key_is_scrubbed_from_error_text():
    client = make_client(FakeOpener(http_error(401, f"invalid key {KEY}")))
    with pytest.raises(AIClientError) as info:
        client.complete("hi")
    assert KEY not in str(info.value)


def test_key_not_in_repr():
    assert KEY not in repr(make_client(FakeOpener()))


@pytest.mark.parametrize("payload", [{}, {"choices": []}, {"choices": [{"message": {"content": None}}]},
                                     {"choices": [{"message": {"content": "  "}}]}])
def test_bad_response_shapes_are_rejected(payload):
    with pytest.raises(AIClientError):
        make_client(FakeOpener(payload)).complete("hi")


def test_list_models_strips_prefix_and_sorts():
    payload = {"data": [{"id": "models/b-flash"}, {"id": "a-model"}]}
    assert make_client(FakeOpener(payload)).list_models() == ["a-model", "b-flash"]


def test_connection_reset_is_retried_then_succeeds():
    opener = FakeOpener(ConnectionResetError("forcibly closed"), GOOD)
    client = make_client(opener)
    assert client.complete("hi") == "hello"
    assert len(client.sleeps) == 1


def test_persistent_connection_reset_becomes_ai_client_error():
    reset = ConnectionResetError("forcibly closed")
    client = make_client(FakeOpener(reset, reset, reset))
    with pytest.raises(AIClientError, match="Network error"):
        client.complete("hi")
