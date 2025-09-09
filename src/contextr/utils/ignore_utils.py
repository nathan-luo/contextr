import os
import platform
import re
from dataclasses import dataclass
from pathlib import Path
from typing import List, Pattern, Set


@dataclass
class _Rule:
    raw: str  # pattern string w/o '!' prefix
    is_negation: bool  # True if rule represents a negation
    regex: Pattern[str] | None = None


class IgnoreManager:
    """
    Manages ignore patterns with git-style pattern semantics.

    Features:
    - Ordered rules with "last match wins" semantics
    - Support for directory-specific patterns
    - Negation with '!' prefix
    - Proper handling of ** glob patterns
    - Case-insensitive matching on Windows and macOS
    """

    def __init__(self, base_dir: Path):
        self.base_dir = base_dir
        self.ignore_file = base_dir / ".contextr" / ".ignore"
        # Ordered list of rules; preserves file order (git-like)
        self._rules: List[_Rule] = []
        self._load_patterns()

    def _load_patterns(self) -> None:
        """Load rules from .ignore in order and compile them."""
        self._rules.clear()
        if self.ignore_file.exists():
            with open(self.ignore_file, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith("#"):
                        continue
                    is_neg = line.startswith("!")
                    raw = line[1:] if is_neg else line
                    self._rules.append(_Rule(raw=raw, is_negation=is_neg))
        self.compile_patterns()

    def compile_patterns(self) -> None:
        """Compile all rules into regex for efficient matching."""
        for r in self._rules:
            r.regex = self._pattern_to_regex(r.raw)

    def _pattern_to_regex(self, pattern: str) -> Pattern[str]:
        """
        Convert a gitignore-style pattern to a regex with segment-aware semantics.
        Highlights:
          - Leading '/' anchors to repo root.
          - Trailing '/' indicates a directory rule, but even without it a segment
            match implies directory descendants are ignored (git behavior).
          - '**/' matches ZERO or more directories.
          - '*' matches within a path segment only (no '/').
          - '?' matches a single non-'/' character.
          - Last match wins is handled at evaluation time, not here.
        """
        # Normalize and strip
        pattern = pattern.strip().replace("\\", "/")

        dir_only = pattern.endswith("/")
        if dir_only:
            pattern = pattern[:-1]

        # Leading slash anchors to root (relative to base_dir)
        anchored = pattern.startswith("/")
        if anchored:
            pattern = pattern[1:]

        # Escape regex specials first
        escaped = re.escape(pattern)

        # Reintroduce git-style globs.
        #
        # IMPORTANT: '**/' must allow ZERO directories. The previous implementation
        # used '.*?/', which forced at least one dir and broke patterns like a/**/b
        # (which should match a/b). We use a non-capturing optional group.
        pattern_regex = (
            escaped
            .replace(r"\*\*\/", r"(?:.*/)?")   # **/  -> zero or more directories
            .replace(r"\*\*", r".*")           # **   -> any chars, including '/'
            .replace(r"\*", r"[^/]*")          # *    -> any chars except '/'
            .replace(r"\?", r"[^/]")           # ?    -> single non-'/' char
        )

        # Segment-aware anchoring:
        # - anchored: must match starting at beginning of relpath
        # - not anchored: allow a segment start boundary anywhere
        prefix = r"^" if anchored else r"(^|/)"

        # Suffix:
        # Git treats a directory-name match (with or without a trailing slash)
        # as affecting everything inside. Using '(/|$)' here ensures both:
        #  - exact leaf matches (files or dirs), AND
        #  - segment matches inside a longer path (…/dir/…).
        # This gives correct behavior for bare names like 'node_modules'.
        suffix = r"(/|$)"

        full = f"{prefix}{pattern_regex}{suffix}"

        # Compile the regex with proper flags
        return re.compile(
            full,
            re.IGNORECASE if (os.name == "nt" or platform.system() == "Darwin") else 0,
        )

    def should_ignore(self, path: str) -> bool:
        """
        Check if a path should be ignored based on current rules.
        Applies git-style semantics: last matching rule wins.

        Args:
            path: Absolute or relative path to check

        Returns:
            bool: True if path should be ignored
        """
        try:
            rel_path = str(Path(path).resolve().relative_to(self.base_dir.resolve()))
            rel_path = rel_path.replace("\\", "/")
        except (ValueError, OSError):
            return False

        ignored = False
        for r in self._rules:
            assert r.regex is not None
            if r.regex.search(rel_path):
                ignored = not r.is_negation
        return ignored

    def add_pattern(self, pattern: str) -> None:
        """
        Append a new pattern (preserving order). Accepts negations with leading '!'.
        """
        pattern = pattern.strip()
        if not pattern:
            return
        is_neg = pattern.startswith("!")
        raw = pattern[1:] if is_neg else pattern
        # Avoid exact duplicate rules
        if not any((r.raw == raw and r.is_negation == is_neg) for r in self._rules):
            self._rules.append(_Rule(raw=raw, is_negation=is_neg))
        self.compile_patterns()
        self.save_patterns()

    def remove_pattern(self, pattern: str) -> bool:
        """
        Remove a pattern (matching by raw + negation). Returns True if removed.
        """
        pattern = pattern.strip()
        if not pattern:
            return False
        is_neg = pattern.startswith("!")
        raw = pattern[1:] if is_neg else pattern
        before = len(self._rules)
        self._rules = [
            r for r in self._rules if not (r.raw == raw and r.is_negation == is_neg)
        ]
        removed = len(self._rules) != before
        if removed:
            self.compile_patterns()
            self.save_patterns()
        return removed

    def save_patterns(self) -> None:
        """Write rules to .ignore preserving order."""
        self.ignore_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.ignore_file, "w", encoding="utf-8") as f:
            for r in self._rules:
                prefix = "!" if r.is_negation else ""
                f.write(f"{prefix}{r.raw}\n")

    def list_patterns(self) -> List[str]:
        """Return patterns in current file order (negations prefixed with '!')."""
        return [("!" if r.is_negation else "") + r.raw for r in self._rules]

    # --- Helpers for manager/state integration ---
    def clear_patterns(self) -> None:
        """Clear all rules and persist an empty .ignore."""
        self._rules.clear()
        self.save_patterns()
        self.compile_patterns()

    def set_patterns(self, normals: Set[str], negations: Set[str]) -> None:
        """
        Replace current rules from sets for state/profile hydration.
        Order for these is deterministic: normals (sorted) then negations (sorted).
        """
        self._rules = [
            _Rule(raw=p.strip(), is_negation=False)
            for p in sorted({p for p in normals if p.strip()})
        ]
        self._rules += [
            _Rule(raw=p.strip(), is_negation=True)
            for p in sorted({p for p in negations if p.strip()})
        ]
        self.compile_patterns()
        self.save_patterns()

    def get_normal_patterns_set(self) -> Set[str]:
        return {r.raw for r in self._rules if not r.is_negation}

    def get_negation_patterns_set(self) -> Set[str]:
        return {r.raw for r in self._rules if r.is_negation}
