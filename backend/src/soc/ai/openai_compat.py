"""A client for any OpenAI-compatible chat API (Gemini, Groq, OpenAI, ...).

Uses only the Python standard library, so there is nothing extra to install.
"""

import json
import time
import urllib.error
import urllib.request

from .client import AIClientError

RETRY_STATUS = {429, 500, 502, 503, 504}


class OpenAICompatClient:
    def __init__(
        self,
        api_key: str,
        base_url: str,
        model: str,
        timeout: float = 60.0,
        max_retries: int = 2,
        backoff_seconds: float = 5.0,
        opener=None,
        sleep=time.sleep,
    ):
        self._api_key = api_key
        self.base_url = base_url if base_url.endswith("/") else base_url + "/"
        self.model = model
        self.timeout = timeout
        self.max_retries = max_retries
        self.backoff_seconds = backoff_seconds
        self._opener = opener or urllib.request.urlopen
        self._sleep = sleep

    def __repr__(self) -> str:  # never show the key
        return f"OpenAICompatClient(model={self.model!r}, base_url={self.base_url!r})"

    def _scrub(self, text: str) -> str:
        return text.replace(self._api_key, "***")[:300] if self._api_key else text[:300]

    def _request(self, path: str, body: dict | None = None) -> dict:
        """Call the API, retrying on rate limits and temporary server errors."""
        data = json.dumps(body).encode("utf-8") if body is not None else None
        last_error = "unknown error"
        for attempt in range(self.max_retries + 1):
            request = urllib.request.Request(
                self.base_url + path,
                data=data,
                method="POST" if data is not None else "GET",
                headers={
                    "Authorization": f"Bearer {self._api_key}",
                    "Content-Type": "application/json",
                },
            )
            try:
                with self._opener(request, timeout=self.timeout) as response:
                    return json.loads(response.read().decode("utf-8"))
            except urllib.error.HTTPError as error:
                detail = self._scrub(error.read().decode("utf-8", errors="replace"))
                last_error = f"HTTP {error.code}: {detail}"
                if error.code not in RETRY_STATUS:
                    raise AIClientError(last_error) from None
            except OSError as error:
                last_error = f"Network error: {self._scrub(str(error))}"
            except json.JSONDecodeError:
                raise AIClientError("The AI service returned something that is not JSON") from None
            if attempt < self.max_retries:
                self._sleep(self.backoff_seconds * (attempt + 1))
        raise AIClientError(f"Giving up after {self.max_retries + 1} attempts. Last error: {last_error}")

    def complete(self, prompt: str) -> str:
        reply = self._request(
            "chat/completions",
            {"model": self.model, "messages": [{"role": "user", "content": prompt}]},
        )
        try:
            content = reply["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError):
            raise AIClientError("Unexpected response shape from the AI service") from None
        if not isinstance(content, str) or not content.strip():
            raise AIClientError("The AI service returned an empty answer")
        return content

    def list_models(self) -> list[str]:
        """Names of the models this key can use."""
        reply = self._request("models")
        try:
            names = [item["id"].removeprefix("models/") for item in reply["data"]]
        except (KeyError, TypeError):
            raise AIClientError("Unexpected response shape when listing models") from None
        return sorted(names)
