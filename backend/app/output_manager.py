"""Collision-safe run directories and atomic JSON report persistence."""
from __future__ import annotations

import json
import os
import re
import tempfile
import uuid
from pathlib import Path
from typing import Any


_RUN_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,63}$")


def make_run_id(value: str | None = None) -> str:
    """Return a safe caller-supplied ID or a collision-resistant generated ID."""
    candidate = value if value is not None else uuid.uuid4().hex
    if not _RUN_ID.fullmatch(candidate) or candidate in {".", ".."} or ".." in candidate:
        raise ValueError("run ID must be 1-64 safe letters, numbers, dots, underscores, or hyphens")
    return candidate


def create_run_directory(output_root: str | Path, run_id: str) -> Path:
    """Create a new run directory and refuse to reuse an existing one."""
    safe_id = make_run_id(run_id)
    root = Path(output_root).expanduser()
    root.mkdir(parents=True, exist_ok=True)
    run_dir = root / safe_id
    try:
        run_dir.mkdir()
    except FileExistsError as exc:
        raise FileExistsError(f"run directory already exists; choose a new run ID: {run_dir}") from exc
    return run_dir



def write_texts_no_overwrite(files: dict[str | Path, str]) -> tuple[Path, ...]:
    """Publish a set of text files without replacing existing outputs.

    Files are staged beside their destinations and linked into place. If any
    destination already exists or publication fails, only files created by
    this call are rolled back.
    """
    staged: list[tuple[Path, Path]] = []
    published: list[tuple[Path, Path]] = []
    try:
        for raw_target, content in files.items():
            target = Path(raw_target).expanduser()
            target.parent.mkdir(parents=True, exist_ok=True)
            with tempfile.NamedTemporaryFile(
                mode="w", encoding="utf-8", newline="", dir=target.parent,
                prefix=f".{target.name}.", suffix=".tmp", delete=False,
            ) as handle:
                temporary = Path(handle.name)
                handle.write(content)
                handle.flush()
                os.fsync(handle.fileno())
            staged.append((temporary, target))

        for temporary, target in staged:
            os.link(temporary, target)
            published.append((temporary, target))
    except Exception:
        for temporary, target in reversed(published):
            try:
                if target.exists() and os.path.samefile(temporary, target):
                    target.unlink()
            except OSError:
                pass
        raise
    finally:
        for temporary, _ in staged:
            temporary.unlink(missing_ok=True)

    return tuple(target for _, target in staged)


def write_json_no_overwrite(path: str | Path, payload: Any) -> Path:
    """Serialize JSON and publish it without replacing an existing file."""
    target = Path(path).expanduser()
    write_texts_no_overwrite({target: json.dumps(payload, indent=2, ensure_ascii=False) + "\\n"})
    return target


def write_json_atomic(path: str | Path, payload: Any) -> Path:
    """Write JSON to a sibling temporary file, then atomically replace target."""
    target = Path(path).expanduser()
    target.parent.mkdir(parents=True, exist_ok=True)
    temp_name: str | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w", encoding="utf-8", dir=target.parent,
            prefix=f".{target.name}.", suffix=".tmp", delete=False,
        ) as handle:
            temp_name = handle.name
            json.dump(payload, handle, indent=2, ensure_ascii=False)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temp_name, target)
        temp_name = None
    finally:
        if temp_name is not None:
            try:
                os.unlink(temp_name)
            except FileNotFoundError:
                pass
    return target
