"""Extra tests for gitignore-style behavior."""

from pathlib import Path

from contextr.utils.ignore_utils import IgnoreManager


def test_double_star_zero_or_more_dirs(tmp_path: Path) -> None:
    """
    '**/' should match zero or more directories:
      - 'a/**/b' must match 'a/b' and 'a/x/y/b'
    """
    base = tmp_path
    im = IgnoreManager(base)
    im.clear_patterns()
    im.add_pattern("a/**/b")

    path1 = base / "a" / "b"
    path2 = base / "a" / "x" / "y" / "b"
    for p in (path1, path2):
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text("x", encoding="utf-8")

    assert im.should_ignore(str(path1)) is True
    assert im.should_ignore(str(path2)) is True


def test_segment_boundary_matching(tmp_path: Path) -> None:
    """
    A simple name should match on segment boundaries only.
    'build' matches '/build' or '/x/build/y', but not '/rebuild'.
    """
    base = tmp_path
    im = IgnoreManager(base)
    im.clear_patterns()
    im.add_pattern("build")

    yes = base / "x" / "build" / "out.txt"
    no = base / "rebuild" / "out.txt"
    yes.parent.mkdir(parents=True, exist_ok=True)
    no.parent.mkdir(parents=True, exist_ok=True)
    yes.write_text("1")
    no.write_text("2")

    assert im.should_ignore(str(yes)) is True
    assert im.should_ignore(str(no)) is False
