# contextr

A command-line tool designed for developers to easily share their codebase with Large Language Models (LLMs). contextr
helps you manage which files and directories you want to share, handles file content export, and lets you instantly copy
formatted code context to your clipboard - perfect for pasting into ChatGPT, Claude, or other AI chat interfaces.

Think of it as "git add" but for AI conversations - select the files you want your AI assistant to see, and export them
in the right format with a single command.

## Installation

1. Clone the repository:

```bash
git clone https://github.com/your-username/contextr.git
cd contextr
```

2. Install in development mode:

```bash
pip install -e .
```

3. Add to PATH:

- For Linux/Mac: Add to `~/.bashrc` or `~/.zshrc`:
  ```bash
  export PATH="$PATH:$HOME/.local/bin"
  ```
- For Windows: Add `%USERPROFILE%\AppData\Local\Programs\Python\Python3x\Scripts` to system PATH

## Quick Start

> Note: You can use `ctxr` as a shorter alias for all `contextr` commands.

1. Initialize contextr in your project:

```bash
contextr init
```

2. Add files to track:

```bash
contextr add "src/**/*.py"
```

3. Export your context:

```bash
contextr export
```

## Commands

### Context Management

- `init`: Initialize contextr in current directory
  ```bash
  contextr init
  ```

- `add <patterns>`: Add files/directories to context
  ```bash
  contextr add "src/*.py" "docs/*.md"
  ```

- `remove <patterns>`: Remove files from context
  ```bash
  contextr remove "tests/*.py"
  ```

- `list`: Display current context as tree
  ```bash
  contextr list
  ```

- `clear`: Remove all files from context
  ```bash
  contextr clear
  ```

- `search <keyword>`: Find files in context
  ```bash
  contextr search "config"
  ```

### Watch Mode

- `watch <patterns>`: Add paths to watch list
  ```bash
  contextr watch "src/**/*.py"
  ```

- `unwatch <patterns>`: Stop watching paths
  ```bash
  contextr unwatch "src/tests"
  ```

- `watch-list`: Show watched patterns
  ```bash
  contextr watch-list
  ```

- `refresh`: Update context from watched paths
  ```bash
  contextr refresh
  ```

### Ignore Management

- `ignore <pattern>`: Add pattern to ignore list
  ```bash
  contextr ignore "*.tmp"
  ```

- `unignore <pattern>`: Remove pattern from ignore list
  ```bash
  contextr unignore "*.tmp"
  ```

- `ignore-list`: Show ignored patterns
  ```bash
  contextr ignore-list
  ```

- `gitignore-sync`: Sync patterns from .gitignore
  ```bash
  contextr gitignore-sync
  ```

### Export

- `export`: Export context to clipboard
  ```bash
  contextr export --relative --full
  ```

- `rexp`: Refresh watched paths and export
  ```bash
  contextr rexp --relative --full
  ```

### State Management

- `save-as <name>`: Save current context state
  ```bash
  contextr save-as dev-setup
  ```

- `load <name>`: Load saved context state
  ```bash
  contextr load dev-setup
  ```

- `states`: List saved states
  ```bash
  contextr states
  ```

- `delete-state <name>`: Delete saved state
  ```bash
  contextr delete-state old-setup
  ```

## Example Workflow

```bash
# Initialize in project (using either command)
contextr init
# or
ctxr init

# Add source files to watch
ctxr watch "src/**/*.py"

# Add documentation
contextr add "docs/*.md"

# Check current context
contextr list

# Export for sharing
contextr export --full

# Save the state
contextr save-as feature-setup

# Later, restore the state
contextr load feature-setup
```

## Features

- File tree visualization
- Clipboard integration
- Git-style ignore patterns
- Watch mode for auto-updates
- State management
- Relative/absolute path support

## Requirements

- Python >= 3.12

## License

MIT License