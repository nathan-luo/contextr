# CI/CD Pipeline Documentation for contextr

This document provides technical documentation for the CI/CD pipeline implementation in the contextr project, detailing the GitHub Actions workflows, PyPI publishing configuration, and operational procedures.

## Table of Contents

1. [Pipeline Architecture Overview](#pipeline-architecture-overview)
2. [CI Workflow Implementation](#ci-workflow-implementation)
3. [Release Workflow Implementation](#release-workflow-implementation)
4. [PyPI Publishing Configuration](#pypi-publishing-configuration)
5. [Branch Protection and Git Flow](#branch-protection-and-git-flow)
6. [Operational Procedures](#operational-procedures)
7. [Technical Troubleshooting](#technical-troubleshooting)

## Pipeline Architecture Overview

The contextr CI/CD pipeline consists of two primary GitHub Actions workflows:

1. **Continuous Integration (CI)**: Automated quality gates for all code changes
2. **Release Management**: Automated PyPI package publishing on version tags

### Technology Stack

- **CI Platform**: GitHub Actions
- **Package Manager**: uv (replacing pip/poetry)
- **Build Backend**: setuptools (PEP 517/518 compliant)
- **Distribution Target**: PyPI (Python Package Index)
- **Testing Framework**: pytest with coverage reporting
- **Code Quality**: Ruff (linting/formatting), Pyright (type checking)

### Workflow Triggers

```yaml
# CI triggers on:
- Push to branches: [main, dev]
- Pull requests targeting: [main, dev]

# Release triggers on:
- Version tags matching: v*.*.*
```

## CI Workflow Implementation

The CI workflow (`.github/workflows/ci.yml`) implements a comprehensive testing matrix to ensure compatibility across multiple environments.

### Test Matrix Configuration

```yaml
strategy:
  fail-fast: false
  matrix:
    os: [ubuntu-latest, windows-latest, macos-latest]
    python-version: ["3.12", "3.13"]
```

This creates 6 parallel jobs testing all combinations of OS and Python versions.

### Workflow Steps Breakdown

1. **Environment Setup**

   ```yaml
   - uses: actions/checkout@v4
   - uses: astral-sh/setup-uv@v5
     with:
       enable-cache: true
       cache-dependency-glob: "uv.lock"
   ```

   - Leverages uv's caching mechanism for faster builds
   - Cache key based on `uv.lock` ensures cache invalidation on dependency changes

2. **Quality Checks**

   ```yaml
   - run: uv run ruff format . --check # Formatting verification
   - run: uv run ruff check . # Linting (F, E/W, I rules)
   - run: uv run pyright # Strict type checking
   ```

3. **Test Execution**

   ```yaml
   - run: uv run pytest --cov=contextr --cov-report=term-missing --cov-report=xml
   ```

   - Generates both terminal and XML coverage reports
   - Current baseline: 89 tests, 62% coverage

4. **Coverage Reporting**
   ```yaml
   - uses: codecov/codecov-action@v4
     if: matrix.os == 'ubuntu-latest' && matrix.python-version == '3.12'
   ```
   - Single upload to avoid duplicate reports
   - Requires `CODECOV_TOKEN` secret (optional but recommended)

### Performance Optimizations

- **Dependency caching**: ~60% reduction in installation time
- **Parallel execution**: 6 jobs run simultaneously
- **Selective coverage upload**: Prevents redundant API calls

## Release Workflow Implementation

The release workflow (`.github/workflows/release.yml`) automates PyPI package publishing using a two-job approach for reliability.

### Job Architecture

```yaml
jobs:
  build: # Builds and validates distribution
  publish: # Publishes to PyPI (depends on build)
```

### Build Job Details

1. **Package Building**

   ```yaml
   - run: |
       uv pip install --system build twine
       python -m build
   ```

   - Uses PEP 517 build isolation
   - Generates both wheel and sdist distributions

2. **Distribution Validation**

   ```yaml
   - run: twine check dist/*
   ```

   - Validates package metadata
   - Ensures PyPI compatibility before upload

3. **Artifact Management**
   ```yaml
   - uses: actions/upload-artifact@v4
     with:
       name: dist-files
       path: dist/
   ```
   - Preserves build artifacts between jobs
   - Enables build/publish separation

### Publish Job Configuration

```yaml
environment:
  name: pypi
  url: https://pypi.org/p/contextr
```

- Creates deployment environment for protection rules
- Provides direct link to published package

### Publishing Methods

The workflow supports two authentication methods:

1. **Trusted Publishing** (Recommended)

   ```yaml
   - uses: pypa/gh-action-pypi-publish@release/v1
   ```

   - Uses OpenID Connect (OIDC) for authentication
   - No long-lived credentials required

2. **API Token Fallback**
   ```yaml
   password: ${{ secrets.PYPI_API_TOKEN }}
   skip-existing: true
   ```
   - Falls back to token if trusted publishing unavailable
   - `skip-existing` prevents duplicate version errors

## PyPI Publishing Configuration

### Trusted Publishing Setup

Trusted publishing eliminates the need for API tokens by establishing trust between GitHub Actions and PyPI.

1. **PyPI Configuration**

   - Navigate to: PyPI → Account Settings → Publishing
   - Add publisher with parameters:
     ```
     Owner: nathan-luo
     Repository: contextr
     Workflow: release.yml
     Environment: pypi
     ```

2. **Security Benefits**
   - No credential rotation required
   - Automatic token generation per workflow run
   - Cryptographically verified publisher identity

### API Token Configuration (Alternative)

For environments where trusted publishing is unavailable:

1. **Token Generation**

   - Scope: Project-specific recommended over account-wide
   - Naming convention: `contextr-github-actions`

2. **Secret Storage**
   ```bash
   # Repository Settings → Secrets → Actions
   Name: PYPI_API_TOKEN
   Value: pypi-[token-string]
   ```

## Branch Protection and Git Flow

### Branch Strategy

```
main (protected) ← dev (default) ← feature branches
      ↑                               ↑
      └─────── Releases only ─────────┘
```

### Protection Rules Configuration

```yaml
# Main branch protection
- Require pull request reviews: 1
- Dismiss stale reviews: true
- Require status checks: ["test"]
- Require up-to-date branches: true
- Include administrators: true
```

### Required Status Checks

The CI workflow creates the following status checks:

- `test (ubuntu-latest, 3.12)`
- `test (ubuntu-latest, 3.13)`
- `test (windows-latest, 3.12)`
- `test (windows-latest, 3.13)`
- `test (macos-latest, 3.12)`
- `test (macos-latest, 3.13)`

Configure branch protection to require all matrix jobs.

## Operational Procedures

### Release Process

1. **Version Preparation**

   ```bash
   # From dev branch
   git checkout -b release/v1.0.1
   # Update pyproject.toml version
   git commit -m "chore: prepare release v1.0.1"
   ```

2. **Release PR Flow**

   ```bash
   # Create PR: release/v1.0.1 → main
   # After merge:
   git checkout main
   git pull origin main
   git tag -a v1.0.1 -m "Release v1.0.1"
   git push origin v1.0.1
   ```

3. **Automated Steps**
   - GitHub Actions detects tag push
   - Builds distribution packages
   - Validates with twine
   - Publishes to PyPI
   - Updates deployment environment

### Monitoring Deployments

1. **GitHub Actions Dashboard**

   - Real-time workflow execution
   - Step-by-step logs
   - Artifact downloads

2. **PyPI Verification**

   ```bash
   # Verify package availability
   pip index versions contextr

   # Test installation
   pip install contextr==1.0.1
   ```

### Rollback Procedures

1. **Pre-publish Rollback**

   ```bash
   git tag -d v1.0.1
   git push origin :refs/tags/v1.0.1
   ```

2. **Post-publish Mitigation**
   - PyPI → Manage → Yank release
   - Publish patch version immediately
   - Update users via GitHub releases

## Technical Troubleshooting

### Common CI Failures

1. **Platform-Specific Test Failures**

   ```python
   # Issue: Path separator differences
   # Solution: Use pathlib
   from pathlib import Path
   path = Path("dir") / "file.txt"
   ```

2. **Type Checking Errors**

   ```bash
   # Local verification
   uv run pyright --pythonversion 3.12
   ```

3. **Coverage Threshold Failures**
   ```bash
   # Generate local coverage report
   uv run pytest --cov=contextr --cov-report=html
   # View htmlcov/index.html
   ```

### Release Pipeline Issues

1. **Build Failures**

   ```bash
   # Local build testing
   python -m build
   twine check dist/*
   ```

2. **Authentication Errors**

   - Verify trusted publisher configuration
   - Check token scope and expiration
   - Ensure environment name matches

3. **Version Conflicts**
   ```bash
   # Check existing versions
   pip index versions contextr
   ```

### Performance Optimization

1. **Workflow Duration Analysis**

   - Check Actions → Workflow → Timing
   - Identify bottlenecks in test matrix
   - Consider job parallelization

2. **Cache Effectiveness**
   ```yaml
   # Monitor cache hit rates
   # Add cache debugging:
   - name: Cache info
     run: |
       echo "Cache hit: ${{ steps.setup-uv.outputs.cache-hit }}"
   ```

## Maintenance Guidelines

### Dependency Updates

```bash
# Update GitHub Actions
dependabot.yml configuration recommended

# Update Python dependencies
uv lock --upgrade-package pytest
```

### Workflow Versioning

- Pin action versions for stability
- Use dependabot for automated updates
- Test major version upgrades in separate branch

### Security Considerations

1. **Secret Rotation**

   - Rotate PyPI tokens quarterly
   - Use project-scoped tokens
   - Enable 2FA on PyPI account

2. **Workflow Permissions**

   ```yaml
   permissions:
     contents: read
     id-token: write # Only for trusted publishing
   ```

3. **Supply Chain Security**
   - Enable Dependabot alerts
   - Review workflow changes carefully
   - Use commit signing for releases
