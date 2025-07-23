# Epic 1: Project Modernization & Foundation

## Epic Goal

This epic focuses on improving the project's long-term health and developer experience. We will integrate a comprehensive suite of modern tooling for linting, formatting, and type-checking. We will also introduce a testing framework and refactor the core `ContextManager` to make it more modular and ready for new features, ensuring that all future development is built on a stable and maintainable foundation.

## Epic Description

### Existing System Context

**Current Project State:**
- **Technology Stack**: Python 3.12+, Typer CLI, Rich, Pyperclip
- **Build System**: Modern pyproject.toml with setuptools
- **Code Organization**: src/ layout with clear module separation
- **Current Tooling**: Basic Black/isort configuration only

**Key Components:**
- `ContextManager`: Core business logic for file pattern management
- `cli.py`: Typer-based command interface
- `formatters.py`: XML output formatting for LLMs
- `utils/`: Path and ignore pattern utilities

### Enhancement Details

**What's Being Added:**
1. Modern development tooling (Ruff, Pyright, pytest)
2. Comprehensive type annotations throughout codebase
3. Unit and integration test infrastructure
4. Refactored ContextManager for extensibility

**Integration Approach:**
- Tool configurations added to existing pyproject.toml
- Type annotations added without changing functionality
- Tests added alongside existing code structure
- ContextManager refactored to maintain API compatibility

**Success Criteria:**
- 100% type coverage with Pyright strict mode
- 80%+ test coverage achieved
- All Ruff checks passing
- Zero breaking changes to existing functionality

## Stories

### Story 1.1: Integrate Ruff for Linting and Formatting
- **Description**: Add Ruff as development dependency and configure comprehensive linting rules
- **Acceptance Criteria**:
  - Ruff added to pyproject.toml with [tool.ruff] configuration
  - Entire codebase passes Ruff formatting and linting
  - CLAUDE.md updated with Ruff usage instructions

### Story 1.2: Configure Pyright for Strict Type Checking  
- **Description**: Set up Pyright for strict type checking across the codebase
- **Acceptance Criteria**:
  - Pyright added as development dependency
  - [tool.pyright] configuration with strict mode enabled
  - All type errors resolved in existing code
  - Guidelines updated with Pyright instructions

### Story 1.3: Set Up Pytest Framework
- **Description**: Establish pytest infrastructure for automated testing
- **Acceptance Criteria**:
  - pytest added as development dependency
  - tests/ directory structure created
  - pytest runs successfully with test discovery
  - Sample unit test created and passing

### Story 1.4: Refactor ContextManager for Extensibility
- **Description**: Decouple state persistence from context management logic
- **Acceptance Criteria**:
  - State I/O logic separated from business logic
  - All existing functionality maintained
  - Unit tests for core ContextManager methods
  - Methods documented with new structure

## Compatibility Requirements

- [x] Existing CLI commands remain unchanged
- [x] State file format remains compatible
- [x] No changes to public API surface
- [x] Performance characteristics maintained
- [x] Cross-platform support preserved

## Dependencies

**Technical Dependencies:**
- Python 3.12+ already required
- No new runtime dependencies
- Development dependencies only

**Story Dependencies:**
- Stories 1.1 and 1.2 can run in parallel
- Story 1.3 can start anytime
- Story 1.4 benefits from 1.3 completion (for testing)

## Risk Assessment

### Technical Risks

**Risk 1: Type Annotation Complexity**
- **Impact**: High effort to annotate complex dynamic code
- **Mitigation**: Start with public APIs, iterate on internals
- **Contingency**: Use `Any` type sparingly where needed

**Risk 2: Test Coverage Goals**
- **Impact**: 80% coverage may be challenging initially
- **Mitigation**: Focus on critical paths first
- **Contingency**: Accept 70% for first iteration

**Risk 3: Breaking Changes During Refactor**
- **Impact**: Could break existing user workflows
- **Mitigation**: Comprehensive testing before refactor
- **Contingency**: Feature flag for new implementation

### Schedule Risks

**Risk**: Tool integration may uncover many issues
- **Mitigation**: Time-boxed fixes per story
- **Contingency**: Create tech debt backlog

## Definition of Done

### Epic Level
- [ ] All 4 stories completed and accepted
- [ ] Development environment fully modernized
- [ ] Existing functionality verified through tests
- [ ] Documentation updated for new tooling
- [ ] No regression in current features

### Story Level
- [ ] Code changes implemented and reviewed
- [ ] Tests written and passing
- [ ] Documentation updated
- [ ] Linting and type checking pass
- [ ] Acceptance criteria verified

## Rollback Plan

Since this epic adds development tooling without changing runtime behavior:

1. **Tool Removal**: Remove dev dependencies from pyproject.toml
2. **Config Removal**: Remove tool configurations
3. **Revert Refactoring**: Git revert the ContextManager changes
4. **Type Annotations**: Can remain (backward compatible)

## Timeline Estimate

**Total Duration**: 1 week (5 business days)

- Story 1.1 (Ruff): 0.5 days
- Story 1.2 (Pyright): 1 day  
- Story 1.3 (Pytest): 1 day
- Story 1.4 (Refactor): 2.5 days

## Success Metrics

### Quantitative
- Type coverage: 100%
- Test coverage: >80%
- Linting score: 0 errors, 0 warnings
- Build time: <10 seconds

### Qualitative
- Developer confidence increased
- Easier onboarding for contributors
- Faster bug detection
- Improved code maintainability