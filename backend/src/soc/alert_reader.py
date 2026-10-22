"""Read Wazuh-style alerts from a JSON Lines file (one JSON alert per line)."""

import json
import logging
import sys
from pathlib import Path

from pydantic import ValidationError

from .models import Alert

logger = logging.getLogger(__name__)


def read_alerts(path: str | Path, min_level: int = 0) -> list[Alert]:
    """Load alerts from `path`, keeping only those at or above `min_level`.

    Blank lines are ignored. A line that is not valid JSON, or that does not
    match the Alert model, is logged and skipped so one bad line never stops
    the whole run.
    """
    alerts: list[Alert] = []
    with Path(path).open(encoding="utf-8") as file:
        for line_number, line in enumerate(file, start=1):
            line = line.strip()
            if not line:
                continue
            try:
                alert = Alert.model_validate(json.loads(line))
            except (json.JSONDecodeError, ValidationError) as error:
                logger.warning("Skipping line %d: %s", line_number, error)
                continue
            if alert.rule.level >= min_level:
                alerts.append(alert)
    return alerts


def main() -> None:
    """Print a quick table of the alerts in a file (for manual checking)."""
    if len(sys.argv) < 2:
        print("Usage: python -m soc.alert_reader <alerts.jsonl> [min_level]")
        raise SystemExit(1)
    min_level = int(sys.argv[2]) if len(sys.argv) > 2 else 0
    alerts = read_alerts(sys.argv[1], min_level)
    print(f"{len(alerts)} alert(s) loaded\n")
    for alert in alerts:
        mitre = ", ".join(alert.rule.mitre.id) or "-"
        print(
            f"[level {alert.rule.level:>2}] {alert.agent.name:<14} "
            f"{mitre:<10} {alert.rule.description}"
        )


if __name__ == "__main__":
    main()
