from pathlib import Path

import pytest

import main as cli

SAMPLE = Path(__file__).resolve().parent.parent / "data" / "sample_alerts.jsonl"


@pytest.fixture(autouse=True)
def clean_environment(monkeypatch):
    """Make sure a real key on this machine can never leak into the tests."""
    for name in ("AI_API_KEY", "AI_BASE_URL", "AI_MODEL"):
        monkeypatch.delenv(name, raising=False)


def args(tmp_path, *extra):
    return [
        "--input", str(SAMPLE),
        "--out", str(tmp_path / "reports"),
        "--state", str(tmp_path / "state.json"),
        "--env-file", str(tmp_path / "no-such.env"),
        *extra,
    ]


def test_cli_success_returns_zero(tmp_path, capsys):
    assert cli.main(args(tmp_path, "--mock")) == 0
    assert "Processed 6, skipped 0, failed 0" in capsys.readouterr().out


def test_cli_second_run_skips(tmp_path, capsys):
    cli.main(args(tmp_path, "--mock"))
    capsys.readouterr()
    assert cli.main(args(tmp_path, "--mock")) == 0
    assert "Processed 0, skipped 6, failed 0" in capsys.readouterr().out


def test_no_key_falls_back_to_mock(tmp_path, capsys):
    assert cli.main(args(tmp_path)) == 0
    assert "mock AI" in capsys.readouterr().out


def test_key_without_model_is_reported(tmp_path, monkeypatch, capsys):
    monkeypatch.setenv("AI_API_KEY", "dummy-key")
    assert cli.main(args(tmp_path)) == 2
    assert "AI_MODEL is empty" in capsys.readouterr().out


def test_list_models_without_key_is_reported(tmp_path, capsys):
    assert cli.main(args(tmp_path, "--list-models")) == 2
    assert "AI_API_KEY is not set" in capsys.readouterr().out


def test_key_is_never_printed(tmp_path, monkeypatch, capsys):
    monkeypatch.setenv("AI_API_KEY", "super-secret-key-123")
    cli.main(args(tmp_path))
    out = capsys.readouterr()
    assert "super-secret-key-123" not in out.out + out.err
