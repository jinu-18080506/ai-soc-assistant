"""Helpers for working with MITRE ATT&CK technique IDs."""

import re
from itertools import zip_longest

from .models import Mitre

# T1059 (technique) or T1059.001 (sub-technique)
_TECHNIQUE_ID = re.compile(r"^T\d{4}(\.\d{3})?$")


def technique_url(technique_id: str) -> str:
    """Return the attack.mitre.org page for a technique or sub-technique ID.

    T1110      -> https://attack.mitre.org/techniques/T1110/
    T1059.001  -> https://attack.mitre.org/techniques/T1059/001/
    """
    if not _TECHNIQUE_ID.match(technique_id):
        raise ValueError(f"Not a valid ATT&CK technique ID: {technique_id!r}")
    base_id, _, sub_id = technique_id.partition(".")
    path = f"{base_id}/{sub_id}" if sub_id else base_id
    return f"https://attack.mitre.org/techniques/{path}/"


def technique_links(mitre: Mitre) -> list[tuple[str, str, str]]:
    """List (id, name, url) for each technique attached to a rule.

    Wazuh gives the IDs and the technique names as two parallel lists. If a
    name is missing, an empty string is used. An ID that is not a valid
    technique ID is skipped.
    """
    links = []
    for technique_id, name in zip_longest(mitre.id, mitre.technique, fillvalue=""):
        if not technique_id:
            continue
        try:
            url = technique_url(technique_id)
        except ValueError:
            continue
        links.append((technique_id, name, url))
    return links
