"""AI clients. A client takes a prompt and returns the model's text answer.

Anything with a `complete(prompt) -> str` method works. That is what lets us
swap the mock for a real provider later without touching the analyzer.
"""

import json
import re
from typing import Protocol


class AIClientError(Exception):
    """A real AI provider could not be reached or returned an error."""


class AIClient(Protocol):
    def complete(self, prompt: str) -> str: ...


class MockClient:
    """A fake AI for development and tests. No network, no key, no cost.

    It reads the rule level and description from the prompt and returns a
    correctly shaped JSON answer. Its output is NOT real analysis, so every
    summary is labelled [MOCK].
    """

    def complete(self, prompt: str) -> str:
        level_match = re.search(r"Rule level: (\d+)", prompt)
        description_match = re.search(r"Rule description: (.+)", prompt)
        level = int(level_match.group(1)) if level_match else 0
        description = description_match.group(1).strip() if description_match else "unknown"

        if level >= 12:
            risk = "critical"
        elif level >= 8:
            risk = "high"
        elif level >= 4:
            risk = "medium"
        else:
            risk = "low"

        answer = {
            "summary": f"[MOCK] Placeholder assessment for: {description}",
            "risk_level": risk,
            "confidence": 50,
            "likely_false_positive": level <= 3,
            "investigation_steps": [
                "[MOCK] Check the affected host for related alerts",
                "[MOCK] Review the full log line for the source and user",
            ],
        }
        return json.dumps(answer)
