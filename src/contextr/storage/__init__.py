"""Storage backend abstractions for contextr."""

from .base import StorageBackend
from .json_storage import JsonStorage

__all__ = ["StorageBackend", "JsonStorage"]
