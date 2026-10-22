"""Data models for SOC alerts.

These classes describe the shape of a Wazuh-style alert. Pydantic checks every
alert against them, so bad data fails loudly instead of causing odd bugs later.
"""

import re
from datetime import datetime

from pydantic import BaseModel, Field, field_validator


class Mitre(BaseModel):
    """MITRE ATT&CK info attached to a rule (all three lists can be empty)."""

    id: list[str] = Field(default_factory=list)
    tactic: list[str] = Field(default_factory=list)
    technique: list[str] = Field(default_factory=list)


class Agent(BaseModel):
    """The machine that produced the alert."""

    id: str
    name: str
    ip: str | None = None


class Rule(BaseModel):
    """The detection rule that fired."""

    id: str
    level: int = Field(ge=0, le=15)  # Wazuh levels run from 0 to 15
    description: str
    groups: list[str] = Field(default_factory=list)
    mitre: Mitre = Field(default_factory=Mitre)


class Alert(BaseModel):
    """One security alert."""

    id: str
    timestamp: datetime
    rule: Rule
    agent: Agent
    location: str | None = None
    full_log: str | None = None

    @field_validator("timestamp", mode="before")
    @classmethod
    def fix_wazuh_timezone(cls, value):
        """Wazuh writes timezones as +0000; convert to +00:00 so it parses."""
        if isinstance(value, str):
            return re.sub(r"([+-]\d{2})(\d{2})$", r"\1:\2", value)
        return value
