"""What every notification channel has in common."""

from typing import Protocol


class NotifyError(Exception):
    """A notification could not be sent."""


class Notifier(Protocol):
    def send(self, text: str) -> None: ...
