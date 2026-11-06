"""Validated SQLite backup helpers for AIKO.

Backups are local snapshots, not encrypted vaults. Keep the backup directory
private and never include it in release ZIPs or public source repositories.
"""
from __future__ import annotations

import sqlite3
from datetime import datetime, timezone
from pathlib import Path
import os
from contextlib import closing


def validate_sqlite(path: str | Path) -> tuple[bool, str]:
    candidate = Path(path)
    if not candidate.is_file():
        return False, "file not found"
    try:
        with closing(sqlite3.connect(f"file:{candidate.resolve()}?mode=ro", uri=True, timeout=10)) as conn:
            result = conn.execute("PRAGMA integrity_check").fetchone()
            if not result or result[0] != "ok":
                return False, str(result[0] if result else "integrity check returned no result")
            # Only accept databases that can enumerate their schema.
            conn.execute("SELECT name FROM sqlite_master LIMIT 1").fetchone()
        return True, "ok"
    except sqlite3.Error as exc:
        return False, f"sqlite error: {type(exc).__name__}"


def create_backup(db_path: str | Path, backup_dir: str | Path | None = None, keep: int = 7) -> Path:
    source = Path(db_path)
    if not source.is_file():
        raise FileNotFoundError(f"database does not exist: {source}")
    target_dir = Path(backup_dir) if backup_dir else source.parent / "backups"
    target_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    final = target_dir / f"aiko-{stamp}.sqlite3"
    temp = final.with_suffix(final.suffix + ".tmp")
    try:
        temp.unlink(missing_ok=True)
        with closing(sqlite3.connect(str(source), timeout=15)) as src, closing(sqlite3.connect(str(temp), timeout=15)) as dst:
            src.backup(dst)
            dst.execute("PRAGMA journal_mode=DELETE")
        ok, message = validate_sqlite(temp)
        if not ok:
            raise RuntimeError(f"backup validation failed: {message}")
        os.replace(temp, final)
        backups = sorted(target_dir.glob("aiko-*.sqlite3"), key=lambda p: p.stat().st_mtime, reverse=True)
        for stale in backups[max(1, int(keep)):]:
            try:
                stale.unlink()
            except OSError:
                pass
        return final
    finally:
        try:
            temp.unlink(missing_ok=True)
        except OSError:
            pass


def restore_backup(backup_path: str | Path, target_db: str | Path) -> Path:
    """Validate and stage a restore. Caller must stop the bot before invoking."""
    backup, target = Path(backup_path), Path(target_db)
    ok, message = validate_sqlite(backup)
    if not ok:
        raise ValueError(f"refusing invalid backup: {message}")
    target.parent.mkdir(parents=True, exist_ok=True)
    staged = target.with_suffix(target.suffix + ".restore.tmp")
    try:
        with closing(sqlite3.connect(str(backup), timeout=15)) as src, closing(sqlite3.connect(str(staged), timeout=15)) as dst:
            src.backup(dst)
        ok, message = validate_sqlite(staged)
        if not ok:
            raise RuntimeError(f"staged restore validation failed: {message}")
        # Preserve the current database before replacement when one exists.
        if target.exists():
            create_backup(target, target.parent / "backups", keep=7)
        for suffix in ("-wal", "-shm"):
            sidecar = Path(str(target) + suffix)
            if sidecar.exists():
                sidecar.unlink()
        os.replace(staged, target)
        return target
    finally:
        staged.unlink(missing_ok=True)
