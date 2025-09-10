# contextr (ctxr)
> **"git add for AI conversations."** Select the files you want an LLM to "see," format them beautifully, and get them onto your clipboard—or into a file—in one command.

`contextr` is a command‑line tool for preparing and sharing **code context** with Large Language Models (LLMs) such as ChatGPT, Claude, etc. It watches the files you care about, respects git‑style ignore rules, and exports a clean, LLM‑friendly Markdown bundle with a file tree and (optionally) file contents.

- 🧭 **Focused Context** — watch only what matters using familiar glob patterns.
- 🚫 **Git‑style Ignores** — last‑match‑wins semantics, `!` negations, `**` globs, bare directory names.
- 📋 **One‑shot Export** — copy straight to clipboard or write to a file.
- 🧩 **Profiles** — branch‑like saved watch patterns you can load/checkout instantly.
- 🎛️ **Production‑ready CLI** — predictable flags, useful status, cross‑platform paths.
- 🧪 **Typed & Tested** — strict typing with Pyright and a comprehensive test suite.

---

## Table of Contents
1. [Installation](#installation)
2. [Quick Start](#quick-start)
3. [CLI Reference](#cli-reference)
   - [Core](#core)
   - [Ignore Rules](#ignore-rules)
   - [Profiles](#profiles)
4. [Output Format](#output-format)
5. [Ignore Semantics (Git‑style)](#ignore-semantics-gitstyle)
6. [Profiles Explained](#profiles-explained)
7. [Python API](#python-api)
8. [Troubleshooting](#troubleshooting)
9. [Security & Privacy](#security--privacy)
10. [Development](#development)
11. [FAQ](#faq)
12. [License](#license)

---

## Installation

> Requires **Python 3.12+**

### Option A — PyPI (recommended)
```bash
pip install contextr
```

This installs both commands: `ctxr` (short) and `contextr` (full).

### Option B — From source

```bash
git clone https://github.com/nathan-luo/contextr.git
cd contextr

# For development (uses uv)
uv sync --extra dev

# Or editable install with pip
pip install -e .
```

> **Note (Linux):** Clipboard features rely on `pyperclip`. On some systems you may need a clipboard helper such as `xclip` or `xsel`.

---

## Quick Start

```bash
# 1) Initialize (creates .contextr/ in your repo)
ctxr init

# 2) Watch what matters (glob patterns welcome)
ctxr watch "src/**/*.py" "docs/*.md" "*.toml"

# 3) Ignore noise (git‑style rules)
ctxr ignore "**/__pycache__/**" "*.pyc" "node_modules/"

# Optionally import your .gitignore
ctxr gis   # (alias: gitignore-sync)

# 4) Export (clipboard by default)
ctxr sync

# Paste into ChatGPT/Claude and start collaborating.
```

Want a file instead of the clipboard?

```bash
ctxr sync --to-file context.md
```

Prefer absolute paths and only the file tree (no contents)?

```bash
ctxr sync --absolute --no-contents --to-file tree.md
```

Check what's tracked:

```bash
ctxr list         # file tree
ctxr watch-list   # watched patterns
ctxr ignore-list  # ignored patterns
ctxr status       # profile, counts, dirty marker
```

---

## CLI Reference

All commands are available via **`ctxr`** (preferred) or **`contextr`**.

### Core

#### `init`

Initialize `.contextr/` in the current directory.

```bash
ctxr init
```

> We **no longer auto‑add** `.contextr/` to `.gitignore` so teams can sync state/profiles if they want. Add it manually if you prefer to keep it untracked.

#### `watch <patterns...>`

Add one or more patterns to the watch list and immediately add matching files.

```bash
ctxr watch "src/**/*.py" "*.md"
```

Patterns are kept as‑is (even if currently matching zero files). Ignores are applied per‑file, not per‑pattern.

#### `unwatch <patterns...>`

Remove patterns from the watch list. Files that are no longer matched by any remaining pattern are removed from the context.

```bash
ctxr unwatch "tests/**"
```

#### `watch-list`

Show watched patterns (sorted).

```bash
ctxr watch-list
```

#### `list`

Print a Rich tree of all files currently in the context.

```bash
ctxr list
```

#### `sync`

Refresh files from watched patterns (respecting ignores) and export.

```bash
ctxr sync
# Options:
#   -o, --to-file PATH   Write export to a file
#       --no-clipboard   Skip copying to clipboard
#       --absolute       Use absolute paths in headings
#       --no-contents    Only include the file tree (no file contents)
```

If the clipboard fails (e.g., no clipboard backend), ctxr prints the output to stdout unless you used `--to-file`.

#### `status`

Show current profile and counts, including an asterisk on the profile name if there are **unsaved** changes to watched patterns.

```bash
ctxr status
```

#### `version`

```bash
ctxr version
```

### Ignore Rules

#### `ignore <patterns...>`

Append patterns to `.contextr/.ignore` (order matters; last match wins).

```bash
ctxr ignore "**/*.log" "build/" "!build/keep/"
```

#### `unignore <patterns...>`

Remove rules from `.contextr/.ignore`.

```bash
ctxr unignore "**/*.log"
```

#### `ignore-list`

List ignore rules in file order, including `!` negations.

```bash
ctxr ignore-list
```

#### `gis` (alias: `gitignore-sync`)

Import rules from `.gitignore` into `.contextr/.ignore`.

```bash
ctxr gis
```

> `gitignore-sync` still works but is **deprecated** in favor of `gis`.

### Profiles

Profiles are **branch‑like**: they capture only your **watched patterns** and metadata. Repo‑level ignores remain in `.contextr/.ignore` and **do not** live inside a profile.

#### `profile save [NAME] [--description TEXT] [--force]`

Save the current watched patterns as a named profile. If `NAME` is omitted, the current profile is updated (when one is loaded).

```bash
ctxr profile save backend --description "Backend API dev"
```

#### `profile list`

List saved profiles in a table. If a profile is loaded, it's shown above the table, with `*` if there are unsaved changes.

```bash
ctxr profile list
```

#### `profile load <NAME>`

Load a profile's watched patterns and apply them to the current context.

```bash
ctxr profile load backend
```

#### `profile checkout <NAME>`

Friendly alias for `profile load`.

```bash
ctxr profile checkout backend
```

#### `profile show <NAME>`

Display metadata and a preview of the first few patterns.

```bash
ctxr profile show backend
```

#### `profile delete <NAME> [--force]`

Delete a profile (prompts unless `--force`).

```bash
ctxr profile delete backend --force
```

#### `profile new --name NAME [--description TEXT]`

Interactive creation flow that clears the current context (preserving ignores), lets you enter patterns line‑by‑line, and then saves the profile.

```bash
ctxr profile new --name frontend --description "Web UI"
# You'll be prompted to enter patterns (blank line to finish)
```

---

## Output Format

By default, `sync` produces a single Markdown blob ideal for LLMs:

* A **header** with repo name and number of files.
* A **file tree** rendered as plain text (generated via Rich).
* An optional **File Contents** section with headings per file:

  * Headings show relative paths (or absolute with `--absolute`).
  * Contents are fenced with a language hint derived from the file extension.
  * If a file is large, content is truncated and marked with `[... truncated ...]`.
  * Fences are dynamically chosen to avoid accidental closing due to backticks in your code.

Example (abbreviated):

````markdown
# Project Context: your-project
Files selected: 5

## File Structure
```
📁 Context
├── src
│   ├── main.py
│   └── utils
│       └── helpers.py
└── README.md
```

## File Contents

### src/main.py
```python
# ...
```
````

---

## Ignore Semantics (Git‑style)

`contextr` implements **git‑style** semantics with ordered rules and "**last match wins**". Highlights:

- **Negation with `!`** re‑includes paths previously ignored.
- **Bare directory names** (e.g., `node_modules`) ignore the whole subtree (like `node_modules/`).
- `**/` matches **zero or more directories** (so `a/**/b` matches both `a/b` and `a/x/y/b`).
- Leading `/` anchors to the repo root (`/build` = only top‑level `build`).
- Trailing `/` denotes a directory rule (but bare names still affect descendants).
- Case‑insensitive match on Windows and macOS; case‑sensitive on Linux.

Examples:
```text
# Ignore everything under node_modules, but keep node_modules/keep/
node_modules
!node_modules/keep/

# Ignore tests anywhere
**/test_*.py

# Keep a specific file that would otherwise be ignored
!src/generated/keep_this.py
```

> Patterns live in `.contextr/.ignore`. Comments (`# ...`) and blank lines are supported. Inline comments like `pattern  # note` are handled when importing from `.gitignore` via `ctxr gis`.

---

## Profiles Explained

Profiles are **just watched patterns + metadata**—no ignore rules. This makes them easy to share without accidentally overriding a team's repo‑level ignore policy.

Typical workflow:

```bash
# Backend profile
ctxr watch "src/**/*.py" "migrations/**/*.sql"
ctxr ignore "tests/**" "*.pyc"
ctxr profile save backend --description "Backend dev"

# Switch to frontend
ctxr profile new --name frontend
# (enter patterns interactively, e.g., "web/**", "*.tsx", etc.)

# Jump between them
ctxr profile checkout backend
ctxr profile checkout frontend

# Inspect or clean up
ctxr profile show backend
ctxr profile delete frontend --force
```

The **dirty** marker (`*`) appears on the current profile in `ctxr status` when your watched patterns differ from what's stored. Use `ctxr profile save` to update.

---

## Python API

You can also use `contextr` programmatically:

```python
from pathlib import Path
from contextr import ContextManager, ProfileManager, format_export_content

base = Path.cwd()
cm = ContextManager()  # uses .contextr/ in base
cm.watch_paths(["src/**/*.py", "*.md"])
cm.add_ignore_patterns(["**/__pycache__/**", "*.pyc"])

# Refresh and format
cm.refresh_watched()
text = format_export_content(
    files=cm.files,
    base_dir=cm.base_dir,
    relative=True,
    include_contents=True,   # set False for tree only
    # max_bytes=512_000,     # per-file cap for contents (default)
)

# Save or copy yourself
(Path("context.md")).write_text(text, encoding="utf-8")

# Profiles
pm = ProfileManager(cm.storage, cm.base_dir)
pm.save_profile("python", watched_patterns=list(cm.watched_patterns))
profile = pm.load_profile("python")
cm.apply_profile(profile, "python")
```

---

## Troubleshooting

**Clipboard doesn't work**

* On Linux, install a clipboard helper such as `xclip` or `xsel`.
* Use `--to-file out.md` and/or `--no-clipboard` to bypass clipboard copy.
* If clipboard fails during `sync`, ctxr prints the output to stdout when not writing to file.

**Glob quoting on shells**

* Quote patterns to prevent shell expansion:

  * ✅ `ctxr watch "src/**/*.py"`
  * ❌ `ctxr watch src/**/*.py`

**Absolute vs relative paths**

* Exports use relative paths by default. Use `--absolute` if your workflow benefits from explicit, machine‑resolvable paths.

**Where is state stored?**

* `.contextr/state.json` for current state and watched patterns.
* `.contextr/.ignore` for ignore rules.
* Profiles are stored in `.contextr/profiles/`.

---

## Security & Privacy

`contextr` does **not** upload your files anywhere. It:

* Reads files locally,
* Formats them into Markdown,
* Copies to your clipboard and/or writes to a local file.

You are in control of what gets included (via **watch** and **ignore** rules).

---

## Development

* Python: **3.12+**
* Install dev deps:

  ```bash
  uv sync --extra dev
  ```
* Pre‑commit:

  ```bash
  uv run pre-commit install
  uv run pre-commit run --all-files
  ```
* Lint & format:

  ```bash
  uv run ruff check .
  uv run ruff format .
  ```
* Type check:

  ```bash
  uv run pyright
  ```
* Tests & coverage:

  ```bash
  uv run pytest
  # with coverage (configured in pyproject.toml):
  # --cov=src/contextr --cov-report=html --cov-report=term
  ```

Release process is documented in [`RELEASE.md`](./RELEASE.md).

---

## FAQ

**Q: What's the difference between `unwatch` and `ignore`?**

* `unwatch` removes a pattern from the **watch list** (so files matching only that pattern drop out of the context).
* `ignore` adds a rule that filters files **globally**, regardless of what you watch (you can re‑include with `!`).

**Q: Can I export only the file tree?**
Yes: `ctxr sync --no-contents --to-file tree.md`.

**Q: How are languages detected for code fences?**
By file extension (common languages like Python, JS/TS, HTML/CSS, JSON, YAML, TOML, etc.). Unknown extensions fall back to `text`.

**Q: Will long files break Markdown fences?**
No—fences are chosen dynamically to avoid collisions with backticks inside your files.

---

## License

MIT