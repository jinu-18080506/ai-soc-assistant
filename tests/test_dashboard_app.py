from pathlib import Path

import pytest

pytest.importorskip("streamlit", reason="dashboard dependencies not installed")
from streamlit.testing.v1 import AppTest  # noqa: E402

APP = Path(__file__).resolve().parent.parent / "dashboard" / "app.py"


def test_dashboard_starts_without_errors():
    app = AppTest.from_file(str(APP), default_timeout=30).run()
    assert not app.exception
    assert app.title[0].value == "AI SOC Assistant"
    assert len(app.metric) == 5


def test_missing_alerts_file_shows_an_error():
    app = AppTest.from_file(str(APP), default_timeout=30).run()
    app.sidebar.text_input[0].set_value("no/such/file.jsonl").run()
    assert not app.exception
    assert any("not found" in error.value for error in app.error)


def test_severity_filter_changes_the_table():
    app = AppTest.from_file(str(APP), default_timeout=30).run()
    app.multiselect[0].set_value(["Critical"]).run()
    assert not app.exception
    assert any("Showing 1 of 6" in caption.value for caption in app.caption)
