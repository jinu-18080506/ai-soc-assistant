from pathlib import Path

import pytest

from soc.ai.client import MockClient
from soc.pipeline import run_pipeline
from soc.state import ProcessedStore

SAMPLE = Path(__file__).resolve().parent.parent / "data" / "sample_alerts.jsonl"


class GarbageClient:
    """Always returns an unusable answer."""

    def complete(self, prompt: str) -> str:
        return "sorry, I cannot help"


class FailsOnFirstClient:
    """Garbage on the first call, valid answers afterwards."""

    def __init__(self):
        self.calls = 0
        self.good = MockClient()

    def complete(self, prompt: str) -> str:
        self.calls += 1
        return "garbage" if self.calls == 1 else self.good.complete(prompt)


@pytest.fixture
def store(tmp_path):
    return ProcessedStore(tmp_path / "state.json")


def run(tmp_path, store, client=None, **kwargs):
    return run_pipeline(SAMPLE, tmp_path / "reports", client or MockClient(), store, **kwargs)


def test_processes_all_alerts_and_writes_reports(tmp_path, store):
    result = run(tmp_path, store)
    assert (result.processed, result.skipped, result.failed) == (6, 0, 0)
    assert len(list((tmp_path / "reports").glob("*.md"))) == 6


def test_second_run_skips_everything(tmp_path, store):
    run(tmp_path, store)
    result = run(tmp_path, store)
    assert (result.processed, result.skipped) == (0, 6)


def test_limit_caps_alerts_processed(tmp_path, store):
    assert run(tmp_path, store, limit=2).processed == 2
    again = run(tmp_path, store)
    assert (again.processed, again.skipped) == (4, 2)


def test_min_level_filters(tmp_path, store):
    assert run(tmp_path, store, min_level=8).processed == 3


def test_dry_run_changes_nothing(tmp_path, store, capsys):
    result = run(tmp_path, store, dry_run=True)
    assert result.processed == 0
    assert not (tmp_path / "reports").exists()
    assert "Would process" in capsys.readouterr().out
    assert run(tmp_path, store).processed == 6  # nothing was marked


def test_failed_alert_is_counted_and_retried_later(tmp_path, store):
    result = run(tmp_path, store, client=FailsOnFirstClient())
    assert (result.processed, result.failed) == (5, 1)
    retry = run(tmp_path, store)
    assert (retry.processed, retry.skipped) == (1, 5)


def test_all_failing_does_not_crash(tmp_path, store):
    result = run(tmp_path, store, client=GarbageClient())
    assert (result.processed, result.failed) == (0, 6)
