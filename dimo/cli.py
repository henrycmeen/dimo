import argparse
import subprocess
import sys
from dimo.update_mets import update_dias_mets
from dimo.report import generate_report
from dimo import __version__
from typing import Optional
from enum import Enum
import typer
from rich.console import Console
from rich.table import Table
from dimo.tester.n5.test_n5 import run_n5_test

app = typer.Typer()

class ReportFormat(str, Enum):
    text = "text"
    json = "json"
    html = "html"

@app.callback(invoke_without_command=True)
def callback(ctx: typer.Context):
    """DIMO - Digital Archive Management Tools"""
    if ctx.invoked_subcommand is None:
        console = Console()
        console.print("\n[bold cyan]DIMO - Digital Archive Management Tools[/]\n")
        
        commands_table = Table(show_header=False, box=None)
        commands_table.add_column(style="cyan")
        commands_table.add_column()
        commands_table.add_row("version", "Show version information")
        commands_table.add_row("update", "Update DIMO to the latest version")
        commands_table.add_row("update-mets", "Update dias-METS file with correct paths and checksums")
        commands_table.add_row("report", "Generate reports about files and content")
        console.print(commands_table)
        console.print()

@app.command()
def version(check: bool = typer.Option(False, help="Check for updates")):
    """Show version information"""
    typer.echo(f"DIMO version {__version__}")
    if check:
        typer.echo("Checking for updates...")

@app.command()
def update():
    """Update DIMO to the latest version"""
    typer.echo("Updating DIMO to the latest version...")
    try:
        subprocess.check_call([
            sys.executable, "-m", "pip", "install", "--upgrade",
            "git+https://github.com/henrycmeen/dimo.git"
        ])
        typer.echo("Successfully updated DIMO!")
    except subprocess.CalledProcessError as e:
        typer.echo(f"Error updating DIMO: {e}", err=True)
        sys.exit(1)

@app.command("update-mets")
def update_mets(
    mets_file: str = typer.Option("dias-mets.xml", help="METS file to update"),
    content_dir: str = typer.Option("content", help="Content directory"),
    dry_run: bool = typer.Option(False, help="Run without writing changes to file")
):
    """Update dias-METS file with correct paths and checksums"""
    update_dias_mets(mets_file, content_dir, dry_run=dry_run)

@app.command()
def report(
    path: str = typer.Option(".", help="Path to analyze"),
    format: ReportFormat = typer.Option(ReportFormat.text, help="Output format")
):
    """Generate reports about files and content"""
    generate_report(path=path, format=format.value)

def display_test_results(results: dict, standard: str):
    """Helper function to display test results in a consistent format"""
    console = Console()
    console.print(f"\n[bold cyan]{standard.upper()} Test Results[/]\n")
    for test_id, test_data in results.items():
        console.print(f"[bold]{test_id}[/]")
        console.print(test_data)
        console.print()

@app.command("test")
def test(
    standard: str = typer.Option(..., help="Standard to test against (n5, siard, etc.)"),
    test_name: Optional[str] = typer.Option(None, help="Test to run (e.g., '01', 'all')"),
):
    """Run tests for different archive standards"""
    try:
        from dimo.test import run_test
        results = run_test(standard, test_name)
        display_test_results(results, standard)
    except Exception as e:
        typer.echo(f"Error running {standard} test: {e}", err=True)
        sys.exit(1)

if __name__ == "__main__":
    app()