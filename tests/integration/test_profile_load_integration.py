"""Integration tests for profile loading functionality."""

import os
import tempfile
from pathlib import Path
from typing import Generator

import pytest

from contextr.manager import ContextManager
from contextr.profile import ProfileManager, ProfileNotFoundError
from contextr.storage import JsonStorage


@pytest.fixture
def temp_dir() -> Generator[Path, None, None]:
    """Create a temporary directory for tests."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def context_manager(temp_dir: Path) -> ContextManager:
    """Create a ContextManager with real storage."""
    storage = JsonStorage(temp_dir / ".contextr")
    # Change to temp directory for tests
    original_cwd = os.getcwd()
    os.chdir(temp_dir)
    manager = ContextManager(storage=storage)
    yield manager
    # Restore original directory
    os.chdir(original_cwd)


@pytest.fixture
def profile_manager(context_manager: ContextManager) -> ProfileManager:
    """Create a ProfileManager using the same storage as ContextManager."""
    return ProfileManager(
        storage=context_manager.storage, base_dir=context_manager.base_dir
    )


class TestProfileLoadIntegration:
    """Integration tests for loading profiles."""

    def test_save_and_load_profile_workflow(
        self,
        context_manager: ContextManager,
        profile_manager: ProfileManager,
        temp_dir: Path,
    ) -> None:
        """Test complete workflow: save profile, clear context, load profile."""
        # Create test files
        src_dir = temp_dir / "src"
        src_dir.mkdir()
        test_files = [
            src_dir / "main.py",
            src_dir / "utils.py",
            temp_dir / "README.md",
            temp_dir / "test.txt",
        ]
        for f in test_files:
            f.touch()

        # Set up initial context
        context_manager.watch_paths(["src/*.py", "*.md"])
        context_manager.add_ignore_patterns(["*.txt"])

        # Verify initial state
        assert len(context_manager.files) == 3  # 2 .py files + 1 .md file
        assert len(context_manager.watched_patterns) == 2
        assert len(context_manager.list_ignore_patterns()) == 1

        # Save profile
        profile_manager.save_profile(
            name="test-profile",
            watched_patterns=list(context_manager.watched_patterns),
            description="Test profile for integration test",
        )

        # Clear context
        context_manager.clear()
        assert len(context_manager.files) == 0
        assert len(context_manager.watched_patterns) == 0
        # Ignores are repo-level; clear preserves them
        assert len(context_manager.list_ignore_patterns()) == 1

        # Load profile
        profile = profile_manager.load_profile("test-profile")
        context_manager.apply_profile(profile, "test-profile")

        # Verify restored state
        assert len(context_manager.files) == 3  # Files should be refreshed
        assert context_manager.watched_patterns == {"src/*.py", "*.md"}
        assert set(context_manager.list_ignore_patterns()) == {"*.txt"}

    def test_load_non_existent_profile(self, profile_manager: ProfileManager) -> None:
        """Test loading a profile that doesn't exist."""
        with pytest.raises(ProfileNotFoundError) as exc_info:
            profile_manager.load_profile("non-existent")

        assert "Profile 'non-existent' not found" in str(exc_info.value)
        assert "ctxr profile list" in str(exc_info.value)

    def test_profile_isolation(
        self,
        context_manager: ContextManager,
        profile_manager: ProfileManager,
        temp_dir: Path,
    ) -> None:
        """Test that different profiles maintain separate contexts."""
        # Create test files
        (temp_dir / "frontend.js").touch()
        (temp_dir / "backend.py").touch()
        (temp_dir / "styles.css").touch()

        # Create and save frontend profile
        context_manager.watch_paths(["*.js", "*.css"])
        profile_manager.save_profile(
            name="frontend",
            watched_patterns=list(context_manager.watched_patterns),
        )

        # Create and save backend profile
        context_manager.clear()
        context_manager.watch_paths(["*.py"])
        profile_manager.save_profile(
            name="backend",
            watched_patterns=list(context_manager.watched_patterns),
        )

        # Load frontend profile
        frontend_profile = profile_manager.load_profile("frontend")
        context_manager.apply_profile(frontend_profile, "frontend")
        assert len(context_manager.files) == 2  # .js and .css files
        assert all(
            f.endswith((".js", ".css"))
            for f in context_manager.get_file_paths(relative=False)
        )

        # Load backend profile
        backend_profile = profile_manager.load_profile("backend")
        context_manager.apply_profile(backend_profile, "backend")
        assert len(context_manager.files) == 1  # Only .py file
        assert all(
            f.endswith(".py") for f in context_manager.get_file_paths(relative=False)
        )

    def test_profile_with_complex_patterns(
        self,
        context_manager: ContextManager,
        profile_manager: ProfileManager,
        temp_dir: Path,
    ) -> None:
        """Test profile with complex glob patterns."""
        # Create nested directory structure
        src_dir = temp_dir / "src"
        src_py_dir = src_dir / "python"
        src_js_dir = src_dir / "javascript"
        test_dir = temp_dir / "tests"

        for d in [src_py_dir, src_js_dir, test_dir]:
            d.mkdir(parents=True)

        # Create files
        files = [
            src_py_dir / "main.py",
            src_py_dir / "utils.py",
            src_js_dir / "app.js",
            src_js_dir / "helpers.js",
            test_dir / "test_main.py",
            test_dir / "test_utils.py",
            temp_dir / "README.md",
            temp_dir / "setup.py",
        ]
        for f in files:
            f.touch()

        # Set up complex patterns
        patterns = [
            "src/**/*.py",
            "tests/**/*.py",
            "*.md",
            "setup.py",
        ]
        ignore_patterns = ["**/__pycache__", "*.pyc"]

        context_manager.watch_paths(patterns)
        context_manager.add_ignore_patterns(ignore_patterns)

        # Save profile
        profile_manager.save_profile(
            name="python-project",
            watched_patterns=list(context_manager.watched_patterns),
        )

        # Clear and reload
        context_manager.clear()
        profile = profile_manager.load_profile("python-project")
        context_manager.apply_profile(profile, "python-project")

        # Verify Python files and README are included and ignores remained repo-level
        assert len(context_manager.files) == 6  # 4 .py files + 1 .md + setup.py
        file_paths = context_manager.get_file_paths(relative=True)
        assert any("main.py" in f for f in file_paths)
        assert any("test_main.py" in f for f in file_paths)
        assert "README.md" in file_paths
        assert set(context_manager.list_ignore_patterns()) == set(ignore_patterns)

    def test_profile_data_validation_on_load(
        self,
        context_manager: ContextManager,
        profile_manager: ProfileManager,
    ) -> None:
        """Test that profile data is validated when loaded."""
        # Save a valid profile first
        profile_manager.save_profile(
            name="valid-profile",
            watched_patterns=["*.py"],
        )

        # Corrupt the profile data directly in storage
        key = "profiles/valid-profile"
        corrupted_data = {"invalid": "data", "missing": "required_fields"}
        context_manager.storage.save(key, corrupted_data)

        # Attempt to load corrupted profile
        with pytest.raises(Exception):  # Could be ProfileError or KeyError
            profile_manager.load_profile("valid-profile")

    def test_profile_load_preserves_metadata(
        self,
        profile_manager: ProfileManager,
    ) -> None:
        """Test that profile metadata is preserved through save/load cycle."""
        # Save profile with metadata
        description = "This is a test profile with metadata"
        profile_manager.save_profile(
            name="metadata-test",
            watched_patterns=["src/**/*.py"],
            description=description,
        )

        # Load profile
        loaded_profile = profile_manager.load_profile("metadata-test")

        # Verify metadata
        assert loaded_profile.metadata["description"] == description
        assert "created_at" in loaded_profile.metadata
        assert "updated_at" in loaded_profile.metadata
