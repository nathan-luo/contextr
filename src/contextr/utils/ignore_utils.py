import os
from pathlib import Path
from typing import List, Set
import fnmatch

class IgnoreManager:
    """Manages .ignore file patterns and file filtering."""

    def __init__(self, base_dir: Path):
        self.base_dir = base_dir
        self.ignore_file = base_dir / ".contextr" / ".ignore"
        self.patterns: Set[str] = set()
        self._load_patterns()

    def _load_patterns(self) -> None:
        """Load patterns from .ignore file."""
        if self.ignore_file.exists():
            with open(self.ignore_file, "r", encoding="utf-8") as f:
                # Strip whitespace and comments, filter empty lines
                self.patterns = {
                    line.strip() for line in f
                    if line.strip() and not line.startswith("#")
                }

    def save_patterns(self) -> None:
        """Save current patterns to .ignore file."""
        self.ignore_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.ignore_file, "w", encoding="utf-8") as f:
            f.write("\n".join(sorted(self.patterns)))

    def add_pattern(self, pattern: str) -> None:
        """Add a new ignore pattern."""
        self.patterns.add(pattern.strip())
        self.save_patterns()

    def remove_pattern(self, pattern: str) -> bool:
        """Remove an ignore pattern. Returns True if pattern was found and removed."""
        if pattern in self.patterns:
            self.patterns.remove(pattern)
            self.save_patterns()
            return True
        return False

    def should_ignore(self, path: str) -> bool:
        """
        Check if a path should be ignored based on current patterns.

        Args:
            path: Absolute or relative path to check

        Returns:
            bool: True if path matches any ignore pattern
        """
        try:
            # Convert to relative path for matching
            rel_path = str(Path(path).resolve().relative_to(self.base_dir))
        except ValueError:
            # If path is outside base_dir, use full path
            rel_path = str(Path(path))

        # Get path parts for directory matching
        path_parts = Path(rel_path).parts

        for pattern in self.patterns:
            # Check if any part of the path matches the pattern
            for part in path_parts:
                if fnmatch.fnmatch(part, pattern):
                    return True

            # Also check the full path against pattern for glob patterns
            if fnmatch.fnmatch(rel_path, pattern):
                return True

        return False

    def list_patterns(self) -> List[str]:
        """Get list of current ignore patterns."""
        return sorted(self.patterns)