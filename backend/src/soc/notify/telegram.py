"""Send messages through a Telegram bot. Standard library only.

The bot token sits inside the request URL, so every piece of error text is
scrubbed before it can reach a log or a screen.
"""

import json
import urllib.error
import urllib.request

from .base import NotifyError

API = "https://api.telegram.org/bot{token}/{method}"
MAX_LENGTH = 4096


class TelegramNotifier:
    def __init__(self, token: str, chat_id: str = "", timeout: float = 20.0, opener=None):
        self._token = token
        self.chat_id = chat_id
        self.timeout = timeout
        self._opener = opener or urllib.request.urlopen

    def __repr__(self) -> str:  # never show the token
        return f"TelegramNotifier(chat_id={self.chat_id!r})"

    def _scrub(self, text: str) -> str:
        return text.replace(self._token, "***")[:300] if self._token else text[:300]

    def _call(self, method: str, body: dict | None = None) -> dict:
        data = json.dumps(body).encode("utf-8") if body is not None else None
        request = urllib.request.Request(
            API.format(token=self._token, method=method),
            data=data,
            method="POST" if data is not None else "GET",
            headers={"Content-Type": "application/json"},
        )
        try:
            with self._opener(request, timeout=self.timeout) as response:
                reply = json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as error:
            detail = self._scrub(error.read().decode("utf-8", errors="replace"))
            raise NotifyError(f"Telegram HTTP {error.code}: {detail}") from None
        except json.JSONDecodeError:
            raise NotifyError("Telegram returned something that is not JSON") from None
        except OSError as error:
            raise NotifyError(f"Network error: {self._scrub(str(error))}") from None
        if not isinstance(reply, dict) or not reply.get("ok"):
            raise NotifyError(f"Telegram refused the request: {self._scrub(str(reply))}")
        return reply

    def send(self, text: str) -> None:
        if not self.chat_id:
            raise NotifyError("TELEGRAM_CHAT_ID is not set")
        self._call(
            "sendMessage",
            {"chat_id": self.chat_id, "text": text[:MAX_LENGTH], "disable_web_page_preview": True},
        )

    def find_chats(self) -> list[tuple[str, str]]:
        """List (chat_id, name) for chats that recently messaged the bot."""
        found: dict[str, str] = {}
        for update in self._call("getUpdates").get("result", []):
            message = update.get("message") or update.get("channel_post") or {}
            chat = message.get("chat") or {}
            if "id" in chat:
                name = chat.get("title") or chat.get("first_name") or chat.get("username") or "?"
                found[str(chat["id"])] = name
        return sorted(found.items())
