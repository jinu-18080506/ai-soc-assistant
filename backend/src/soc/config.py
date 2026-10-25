"""Load settings from a .env file and environment variables.

Real environment variables win over the file. The API key is kept out of the
repr, so it cannot leak by accident into a log line or a traceback.
"""

import os
from dataclasses import dataclass, field
from pathlib import Path

DEFAULT_BASE_URL = "https://generativelanguage.googleapis.com/v1beta/openai/"


@dataclass(frozen=True)
class Settings:
    api_key: str = field(default="", repr=False)
    base_url: str = DEFAULT_BASE_URL
    model: str = ""


def parse_env_file(path: str | Path) -> dict[str, str]:
    """Read KEY=VALUE lines. Blank lines, # comments and bad lines are ignored."""
    file = Path(path)
    if not file.exists():
        return {}
    values: dict[str, str] = {}
    for line in file.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("export "):
            line = line[len("export "):]
        key, separator, value = line.partition("=")
        if not separator:
            continue
        value = value.strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
            value = value[1:-1]
        values[key.strip()] = value
    return values


def load_settings(env_file: str | Path = ".env", environ=None) -> Settings:
    """Build Settings from the .env file, overridden by real environment variables."""
    environ = os.environ if environ is None else environ
    merged = {**parse_env_file(env_file)}
    for name in ("AI_API_KEY", "AI_BASE_URL", "AI_MODEL"):
        if environ.get(name):
            merged[name] = environ[name]
    return Settings(
        api_key=merged.get("AI_API_KEY", "").strip(),
        base_url=merged.get("AI_BASE_URL", "").strip() or DEFAULT_BASE_URL,
        model=merged.get("AI_MODEL", "").strip(),
    )
