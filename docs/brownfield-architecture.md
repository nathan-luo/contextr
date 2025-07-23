# contextr Brownfield Architecture Document

## Table of Contents
1. [Current Architecture Overview](#current-architecture-overview)
2. [Component Analysis](#component-analysis)
3. [Data Flow & State Management](#data-flow--state-management)
4. [Proposed Architecture Changes](#proposed-architecture-changes)
5. [Migration Strategy](#migration-strategy)
6. [Technical Decisions](#technical-decisions)

## Current Architecture Overview

### System Context
```
┌─────────────────┐     ┌──────────────┐     ┌─────────────┐
│   Developer     │────▶│   contextr   │────▶│  Clipboard  │
│   (CLI User)    │     │     CLI      │     │   (LLM)     │
└─────────────────┘     └──────────────┘     └─────────────┘
         │                      │
         │                      ▼
         │              ┌──────────────┐
         └─────────────▶│  File System │
                        │  (.contextr) │
                        └──────────────┘
```

### Component Architecture
```
src/contextr/
├── cli.py                 # User Interface Layer
│   ├── app: Typer        # CLI application instance
│   ├── watch()           # Add file patterns
│   ├── ignore()          # Add ignore patterns
│   ├── list()            # Display tracked files
│   ├── clear()           # Clear patterns
│   └── sync()            # Copy to clipboard
│
├── manager.py             # Business Logic Layer
│   └── ContextManager
│       ├── __init__()    # Load state
│       ├── add_files()   # Add patterns
│       ├── remove_files()# Remove patterns
│       ├── get_files()   # List files
│       ├── save_state()  # Persist state
│       └── _load_state() # Load state
│
├── formatters.py          # Presentation Layer
│   └── format_files_as_xml()
│
└── utils/                 # Utility Layer
    ├── ignore_utils.py
    │   └── should_ignore()
    └── path_utils.py
        ├── find_git_root()
        └── get_relative_path()
```

## Component Analysis

### CLI Layer (`cli.py`)
- **Responsibility**: User interface and command handling
- **Dependencies**: Typer, Rich (console output)
- **Current Issues**: 
  - Tightly coupled to ContextManager
  - No command validation
  - Limited error handling

### Business Logic Layer (`manager.py`)
- **Responsibility**: Core context management
- **Key Class**: `ContextManager`
- **Current Issues**:
  - Mixes state persistence with business logic
  - No abstraction for storage backend
  - Single context limitation
  - No transaction support

### Presentation Layer (`formatters.py`)
- **Responsibility**: Output formatting
- **Current Issues**:
  - Single format support (XML)
  - No extensibility mechanism
  - Hardcoded formatting rules

### Utility Layer (`utils/`)
- **Responsibility**: Cross-cutting concerns
- **Current Issues**:
  - Missing type annotations
  - No comprehensive path validation
  - Limited test coverage

## Data Flow & State Management

### Current State Model
```json
{
  "watched_patterns": ["src/**/*.py", "tests/**/*.py"],
  "ignore_patterns": ["**/__pycache__/**", "*.pyc"]
}
```

### File Discovery Flow
```
1. User adds pattern via CLI
2. ContextManager updates in-memory state
3. State persisted to .contextr/state.json
4. On sync, patterns resolved to actual files
5. Files filtered through ignore patterns
6. Formatted output copied to clipboard
```

### State Persistence
- **Location**: `.contextr/state.json`
- **Format**: JSON
- **Issues**: 
  - No versioning
  - No validation
  - No atomic writes
  - No backup mechanism

## Proposed Architecture Changes

### Enhanced Component Architecture
```
src/contextr/
├── cli/
│   ├── __init__.py
│   ├── app.py            # Main CLI app
│   ├── commands/         # Command modules
│   │   ├── __init__.py
│   │   ├── basic.py      # Existing commands
│   │   └── profile.py    # New profile commands
│   └── validators.py     # Input validation
│
├── core/
│   ├── __init__.py
│   ├── manager.py        # Refactored ContextManager
│   ├── profile.py        # ProfileManager
│   └── models.py         # Data models
│
├── storage/
│   ├── __init__.py
│   ├── base.py           # Storage interface
│   ├── json_storage.py   # JSON implementation
│   └── migrations.py     # Schema migrations
│
├── formatters/
│   ├── __init__.py
│   ├── base.py           # Formatter interface
│   ├── xml.py            # XML formatter
│   └── json.py           # JSON formatter
│
└── utils/
    ├── __init__.py
    ├── ignore.py         # Enhanced ignore utils
    ├── paths.py          # Enhanced path utils
    └── validators.py     # Common validators
```

### New Profile Architecture
```
┌─────────────────┐
│  ProfileManager │
├─────────────────┤
│ + create()      │
│ + load()        │
│ + list()        │
│ + delete()      │
│ + get_active()  │
└────────┬────────┘
         │
         ▼
┌─────────────────┐     ┌─────────────────┐
│ ProfileStorage  │────▶│  ContextManager │
├─────────────────┤     ├─────────────────┤
│ + save()        │     │ + add_files()   │
│ + load()        │     │ + remove_files()│
│ + list()        │     │ + get_files()   │
│ + delete()      │     │ + clear()       │
└─────────────────┘     └─────────────────┘
```

### Storage Abstraction
```python
from abc import ABC, abstractmethod
from typing import Dict, List, Optional

class StorageBackend(ABC):
    @abstractmethod
    def save(self, key: str, data: Dict) -> None:
        """Save data with given key"""
        
    @abstractmethod
    def load(self, key: str) -> Optional[Dict]:
        """Load data by key"""
        
    @abstractmethod
    def delete(self, key: str) -> bool:
        """Delete data by key"""
        
    @abstractmethod
    def list_keys(self) -> List[str]:
        """List all available keys"""
```

## Migration Strategy

### Phase 1: Foundation (Week 1)
1. **Add Development Tools**
   - Configure Ruff with comprehensive rules
   - Set up Pyright in strict mode
   - Create pytest infrastructure
   - Add pre-commit hooks

2. **Type Safety**
   - Add type annotations to all modules
   - Fix type errors identified by Pyright
   - Create type stubs for external deps

### Phase 2: Refactoring (Week 2)
1. **Storage Abstraction**
   - Create storage interface
   - Implement JSON storage backend
   - Migrate ContextManager to use storage
   - Add transaction support

2. **Module Reorganization**
   - Create new package structure
   - Move components to appropriate modules
   - Update import statements
   - Maintain backward compatibility

### Phase 3: Profile Implementation (Weeks 3-4)
1. **Profile Management**
   - Implement ProfileManager
   - Create profile storage
   - Add profile commands
   - Implement profile switching

2. **Enhanced Features**
   - Multi-format support
   - Profile templates
   - Import/export functionality
   - Profile metadata

### Phase 4: Testing & Documentation (Week 5)
1. **Comprehensive Testing**
   - Unit tests (>80% coverage)
   - Integration tests
   - Performance tests
   - User acceptance tests

2. **Documentation**
   - Update README
   - Create user guide
   - API documentation
   - Migration guide

## Technical Decisions

### Design Patterns
1. **Strategy Pattern**: For formatters and storage backends
2. **Factory Pattern**: For creating storage instances
3. **Command Pattern**: For CLI command structure
4. **Repository Pattern**: For profile storage

### Technology Choices
1. **Pydantic**: For data validation and models
2. **Click**: Consider migration from Typer for better testability
3. **Pathlib**: Exclusive use for path operations
4. **JSON Schema**: For profile validation

### Performance Considerations
1. **Lazy Loading**: Load profiles on demand
2. **Caching**: Cache file discovery results
3. **Async I/O**: For file operations (future)
4. **Incremental Updates**: Only scan changed directories

### Security Considerations
1. **Path Traversal**: Validate all file paths
2. **JSON Injection**: Validate profile data
3. **File Permissions**: Check before operations
4. **Sensitive Data**: Never store in profiles

## API Design

### ProfileManager API
```python
class ProfileManager:
    def create_profile(self, name: str, description: str = "") -> Profile:
        """Create a new profile from current context"""
        
    def load_profile(self, name: str) -> None:
        """Load and activate a profile"""
        
    def list_profiles(self) -> List[ProfileSummary]:
        """List all available profiles"""
        
    def delete_profile(self, name: str) -> bool:
        """Delete a profile"""
        
    def export_profile(self, name: str, format: str = "json") -> str:
        """Export profile to string"""
        
    def import_profile(self, data: str, format: str = "json") -> Profile:
        """Import profile from string"""
```

### Enhanced ContextManager API
```python
class ContextManager:
    def __init__(self, storage: StorageBackend):
        """Initialize with storage backend"""
        
    def switch_profile(self, profile: Profile) -> None:
        """Switch to a different profile"""
        
    def get_current_profile(self) -> Optional[str]:
        """Get name of current profile"""
        
    def validate_patterns(self, patterns: List[str]) -> List[str]:
        """Validate file patterns"""
        
    def refresh_cache(self) -> None:
        """Refresh file discovery cache"""
```

## Error Handling Strategy

### Error Hierarchy
```python
class ContextrError(Exception):
    """Base exception for contextr"""

class ProfileError(ContextrError):
    """Profile-related errors"""

class StorageError(ContextrError):
    """Storage-related errors"""

class ValidationError(ContextrError):
    """Validation errors"""
```

### Error Handling Patterns
1. **User Input**: Validate early, fail fast
2. **File Operations**: Graceful degradation
3. **Profile Operations**: Atomic with rollback
4. **Network Operations**: Timeout and retry

## Testing Strategy

### Unit Tests
- Test each component in isolation
- Mock external dependencies
- Focus on edge cases
- Achieve >80% coverage

### Integration Tests
- Test complete workflows
- Use temporary directories
- Test error scenarios
- Verify state persistence

### Performance Tests
- Large file tree handling
- Pattern matching efficiency
- Profile switching speed
- Memory usage monitoring

## Deployment & Release

### Version Strategy
- Semantic versioning (MAJOR.MINOR.PATCH)
- Backward compatibility for 1.x releases
- Deprecation warnings for removed features
- Clear migration guides

### Release Process
1. Feature freeze
2. Testing phase
3. Documentation update
4. Release candidate
5. User testing
6. Final release
7. Post-release monitoring

## Monitoring & Metrics

### Usage Metrics (Optional)
- Command usage frequency
- Profile count distribution
- Performance metrics
- Error rates

### Quality Metrics
- Code coverage
- Type coverage
- Linting score
- Documentation coverage

## Future Considerations

### Potential Features
1. **Cloud Sync**: Sync profiles across machines
2. **Team Profiles**: Shared profile repository
3. **Auto-discovery**: Detect project type
4. **IDE Integration**: VSCode/PyCharm plugins
5. **Web UI**: Browser-based management

### Scalability Plans
1. **Async Operations**: For large codebases
2. **Distributed Storage**: For team features
3. **Plugin System**: For extensibility
4. **API Server**: For remote access

## Conclusion

This architecture document provides a comprehensive view of the current `contextr` system and a detailed plan for evolving it to support profile management. The phased approach ensures maintainability while delivering new capabilities to users.