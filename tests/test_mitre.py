import pytest

from soc.mitre import technique_links, technique_url
from soc.models import Mitre


def test_technique_url():
    assert technique_url("T1110") == "https://attack.mitre.org/techniques/T1110/"


def test_sub_technique_url():
    assert (
        technique_url("T1059.001")
        == "https://attack.mitre.org/techniques/T1059/001/"
    )


@pytest.mark.parametrize("bad_id", ["", "1110", "T11", "T1059.1", "X1110", "T1110/"])
def test_invalid_technique_id_is_rejected(bad_id):
    with pytest.raises(ValueError):
        technique_url(bad_id)


def test_technique_links_pairs_ids_with_names():
    mitre = Mitre(id=["T1059.001", "T1027"], technique=["PowerShell", "Obfuscation"])
    assert technique_links(mitre) == [
        ("T1059.001", "PowerShell", "https://attack.mitre.org/techniques/T1059/001/"),
        ("T1027", "Obfuscation", "https://attack.mitre.org/techniques/T1027/"),
    ]


def test_technique_links_empty_when_no_mitre_data():
    assert technique_links(Mitre()) == []


def test_technique_links_skips_invalid_ids():
    assert technique_links(Mitre(id=["nonsense"], technique=["x"])) == []
