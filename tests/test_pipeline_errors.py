from pathlib import Path

from soc.ai.client import AIClientError
from soc.pipeline import run_pipeline
from soc.state import ProcessedStore

SAMPLE = Path(__file__).resolve().parent.parent / "data" / "sample_alerts.jsonl"


class DownClient:
    def complete(self, prompt: str) -> str:
        raise AIClientError("service unavailable")


def test_ai_service_errors_are_counted_not_fatal(tmp_path):
    store = ProcessedStore(tmp_path / "s.json")
    result = run_pipeline(SAMPLE, tmp_path / "r", DownClient(), store)
    assert (result.processed, result.failed) == (0, 6)
    assert not store.is_processed("1760000001.100001")  # retried on the next run
