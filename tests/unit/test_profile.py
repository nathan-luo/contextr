"""Unit tests for profile management functionality."""

from datetime import datetime
from pathlib import Path
from typing import Any, Dict
from unittest.mock import Mock

import pytest

from contextr.profile import Profile, ProfileError, ProfileManager, ProfileNotFoundError
from contextr.storage import StorageBackend


@pytest.fixture
def mock_storage() -> Mock:
    """Create a mock storage backend."""
    return Mock(spec=StorageBackend)


@pytest.fixture
def profile_manager(mock_storage: Mock, tmp_path: Path) -> ProfileManager:
    """Create a ProfileManager instance with mocked storage."""
    return ProfileManager(storage=mock_storage, base_dir=tmp_path)


class TestProfile:
    """Test the Profile class."""

    def test_init_with_metadata(self) -> None:
        """Test Profile initialization with provided metadata."""
        metadata = {
            "created_at": "2025-07-25T12:00:00Z",
            "updated_at": "2025-07-25T12:00:00Z",
            "description": "Test profile",
        }
        profile = Profile(
            name="test",
            watched_patterns=["*.py"],
            ignore_patterns=["*.pyc"],
            metadata=metadata,
        )

        assert profile.name == "test"
        assert profile.watched_patterns == ["*.py"]
        assert profile.ignore_patterns == ["*.pyc"]
        assert profile.metadata == metadata

    def test_init_without_metadata(self) -> None:
        """Test Profile initialization without metadata."""
        profile = Profile(
            name="test", watched_patterns=["*.py"], ignore_patterns=["*.pyc"]
        )

        assert profile.name == "test"
        assert profile.watched_patterns == ["*.py"]
        assert profile.ignore_patterns == ["*.pyc"]
        assert "created_at" in profile.metadata
        assert "updated_at" in profile.metadata
        assert profile.metadata["description"] == ""

    def test_to_dict(self) -> None:
        """Test converting Profile to dictionary."""
        profile = Profile(
            name="test", watched_patterns=["*.py"], ignore_patterns=["*.pyc"]
        )
        data = profile.to_dict()

        assert data["name"] == "test"
        assert data["watched_patterns"] == ["*.py"]
        assert data["ignore_patterns"] == ["*.pyc"]
        assert "metadata" in data
        assert "created_at" in data["metadata"]

    def test_from_dict(self) -> None:
        """Test creating Profile from dictionary."""
        data = {
            "name": "test",
            "watched_patterns": ["*.py"],
            "ignore_patterns": ["*.pyc"],
            "metadata": {
                "created_at": "2025-07-25T12:00:00Z",
                "updated_at": "2025-07-25T12:00:00Z",
                "description": "Test profile",
            },
        }
        profile = Profile.from_dict(data)

        assert profile.name == "test"
        assert profile.watched_patterns == ["*.py"]
        assert profile.ignore_patterns == ["*.pyc"]
        assert profile.metadata["description"] == "Test profile"


class TestProfileManager:
    """Test the ProfileManager class."""

    def test_save_profile_valid_name(
        self, profile_manager: ProfileManager, mock_storage: Mock
    ) -> None:
        """Test saving a profile with valid name."""
        mock_storage.exists.return_value = False

        success = profile_manager.save_profile(
            name="test-profile",
            watched_patterns=["*.py"],
            ignore_patterns=["*.pyc"],
            description="Test description",
        )

        assert success is True
        mock_storage.save.assert_called_once()
        saved_key, saved_data = mock_storage.save.call_args[0]
        assert saved_key == "profiles/test-profile"
        assert saved_data["name"] == "test-profile"
        assert saved_data["watched_patterns"] == ["*.py"]
        assert saved_data["ignore_patterns"] == ["*.pyc"]
        assert saved_data["metadata"]["description"] == "Test description"

    def test_save_profile_invalid_name(self, profile_manager: ProfileManager) -> None:
        """Test saving a profile with invalid name."""
        with pytest.raises(ValueError) as exc_info:
            profile_manager.save_profile(
                name="test profile!",  # Invalid: contains space and !
                watched_patterns=["*.py"],
                ignore_patterns=["*.pyc"],
            )
        assert "Invalid profile name" in str(exc_info.value)

    def test_save_profile_overwrite_without_force(
        self, profile_manager: ProfileManager, mock_storage: Mock
    ) -> None:
        """Test saving over existing profile without force flag."""
        mock_storage.exists.return_value = True

        success = profile_manager.save_profile(
            name="existing", watched_patterns=["*.py"], ignore_patterns=["*.pyc"]
        )

        assert success is False
        mock_storage.save.assert_not_called()

    def test_save_profile_overwrite_with_force(
        self, profile_manager: ProfileManager, mock_storage: Mock
    ) -> None:
        """Test saving over existing profile with force flag."""
        mock_storage.exists.return_value = True
        existing_data = {
            "name": "existing",
            "watched_patterns": ["*.js"],
            "ignore_patterns": [],
            "metadata": {
                "created_at": "2025-07-25T10:00:00Z",
                "updated_at": "2025-07-25T10:00:00Z",
                "description": "Old description",
            },
        }
        mock_storage.load.return_value = existing_data

        success = profile_manager.save_profile(
            name="existing",
            watched_patterns=["*.py"],
            ignore_patterns=["*.pyc"],
            force=True,
        )

        assert success is True
        mock_storage.save.assert_called_once()
        saved_key, saved_data = mock_storage.save.call_args[0]
        assert saved_key == "profiles/existing"
        assert saved_data["watched_patterns"] == ["*.py"]
        # Should preserve original created_at
        assert saved_data["metadata"]["created_at"] == "2025-07-25T10:00:00Z"
        # Should update updated_at
        assert saved_data["metadata"]["updated_at"] != "2025-07-25T10:00:00Z"

    def test_save_profile_io_error(
        self, profile_manager: ProfileManager, mock_storage: Mock
    ) -> None:
        """Test save profile handling IOError."""
        mock_storage.exists.return_value = False
        mock_storage.save.side_effect = IOError("Storage error")

        success = profile_manager.save_profile(
            name="test", watched_patterns=["*.py"], ignore_patterns=[]
        )

        assert success is False

    def test_list_profiles_empty(
        self, profile_manager: ProfileManager, mock_storage: Mock
    ) -> None:
        """Test listing profiles when none exist."""
        mock_storage.list_keys.return_value = []

        profiles = profile_manager.list_profiles()

        assert profiles == []
        mock_storage.list_keys.assert_called_once_with("profiles/")

    def test_list_profiles_multiple(
        self, profile_manager: ProfileManager, mock_storage: Mock
    ) -> None:
        """Test listing multiple profiles."""
        mock_storage.list_keys.return_value = [
            "profiles/backend",
            "profiles/frontend",
            "profiles/api",
        ]

        profile_data = {
            "profiles/backend": {
                "name": "backend",
                "watched_patterns": ["*.py"],
                "ignore_patterns": ["*.pyc"],
                "metadata": {"description": "Backend profile"},
            },
            "profiles/frontend": {
                "name": "frontend",
                "watched_patterns": ["*.js", "*.tsx"],
                "ignore_patterns": ["node_modules"],
                "metadata": {"description": "Frontend profile"},
            },
            "profiles/api": {
                "name": "api",
                "watched_patterns": ["*.go"],
                "ignore_patterns": ["vendor"],
                "metadata": {"description": "API profile"},
            },
        }

        mock_storage.load.side_effect = lambda key: profile_data.get(key)  # type: ignore[no-any-return]

        profiles = profile_manager.list_profiles()

        assert len(profiles) == 3
        # Should be sorted by name
        assert profiles[0].name == "api"
        assert profiles[1].name == "backend"
        assert profiles[2].name == "frontend"

    def test_list_profiles_skip_invalid(
        self, profile_manager: ProfileManager, mock_storage: Mock
    ) -> None:
        """Test listing profiles skips invalid ones."""
        mock_storage.list_keys.return_value = [
            "profiles/valid",
            "profiles/invalid",
        ]

        def load_side_effect(key: str) -> Dict[str, Any] | None:
            if key == "profiles/valid":
                return {
                    "name": "valid",
                    "watched_patterns": ["*.py"],
                    "ignore_patterns": [],
                    "metadata": {},
                }
            else:
                # Missing required field
                return {"watched_patterns": ["*.py"]}

        mock_storage.load.side_effect = load_side_effect

        profiles = profile_manager.list_profiles()

        assert len(profiles) == 1
        assert profiles[0].name == "valid"

    def test_load_profile_exists(
        self, profile_manager: ProfileManager, mock_storage: Mock
    ) -> None:
        """Test loading an existing profile."""
        profile_data = {
            "name": "test",
            "watched_patterns": ["*.py"],
            "ignore_patterns": ["*.pyc"],
            "metadata": {"description": "Test profile"},
        }
        mock_storage.load.return_value = profile_data

        profile = profile_manager.load_profile("test")

        assert profile.name == "test"
        assert profile.watched_patterns == ["*.py"]
        assert profile.ignore_patterns == ["*.pyc"]
        assert profile.metadata["description"] == "Test profile"
        mock_storage.load.assert_called_once_with("profiles/test")

    def test_load_profile_not_found(
        self, profile_manager: ProfileManager, mock_storage: Mock
    ) -> None:
        """Test loading a non-existent profile raises ProfileNotFoundError."""
        mock_storage.load.return_value = None

        with pytest.raises(ProfileNotFoundError) as exc_info:
            profile_manager.load_profile("nonexistent")

        assert "Profile 'nonexistent' not found" in str(exc_info.value)
        assert "ctxr profile list" in str(exc_info.value)

    def test_load_profile_invalid_data(
        self, profile_manager: ProfileManager, mock_storage: Mock
    ) -> None:
        """Test loading profile with invalid data raises ProfileError."""
        # Missing required field
        mock_storage.load.return_value = {"watched_patterns": ["*.py"]}

        with pytest.raises(ProfileError) as exc_info:
            profile_manager.load_profile("invalid")

        assert "Error loading profile 'invalid'" in str(exc_info.value)

    def test_delete_profile_exists(
        self, profile_manager: ProfileManager, mock_storage: Mock
    ) -> None:
        """Test deleting an existing profile."""
        mock_storage.exists.return_value = True
        mock_storage.delete.return_value = True

        success = profile_manager.delete_profile("test")

        assert success is True
        mock_storage.exists.assert_called_once_with("profiles/test")
        mock_storage.delete.assert_called_once_with("profiles/test")

    def test_delete_profile_not_found(
        self, profile_manager: ProfileManager, mock_storage: Mock
    ) -> None:
        """Test deleting a non-existent profile raises ProfileNotFoundError."""
        mock_storage.exists.return_value = False

        with pytest.raises(ProfileNotFoundError) as exc_info:
            profile_manager.delete_profile("nonexistent")

        assert "Profile 'nonexistent' not found" in str(exc_info.value)
        assert "ctxr profile list" in str(exc_info.value)
        mock_storage.exists.assert_called_once_with("profiles/nonexistent")
        mock_storage.delete.assert_not_called()

    def test_delete_profile_storage_failure(
        self, profile_manager: ProfileManager, mock_storage: Mock
    ) -> None:
        """Test delete profile returns False on storage failure."""
        mock_storage.exists.return_value = True
        mock_storage.delete.return_value = False

        success = profile_manager.delete_profile("test")

        assert success is False
        mock_storage.exists.assert_called_once_with("profiles/test")
        mock_storage.delete.assert_called_once_with("profiles/test")

    def test_validate_profile_name(self, profile_manager: ProfileManager) -> None:
        """Test profile name validation."""
        # Valid names
        assert profile_manager._validate_profile_name("test") is True  # type: ignore[reportPrivateUsage]
        assert profile_manager._validate_profile_name("test-profile") is True  # type: ignore[reportPrivateUsage]
        assert profile_manager._validate_profile_name("test_profile") is True  # type: ignore[reportPrivateUsage]
        assert profile_manager._validate_profile_name("Test123") is True  # type: ignore[reportPrivateUsage]

        # Invalid names
        assert profile_manager._validate_profile_name("test profile") is False  # type: ignore[reportPrivateUsage]
        assert profile_manager._validate_profile_name("test!") is False  # type: ignore[reportPrivateUsage]
        assert profile_manager._validate_profile_name("test@profile") is False  # type: ignore[reportPrivateUsage]
        assert profile_manager._validate_profile_name("test.profile") is False  # type: ignore[reportPrivateUsage]
        assert profile_manager._validate_profile_name("") is False  # type: ignore[reportPrivateUsage]
        # Test length validation
        assert profile_manager._validate_profile_name("a" * 101) is False  # type: ignore[reportPrivateUsage]

    def test_format_profiles_table(self, profile_manager: ProfileManager) -> None:
        """Test formatting profiles as a table."""
        profiles = [
            Profile(
                name="backend",
                watched_patterns=["*.py", "*.md"],
                ignore_patterns=["*.pyc"],
                metadata={
                    "created_at": "2025-07-25T12:00:00Z",
                    "description": "Backend dev",
                },
            ),
            Profile(
                name="frontend",
                watched_patterns=["*.js"],
                ignore_patterns=[],
                metadata={"created_at": "invalid-date", "description": ""},
            ),
        ]

        table = profile_manager.format_profiles_table(profiles)

        # Basic checks - Rich Table doesn't expose much for testing
        assert table.title == "Saved Profiles"
        assert len(table.columns) == 5


@pytest.mark.parametrize(
    "name,expected",
    [
        ("simple", True),
        ("with-dash", True),
        ("with_underscore", True),
        ("AlphaNumerics123", True),
        ("with space", False),
        ("with!special", False),
        ("", False),
        (".", False),
        ("..", False),
        ("a" * 100, True),  # Exactly 100 chars is valid
        ("a" * 101, False),  # 101 chars is invalid
    ],
)
def test_profile_name_validation_parametrized(
    profile_manager: ProfileManager, name: str, expected: bool
) -> None:
    """Parametrized test for profile name validation."""
    assert profile_manager._validate_profile_name(name) == expected  # type: ignore[reportPrivateUsage]


def test_profile_metadata_timestamps() -> None:
    """Test that profile metadata timestamps are properly formatted."""
    profile = Profile(name="test", watched_patterns=[], ignore_patterns=[])

    # Check timestamp format
    created_at = profile.metadata["created_at"]
    updated_at = profile.metadata["updated_at"]

    # Should be able to parse as ISO format
    dt_created = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
    dt_updated = datetime.fromisoformat(updated_at.replace("Z", "+00:00"))

    # Should be timezone aware (UTC)
    assert dt_created.tzinfo is not None
    assert dt_updated.tzinfo is not None

    # Created and updated should be the same for new profile
    assert created_at == updated_at
