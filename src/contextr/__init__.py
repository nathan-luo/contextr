"""
contextr - A tool for managing and exporting file contexts
"""

from .formatters import format_export_content as format_export_content
from .formatters import get_file_tree as get_file_tree
from .manager import ContextManager as ContextManager
from .profile import ProfileManager as ProfileManager

# Resolve version from installed package; fallback during dev/tests
try:
    from importlib.metadata import PackageNotFoundError
    from importlib.metadata import version as _pkg_version

    try:
        __version__ = _pkg_version("contextr")
    except PackageNotFoundError:
        __version__ = "0.0.0+unknown"
except Exception:
    __version__ = "0.0.0+unknown"

__all__ = ["ContextManager", "ProfileManager", "format_export_content", "get_file_tree"]
