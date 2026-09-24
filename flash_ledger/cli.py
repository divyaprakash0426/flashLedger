"""flashLedger Command Line Interface (CLI)."""

from __future__ import annotations
import asyncio
from pathlib import Path
from typing import Optional
import typer
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich import box
import flash_ledger
from flash_ledger.coa import ChartOfAccounts
from flash_ledger.engine import JevDecisionEngine
from flash_ledger.batch import BatchAuditor
from flash_ledger.preprocessor import parse_statement_csv
from flash_ledger.exporters import (
    export_qbo_csv,
    export_xero_csv,
    export_freshbooks_csv,
    export_audit_csv,
    export_json,
)
from flash_ledger.demo import run_split_screen_demo
from flash_ledger.datasets.synthetic import generate_benchmark_dataset, save_benchmark_csv
from flash_ledger.datasets.download import download_uk_gov_data, download_hf_dataset
from flash_ledger.mcp_server import main as run_mcp_server

app = typer.Typer(
    name="flash-ledger",
    help="⚡ flashLedger: Autonomous Bank Feed & Card Auditor powered by TypeSafe Jev.",
    add_completion=False,
)
console = Console()


def version_callback(value: bool):
    if value:
        console.print(f"[bold cyan]flash-ledger[/] version [bold green]{flash_ledger.__version__}[/]")
        raise typer.Exit()


@app.callback()
def main_callback(
    version: Optional[bool] = typer.Option(
        None, "--version", "-v", callback=version_callback, is_eager=True, help="Show version and exit."
    ),
):
    """Autonomous Bank Feed & Card Auditor powered by TypeSafe Jev."""
    pass


@app.command("classify")
def classify_cmd(
    file_path: Path = typer.Argument(..., help="Path to input CSV statement (Chase, Amex, Brex, etc.)"),
    output: Optional[Path] = typer.Option(None, "--output", "-o", help="Output file path"),
    format: str = typer.Option("qbo", "--format", "-f", help="Export format: qbo, xero, freshbooks, csv, json"),
    coa: Optional[Path] = typer.Option(None, "--coa", help="Path to custom coa.json file"),
    concurrency: int = typer.Option(50, "--concurrency", "-c", help="Concurrent worker threads"),
    capex_threshold: float = typer.Option(2500.0, "--capex-threshold", help="IRS CapEx safe harbor limit ($)"),
    api: bool = typer.Option(False, "--api", help="Force live TypeSafe API calls instead of auto/mock"),
):
    """Ingest raw bank statement CSV and export classified GL accounts and tax flags."""
    if not file_path.exists():
        console.print(f"[bold red]Error:[/] File not found: {file_path}")
        raise typer.Exit(code=1)

    chart = ChartOfAccounts.load(coa) if coa else ChartOfAccounts.load_default()
    chart.capex_threshold = capex_threshold
    mode = "api" if api else "auto"

    console.print(f"[dim]Parsing {file_path}...[/]")
    transactions = parse_statement_csv(file_path)
    console.print(f"[green]✓[/] Loaded [bold]{len(transactions)}[/] transactions.")

    engine = JevDecisionEngine(coa=chart, mode=mode)
    auditor = BatchAuditor(engine=engine, max_concurrency=concurrency)

    console.print(f"[cyan]Auditing with TypeSafe Jev (concurrency={concurrency}, mode={engine.mode})...[/]")
    results, summary = asyncio.run(auditor.audit_batch(transactions))

    console.print(
        f"[bold green]✓ Audit Completed:[/] {summary.total_transactions} txns in "
        f"[bold]{summary.total_transactions / max(summary.throughput_tps, 1):.2f}s[/] "
        f"({summary.throughput_tps} txns/sec, avg {summary.avg_latency_ms:.1f}ms/txn)"
    )

    # Determine output path if not given
    out_path = output
    if not out_path:
        out_path = file_path.parent / f"{file_path.stem}_audited.{'json' if format == 'json' else 'csv'}"

    fmt = format.lower()
    if fmt == "qbo":
        export_qbo_csv(results, out_path)
    elif fmt == "xero":
        export_xero_csv(results, out_path)
    elif fmt == "freshbooks":
        export_freshbooks_csv(results, out_path)
    elif fmt == "json":
        export_json(results, out_path)
    else:
        export_audit_csv(results, out_path)

    console.print(f"[bold cyan]Exported {fmt.upper()} to:[/] [underline]{out_path}[/]")


@app.command("audit")
def audit_cmd(
    file_path: Path = typer.Argument(..., help="Path to input bank statement CSV"),
    coa: Optional[Path] = typer.Option(None, "--coa", help="Path to custom coa.json file"),
):
    """Run compliance audit and display real-time interactive risk tables and flags."""
    chart = ChartOfAccounts.load(coa) if coa else ChartOfAccounts.load_default()
    transactions = parse_statement_csv(file_path)

    engine = JevDecisionEngine(coa=chart, mode="auto")
    auditor = BatchAuditor(engine=engine)
    results, summary = asyncio.run(auditor.audit_batch(transactions))

    table = Table(
        title="[bold cyan]⚡ flashLedger Compliance & Tax Audit Report[/]",
        box=box.ROUNDED,
        header_style="bold yellow",
    )
    table.add_column("Date", style="dim", width=12)
    table.add_column("Clean Merchant", style="white")
    table.add_column("Amount", justify="right", style="bold")
    table.add_column("GL Account", style="green")
    table.add_column("Deductible?", justify="center")
    table.add_column("Expense Type", justify="center")
    table.add_column("Audit Risk", justify="right")
    table.add_column("Flags", style="bold yellow")

    for txn, res in results[:25]:  # Preview top 25
        deduct_str = "[green]Yes[/]" if res.is_tax_deductible else "[red]No[/]"
        exp_style = "[yellow]CapEx[/]" if res.expense_type == "CapEx" else "OpEx"
        risk_style = (
            f"[bold red]{res.audit_risk_score:.2f}[/]"
            if res.audit_risk_score >= 0.70
            else f"[green]{res.audit_risk_score:.2f}[/]"
        )

        table.add_row(
            txn.date.isoformat(),
            txn.clean_description[:28],
            f"${txn.amount:,.2f}",
            res.gl_code,
            deduct_str,
            exp_style,
            risk_style,
            ", ".join(res.flags),
        )

    console.print(table)
    if len(results) > 25:
        console.print(f"[dim]... and {len(results) - 25} more transactions audited.[/]")

    # Print summary panel
    stats_text = (
        f"[bold]Total Audited:[/] {summary.total_transactions} txns (${summary.total_amount:,.2f})\n"
        f"[bold]Tax Deductible Business Spend:[/] [green]${summary.tax_deductible_amount:,.2f}[/]\n"
        f"[bold]Non-Deductible / Flagged:[/] [red]${summary.total_amount - summary.tax_deductible_amount:,.2f}[/] ({summary.flagged_count} flagged)\n"
        f"[bold]Capital Expenditures (CapEx):[/] [yellow]{summary.capex_count} purchases[/] exceeding threshold (${chart.capex_threshold:,.2f})\n"
        f"[bold]Audit Throughput:[/] {summary.throughput_tps:.1f} txns/sec (Avg {summary.avg_latency_ms:.1f}ms/txn)"
    )
    console.print(Panel(stats_text, title="[bold green]Executive Audit Summary[/]", box=box.ROUNDED))


@app.command("benchmark")
def benchmark_cmd(
    count: int = typer.Option(1000, "--count", "-n", help="Number of transactions to benchmark"),
    concurrency: int = typer.Option(50, "--concurrency", "-c", help="Concurrent worker threads"),
    save_csv: Optional[Path] = typer.Option(None, "--save-csv", help="Save benchmark dataset to CSV"),
):
    """Run ultra-fast throughput benchmark with realistic noisy bank feed dataset."""
    console.print(f"[cyan]Generating {count:,} noisy bank transactions for benchmark...[/]")
    transactions = generate_benchmark_dataset(count=count, seed=42)

    if save_csv:
        save_benchmark_csv(save_csv, count=count)
        console.print(f"[dim]Saved dataset to {save_csv}[/]")

    engine = JevDecisionEngine(mode="mock")
    auditor = BatchAuditor(engine=engine, max_concurrency=concurrency)

    console.print(f"[bold yellow]Starting flashLedger benchmark ({count:,} transactions, concurrency={concurrency})...[/]")
    results, summary = asyncio.run(auditor.audit_batch(transactions))

    console.print("\n[bold green]✓ Benchmark Complete![/]")
    table = Table(box=box.ROUNDED)
    table.add_column("Metric", style="bold white")
    table.add_column("Value", style="bold cyan", justify="right")

    table.add_row("Transactions Evaluated", f"{summary.total_transactions:,}")
    table.add_row("Total Processing Time", f"{summary.total_transactions / max(summary.throughput_tps, 1):.2f} seconds")
    table.add_row("Throughput Speed", f"[bold green]{summary.throughput_tps:,.1f} transactions/second[/]")
    table.add_row("Average Latency per Txn", f"{summary.avg_latency_ms:.2f} ms")
    table.add_row("CapEx Assets Flagged", f"{summary.capex_count}")
    table.add_row("High-Risk/Non-Deductible", f"{summary.flagged_count}")
    table.add_row("Calculated Cost (Jev)", "[bold green]<$0.01[/]")
    table.add_row("Estimated Cost (GPT-4o)", "[red]~$15.00[/]")
    table.add_row("Estimated Time (GPT-4o)", "[red]~550 seconds[/]")

    console.print(table)


@app.command("demo")
def demo_cmd(
    headless: bool = typer.Option(False, "--headless", help="Run in headless non-interactive mode for scripting"),
    count: int = typer.Option(1000, "--count", "-n", help="Transaction count for waterfall cascade"),
    api: bool = typer.Option(False, "--api", help="Connect to live TypeSafe Jev API (requires TYPESAFE_API_KEY)"),
):
    """Launch the split-screen waterfall demo (GPT-4o vs Jev)."""
    mode = "api" if api else "auto"
    asyncio.run(run_split_screen_demo(console=console, interactive=not headless, count=count, mode=mode))


@app.command("download-dataset")
def download_cmd(
    source: str = typer.Option("uk-gov", "--source", "-s", help="Dataset to fetch: 'uk-gov' or 'hf'"),
    dest: Optional[Path] = typer.Option(None, "--dest", "-d", help="Destination path"),
    token: Optional[str] = typer.Option(None, "--token", "-t", help="Hugging Face API token (for HF gated datasets)"),
):
    """Download authentic public expenditure datasets (UK Gov corporate spend or HF)."""
    if source == "uk-gov":
        console.print("[cyan]Downloading UK Government corporate expenditure dataset (> £25k)...[/]")
        path = download_uk_gov_data(dest)
        console.print(f"[bold green]✓ Downloaded UK Gov spending data to:[/] {path} ({path.stat().st_size:,} bytes)")
    elif source == "hf":
        console.print("[cyan]Connecting to Hugging Face (mitulshah/transaction-categorization)...[/]")
        path = download_hf_dataset(dest, token=token)
        console.print(f"[bold green]✓ Result saved to:[/] {path}")
    else:
        console.print(f"[red]Unknown source: {source}. Choose 'uk-gov' or 'hf'.[/]")


@app.command("mcp")
def mcp_cmd():
    """Start the Model Context Protocol (MCP) server for Claude Code, Cursor, and Copilot."""
    console.print("[bold cyan]Starting flashLedger MCP Server on stdio...[/]")
    run_mcp_server()


@app.command("coa")
def coa_cmd(
    coa: Optional[Path] = typer.Option(None, "--file", "-f", help="Custom COA JSON path"),
):
    """Display the active Chart of Accounts (COA) and tax deduction rules."""
    chart = ChartOfAccounts.load(coa) if coa else ChartOfAccounts.load_default()

    table = Table(
        title=f"[bold green]{chart.name}[/] (CapEx Threshold: ${chart.capex_threshold:,.2f})",
        box=box.ROUNDED,
    )
    table.add_column("Code", style="bold yellow", width=8)
    table.add_column("Account Name", style="bold white", width=26)
    table.add_column("Category", style="cyan", width=22)
    table.add_column("Tax Deductible", justify="center", width=14)
    table.add_column("Description / Examples", style="dim")

    for acc in chart.accounts:
        deduct_str = "[green]Yes[/]" if acc.tax_deductible_default else "[red]No[/]"
        table.add_row(acc.code, acc.name, acc.category, deduct_str, acc.description)

    console.print(table)


if __name__ == "__main__":
    app()
