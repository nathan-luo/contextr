# Epic 4: Performance & Workflow Optimization

## Epic Goal
Optimize CI/CD workflows to run tests only on PRs to main branch and improve pattern matching performance to prevent accidental processing of large directories like node_modules or .venv.

## Epic Description

**Existing System Context:**
- Current CI/CD: GitHub Actions running on every push/PR to main/dev branches  
- Technology stack: Python 3.12+, uv package manager, pytest, ruff, pyright
- Pattern matching: Regex-based ignore system with O(n×m) complexity

**Enhancement Details:**
- What's being added/changed:
  - Restrict CI test runs to PRs targeting main only
  - Add pre-commit hooks for local validation
  - Optimize pattern matching with caching and early termination
  - Add safeguards against large directory traversal
- How it integrates: Updates to existing .github/workflows/ci.yml and ignore_utils.py
- Success criteria:
  - CI runs reduced by ~75%
  - Pattern matching 10x faster on large directories
  - Zero accidental processing of node_modules/.venv

## Stories

### Story 1: Optimize CI/CD Workflow Configuration
**Priority:** High
**Description:** Modify GitHub Actions to run full test suite only on PRs to main, while keeping minimal checks on other branches.

**Acceptance Criteria:**
1. Full test suite (pytest, coverage) runs ONLY on pull requests targeting main branch
2. Formatting and linting checks removed from all branches except PRs to main
3. Release workflow remains unchanged (triggers on version tags)
4. Pre-commit framework installed with ruff format, ruff check, and pyright hooks
5. Developer documentation updated with new workflow

### Story 2: Implement Pattern Matching Performance Optimizations
**Priority:** High  
**Description:** Optimize the ignore pattern matching system to handle large directories efficiently.

**Acceptance Criteria:**
1. Compiled regex patterns are cached to prevent recompilation
2. Directory-level ignore patterns terminate traversal early
3. Performance benchmarks show 10x improvement on directories with 10k+ files
4. All existing ignore pattern tests continue to pass
5. Memory usage remains reasonable under high file counts

### Story 3: Enhance Ignore System Robustness
**Priority:** Medium
**Description:** Add safeguards and improvements to prevent accidental processing of large directories.

**Acceptance Criteria:**
1. .gitignore updated with common large directories (node_modules/, htmlcov/, etc.)
2. Warning system implemented for directories over 1000 files
3. Progress indicators added for operations taking >2 seconds
4. Automatic exclusion of .git/ directory from all traversals
5. Integration tests added for large directory scenarios

## Technical Constraints
- Must maintain backward compatibility with existing CLI commands
- Performance improvements must be transparent to users
- No breaking changes to public APIs
- All changes must pass existing test suite

## Definition of Done
- [ ] All stories completed with acceptance criteria met
- [ ] Existing functionality verified through testing  
- [ ] CI time reduced for non-main branches
- [ ] Pattern matching benchmarks show 10x improvement
- [ ] No regression in ignore pattern behavior
- [ ] Documentation updated for workflow changes