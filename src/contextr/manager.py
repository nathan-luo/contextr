from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple, TypeAlias

from rich.console import Console

from .profile import Profile
from .storage import JsonStorage, StorageBackend
from .utils.ignore_utils import IgnoreManager
from .utils.path_utils import make_absolute, make_relative, normalize_paths

# Type aliases for clarity
FilePath: TypeAlias = str
Pattern: TypeAlias = str
FileStats: TypeAlias = Dict[str, int]

console = Console()


class ContextManager:
    """
    Manages the current "context" of files and directories.
    Keeps track of files and provides methods to manipulate them.

    The ContextManager uses a pluggable storage backend for persisting state.
    By default, it uses JsonStorage which maintains backward compatibility
    with the original file-based storage format. The storage abstraction
    allows for easy extension to support different storage mechanisms
    (e.g., profiles, cloud storage) without modifying core functionality.

    Args:
        storage: Optional storage backend implementation. If not provided,
                defaults to JsonStorage using the .contextr directory.
    """

    def __init__(self, storage: Optional[StorageBackend] = None) -> None:
        self.files: Set[FilePath] = set()
        self.watched_patterns: Set[Pattern] = set()
        self.base_dir: Path = Path.cwd()
        self.state_dir: Path = self.base_dir / ".contextr"
        self.state_file: Path = self.state_dir / "state.json"
        self.storage: StorageBackend = storage or JsonStorage(self.state_dir)
        self.ignore_manager: IgnoreManager = IgnoreManager(self.base_dir)
        self._load_state()

    def add_ignore_pattern(self, pattern: Pattern) -> Tuple[int, int]:
        """
        Add a new pattern to .ignore file and update current context.

        Args:
            pattern: Pattern to add (glob-style)

        Returns:
            Tuple[int, int]: (Number of files removed, Number of directories cleaned)
        """
        self.ignore_manager.add_pattern(pattern)

        # Track both files and directories affected
        files_to_remove: Set[FilePath] = set()
        cleaned_dirs: Set[FilePath] = set()

        # First pass: identify files to remove
        for filepath in self.files:
            if self.ignore_manager.should_ignore(filepath):
                files_to_remove.add(filepath)
                parent_dir = str(Path(filepath).parent)
                cleaned_dirs.add(parent_dir)

        # Remove files and save state
        self.files -= files_to_remove
        self._save_state()

        # Optionally rescan directories that had ignored files
        for dir_path in cleaned_dirs:
            p: Path = Path(dir_path)
            if p.exists() and p.is_dir():
                # Check remaining files in this directory
                for file_path in p.rglob("*"):
                    if file_path.is_file():
                        file_abs = str(file_path.resolve())
                        # Add file only if it's not ignored
                        if not self.ignore_manager.should_ignore(file_abs):
                            self.files.add(file_abs)

        self._save_state()
        return len(files_to_remove), len(cleaned_dirs)

    def remove_ignore_pattern(self, pattern: Pattern) -> bool:
        """
        Remove a pattern from .ignore file.

        Args:
            pattern: Pattern to remove

        Returns:
            bool: True if pattern was found and removed
        """
        return self.ignore_manager.remove_pattern(pattern)

    def list_ignore_patterns(self) -> List[Pattern]:
        """
        Get list of current ignore patterns.

        Returns:
            List[Pattern]: List of glob-style ignore patterns
        """
        return self.ignore_manager.list_patterns()

    def sync_gitignore(self) -> Tuple[int, List[str]]:
        """
        Sync patterns from .gitignore to .ignore file.

        Returns:
            Tuple[int, List[str]]: (Number of new patterns added, List of new patterns)
        """
        gitignore_path = self.base_dir / ".gitignore"
        if not gitignore_path.exists():
            return 0, []

        # Read .gitignore patterns
        with open(gitignore_path, "r", encoding="utf-8") as f:
            gitignore_patterns: Set[Pattern] = {
                line.strip() for line in f if line.strip() and not line.startswith("#")
            }

        # Find new patterns
        new_patterns: Set[Pattern] = gitignore_patterns - self.ignore_manager.patterns

        # Add new patterns
        for pattern in new_patterns:
            self.ignore_manager.add_pattern(pattern)

        return len(new_patterns), sorted(new_patterns)

    def initialize(self) -> Tuple[bool, bool]:
        """
        Initialize .contextr directory and update .gitignore.

        Returns:
            Tuple[bool, bool]: (Created .contextr, Updated .gitignore)
        """
        # TODO: Consider returning a dataclass instead of tuple for clarity
        created_dir = False
        updated_gitignore = False

        # Create .contextr directory if it doesn't exist
        if not self.state_dir.exists():
            self.state_dir.mkdir(parents=True)
            created_dir = True

        # Update .gitignore if it exists
        gitignore_path = self.base_dir / ".gitignore"
        if gitignore_path.exists():
            with open(gitignore_path, "r", encoding="utf-8") as f:
                content = f.read()

            # Add .contextr/ to .gitignore if not already present
            if ".contextr/" not in content and ".contextr" not in content:
                with open(gitignore_path, "a", encoding="utf-8") as f:
                    f.write("\n# Contextr directory\n.contextr/\n")
                updated_gitignore = True

        return created_dir, updated_gitignore

    def _load_state(self) -> None:
        """Load state (files and watched patterns) from storage."""
        try:
            data = self.storage.load("state")
            if data:
                # Validate and load files
                self.files = set(
                    make_absolute(p, self.base_dir) for p in data.get("files", [])
                )
                # Validate and load watched patterns
                self.watched_patterns = set(data.get("watched_patterns", []))
        except IOError as e:
            console.print(f"[red]Error loading state: {e}[/red]")

    def _save_state(self) -> None:
        """Save current state (files and watched patterns) to storage."""
        try:
            data = {
                "files": [make_relative(p, self.base_dir) for p in sorted(self.files)],
                "watched_patterns": sorted(
                    self.watched_patterns
                ),  # Save watched patterns
            }
            self.storage.save("state", data)
        except IOError as e:
            console.print(f"[red]Error saving state: {e}[/red]")

    def add_files(self, patterns: List[Pattern]) -> int:
        """Add files, respecting ignore patterns."""
        abs_paths = normalize_paths(patterns, self.base_dir, self.ignore_manager)
        if not abs_paths:
            return 0

        new_files_count = 0
        for path_str in abs_paths:
            p = Path(path_str)
            if p.is_file() and not self.ignore_manager.should_ignore(path_str):
                if path_str not in self.files:
                    new_files_count += 1
                self.files.add(path_str)
            elif p.is_dir():
                # Add all files within the directory that aren't ignored
                for file_path in p.rglob("*"):
                    if file_path.is_file():
                        file_abs = str(file_path.resolve())
                        if not self.ignore_manager.should_ignore(file_abs):
                            if file_abs not in self.files:
                                new_files_count += 1
                            self.files.add(file_abs)

        self._save_state()
        return new_files_count

    def remove_files(self, patterns: List[Pattern]) -> int:
        """
        Remove files or directories from the context.
        If a directory is removed, all files under it are also removed.

        Args:
            patterns: List of file/directory patterns to remove

        Returns:
            int: Number of files removed
        """
        abs_paths = normalize_paths(patterns, self.base_dir)
        if not abs_paths:
            return 0

        files_to_remove: Set[FilePath] = set()
        for path_str in abs_paths:
            p = Path(path_str)
            if p.is_file():
                if path_str in self.files:
                    files_to_remove.add(path_str)
            elif p.is_dir():
                # Remove all files under that directory
                for file_path in p.rglob("*"):
                    fp_str = str(file_path.resolve())
                    if fp_str in self.files:
                        files_to_remove.add(fp_str)

        removed_count = len(files_to_remove)
        self.files -= files_to_remove
        self._save_state()
        return removed_count

    def clear_context(self) -> None:
        """
        Clear all files from context.

        Side Effects:
            - Removes all files from current context
            - Saves empty state to disk
        """
        self.files.clear()
        self._save_state()

    def clear(self) -> None:
        """
        Clear all context data including files and patterns.

        Side Effects:
            - Removes all files from current context
            - Clears watched patterns
            - Clears ignore patterns
            - Saves empty state to disk
        """
        self.files.clear()
        self.watched_patterns.clear()
        self.ignore_manager.patterns.clear()
        self.ignore_manager.negation_patterns.clear()
        self._save_state()

    def search_files(self, keyword: str) -> List[FilePath]:
        """
        Search for files in the context containing the given keyword in their path.

        Args:
            keyword: Search term

        Returns:
            List[str]: List of matching file paths (relative to base_dir)
        """
        return [
            make_relative(f, self.base_dir)
            for f in self.files
            if keyword.lower() in f.lower()
        ]

    def get_file_paths(self, relative: bool = True) -> List[FilePath]:
        """
        Get all file paths in the context.

        Args:
            relative: Whether to return relative paths

        Returns:
            List[str]: List of file paths
        """
        if relative:
            return [make_relative(f, self.base_dir) for f in sorted(self.files)]
        return sorted(self.files)

    def unwatch_paths(self, patterns: List[Pattern]) -> Tuple[int, int]:
        """
        Remove paths from watch list but keep existing files.

        Args:
            patterns: List of patterns to stop watching

        Returns:
            Tuple[int, int]: (Number of patterns removed, Number of files kept)
        """
        removed_patterns: Set[Pattern] = set()
        affected_files: Set[FilePath] = set()

        for pattern in patterns:
            if pattern in self.watched_patterns:
                removed_patterns.add(pattern)
                # Count files that were added by this pattern
                abs_paths = normalize_paths(
                    [pattern], self.base_dir, self.ignore_manager
                )
                for path in abs_paths:
                    if path in self.files:
                        affected_files.add(path)

        self.watched_patterns -= removed_patterns
        self._save_state()

        return len(removed_patterns), len(affected_files)

    def watch_paths(self, patterns: List[Pattern]) -> Tuple[int, int]:
        """
        Add paths to watch list and perform initial file addition.
        Filters out ignored patterns before adding to watch list.

        Args:
            patterns: List of file/directory patterns to watch

        Returns:
            Tuple[int, int]: (Number of new patterns, Number of files added)
        """
        # Filter out patterns that would be entirely ignored
        valid_patterns: List[Pattern] = []
        for pattern in patterns:
            # Normalize the pattern path
            abs_pattern = make_absolute(pattern, self.base_dir)
            # If the pattern itself isn't ignored, add it
            if not self.ignore_manager.should_ignore(abs_pattern):
                valid_patterns.append(pattern)

        # Only add non-ignored patterns to watch list
        new_patterns: Set[Pattern] = set(valid_patterns) - self.watched_patterns
        self.watched_patterns.update(new_patterns)

        # Do initial file addition (ignore patterns are respected in add_files)
        added_count = self.add_files(valid_patterns)

        self._save_state()
        return len(new_patterns), added_count

    def refresh_watched(self) -> FileStats:
        """
        Refresh all watched paths to detect changes.
        Only includes non-ignored files in the refresh.

        Returns:
            Dict[str, int]: Statistics about changes (added, removed files)
        """
        stats: FileStats = {"added": 0, "removed": 0}
        old_files: Set[FilePath] = self.files.copy()

        # Clear files that came from watched patterns
        self.files.clear()

        # Re-add all files from watched patterns, respecting ignore patterns
        valid_patterns: List[Pattern] = [
            p
            for p in self.watched_patterns
            if not self.ignore_manager.should_ignore(make_absolute(p, self.base_dir))
        ]

        for pattern in valid_patterns:
            added = self.add_files([pattern])
            stats["added"] += added

        # Count removed files
        stats["removed"] = len(old_files - self.files)

        return stats

    def list_watched(self) -> List[Pattern]:
        """
        Get list of currently watched patterns, excluding those that would be ignored.

        Returns:
            List[Pattern]: Sorted list of valid watched patterns
        """
        return sorted(
            p
            for p in self.watched_patterns
            if not self.ignore_manager.should_ignore(make_absolute(p, self.base_dir))
        )

    def save_state_as(self, state_name: str) -> bool:
        """
        Save current state to a named file in the states directory.

        Args:
            state_name: Name of the state to save

        Returns:
            bool: True if save was successful
        """
        # Ensure state name is valid
        state_name = state_name.replace(" ", "_")
        # Remove .json extension if present for key
        if state_name.endswith(".json"):
            state_name = state_name[:-5]

        key = f"states/{state_name}"

        try:
            data = {
                "files": [make_relative(p, self.base_dir) for p in sorted(self.files)],
                "watched_patterns": sorted(self.watched_patterns),
                "ignore_patterns": sorted(self.ignore_manager.patterns),
                "negation_patterns": sorted(self.ignore_manager.negation_patterns),
            }
            self.storage.save(key, data)
            return True
        except IOError as e:
            console.print(f"[red]Error saving state '{state_name}': {e}[/red]")
            return False

    def load_state(self, state_name: str) -> bool:
        """
        Load a previously saved state.

        Args:
            state_name: Name of the state to load

        Returns:
            bool: True if load was successful
        """
        # Remove .json extension if present for key
        if state_name.endswith(".json"):
            state_name = state_name[:-5]

        key = f"states/{state_name}"

        try:
            data = self.storage.load(key)
            if not data:
                console.print(f"[red]State file not found: {state_name}[/red]")
                return False

            # Load files with validation
            self.files = set(
                make_absolute(p, self.base_dir) for p in data.get("files", [])
            )

            # Load watched patterns with validation
            self.watched_patterns = set(data.get("watched_patterns", []))

            # Load ignore patterns with validation
            self.ignore_manager.patterns = set(data.get("ignore_patterns", []))
            self.ignore_manager.negation_patterns = set(
                data.get("negation_patterns", [])
            )
            self.ignore_manager.save_patterns()  # Update the .ignore file

            self._save_state()  # Save as current state
            return True
        except IOError as e:
            console.print(f"[red]Error loading state '{state_name}': {e}[/red]")
            return False

    def list_saved_states(self) -> List[str]:
        """
        Get list of all saved states.

        Returns:
            List[str]: Names of saved states
        """
        # Get all keys with states/ prefix and remove the prefix
        states = self.storage.list_keys("states/")
        return [state.replace("states/", "") for state in states]

    def delete_state(self, state_name: str) -> bool:
        """
        Delete a saved state file.

        Args:
            state_name: Name of the state to delete

        Returns:
            bool: True if deletion was successful
        """
        # Remove .json extension if present for key
        if state_name.endswith(".json"):
            state_name = state_name[:-5]

        key = f"states/{state_name}"

        try:
            if not self.storage.exists(key):
                console.print(f"[red]State file not found: {state_name}[/red]")
                return False
            return self.storage.delete(key)
        except IOError as e:
            console.print(f"[red]Error deleting state '{state_name}': {e}[/red]")
            return False

    def apply_profile(self, profile: Profile) -> None:
        """
        Replace current context with profile data.

        Args:
            profile: Profile object containing patterns to apply

        Side Effects:
            - Clears current context
            - Applies profile patterns
            - Triggers automatic file refresh
        """
        self.clear()
        self.watched_patterns = set(profile.watched_patterns)
        self.ignore_manager.patterns = set(profile.ignore_patterns)
        self.refresh_files()

    def refresh_files(self) -> int:
        """
        Refresh files based on current watched patterns.

        Returns:
            int: Number of files added
        """
        # Clear existing files
        self.files.clear()

        # Re-add all files from watched patterns
        total_added = 0
        for pattern in self.watched_patterns:
            added = self.add_files([pattern])
            total_added += added

        return total_added
