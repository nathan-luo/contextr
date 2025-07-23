"""Unit tests for JsonStorage implementation."""

import json
import tempfile
from pathlib import Path

import pytest

from contextr.storage import JsonStorage


class TestJsonStorage:
    """Test cases for JsonStorage backend."""

    @pytest.fixture
    def temp_dir(self) -> Path:
        """Create a temporary directory for tests."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)

    @pytest.fixture
    def storage(self, temp_dir: Path) -> JsonStorage:
        """Create a JsonStorage instance with temp directory."""
        return JsonStorage(temp_dir)

    def test_init_creates_directory(self, temp_dir: Path) -> None:
        """Test that initialization creates the base directory."""
        sub_dir = temp_dir / "subdir"
        assert not sub_dir.exists()

        JsonStorage(sub_dir)
        assert sub_dir.exists()

    def test_save_and_load_simple_key(
        self, storage: JsonStorage, temp_dir: Path
    ) -> None:
        """Test saving and loading data with a simple key."""
        key = "test_key"
        data = {"name": "test", "value": 42, "items": ["a", "b", "c"]}

        # Save data
        storage.save(key, data)

        # Check file was created
        expected_file = temp_dir / "test_key.json"
        assert expected_file.exists()

        # Load data
        loaded = storage.load(key)
        assert loaded == data

    def test_save_and_load_nested_key(
        self, storage: JsonStorage, temp_dir: Path
    ) -> None:
        """Test saving and loading data with nested directory structure."""
        key = "states/my_state"
        data = {"files": ["file1.py", "file2.py"], "patterns": ["*.py"]}

        # Save data
        storage.save(key, data)

        # Check directory structure was created
        states_dir = temp_dir / "states"
        assert states_dir.exists()
        expected_file = states_dir / "my_state.json"
        assert expected_file.exists()

        # Load data
        loaded = storage.load(key)
        assert loaded == data

    def test_load_nonexistent_key(self, storage: JsonStorage) -> None:
        """Test loading a key that doesn't exist returns None."""
        result = storage.load("nonexistent")
        assert result is None

    def test_exists_method(self, storage: JsonStorage) -> None:
        """Test exists method for checking key existence."""
        key = "test_exists"

        # Key doesn't exist initially
        assert not storage.exists(key)

        # Save data
        storage.save(key, {"test": True})

        # Key exists now
        assert storage.exists(key)

    def test_delete_existing_key(self, storage: JsonStorage) -> None:
        """Test deleting an existing key."""
        key = "test_delete"
        data = {"delete": "me"}

        # Save data
        storage.save(key, data)
        assert storage.exists(key)

        # Delete key
        result = storage.delete(key)
        assert result is True
        assert not storage.exists(key)

    def test_delete_nonexistent_key(self, storage: JsonStorage) -> None:
        """Test deleting a non-existent key returns False."""
        result = storage.delete("nonexistent")
        assert result is False

    def test_list_keys_empty(self, storage: JsonStorage) -> None:
        """Test listing keys when storage is empty."""
        keys = storage.list_keys()
        assert keys == []

    def test_list_keys_simple(self, storage: JsonStorage) -> None:
        """Test listing all keys in storage."""
        # Save multiple keys
        storage.save("key1", {"data": 1})
        storage.save("key2", {"data": 2})
        storage.save("key3", {"data": 3})

        keys = storage.list_keys()
        assert sorted(keys) == ["key1", "key2", "key3"]

    def test_list_keys_with_prefix(self, storage: JsonStorage) -> None:
        """Test listing keys with a prefix filter."""
        # Save keys with different prefixes
        storage.save("test_1", {"data": 1})
        storage.save("test_2", {"data": 2})
        storage.save("prod_1", {"data": 3})

        # List with prefix
        test_keys = storage.list_keys("test")
        assert sorted(test_keys) == ["test_1", "test_2"]

        prod_keys = storage.list_keys("prod")
        assert prod_keys == ["prod_1"]

    def test_list_keys_nested_structure(self, storage: JsonStorage) -> None:
        """Test listing keys with nested directory structure."""
        # Save nested keys
        storage.save("states/state1", {"data": 1})
        storage.save("states/state2", {"data": 2})
        storage.save("configs/config1", {"data": 3})

        # List all states
        states = storage.list_keys("states/")
        assert sorted(states) == ["states/state1", "states/state2"]

        # List all configs
        configs = storage.list_keys("configs/")
        assert configs == ["configs/config1"]

    def test_save_overwrites_existing(self, storage: JsonStorage) -> None:
        """Test that save overwrites existing data."""
        key = "overwrite_test"

        # Save initial data
        storage.save(key, {"version": 1})
        assert storage.load(key) == {"version": 1}

        # Overwrite with new data
        storage.save(key, {"version": 2})
        assert storage.load(key) == {"version": 2}

    def test_json_formatting(self, storage: JsonStorage, temp_dir: Path) -> None:
        """Test that JSON files are properly formatted."""
        key = "format_test"
        data = {"name": "test", "items": ["a", "b"], "count": 42}

        storage.save(key, data)

        # Read file directly to check formatting
        file_path = temp_dir / "format_test.json"
        with open(file_path, "r") as f:
            content = f.read()

        # Check indentation and sorting
        assert "    " in content  # 4-space indentation
        parsed = json.loads(content)
        assert list(parsed.keys()) == sorted(parsed.keys())  # Keys are sorted

    def test_error_handling_save(self, temp_dir: Path) -> None:
        """Test error handling when save fails."""
        storage = JsonStorage(temp_dir)

        # Make directory read-only to cause save failure
        temp_dir.chmod(0o444)

        try:
            with pytest.raises(IOError, match="Failed to save data"):
                storage.save("test", {"data": "value"})
        finally:
            # Restore permissions for cleanup
            temp_dir.chmod(0o755)

    def test_error_handling_load_corrupt_json(
        self, storage: JsonStorage, temp_dir: Path
    ) -> None:
        """Test error handling when JSON file is corrupted."""
        # Create a corrupted JSON file
        file_path = temp_dir / "corrupt.json"
        with open(file_path, "w") as f:
            f.write("{invalid json}")

        with pytest.raises(IOError, match="Failed to parse JSON"):
            storage.load("corrupt")
