# Release Process for contextr

This document outlines the release process for the contextr package.

## Branch Strategy

- **main**: Production branch for releases only
- **dev**: Default development branch for new features

## Prerequisites

1. Ensure you have push access to the repository
2. Ensure PyPI account is configured (see below)
3. All changes are merged to main branch
4. All CI checks are passing

## Release Steps

### 1. Prepare the Release

1. Create a PR from `dev` to `main`:
   ```bash
   git checkout main
   git pull origin main
   git checkout dev
   git pull origin dev
   git checkout -b release/v1.x.x
   ```

2. Update version in `pyproject.toml`:
   ```toml
   version = "1.x.x"
   ```

3. Update CHANGELOG.md with release notes

4. Commit changes:
   ```bash
   git add pyproject.toml CHANGELOG.md
   git commit -m "chore: prepare release v1.x.x"
   git push origin release/v1.x.x
   ```

5. Create PR from `release/v1.x.x` to `main`
6. Wait for CI checks to pass
7. Get PR reviewed and approved

### 2. Tag and Release

1. After PR is merged to main:
   ```bash
   git checkout main
   git pull origin main
   ```

2. Create and push tag:
   ```bash
   git tag -a v1.x.x -m "Release v1.x.x"
   git push origin v1.x.x
   ```

3. The GitHub Actions release workflow will automatically:
   - Build the distribution packages
   - Validate the packages
   - Upload to PyPI

### 3. Verify Release

1. Check GitHub Actions for successful deployment
2. Verify package on PyPI: https://pypi.org/project/contextr/
3. Test installation:
   ```bash
   pip install contextr==1.x.x
   contextr --version
   ```

## Testing with TestPyPI

Before releasing to production PyPI, you can test with TestPyPI:

1. Build locally:
   ```bash
   python -m build
   ```

2. Upload to TestPyPI:
   ```bash
   twine upload --repository testpypi dist/*
   ```

3. Test installation:
   ```bash
   pip install --index-url https://test.pypi.org/simple/ contextr
   ```

## Rollback Procedures

If a release has issues:

1. **Delete the tag** (if not yet published):
   ```bash
   git tag -d v1.x.x
   git push origin :refs/tags/v1.x.x
   ```

2. **Yank the release** on PyPI:
   - Login to PyPI
   - Go to the release
   - Click "Manage" → "Yank"
   - This prevents new installations but doesn't break existing ones

3. **Create a patch release**:
   - Fix the issue in a new branch
   - Follow the release process with a patch version (e.g., v1.x.x+1)

## PyPI Configuration

### Option 1: Trusted Publishing (Recommended)

1. Go to PyPI account settings
2. Add a new trusted publisher:
   - Owner: nathan-luo
   - Repository: contextr
   - Workflow: release.yml
   - Environment: pypi

### Option 2: API Token

1. Generate API token on PyPI
2. Add to GitHub repository secrets as `PYPI_API_TOKEN`

## Local Development Setup

For contributors:

1. Clone the repository:
   ```bash
   git clone https://github.com/nathan-luo/contextr.git
   cd contextr
   ```

2. Install uv:
   ```bash
   curl -LsSf https://astral.sh/uv/install.sh | sh
   ```

3. Install dependencies:
   ```bash
   uv sync --extra dev
   ```

4. Create feature branch from dev:
   ```bash
   git checkout dev
   git pull origin dev
   git checkout -b feature/your-feature
   ```

5. Make changes and test:
   ```bash
   uv run pytest
   uv run ruff check .
   uv run pyright
   ```

6. Push and create PR to dev branch