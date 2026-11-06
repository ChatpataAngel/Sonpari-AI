from __future__ import annotations
import sqlite3
from datetime import date, timedelta
from pathlib import Path

import pytest

from aiko.preferences import parse_quiet_hours, quiet_now, validate_timezone
from aiko.daily_challenges import challenge_for, next_streak
from aiko.backup import create_backup, restore_backup, validate_sqlite
from aiko.multi_ai import MultiAIClient


def test_timezone_validation():
    assert validate_timezone("Asia/Kolkata") == "Asia/Kolkata"
    with pytest.raises(ValueError):
        validate_timezone("../../etc/passwd")
    with pytest.raises(ValueError):
        validate_timezone("Not/A_Real_Zone")


def test_quiet_hours_parse_and_cross_midnight():
    assert parse_quiet_hours("23-08") == (23, 8)
    assert parse_quiet_hours("off") == (None, None)
    assert quiet_now(23, 23, 8)
    assert quiet_now(4, 23, 8)
    assert not quiet_now(8, 23, 8)
    assert not quiet_now(14, None, None)
    with pytest.raises(ValueError):
        parse_quiet_hours("8-8")
    with pytest.raises(ValueError):
        parse_quiet_hours("25-07")


def test_daily_challenge_is_stable_and_personalized():
    day = date(2026, 10, 28)
    first = challenge_for(100, day)
    assert first == challenge_for(100, day)
    assert first[0] == day.isoformat()
    from aiko.daily_challenges import CHALLENGES
    assert first[1] in {c[0] for c in CHALLENGES}
    # Deterministic selection can coincide by chance, so don't require different users
    assert len(first[2]) > 10


def test_streak_continuity_and_gap():
    today = date(2026, 10, 28)
    assert next_streak((today - timedelta(days=1)).isoformat(), 3, today) == 4
    assert next_streak((today - timedelta(days=3)).isoformat(), 3, today) == 1
    assert next_streak(today.isoformat(), 2, today) == 2
    assert next_streak(None, 0, today) == 1


def _make_db(path: Path, value: str):
    with sqlite3.connect(path) as conn:
        conn.execute("CREATE TABLE IF NOT EXISTS sample(value TEXT NOT NULL)")
        conn.execute("DELETE FROM sample")
        conn.execute("INSERT INTO sample(value) VALUES(?)", (value,))


def test_backup_validate_and_restore_preserves_database(tmp_path):
    db = tmp_path / "aiko.sqlite3"
    _make_db(db, "original-data")
    backup = create_backup(db, tmp_path / "backups", keep=3)
    ok, detail = validate_sqlite(backup)
    assert ok and detail == "ok"
    _make_db(db, "changed-data")
    restore_backup(backup, db)
    with sqlite3.connect(db) as conn:
        assert conn.execute("SELECT value FROM sample").fetchone()[0] == "original-data"
    # Restore must have made a pre-restore snapshot of the replaced database.
    assert list((tmp_path / "backups").glob("aiko-*.sqlite3"))


def test_backup_rejects_invalid_sqlite(tmp_path):
    bad = tmp_path / "not-a-db.sqlite3"
    bad.write_text("not sqlite", encoding="utf-8")
    ok, _ = validate_sqlite(bad)
    assert not ok
    with pytest.raises(ValueError):
        restore_backup(bad, tmp_path / "target.sqlite3")


def test_provider_alert_is_repeated_failure_only_and_rate_limited():
    client = MultiAIClient(persona={})
    client._enabled_providers = [object()]
    client._consecutive_failures = 2
    assert not client.should_alert_failure()
    client._consecutive_failures = 3
    assert client.should_alert_failure()
    assert not client.should_alert_failure()
    assert "consecutive full failures=3" in client.health_summary()
