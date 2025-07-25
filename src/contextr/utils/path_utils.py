import glob
import os
import platform
from pathlib import Path
from typing import List, Optional

from rich.console import Console

from .ignore_utils import IgnoreManager

console = Console()


def make_relative(path: str, base_dir: Path) -> str:
    """
    Convert absolute path to relative path from base_dir.
    Handles cross-platform path issues and symlinks.

    Args:
        path: The path to convert
        base_dir: The base directory to make the path relative to

    Returns:
        str: The relative path or absolute path if relative is not possible
    """
    try:
        # Normalize path and handle case sensitivity
        path_obj = Path(path).resolve()
        base_dir_resolved = base_dir.resolve()

        # Handle case-insensitive file systems on Windows/macOS
        if platform.system() in ("Windows", "Darwin"):
            path_str = str(path_obj)
            base_str = str(base_dir_resolved)

            # Compare paths case-insensitively
            if path_str.lower().startswith(base_str.lower()):
                # Calculate relative path preserving original case
                rel_path = path_str[len(base_str) :]
                if rel_path.startswith(os.sep):
                    rel_path = rel_path[1:]
                # Return with OS-specific separators
                return rel_path if rel_path else "."

        # Standard approach for case-sensitive filesystems
        rel_path = path_obj.relative_to(base_dir_resolved)
        # Convert to string to get OS-specific separators
        return str(rel_path)
    except ValueError:
        # If we can't make it relative, return the absolute path
        return str(Path(path).resolve())


def make_absolute(path: str, base_dir: Path) -> str:
    """
    Convert relative path to absolute path from base_dir.
    Handles tilde expansion, environment variables, and symlinks.

    Args:
        path: The path to convert
        base_dir: The base directory to resolve relative paths against

    Returns:
        str: The normalized absolute path
    """
    # Handle ~/ expansion for home directory
    if path.startswith("~"):
        expanded_path = os.path.expanduser(path)
        return str(Path(expanded_path).resolve())

    # Handle environment variables in paths like $HOME/docs
    if "$" in path:
        expanded_path = os.path.expandvars(path)
        if os.path.isabs(expanded_path):
            return str(Path(expanded_path).resolve())
        return str((base_dir / expanded_path).resolve())

    # Handle standard absolute and relative paths
    if os.path.isabs(path):
        return str(Path(path).resolve())

    # Handle relative paths
    return str((base_dir / path).resolve())


def normalize_paths(
    patterns: List[str], base_dir: Path, ignore_manager: Optional[IgnoreManager] = None
) -> List[str]:
    """
    Normalize and expand glob patterns to absolute paths, respecting ignore patterns.
    Handles symlinks, non-existent files, and case sensitivity.

    Args:
        patterns: List of file patterns (can include globs)
        base_dir: The base directory to resolve relative paths against
        ignore_manager: Optional IgnoreManager to filter ignored files

    Returns:
        List[str]: List of normalized absolute paths
    """
    all_paths: List[str] = []

    for pattern in patterns:
        # Handle special cases in patterns
        expanded_pattern = os.path.expanduser(pattern)
        expanded_pattern = os.path.expandvars(expanded_pattern)
        abs_pattern = make_absolute(expanded_pattern, base_dir)

        # Handle glob patterns
        if any(char in expanded_pattern for char in ["*", "?", "[", "]"]):
            try:
                matched_files = glob.glob(abs_pattern, recursive=True)

                if matched_files:
                    # Filter out ignored files if ignore_manager is provided
                    if ignore_manager:
                        matched_files = [
                            f
                            for f in matched_files
                            if not ignore_manager.should_ignore(f)
                        ]
                    all_paths.extend(matched_files)
                else:
                    console.print(
                        f"[yellow]Warning:[/yellow] No matches for pattern: '{pattern}'"
                    )
            except Exception as e:
                console.print(
                    f"[yellow]Warning:[/yellow] Error processing pattern "
                    f"'{pattern}': {e}"
                )
        else:
            # Handle non-glob paths
            path_obj = Path(abs_pattern)
            if path_obj.exists():
                # Check if path should be ignored
                if ignore_manager and ignore_manager.should_ignore(str(path_obj)):
                    continue
                all_paths.append(str(path_obj))
            else:
                console.print(
                    f"[yellow]Warning:[/yellow] Path does not exist: '{pattern}'"
                )

    # Deduplicate paths and return
    return list(dict.fromkeys(all_paths))
