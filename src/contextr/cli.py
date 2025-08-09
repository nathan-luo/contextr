#!/usr/bin/env python3
from datetime import datetime
from typing import List, Optional

import pyperclip
import typer
from rich.console import Console
from rich.table import Table

from .formatters import format_export_content, get_file_tree
from .manager import ContextManager
from .profile import ProfileManager, ProfileNotFoundError

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
    Watch file patterns - matching files are automatically added to context.

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
    Refresh files from watched patterns and export to clipboard.

    Example: ctxr sync
    """
    # Refresh files and get accurate added/removed stats
    stats = context_manager.refresh_watched()
    total_added = stats.get("added", 0)
    files_removed = stats.get("removed", 0)

    # Show what changed
    if total_added > 0 or files_removed > 0:
        if total_added > 0:
            console.print(
                f"[green]Added [bold]{total_added}[/bold] files from "
                "watched patterns.[/green]"
            )
        if files_removed > 0:
            console.print(
                f"[yellow]Removed [bold]{files_removed}[/bold] files no "
                "longer matching patterns.[/yellow]"
            )
    else:
        console.print("[blue]Files are already in sync with watched patterns.[/blue]")

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
    try:
        pyperclip.copy(output_text)
    except Exception as e:
        console.print(f"[red]Clipboard error:[/red] {e}")
        return

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
    Remove patterns from watch list and their associated files.

    Example: ctxr unwatch "src/tests/**"
    """
    removed_patterns, removed_files = context_manager.unwatch_paths(patterns)

    if removed_patterns > 0:
        console.print(
            f"[green]Removed [bold]{removed_patterns}[/bold] pattern(s) from "
            "watch list.[/green]"
        )
        console.print(
            f"[yellow]Removed [bold]{removed_files}[/bold] associated files "
            "from context.[/yellow]"
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
        # Keep context consistent with watch patterns after ignore changes
        stats = context_manager.refresh_watched()
        if stats["added"] or stats["removed"]:
            console.print(
                f"[blue]Context updated: +{stats['added']} / -{stats['removed']}[/blue]"
            )
        if context_manager.files:
            console.print(
                get_file_tree(context_manager.files, context_manager.base_dir)
            )
    else:
        console.print(f"[yellow]Pattern not found in ignore list: {pattern}[/yellow]")


@app.command(name="gis")
def gis() -> None:
    """
    Sync patterns from .gitignore to ignore list.

    Example: ctxr gis
    """
    if not (context_manager.base_dir / ".gitignore").exists():
        console.print("[red]No .gitignore file found in current directory![/red]")
        return

    added_count, new_patterns = context_manager.sync_gitignore()

    if added_count > 0:
        console.print(
            f"[green]Added {added_count} new patterns from .gitignore:[/green]"
        )
        # List patterns without table for better readability
        for pattern in new_patterns[:10]:  # Show first 10
            console.print(f"  [green]+[/green] {pattern}")
        if len(new_patterns) > 10:
            console.print(
                f"  [dim]... and {len(new_patterns) - 10} more patterns[/dim]"
            )

        # Show total ignore patterns
        total_patterns = len(context_manager.list_ignore_patterns())
        console.print(f"\n[dim]Total ignore patterns now: {total_patterns}[/dim]")
    else:
        console.print("[yellow]No new patterns to sync from .gitignore[/yellow]")
        existing_count = len(context_manager.list_ignore_patterns())
        if existing_count > 0:
            console.print(
                f"[dim]All patterns already in ignore list "
                f"({existing_count} total)[/dim]"
            )


# Hidden alias for backward compatibility
@app.command(name="gitignore-sync", hidden=True)
def gitignore_sync() -> None:
    """
    (Deprecated) Use 'gis' instead. Sync patterns from .gitignore to ignore list.
    """
    gis()


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
def status() -> None:
    """
    Show current context status including profile and unsaved changes.

    Example: ctxr status
    """
    # Show current profile and dirty state
    profile_info = "None"
    if context_manager.current_profile_name:
        profile_info = context_manager.current_profile_name
        if context_manager.is_dirty:
            profile_info += " [yellow]*[/yellow]"  # Asterisk indicates unsaved changes

    console.print(f"[bold]Current Profile:[/bold] {profile_info}")

    # Show file and pattern counts
    console.print(f"[bold]Files in context:[/bold] {len(context_manager.files)}")
    console.print(
        f"[bold]Watched patterns:[/bold] {len(context_manager.watched_patterns)}"
    )
    console.print(
        f"[bold]Ignore patterns:[/bold] {len(context_manager.list_ignore_patterns())}"
    )

    # Show unsaved changes hint
    if context_manager.is_dirty and context_manager.current_profile_name:
        console.print(
            "\n[yellow]You have unsaved changes. "
            "Use 'ctxr profile save' to save.[/yellow]"
        )


@app.command()
def version() -> None:
    """Print version information."""
    console.print(f"[bold green]ctxr v{VERSION}[/bold green]")


# Create profile subcommand group
profile_app = typer.Typer(help="Manage context profiles")
app.add_typer(profile_app, name="profile")


@profile_app.command("save")
def profile_save(
    name: Optional[str] = typer.Argument(
        None, help="Name for the profile (defaults to current profile)"
    ),
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
    # Use current profile name if no name provided
    if name is None:
        if context_manager.current_profile_name:
            name = context_manager.current_profile_name
        else:
            console.print(
                "[red]No profile name provided and no current profile loaded.[/red]"
            )
            console.print("Usage: ctxr profile save <name>")
            return
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

        # Update profile tracking state
        context_manager.current_profile_name = name
        context_manager.reset_dirty_state()  # Reset dirty flag
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

    # Display profiles table with current profile indicator
    table = profile_manager.format_profiles_table(profiles)

    # Add current profile indicator
    if context_manager.current_profile_name:
        console.print(
            f"[bold]Current profile:[/bold] {context_manager.current_profile_name}"
        )
        if context_manager.is_dirty:
            console.print("[yellow]* You have unsaved changes[/yellow]")
        console.print()

    console.print(table)
    console.print(f"\n[dim]Total profiles: {len(profiles)}[/dim]")


@profile_app.command("load")
def profile_load(
    name: str = typer.Argument(..., help="Name of the profile to load"),
) -> None:
    """
    Load a previously saved profile to replace current context.

    Example: ctxr profile load frontend
    """
    # Create ProfileManager instance
    profile_manager = ProfileManager(context_manager.storage, context_manager.base_dir)

    try:
        # Load the profile
        profile = profile_manager.load_profile(name)

        # Apply the profile to the context
        context_manager.apply_profile(profile, name)

        # Display success message with loaded patterns summary
        console.print(f"[green]✓ Profile '{name}' loaded successfully![/green]")

        # Show profile details
        if profile.metadata.get("description"):
            console.print(f"  Description: {profile.metadata['description']}")

        console.print(f"  Watched patterns: {len(profile.watched_patterns)}")
        if profile.watched_patterns:
            for pattern in sorted(profile.watched_patterns)[:3]:
                console.print(f"    - {pattern}")
            if len(profile.watched_patterns) > 3:
                console.print(f"    ... and {len(profile.watched_patterns) - 3} more")

        console.print(f"  Ignore patterns: {len(profile.ignore_patterns)}")

        # Show the files now in context
        file_count = len(context_manager.files)
        console.print(f"\n[blue]Context updated with {file_count} files[/blue]")

        # Show file tree if not too many files
        if file_count > 0 and file_count <= 50:
            console.print(
                get_file_tree(context_manager.files, context_manager.base_dir)
            )
        elif file_count > 50:
            console.print(
                f"[dim]Use 'ctxr list' to see all {file_count} files in context[/dim]"
            )

    except ProfileNotFoundError:
        console.print(f"[red]Profile '{name}' not found.[/red]")
        console.print("\nUse 'ctxr profile list' to see available profiles.")
        raise typer.Exit(1)
    except Exception as e:
        console.print(f"[red]Error loading profile: {e}[/red]")
        raise typer.Exit(1)


@profile_app.command("delete")
def profile_delete(
    name: str = typer.Argument(..., help="Profile name to delete"),
    force: bool = typer.Option(False, "--force", "-f", help="Skip confirmation"),
) -> None:
    """
    Delete a saved profile.

    Example: ctxr profile delete frontend
    """
    # Create ProfileManager instance
    profile_manager = ProfileManager(context_manager.storage, context_manager.base_dir)

    try:
        # Load profile to show details before deletion
        profile = profile_manager.load_profile(name)

        # Show profile details before deletion prompt
        console.print(f"Profile: [cyan]{name}[/cyan]")
        if profile.metadata.get("description"):
            console.print(f"Description: {profile.metadata['description']}")
        console.print(f"Watched patterns: {len(profile.watched_patterns)}")
        console.print(f"Ignore patterns: {len(profile.ignore_patterns)}")

        # Format creation date
        created_at = profile.metadata.get("created_at", "")
        if created_at:
            try:
                dt = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
                created_str = dt.strftime("%Y-%m-%d %H:%M")
                console.print(f"Created: {created_str}")
            except ValueError:
                pass

        # Confirmation prompt
        if not force:
            confirm = typer.confirm(f"\nDelete profile '{name}'?")
            if not confirm:
                console.print("[yellow]Profile deletion cancelled.[/yellow]")
                raise typer.Abort()

        # Delete the profile
        success = profile_manager.delete_profile(name)

        if success:
            console.print(f"[green]✓ Profile '{name}' deleted successfully![/green]")
        else:
            console.print(f"[red]Failed to delete profile '{name}'[/red]")
            raise typer.Exit(1)

    except ProfileNotFoundError:
        console.print(f"[red]Profile '{name}' not found.[/red]")
        console.print("\nUse 'ctxr profile list' to see available profiles.")
        raise typer.Exit(1)
    except typer.Abort:
        raise
    except Exception as e:
        console.print(f"[red]Error deleting profile: {e}[/red]")
        raise typer.Exit(1)


@profile_app.command("new")
def profile_new(
    name: str = typer.Option(..., "--name", "-n", help="Profile name"),
    description: str = typer.Option(
        "", "--description", "-d", help="Profile description"
    ),
    gis: bool = typer.Option(False, "--gis", help="Sync gitignore patterns"),
    gitignore_sync: bool = typer.Option(
        False, "--gitignore-sync", help="Sync gitignore patterns (same as --gis)"
    ),
) -> None:
    """
    Create a new profile with interactive pattern entry.

    Example: ctxr profile new --name frontend --gis
    """
    # Check for unsaved changes
    if context_manager.is_dirty and context_manager.current_profile_name:
        response = typer.prompt(
            f"Save changes to profile '{context_manager.current_profile_name}'? "
            "[y/n/cancel]",
            type=str,
        )
        if response.lower() == "y":
            # Save current profile
            profile_manager = ProfileManager(
                context_manager.storage, context_manager.base_dir
            )
            profile_manager.save_profile(
                name=context_manager.current_profile_name,
                watched_patterns=list(context_manager.watched_patterns),
                ignore_patterns=context_manager.list_ignore_patterns(),
                force=True,
            )
            console.print(
                f"[green]✓ Saved changes to "
                f"'{context_manager.current_profile_name}'[/green]"
            )
        elif response.lower() == "cancel":
            console.print("[yellow]Profile creation cancelled.[/yellow]")
            raise typer.Abort()

    # Clear current context
    console.print("\n[blue]Starting new profile...[/blue]")
    context_manager.clear()

    # Combine gis and gitignore_sync flags
    sync_gitignore = gis or gitignore_sync

    # Sync gitignore if requested
    if sync_gitignore:
        console.print("\n[cyan]Syncing patterns from .gitignore...[/cyan]")
        added_count, new_patterns = context_manager.sync_gitignore()

        if added_count > 0:
            console.print(
                f"[green]Added {added_count} patterns from .gitignore:[/green]"
            )
            for pattern in new_patterns[:5]:  # Show first 5
                console.print(f"  - {pattern}")
            if len(new_patterns) > 5:
                console.print(f"  ... and {len(new_patterns) - 5} more")
        else:
            console.print("[yellow]No new patterns found in .gitignore[/yellow]")

    # Show current ignore patterns
    ignore_patterns = context_manager.list_ignore_patterns()
    if ignore_patterns:
        console.print(f"\n[dim]Current ignore patterns ({len(ignore_patterns)}):[/dim]")
        for pattern in ignore_patterns[:5]:
            console.print(f"  - {pattern}")
        if len(ignore_patterns) > 5:
            console.print(f"  ... and {len(ignore_patterns) - 5} more")

    # Interactive pattern entry
    console.print(
        "\n[bold]Enter watch patterns[/bold] (one per line, empty line to finish):"
    )
    console.print("[dim]Example: src/**/*.py[/dim]")

    watch_patterns: List[str] = []
    while True:
        pattern = typer.prompt("Pattern", default="", show_default=False)
        if not pattern:
            break
        watch_patterns.append(pattern)
        console.print(f"[green]Added: {pattern}[/green]")

    if not watch_patterns:
        console.print(
            "[red]No watch patterns provided. Profile creation cancelled.[/red]"
        )
        raise typer.Abort()

    # Apply patterns to context
    context_manager.watch_paths(watch_patterns)

    # Show summary
    console.print("\n[bold]Profile Summary:[/bold]")
    console.print(f"Name: {name}")
    if description:
        console.print(f"Description: {description}")
    console.print(f"Watch patterns: {len(watch_patterns)}")
    console.print(f"Ignore patterns: {len(ignore_patterns)}")
    console.print(f"Files matched: {len(context_manager.files)}")

    # Confirm and save
    if typer.confirm("\nCreate profile?", default=True):
        profile_manager = ProfileManager(
            context_manager.storage, context_manager.base_dir
        )
        success = profile_manager.save_profile(
            name=name,
            watched_patterns=list(context_manager.watched_patterns),
            ignore_patterns=ignore_patterns,
            description=description,
            force=True,
        )

        if success:
            context_manager.current_profile_name = name
            context_manager.reset_dirty_state()
            console.print(f"\n[green]✓ Profile '{name}' created successfully![/green]")
        else:
            console.print(f"\n[red]Failed to create profile '{name}'[/red]")
    else:
        console.print("[yellow]Profile creation cancelled.[/yellow]")


def main() -> None:
    """Entrypoint for the CLI."""
    app()


if __name__ == "__main__":
    main()
