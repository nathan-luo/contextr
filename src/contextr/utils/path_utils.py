import os
import glob
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
        # Normalize path (resolve symlinks) and handle case sensitivity based on platform
        path_obj = Path(path).resolve()
        base_dir_resolved = base_dir.resolve()

        # Handle case-insensitive file systems on Windows/macOS
        if platform.system() in ('Windows', 'Darwin'):
            if str(path_obj).lower().startswith(str(base_dir_resolved).lower()):
                # If we're on a case-insensitive filesystem but the resolved path doesn't match,
                # we need to handle this special case
                rel_path = str(path_obj)[len(str(base_dir_resolved)):]
                if rel_path.startswith(os.sep):
                    rel_path = rel_path[1:]
                return rel_path

        # Standard approach for case-sensitive filesystems
        return str(path_obj.relative_to(base_dir_resolved))
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
    if path.startswith('~'):
        expanded_path = os.path.expanduser(path)
        return str(Path(expanded_path).resolve())
        
    # Handle environment variables in paths like $HOME/docs
    if '$' in path:
        expanded_path = os.path.expandvars(path)
        if os.path.isabs(expanded_path):
            return str(Path(expanded_path).resolve())
        return str((base_dir / expanded_path).resolve())
        
    # Handle standard absolute and relative paths
    if os.path.isabs(path):
        return str(Path(path).resolve())
        
    # Handle relative paths
    return str((base_dir / path).resolve())

def normalize_paths(patterns: List[str], base_dir: Path, ignore_manager: Optional[IgnoreManager] = None) -> List[str]:
    """
    Normalize and expand glob patterns to absolute paths, respecting ignore patterns.
    Improved to handle edge cases with symlinks, non-existent files, and case sensitivity.

    Args:
        patterns: List of file patterns (can include globs)
        base_dir: The base directory to resolve relative paths against
        ignore_manager: Optional IgnoreManager to filter ignored files

    Returns:
        List[str]: List of normalized absolute paths
    """
    all_paths = []
    
    for pattern in patterns:
        # Handle special cases in patterns
        expanded_pattern = os.path.expanduser(pattern)
        expanded_pattern = os.path.expandvars(expanded_pattern)
        abs_pattern = make_absolute(expanded_pattern, base_dir)

        # Handle glob patterns
        if any(char in expanded_pattern for char in ['*', '?', '[', ']']):
            try:
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
            except Exception as e:
                console.print(
                    f"[yellow]Warning:[/yellow] Error processing pattern '{pattern}': {e}"
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