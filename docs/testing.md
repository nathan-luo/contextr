# Testing Guide

## Local Testing

Run the same checks that CI runs:

```bash
# Install dependencies
uv sync --extra dev

# Format check
uv run ruff format . --check

# Linting
uv run ruff check .

# Type checking
uv run pyright

# Run tests with coverage
uv run pytest --cov=contextr --cov-report=term-missing
```

To fix issues:
```bash
# Auto-format code
uv run ruff format .

# Fix linting issues (where possible)
uv run ruff check . --fix
```

## Cross-Platform Testing

Since platform-specific issues (Windows path handling, macOS case sensitivity, etc.) can only be caught on actual operating systems, we use GitHub Actions for true cross-platform testing.

### Manual Cross-Platform Testing

The repository includes a workflow that can be triggered manually to test on specific platforms:

1. Go to the [Actions tab](../../actions) on GitHub
2. Select "Test on Demand" workflow
3. Click "Run workflow"
4. Choose platform:
   - `all` - Test on Ubuntu, Windows, and macOS
   - `ubuntu-latest` - Test on Ubuntu only
   - `windows-latest` - Test on Windows only  
   - `macos-latest` - Test on macOS only

### Automatic CI Testing

The main CI workflow (`.github/workflows/ci.yml`) automatically runs on:
- All pull requests to the `main` branch
- Tests on Ubuntu, Windows, and macOS
- Uses Python 3.13

## Test Coverage

Current test coverage: ~71%

View detailed coverage report after running tests:
```bash
# Generate HTML coverage report
uv run pytest --cov=contextr --cov-report=html

# Open in browser
open htmlcov/index.html  # macOS
xdg-open htmlcov/index.html  # Linux
start htmlcov/index.html  # Windows
```

## Platform-Specific Considerations

### Windows
- Path separators (`\` vs `/`)
- Case-insensitive filesystem
- Different line endings (CRLF vs LF)
- No symlink support without admin rights

### macOS
- Case-insensitive filesystem (by default)
- Different `sed` command syntax
- `.DS_Store` files

### Linux
- Case-sensitive filesystem
- Native Docker support
- Different package managers

## Debugging Test Failures

If tests pass locally but fail in CI:

1. **Check the platform** - It's likely a platform-specific issue
2. **Check Python version** - CI uses Python 3.13
3. **Check for uncommitted files** - CI runs on clean checkout
4. **Review CI logs** - Available in the Actions tab on GitHub

## Writing Cross-Platform Tests

When writing tests, consider:

```python
import os
import sys
from pathlib import Path

def test_path_handling():
    # Use pathlib for cross-platform paths
    path = Path("src") / "file.py"
    
    # Don't hardcode path separators
    # BAD: "src/file.py" or "src\\file.py"
    # GOOD: Path("src") / "file.py"
    
    # Handle platform differences
    if sys.platform == "win32":
        # Windows-specific code
        pass
    elif sys.platform == "darwin":
        # macOS-specific code
        pass
    else:
        # Linux/Unix code
        pass
```