import os
from pathlib import Path
from typing import Set, Dict, List
from rich.tree import Tree
from rich.console import Console

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

def format_export_content(
        files: Set[str],
        base_dir: Path,
        relative: bool = True,
        include_contents: bool = False
) -> str:
    """
    Format context information for export.

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

    # Start with tree wrapped in XML-like tags
    output_parts = [
        "<file_tree>",
        tree_text.strip(),
        "</file_tree>",
        ""  # Empty line after tree
    ]

    # Add file contents if requested
    if include_contents:
        for fpath in sorted(files):
            if relative:
                path_str = str(Path(fpath).resolve().relative_to(base_dir))
            else:
                path_str = fpath

            # Add file header
            output_parts.append(f'<file path="{path_str}">')

            # Try to read and add file contents
            try:
                with open(fpath, "r", encoding="utf-8") as f:
                    output_parts.append(f.read())
            except Exception as e:
                output_parts.append(f"<Unable to read file: {fpath}> (Error: {e})")

            # Add file footer and spacing
            output_parts.extend([
                "</file>",
                ""  # Empty line between files
            ])

    return "\n".join(output_parts)