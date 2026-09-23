"""Unit tests for flash_ledger.cli."""

from typer.testing import CliRunner
from flash_ledger.cli import app

runner = CliRunner()

def test_cli_version():
    result = runner.invoke(app, ["--version"])
    assert result.exit_code == 0
    assert "0.1.0" in result.stdout

def test_cli_coa():
    result = runner.invoke(app, ["coa"])
    assert result.exit_code == 0
    assert "Software/SaaS" in result.stdout
    assert "Meals & Entertainment" in result.stdout

def test_cli_classify_help():
    result = runner.invoke(app, ["classify", "--help"])
    assert result.exit_code == 0
    assert "--format" in result.stdout

def test_cli_benchmark():
    result = runner.invoke(app, ["benchmark", "--count", "50"])
    assert result.exit_code == 0
    assert "Benchmark Complete" in result.stdout or "Transactions" in result.stdout

def test_cli_classify_file(tmp_path):
    csv_file = tmp_path / "test.csv"
    csv_file.write_text(
        "Date,Description,Amount\n"
        "2026-03-15,SQ *BLUE BOTTLE SOMA,14.20\n"
        "2026-03-16,AWS CLOUD SERVICES,150.00\n"
    )
    out_file = tmp_path / "out.csv"
    result = runner.invoke(app, ["classify", str(csv_file), "--output", str(out_file), "--format", "qbo"])
    assert result.exit_code == 0
    assert out_file.exists()
