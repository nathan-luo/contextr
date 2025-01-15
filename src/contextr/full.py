# #!/usr/bin/env python3
# import os
# import sys
# import glob
# import json
# import pyperclip
# import typer
#
# from rich.tree import Tree
# from rich.console import Console
# from rich.table import Table
# from pathlib import Path
# from typing import List, Dict, Set
#
# app = typer.Typer(help="Context CLI - Manage files and export to clipboard")
# console = Console()
#
# VERSION = "0.1.1"
#
#
# class ContextManager:
#     """
#     Manages the current "context" of files and directories.
#
#     - Keeps track of individual files.
#     - Provides methods to add, remove, export, and display the file tree.
#     """
#
#     def __init__(self):
#         self.files: Set[str] = set()
#         self.base_dir = Path.cwd()
#         self.state_dir = self.base_dir / ".contextr"
#         self.state_file = self.state_dir / "state.json"
#         self._load_state()
#
#     def _make_relative(self, path: str) -> str:
#         """
#         Convert absolute path to relative path from base_dir, if possible.
#         Otherwise, return the absolute path.
#         """
#         try:
#             return str(Path(path).resolve().relative_to(self.base_dir))
#         except ValueError:
#             return str(Path(path).resolve())
#
#     def _make_absolute(self, path: str) -> str:
#         """
#         Convert relative path to absolute path from base_dir.
#         If already absolute, just resolve it.
#         """
#         if os.path.isabs(path):
#             return str(Path(path).resolve())
#         return str((self.base_dir / path).resolve())
#
#     def _normalize_paths(self, patterns: List[str]) -> List[str]:
#         """
#         Normalize and expand glob patterns to absolute paths.
#         If no file is found for a pattern, print a warning.
#         """
#         all_paths = []
#         for pattern in patterns:
#             abs_pattern = self._make_absolute(pattern)
#
#             if "*" in pattern or "?" in pattern:
#                 matched_files = glob.glob(abs_pattern, recursive=True)
#                 if matched_files:
#                     all_paths.extend(matched_files)
#                 else:
#                     console.print(
#                         f"[yellow]Warning:[/yellow] No matches for pattern: '{pattern}'"
#                     )
#             else:
#                 path_obj = Path(abs_pattern)
#                 if path_obj.exists():
#                     all_paths.append(str(path_obj))
#                 else:
#                     console.print(
#                         f"[yellow]Warning:[/yellow] Path does not exist: '{pattern}'"
#                     )
#         return all_paths
#
#     def _load_state(self) -> None:
#         """
#         Load state (files) from a JSON file if it exists.
#         """
#         if self.state_file.exists():
#             try:
#                 with open(self.state_file, "r", encoding="utf-8") as f:
#                     data = json.load(f)
#                 self.files = set(self._make_absolute(p) for p in data.get("files", []))
#             except Exception as e:
#                 console.print(f"[red]Error loading state: {e}[/red]")
#
#     def _save_state(self) -> None:
#         """
#         Save current state (files) to a JSON file.
#         """
#         self.state_dir.mkdir(parents=True, exist_ok=True)
#         try:
#             with open(self.state_file, "w", encoding="utf-8") as f:
#                 data = {
#                     "files": [
#                         self._make_relative(p) for p in sorted(self.files)
#                     ]
#                 }
#                 json.dump(data, f, indent=4)
#         except Exception as e:
#             console.print(f"[red]Error saving state: {e}[/red]")
#
#     def add_files(self, patterns: List[str]) -> None:
#         """
#         Add files or directories to the context.
#         If a directory is added, all files in it are also added.
#         """
#         abs_paths = self._normalize_paths(patterns)
#         if not abs_paths:
#             return
#
#         new_files_count = 0
#         for path_str in abs_paths:
#             p = Path(path_str)
#             if p.is_file():
#                 if path_str not in self.files:
#                     new_files_count += 1
#                 self.files.add(path_str)
#             elif p.is_dir():
#                 # Add all files within the directory
#                 for file_path in p.rglob("*"):
#                     if file_path.is_file():
#                         file_abs = str(file_path.resolve())
#                         if file_abs not in self.files:
#                             new_files_count += 1
#                         self.files.add(file_abs)
#
#         self._save_state()
#         console.print(
#             f"[green]Added [bold]{new_files_count}[/bold] files/directories to context.[/green]"
#         )
#
#     def remove_files(self, patterns: List[str]) -> None:
#         """
#         Remove files or directories from the context.
#         If a directory is removed, all files under it are also removed.
#         """
#         abs_paths = self._normalize_paths(patterns)
#         if not abs_paths:
#             return
#
#         files_to_remove = set()
#         for path_str in abs_paths:
#             p = Path(path_str)
#             if p.is_file():
#                 if path_str in self.files:
#                     files_to_remove.add(path_str)
#             elif p.is_dir():
#                 # Remove all files under that directory
#                 for file_path in p.rglob("*"):
#                     fp_str = str(file_path.resolve())
#                     if fp_str in self.files:
#                         files_to_remove.add(fp_str)
#
#         removed_count = len(files_to_remove)
#         self.files -= files_to_remove
#         self._save_state()
#
#         console.print(
#             f"[red]Removed [bold]{removed_count}[/bold] files/directories from context.[/red]"
#         )
#
#     def clear_context(self) -> None:
#         """
#         Clear all files from context.
#         """
#         self.files.clear()
#         self._save_state()
#         console.print("[yellow]Context cleared![/yellow]")
#
#     def get_file_tree(self) -> Tree:
#         """
#         Generate a Rich Tree representation of the current context files.
#         """
#         tree = Tree("📁 [bold]Context[/bold]")
#         dir_groups: Dict[str, List[str]] = {}
#
#         # Group files by their parent directories
#         for file_path in sorted(self.files):
#             rel_path = self._make_relative(file_path)
#             parent_dir = str(Path(rel_path).parent)
#             dir_groups.setdefault(parent_dir, []).append(os.path.basename(rel_path))
#
#         # Build a nested tree
#         for dir_path, files in sorted(dir_groups.items()):
#             current_node = tree
#             if dir_path != ".":
#                 for part in Path(dir_path).parts:
#                     found = False
#                     for node in current_node.children:
#                         # Remove the "📁 " from node label for matching
#                         label_stripped = node.label.replace("📁 ", "")
#                         if label_stripped == part:
#                             current_node = node
#                             found = True
#                             break
#                     if not found:
#                         current_node = current_node.add(f"📁 {part}")
#
#             for f in sorted(files):
#                 current_node.add(f"📄 {f}")
#
#         return tree
#
#     def export_to_clipboard(self, relative: bool = True, include_contents: bool = False) -> None:
#         """
#         Export context information to the clipboard in a plain text format optimized for LLM parsing:
#
#         <file_tree>
#         📁 Root
#         └── 📄 file1.txt
#         └── 📄 file2.txt
#         </file_tree>
#
#         <file path="file1.txt">
#         <contents if include_contents is True>
#         </file>
#
#         <file path="file2.txt">
#         <contents if include_contents is True>
#         </file>
#         """
#         if not self.files:
#             console.print("[red]No files in context to export![/red]")
#             return
#
#         # Get the tree structure as text
#         temp_console = Console(record=True)
#         temp_console.print(self.get_file_tree())
#         tree_text = temp_console.export_text()
#
#         # Start with tree wrapped in XML-like tags
#         output_text = [
#             "<file_tree>",
#             tree_text.strip(),
#             "</file_tree>",
#             ""  # Empty line after tree
#         ]
#
#         # Add file contents if requested
#         if include_contents:
#             for fpath in sorted(self.files):
#                 if relative:
#                     path_str = self._make_relative(fpath)
#                 else:
#                     path_str = fpath
#
#                 # Add file header
#                 output_text.append(f'<file path="{path_str}">')
#
#                 # Try to read and add file contents
#                 try:
#                     with open(fpath, "r", encoding="utf-8") as f:
#                         output_text.append(f.read())
#                 except Exception as e:
#                     output_text.append(f"<Unable to read file: {fpath}> (Error: {e})")
#
#                 # Add file footer and spacing
#                 output_text.extend([
#                     "</file>",
#                     ""  # Empty line between files
#                 ])
#
#         # Join all parts with newlines and copy to clipboard
#         final_output = "\n".join(output_text)
#         pyperclip.copy(final_output)
#
#         console.print(
#             f"[green]Exported {len(self.files)} files to clipboard "
#             f"{'with contents' if include_contents else '(paths only)'}![/green]"
#         )
#
# # Global context manager
# context_manager = ContextManager()
#
#
# @app.command()
# def add(patterns: List[str] = typer.Argument(..., help="File patterns to add (supports glob)")):
#     """
#     Add files/directories to the context.
#     """
#     context_manager.add_files(patterns)
#     console.print(context_manager.get_file_tree())
#
#
# @app.command()
# def remove(patterns: List[str] = typer.Argument(..., help="File patterns to remove (supports glob)")):
#     """
#     Remove files/directories from the context.
#     """
#     context_manager.remove_files(patterns)
#     console.print(context_manager.get_file_tree())
#
#
# @app.command()
# def clear():
#     """
#     Clear all files from the context.
#     """
#     context_manager.clear_context()
#
#
# @app.command(name="list")
# def list_command():
#     """
#     List all files in the context (in a tree view).
#     """
#     console.print(context_manager.get_file_tree())
#
#
# @app.command()
# def export(
#         relative: bool = typer.Option(True, help="Export relative paths instead of absolute"),
#         full: bool = typer.Option(True, help="Include file contents in the export"),
# ):
#     """
#     Export the current context to the clipboard.
#
#     By default, exports only the file paths (relative).
#     Use `--full` to also include the content of each file.
#     """
#     context_manager.export_to_clipboard(relative=relative, include_contents=full)
#
#
# @app.command()
# def search(keyword: str):
#     """
#     Search for files in the context containing the given keyword in their path.
#     """
#     matches = [
#         context_manager._make_relative(f)
#         for f in context_manager.files
#         if keyword.lower() in f.lower()
#     ]
#
#     if matches:
#         table = Table("Matched Files", style="bold green")
#         for m in sorted(matches):
#             table.add_row(m)
#         console.print(table)
#     else:
#         console.print(f"[red]No files in context match keyword: '{keyword}'[/red]")
#
#
# @app.command()
# def version():
#     """
#     Print version information.
#     """
#     console.print(f"[bold green]Context CLI v{VERSION}[/bold green]")
#
#
# def main():
#     """
#     Entrypoint for the CLI.
#     """
#     app()
#
#
# if __name__ == "__main__":
#     main()
