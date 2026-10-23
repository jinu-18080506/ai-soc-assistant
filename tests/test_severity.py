import pytest

from soc.severity import Severity, severity_for_level


@pytest.mark.parametrize(
    ("level", "expected"),
    [
        (0, Severity.LOW),
        (3, Severity.LOW),
        (4, Severity.MEDIUM),
        (7, Severity.MEDIUM),
        (8, Severity.HIGH),
        (11, Severity.HIGH),
        (12, Severity.CRITICAL),
        (15, Severity.CRITICAL),
    ],
)
def test_level_maps_to_expected_severity(level, expected):
    assert severity_for_level(level) == expected


@pytest.mark.parametrize("level", [-1, 16, 100])
def test_out_of_range_level_is_rejected(level):
    with pytest.raises(ValueError):
        severity_for_level(level)
