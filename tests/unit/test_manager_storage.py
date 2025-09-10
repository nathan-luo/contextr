"""Unit tests for ContextManager with storage abstraction."""

import tempfile
from pathlib import Path
from typing import Any, Dict, List, Optional
from unittest.mock import patch

import pytest

from contextr.manager import ContextManager
from contextr.profile import Profile
from contextr.storage import StorageBackend
from contextr.utils.ignore_utils import _Rule


class MockStorage(StorageBackend):
    """Mock storage backend for testing."""

    def __init__(self) -> None:
        self.data: Dict[str, Dict[str, Any]] = {}
        self.save_called = 0
        self.load_called = 0

    def save(self, key: str, data: Dict[str, Any]) -> None:
        self.save_called += 1
        self.data[key] = data

    def load(self, key: str) -> Optional[Dict[str, Any]]:
        self.load_called += 1
        return self.data.get(key)

    def exists(self, key: str) -> bool:
        return key in self.data

    def delete(self, key: str) -> bool:
        if key in self.data:
            del self.data[key]
            return True
        return False

    def list_keys(self, prefix: str = "") -> List[str]:
        return [k for k in self.data.keys() if k.startswith(prefix)]


class TestContextManagerStorage:
    """Test ContextManager with storage abstraction."""

    @pytest.fixture
    def mock_storage(self) -> MockStorage:
        """Create a mock storage backend."""
        return MockStorage()

    @pytest.fixture
    def manager_with_mock_storage(self, mock_storage: MockStorage) -> ContextManager:
        """Create ContextManager with mock storage."""
        with patch("contextr.manager.Path.cwd", return_value=Path("/test/dir")):
            return ContextManager(storage=mock_storage)

    def test_init_with_custom_storage(self, mock_storage: MockStorage) -> None:
        """Test ContextManager can be initialized with custom storage."""
        with patch("contextr.manager.Path.cwd", return_value=Path("/test/dir")):
            manager = ContextManager(storage=mock_storage)
            assert manager.storage is mock_storage

    def test_init_loads_state(self, mock_storage: MockStorage) -> None:
        """Test that initialization loads state from storage."""
        # Pre-populate storage with state
        mock_storage.data["state"] = {
            "files": ["file1.py", "file2.py"],
            "watched_patterns": ["*.py", "src/**/*.js"],
        }

        with patch("contextr.manager.Path.cwd", return_value=Path("/test/dir")):
            manager = ContextManager(storage=mock_storage)

        assert mock_storage.load_called == 1
        assert len(manager.files) == 2
        assert len(manager.watched_patterns) == 2

    def test_save_state_uses_storage(
        self, manager_with_mock_storage: ContextManager, mock_storage: MockStorage
    ) -> None:
        """Test that _save_state uses the storage backend."""
        manager = manager_with_mock_storage
        manager.files = {"/test/dir/file1.py", "/test/dir/file2.py"}
        manager.watched_patterns = {"*.py"}

        manager._save_state()

        assert mock_storage.save_called == 1
        assert "state" in mock_storage.data
        saved_data = mock_storage.data["state"]
        assert sorted(saved_data["files"]) == ["file1.py", "file2.py"]
        assert saved_data["watched_patterns"] == ["*.py"]

    def test_add_files_saves_state(
        self, manager_with_mock_storage: ContextManager, mock_storage: MockStorage
    ) -> None:
        """Test that _add_files saves state through storage."""
        manager = manager_with_mock_storage

        with patch("contextr.manager.normalize_paths") as mock_normalize:
            mock_normalize.return_value = ["/test/dir/new_file.py"]
            with patch("pathlib.Path.is_file", return_value=True):
                manager._add_files(["new_file.py"])

        assert mock_storage.save_called >= 1
        assert "state" in mock_storage.data

    def test_save_state_as_uses_storage(
        self, manager_with_mock_storage: ContextManager, mock_storage: MockStorage
    ) -> None:
        """Test save_state_as uses storage with correct key."""
        manager = manager_with_mock_storage
        manager.files = {"/test/dir/file1.py"}
        manager.watched_patterns = {"*.py"}

        result = manager.save_state_as("my_state")

        assert result is True
        assert "states/my_state" in mock_storage.data
        saved_data = mock_storage.data["states/my_state"]
        assert "files" in saved_data
        assert "watched_patterns" in saved_data
        assert "ignore_patterns" in saved_data

    def test_load_state_uses_storage(
        self, manager_with_mock_storage: ContextManager, mock_storage: MockStorage
    ) -> None:
        """Test load_state uses storage to load saved states."""
        manager = manager_with_mock_storage

        # Pre-populate a saved state
        mock_storage.data["states/saved_state"] = {
            "files": ["loaded_file.py"],
            "watched_patterns": ["loaded/*.py"],
            "ignore_patterns": ["*.pyc"],
            "negation_patterns": [],
        }

        with patch.object(manager.ignore_manager, "save_patterns"):
            result = manager.load_state("saved_state")

        assert result is True
        # Check that the loaded file is in the files set
        # On Windows, paths will have drive letters, so we check the end of the path
        loaded_files = list(manager.files)
        assert len(loaded_files) == 1
        assert loaded_files[0].endswith("loaded_file.py")
        assert "loaded/*.py" in manager.watched_patterns

    def test_list_saved_states_uses_storage(
        self, manager_with_mock_storage: ContextManager, mock_storage: MockStorage
    ) -> None:
        """Test list_saved_states uses storage list_keys."""
        manager = manager_with_mock_storage

        # Add some saved states
        mock_storage.data["states/state1"] = {}
        mock_storage.data["states/state2"] = {}
        mock_storage.data["other/key"] = {}

        states = manager.list_saved_states()

        assert sorted(states) == ["state1", "state2"]

    def test_delete_state_uses_storage(
        self, manager_with_mock_storage: ContextManager, mock_storage: MockStorage
    ) -> None:
        """Test delete_state uses storage delete method."""
        manager = manager_with_mock_storage

        # Add a state to delete
        mock_storage.data["states/to_delete"] = {}

        result = manager.delete_state("to_delete")

        assert result is True
        assert "states/to_delete" not in mock_storage.data

    def test_backward_compatibility_with_default_storage(self) -> None:
        """Test that ContextManager works without specifying storage."""
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch("contextr.manager.Path.cwd", return_value=Path(tmpdir)):
                manager = ContextManager()

                # Should have JsonStorage by default
                assert manager.storage is not None
                assert manager.storage.__class__.__name__ == "JsonStorage"

    def test_storage_error_handling(
        self, manager_with_mock_storage: ContextManager, mock_storage: MockStorage
    ) -> None:
        """Test that storage errors are handled gracefully."""
        manager = manager_with_mock_storage

        # Make save raise an error
        def save_error(key: str, data: Dict[str, Any]) -> None:
            raise IOError("Storage failure")

        mock_storage.save = save_error

        # Should not raise, but print error
        with patch("contextr.manager.console.print") as mock_print:
            manager._save_state()
            mock_print.assert_called_once()
            assert "Error saving state" in str(mock_print.call_args)

    def test_state_format_consistency(
        self, manager_with_mock_storage: ContextManager, mock_storage: MockStorage
    ) -> None:
        """Test that state format is consistent with original implementation."""
        manager = manager_with_mock_storage
        manager.files = {"/test/dir/src/file1.py", "/test/dir/README.md"}
        manager.watched_patterns = {"src/**/*.py", "*.md"}

        manager._save_state()

        saved_state = mock_storage.data["state"]

        # Check format matches expected structure
        assert "files" in saved_state
        assert "watched_patterns" in saved_state
        assert isinstance(saved_state["files"], list)
        assert isinstance(saved_state["watched_patterns"], list)
        assert all(isinstance(f, str) for f in saved_state["files"])
        assert all(isinstance(p, str) for p in saved_state["watched_patterns"])

    def test_clear_method_preserves_ignores(
        self, manager_with_mock_storage: ContextManager, mock_storage: MockStorage
    ) -> None:
        """Test clear method clears context data but preserves ignores by default."""
        manager = manager_with_mock_storage

        # Set up initial state
        manager.files = {"/test/file1.py", "/test/file2.py"}
        manager.watched_patterns = {"*.py", "src/**/*.js"}
        # Set ignore patterns without persistent save (test environment)
        try:
            manager.ignore_manager.set_patterns(
                {"*.pyc", "__pycache__"}, {"important.pyc"}
            )
        except OSError:
            # Fall back to in-memory only for test environment
            manager.ignore_manager._rules = [
                _Rule(raw="*.pyc", is_negation=False),
                _Rule(raw="__pycache__", is_negation=False),
                _Rule(raw="important.pyc", is_negation=True),
            ]
            manager.ignore_manager.compile_patterns()

        # Clear context (preserve ignores)
        manager.clear()

        # Verify files and watched patterns are cleared but ignores remain
        assert len(manager.files) == 0
        assert len(manager.watched_patterns) == 0
        # Ignores are repo-level and persist
        assert manager.ignore_manager.list_patterns() != []

        # Verify state was saved
        assert mock_storage.save_called > 0
        saved_state = mock_storage.data["state"]
        assert saved_state["files"] == []
        assert saved_state["watched_patterns"] == []

    def test_apply_profile_preserves_repo_ignores(
        self, manager_with_mock_storage: ContextManager, mock_storage: MockStorage
    ) -> None:
        """Test apply_profile replaces watched patterns but preserves repo ignores."""
        manager = manager_with_mock_storage

        # Set up initial state with different patterns
        manager.files = {"/old/file1.py", "/old/file2.py"}
        manager.watched_patterns = {"old/*.py"}
        # Set initial ignore rule
        try:
            manager.ignore_manager.set_patterns({"*.old"}, set())
        except OSError:
            manager.ignore_manager._rules = [
                _Rule(raw="*.old", is_negation=False),
            ]
            manager.ignore_manager.compile_patterns()

        # Create a profile to apply
        profile = Profile(
            name="test-profile",
            watched_patterns=["src/**/*.py", "tests/**/*.py"],
        )

        # Apply the profile
        manager.apply_profile(profile, "test-profile")

        # Verify context was cleared and profile patterns applied
        assert manager.watched_patterns == {"src/**/*.py", "tests/**/*.py"}
        # Repo-level ignores remain untouched
        assert manager.ignore_manager.get_normal_patterns_set() == {"*.old"}

        # Files should be cleared initially by clear() but may be
        # repopulated by refresh_files. The actual file population
        # depends on the filesystem, so we just verify the patterns

    def test_refresh_files(
        self, manager_with_mock_storage: ContextManager, mock_storage: MockStorage
    ) -> None:
        """Test refresh_files method re-adds files from watched patterns."""
        manager = manager_with_mock_storage

        # Use a temporary directory for test files
        with tempfile.TemporaryDirectory() as tmpdir:
            temp_path = Path(tmpdir)

            # Create test files
            test_files = [
                temp_path / "test1.py",
                temp_path / "test2.py",
                temp_path / "test.txt",
            ]
            for f in test_files:
                f.touch()

            # Update manager's base_dir to temp directory
            manager.base_dir = temp_path

            # Set watched patterns
            manager.watched_patterns = {"*.py"}

            # Refresh files
            added = manager.refresh_files()

            # Should have added the .py files
            assert added == 2
            assert len(manager.files) == 2

    def test_apply_profile_idempotent(
        self, manager_with_mock_storage: ContextManager, mock_storage: MockStorage
    ) -> None:
        """Test that applying the same profile multiple times is idempotent."""
        manager = manager_with_mock_storage

        # Create a profile
        profile = Profile(
            name="idempotent-test",
            watched_patterns=["*.md", "docs/**/*.md"],
        )

        # Apply profile first time
        manager.apply_profile(profile, "test-profile")
        first_patterns = manager.watched_patterns.copy()

        # Apply profile second time
        manager.apply_profile(profile, "test-profile")
        second_patterns = manager.watched_patterns

        # Should be identical
        assert first_patterns == second_patterns
