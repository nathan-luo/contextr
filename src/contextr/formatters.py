import os
from pathlib import Path
from typing import Dict, List, Set, Tuple

from rich.console import Console
from rich.tree import Tree


def get_file_tree(files: Set[str], base_dir: Path) -> Tree:
    """
    Generate a Rich Tree representation of the current context files.

    Args:
        files: Set of absolute file paths
        base_dir: Base directory for making paths relative

    Returns:
        Tree: Rich Tree object representing the file hierarchy
    """
    tree = Tree("📁 [bold]Context[/bold]")
    dir_groups: Dict[str, List[str]] = {}

    # Group files by their parent directories
    for file_path in sorted(files):
        try:
            rel_path = str(Path(file_path).resolve().relative_to(base_dir))
            parent_dir = str(Path(rel_path).parent)
            dir_groups.setdefault(parent_dir, []).append(os.path.basename(rel_path))
        except ValueError:
            # For files outside base_dir, use absolute path
            abs_path = str(Path(file_path).resolve())
            dir_groups.setdefault(str(Path(abs_path).parent), []).append(
                os.path.basename(abs_path)
            )

    # Build a nested tree
    for dir_path, file_list in sorted(dir_groups.items()):
        current_node = tree
        if dir_path != ".":
            for part in Path(dir_path).parts:
                found = False
                for node in current_node.children:
                    # Remove the "📁 " from node label for matching
                    label_stripped = str(node.label).replace("📁 ", "")
                    if label_stripped == part:
                        current_node = node
                        found = True
                        break
                if not found:
                    current_node = current_node.add(f"📁 {part}")

        for f in sorted(file_list):
            current_node.add(f"📄 {f}")

    return tree


def detect_language(file_path: str) -> str:
    """
    Detect programming language from file extension.

    Args:
        file_path: Path to the file

    Returns:
        str: Language name for syntax highlighting
    """
    ext = os.path.splitext(file_path)[1].lower()

    # Map of file extensions to language names
    lang_map = {
        ".py": "python",
        ".js": "javascript",
        ".ts": "typescript",
        ".jsx": "jsx",
        ".tsx": "tsx",
        ".html": "html",
        ".css": "css",
        ".json": "json",
        ".md": "markdown",
        ".sql": "sql",
        ".c": "c",
        ".cpp": "cpp",
        ".h": "c",
        ".hpp": "cpp",
        ".rs": "rust",
        ".go": "go",
        ".java": "java",
        ".rb": "ruby",
        ".php": "php",
        ".sh": "bash",
        ".yaml": "yaml",
        ".yml": "yaml",
        ".toml": "toml",
        ".ini": "ini",
        ".env": "properties",
        ".bat": "batch",
        ".ps1": "powershell",
    }

    return lang_map.get(ext, "text")


def _choose_fence(text: str, base: str = "```") -> str:
    """Choose a fence sequence not present in text."""
    fence = base
    while fence in text:
        fence += "`"
    return fence


def _read_text(path: str, max_bytes: int = 512_000) -> Tuple[str, bool]:
    """
    Read up to max_bytes from file as UTF-8 (replace errors).
    Returns (content, truncated).
    """
    try:
        with open(path, "rb") as fb:
            raw = fb.read(max_bytes + 1)
        truncated = len(raw) > max_bytes
        content = raw[:max_bytes].decode("utf-8", errors="replace")
        return content, truncated
    except Exception as e:
        return f"[ERROR: Unable to read file: {e}]", False


def format_export_content(
    files: Set[str],
    base_dir: Path,
    relative: bool = True,
    include_contents: bool = True,
    max_bytes: int = 512_000,
) -> str:
    """
    Format context information for export.
    Generates an LLM-friendly format with file tree and contents.

    Args:
        files: Set of absolute file paths
        base_dir: Base directory for making paths relative
        relative: Whether to use relative paths in output
        include_contents: Whether to include file contents

    Returns:
        str: Formatted export content
    """
    # Create temporary console for capturing tree output
    temp_console = Console(record=True)
    temp_console.print(get_file_tree(files, base_dir))
    tree_text = temp_console.export_text()

    # Format header with project info
    repo_name = base_dir.name
    total_files = len(files)

    output_parts = [
        f"# Project Context: {repo_name}",
        f"Files selected: {total_files}",
        "",
        "## File Structure",
        "```",
        tree_text.strip(),
        "```",
        "",
    ]

    # Add file contents if requested
    if include_contents:
        output_parts.append("## File Contents")

        for fpath in sorted(files):
            if relative:
                try:
                    path_str = str(Path(fpath).resolve().relative_to(base_dir))
                except ValueError:
                    path_str = str(Path(fpath).resolve())
            else:
                path_str = fpath

            # Detect language for syntax highlighting
            lang = detect_language(path_str)

            output_parts.append(f"\n### {path_str}")
            content, truncated = _read_text(fpath, max_bytes=max_bytes)
            fence = _choose_fence(content, base="```")
            output_parts.append(f"{fence}{lang}")
            output_parts.append(content)
            if truncated:
                output_parts.append("\n[... truncated ...]")
            output_parts.append(f"{fence}")

    return "\n".join(output_parts)
