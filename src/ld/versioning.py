from __future__ import annotations

from pathlib import Path


def next_version_path(directory: Path, basename: str, kind: str = "final") -> Path:
    directory.mkdir(parents=True, exist_ok=True)
    n = 1
    while True:
        if kind == "final":
            p = directory / f"{basename}_v{n}.docx"
        else:
            p = directory / f"{basename}_{kind}_v{n}.docx"
        if not p.exists():
            return p
        n += 1
