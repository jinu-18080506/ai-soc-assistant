from pathlib import Path

from soc.ai.client import MockClient
from soc.notify.base import NotifyError
from soc.pipeline import run_pipeline
from soc.state import ProcessedStore

SAMPLE = Path(__file__).resolve().parent.parent / "data" / "sample_alerts.jsonl"


class RecordingNotifier:
    def __init__(self):
        self.messages = []

    def send(self, text):
        self.messages.append(text)


class BrokenNotifier:
    def send(self, text):
        raise NotifyError("telegram is down")


def run(tmp_path, notifier, **kwargs):
    store = ProcessedStore(tmp_path / "s.json")
    return run_pipeline(SAMPLE, tmp_path / "r", MockClient(), store, notifier=notifier, **kwargs), store


def test_only_high_alerts_are_sent_by_default(tmp_path):
    notifier = RecordingNotifier()
    result, _ = run(tmp_path, notifier)
    assert result.processed == 6
    assert result.notified == len(notifier.messages) == 3  # levels 10, 8 and 12


def test_notify_level_can_be_changed(tmp_path):
    notifier = RecordingNotifier()
    run(tmp_path, notifier, notify_min_level=12)
    assert len(notifier.messages) == 1
    assert "CRITICAL" in notifier.messages[0]


def test_no_notifier_means_no_messages(tmp_path):
    result, _ = run(tmp_path, None)
    assert (result.processed, result.notified) == (6, 0)


def test_failed_notification_does_not_fail_or_redo_the_alert(tmp_path):
    result, store = run(tmp_path, BrokenNotifier())
    assert (result.processed, result.failed) == (6, 0)
    assert result.notify_failed == 3
    assert store.is_processed("1760000001.100001")  # saved, so it is not analysed again


def test_dry_run_sends_nothing(tmp_path):
    notifier = RecordingNotifier()
    run(tmp_path, notifier, dry_run=True)
    assert notifier.messages == []
