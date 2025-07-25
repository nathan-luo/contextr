"""Unit tests for path_utils module."""

import os
from pathlib import Path

import pytest
from pytest_mock import MockerFixture

from contextr.utils.path_utils import make_absolute, make_relative, normalize_paths


class TestMakeRelative:
    """Test cases for make_relative function."""

    def test_simple_relative_path(self) -> None:
        """Test converting a simple absolute path to relative."""
        base_dir = Path("/home/user/project")
        path = "/home/user/project/src/main.py"
        result = make_relative(path, base_dir)
        expected = os.path.join("src", "main.py")
        assert result == expected

    def test_already_relative_path(self) -> None:
        """Test handling a path that's already relative."""
        base_dir = Path("/home/user/project")
        path = "/other/location/file.py"
        result = make_relative(path, base_dir)
        # Should return absolute path when can't make relative
        # Handle Windows absolute paths with drive letters
        expected = str(Path(path).resolve())
        assert result == expected

    def test_path_with_symlinks(self, tmp_path: Path) -> None:
        """Test handling paths with symlinks."""
        # Create a real directory and a symlink
        real_dir = tmp_path / "real"
        real_dir.mkdir()
        symlink_dir = tmp_path / "link"
        try:
            symlink_dir.symlink_to(real_dir)
        except OSError:
            # Skip test if symlinks are not supported (Windows without admin)
            pytest.skip("Symlinks not supported on this system")

        # Test path through symlink
        file_path = symlink_dir / "file.txt"
        result = make_relative(str(file_path), tmp_path)
        # Should resolve to real path with OS-specific separators
        expected = os.path.join("real", "file.txt")
        assert result == expected


class TestMakeAbsolute:
    """Test cases for make_absolute function."""

    def test_relative_path(self) -> None:
        """Test converting relative path to absolute."""
        base_dir = Path("/home/user/project")
        path = "src/main.py"
        result = make_absolute(path, base_dir)
        assert result == str((base_dir / path).resolve())

    def test_already_absolute_path(self) -> None:
        """Test handling already absolute path."""
        base_dir = Path("/home/user/project")
        path = "/other/location/file.py"
        result = make_absolute(path, base_dir)
        # Handle Windows absolute paths
        expected = str(Path(path).resolve())
        assert result == expected

    def test_home_expansion(self) -> None:
        """Test tilde expansion for home directory."""
        base_dir = Path("/home/user/project")
        path = "~/documents/file.txt"
        result = make_absolute(path, base_dir)
        # Should expand to user's home directory
        result_path = Path(result)
        home_path = Path.home()
        assert result_path.parts[: len(home_path.parts)] == home_path.parts
        # Check the relative part matches (case-insensitive for directory name)
        assert result_path.parts[-1] == "file.txt"
        assert result_path.parts[-2].lower() == "documents"

    def test_environment_variable_expansion(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test environment variable expansion."""
        base_dir = Path("/home/user/project")
        # Use a path that works on Windows
        test_path = str(Path("/custom/path").resolve())
        monkeypatch.setenv("TEST_DIR", test_path)
        path = "$TEST_DIR/file.txt"
        result = make_absolute(path, base_dir)
        expected = str((Path(test_path) / "file.txt").resolve())
        assert result == expected


class TestNormalizePaths:
    """Test cases for normalize_paths function."""

    def test_simple_file_patterns(self, tmp_path: Path) -> None:
        """Test normalizing simple file patterns."""
        # Create test files
        (tmp_path / "file1.py").touch()
        (tmp_path / "file2.py").touch()

        patterns = ["file1.py", "file2.py"]
        result = normalize_paths(patterns, tmp_path)

        assert len(result) == 2
        assert str(tmp_path / "file1.py") in result
        assert str(tmp_path / "file2.py") in result

    def test_glob_patterns(self, tmp_path: Path) -> None:
        """Test glob pattern expansion."""
        # Create test structure
        src_dir = tmp_path / "src"
        src_dir.mkdir()
        (src_dir / "main.py").touch()
        (src_dir / "utils.py").touch()
        (src_dir / "test.txt").touch()

        patterns = ["src/*.py"]
        result = normalize_paths(patterns, tmp_path)

        assert len(result) == 2
        assert str(src_dir / "main.py") in result
        assert str(src_dir / "utils.py") in result
        assert str(src_dir / "test.txt") not in result

    def test_nonexistent_path_warning(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """Test warning for non-existent paths."""
        patterns = ["nonexistent.py"]
        result = normalize_paths(patterns, tmp_path)

        assert len(result) == 0
        captured = capsys.readouterr()
        assert "Warning" in captured.out
        assert "does not exist" in captured.out

    def test_deduplication(self, tmp_path: Path) -> None:
        """Test that duplicate paths are removed."""
        # Create test file
        (tmp_path / "file.py").touch()

        # Add same file multiple times
        patterns = ["file.py", "./file.py", str(tmp_path / "file.py")]
        result = normalize_paths(patterns, tmp_path)

        # Should only have one entry
        assert len(result) == 1
        assert str(tmp_path / "file.py") in result

    def test_with_ignore_manager(self, tmp_path: Path, mocker: MockerFixture) -> None:
        """Test normalize_paths with ignore manager filtering."""
        # Create test files
        (tmp_path / "include.py").touch()
        (tmp_path / "exclude.py").touch()
        (tmp_path / "test.txt").touch()

        # Mock ignore manager
        mock_ignore_manager = mocker.Mock()
        mock_ignore_manager.should_ignore.side_effect = lambda path: "exclude" in path

        # Test with glob pattern
        patterns = ["*.py"]
        result = normalize_paths(patterns, tmp_path, mock_ignore_manager)

        assert len(result) == 1
        assert str(tmp_path / "include.py") in result
        assert str(tmp_path / "exclude.py") not in result

        # Test with direct file path
        patterns = ["exclude.py", "include.py"]
        result = normalize_paths(patterns, tmp_path, mock_ignore_manager)

        assert len(result) == 1
        assert str(tmp_path / "include.py") in result
        assert str(tmp_path / "exclude.py") not in result

    def test_glob_pattern_error_handling(
        self, tmp_path: Path, mocker: MockerFixture
    ) -> None:
        """Test error handling for glob pattern processing."""
        # Mock glob to raise an exception
        mock_glob = mocker.patch("contextr.utils.path_utils.Path.glob")
        mock_glob.side_effect = Exception("Glob error")

        patterns = ["*.py"]
        result = normalize_paths(patterns, tmp_path)

        # Should return empty list on error
        assert len(result) == 0

    def test_environment_variable_relative_path(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test environment variable that expands to relative path."""
        base_dir = tmp_path
        monkeypatch.setenv("TEST_REL_DIR", "relative/path")
        path = "$TEST_REL_DIR/file.txt"
        result = make_absolute(path, base_dir)

        # Should resolve relative path from base_dir
        expected = str((base_dir / "relative/path/file.txt").resolve())
        assert result == expected
