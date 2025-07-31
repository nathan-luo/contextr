"""Unit tests for ContextManager auto-sync behavior."""

import tempfile
from pathlib import Path

import pytest

from contextr.manager import ContextManager
from contextr.storage import JsonStorage


class TestContextManagerAutoSync:
    """Test auto-sync behavior where files follow watched patterns."""

    @pytest.fixture
    def temp_dir(self) -> Path:
        """Create a temporary directory for tests."""
        with tempfile.TemporaryDirectory() as tmp:
            yield Path(tmp)

    @pytest.fixture
    def manager(self, temp_dir: Path) -> ContextManager:
        """Create a ContextManager instance with test directory."""
        # Change to temp directory to avoid side effects
        import os

        old_cwd = os.getcwd()
        os.chdir(temp_dir)
        storage = JsonStorage(temp_dir / ".contextr")
        manager = ContextManager(storage=storage)
        yield manager
        os.chdir(old_cwd)

    def create_test_files(self, temp_dir: Path) -> None:
        """Create test file structure."""
        # Create directories
        (temp_dir / "src").mkdir()
        (temp_dir / "src" / "utils").mkdir()
        (temp_dir / "tests").mkdir()
        (temp_dir / "docs").mkdir()

        # Create files
        (temp_dir / "README.md").write_text("# Test Project")
        (temp_dir / "setup.py").write_text("setup()")
        (temp_dir / "src" / "__init__.py").write_text("")
        (temp_dir / "src" / "main.py").write_text("def main(): pass")
        (temp_dir / "src" / "utils" / "__init__.py").write_text("")
        (temp_dir / "src" / "utils" / "helper.py").write_text("def help(): pass")
        (temp_dir / "tests" / "test_main.py").write_text("def test_main(): pass")
        (temp_dir / "docs" / "api.md").write_text("# API")
        (temp_dir / "docs" / "guide.md").write_text("# Guide")

    def test_watch_paths_adds_files_automatically(
        self, manager: ContextManager, temp_dir: Path
    ) -> None:
        """Test that watching patterns automatically adds matching files."""
        self.create_test_files(temp_dir)

        # Watch Python files
        patterns_added, files_added = manager.watch_paths(["src/**/*.py"])

        assert patterns_added == 1
        assert files_added == 4  # __init__.py files and main.py, helper.py

        # Verify files are in context
        files = manager.get_file_paths(relative=True)
        # Normalize paths for cross-platform compatibility
        normalized_files = [f.replace("\\", "/") for f in files]
        assert "src/__init__.py" in normalized_files
        assert "src/main.py" in normalized_files
        assert "src/utils/__init__.py" in normalized_files
        assert "src/utils/helper.py" in normalized_files

    def test_unwatch_paths_removes_files_automatically(
        self, manager: ContextManager, temp_dir: Path
    ) -> None:
        """Test that unwatching patterns automatically removes associated files."""
        self.create_test_files(temp_dir)

        # Watch multiple patterns
        manager.watch_paths(["src/**/*.py", "*.md"])
        initial_count = len(manager.files)
        assert initial_count > 0

        # Unwatch Python files
        patterns_removed, files_removed = manager.unwatch_paths(["src/**/*.py"])

        assert patterns_removed == 1
        assert files_removed == 4  # All Python files removed

        # Verify only markdown files remain
        files = manager.get_file_paths(relative=True)
        # Normalize paths for cross-platform compatibility
        normalized_files = [f.replace("\\", "/") for f in files]
        assert "README.md" in normalized_files
        assert "src/main.py" not in normalized_files
        assert len(files) == 1  # Only README.md

    def test_multiple_patterns_no_duplicate_files(
        self, manager: ContextManager, temp_dir: Path
    ) -> None:
        """Test that overlapping patterns don't create duplicate files."""
        self.create_test_files(temp_dir)

        # Watch overlapping patterns
        manager.watch_paths(["src/**/*.py"])
        first_count = len(manager.files)

        manager.watch_paths(["src/*.py"])  # Overlaps with previous
        second_count = len(manager.files)

        # No new files should be added (src/*.py is subset of src/**/*.py)
        assert first_count == second_count

    def test_refresh_files_syncs_with_patterns(
        self, manager: ContextManager, temp_dir: Path
    ) -> None:
        """Test that refresh_files keeps files in sync with patterns."""
        self.create_test_files(temp_dir)

        # Watch patterns
        manager.watch_paths(["src/**/*.py"])
        initial_files = set(manager.get_file_paths(relative=True))

        # Manually add a file that doesn't match patterns (simulate corruption)
        manager.files.add(str(temp_dir / "docs" / "api.md"))

        # Refresh should remove the non-matching file
        manager.refresh_files()
        refreshed_files = set(manager.get_file_paths(relative=True))

        assert refreshed_files == initial_files
        assert "docs/api.md" not in refreshed_files

    def test_sync_command_behavior(
        self, manager: ContextManager, temp_dir: Path
    ) -> None:
        """Test that sync refreshes based on watched patterns only."""
        self.create_test_files(temp_dir)

        # Watch patterns
        manager.watch_paths(["*.md"])
        initial_count = len(manager.files)

        # Create new file matching pattern
        (temp_dir / "NEW.md").write_text("# New")

        # Sync should pick up the new file
        added = manager.refresh_files()
        assert added == initial_count + 1  # All files re-added plus new one
        # Normalize paths for cross-platform compatibility
        normalized_files = [
            f.replace("\\", "/") for f in manager.get_file_paths(relative=True)
        ]
        assert "NEW.md" in normalized_files

    def test_ignore_patterns_respected_in_auto_sync(
        self, manager: ContextManager, temp_dir: Path
    ) -> None:
        """Test that ignore patterns are respected during auto-sync."""
        self.create_test_files(temp_dir)

        # Add ignore pattern first
        manager.add_ignore_pattern("**/test_*.py")

        # Watch all Python files
        patterns_added, files_added = manager.watch_paths(["**/*.py"])

        # Verify test files are not included
        files = manager.get_file_paths(relative=True)
        # Normalize paths for cross-platform compatibility
        normalized_files = [f.replace("\\", "/") for f in files]
        assert "tests/test_main.py" not in normalized_files
        assert "src/main.py" in normalized_files
        assert files_added == 5  # setup.py + 4 source files (non-test)

    def test_empty_patterns_behavior(self, manager: ContextManager) -> None:
        """Test behavior with empty watch patterns."""
        # No patterns watched
        assert len(manager.watched_patterns) == 0
        assert len(manager.files) == 0

        # Refresh should keep empty
        added = manager.refresh_files()
        assert added == 0
        assert len(manager.files) == 0

    def test_invalid_patterns_ignored(
        self, manager: ContextManager, temp_dir: Path
    ) -> None:
        """Test that invalid patterns are handled gracefully."""
        # Try to watch non-existent path
        patterns_added, files_added = manager.watch_paths(["/nonexistent/path/*.py"])

        assert patterns_added == 1  # Pattern is added
        assert files_added == 0  # But no files match

    def test_remove_pattern_with_shared_files(
        self, manager: ContextManager, temp_dir: Path
    ) -> None:
        """Test removing pattern when files are matched by multiple patterns."""
        self.create_test_files(temp_dir)

        # Watch overlapping patterns
        manager.watch_paths(["src/**/*.py", "src/main.py"])
        # Normalize paths for cross-platform compatibility
        normalized_files = [
            f.replace("\\", "/") for f in manager.get_file_paths(relative=True)
        ]
        assert "src/main.py" in normalized_files

        # Remove specific pattern
        patterns_removed, files_removed = manager.unwatch_paths(["src/main.py"])

        # File should still exist due to other pattern
        assert patterns_removed == 1
        # Normalize paths for cross-platform compatibility
        normalized_files = [
            f.replace("\\", "/") for f in manager.get_file_paths(relative=True)
        ]
        assert "src/main.py" in normalized_files

    def test_profile_with_auto_sync(
        self, manager: ContextManager, temp_dir: Path
    ) -> None:
        """Test that profiles work correctly with auto-sync."""
        self.create_test_files(temp_dir)

        # Set up initial context
        manager.watch_paths(["**/*.py"])
        manager.add_ignore_pattern("**/test_*.py")

        # Save state
        manager.save_state_as("python_dev")

        # Clear and verify
        manager.clear()
        assert len(manager.files) == 0
        assert len(manager.watched_patterns) == 0

        # Load state
        success = manager.load_state("python_dev")
        assert success

        # Verify patterns restored and files auto-synced
        assert "**/*.py" in manager.watched_patterns
        assert "**/test_*.py" in manager.list_ignore_patterns()
        assert len(manager.files) == 5  # setup.py + 4 source files (non-test)

    def test_watch_then_modify_filesystem(
        self, manager: ContextManager, temp_dir: Path
    ) -> None:
        """Test behavior when filesystem changes after watching."""
        self.create_test_files(temp_dir)

        # Watch markdown files
        manager.watch_paths(["*.md"])
        initial_count = len(manager.files)

        # Add new file
        (temp_dir / "changelog.md").write_text("# Changelog")

        # Refresh to pick up changes
        manager.refresh_files()
        assert len(manager.files) == initial_count + 1
        # Normalize paths for cross-platform compatibility
        normalized_files = [
            f.replace("\\", "/") for f in manager.get_file_paths(relative=True)
        ]
        assert "changelog.md" in normalized_files

        # Delete a file
        (temp_dir / "README.md").unlink()

        # Refresh should remove deleted file
        manager.refresh_files()
        # Normalize paths for cross-platform compatibility
        normalized_files = [
            f.replace("\\", "/") for f in manager.get_file_paths(relative=True)
        ]
        assert "README.md" not in normalized_files

    def test_state_persistence_with_auto_sync(
        self, manager: ContextManager, temp_dir: Path
    ) -> None:
        """Test that state is correctly saved and loaded with auto-sync."""
        self.create_test_files(temp_dir)

        # Set up context
        manager.watch_paths(["src/**/*.py"])
        original_files = set(manager.get_file_paths(relative=True))
        original_patterns = set(manager.watched_patterns)

        # Create new manager instance (simulates restart)
        new_manager = ContextManager(storage=JsonStorage(temp_dir / ".contextr"))

        # Verify state was persisted
        assert set(new_manager.watched_patterns) == original_patterns
        assert set(new_manager.get_file_paths(relative=True)) == original_files

    def test_no_manual_file_operations(self, manager: ContextManager) -> None:
        """Test that manual file operations are not available."""
        # These methods should be private
        assert not hasattr(manager, "add_files")
        assert not hasattr(manager, "remove_files")

        # Only these should be public
        assert hasattr(manager, "_add_files")
        assert hasattr(manager, "_remove_files")
