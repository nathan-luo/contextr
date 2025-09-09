"""Tests for CLI sync command options and fallbacks."""

from pathlib import Path
from unittest.mock import patch

from typer.testing import CliRunner

from contextr.cli import app


def test_sync_writes_file_and_handles_clipboard_failure(tmp_path: Path) -> None:
    runner = CliRunner()
    sample = tmp_path / "a.txt"
    sample.write_text("hello", encoding="utf-8")
    out_file = tmp_path / "out.md"

    with (
        patch("contextr.cli.context_manager") as mock_cm,
        patch("contextr.cli.pyperclip.copy", side_effect=Exception("no clipboard")),
    ):
        mock_cm.base_dir = tmp_path
        mock_cm.files = {str(sample)}
        mock_cm.refresh_watched.return_value = {"added": 0, "removed": 0}

        result = runner.invoke(app, ["sync", "--to-file", str(out_file)])

        assert result.exit_code == 0
        assert "Saved export to" in result.stdout
        assert "Clipboard failed" in result.stdout
        assert out_file.exists()
        assert out_file.read_text(encoding="utf-8").startswith("# Project Context")


def test_sync_no_clipboard_absolute_paths(tmp_path: Path) -> None:
    runner = CliRunner()
    sample = tmp_path / "a.txt"
    sample.write_text("x", encoding="utf-8")
    out_file = tmp_path / "out.md"

    with (
        patch("contextr.cli.context_manager") as mock_cm,
        patch("contextr.cli.pyperclip.copy") as mock_copy,
    ):
        mock_cm.base_dir = tmp_path
        mock_cm.files = {str(sample)}
        mock_cm.refresh_watched.return_value = {"added": 0, "removed": 0}

        result = runner.invoke(
            app,
            [
                "sync",
                "--to-file",
                str(out_file),
                "--no-clipboard",
                "--absolute",
            ],
        )

        assert result.exit_code == 0
        mock_copy.assert_not_called()
        content = out_file.read_text(encoding="utf-8")
        # Absolute path should appear in the "File Contents" section header
        assert f"### {str(sample)}" in content
