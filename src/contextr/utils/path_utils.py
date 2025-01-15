import os
import glob
from pathlib import Path
from typing import List
from rich.console import Console
from .ignore_utils import IgnoreManager

console = Console()

def make_relative(path: str, base_dir: Path) -> str:
    """
    Convert absolute path to relative path from base_dir, if possible.
    Otherwise, return the absolute path.

    Args:
        path: The path to convert
        base_dir: The base directory to make the path relative to

    Returns:
        str: The relative path or absolute path if relative is not possible
    """
    try:
        return str(Path(path).resolve().relative_to(base_dir))
    except ValueError:
        return str(Path(path).resolve())

def make_absolute(path: str, base_dir: Path) -> str:
    """
    Convert relative path to absolute path from base_dir.
    If already absolute, just resolve it.

    Args:
        path: The path to convert
        base_dir: The base directory to resolve relative paths against

    Returns:
        str: The absolute path
    """
    if os.path.isabs(path):
        return str(Path(path).resolve())
    return str((base_dir / path).resolve())

def normalize_paths(patterns: List[str], base_dir: Path, ignore_manager: IgnoreManager = None) -> List[str]:
    """
    Normalize and expand glob patterns to absolute paths, respecting ignore patterns.

    Args:
        patterns: List of file patterns (can include globs)
        base_dir: The base directory to resolve relative paths against
        ignore_manager: Optional IgnoreManager to filter ignored files

    Returns:
        List[str]: List of normalized absolute paths
    """
    all_paths = []
    for pattern in patterns:
        abs_pattern = make_absolute(pattern, base_dir)

        if "*" in pattern or "?" in pattern:
            matched_files = glob.glob(abs_pattern, recursive=True)
            if matched_files:
                # Filter out ignored files if ignore_manager is provided
                if ignore_manager:
                    matched_files = [
                        f for f in matched_files
                        if not ignore_manager.should_ignore(f)
                    ]
                all_paths.extend(matched_files)
            else:
                console.print(
                    f"[yellow]Warning:[/yellow] No matches for pattern: '{pattern}'"
                )
        else:
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
    return all_paths