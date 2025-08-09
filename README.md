# contextr (ctxr)

A streamlined command-line tool designed for developers to easily share their codebase with Large Language Models (LLMs). contextr helps you monitor specific files and directories, intelligently handles ignore patterns, and lets you instantly export formatted code context to your clipboard - perfect for pasting into ChatGPT, Claude, or other AI chat interfaces.

Think of it as "git add" but for AI conversations - select the files you want your AI assistant to see, and export them in a Markdown format optimized for LLM comprehension.

## Features

- **🔍 Smart File Selection**: Watch specific file patterns and automatically track changes
- **🚫 Git-Style Ignores**: Full support for ignore patterns including negation with `!`
- **📋 One-Click Export**: Sync changes and copy formatted context to clipboard instantly
- **🎨 LLM-Optimized Output**: Markdown formatting with syntax highlighting for 40+ languages
- **💾 Context Profiles**: Save and instantly switch between different context configurations
- **🔄 Auto-Sync**: Automatically detect when watched files are added or removed
- **🌐 Cross-Platform**: Works seamlessly on Linux, macOS, and Windows
- **🔗 Path Intelligence**: Handles symlinks, `~` expansion, and environment variables
- **🤖 Modern Development**: Type-safe code with 62% test coverage and strict linting

## Installation

### Method 1: Install from PyPI (Recommended)

The easiest way to install (requires Python 3.12+):

```bash
pip install contextr
```

This makes both `ctxr` (short alias) and `contextr` commands available globally.

### Method 2: Install from source

```bash
# Clone the repository
git clone https://github.com/your-username/contextr.git
cd contextr

# Install using uv (recommended for development)
uv sync --extra dev

# Or install with pip
pip install -e .
```

## Quick Start

```bash
# Initialize contextr in your project
ctxr init

# Add files to watch (supports glob patterns)
ctxr watch "src/**/*.py" "docs/*.md" "*.yaml"

# Ignore test files and build artifacts
ctxr ignore "**/__pycache__/**" "**/node_modules/**" "*.pyc"

# Sync watched files and copy to clipboard
ctxr sync

# Paste into your favorite LLM and start coding!
```

## Core Commands

### File Selection & Monitoring

- **`watch <patterns>`** - Add file patterns to monitor
  ```bash
  ctxr watch "src/**/*.py" "tests/**/*.py" "*.md"
  ```

- **`unwatch <patterns>`** - Remove patterns from watch list
  ```bash
  ctxr unwatch "tests/**"
  ```

- **`watch-list`** - Display all watched patterns
  ```bash
  ctxr watch-list
  ```

- **`list`** - Show current file context as a tree
  ```bash
  ctxr list
  ```

### Context Management

- **`sync`** - Refresh context from watched files and export to clipboard
  ```bash
  ctxr sync
  ```

- **`init`** - Initialize contextr in current directory
  ```bash
  ctxr init
  ```

### Ignore Patterns

- **`ignore <pattern>`** - Add pattern to ignore list
  ```bash
  ctxr ignore "**/*.log" "build/**"
  ```

- **`unignore <pattern>`** - Remove pattern from ignore list
  ```bash
  ctxr unignore "**/*.log"
  ```

- **`ignore-list`** - Show all ignored patterns
  ```bash
  ctxr ignore-list
  ```

- **`gitignore-sync`** - Import patterns from .gitignore
  ```bash
  ctxr gitignore-sync
  ```

## Advanced Usage

### Pattern Examples

contextr supports standard glob patterns and git-style ignore syntax:

```bash
# Watch all Python files
ctxr watch "**/*.py"

# Watch specific directories
ctxr watch "src/" "lib/" "tests/"

# Watch with multiple extensions
ctxr watch "**/*.{js,jsx,ts,tsx}"

# Ignore patterns with negation
ctxr ignore "**/*.test.py"    # Ignore all test files
ctxr ignore "!important.test.py"  # But include this specific test
```

### Context Profiles

Save and instantly switch between different context configurations:

```bash
# Save current context as a profile
ctxr profile save backend --description "Backend API development"

# Load a saved profile
ctxr profile load backend

# List all saved profiles
ctxr profile list

# Delete a profile
ctxr profile delete backend
```

## Output Format

contextr generates clean, LLM-friendly Markdown output:

```markdown
# Project Context: your-project
Files selected: 5

## File Structure
```
src/
├── main.py
├── utils/
│   ├── helpers.py
│   └── config.py
└── models/
    └── user.py
README.md
```

## File Contents

### src/main.py
```python
# Your code here with proper syntax highlighting
```

### src/utils/helpers.py
```python
# More code with language detection
```
```

## How It Works

1. **Pattern Matching**: Uses glob patterns to match files, with full support for `**` recursive matching
2. **Ignore System**: Implements git-style ignore rules including directory-specific patterns and negation
3. **File Detection**: Automatically detects programming languages for syntax highlighting
4. **Smart Formatting**: Escapes code blocks properly to prevent Markdown rendering issues
5. **Clipboard Integration**: Uses pyperclip for cross-platform clipboard support

## Configuration

contextr stores its configuration in a `.contextr/` directory in your project:

- `.contextr/state.json` - Current context state and watched patterns
- `.contextr/.ignore` - Custom ignore patterns
- `.contextr/states/` - Saved named states (coming soon)

## Development

### Workflow

contextr uses a streamlined CI/CD workflow:

- **CI Tests**: Run automatically on pull requests to `main` branch only
- **Local Validation**: Use pre-commit hooks for instant feedback during development
- **Release**: Automated PyPI deployment on version tags

### Setup Development Environment

```bash
# Install development dependencies
uv sync --extra dev

# Install pre-commit hooks for local validation
uv run pre-commit install
```

### Local Development Commands

```bash
# Run tests
uv run pytest

# Type checking
uv run pyright

# Linting and formatting
uv run ruff check .
uv run ruff format .

# Run all pre-commit checks manually
uv run pre-commit run --all-files

# Bypass pre-commit hooks when needed
git commit --no-verify -m "Emergency fix"
```

### Pre-commit Hooks

The project uses pre-commit hooks to ensure code quality before commits:

- **ruff-format**: Automatically formats code to project standards
- **ruff**: Checks for code quality issues
- **pyright**: Performs strict type checking

These hooks run automatically on `git commit`. To skip them in special cases, use `--no-verify`.

## Why Use contextr?

**For Developers:**
- 🚀 Save time by automating code context preparation
- 🎯 Ensure you include all relevant files for LLM understanding
- 🔄 Keep context updated as your code changes
- 📦 Manage different contexts for different features/discussions

**For LLMs:**
- 📝 Consistent, well-formatted code presentation
- 🗂️ Clear file structure visualization
- 🏷️ Proper syntax highlighting for better comprehension
- 📍 Complete file paths for precise references

## Requirements

- Python >= 3.12
- Cross-platform: Linux, macOS, Windows

## License

MIT License

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## Roadmap

- [x] Context Profiles - Save and switch between different contexts
- [ ] Profile templates for common project types
- [ ] Interactive file selection mode
- [ ] Custom output templates
- [ ] Integration with popular IDEs
- [ ] Direct LLM API integration
- [ ] Context size optimization
- [ ] Team profile sharing