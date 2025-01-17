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


@app.command()
def watch(patterns: List[str] = typer.Argument(..., help="File patterns to watch (supports glob)")):
    """Add files/directories to watch list for continuous monitoring."""
    new_patterns, added_files = context_manager.watch_paths(patterns)

    if new_patterns > 0:
        console.print(
            f"[green]Added [bold]{new_patterns}[/bold] new pattern(s) to watch list.[/green]"
        )
    else:
        console.print("[yellow]All patterns were already being watched.[/yellow]")

    if added_files > 0:
        console.print(
            f"[green]Initially added [bold]{added_files}[/bold] files to context.[/green]"
        )

    console.print(get_file_tree(context_manager.files, context_manager.base_dir))


@app.command()
def unwatch(patterns: List[str] = typer.Argument(..., help="File patterns to stop watching")):
    """Remove patterns from watch list but keep existing files."""
    removed_patterns, kept_files = context_manager.unwatch_paths(patterns)

    if removed_patterns > 0:
        console.print(
            f"[green]Removed [bold]{removed_patterns}[/bold] pattern(s) from watch list.[/green]"
        )
        console.print(
            f"[blue]Keeping [bold]{kept_files}[/bold] existing files in context.[/blue]"
        )
    else:
        console.print("[yellow]No matching patterns were being watched.[/yellow]")


@app.command(name="watch-list")
def watch_list():
    """List all patterns currently being watched."""
    patterns = context_manager.list_watched()
    if patterns:
        table = Table("Watched Patterns", style="bold green")
        for pattern in patterns:
            table.add_row(pattern)
        console.print(table)
    else:
        console.print("[yellow]No patterns are currently being watched[/yellow]")


@app.command(name="rexp")
def refresh_and_export(
        relative: bool = typer.Option(True, help="Export relative paths instead of absolute"),
        full: bool = typer.Option(True, help="Include file contents in the export"),
):
    """Refresh watched paths and immediately export the results."""
    # First refresh
    stats = context_manager.refresh_watched()

    if stats["added"] > 0 or stats["removed"] > 0:
        if stats["added"] > 0:
            console.print(
                f"[green]Added [bold]{stats['added']}[/bold] new files.[/green]"
            )
        if stats["removed"] > 0:
            console.print(
                f"[yellow]Removed [bold]{stats['removed']}[/bold] files that no longer exist.[/yellow]"
            )
    else:
        console.print("[blue]No changes detected in watched paths.[/blue]")

    # Then export
    if not context_manager.files:
        console.print("[red]No files in context to export![/red]")
        return

    # Format and export the content
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
def refresh():
    """Update context by refreshing all watched paths."""
    stats = context_manager.refresh_watched()

    if stats["added"] > 0 or stats["removed"] > 0:
        if stats["added"] > 0:
            console.print(
                f"[green]Added [bold]{stats['added']}[/bold] new files.[/green]"
            )
        if stats["removed"] > 0:
            console.print(
                f"[yellow]Removed [bold]{stats['removed']}[/bold] files that no longer exist.[/yellow]"
            )
        console.print("\nCurrent context:")
        console.print(get_file_tree(context_manager.files, context_manager.base_dir))
    else:
        console.print("[blue]No changes detected in watched paths.[/blue]")


@app.command(name="save-as")
def save_state_as(
        name: str = typer.Argument(..., help="Name for the saved state")
):
    """Save current context state to a named file."""
    if context_manager.save_state_as(name):
        console.print(f"[green]Successfully saved state as: {name}[/green]")
    else:
        console.print(f"[red]Failed to save state: {name}[/red]")


@app.command(name="load")
def load_state(
        name: str = typer.Argument(..., help="Name of the state to load")
):
    """Load a previously saved context state."""
    if context_manager.load_state(name):
        console.print(f"[green]Successfully loaded state: {name}[/green]")
        console.print("\nCurrent context:")
        console.print(get_file_tree(context_manager.files, context_manager.base_dir))
    else:
        console.print(f"[red]Failed to load state: {name}[/red]")


@app.command(name="states")
def list_states():
    """List all saved states."""
    states = context_manager.list_saved_states()
    if states:
        table = Table("Saved States", style="bold green")
        for state in sorted(states):
            table.add_row(state)
        console.print(table)
    else:
        console.print("[yellow]No saved states found[/yellow]")


@app.command(name="delete-state")
def delete_state(
        name: str = typer.Argument(..., help="Name of the state to delete")
):
    """Delete a saved state."""
    if context_manager.delete_state(name):
        console.print(f"[green]Successfully deleted state: {name}[/green]")
    else:
        console.print(f"[red]Failed to delete state: {name}[/red]")

def main():
    """Entrypoint for the CLI."""
    app()

if __name__ == "__main__":
    main()