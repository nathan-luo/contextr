# contextr Product Requirements Document (PRD)

## Executive Summary

`contextr` is a CLI tool that bundles project files for sharing with Large Language Models (LLMs). This PRD defines the project's requirements, current state, and future roadmap.

## Current State (As of July 2025)

### Implemented Features
- **File Management**: Watch/ignore patterns for tracking files
- **Output Formatting**: XML-style output optimized for LLM consumption  
- **Clipboard Integration**: Direct copy to clipboard functionality
- **State Persistence**: JSON-based state management
- **Modern Development Tooling**: Ruff linting/formatting, Pyright type checking, pytest framework
- **Storage Abstraction**: Pluggable storage backend architecture

### Technology Stack
- **Language**: Python 3.12+
- **CLI Framework**: Typer with Rich for terminal UI
- **Build System**: Modern pyproject.toml with uv package manager
- **Code Quality**: Ruff (linting/formatting), Pyright (strict type checking)
- **Testing**: pytest with 40+ tests, ~42% coverage

## Goals and Vision

### Primary Goals
1. Evolve `contextr` from a simple file bundler into an intelligent context manager
2. Enable developers to define, save, and instantly load different "Context Profiles" 
3. Significantly improve workflow efficiency for developers using LLMs for multiple tasks
4. Maintain simplicity and ease of use while adding powerful features

### Success Metrics
- Context switch time reduced from minutes to seconds
- Zero data loss during profile operations
- 80%+ test coverage across codebase
- 100% type coverage with strict checking
- Sub-100ms profile operation performance

## Requirements

### Functional Requirements

#### Core Features (Implemented)
1. **FR-CORE-1**: Add file patterns to track using glob syntax
2. **FR-CORE-2**: Add ignore patterns using gitignore syntax  
3. **FR-CORE-3**: List all tracked files with current patterns
4. **FR-CORE-4**: Clear all patterns and reset context
5. **FR-CORE-5**: Sync (copy) formatted output to clipboard

#### Profile Management (To Be Implemented - Epic 2)
1. **FR-PROF-1**: Save current context as a named profile
2. **FR-PROF-2**: Load a named profile to replace current context
3. **FR-PROF-3**: List all saved profiles with metadata
4. **FR-PROF-4**: Delete a specified profile with confirmation
5. **FR-PROF-5**: Profile operations must be idempotent

### Non-Functional Requirements

#### Performance
1. **NFR-PERF-1**: Profile operations complete in <100ms
2. **NFR-PERF-2**: File discovery scales to 10k+ files
3. **NFR-PERF-3**: Minimal memory footprint for large contexts

#### Quality
1. **NFR-QUAL-1**: 80%+ test coverage
2. **NFR-QUAL-2**: 100% type coverage with strict checking
3. **NFR-QUAL-3**: Zero linting errors or warnings
4. **NFR-QUAL-4**: All code follows project style guidelines

#### Compatibility
1. **NFR-COMP-1**: Cross-platform support (Linux, macOS, Windows)
2. **NFR-COMP-2**: No breaking changes to existing CLI interface
3. **NFR-COMP-3**: Backward compatible state file format
4. **NFR-COMP-4**: Python 3.12+ requirement

#### Architecture
1. **NFR-ARCH-1**: Pluggable storage backend system
2. **NFR-ARCH-2**: Clear separation of concerns
3. **NFR-ARCH-3**: Extensible for future enhancements
4. **NFR-ARCH-4**: No external database dependencies

## Technical Architecture

### Current Implementation

```
src/contextr/
├── cli.py                 # CLI commands (Typer-based)
├── manager.py             # Core ContextManager with storage abstraction
├── formatters.py          # Output formatting (XML for LLMs)
├── storage/               # Storage abstraction layer
│   ├── base.py           # StorageBackend ABC
│   └── json_storage.py   # JSON file implementation
└── utils/                # Utilities
    ├── ignore_utils.py   # Gitignore pattern matching
    └── path_utils.py     # Path manipulation
```

### Storage Design

- **Abstraction**: `StorageBackend` ABC for extensibility
- **Implementation**: `JsonStorage` with atomic file operations
- **State Location**: `.contextr/state.json`
- **Profile Location**: `.contextr/profiles/` (future)

### Key Design Decisions

1. **Storage Abstraction**: Enables future backends (SQLite, cloud, etc.)
2. **Dependency Injection**: ContextManager accepts storage backend
3. **Atomic Operations**: Prevents data corruption
4. **Type Safety**: Full type annotations with strict checking

## Epic Roadmap

### Epic 1: Project Modernization & Foundation ✅ COMPLETED

**Status**: All 4 stories completed and deployed

1. **Story 1.1**: Integrate Ruff ✅
2. **Story 1.2**: Configure Pyright ✅  
3. **Story 1.3**: Set Up Pytest ✅
4. **Story 1.4**: Refactor ContextManager ✅

**Outcomes**:
- Modern development tooling fully integrated
- Comprehensive type annotations added
- Test infrastructure established (40+ tests)
- Storage abstraction implemented

### Epic 2: Context Profile Management 🚧 READY TO START

**Goal**: Implement full profile lifecycle management

#### Story 2.1: Save and List Context Profiles
- Command: `ctxr profile save <name>`
- Command: `ctxr profile list`
- Overwrite protection with confirmation
- Profile metadata (created/updated timestamps)

#### Story 2.2: Load a Context Profile  
- Command: `ctxr profile load <name>`
- Clear current context before loading
- Automatic file list refresh
- Error handling for missing profiles

#### Story 2.3: Delete a Context Profile
- Command: `ctxr profile delete <name>`
- Confirmation prompt required
- Filesystem cleanup
- Clear error messages

### Future Epics (Backlog)

#### Epic 3: Enhanced User Experience
- Profile templates for common project types
- Auto-detection of project type
- Interactive profile creation wizard
- Profile composition/inheritance

#### Epic 4: Team Collaboration
- Profile sharing/export functionality
- Cloud sync for profiles
- Team profile repository
- Version control integration

#### Epic 5: Advanced Features
- Multiple output formats (JSON, Markdown)
- Incremental context updates
- Context diffing between profiles
- Plugin system for extensions

## Implementation Guidelines

### Development Process
1. All code must pass: `uv run ruff format .` and `uv run ruff check .`
2. Type checking required: `uv run pyright` with zero errors
3. Tests required for new features: `uv run pytest`
4. Update documentation for all changes

### Code Style
- Line length: 88 characters (Black standard)
- Imports: Sorted with Ruff (I rules)
- Docstrings: Google style with Args/Returns
- Type hints: Required for all public APIs

### Testing Strategy
- Unit tests for all new functions
- Integration tests for CLI commands
- Mock external dependencies
- Minimum 80% coverage target

## Risk Assessment

### Technical Risks
1. **Profile Corruption**: Mitigated by atomic writes
2. **Performance Degradation**: Monitor with large contexts
3. **Storage Compatibility**: Maintain format versioning

### User Experience Risks
1. **Confusion with Multiple Profiles**: Clear status indicators
2. **Accidental Data Loss**: Confirmation prompts
3. **Complex Commands**: Intuitive CLI design

## Change Log

| Date       | Version | Description                           | Author      |
|------------|---------|---------------------------------------|-------------|
| 2025-07-23 | 1.0     | Initial PRD                          | John (PM)   |
| 2025-07-23 | 1.1     | Epic 1 completed                     | Dev Team    |
| 2025-07-25 | 2.0     | Updated with current state           | Bob (SM)    |

## Appendices

### A. Profile Schema (Proposed)
```json
{
  "name": "frontend",
  "watched_patterns": ["src/**/*.tsx", "src/**/*.css"],
  "ignore_patterns": ["**/*.test.tsx", "build/**"],
  "metadata": {
    "created_at": "2025-07-25T12:00:00Z",
    "updated_at": "2025-07-25T12:00:00Z",
    "description": "Frontend development context"
  }
}
```

### B. CLI Command Reference

#### Current Commands
- `ctxr watch <pattern>` - Add watch pattern
- `ctxr ignore <pattern>` - Add ignore pattern  
- `ctxr list` - Show tracked files
- `ctxr clear` - Clear all patterns
- `ctxr sync` - Copy to clipboard

#### Planned Profile Commands (Epic 2)
- `ctxr profile save <name>` - Save current as profile
- `ctxr profile load <name>` - Load profile
- `ctxr profile list` - List all profiles
- `ctxr profile delete <name>` - Delete profile

### C. Success Criteria Checklist

#### Epic 1 ✅
- [x] Ruff integrated and configured
- [x] Pyright in strict mode with 100% coverage
- [x] Pytest framework with 40+ tests
- [x] Storage abstraction implemented
- [x] All existing functionality maintained

#### Epic 2 (Pending)
- [ ] Profile save functionality
- [ ] Profile load with context switching
- [ ] Profile listing with metadata
- [ ] Profile deletion with safety
- [ ] Integration tests for all workflows
- [ ] User documentation updated

## Conclusion

This PRD serves as the single source of truth for the `contextr` project. Epic 1 has successfully modernized the codebase with professional development tooling and a solid architectural foundation. The project is now ready to proceed with Epic 2, implementing the Context Profile Management feature that will transform `contextr` from a simple file bundler into an intelligent context manager for developers working with LLMs.