#!/usr/bin/env python3
from typing import List

import pyperclip
import typer
from rich.console import Console
from rich.table import Table

from .formatters import format_export_content, get_file_tree
from .manager import ContextManager
from .profile import ProfileManager

app = typer.Typer(help="ctxr - Share your codebase with Large Language Models")
console = Console()

VERSION = "1.0.0"

# Global context manager instance
context_manager = ContextManager()


@app.command()
def watch(
    patterns: List[str] = typer.Argument(
        ..., help="File patterns to watch (supports glob)"
    ),
) -> None:
    """
    Add files to context and monitor them for changes.

    Example: ctxr watch "src/**/*.py" "*.md"
    """
    new_patterns, added_files = context_manager.watch_paths(patterns)

    if new_patterns > 0:
        console.print(
            f"[green]Added [bold]{new_patterns}[/bold] new pattern(s) to "
            "watch list.[/green]"
        )
    else:
        console.print("[yellow]All patterns were already being watched.[/yellow]")

    if added_files > 0:
        console.print(
            f"[green]Initially added [bold]{added_files}[/bold] files to "
            "context.[/green]"
        )

    console.print(get_file_tree(context_manager.files, context_manager.base_dir))


@app.command()
def ignore(
    pattern: str = typer.Argument(..., help="Pattern to add to .ignore file"),
) -> None:
    """
    Add a pattern to ignore list.

    Example: ctxr ignore "**/*.log"
    """
    removed_files, cleaned_dirs = context_manager.add_ignore_pattern(pattern)
    console.print(f"[green]Added pattern to .ignore: {pattern}[/green]")

    if removed_files:
        console.print(
            f"[yellow]Removed {removed_files} existing files matching pattern[/yellow]"
        )

    if cleaned_dirs:
        console.print(
            f"[blue]Rescanned {cleaned_dirs} directories for new valid files[/blue]"
        )

    # Show the updated context
    console.print(get_file_tree(context_manager.files, context_manager.base_dir))


@app.command(name="ignore-list")
def ignore_list() -> None:
    """
    List all ignored patterns.

    Example: ctxr ignore-list
    """
    patterns = context_manager.list_ignore_patterns()
    if patterns:
        table = Table("Ignore Patterns", style="bold green")
        for pattern in patterns:
            table.add_row(pattern)
        console.print(table)
    else:
        console.print("[yellow]No patterns in .ignore file[/yellow]")


@app.command(name="sync")
def sync() -> None:
    """
    Sync context from watched patterns and export to clipboard.

    Example: ctxr sync
    """
    # First refresh the context
    stats = context_manager.refresh_watched()

    if stats["added"] > 0 or stats["removed"] > 0:
        if stats["added"] > 0:
            console.print(
                f"[green]Added [bold]{stats['added']}[/bold] new files.[/green]"
            )
        if stats["removed"] > 0:
            console.print(
                f"[yellow]Removed [bold]{stats['removed']}[/bold] files that no "
                "longer exist.[/yellow]"
            )
    else:
        console.print("[blue]No changes detected in watched paths.[/blue]")

    # Then export to clipboard
    if not context_manager.files:
        console.print("[red]No files in context to export![/red]")
        return

    # Format and export the content
    output_text = format_export_content(
        context_manager.files,
        context_manager.base_dir,
        relative=True,
        include_contents=True,
    )

    # Copy to clipboard
    pyperclip.copy(output_text)

    console.print(
        f"[green]Exported {len(context_manager.files)} files to clipboard![/green]"
    )


@app.command(name="list")
def list_command() -> None:
    """
    List all files in the current context.

    Example: ctxr list
    """
    console.print(get_file_tree(context_manager.files, context_manager.base_dir))


@app.command(name="watch-list")
def watch_list() -> None:
    """
    List all patterns currently being watched.

    Example: ctxr watch-list
    """
    patterns = context_manager.list_watched()
    if patterns:
        table = Table("Watched Patterns", style="bold green")
        for pattern in patterns:
            table.add_row(pattern)
        console.print(table)
    else:
        console.print("[yellow]No patterns are currently being watched[/yellow]")


@app.command(name="unwatch")
def unwatch(
    patterns: List[str] = typer.Argument(..., help="File patterns to stop watching"),
) -> None:
    """
    Remove patterns from watch list.

    Example: ctxr unwatch "src/tests/**"
    """
    removed_patterns, kept_files = context_manager.unwatch_paths(patterns)

    if removed_patterns > 0:
        console.print(
            f"[green]Removed [bold]{removed_patterns}[/bold] pattern(s) from "
            "watch list.[/green]"
        )
        console.print(
            f"[blue]Keeping [bold]{kept_files}[/bold] existing files in context.[/blue]"
        )
    else:
        console.print("[yellow]No matching patterns were being watched.[/yellow]")


@app.command(name="unignore")
def unignore(
    pattern: str = typer.Argument(..., help="Pattern to remove from ignore list"),
) -> None:
    """
    Remove a pattern from ignore list.

    Example: ctxr unignore "**/*.log"
    """
    if context_manager.remove_ignore_pattern(pattern):
        console.print(f"[green]Removed pattern from ignore list: {pattern}[/green]")
    else:
        console.print(f"[yellow]Pattern not found in ignore list: {pattern}[/yellow]")


@app.command(name="gitignore-sync")
def gitignore_sync() -> None:
    """
    Sync patterns from .gitignore to ignore list.

    Example: ctxr gitignore-sync
    """
    if not (context_manager.base_dir / ".gitignore").exists():
        console.print("[red]No .gitignore file found in current directory![/red]")
        return

    added_count, new_patterns = context_manager.sync_gitignore()

    if added_count > 0:
        console.print(
            f"[green]Added {added_count} new patterns from .gitignore:[/green]"
        )
        table = Table("New Patterns", style="bold green")
        for pattern in new_patterns:
            table.add_row(pattern)
        console.print(table)
    else:
        console.print("[yellow]No new patterns to sync from .gitignore[/yellow]")


@app.command()
def init() -> None:
    """
    Initialize ctxr in the current directory.

    Example: ctxr init
    """
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

    console.print("\n[bold green]ctxr is ready to use![/bold green]")
    console.print("\nQuick start:")
    console.print('  1. Add files to watch: [bold]ctxr watch "src/**/*.py"[/bold]')
    console.print("  2. Sync to clipboard:  [bold]ctxr sync[/bold]")


@app.command()
def version() -> None:
    """Print version information."""
    console.print(f"[bold green]ctxr v{VERSION}[/bold green]")


# Create profile subcommand group
profile_app = typer.Typer(help="Manage context profiles")
app.add_typer(profile_app, name="profile")


@profile_app.command("save")
def profile_save(
    name: str = typer.Argument(..., help="Name for the profile"),
    description: str = typer.Option(
        "", "--description", "-d", help="Profile description"
    ),
    force: bool = typer.Option(
        False, "--force", "-f", help="Overwrite without confirmation"
    ),
) -> None:
    """
    Save current context as a named profile.

    Example: ctxr profile save frontend --description "Frontend development context"
    """
    # Create ProfileManager instance
    profile_manager = ProfileManager(context_manager.storage, context_manager.base_dir)

    # Get current context state
    watched_patterns = list(context_manager.watched_patterns)
    ignore_patterns = context_manager.list_ignore_patterns()

    # Check if profile exists and handle overwrite
    key = f"profiles/{name}"
    if context_manager.storage.exists(key) and not force:
        confirm = typer.confirm(f"Profile '{name}' already exists. Overwrite?")
        if not confirm:
            console.print("[yellow]Profile save cancelled.[/yellow]")
            return
        force = True

    # Save profile
    success = profile_manager.save_profile(
        name=name,
        watched_patterns=watched_patterns,
        ignore_patterns=ignore_patterns,
        description=description,
        force=force,
    )

    if success:
        console.print(f"[green]✓ Profile '{name}' saved successfully![/green]")
        if description:
            console.print(f"  Description: {description}")
        console.print(f"  Watched patterns: {len(watched_patterns)}")
        console.print(f"  Ignore patterns: {len(ignore_patterns)}")
    else:
        console.print(f"[red]Failed to save profile '{name}'[/red]")


@profile_app.command("list")
def profile_list() -> None:
    """
    List all saved profiles.

    Example: ctxr profile list
    """
    # Create ProfileManager instance
    profile_manager = ProfileManager(context_manager.storage, context_manager.base_dir)

    # Get all profiles
    profiles = profile_manager.list_profiles()

    if not profiles:
        console.print("[yellow]No saved profiles found.[/yellow]")
        console.print(
            "\nCreate your first profile with: [bold]ctxr profile save <name>[/bold]"
        )
        return

    # Display profiles table
    table = profile_manager.format_profiles_table(profiles)
    console.print(table)
    console.print(f"\n[dim]Total profiles: {len(profiles)}[/dim]")


def main() -> None:
    """Entrypoint for the CLI."""
    app()


if __name__ == "__main__":
    main()
