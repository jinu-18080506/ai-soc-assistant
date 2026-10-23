"""Turn a Wazuh rule level (0-15) into a simple severity label.

The cut-offs below are this project's own choice, not an official Wazuh
standard. Change them here if you want triage to be stricter or looser.
"""

from enum import Enum


class Severity(str, Enum):
    LOW = "Low"
    MEDIUM = "Medium"
    HIGH = "High"
    CRITICAL = "Critical"


def severity_for_level(level: int) -> Severity:
    """Map a rule level to a Severity.

    0-3   -> Low
    4-7   -> Medium
    8-11  -> High
    12-15 -> Critical
    """
    if not 0 <= level <= 15:
        raise ValueError(f"Rule level must be between 0 and 15, got {level}")
    if level <= 3:
        return Severity.LOW
    if level <= 7:
        return Severity.MEDIUM
    if level <= 11:
        return Severity.HIGH
    return Severity.CRITICAL
