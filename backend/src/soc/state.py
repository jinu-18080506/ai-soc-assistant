"""Remember which alerts were already processed, so reruns skip them.

Skipping matters once a real AI is connected: every alert analysed again would
be billed again.
"""

import json
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


class ProcessedStore:
    """A set of processed alert IDs, saved as a small JSON file."""

    def __init__(self, path: str | Path):
        self.path = Path(path)
        self._ids: set[str] = set()
        self._load()

    def _load(self) -> None:
        if not self.path.exists():
            return
        try:
            data = json.loads(self.path.read_text(encoding="utf-8"))
            self._ids = {str(item) for item in data}
        except (json.JSONDecodeError, TypeError, OSError) as error:
            logger.warning("State file %s is unreadable, starting empty: %s", self.path, error)

    def is_processed(self, alert_id: str) -> bool:
        return alert_id in self._ids

    def mark(self, alert_id: str) -> None:
        """Record an alert as processed and save straight away."""
        self._ids.add(alert_id)
        self._save()

    def _save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        temp = self.path.with_suffix(".tmp")
        temp.write_text(json.dumps(sorted(self._ids)), encoding="utf-8")
        temp.replace(self.path)  # replace in one step so a crash can't half-write it
