# contextr Project Structure & Conventions

## Overview

This document outlines the structure, conventions, and development practices for the `contextr` project - a CLI tool for sharing codebases with LLMs.

## Project Layout

```
contextr/
├── .claude/                    # Claude-specific configuration
├── .contextr/                  # Runtime state directory (git-ignored)
│   ├── state.json             # Current watched/ignored patterns
│   └── profiles/              # (Future) Profile storage
├── .cursor/                    # Cursor IDE configuration
├── .gemini/                    # Gemini configuration
├── .git/                       # Git repository
├── .gitignore                  # Git ignore patterns
├── .python-version             # Python version specification (3.12)
├── CLAUDE.md                   # Project guidelines for AI assistants
├── README.md                   # User-facing documentation
├── docs/                       # Documentation directory
│   ├── brownfield-architecture.md  # Current architecture analysis
│   ├── brownfield-prd.md          # Brownfield requirements
│   ├── prd.md                     # Original product requirements
│   └── project-structure.md       # This file
├── install.py                  # Custom installation script
├── pyproject.toml              # Python package configuration
├── src/                        # Source code directory
│   └── contextr/              # Main package
│       ├── __init__.py        # Package initialization
│       ├── cli.py             # CLI command definitions
│       ├── formatters.py      # Output formatting
│       ├── manager.py         # Core business logic
│       └── utils/             # Utility modules
│           ├── __init__.py
│           ├── ignore_utils.py # Gitignore pattern handling
│           └── path_utils.py   # Path manipulation
└── tests/                      # (Future) Test directory
    ├── __init__.py
    ├── unit/                   # Unit tests
    ├── integration/            # Integration tests
    └── fixtures/               # Test data
```

## Code Organization

### Package Structure
- **src Layout**: Uses modern Python src/ layout for better testing isolation
- **Modular Design**: Clear separation between CLI, business logic, and utilities
- **Single Responsibility**: Each module has a focused purpose

### Module Responsibilities

#### `cli.py`
- Defines all CLI commands using Typer framework
- Handles user input/output
- Delegates business logic to ContextManager
- Entry point: Creates Typer app instance

#### `manager.py`
- Core business logic for context management with storage abstraction
- Manages watched and ignored file patterns
- Handles state persistence via injected storage backend
- File discovery and filtering
- Profile application support (apply_profile method)

#### `formatters.py`
- Formats file contents for output
- Currently supports XML format for LLMs
- Extensible for future format support

#### `utils/`
- **ignore_utils.py**: Gitignore pattern matching
- **path_utils.py**: Path resolution and manipulation
- Cross-cutting utility functions

## Coding Standards

### Python Version
- **Required**: Python 3.12 or higher
- **Features Used**: Modern type hints, match statements (if applicable)

### Style Guidelines
- **PEP 8 Compliance**: With ~80-90 character line limit
- **Formatting**: Black formatter (88 char line length configured)
- **Import Sorting**: isort with standard grouping
- **Docstrings**: Google style with Args/Returns sections

### Naming Conventions
```python
# Variables and functions: snake_case
def get_file_list():
    file_count = 0
    
# Classes: PascalCase
class ContextManager:
    pass
    
# Constants: UPPER_SNAKE_CASE
DEFAULT_IGNORE_PATTERNS = ["*.pyc", "__pycache__"]

# Private: Leading underscore
def _internal_function():
    pass
```

### Type Hints
```python
from typing import List, Optional, Dict, Set
from pathlib import Path

def find_files(
    patterns: List[str], 
    root: Optional[Path] = None
) -> Set[Path]:
    """Find files matching patterns.
    
    Args:
        patterns: List of glob patterns
        root: Root directory to search from
        
    Returns:
        Set of matching file paths
    """
```

## Development Workflow

### Setup
```bash
# Clone repository
git clone <repo-url>
cd contextr

# Install with development dependencies
pip install -e .

# Or using uv (recommended)
uv pip install -e .
```

### Running Locally
```bash
# Run from source
python -m contextr.cli

# After installation
contextr --help
ctxr --help  # Short alias
```

### Testing Commands
```bash
# Run tests
uv run pytest

# Run with coverage
pytest --cov=contextr --cov-report=html

# Type checking
pyright

# Linting
ruff check .

# Formatting
ruff format .
```

## Configuration Files

### pyproject.toml
- **Build System**: Uses hatchling
- **Dependencies**: Defined in project.dependencies
- **Dev Dependencies**: (To be added) in project.optional-dependencies
- **Tool Configs**: Black, isort settings

### .gitignore
- Excludes `.contextr/` runtime directory
- Standard Python ignores (__pycache__, *.pyc)
- IDE-specific directories

### CLAUDE.md
- Project-specific instructions for AI assistants
- Coding style preferences
- Build and test commands
- Important project guidelines

## State Management

### Runtime State
- **Location**: `.contextr/state.json`
- **Format**: JSON with watched/ignored patterns
- **Persistence**: Saved after each modification

### Future Profile Storage
```
.contextr/
├── state.json          # Active state
├── profiles/           # Named profiles
│   ├── frontend.json
│   ├── backend.json
│   └── testing.json
└── config.json         # Global configuration
```

## CLI Command Structure

### Current Commands
```bash
ctxr watch "**/*.py"      # Add watch pattern
ctxr ignore "**/*.pyc"    # Add ignore pattern
ctxr list                 # Show tracked files
ctxr clear               # Clear all patterns
ctxr sync                # Copy to clipboard
```

### Future Profile Commands
```bash
ctxr profile save <name>   # Save current as profile
ctxr profile load <name>   # Load profile
ctxr profile list         # List profiles
ctxr profile delete <name> # Delete profile
```

## Error Handling

### Principles
- User-friendly error messages
- Graceful degradation
- Clear recovery instructions
- Proper exit codes

### Pattern
```python
try:
    # Operation
    result = perform_operation()
except SpecificError as e:
    console.print(f"[red]Error:[/red] {e}")
    raise typer.Exit(1)
```

## Documentation Standards

### Code Documentation
- All public functions must have docstrings
- Complex logic should have inline comments
- Type hints for all parameters and returns

### User Documentation
- README.md for installation and basic usage
- Comprehensive help text in CLI commands
- Examples for common use cases

## Version Control

### Branch Strategy
- `main`/`master`: Stable releases
- `develop`: Integration branch
- `feature/*`: New features
- `fix/*`: Bug fixes

### Commit Messages
- Clear, concise descriptions
- Reference issues when applicable
- Follow conventional commits (optional)

## Release Process

### Version Numbering
- Semantic versioning: MAJOR.MINOR.PATCH
- Update version in `pyproject.toml` and `__init__.py`

### Release Steps
1. Update version numbers
2. Update changelog
3. Run full test suite
4. Create git tag
5. Build distribution
6. Upload to PyPI

## Future Enhancements

### Planned Structure Changes
- Separate CLI commands into modules
- Add storage abstraction layer
- Implement plugin system
- Add comprehensive test coverage

### Tooling Improvements
- Ruff for linting/formatting
- Pyright for type checking
- Pre-commit hooks
- CI/CD pipeline

## Contributing Guidelines

### Code Contributions
1. Fork repository
2. Create feature branch
3. Write tests for new code
4. Ensure all tests pass
5. Submit pull request

### Quality Checklist
- [ ] Code follows style guidelines
- [ ] All tests pass
- [ ] Type hints added
- [ ] Documentation updated
- [ ] No linting errors

## Maintenance

### Regular Tasks
- Update dependencies
- Review and merge PRs
- Address security alerts
- Update documentation

### Health Metrics
- Test coverage > 80%
- Type coverage 100%
- Zero linting errors
- Up-to-date dependencies