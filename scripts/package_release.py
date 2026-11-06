#!/usr/bin/env python3
"""Build a clean AIKO release archive without environment secrets or runtime state."""
from __future__ import annotations
import argparse
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

EXCLUDED_PARTS = {".git", ".venv", "venv", "__pycache__", ".pytest_cache", ".mypy_cache", ".ruff_cache", "backups"}
EXCLUDED_SUFFIXES = {".pyc", ".pyo", ".sqlite3", ".db", ".log", ".tmp"}


def include_file(path: Path, root: Path, output: Path) -> bool:
    try:
        if path.resolve() == output.resolve(): return False
    except OSError:
        pass
    rel = path.relative_to(root)
    if any(part in EXCLUDED_PARTS for part in rel.parts): return False
    if any(part.startswith(".env") for part in rel.parts) and rel.as_posix() != ".env.example": return False
    if rel.parts and rel.parts[0] == "data":
        return rel.as_posix() == "data/.gitkeep"
    if path.suffix.lower() in EXCLUDED_SUFFIXES: return False
    if path.name.endswith(("-wal", "-shm")): return False
    if path.name.lower().endswith((".zip", ".tar.gz", ".rar", ".7z")): return False
    return path.is_file()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", default=".", help="project root (default: current directory)")
    parser.add_argument("--output", default="../AIKO_v29_Companion_Upgrade.zip", help="output ZIP path")
    args = parser.parse_args()
    root = Path(args.root).resolve()
    output = (root / args.output).resolve() if not Path(args.output).is_absolute() else Path(args.output).resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    files = sorted(p for p in root.rglob("*") if include_file(p, root, output))
    if not files:
        raise SystemExit("No project files found; check --root.")
    with ZipFile(output, "w", compression=ZIP_DEFLATED, compresslevel=8) as archive:
        for path in files:
            archive.write(path, path.relative_to(root).as_posix())
    print(f"Created {output} with {len(files)} files.")
    print("Runtime databases, backups, .env secrets, caches and previous archives were excluded.")
    return 0

if __name__ == "__main__": raise SystemExit(main())
