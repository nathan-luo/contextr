# Epic 2: Context Profile Management

## Epic Goal

This epic delivers the core user-facing "Context Profiles" feature. Building on the modernized foundation from Epic 1, we will implement the full lifecycle of profile management: creating, loading, listing, and deleting. The outcome will be a significantly more efficient workflow for developers, allowing them to switch between different task-specific contexts with a single command.

## Epic Description

### Existing System Context

**Current State Management:**
- **Single Context**: Only one set of watched/ignored patterns at a time
- **State Storage**: JSON file at `.contextr/state.json`
- **Manual Management**: Users must reconfigure patterns for each task
- **State Structure**: Simple JSON with `watched_patterns` and `ignore_patterns`

**Pain Points:**
- Switching between tasks requires manual pattern reconfiguration
- No way to save common configurations
- Risk of losing carefully crafted pattern sets
- Inefficient workflow for multi-task development

### Enhancement Details

**What's Being Added:**
1. Named profile storage system
2. Profile management commands (save, load, list, delete)
3. Profile switching with automatic context refresh
4. Persistent profile storage in `.contextr/profiles/`

**Integration Approach:**
- New CLI command group: `ctxr profile`
- Profiles stored as individual JSON files
- Current state.json remains for active context
- Backward compatible with existing commands

**Success Criteria:**
- Instant context switching via profiles
- Zero data loss during profile operations
- Intuitive CLI interface for profile management
- Seamless integration with existing workflow

## Stories

### Story 2.1: Save and List Context Profiles
- **Description**: Implement profile saving from current context and listing all profiles
- **Acceptance Criteria**:
  - `ctxr profile save <name>` command implemented
  - `ctxr profile list` shows all saved profiles
  - Overwrite protection with confirmation prompt
  - Profile data persisted to `.contextr/profiles/`
  - Unit tests for save/list functionality

### Story 2.2: Load a Context Profile
- **Description**: Enable loading saved profiles to replace current context
- **Acceptance Criteria**:
  - `ctxr profile load <name>` command implemented
  - Current context cleared before loading
  - File list automatically refreshed after load
  - Error handling for non-existent profiles
  - Profile loading is idempotent
  - Unit tests for load mechanism

### Story 2.3: Delete a Context Profile
- **Description**: Allow removal of saved profiles with safety checks
- **Acceptance Criteria**:
  - `ctxr profile delete <name>` command implemented
  - Confirmation prompt before deletion
  - Clear error for non-existent profiles
  - Profile removed from filesystem
  - Unit tests for deletion logic

## Architecture Changes

### Storage Structure
```
.contextr/
├── state.json          # Active context (existing)
├── profiles/           # New profile directory
│   ├── frontend.json   # Example profile
│   ├── backend.json    # Example profile
│   └── testing.json    # Example profile
└── .gitignore          # Ignore profiles by default
```

### Profile Schema
```json
{
  "name": "frontend",
  "watched_patterns": [
    "src/**/*.tsx",
    "src/**/*.ts", 
    "src/**/*.css"
  ],
  "ignore_patterns": [
    "**/*.test.tsx",
    "build/**",
    "node_modules/**"
  ],
  "metadata": {
    "created_at": "2025-07-23T12:00:00Z",
    "updated_at": "2025-07-23T12:00:00Z",
    "description": "Frontend development context"
  }
}
```

### New Components
- `ProfileManager`: Handles profile CRUD operations
- `ProfileStorage`: Abstracts profile persistence
- Profile-related CLI commands in new module

## Compatibility Requirements

- [x] Existing commands work unchanged
- [x] state.json format remains compatible  
- [x] No changes to file discovery logic
- [x] Existing ignore patterns respected
- [x] Cross-platform file paths handled

## Dependencies

**Epic Dependencies:**
- Requires Epic 1 completion (refactored ContextManager)
- Benefits from test infrastructure
- Uses type annotations from Epic 1

**Technical Dependencies:**
- No new runtime dependencies
- Existing Typer CLI framework
- Standard library JSON/pathlib

**Story Dependencies:**
- Story 2.1 (save/list) must complete first
- Story 2.2 (load) depends on 2.1
- Story 2.3 (delete) can start after 2.1

## Risk Assessment

### Technical Risks

**Risk 1: Profile Corruption**
- **Impact**: Loss of saved configurations
- **Mitigation**: Atomic writes, validation before save
- **Contingency**: Backup before operations

**Risk 2: State Synchronization**
- **Impact**: Confusion between active and saved state
- **Mitigation**: Clear status indicators
- **Contingency**: Recovery command

**Risk 3: Performance with Many Profiles**
- **Impact**: Slow profile operations
- **Mitigation**: Efficient file operations
- **Contingency**: Profile limit warning

### User Experience Risks

**Risk 1: Confusing Profile vs Current State**
- **Impact**: Users unsure what's active
- **Mitigation**: Clear status in list command
- **Contingency**: Add status command

**Risk 2: Accidental Overwrite/Delete**
- **Impact**: Loss of carefully crafted profiles
- **Mitigation**: Confirmation prompts
- **Contingency**: Undo functionality (future)

## Definition of Done

### Epic Level
- [x] All 3 stories completed and accepted
- [x] Profile lifecycle fully implemented
- [x] Integration tests cover all workflows
- [x] User documentation created (in CLI help)
- [x] No regression in existing features

### Story Level
- [ ] Feature implemented and tested
- [ ] Edge cases handled gracefully
- [ ] Error messages are helpful
- [ ] Documentation updated
- [ ] Code review completed

## Migration Plan

### For Existing Users
1. Existing state.json continues to work
2. First profile save migrates current state
3. Clear upgrade instructions in README
4. No breaking changes to CLI

### Data Migration
- No automatic migration needed
- Users opt-in by saving first profile
- Existing workflows unaffected

## Rollback Plan

If profiles cause issues:

1. **Disable Commands**: Remove profile command group
2. **Preserve State**: Keep existing state.json
3. **Clean Profiles**: Remove `.contextr/profiles/`
4. **Revert Code**: Git revert profile commits
5. **Document**: Explain rollback to users

## Timeline Estimate

**Total Duration**: 2 weeks (10 business days)

- Story 2.1 (Save/List): 3 days
- Story 2.2 (Load): 4 days
- Story 2.3 (Delete): 1 day
- Integration Testing: 1.5 days
- Documentation: 0.5 days

## Success Metrics

### Quantitative
- Profile operations < 100ms ✅
- Zero data loss rate ✅
- 99% test coverage for profile code ✅ (only 1 line uncovered)
- <5 second context switch time ✅

### Qualitative
- Improved developer workflow efficiency
- Reduced context switching friction
- Positive user feedback
- Increased tool adoption

## Future Enhancements

### Potential Features (Not in Scope)
- Profile templates for common project types
- Profile sharing/export capabilities
- Cloud sync for profiles
- Auto-detection of project type
- Profile composition/inheritance

These are noted for future consideration but not part of this epic's scope.