# Epic 2: Context Profile Management - Implementation Guide

## Status: ✅ COMPLETED

## Overview

This guide documents the implementation of Epic 2, which built on the modernized foundation established in Epic 1. The epic delivered the Context Profiles feature, allowing users to save, load, list, and delete named context configurations.

**Implementation Summary:**
- All 3 stories completed successfully
- ProfileManager class implemented with full CRUD operations
- CLI commands integrated into the main application
- 99% test coverage for profile code (106 statements, 1 missed)
- Rich table formatting for profile listing
- Comprehensive error handling and user feedback

## Pre-Implementation Checklist

### ✅ Prerequisites from Epic 1
- [x] Storage abstraction layer implemented
- [x] Ruff linting/formatting configured
- [x] Pyright type checking in strict mode
- [x] pytest framework with test structure
- [x] ContextManager refactored for extensibility

### 🔧 Technical Readiness
- Storage backend supports hierarchical keys
- Atomic file operations prevent corruption
- Test infrastructure ready for new features
- Type annotations throughout codebase

## Story Implementation Details

### Story 2.1: Save and List Context Profiles

#### Technical Design
```python
# New ProfileManager class
class ProfileManager:
    def __init__(self, storage: StorageBackend):
        self.storage = storage
        self.profile_prefix = "profiles"
    
    def save_profile(
        self, 
        name: str, 
        context: ContextManager,
        description: Optional[str] = None
    ) -> Profile:
        """Save current context as a named profile"""
        
    def list_profiles(self) -> List[ProfileSummary]:
        """List all saved profiles with metadata"""
```

#### CLI Commands
```python
# In cli.py - new profile command group
@app.callback()
def profile():
    """Manage context profiles"""
    pass

@profile.command("save")
def save_profile(
    name: str = typer.Argument(..., help="Profile name"),
    description: Optional[str] = typer.Option(None, "--description", "-d"),
    force: bool = typer.Option(False, "--force", "-f", help="Overwrite existing")
):
    """Save current context as a profile"""
    
@profile.command("list")
def list_profiles():
    """List all saved profiles"""
```

#### Implementation Steps
1. Create `src/contextr/profile.py` with ProfileManager class
2. Add profile commands to `cli.py`
3. Implement profile storage format with metadata
4. Add overwrite protection with confirmation
5. Create table formatter for profile list display
6. Write comprehensive unit tests

#### Test Cases
- Save new profile successfully
- Prevent overwrite without --force
- List profiles with correct metadata
- Handle empty profile list
- Validate profile names

### Story 2.2: Load a Context Profile

#### Technical Design
```python
class ProfileManager:
    def load_profile(self, name: str) -> Profile:
        """Load a profile by name"""
        key = f"{self.profile_prefix}/{name}"
        data = self.storage.load(key)
        if not data:
            raise ProfileNotFoundError(f"Profile '{name}' not found")
        return Profile.from_dict(data)

class ContextManager:
    def apply_profile(self, profile: Profile) -> None:
        """Replace current context with profile data"""
        self.clear()
        self.watched_patterns = set(profile.watched_patterns)
        self.ignore_patterns = set(profile.ignore_patterns)
        self.refresh_files()
```

#### CLI Command
```python
@profile.command("load")
def load_profile(
    name: str = typer.Argument(..., help="Profile name to load")
):
    """Load and activate a saved profile"""
    try:
        profile = profile_manager.load_profile(name)
        context_manager.apply_profile(profile)
        console.print(f"[green]✓[/green] Loaded profile '{name}'")
        # Show loaded patterns
    except ProfileNotFoundError as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)
```

#### Implementation Steps
1. Add load_profile method to ProfileManager
2. Add apply_profile method to ContextManager
3. Implement profile validation on load
4. Add automatic file refresh after load
5. Create informative success/error messages
6. Write integration tests for full workflow

#### Test Cases
- Load existing profile successfully
- Error on non-existent profile
- Verify context cleared before load
- Confirm files refreshed after load
- Test idempotent loading

### Story 2.3: Delete a Context Profile

#### Technical Design
```python
class ProfileManager:
    def delete_profile(self, name: str) -> bool:
        """Delete a profile by name"""
        key = f"{self.profile_prefix}/{name}"
        if not self.storage.exists(key):
            raise ProfileNotFoundError(f"Profile '{name}' not found")
        return self.storage.delete(key)
```

#### CLI Command
```python
@profile.command("delete")
def delete_profile(
    name: str = typer.Argument(..., help="Profile name to delete"),
    force: bool = typer.Option(False, "--force", "-f", help="Skip confirmation")
):
    """Delete a saved profile"""
    if not force:
        confirm = typer.confirm(f"Delete profile '{name}'?")
        if not confirm:
            raise typer.Abort()
    
    try:
        profile_manager.delete_profile(name)
        console.print(f"[green]✓[/green] Deleted profile '{name}'")
    except ProfileNotFoundError as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)
```

#### Implementation Steps
1. Add delete_profile method to ProfileManager
2. Implement confirmation prompt
3. Add --force flag to skip confirmation
4. Handle missing profile gracefully
5. Clean up profile file from filesystem
6. Write tests for deletion scenarios

#### Test Cases
- Delete existing profile with confirmation
- Delete with --force flag
- Abort deletion on "no" confirmation
- Error on non-existent profile
- Verify filesystem cleanup

## Data Models

### Profile Model
```python
from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional

@dataclass
class Profile:
    name: str
    watched_patterns: List[str]
    ignore_patterns: List[str]
    created_at: datetime
    updated_at: datetime
    description: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary for storage"""
        
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Profile":
        """Deserialize from storage dictionary"""

@dataclass
class ProfileSummary:
    name: str
    description: Optional[str]
    pattern_count: int
    created_at: datetime
    updated_at: datetime
```

## Error Handling

### Custom Exceptions
```python
class ProfileError(Exception):
    """Base exception for profile operations"""

class ProfileNotFoundError(ProfileError):
    """Profile does not exist"""

class ProfileExistsError(ProfileError):
    """Profile already exists"""

class InvalidProfileNameError(ProfileError):
    """Invalid profile name"""
```

### Error Messages
- Profile not found: "Profile '{name}' not found. Use 'ctxr profile list' to see available profiles."
- Profile exists: "Profile '{name}' already exists. Use --force to overwrite."
- Invalid name: "Profile name can only contain letters, numbers, hyphens, and underscores."

## Testing Strategy

### Unit Tests Structure
```
tests/unit/
├── test_profile.py          # ProfileManager tests
│   ├── test_save_profile
│   ├── test_load_profile
│   ├── test_list_profiles
│   └── test_delete_profile
└── test_cli_profile.py      # Profile CLI command tests
```

### Integration Tests
```python
# tests/integration/test_profile_workflow.py
def test_full_profile_lifecycle(temp_context):
    """Test complete profile workflow"""
    # 1. Add patterns to context
    # 2. Save as profile
    # 3. Clear context
    # 4. Load profile
    # 5. Verify patterns restored
    # 6. Delete profile
```

### Test Fixtures
```python
@pytest.fixture
def sample_profile():
    return Profile(
        name="test-profile",
        watched_patterns=["src/**/*.py"],
        ignore_patterns=["**/__pycache__/**"],
        created_at=datetime.now(),
        updated_at=datetime.now()
    )

@pytest.fixture
def profile_manager(tmp_path):
    storage = JsonStorage(tmp_path / ".contextr")
    return ProfileManager(storage)
```

## Implementation Timeline

### Week 1: Core Functionality
- **Day 1-2**: ProfileManager implementation with save/list
- **Day 3-4**: Load functionality and ContextManager integration  
- **Day 5**: Delete functionality and error handling

### Week 2: Polish & Testing
- **Day 1-2**: Comprehensive test suite
- **Day 3**: CLI polish and user experience
- **Day 4**: Documentation updates
- **Day 5**: Final testing and review

## Quality Checklist

### Before Starting Each Story
- [ ] Review acceptance criteria
- [ ] Check dependencies are ready
- [ ] Set up test structure

### During Implementation
- [ ] Write tests first (TDD)
- [ ] Add type annotations
- [ ] Handle edge cases
- [ ] Add helpful error messages

### Before Completing Each Story
- [ ] All tests passing
- [ ] Type checking passes (`uv run pyright`)
- [ ] Linting passes (`uv run ruff check .`)
- [ ] Documentation updated
- [ ] Code review completed

## Migration Considerations

### Backward Compatibility
- Existing state.json remains untouched
- Profile commands are additive only
- No changes to existing commands
- Users opt-in to profiles

### Future Extensibility
- Profile schema versioning for updates
- Export/import functionality preparation
- Team sharing considerations
- Cloud sync preparation

## User Documentation Template

### README.md Addition
```markdown
## Context Profiles

Save and switch between different context configurations:

### Save current context as a profile
ctxr profile save backend --description "Backend development files"

### List available profiles  
ctxr profile list

### Load a profile
ctxr profile load backend

### Delete a profile
ctxr profile delete backend
```

## Success Metrics

### Technical Metrics
- All profile operations < 100ms ✅
- 99% test coverage for profile code ✅ (exceeded 90% target)
- Zero type/lint errors ✅
- Atomic operations verified ✅

### User Experience Metrics  
- Clear, helpful error messages
- Intuitive command structure
- Fast context switching
- No data loss scenarios

## Risk Mitigation

### Technical Risks
1. **Data Corruption**: Use atomic writes, add recovery mode
2. **Performance**: Benchmark with many profiles, add caching if needed
3. **Compatibility**: Extensive testing on all platforms

### User Risks
1. **Confusion**: Clear docs, helpful command output
2. **Data Loss**: Confirmation prompts, backup option
3. **Complexity**: Keep commands simple and intuitive

## Final Notes

This implementation guide provides a comprehensive roadmap for Epic 2. The modular design and thorough testing approach ensure a robust implementation that enhances user productivity while maintaining the simplicity that makes contextr valuable.

Remember: The goal is to make context switching effortless for developers working with LLMs across multiple tasks.