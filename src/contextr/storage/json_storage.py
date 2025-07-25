"""JSON file-based storage backend implementation."""

import json
from pathlib import Path
from typing import Any, Dict, List, Optional

from .base import StorageBackend


class JsonStorage(StorageBackend):
    """JSON file-based storage backend.

    Stores data as JSON files in a specified directory.
    Each key maps to a separate JSON file.
    """

    def __init__(self, base_path: Path) -> None:
        """Initialize JSON storage backend.

        Args:
            base_path: Base directory for storing JSON files
        """
        self.base_path = base_path
        self.base_path.mkdir(parents=True, exist_ok=True)

    def _get_file_path(self, key: str) -> Path:
        """Get file path for a given key.

        Args:
            key: Storage key

        Returns:
            Path: File path for the key
        """
        # Handle nested directory structure in keys
        if "/" in key:
            parts = key.split("/")
            dir_path = self.base_path
            for part in parts[:-1]:
                dir_path = dir_path / part
            dir_path.mkdir(parents=True, exist_ok=True)
            filename = parts[-1]
            if not filename.endswith(".json"):
                filename += ".json"
            return dir_path / filename
        else:
            # Simple key without directory structure
            if not key.endswith(".json"):
                key += ".json"
            return self.base_path / key

    def save(self, key: str, data: Dict[str, Any]) -> None:
        """Save data to JSON file with atomic write operation.

        Args:
            key: Unique identifier for the data
            data: Dictionary of data to save

        Raises:
            IOError: If save operation fails
        """
        file_path = self._get_file_path(key)
        temp_path = file_path.with_suffix(".tmp")

        try:
            # Write to temporary file first
            with open(temp_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=4, sort_keys=True)

            # Atomically rename temp file to target file
            temp_path.replace(file_path)
        except (IOError, OSError) as e:
            # Clean up temp file if it exists
            try:
                if temp_path.exists():
                    temp_path.unlink()
            except OSError:
                pass
            raise IOError(f"Failed to save data: {e}") from e

    def load(self, key: str) -> Optional[Dict[str, Any]]:
        """Load data from JSON file.

        Args:
            key: Unique identifier for the data

        Returns:
            Optional[Dict[str, Any]]: The loaded data, or None if key doesn't exist

        Raises:
            IOError: If load operation fails (but not if key doesn't exist)
        """
        file_path = self._get_file_path(key)
        if not file_path.exists():
            return None

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            return data
        except json.JSONDecodeError as e:
            raise IOError(f"Failed to parse JSON: {e}") from e
        except (IOError, OSError) as e:
            raise IOError(f"Failed to load data: {e}") from e

    def exists(self, key: str) -> bool:
        """Check if a key exists in storage.

        Args:
            key: Unique identifier to check

        Returns:
            bool: True if key exists, False otherwise
        """
        file_path = self._get_file_path(key)
        return file_path.exists()

    def delete(self, key: str) -> bool:
        """Delete JSON file associated with a key.

        Args:
            key: Unique identifier for the data to delete

        Returns:
            bool: True if deletion was successful, False if key didn't exist

        Raises:
            IOError: If delete operation fails
        """
        file_path = self._get_file_path(key)
        if not file_path.exists():
            return False

        try:
            file_path.unlink()
            return True
        except OSError as e:
            raise IOError(f"Failed to delete file: {e}") from e

    def list_keys(self, prefix: str = "") -> List[str]:
        """List all keys in storage with optional prefix filter.

        Args:
            prefix: Optional prefix to filter keys

        Returns:
            List[str]: List of keys matching the prefix
        """
        keys: List[str] = []

        # Handle nested directory structure for prefixes like "states/"
        if prefix and "/" in prefix:
            prefix_parts = prefix.split("/")
            search_dir = self.base_path
            for part in prefix_parts[:-1]:
                search_dir = search_dir / part
            if search_dir.exists():
                pattern = f"{prefix_parts[-1]}*.json" if prefix_parts[-1] else "*.json"
                for file_path in search_dir.glob(pattern):
                    # Reconstruct the full key
                    relative_path = file_path.relative_to(self.base_path)
                    key = str(relative_path).replace("\\", "/")
                    if key.endswith(".json"):
                        key = key[:-5]  # Remove .json extension
                    keys.append(key)
        else:
            # Search in base directory
            pattern = f"{prefix}*.json" if prefix else "*.json"
            for file_path in self.base_path.glob(pattern):
                if file_path.is_file():
                    key = file_path.stem
                    keys.append(key)

        return sorted(keys)
