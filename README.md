# contextr

contextr is a command-line tool designed to manage and export file contexts efficiently. It provides a simple interface
for working with files and directories, allowing users to add, remove, list, search, and export file structures with
ease. contextr also integrates with `.gitignore` to avoid managing unnecessary files and supports customizable ignore
patterns.

---

## Features

- **Add or Remove Files and Directories**: Manage a list of files or directories with support for glob patterns.
- **Export Context**: Export the file context as a tree view or include file contents directly.
- **Ignore Management**: Define custom ignore patterns or sync with `.gitignore`.
- **Tree Visualization**: View the file hierarchy in a visually appealing format using `rich`.
- **Clipboard Integration**: Copy the exported context directly to the clipboard.

---

## Installation

### Prerequisites

- Python >= 3.12

### Using `pip`

```bash
pip install contextr
```

### From Source

1. Clone the repository:

   ```bash
   git clone https://github.com/your-username/contextr.git
   cd contextr
   ```

2. Install the dependencies:

   ```bash
   pip install .
   ```

---

## Usage

contextr uses a command-line interface powered by `typer`. Below are examples of common commands:

### Initialize

```bash
contextr init
```

Creates the `.contextr` directory and updates `.gitignore` to ignore it.

### Add Files

```bash
contextr add "src/**/*.py"
```

Adds all Python files in the `src` directory and its subdirectories to the context.

### List Context

```bash
contextr list
```

Displays the current file context as a tree view.

### Export Context

```bash
contextr export --relative --full
```

Exports the context to the clipboard, including file contents and using relative paths.

### Manage Ignore Patterns

- Add a pattern to `.ignore`:

  ```bash
  contextr ignore "*.tmp"
  ```

- Remove a pattern from `.ignore`:

  ```bash
  contextr unignore "*.tmp"
  ```

- Sync patterns from `.gitignore`:

  ```bash
  contextr gitignore-sync
  ```

### Clear Context

```bash
contextr clear
```

Clears all files from the context.

### Search Context

```bash
contextr search "keyword"
```

Searches for files in the context containing the specified keyword in their paths.

### Version

```bash
contextr version
```

Displays the current version of contextr.

---

## Configuration

contextr maintains its state in a `.contextr` directory in the root of your project. The `.ignore` file inside
`.contextr` allows you to define patterns for excluding files or directories.

---

## Development

1. Install development dependencies:

   ```bash
   pip install -r requirements-dev.txt
   ```

2. Run tests:

   ```bash
   pytest
   ```

---

## Roadmap

- Support for additional export formats (JSON, YAML, Markdown).
- Interactive CLI mode for context management.
- Integration with cloud storage for exporting contexts.

---

## Contributing

Contributions are welcome! To contribute:

1. Fork the repository.
2. Create a feature branch.
3. Submit a pull request with a detailed description of your changes.

---

## License

This project is licensed under the MIT License. See the `LICENSE` file for details.

---

## Acknowledgments

- Built with love using `typer`, `rich`, and `pyperclip`.

---

Start managing your file contexts today with contextr!

