"""Shared pytest fixtures for contextr tests."""

from pathlib import Path

import pytest


@pytest.fixture
def tmp_project(tmp_path: Path) -> Path:
    """Create a temporary project directory with basic structure."""
    # Create project structure
    src_dir = tmp_path / "src"
    src_dir.mkdir()

    # Create some sample files
    (src_dir / "main.py").write_text("print('Hello, World!')")
    (src_dir / "utils.py").write_text("def helper(): pass")

    # Create .git directory to simulate a git project
    git_dir = tmp_path / ".git"
    git_dir.mkdir()

    return tmp_path


@pytest.fixture
def sample_ignore_patterns() -> list[str]:
    """Provide sample ignore patterns for testing."""
    return [
        "*.pyc",
        "__pycache__/",
        ".git/",
        "*.log",
        "build/",
        "dist/",
    ]
