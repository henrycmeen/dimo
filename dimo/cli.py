import argparse
import subprocess
import sys
from dimo.update_mets import update_dias_mets
from dimo.report import generate_report
from dimo import __version__
from typing import Optional
from enum import Enum

class CustomFormatter(argparse.HelpFormatter):
    def _format_action_invocation(self, action):
        if not action.option_strings:
            default = self._get_default_metavar_for_positional(action)
            metavar = action.metavar or default
            return metavar
        else:
            parts = []
            if action.nargs == 0:
                parts.extend(action.option_strings)
            else:
                default = self._get_default_metavar_for_optional(action)
                args_string = self._format_args(action, default)
                for option_string in action.option_strings:
                    parts.append('%s %s' % (option_string, args_string))
            return ', '.join(parts)

import typer
from rich.console import Console
from rich.table import Table
import subprocess
import sys
from dimo.update_mets import update_dias_mets
from dimo.report import generate_report
from dimo import __version__
from typing import Optional
from enum import Enum

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

if __name__ == "__main__":
    app()