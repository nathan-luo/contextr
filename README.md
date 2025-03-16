# contextr (ctxr)

A streamlined command-line tool designed for developers to easily share their codebase with Large Language Models (LLMs). contextr helps you monitor specific files and directories, intelligently handles ignoring patterns, and lets you instantly export formatted code context to your clipboard - perfect for pasting into ChatGPT, Claude, or other AI chat interfaces.

Think of it as "git add" but for AI conversations - select the files you want your AI assistant to see, and export them in the right format with a single command.

## Features

- **Watch Mode**: Easily track changes to specific file patterns
- **Ignore System**: Git-style ignore patterns with full support for negation
- **Clipboard Integration**: One command to sync changes and export to clipboard
- **LLM-Optimized Output**: Markdown formatting with syntax highlighting by language
- **Cross-Platform**: Works on Linux, macOS, and Windows
- **Path Intelligence**: Handles symlinks, environment variables, and relative paths

## Installation

### Method 1: Install from PyPI (Recommended)

The easiest way to install (requires Python 3.12+):

```bash
pip install contextr
```

This makes the `ctxr` and `contextr` commands available globally.

### Method 2: Install from source

```bash
# Clone the repository
git clone https://github.com/your-username/contextr.git
cd contextr

# Option A: Use the automated installer script
python install.py

# Option B: Install in development mode
pip install -e .
```

### Installation notes

- **Windows users**: If using Method 2, you may need to add the Python Scripts directory to your PATH
- **macOS/Linux users**: The installer script will try to create symlinks in ~/.local/bin
- **First-time setup**: After installation, run `ctxr init` in your project directory to initialize contextr

## Quick Start

```bash
# Initialize contextr in your project
ctxr init

# Add files to watch (will be auto-monitored for changes)
ctxr watch "src/**/*.py" "docs/*.md"

# Ignore specific patterns
ctxr ignore "**/__pycache__/**"

# Sync changes from watched files and export to clipboard
ctxr sync

# That's it! Paste into your favorite LLM
```

## Core Commands

### Watch & Sync

- `watch <patterns>`: Add files to monitor
  ```bash
  ctxr watch "src/**/*.py" "*.md"
  ```

- `sync`: Refresh context & export to clipboard
  ```bash
  ctxr sync
  ```

- `watch-list`: Show currently watched patterns
  ```bash
  ctxr watch-list
  ```
  
- `unwatch <patterns>`: Stop watching patterns
  ```bash
  ctxr unwatch "src/tests/**"
  ```

### Ignore Management

- `ignore <pattern>`: Add pattern to ignore list
  ```bash
  ctxr ignore "**/*.log"
  ```

- `ignore-list`: Show ignored patterns
  ```bash
  ctxr ignore-list
  ```

- `unignore <pattern>`: Remove pattern from ignore list
  ```bash
  ctxr unignore "**/*.log"
  ```

- `gitignore-sync`: Sync patterns from .gitignore
  ```bash
  ctxr gitignore-sync
  ```

### Info & Setup

- `init`: Initialize ctxr in current directory
  ```bash
  ctxr init
  ```

- `list`: Display current context as tree
  ```bash
  ctxr list
  ```

- `version`: Show version information
  ```bash
  ctxr version
  ```

## Why Use contextr?

**For developers:**
- Save time by automating the selection of relevant code files
- Ensure you include all necessary context for LLMs to understand your codebase
- Avoid manually copying and pasting multiple files
- Focus on just what matters - watches only what you need

**For LLMs:**
- Proper markdown formatting with language-specific syntax highlighting
- Clean file structure visualization
- Consistent context representation

## Requirements

- Python >= 3.12

## License

MIT License