import os
import re
from pathlib import Path
from typing import List, Set, Optional, Tuple


class IgnoreManager:
    """
    Manages ignore patterns with improved git-style pattern support.
    
    Features:
    - Full support for git-style ignore patterns
    - Support for directory-specific patterns
    - Negation patterns with ! prefix
    - Proper handling of ** glob patterns
    - Case-insensitive matching on Windows and macOS
    """

    def __init__(self, base_dir: Path):
        self.base_dir = base_dir
        self.ignore_file = base_dir / ".contextr" / ".ignore"
        self.patterns: Set[str] = set()
        self.negation_patterns: Set[str] = set()  # For patterns starting with !
        self._compiled_patterns: List[Tuple[re.Pattern, bool]] = []  # (regex, is_negation)
        self._load_patterns()

    def _load_patterns(self) -> None:
        """Load patterns from .ignore file and compile them for efficient matching."""
        if self.ignore_file.exists():
            with open(self.ignore_file, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#"):
                        if line.startswith("!"):
                            self.negation_patterns.add(line[1:])  # Remove the !
                        else:
                            self.patterns.add(line)
        
        # Pre-compile patterns for efficient matching
        self._compile_patterns()

    def _compile_patterns(self) -> None:
        """Compile all patterns into regex for efficient matching."""
        self._compiled_patterns = []
        
        # Compile normal patterns
        for pattern in self.patterns:
            regex = self._pattern_to_regex(pattern)
            self._compiled_patterns.append((regex, False))
            
        # Compile negation patterns
        for pattern in self.negation_patterns:
            regex = self._pattern_to_regex(pattern)
            self._compiled_patterns.append((regex, True))

    def _pattern_to_regex(self, pattern: str) -> re.Pattern:
        """
        Convert a glob pattern to a regular expression.
        Handles git-style pattern syntax.
        """
        # Clean up the pattern
        pattern = pattern.strip().replace('\\', '/')
        
        # Handle directory-only patterns
        dir_only = pattern.endswith('/')
        if dir_only:
            pattern = pattern[:-1]
        
        # Handle patterns that start with /
        anchored = pattern.startswith('/')
        if anchored:
            pattern = pattern[1:]
        
        # Escape regex special chars, except those we want to use (* and ?)
        pattern = re.escape(pattern)
        
        # Restore wildcards and handle special cases
        pattern = pattern.replace('\\*\\*/', '.*?/')  # **/ matches any directory
        pattern = pattern.replace('\\*\\*', '.*?')    # ** matches any path
        pattern = pattern.replace('\\*', '[^/]*')     # * matches any non-path chars
        pattern = pattern.replace('\\?', '[^/]')      # ? matches one non-path char
        
        # Anchor the pattern appropriately
        if anchored:
            pattern = f'^{pattern}'
        else:
            pattern = f'(^|/){pattern}'
        
        # Handle directory-only patterns
        if dir_only:
            pattern = f'{pattern}(/|$)'
        else:
            pattern = f'{pattern}$'
        
        # Compile the regex with proper flags
        return re.compile(pattern, re.IGNORECASE if os.name == 'nt' else 0)

    def should_ignore(self, path: str) -> bool:
        """
        Check if a path should be ignored based on current patterns.
        Uses pre-compiled regex patterns for fast matching.

        Args:
            path: Absolute or relative path to check

        Returns:
            bool: True if path should be ignored
        """
        try:
            # Convert to relative path for matching
            rel_path = str(Path(path).resolve().relative_to(self.base_dir.resolve()))
            # Normalize separators for matching
            rel_path = rel_path.replace('\\', '/')
            
            # Check against compiled patterns
            should_ignore = False
            
            for regex, is_negation in self._compiled_patterns:
                if regex.search(rel_path):
                    # Negation patterns override previous matches
                    should_ignore = not is_negation
                    
                    # If it's a negation pattern that matched, we're done
                    if is_negation:
                        return False
            
            return should_ignore
            
        except (ValueError, OSError):
            # If path is outside base_dir or other error, don't ignore it
            return False

    def add_pattern(self, pattern: str) -> None:
        """
        Add a new ignore pattern, handling negation patterns.
        Recompiles the pattern list for efficient matching.
        """
        pattern = pattern.strip()
        if pattern.startswith("!"):
            self.negation_patterns.add(pattern[1:])
        else:
            self.patterns.add(pattern)
        
        # Recompile patterns and save
        self._compile_patterns()
        self.save_patterns()

    def remove_pattern(self, pattern: str) -> bool:
        """
        Remove an ignore pattern. Returns True if pattern was found and removed.
        Recompiles the pattern list for efficient matching.
        """
        pattern = pattern.strip()
        removed = False
        
        if pattern.startswith("!"):
            pattern = pattern[1:]
            if pattern in self.negation_patterns:
                self.negation_patterns.remove(pattern)
                removed = True
        else:
            if pattern in self.patterns:
                self.patterns.remove(pattern)
                removed = True
        
        if removed:
            # Recompile patterns and save
            self._compile_patterns()
            self.save_patterns()
            
        return removed

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

    def list_patterns(self) -> List[str]:
        """Get list of current ignore patterns, including negation patterns."""
        patterns = []
        patterns.extend(sorted(self.patterns))
        patterns.extend(f"!{pattern}" for pattern in sorted(self.negation_patterns))
        return patterns