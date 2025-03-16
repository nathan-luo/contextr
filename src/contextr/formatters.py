import os
from pathlib import Path
from typing import Set, Dict, List
import re
from rich.tree import Tree
from rich.console import Console
from rich.syntax import Syntax


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
    for dir_path, files in sorted(dir_groups.items()):
        current_node = tree
        if dir_path != ".":
            for part in Path(dir_path).parts:
                found = False
                for node in current_node.children:
                    # Remove the "📁 " from node label for matching
                    label_stripped = node.label.replace("📁 ", "")
                    if label_stripped == part:
                        current_node = node
                        found = True
                        break
                if not found:
                    current_node = current_node.add(f"📁 {part}")

        for f in sorted(files):
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
        '.py': 'python',
        '.js': 'javascript',
        '.ts': 'typescript',
        '.jsx': 'jsx',
        '.tsx': 'tsx',
        '.html': 'html',
        '.css': 'css',
        '.json': 'json',
        '.md': 'markdown',
        '.sql': 'sql',
        '.c': 'c',
        '.cpp': 'cpp',
        '.h': 'c',
        '.hpp': 'cpp',
        '.rs': 'rust',
        '.go': 'go',
        '.java': 'java',
        '.rb': 'ruby',
        '.php': 'php',
        '.sh': 'bash',
        '.yaml': 'yaml',
        '.yml': 'yaml',
        '.toml': 'toml',
    }
    
    return lang_map.get(ext, 'text')


def format_export_content(
        files: Set[str],
        base_dir: Path,
        relative: bool = True,
        include_contents: bool = True
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
        ""
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
            
            # Add file header with language
            output_parts.append(f"\n### {path_str}")
            output_parts.append(f"```{lang}")

            # Try to read and add file contents
            try:
                with open(fpath, "r", encoding="utf-8") as f:
                    content = f.read()
                    # Remove any potential backtick confusion by escaping triple backticks
                    # This ensures code blocks terminate properly in markdown
                    content = re.sub(r'```', '\\`\\`\\`', content)
                    output_parts.append(content)
            except Exception as e:
                output_parts.append(f"[ERROR: Unable to read file: {e}]")

            # Close code block
            output_parts.append("```")

    return "\n".join(output_parts)