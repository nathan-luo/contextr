import os
from pathlib import Path

from contextr.manager import ContextManager
from contextr.storage.json_storage import JsonStorage


def touch(p: Path, text=""):
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text, encoding="utf-8")


def test_refresh_counts(tmp_path: Path):
    # Change to tmp directory to avoid picking up project files
    os.chdir(tmp_path)
    state_dir = tmp_path / ".contextr"
    cm = ContextManager(storage=JsonStorage(state_dir))
    a = tmp_path / "src" / "a.py"
    b = tmp_path / "src" / "b.py"
    touch(a, "print(1)")
    touch(b, "print(2)")
    cm.watch_paths(["src/**/*.py"])
    assert len(cm.files) == 2

    # Add a file on disk
    c = tmp_path / "src" / "c.py"
    touch(c, "print(3)")
    stats = cm.refresh_watched()
    assert stats["added"] == 3  # Total files after refresh
    assert stats["removed"] == 0


def test_add_ignore_doesnt_add_unwatched(tmp_path: Path):
    os.chdir(tmp_path)
    state_dir = tmp_path / ".contextr"
    cm = ContextManager(storage=JsonStorage(state_dir))
    touch(tmp_path / "src" / "a.py")
    touch(tmp_path / "src" / "note.md")
    cm.watch_paths(["src/**/*.py"])
    assert len(cm.files) == 1  # just a.py

    cm.add_ignore_pattern("src/**/generated/")
    # Still only python files per watch pattern
    paths = cm.get_file_paths()
    # Normalize path separators for cross-platform comparison
    normalized_paths = [p.replace("\\", "/") for p in paths]
    assert normalized_paths == ["src/a.py"]


def test_profile_negation_roundtrip(tmp_path: Path):
    os.chdir(tmp_path)
    state_dir = tmp_path / ".contextr"
    cm = ContextManager(storage=JsonStorage(state_dir))
    touch(tmp_path / "node_modules" / "keep" / "x.js", "x")
    touch(tmp_path / "node_modules" / "drop" / "y.js", "y")
    cm.watch_paths(["**/*.js"])
    cm.add_ignore_pattern("node_modules/")
    cm.add_ignore_pattern("!node_modules/keep/")

    from contextr.profile import ProfileManager

    pm = ProfileManager(cm.storage, cm.base_dir)
    assert pm.save_profile(
        "p1",
        watched_patterns=list(cm.watched_patterns),
        ignore_patterns=cm.list_ignore_patterns(),
        force=True,
    )

    profile = pm.load_profile("p1")
    cm.apply_profile(profile, "p1")
    cm.refresh_watched()
    rels = cm.get_file_paths()
    # Normalize path separators for cross-platform comparison
    normalized_rels = [p.replace("\\", "/") for p in rels]
    assert "node_modules/keep/x.js" in normalized_rels
    assert "node_modules/drop/y.js" not in normalized_rels


def test_clear_persists_empty_ignore(tmp_path: Path):
    os.chdir(tmp_path)
    state_dir = tmp_path / ".contextr"
    cm = ContextManager(storage=JsonStorage(state_dir))

    # Add some patterns
    cm.add_ignore_pattern("*.log")
    cm.add_ignore_pattern("node_modules/")
    assert len(cm.list_ignore_patterns()) == 2

    # Clear everything
    cm.clear()

    # Verify ignore file is empty
    ignore_file = state_dir / ".ignore"
    assert ignore_file.exists()
    content = ignore_file.read_text()
    assert content.strip() == ""  # File should be empty

    # Create new manager to verify persistence
    cm2 = ContextManager(storage=JsonStorage(state_dir))
    assert len(cm2.list_ignore_patterns()) == 0


def test_watch_patterns_not_filtered(tmp_path: Path):
    os.chdir(tmp_path)
    state_dir = tmp_path / ".contextr"
    cm = ContextManager(storage=JsonStorage(state_dir))

    # Add ignore pattern first
    cm.add_ignore_pattern("src/")

    # Watch a pattern that would match the ignore
    cm.watch_paths(["src/**/*.py"])

    # Pattern should still be in watched list
    assert "src/**/*.py" in cm.list_watched()

    # Files should be ignored per-file, not per-pattern
    touch(tmp_path / "src" / "test.py", "print('test')")
    cm.refresh_watched()
    # File is ignored, but pattern is still watched
    assert len(cm.files) == 0
    assert "src/**/*.py" in cm.list_watched()
