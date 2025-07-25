# Story etc.1: Setup CI/CD Pipeline for Python Package Deployment

## Status

Ready for Review

## Story

**As a** contextr maintainer,
**I want** automated CI/CD pipelines that build and deploy the package to PyPI,
**so that** releases are consistent, automated, and I can focus on development rather than manual deployment steps.

## Acceptance Criteria

1. GitHub Actions workflow for CI (tests, linting, type checking) on every push/PR
2. Automated package building and validation on tagged releases
3. Automatic deployment to PyPI when a version tag is pushed (e.g., v1.0.1)
4. Build artifacts are properly created (wheel and source distribution)
5. Branch protection with main branch requiring passing CI checks
6. Clear documentation on the release process and branch workflow
7. Secrets properly configured for PyPI authentication

## Tasks / Subtasks

- [x] Create GitHub Actions CI workflow (AC: 1, 5)
  - [x] Create `.github/workflows/ci.yml` for continuous integration
  - [x] Run tests with pytest on Python 3.13
  - [x] Run ruff linting and format checking
  - [x] Run pyright type checking
  - [x] Generate and upload coverage reports
  - [x] Configure to run on push to main/dev and all PRs
- [x] Create GitHub Actions release workflow (AC: 2, 3, 4)
  - [x] Create `.github/workflows/release.yml` for PyPI deployment
  - [x] Trigger on version tags (v*.*.\*)
  - [x] Build source distribution (sdist) and wheel
  - [x] Validate built packages with twine check
  - [x] Upload to PyPI using trusted publishing or API token
- [ ] Setup PyPI configuration (AC: 3, 7)
  - [ ] Create PyPI account if needed
  - [ ] Configure trusted publishing or generate API token
  - [ ] Add PYPI_API_TOKEN to GitHub repository secrets
  - [ ] Test token permissions with test deployment
- [ ] Configure branch protection rules (AC: 5)
  - [ ] Protect main branch in GitHub settings
  - [ ] Require PR reviews before merging
  - [ ] Require status checks to pass (CI workflow)
  - [ ] Dismiss stale reviews when new commits are pushed
  - [ ] Include administrators in restrictions
- [x] Create release documentation (AC: 6)
  - [x] Document branch strategy (main for releases, dev for development)
  - [x] Document version tagging process
  - [x] Create RELEASE.md with step-by-step release instructions
  - [x] Document how to test releases with TestPyPI first
  - [x] Include rollback procedures
- [x] Setup development workflow (AC: 6)
  - [ ] Configure dev branch as default for new work
  - [x] Document PR workflow from dev to main
  - [x] Create PR template for consistency
  - [x] Document local development setup

## Dev Notes

### Architecture Context

**Technology Stack** [Source: architecture.md#current-architecture]

- Python 3.13+ requirement
- uv package manager for development
- setuptools build backend
- PyPI distribution format

**Build System** [Source: pyproject.toml]

```toml
[build-system]
requires = ["setuptools>=61.0", "wheel"]
build-backend = "setuptools.build_meta"
```

**Quality Tools** [Source: pyproject.toml]

- Ruff for linting/formatting (line-length: 88)
- Pyright in strict mode for type checking
- pytest with coverage reporting
- Current test coverage: ~62%

**Package Metadata** [Source: pyproject.toml]

- Package name: contextr
- Current version: 1.0.0
- Entry points: contextr and ctxr (alias)
- MIT license
- Author: Nathan Luo

**Project URLs** [Source: pyproject.toml]

- Homepage: https://github.com/nathan-luo/contextr
- Bug Tracker: https://github.com/nathan-luo/contextr/issues

### Previous Story Insights

- Testing infrastructure established with pytest
- Ruff and Pyright configurations working and passing
- All development tooling properly configured
- 89 tests currently passing

### File Locations Based on Project Structure

- CI workflow: `.github/workflows/ci.yml`
- Release workflow: `.github/workflows/release.yml`
- Release documentation: `RELEASE.md`
- PR template: `.github/pull_request_template.md`

### Testing Requirements

**CI Testing Matrix**

- Test on Python 3.13
- Test on Ubuntu, macOS, and Windows
- Run full test suite with coverage
- Ensure all quality checks pass

### Technical Constraints

- Must maintain compatibility with uv package manager
- Use GitHub's built-in environments for deployment protection
- Follow Python packaging best practices (PEP 517/518)
- Use trusted publishing if possible (more secure than tokens)

### Performance Requirements

- CI builds should complete in under 5 minutes
- Deployment to PyPI should complete in under 2 minutes
- Use caching for dependencies to speed up builds

## Change Log

| Date       | Version | Description            | Author   |
| ---------- | ------- | ---------------------- | -------- |
| 2025-07-25 | 1.0     | Initial story creation | Bob (SM) |

## Dev Agent Record

### Agent Model Used

claude-opus-4-20250514

### Debug Log References

- Successfully created GitHub Actions CI workflow with matrix testing
- Created release workflow with trusted publishing support
- All local tests pass (89 tests, 62% coverage)
- Ruff and pyright checks pass

### Completion Notes List

- CI workflow configured for Python 3.13 on Ubuntu, Windows, and macOS
- Release workflow uses trusted publishing with fallback to API token
- Coverage reports will be uploaded to Codecov (token needs to be added)
- PR template includes comprehensive checklist
- RELEASE.md provides detailed release process including TestPyPI testing
- Branch protection and PyPI configuration require manual setup in GitHub/PyPI

**Manual Steps Still Required:**
1. Configure branch protection rules in GitHub settings
2. Setup PyPI account and configure trusted publishing or API token
3. Add PYPI_API_TOKEN to GitHub repository secrets (if using token)
4. Configure dev branch as default in GitHub settings
5. Add CODECOV_TOKEN to GitHub repository secrets (optional)

### File List

- Created: `.github/workflows/ci.yml`
- Created: `.github/workflows/release.yml`
- Created: `RELEASE.md`
- Created: `.github/pull_request_template.md`

## QA Results

_To be filled by QA Agent_
