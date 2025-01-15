import json
from pathlib import Path
from typing import Set, List, Dict, Tuple
from rich.console import Console

from .utils.ignore_utils import IgnoreManager
from .utils.path_utils import make_relative, make_absolute, normalize_paths

console = Console()

class ContextManager:
    """
    Manages the current "context" of files and directories.
    Keeps track of files and provides methods to manipulate them.
    """

    def __init__(self):
        self.files: Set[str] = set()
        self.base_dir = Path.cwd()
        self.state_dir = self.base_dir / ".contextr"
        self.state_file = self.state_dir / "state.json"
        self.ignore_manager = IgnoreManager(self.base_dir)
        self._load_state()

    def add_ignore_pattern(self, pattern: str) -> Tuple[int, int]:
        """
        Add a new pattern to .ignore file and update current context.

        Args:
            pattern: Pattern to add (glob-style)

        Returns:
            Tuple[int, int]: (Number of files removed, Number of directories cleaned)
        """
        self.ignore_manager.add_pattern(pattern)

        # Track both files and directories affected
        files_to_remove = set()
        cleaned_dirs = set()

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
            p = Path(dir_path)
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

    def remove_ignore_pattern(self, pattern: str) -> bool:
        """
        Remove a pattern from .ignore file.

        Args:
            pattern: Pattern to remove

        Returns:
            bool: True if pattern was found and removed
        """
        return self.ignore_manager.remove_pattern(pattern)

    def list_ignore_patterns(self) -> List[str]:
        """Get list of current ignore patterns."""
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
            gitignore_patterns = {
                line.strip() for line in f
                if line.strip() and not line.startswith("#")
            }

        # Find new patterns
        new_patterns = gitignore_patterns - self.ignore_manager.patterns

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
        """Load state (files) from a JSON file if it exists."""
        if self.state_file.exists():
            try:
                with open(self.state_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                self.files = set(
                    make_absolute(p, self.base_dir) for p in data.get("files", [])
                )
            except Exception as e:
                console.print(f"[red]Error loading state: {e}[/red]")

    def _save_state(self) -> None:
        """Save current state (files) to a JSON file."""
        self.state_dir.mkdir(parents=True, exist_ok=True)
        try:
            with open(self.state_file, "w", encoding="utf-8") as f:
                data = {
                    "files": [
                        make_relative(p, self.base_dir) for p in sorted(self.files)
                    ]
                }
                json.dump(data, f, indent=4)
        except Exception as e:
            console.print(f"[red]Error saving state: {e}[/red]")

    def add_files(self, patterns: List[str]) -> int:
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

    def remove_files(self, patterns: List[str]) -> int:
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

        files_to_remove = set()
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
        """Clear all files from context."""
        self.files.clear()
        self._save_state()

    def search_files(self, keyword: str) -> List[str]:
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

    def get_file_paths(self, relative: bool = True) -> List[str]:
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