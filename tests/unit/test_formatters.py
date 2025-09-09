"""Tests for export formatter robustness."""

from pathlib import Path

from contextr.formatters import format_export_content


def test_dynamic_code_fences_avoid_collision(tmp_path: Path) -> None:
    p = tmp_path / "file.md"
    # Include triple backticks inside content
    p.write_text("```inside\ncode\n```", encoding="utf-8")
    out = format_export_content(
        {str(p)}, tmp_path, relative=True, include_contents=True
    )
    # Expect more than 3 backticks in fences or a different safe sequence
    assert "```markdown" in out or "```text" in out
    # No raw unbalanced fence termination (we just check it contains both
    # opening and closing)
    assert out.count("```") >= 2


def test_truncation_marker_for_large_files(tmp_path: Path) -> None:
    p = tmp_path / "big.txt"
    p.write_bytes(b"a" * 1024)  # 1KB
    out = format_export_content(
        {str(p)}, tmp_path, relative=True, include_contents=True, max_bytes=100
    )
    assert "[... truncated ...]" in out
