#!/usr/bin/env python3
import typer
import pyperclip
from rich.console import Console
from rich.table import Table
from typing import List

from .manager import ContextManager
from .formatters import get_file_tree, format_export_content

app = typer.Typer(help="Context CLI - Manage files and export to clipboard")
console = Console()

VERSION = "0.1.1"

# Global context manager instance
context_manager = ContextManager()

@app.command()
def add(patterns: List[str] = typer.Argument(..., help="File patterns to add (supports glob)")):
    """Add files/directories to the context."""
    added_count = context_manager.add_files(patterns)
    console.print(
        f"[green]Added [bold]{added_count}[/bold] files/directories to context.[/green]"
    )
    console.print(get_file_tree(context_manager.files, context_manager.base_dir))

@app.command()
def remove(patterns: List[str] = typer.Argument(..., help="File patterns to remove (supports glob)")):
    """Remove files/directories from the context."""
    removed_count = context_manager.remove_files(patterns)
    console.print(
        f"[red]Removed [bold]{removed_count}[/bold] files/directories from context.[/red]"
    )
    console.print(get_file_tree(context_manager.files, context_manager.base_dir))

@app.command()
def clear():
    """Clear all files from the context."""
    context_manager.clear_context()
    console.print("[yellow]Context cleared![/yellow]")

@app.command(name="list")
def list_command():
    """List all files in the context (in a tree view)."""
    console.print(get_file_tree(context_manager.files, context_manager.base_dir))

@app.command()
def export(
        relative: bool = typer.Option(True, help="Export relative paths instead of absolute"),
        full: bool = typer.Option(True, help="Include file contents in the export"),
):
    """
    Export the current context to the clipboard.

    By default, exports relative paths and includes file contents.
    Use --no-relative for absolute paths.
    Use --no-full to exclude file contents.
    """
    if not context_manager.files:
        console.print("[red]No files in context to export![/red]")
        return

    # Format the content for export
    output_text = format_export_content(
        context_manager.files,
        context_manager.base_dir,
        relative=relative,
        include_contents=full
    )

    # Copy to clipboard
    pyperclip.copy(output_text)

    console.print(
        f"[green]Exported {len(context_manager.files)} files to clipboard "
        f"{'with contents' if full else '(paths only)'}![/green]"
    )

@app.command()
def search(keyword: str):
    """Search for files in the context containing the given keyword in their path."""
    matches = context_manager.search_files(keyword)

    if matches:
        table = Table("Matched Files", style="bold green")
        for m in sorted(matches):
            table.add_row(m)
        console.print(table)
    else:
        console.print(f"[red]No files in context match keyword: '{keyword}'[/red]")

@app.command()
def version():
    """Print version information."""
    console.print(f"[bold green]Context CLI v{VERSION}[/bold green]")

@app.command()
def ignore(
        pattern: str = typer.Argument(..., help="Pattern to add to .ignore file"),
        rescan: bool = typer.Option(True, help="Rescan directories after removing ignored files")
):
    """Add a pattern to .ignore file and update current context."""
    removed_files, cleaned_dirs = context_manager.add_ignore_pattern(pattern)
    console.print(f"[green]Added pattern to .ignore: {pattern}[/green]")

    if removed_files:
        console.print(f"[yellow]Removed {removed_files} existing files matching pattern[/yellow]")

    if cleaned_dirs:
        console.print(f"[blue]Rescanned {cleaned_dirs} directories for new valid files[/blue]")

    # Show the updated context
    console.print(get_file_tree(context_manager.files, context_manager.base_dir))

@app.command()
def unignore(
        pattern: str = typer.Argument(..., help="Pattern to remove from .ignore file"),
):
    """Remove a pattern from .ignore file."""
    if context_manager.remove_ignore_pattern(pattern):
        console.print(f"[green]Removed pattern from .ignore: {pattern}[/green]")
    else:
        console.print(f"[yellow]Pattern not found in .ignore: {pattern}[/yellow]")

@app.command(name="ignore-list")
def ignore_list():
    """List all patterns in .ignore file."""
    patterns = context_manager.list_ignore_patterns()
    if patterns:
        table = Table("Ignore Patterns", style="bold green")
        for pattern in patterns:
            table.add_row(pattern)
        console.print(table)
    else:
        console.print("[yellow]No patterns in .ignore file[/yellow]")

@app.command(name="gitignore-sync")
def gitignore_sync():
    """Sync patterns from .gitignore to .ignore file."""
    if not (context_manager.base_dir / ".gitignore").exists():
        console.print("[red]No .gitignore file found in current directory![/red]")
        return

    added_count, new_patterns = context_manager.sync_gitignore()

    if added_count > 0:
        console.print(f"[green]Added {added_count} new patterns from .gitignore:[/green]")
        table = Table("New Patterns", style="bold green")
        for pattern in new_patterns:
            table.add_row(pattern)
        console.print(table)
    else:
        console.print("[yellow]No new patterns to sync from .gitignore[/yellow]")

@app.command()
def init():
    """Initialize contextr in the current directory."""
    created_dir, updated_gitignore = context_manager.initialize()

    if created_dir:
        console.print("[green]Created .contextr directory[/green]")
    else:
        console.print("[yellow].contextr directory already exists[/yellow]")

    if updated_gitignore:
        console.print("[green]Added .contextr/ to .gitignore[/green]")
    elif (context_manager.base_dir / ".gitignore").exists():
        console.print("[yellow].contextr already in .gitignore[/yellow]")
    else:
        console.print("[yellow]No .gitignore file found to update[/yellow]")

def main():
    """Entrypoint for the CLI."""
    app()

if __name__ == "__main__":
    main()