"""Unit tests for CLI commands."""

from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

import pytest
from typer.testing import CliRunner

from contextr.cli import app


@pytest.fixture
def runner():
    """Create a CLI runner for testing."""
    return CliRunner()


@pytest.fixture
def mock_context_manager():
    """Mock the global context manager."""
    with patch("contextr.cli.context_manager") as mock_cm:
        mock_cm.base_dir = Path("/test/dir")
        mock_cm.current_profile_name = None
        mock_cm.is_dirty = False
        mock_cm.files = set()
        mock_cm.watched_patterns = set()
        mock_cm.list_ignore_patterns = MagicMock(return_value=[])
        yield mock_cm


class TestGisCommand:
    """Test the gis command and its backward compatibility alias."""

    def test_gis_command_success(self, runner, mock_context_manager):
        """Test successful gitignore sync with gis command."""
        # Setup mocks
        mock_context_manager.base_dir = Path("/test/dir")

        with patch.object(Path, "exists") as mock_exists:
            mock_exists.return_value = True
            mock_context_manager.sync_gitignore.return_value = (
                3,
                ["*.log", "*.tmp", "*.cache"],
            )

            # Run command
            result = runner.invoke(app, ["gis"])

            # Verify
            assert result.exit_code == 0
            assert "Added 3 new patterns from .gitignore:" in result.stdout
            assert "+ *.log" in result.stdout
            assert "+ *.tmp" in result.stdout
            assert "+ *.cache" in result.stdout
            assert "Total ignore patterns now:" in result.stdout
            mock_context_manager.sync_gitignore.assert_called_once()

    def test_gis_command_no_gitignore(self, runner, mock_context_manager):
        """Test gis command when no .gitignore file exists."""
        # Setup mocks
        mock_context_manager.base_dir = Path("/test/dir")

        with patch.object(Path, "exists") as mock_exists:
            mock_exists.return_value = False

            # Run command
            result = runner.invoke(app, ["gis"])

            # Verify
            assert result.exit_code == 0
            assert "No .gitignore file found in current directory!" in result.stdout
            mock_context_manager.sync_gitignore.assert_not_called()

    def test_gis_command_no_new_patterns(self, runner, mock_context_manager):
        """Test gis command when no new patterns to sync."""
        # Setup mocks
        mock_context_manager.base_dir = Path("/test/dir")

        with patch.object(Path, "exists") as mock_exists:
            mock_exists.return_value = True
            mock_context_manager.sync_gitignore.return_value = (0, [])
            mock_context_manager.list_ignore_patterns.return_value = ["*.log", "*.tmp"]

            # Run command
            result = runner.invoke(app, ["gis"])

            # Verify
            assert result.exit_code == 0
            assert "No new patterns to sync from .gitignore" in result.stdout
            assert "All patterns already in ignore list" in result.stdout
            assert "(2 total)" in result.stdout
            mock_context_manager.sync_gitignore.assert_called_once()

    def test_gitignore_sync_backward_compatibility(self, runner, mock_context_manager):
        """Test that gitignore-sync still works as hidden alias."""
        # Setup mocks
        mock_context_manager.base_dir = Path("/test/dir")

        with patch.object(Path, "exists") as mock_exists:
            mock_exists.return_value = True
            mock_context_manager.sync_gitignore.return_value = (2, ["*.bak", "temp/"])

            # Run command using old name
            result = runner.invoke(app, ["gitignore-sync"])

            # Verify it works the same way
            assert result.exit_code == 0
            assert "Added 2 new patterns from .gitignore:" in result.stdout
            assert "*.bak" in result.stdout
            assert "temp/" in result.stdout
            mock_context_manager.sync_gitignore.assert_called_once()

    def test_gis_not_shown_in_help_gitignore_sync_hidden(self, runner):
        """Test that gis is shown in help but gitignore-sync is hidden."""
        # Get main help
        result = runner.invoke(app, ["--help"])

        # Verify gis is shown and gitignore-sync is not
        assert "gis" in result.stdout
        assert "gitignore-sync" not in result.stdout
        assert result.exit_code == 0


class TestStatusCommand:
    """Test the status command and profile state tracking."""

    def test_status_no_profile(self, runner, mock_context_manager):
        """Test status command when no profile is loaded."""
        # Setup
        mock_context_manager.current_profile_name = None
        mock_context_manager.is_dirty = False
        mock_context_manager.files = {"file1.py", "file2.py"}
        mock_context_manager.watched_patterns = {"src/**/*.py"}
        mock_context_manager.list_ignore_patterns.return_value = ["*.log", "*.tmp"]

        # Run command
        result = runner.invoke(app, ["status"])

        # Verify
        assert result.exit_code == 0
        assert "Current Profile: None" in result.stdout
        assert "Files in context: 2" in result.stdout
        assert "Watched patterns: 1" in result.stdout
        assert "Ignore patterns: 2" in result.stdout
        assert "unsaved changes" not in result.stdout

    def test_status_with_clean_profile(self, runner, mock_context_manager):
        """Test status command with a clean profile loaded."""
        # Setup
        mock_context_manager.current_profile_name = "frontend"
        mock_context_manager.is_dirty = False
        mock_context_manager.files = {"src/app.js", "src/index.js"}
        mock_context_manager.watched_patterns = {"src/**/*.js"}
        mock_context_manager.list_ignore_patterns.return_value = ["node_modules/"]

        # Run command
        result = runner.invoke(app, ["status"])

        # Verify
        assert result.exit_code == 0
        assert "Current Profile: frontend" in result.stdout
        assert "*" not in result.stdout  # No asterisk for clean profile
        assert "Files in context: 2" in result.stdout
        assert "unsaved changes" not in result.stdout

    def test_status_with_dirty_profile(self, runner, mock_context_manager):
        """Test status command with unsaved changes."""
        # Setup
        mock_context_manager.current_profile_name = "backend"
        mock_context_manager.is_dirty = True
        mock_context_manager.files = {"main.py", "utils.py", "test.py"}
        mock_context_manager.watched_patterns = {"*.py", "src/**/*.py"}

        # Run command
        result = runner.invoke(app, ["status"])

        # Verify
        assert result.exit_code == 0
        assert "Current Profile: backend" in result.stdout
        assert "*" in result.stdout  # Asterisk indicates unsaved changes
        assert "You have unsaved changes" in result.stdout
        assert "ctxr profile save" in result.stdout


class TestProfileStateTracking:
    """Test profile state tracking integration."""

    def test_profile_save_updates_current_profile(self, runner, mock_context_manager):
        """Test that saving a profile updates the current profile name."""
        # Setup mocks
        mock_context_manager.reset_dirty_state = MagicMock()
        mock_context_manager.storage = MagicMock()
        # Profile doesn't exist
        mock_context_manager.storage.exists.return_value = False

        with patch("contextr.cli.ProfileManager") as MockPM:
            mock_pm_instance = MockPM.return_value
            mock_pm_instance.save_profile.return_value = True

            # Run command
            result = runner.invoke(app, ["profile", "save", "myprofile"])

            # Verify profile tracking was updated
            assert result.exit_code == 0
            assert mock_context_manager.current_profile_name == "myprofile"
            mock_context_manager.reset_dirty_state.assert_called_once()

    def test_profile_save_without_name_uses_current(self, runner, mock_context_manager):
        """Test that profile save without name uses current profile."""
        # Setup
        mock_context_manager.current_profile_name = "existing-profile"
        mock_context_manager.watched_patterns = {"src/**/*.py"}
        mock_context_manager.reset_dirty_state = MagicMock()
        mock_context_manager.storage = MagicMock()
        # Profile exists, force update
        mock_context_manager.storage.exists.return_value = True

        with patch("contextr.cli.ProfileManager") as MockPM:
            mock_pm_instance = MockPM.return_value
            mock_pm_instance.save_profile.return_value = True

            # Run command without profile name with force flag
            result = runner.invoke(app, ["profile", "save", "--force"])

            # Verify it used the current profile name
            assert result.exit_code == 0
            assert "existing-profile" in result.stdout
            mock_pm_instance.save_profile.assert_called_once()
            call_args = mock_pm_instance.save_profile.call_args
            assert call_args[1]["name"] == "existing-profile"

    def test_profile_save_without_name_no_current(self, runner, mock_context_manager):
        """Test error when saving without name and no current profile."""
        # Setup
        mock_context_manager.current_profile_name = None

        # Run command without profile name
        result = runner.invoke(app, ["profile", "save"])

        # Verify error message
        assert result.exit_code == 0
        assert "No profile name provided" in result.stdout
        assert "no current profile loaded" in result.stdout

    def test_profile_list_shows_current_profile(self, runner, mock_context_manager):
        """Test that profile list shows current profile indicator."""
        # Setup
        mock_context_manager.current_profile_name = "active-profile"
        mock_context_manager.is_dirty = False

        with patch("contextr.cli.ProfileManager") as MockPM:
            mock_pm_instance = MockPM.return_value
            mock_pm_instance.list_profiles.return_value = [
                {"name": "profile1", "metadata": {}},
                {"name": "active-profile", "metadata": {}},
                {"name": "profile3", "metadata": {}},
            ]
            mock_pm_instance.format_profiles_table.return_value = Mock()

            # Run command
            result = runner.invoke(app, ["profile", "list"])

            # Verify
            assert result.exit_code == 0
            assert "Current profile: active-profile" in result.stdout
            assert "unsaved changes" not in result.stdout

    def test_profile_list_shows_dirty_indicator(self, runner, mock_context_manager):
        """Test that profile list shows unsaved changes indicator."""
        # Setup
        mock_context_manager.current_profile_name = "dirty-profile"
        mock_context_manager.is_dirty = True

        with patch("contextr.cli.ProfileManager") as MockPM:
            mock_pm_instance = MockPM.return_value
            mock_pm_instance.list_profiles.return_value = [
                {"name": "dirty-profile", "metadata": {}},
            ]
            mock_pm_instance.format_profiles_table.return_value = Mock()

            # Run command
            result = runner.invoke(app, ["profile", "list"])

            # Verify
            assert result.exit_code == 0
            assert "Current profile: dirty-profile" in result.stdout
            assert "You have unsaved changes" in result.stdout


class TestProfileNewCommand:
    """Test the profile new command functionality."""

    def test_profile_new_basic(self, runner, mock_context_manager):
        """Test basic profile new command."""
        # Setup
        mock_context_manager.is_dirty = False
        mock_context_manager.clear = MagicMock()
        mock_context_manager.watch_paths = MagicMock()
        mock_context_manager.reset_dirty_state = MagicMock()
        mock_context_manager.files = {"src/app.py", "src/utils.py"}
        mock_context_manager.list_ignore_patterns.return_value = []

        with patch("contextr.cli.ProfileManager") as MockPM:
            mock_pm_instance = MockPM.return_value
            mock_pm_instance.save_profile.return_value = True

            # Simulate user input for interactive prompts
            with patch("typer.prompt") as mock_prompt:
                # Mock pattern entry
                mock_prompt.side_effect = ["src/**/*.py", ""]  # One pattern, then empty

                with patch("typer.confirm") as mock_confirm:
                    mock_confirm.return_value = True  # Confirm profile creation

                    # Run command
                    result = runner.invoke(
                        app, ["profile", "new", "--name", "test-profile"]
                    )

                    # Verify
                    assert result.exit_code == 0
                    assert "Starting new profile" in result.stdout
                    assert (
                        "Profile 'test-profile' created successfully!" in result.stdout
                    )
                    mock_context_manager.clear.assert_called_once()
                    mock_context_manager.watch_paths.assert_called_once_with(
                        ["src/**/*.py"]
                    )

    def test_profile_new_with_unsaved_changes(self, runner, mock_context_manager):
        """Test profile new prompts to save unsaved changes."""
        # Setup
        mock_context_manager.is_dirty = True
        mock_context_manager.current_profile_name = "old-profile"
        mock_context_manager.watched_patterns = {"old/**/*.py"}
        mock_context_manager.list_ignore_patterns.return_value = []
        mock_context_manager.clear = MagicMock()
        mock_context_manager.watch_paths = MagicMock()
        mock_context_manager.reset_dirty_state = MagicMock()

        with patch("contextr.cli.ProfileManager") as MockPM:
            mock_pm_instance = MockPM.return_value
            mock_pm_instance.save_profile.return_value = True

            with patch("typer.prompt") as mock_prompt:
                # First prompt: save changes? yes
                # Second/third prompts: pattern entry
                mock_prompt.side_effect = ["y", "new/**/*.js", ""]

                with patch("typer.confirm") as mock_confirm:
                    mock_confirm.return_value = True

                    # Run command
                    result = runner.invoke(
                        app, ["profile", "new", "--name", "new-profile"]
                    )

                    # Verify
                    assert result.exit_code == 0
                    assert "Saved changes to 'old-profile'" in result.stdout
                    # Verify save was called for old profile (without ignores)
                    # First call saves old profile, second saves new profile
                    assert mock_pm_instance.save_profile.call_count == 2
                    # First call should be old profile with old patterns
                    first_call = mock_pm_instance.save_profile.call_args_list[0]
                    assert first_call[1]["name"] == "old-profile"
                    assert first_call[1]["watched_patterns"] == ["old/**/*.py"]

    def test_profile_new_cancel_unsaved_changes(self, runner, mock_context_manager):
        """Test cancelling profile new when unsaved changes exist."""
        # Setup
        mock_context_manager.is_dirty = True
        mock_context_manager.current_profile_name = "current-profile"

        with patch("typer.prompt") as mock_prompt:
            mock_prompt.return_value = "cancel"

            # Run command
            result = runner.invoke(app, ["profile", "new", "--name", "new-profile"])

            # Verify
            assert result.exit_code == 1  # Aborted
            assert "Profile creation cancelled" in result.stdout

    def test_profile_new_no_patterns(self, runner, mock_context_manager):
        """Test profile new with no patterns provided."""
        # Setup
        mock_context_manager.is_dirty = False
        mock_context_manager.clear = MagicMock()
        mock_context_manager.list_ignore_patterns.return_value = []

        with patch("typer.prompt") as mock_prompt:
            mock_prompt.return_value = ""  # No patterns

            # Run command
            result = runner.invoke(app, ["profile", "new", "--name", "empty-profile"])

            # Verify
            assert result.exit_code == 1  # Aborted
            assert "No watch patterns provided" in result.stdout
