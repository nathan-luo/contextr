"""Unit tests for ContextManager with storage abstraction."""

import tempfile
from pathlib import Path
from typing import Any, Dict, List, Optional
from unittest.mock import patch

import pytest

from contextr.manager import ContextManager
from contextr.storage import StorageBackend


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
        """Test that add_files saves state through storage."""
        manager = manager_with_mock_storage

        with patch("contextr.manager.normalize_paths") as mock_normalize:
            mock_normalize.return_value = ["/test/dir/new_file.py"]
            with patch("pathlib.Path.is_file", return_value=True):
                manager.add_files(["new_file.py"])

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
        assert "/test/dir/loaded_file.py" in manager.files
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
