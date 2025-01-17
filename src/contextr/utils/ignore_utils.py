import os
from pathlib import Path
from typing import List, Set
import fnmatch


class IgnoreManager:
    """Manages .ignore file patterns and file filtering with git-style pattern support."""

    def __init__(self, base_dir: Path):
        self.base_dir = base_dir
        self.ignore_file = base_dir / ".contextr" / ".ignore"
        self.patterns: Set[str] = set()
        self.negation_patterns: Set[str] = set()  # For patterns starting with !
        self._load_patterns()

    def _load_patterns(self) -> None:
        """Load patterns from .ignore file, separating negation patterns."""
        if self.ignore_file.exists():
            with open(self.ignore_file, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#"):
                        if line.startswith("!"):
                            self.negation_patterns.add(line[1:])  # Remove the !
                        else:
                            self.patterns.add(line)

    def save_patterns(self) -> None:
        """Save current patterns to .ignore file, preserving negation patterns."""
        self.ignore_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.ignore_file, "w", encoding="utf-8") as f:
            # Write normal patterns first
            for pattern in sorted(self.patterns):
                f.write(f"{pattern}\n")
            # Then write negation patterns
            for pattern in sorted(self.negation_patterns):
                f.write(f"!{pattern}\n")

    def _normalize_pattern(self, pattern: str) -> str:
        """Normalize a pattern for consistent matching."""
        # Convert backslashes to forward slashes
        pattern = pattern.replace("\\", "/")

        # Handle patterns that start with /
        if pattern.startswith("/"):
            pattern = pattern[1:]  # Remove leading /

        # Handle patterns that end with /
        if pattern.endswith("/"):
            pattern = pattern + "**"  # Match all contents of directory

        # Replace ** with a special marker for path matching
        pattern = pattern.replace("**/", "__DOUBLESTAR__/")
        pattern = pattern.replace("**", "__DOUBLESTAR__")

        return pattern

    def _match_pattern(self, path: str, pattern: str) -> bool:
        """Match a single pattern against a path."""
        normalized_pattern = self._normalize_pattern(pattern)
        path = path.replace("\\", "/")

        # Handle absolute paths
        if pattern.startswith("/"):
            return fnmatch.fnmatch(path, normalized_pattern)

        # Handle directory-only patterns (ending with /)
        if pattern.endswith("/"):
            if not os.path.isdir(path):
                return False

        # Split path and pattern into components
        path_parts = path.split("/")
        pattern_parts = normalized_pattern.split("/")

        # Handle ** pattern
        if "__DOUBLESTAR__" in normalized_pattern:
            # Convert the pattern to regex
            regex_pattern = normalized_pattern.replace("__DOUBLESTAR__", ".*")
            regex_pattern = regex_pattern.replace("*", "[^/]*")
            regex_pattern = regex_pattern.replace("?", "[^/]")
            import re
            return bool(re.match(f"^{regex_pattern}$", path))

        # If pattern doesn't contain /, match against basename
        if "/" not in pattern:
            return any(fnmatch.fnmatch(part, pattern) for part in path_parts)

        # Match complete path
        return fnmatch.fnmatch(path, normalized_pattern)

    def should_ignore(self, path: str) -> bool:
        """
        Check if a path should be ignored based on current patterns.
        Supports git-style ignore patterns including:
        - Patterns starting with / match from root
        - Patterns ending with / match directories only
        - ** matches zero or more directories
        - ! negates a pattern

        Args:
            path: Absolute or relative path to check

        Returns:
            bool: True if path should be ignored
        """
        try:
            # Convert to relative path for matching
            rel_path = str(Path(path).resolve().relative_to(self.base_dir))
        except ValueError:
            # If path is outside base_dir, use full path
            rel_path = str(Path(path))

        # First check negation patterns
        for pattern in self.negation_patterns:
            if self._match_pattern(rel_path, pattern):
                return False  # Path is explicitly not ignored

        # Then check ignore patterns
        for pattern in self.patterns:
            if self._match_pattern(rel_path, pattern):
                return True

        return False

    def add_pattern(self, pattern: str) -> None:
        """Add a new ignore pattern, handling negation patterns."""
        pattern = pattern.strip()
        if pattern.startswith("!"):
            self.negation_patterns.add(pattern[1:])
        else:
            self.patterns.add(pattern)
        self.save_patterns()

    def remove_pattern(self, pattern: str) -> bool:
        """Remove an ignore pattern. Returns True if pattern was found and removed."""
        pattern = pattern.strip()
        if pattern.startswith("!"):
            pattern = pattern[1:]
            if pattern in self.negation_patterns:
                self.negation_patterns.remove(pattern)
                self.save_patterns()
                return True
        else:
            if pattern in self.patterns:
                self.patterns.remove(pattern)
                self.save_patterns()
                return True
        return False

    def list_patterns(self) -> List[str]:
        """Get list of current ignore patterns, including negation patterns."""
        patterns = []
        patterns.extend(sorted(self.patterns))
        patterns.extend(f"!{pattern}" for pattern in sorted(self.negation_patterns))
        return patterns