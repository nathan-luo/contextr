"""Unit tests for CLI profile commands."""

from pathlib import Path
from unittest.mock import Mock, patch

import pytest
from typer.testing import CliRunner

from contextr.cli import app
from contextr.profile import Profile, ProfileNotFoundError


@pytest.fixture
def runner() -> CliRunner:
    """Create a CLI test runner."""
    return CliRunner()


@pytest.fixture
def mock_context_manager() -> Mock:
    """Mock context manager for testing."""
    mock = Mock()
    mock.storage = Mock()
    mock.base_dir = Path("/test/dir")
    mock.watched_patterns = ["*.py", "*.md"]
    mock.list_ignore_patterns.return_value = ["*.pyc", "__pycache__"]
    mock.files = []
    return mock


@pytest.fixture
def sample_profile() -> Profile:
    """Create a sample profile for testing."""
    return Profile(
        name="test-profile",
        watched_patterns=["*.py", "*.md"],
        ignore_patterns=["*.pyc", "__pycache__"],
        metadata={
            "created_at": "2025-07-25T12:00:00Z",
            "updated_at": "2025-07-25T12:00:00Z",
            "description": "Test profile description",
        },
    )


class TestProfileDeleteCommand:
    """Test the profile delete command."""

    @patch("contextr.cli.context_manager")
    @patch("contextr.cli.ProfileManager")
    def test_delete_profile_with_confirmation(
        self,
        mock_profile_manager_class: Mock,
        mock_context_manager: Mock,
        runner: CliRunner,
        sample_profile: Profile,
    ) -> None:
        """Test deleting a profile with user confirmation."""
        # Setup mocks
        mock_context_manager.storage = Mock()
        mock_context_manager.base_dir = Path("/test/dir")
        mock_profile_manager = Mock()
        mock_profile_manager_class.return_value = mock_profile_manager
        mock_profile_manager.load_profile.return_value = sample_profile
        mock_profile_manager.delete_profile.return_value = True

        # Run command with confirmation
        result = runner.invoke(app, ["profile", "delete", "test-profile"], input="y\n")

        assert result.exit_code == 0
        assert "Profile: test-profile" in result.output
        assert "Description: Test profile description" in result.output
        assert "Watched patterns: 2" in result.output
        assert "Ignore patterns: 2" in result.output
        assert "Created: 2025-07-25 12:00" in result.output
        assert "Delete profile 'test-profile'?" in result.output
        assert "✓ Profile 'test-profile' deleted successfully!" in result.output

        mock_profile_manager.load_profile.assert_called_once_with("test-profile")
        mock_profile_manager.delete_profile.assert_called_once_with("test-profile")

    @patch("contextr.cli.context_manager")
    @patch("contextr.cli.ProfileManager")
    def test_delete_profile_with_force(
        self,
        mock_profile_manager_class: Mock,
        mock_context_manager: Mock,
        runner: CliRunner,
        sample_profile: Profile,
    ) -> None:
        """Test deleting a profile with --force flag."""
        # Setup mocks
        mock_context_manager.storage = Mock()
        mock_context_manager.base_dir = Path("/test/dir")
        mock_profile_manager = Mock()
        mock_profile_manager_class.return_value = mock_profile_manager
        mock_profile_manager.load_profile.return_value = sample_profile
        mock_profile_manager.delete_profile.return_value = True

        # Run command with --force flag
        result = runner.invoke(app, ["profile", "delete", "test-profile", "--force"])

        assert result.exit_code == 0
        assert "Profile: test-profile" in result.output
        assert "Delete profile 'test-profile'?" not in result.output
        assert "✓ Profile 'test-profile' deleted successfully!" in result.output

        mock_profile_manager.load_profile.assert_called_once_with("test-profile")
        mock_profile_manager.delete_profile.assert_called_once_with("test-profile")

    @patch("contextr.cli.context_manager")
    @patch("contextr.cli.ProfileManager")
    def test_delete_profile_cancelled(
        self,
        mock_profile_manager_class: Mock,
        mock_context_manager: Mock,
        runner: CliRunner,
        sample_profile: Profile,
    ) -> None:
        """Test cancelling profile deletion."""
        # Setup mocks
        mock_context_manager.storage = Mock()
        mock_context_manager.base_dir = Path("/test/dir")
        mock_profile_manager = Mock()
        mock_profile_manager_class.return_value = mock_profile_manager
        mock_profile_manager.load_profile.return_value = sample_profile

        # Run command and cancel
        result = runner.invoke(app, ["profile", "delete", "test-profile"], input="n\n")

        assert result.exit_code == 1
        assert "Profile: test-profile" in result.output
        assert "Delete profile 'test-profile'?" in result.output
        assert "Profile deletion cancelled." in result.output

        mock_profile_manager.load_profile.assert_called_once_with("test-profile")
        mock_profile_manager.delete_profile.assert_not_called()

    @patch("contextr.cli.context_manager")
    @patch("contextr.cli.ProfileManager")
    def test_delete_profile_not_found(
        self,
        mock_profile_manager_class: Mock,
        mock_context_manager: Mock,
        runner: CliRunner,
    ) -> None:
        """Test deleting a non-existent profile."""
        # Setup mocks
        mock_context_manager.storage = Mock()
        mock_context_manager.base_dir = Path("/test/dir")
        mock_profile_manager = Mock()
        mock_profile_manager_class.return_value = mock_profile_manager
        mock_profile_manager.load_profile.side_effect = ProfileNotFoundError(
            "Profile 'nonexistent' not found. "
            "Use 'ctxr profile list' to see available profiles."
        )

        # Run command
        result = runner.invoke(app, ["profile", "delete", "nonexistent"])

        assert result.exit_code == 1
        assert "Profile 'nonexistent' not found." in result.output
        assert "Use 'ctxr profile list' to see available profiles." in result.output

        mock_profile_manager.load_profile.assert_called_once_with("nonexistent")
        mock_profile_manager.delete_profile.assert_not_called()

    @patch("contextr.cli.context_manager")
    @patch("contextr.cli.ProfileManager")
    def test_delete_profile_without_description(
        self,
        mock_profile_manager_class: Mock,
        mock_context_manager: Mock,
        runner: CliRunner,
    ) -> None:
        """Test deleting a profile without description."""
        # Setup mocks
        mock_context_manager.storage = Mock()
        mock_context_manager.base_dir = Path("/test/dir")
        mock_profile_manager = Mock()
        mock_profile_manager_class.return_value = mock_profile_manager

        # Profile without description
        profile = Profile(
            name="no-desc",
            watched_patterns=["*.py"],
            ignore_patterns=[],
            metadata={
                "created_at": "2025-07-25T12:00:00Z",
                "updated_at": "2025-07-25T12:00:00Z",
            },
        )
        mock_profile_manager.load_profile.return_value = profile
        mock_profile_manager.delete_profile.return_value = True

        # Run command with force
        result = runner.invoke(app, ["profile", "delete", "no-desc", "--force"])

        assert result.exit_code == 0
        assert "Profile: no-desc" in result.output
        assert "Description:" not in result.output
        assert "✓ Profile 'no-desc' deleted successfully!" in result.output

    @patch("contextr.cli.context_manager")
    @patch("contextr.cli.ProfileManager")
    def test_delete_profile_with_invalid_date(
        self,
        mock_profile_manager_class: Mock,
        mock_context_manager: Mock,
        runner: CliRunner,
    ) -> None:
        """Test deleting a profile with invalid creation date."""
        # Setup mocks
        mock_context_manager.storage = Mock()
        mock_context_manager.base_dir = Path("/test/dir")
        mock_profile_manager = Mock()
        mock_profile_manager_class.return_value = mock_profile_manager

        # Profile with invalid date
        profile = Profile(
            name="bad-date",
            watched_patterns=["*.py"],
            ignore_patterns=[],
            metadata={
                "created_at": "invalid-date",
                "updated_at": "invalid-date",
                "description": "Test",
            },
        )
        mock_profile_manager.load_profile.return_value = profile
        mock_profile_manager.delete_profile.return_value = True

        # Run command with force
        result = runner.invoke(app, ["profile", "delete", "bad-date", "--force"])

        assert result.exit_code == 0
        assert "Profile: bad-date" in result.output
        assert "Created:" not in result.output  # Should skip invalid date
        assert "✓ Profile 'bad-date' deleted successfully!" in result.output

    @patch("contextr.cli.context_manager")
    @patch("contextr.cli.ProfileManager")
    def test_delete_profile_deletion_fails(
        self,
        mock_profile_manager_class: Mock,
        mock_context_manager: Mock,
        runner: CliRunner,
        sample_profile: Profile,
    ) -> None:
        """Test when profile deletion fails."""
        # Setup mocks
        mock_context_manager.storage = Mock()
        mock_context_manager.base_dir = Path("/test/dir")
        mock_profile_manager = Mock()
        mock_profile_manager_class.return_value = mock_profile_manager
        mock_profile_manager.load_profile.return_value = sample_profile
        mock_profile_manager.delete_profile.return_value = False

        # Run command with force
        result = runner.invoke(app, ["profile", "delete", "test-profile", "--force"])

        assert result.exit_code == 1
        assert "Failed to delete profile 'test-profile'" in result.output

        mock_profile_manager.delete_profile.assert_called_once_with("test-profile")
