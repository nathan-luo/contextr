"""Tests for ordered git-like ignore semantics."""

from pathlib import Path

from contextr.utils.ignore_utils import IgnoreManager


def test_ignore_order_last_match_wins(tmp_path: Path) -> None:
    base = tmp_path
    im = IgnoreManager(base)
    # Clear any pre-existing rules
    im.clear_patterns()

    # Create a fake structure
    keep_x = base / "node_modules" / "keep" / "x.js"
    keep_tmp = base / "node_modules" / "keep" / "tmp.tmp"
    drop_y = base / "node_modules" / "drop" / "y.js"
    for p in [keep_x, keep_tmp, drop_y]:
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text("// test", encoding="utf-8")

    # Rules: ignore node_modules, un-ignore keep/, then re-ignore *.tmp in keep/
    im.add_pattern("node_modules/")
    im.add_pattern("!node_modules/keep/")
    im.add_pattern("node_modules/keep/*.tmp")

    assert im.should_ignore(str(drop_y)) is True
    assert im.should_ignore(str(keep_x)) is False
    assert im.should_ignore(str(keep_tmp)) is True


def test_ignore_order_sensitivity(tmp_path: Path) -> None:
    base = tmp_path
    im = IgnoreManager(base)
    im.clear_patterns()

    file_a = base / "build" / "out.txt"
    file_a.parent.mkdir(parents=True, exist_ok=True)
    file_a.write_text("x", encoding="utf-8")

    # First allow, then ignore => last wins => ignored
    im.add_pattern("!build/")
    im.add_pattern("build/")
    assert im.should_ignore(str(file_a)) is True
