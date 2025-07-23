# contextr Brownfield Product Requirements Document

## Executive Summary

This brownfield PRD documents the current state of the `contextr` project and outlines the requirements for evolving it from a simple file bundler into an intelligent context manager with profile support.

## Current State Analysis

### Existing Functionality
- **File Watching**: Add/remove file patterns to track
- **Ignore Patterns**: Support for gitignore-style exclusions
- **Output Formatting**: XML-style tags for LLM consumption
- **Clipboard Integration**: Direct copy to clipboard functionality
- **State Persistence**: Saves watched/ignored patterns in `.contextr/state.json`
- **CLI Interface**: Typer-based commands (watch, ignore, list, clear, sync)

### Technology Stack
- **Language**: Python 3.12+
- **CLI Framework**: Typer
- **Dependencies**: prompt-toolkit, pyperclip, rich
- **Build System**: Modern pyproject.toml with uv package manager
- **Code Style**: PEP 8 with ~80-90 char lines, Google-style docstrings

### Architecture Overview
- **Entry Points**: `contextr` and `ctxr` CLI commands
- **Core Components**:
  - `cli.py`: Command definitions and user interface
  - `manager.py`: Core context management logic
  - `formatters.py`: Output formatting for different targets
  - `utils/`: Helper modules for paths and ignore patterns

### Identified Gaps
1. **No Testing Framework**: No pytest setup or test files
2. **Limited Linting**: Only Black/isort configured, no Ruff or Pyright
3. **Version Mismatch**: pyproject.toml (1.0.0) vs __init__.py (0.1.1)
4. **Single Context Limitation**: No support for multiple named contexts
5. **Manual Context Switching**: Requires manual reconfiguration for task changes

## Migration Requirements

### Phase 1: Foundation Modernization

#### Code Quality Tools
- **Ruff Integration**: Add linting and formatting with comprehensive ruleset
- **Pyright Setup**: Enable strict type checking across codebase
- **Type Annotations**: Add missing type hints to all functions/methods

#### Testing Infrastructure
- **Pytest Framework**: Set up test directory and configuration
- **Unit Tests**: Cover core functionality (ContextManager, utils)
- **Integration Tests**: Test CLI commands and file operations
- **Coverage Goals**: Minimum 80% code coverage

#### Refactoring Needs
- **ContextManager Decoupling**: Separate state persistence from in-memory management
- **Profile Support Preparation**: Create extensible architecture for multiple contexts
- **Error Handling**: Standardize exception handling patterns

### Phase 2: Context Profiles Feature

#### New Commands
1. **profile save <name>**: Save current context configuration
2. **profile load <name>**: Load and activate saved profile
3. **profile list**: Display all available profiles
4. **profile delete <name>**: Remove saved profile

#### Storage Design
- **Location**: `.contextr/profiles/` directory
- **Format**: JSON files per profile
- **Schema**: Compatible with existing state.json structure

#### User Experience
- **Seamless Switching**: Single command to change entire context
- **Confirmation Prompts**: For destructive operations (overwrite/delete)
- **Clear Feedback**: Success/error messages for all operations

## Technical Specifications

### File Structure (Proposed)
```
.contextr/
├── state.json          # Current active state
├── profiles/           # Profile storage
│   ├── frontend.json   # Example profile
│   ├── backend.json    # Example profile
│   └── fullstack.json  # Example profile
└── config.json         # Future: Global settings
```

### Profile Schema
```json
{
  "name": "frontend",
  "description": "Frontend development context",
  "watched_patterns": ["src/**/*.tsx", "src/**/*.css"],
  "ignore_patterns": ["**/*.test.tsx", "build/**"],
  "created_at": "2025-07-23T12:00:00Z",
  "updated_at": "2025-07-23T12:00:00Z"
}
```

### API Changes
- **ContextManager**: Add profile management methods
- **CLI**: New profile command group
- **State Management**: Profile-aware save/load operations

## Implementation Plan

### Sprint 1: Foundation (1 week)
- Set up Ruff and Pyright
- Create test infrastructure
- Fix type annotations
- Resolve version mismatch

### Sprint 2: Refactoring (1 week)
- Decouple ContextManager components
- Create profile storage interface
- Write comprehensive tests
- Update documentation

### Sprint 3: Profile Features (2 weeks)
- Implement profile commands
- Add profile storage logic
- Create integration tests
- Update user documentation

### Sprint 4: Polish & Release (1 week)
- Performance optimization
- Error handling improvements
- Documentation updates
- Release preparation

## Success Metrics

### Technical Metrics
- 100% type coverage with Pyright strict mode
- 80%+ test coverage
- All Ruff checks passing
- Profile operations < 100ms

### User Experience Metrics
- Context switch time reduced from minutes to seconds
- Zero data loss during profile operations
- Clear error messages for all edge cases
- Backward compatibility maintained

## Risk Mitigation

### Technical Risks
1. **State Corruption**: Implement atomic file operations
2. **Performance**: Use efficient file pattern matching
3. **Compatibility**: Maintain existing CLI interface

### User Risks
1. **Data Loss**: Implement backup before destructive operations
2. **Confusion**: Clear documentation and help text
3. **Migration**: Smooth upgrade path for existing users

## Future Considerations

### Potential Enhancements
- Profile templates for common scenarios
- Profile sharing/export functionality
- Auto-detection of project type
- Integration with version control
- Cloud sync for profiles

### Extensibility Points
- Plugin system for custom formatters
- Hook system for profile events
- Configuration file support
- Multiple output targets

## Conclusion

This brownfield PRD provides a comprehensive view of the current `contextr` state and a clear path forward for implementing the Context Profiles feature. The phased approach ensures minimal disruption while delivering significant user value.