import shutil
from pathlib import Path

import main as cli

SAMPLE = Path(__file__).resolve().parent.parent / "data" / "sample_alerts.jsonl"


def args(tmp_path, *extra):
    return [
        "--input", str(SAMPLE),
        "--out", str(tmp_path / "reports"),
        "--state", str(tmp_path / "state.json"),
        *extra,
    ]


def test_cli_success_returns_zero(tmp_path, capsys):
    assert cli.main(args(tmp_path)) == 0
    assert "Processed 6, skipped 0, failed 0" in capsys.readouterr().out


def test_cli_second_run_skips(tmp_path, capsys):
    cli.main(args(tmp_path))
    capsys.readouterr()
    assert cli.main(args(tmp_path)) == 0
    assert "Processed 0, skipped 6, failed 0" in capsys.readouterr().out
