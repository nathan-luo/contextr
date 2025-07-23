"""Abstract base class for storage backends."""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional


class StorageBackend(ABC):
    """Abstract base class for storage backends.

    Provides interface for saving and loading data with arbitrary keys.
    Implementations should handle serialization and persistence.
    """

    @abstractmethod
    def save(self, key: str, data: Dict[str, Any]) -> None:
        """Save data with given key.

        Args:
            key: Unique identifier for the data
            data: Dictionary of data to save

        Raises:
            IOError: If save operation fails
        """
        pass

    @abstractmethod
    def load(self, key: str) -> Optional[Dict[str, Any]]:
        """Load data by key.

        Args:
            key: Unique identifier for the data

        Returns:
            Optional[Dict[str, Any]]: The loaded data, or None if key doesn't exist

        Raises:
            IOError: If load operation fails (but not if key doesn't exist)
        """
        pass

    @abstractmethod
    def exists(self, key: str) -> bool:
        """Check if a key exists in storage.

        Args:
            key: Unique identifier to check

        Returns:
            bool: True if key exists, False otherwise
        """
        pass

    @abstractmethod
    def delete(self, key: str) -> bool:
        """Delete data associated with a key.

        Args:
            key: Unique identifier for the data to delete

        Returns:
            bool: True if deletion was successful, False if key didn't exist

        Raises:
            IOError: If delete operation fails
        """
        pass

    @abstractmethod
    def list_keys(self, prefix: str = "") -> List[str]:
        """List all keys in storage with optional prefix filter.

        Args:
            prefix: Optional prefix to filter keys

        Returns:
            List[str]: List of keys matching the prefix
        """
        pass
