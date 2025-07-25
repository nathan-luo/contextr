"""Profile management for saving and loading context configurations."""

import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, TypeAlias

from rich.console import Console
from rich.table import Table

from .storage import StorageBackend

# Type aliases for clarity
ProfileName: TypeAlias = str
Pattern: TypeAlias = str
FilePath: TypeAlias = str

# Compiled regex for profile name validation
PROFILE_NAME_PATTERN = re.compile(r"^[a-zA-Z0-9_-]+$")

console = Console()


class ProfileError(Exception):
    """Base exception for profile-related errors."""

    pass


class ProfileNotFoundError(ProfileError):
    """Exception raised when a profile is not found."""

    pass


class Profile:
    """Represents a saved context profile."""

    def __init__(
        self,
        name: str,
        watched_patterns: List[Pattern],
        ignore_patterns: List[Pattern],
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Initialize a Profile.

        Args:
            name: Name of the profile
            watched_patterns: List of patterns being watched
            ignore_patterns: List of ignore patterns
            metadata: Optional metadata dictionary
        """
        self.name = name
        self.watched_patterns = watched_patterns
        self.ignore_patterns = ignore_patterns
        self.metadata = metadata or self._create_metadata()

    def _create_metadata(self) -> Dict[str, Any]:
        """Create default metadata for new profile."""
        now = datetime.now(timezone.utc).isoformat()
        return {
            "created_at": now,
            "updated_at": now,
            "description": "",
        }

    def to_dict(self) -> Dict[str, Any]:
        """Convert profile to dictionary for storage."""
        return {
            "name": self.name,
            "watched_patterns": self.watched_patterns,
            "ignore_patterns": self.ignore_patterns,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Profile":
        """Create Profile from dictionary."""
        return cls(
            name=data["name"],
            watched_patterns=data.get("watched_patterns", []),
            ignore_patterns=data.get("ignore_patterns", []),
            metadata=data.get("metadata"),
        )


class ProfileManager:
    """Manages saving and loading context profiles."""

    def __init__(self, storage: StorageBackend, base_dir: Path) -> None:
        """Initialize ProfileManager.

        Args:
            storage: Storage backend for persisting profiles
            base_dir: Base directory for relative path calculations
        """
        self.storage = storage
        self.base_dir = base_dir

    def save_profile(
        self,
        name: ProfileName,
        watched_patterns: List[Pattern],
        ignore_patterns: List[Pattern],
        description: str = "",
        force: bool = False,
    ) -> bool:
        """Save current context as a named profile.

        Args:
            name: Name for the profile
            watched_patterns: List of watched patterns
            ignore_patterns: List of ignore patterns
            description: Optional description for the profile
            force: Whether to overwrite existing profile without confirmation

        Returns:
            bool: True if save was successful

        Raises:
            ValueError: If profile name is invalid
        """
        # Validate profile name
        if not self._validate_profile_name(name):
            raise ValueError(
                f"Invalid profile name: '{name}'. "
                "Use alphanumeric, dash, or underscore."
            )

        key = f"profiles/{name}"

        # Check if profile exists
        if self.storage.exists(key) and not force:
            return False  # Caller should handle confirmation

        # Create profile
        profile = Profile(
            name=name,
            watched_patterns=watched_patterns,
            ignore_patterns=ignore_patterns,
        )

        # Update description if provided
        if description:
            profile.metadata["description"] = description

        # Update timestamp for existing profiles
        if self.storage.exists(key):
            existing_data = self.storage.load(key)
            if existing_data and "metadata" in existing_data:
                profile.metadata["created_at"] = existing_data["metadata"].get(
                    "created_at", profile.metadata["created_at"]
                )
                profile.metadata["updated_at"] = datetime.now(timezone.utc).isoformat()

        # Save profile
        try:
            self.storage.save(key, profile.to_dict())
            return True
        except IOError as e:
            console.print(f"[red]Error saving profile '{name}': {e}[/red]")
            return False

    def list_profiles(self) -> List[Profile]:
        """List all saved profiles.

        Returns:
            List[Profile]: List of saved profiles sorted by name
        """
        profile_keys = self.storage.list_keys("profiles/")
        profiles: List[Profile] = []

        for key in profile_keys:
            profile_name = key.replace("profiles/", "")
            data = self.storage.load(key)
            if data:
                try:
                    profile = Profile.from_dict(data)
                    profiles.append(profile)
                except (KeyError, TypeError) as e:
                    console.print(
                        f"[yellow]Warning: Skipping invalid profile "
                        f"'{profile_name}': {e}[/yellow]"
                    )

        return sorted(profiles, key=lambda p: p.name)

    def load_profile(self, name: ProfileName) -> Profile:
        """Load a specific profile by name.

        Args:
            name: Name of the profile to load

        Returns:
            Profile: The loaded profile

        Raises:
            ProfileNotFoundError: If profile doesn't exist
        """
        key = f"profiles/{name}"
        data = self.storage.load(key)

        if not data:
            raise ProfileNotFoundError(
                f"Profile '{name}' not found. "
                "Use 'ctxr profile list' to see available profiles."
            )

        try:
            return Profile.from_dict(data)
        except (KeyError, TypeError) as e:
            raise ProfileError(f"Error loading profile '{name}': {e}") from e

    def delete_profile(self, name: ProfileName) -> bool:
        """Delete a profile by name.

        Args:
            name: Name of the profile to delete

        Returns:
            bool: True if deletion was successful

        Raises:
            ProfileNotFoundError: If profile doesn't exist
        """
        key = f"profiles/{name}"
        if not self.storage.exists(key):
            raise ProfileNotFoundError(
                f"Profile '{name}' not found. "
                "Use 'ctxr profile list' to see available profiles."
            )
        return self.storage.delete(key)

    def _validate_profile_name(self, name: str) -> bool:
        """Validate profile name.

        Args:
            name: Profile name to validate

        Returns:
            bool: True if name is valid
        """
        # Allow alphanumeric, dash, underscore
        # Add length validation to prevent excessively long profile names
        if not name or len(name) > 100:
            return False

        return bool(PROFILE_NAME_PATTERN.match(name))

    def format_profiles_table(self, profiles: List[Profile]) -> Table:
        """Format profiles as a Rich table.

        Args:
            profiles: List of profiles to format

        Returns:
            Table: Formatted table for display
        """
        table = Table(title="Saved Profiles", show_lines=True)
        table.add_column("Name", style="cyan", no_wrap=True)
        table.add_column("Description", style="white")
        table.add_column("Patterns", style="green")
        table.add_column("Ignored", style="red")
        table.add_column("Created", style="blue")

        for profile in profiles:
            description = profile.metadata.get("description", "")
            patterns_count = len(profile.watched_patterns)
            ignored_count = len(profile.ignore_patterns)

            # Format creation date
            created_at = profile.metadata.get("created_at", "")
            if created_at:
                try:
                    dt = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
                    created_str = dt.strftime("%Y-%m-%d %H:%M")
                except ValueError:
                    created_str = "Unknown"
            else:
                created_str = "Unknown"

            table.add_row(
                profile.name,
                description or "[dim]No description[/dim]",
                str(patterns_count),
                str(ignored_count),
                created_str,
            )

        return table
