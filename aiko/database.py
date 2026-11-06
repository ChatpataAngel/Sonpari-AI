from __future__ import annotations
import os
import sqlite3
import asyncio
import logging
from contextlib import closing
from pathlib import Path
import aiosqlite

SCHEMA_VERSION = 5
_LOG = logging.getLogger(__name__)


def _needs_migration_backup(path: str) -> bool:
    """Detect older/partial schemas without mutating the existing database."""
    if not Path(path).is_file() or Path(path).stat().st_size == 0:
        return False
    try:
        with closing(sqlite3.connect(f"file:{Path(path).resolve()}?mode=ro", uri=True, timeout=5)) as conn:
            tables = {r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")}
            if not tables:
                return False
            if "users" not in tables:
                return True
            user_cols = {r[1] for r in conn.execute("PRAGMA table_info(users)")}
            required_cols = {"lang", "lang_preference", "adult_mode", "bf_access", "quiet_start", "quiet_end", "quiet_override", "greetings_enabled", "timezone_preference", "memory_enabled", "learning_enabled"}
            if not required_cols.issubset(user_cols):
                return True
            required_tables = {"facts", "history", "reminders", "pass_attempts", "challenge_progress", "challenge_streaks", "challenge_badges"}
            if not required_tables.issubset(tables):
                return True
            if "schema_version" not in tables:
                return True
            row = conn.execute("SELECT MAX(version) FROM schema_version").fetchone()
            version = int(row[0] or 1) if row else 1
            return version < SCHEMA_VERSION
    except sqlite3.Error:
        # A malformed database should not be silently backed up as a valid migration source.
        raise RuntimeError("Existing database could not be inspected safely; preserve a copy and repair it before startup.")
class Database:
    def __init__(self, path: str, log_message_content: bool = False):
        self.path, self.log_message_content = path, log_message_content
        self.conn: aiosqlite.Connection | None = None
    async def open(self):
        Path(self.path).parent.mkdir(parents=True, exist_ok=True)
        # Before an in-place schema migration, make a verified snapshot of old
        # user data. If that fails, abort rather than mutate an unprotected DB.
        if _needs_migration_backup(self.path):
            from .backup import create_backup
            await asyncio.to_thread(create_backup, self.path, Path(self.path).parent / "backups", 7)
            _LOG.info("Created pre-migration database snapshot for schema version < %s", SCHEMA_VERSION)
        self.conn = await aiosqlite.connect(self.path)
        try:
            self.conn.row_factory = aiosqlite.Row
            await self.conn.execute("PRAGMA foreign_keys=ON")
            await self.conn.execute("PRAGMA journal_mode=WAL")
            await self.initialize()
            return self
        except Exception:
            await self.conn.close()
            self.conn = None
            raise
    async def initialize(self):
        assert self.conn
        await self.conn.executescript("""
        CREATE TABLE IF NOT EXISTS schema_version(version INTEGER NOT NULL);
        INSERT INTO schema_version(version) SELECT 1 WHERE NOT EXISTS (SELECT 1 FROM schema_version);
        CREATE TABLE IF NOT EXISTS users(
          user_id INTEGER PRIMARY KEY, username TEXT, display_name TEXT,
          first_seen TEXT NOT NULL, last_seen TEXT NOT NULL, message_count INTEGER DEFAULT 0,
          affection INTEGER DEFAULT 10, mood TEXT DEFAULT 'neutral', mood_updated TEXT,
          last_proactive TEXT, proactive_enabled INTEGER DEFAULT 1, timezone TEXT,
          lang TEXT DEFAULT 'hinglish', lang_preference TEXT DEFAULT NULL,
          pass_code TEXT DEFAULT NULL, owner_code TEXT DEFAULT NULL,
          bf_access INTEGER NOT NULL DEFAULT 0, adult_mode INTEGER DEFAULT 0,
          quiet_start INTEGER DEFAULT NULL, quiet_end INTEGER DEFAULT NULL, quiet_override INTEGER NOT NULL DEFAULT 0,
          greetings_enabled INTEGER NOT NULL DEFAULT 1, timezone_preference TEXT DEFAULT NULL,
          memory_enabled INTEGER NOT NULL DEFAULT 1, learning_enabled INTEGER NOT NULL DEFAULT 1);
        CREATE TABLE IF NOT EXISTS facts(
          id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER NOT NULL, key TEXT NOT NULL,
          value TEXT NOT NULL, created_at TEXT NOT NULL, UNIQUE(user_id,key),
          FOREIGN KEY(user_id) REFERENCES users(user_id) ON DELETE CASCADE);
        CREATE TABLE IF NOT EXISTS history(
          id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER NOT NULL, role TEXT NOT NULL,
          rule_id TEXT, created_at TEXT NOT NULL,
          FOREIGN KEY(user_id) REFERENCES users(user_id) ON DELETE CASCADE);
        CREATE TABLE IF NOT EXISTS rule_cooldowns(
          user_id INTEGER NOT NULL, rule_id TEXT NOT NULL, last_fired REAL NOT NULL,
          PRIMARY KEY(user_id,rule_id), FOREIGN KEY(user_id) REFERENCES users(user_id) ON DELETE CASCADE);
        CREATE TABLE IF NOT EXISTS milestones(
          id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER NOT NULL, label TEXT NOT NULL,
          created_at TEXT NOT NULL, FOREIGN KEY(user_id) REFERENCES users(user_id) ON DELETE CASCADE);
        CREATE TABLE IF NOT EXISTS mood_log(
          id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER NOT NULL, old_mood TEXT, new_mood TEXT,
          reason TEXT, created_at TEXT NOT NULL, FOREIGN KEY(user_id) REFERENCES users(user_id) ON DELETE CASCADE);
        CREATE TABLE IF NOT EXISTS response_variations(
          user_id INTEGER NOT NULL, response TEXT NOT NULL, created_at REAL NOT NULL);
        CREATE TABLE IF NOT EXISTS daily_greetings(
          user_id INTEGER NOT NULL, day TEXT NOT NULL, kind TEXT NOT NULL,
          PRIMARY KEY(user_id,day,kind), FOREIGN KEY(user_id) REFERENCES users(user_id) ON DELETE CASCADE);
        CREATE TABLE IF NOT EXISTS journal_entries(
          id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER NOT NULL, entry TEXT NOT NULL,
          created_at TEXT NOT NULL, FOREIGN KEY(user_id) REFERENCES users(user_id) ON DELETE CASCADE);
        CREATE TABLE IF NOT EXISTS reminders(
          id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER NOT NULL, message TEXT NOT NULL,
          due_at TEXT NOT NULL, created_at TEXT NOT NULL, sent INTEGER NOT NULL DEFAULT 0,
          FOREIGN KEY(user_id) REFERENCES users(user_id) ON DELETE CASCADE);
        CREATE TABLE IF NOT EXISTS pass_attempts(
          user_id INTEGER PRIMARY KEY, attempts INTEGER NOT NULL DEFAULT 0,
          window_started TEXT NOT NULL, locked_until TEXT,
          FOREIGN KEY(user_id) REFERENCES users(user_id) ON DELETE CASCADE);
        CREATE TABLE IF NOT EXISTS challenge_progress(
          user_id INTEGER NOT NULL, challenge_date TEXT NOT NULL, challenge_key TEXT NOT NULL,
          completed INTEGER NOT NULL DEFAULT 0, points INTEGER NOT NULL DEFAULT 0,
          completed_at TEXT, PRIMARY KEY(user_id, challenge_date),
          FOREIGN KEY(user_id) REFERENCES users(user_id) ON DELETE CASCADE);
        CREATE TABLE IF NOT EXISTS challenge_streaks(
          user_id INTEGER PRIMARY KEY, current_streak INTEGER NOT NULL DEFAULT 0,
          best_streak INTEGER NOT NULL DEFAULT 0, last_completed TEXT, total_points INTEGER NOT NULL DEFAULT 0,
          FOREIGN KEY(user_id) REFERENCES users(user_id) ON DELETE CASCADE);
        CREATE TABLE IF NOT EXISTS challenge_badges(
          user_id INTEGER NOT NULL, badge_key TEXT NOT NULL, earned_at TEXT NOT NULL,
          PRIMARY KEY(user_id,badge_key),
          FOREIGN KEY(user_id) REFERENCES users(user_id) ON DELETE CASCADE);
        """)
        if self.log_message_content:
            cur = await self.conn.execute("PRAGMA table_info(history)")
            cols = {r["name"] for r in await cur.fetchall()}
            if "content" not in cols: await self.conn.execute("ALTER TABLE history ADD COLUMN content TEXT")
        # Idempotent migrations: support databases shipped by earlier v28 builds.
        cur = await self.conn.execute("PRAGMA table_info(users)")
        cols = {r["name"] for r in await cur.fetchall()}
        migrations = {
            "lang": "ALTER TABLE users ADD COLUMN lang TEXT DEFAULT 'hinglish'",
            "lang_preference": "ALTER TABLE users ADD COLUMN lang_preference TEXT DEFAULT NULL",
            "adult_mode": "ALTER TABLE users ADD COLUMN adult_mode INTEGER DEFAULT 0",
            "pass_code": "ALTER TABLE users ADD COLUMN pass_code TEXT DEFAULT NULL",
            "owner_code": "ALTER TABLE users ADD COLUMN owner_code TEXT DEFAULT NULL",
            "bf_access": "ALTER TABLE users ADD COLUMN bf_access INTEGER NOT NULL DEFAULT 0",
            "quiet_start": "ALTER TABLE users ADD COLUMN quiet_start INTEGER DEFAULT NULL",
            "quiet_end": "ALTER TABLE users ADD COLUMN quiet_end INTEGER DEFAULT NULL",
            "quiet_override": "ALTER TABLE users ADD COLUMN quiet_override INTEGER NOT NULL DEFAULT 0",
            "greetings_enabled": "ALTER TABLE users ADD COLUMN greetings_enabled INTEGER NOT NULL DEFAULT 1",
            "timezone_preference": "ALTER TABLE users ADD COLUMN timezone_preference TEXT DEFAULT NULL",
            "memory_enabled": "ALTER TABLE users ADD COLUMN memory_enabled INTEGER NOT NULL DEFAULT 1",
            "learning_enabled": "ALTER TABLE users ADD COLUMN learning_enabled INTEGER NOT NULL DEFAULT 1",
        }
        for column, statement in migrations.items():
            if column not in cols:
                await self.conn.execute(statement)
        await self.conn.execute("UPDATE schema_version SET version=?", (SCHEMA_VERSION,))
        await self.conn.commit()
    async def execute(self, sql, params=()):
        assert self.conn
        cur = await self.conn.execute(sql, params); await self.conn.commit(); return cur
    async def fetchone(self, sql, params=()):
        assert self.conn
        cur = await self.conn.execute(sql, params); return await cur.fetchone()
    async def fetchall(self, sql, params=()):
        assert self.conn
        cur = await self.conn.execute(sql, params); return await cur.fetchall()
    async def ensure_user(self, user_id, username=None, display_name=None, timezone=None):
        from datetime import datetime, timezone as tz
        now = datetime.now(tz.utc).isoformat()
        await self.execute("""INSERT INTO users(user_id,username,display_name,first_seen,last_seen,mood_updated,timezone)
        VALUES(?,?,?,?,?,?,?) ON CONFLICT(user_id) DO UPDATE SET username=excluded.username,
        display_name=excluded.display_name,last_seen=excluded.last_seen""",
        (user_id,username,display_name,now,now,now,timezone))
    async def get_user(self, user_id):
        return await self.fetchone("SELECT * FROM users WHERE user_id=?", (user_id,))
    async def log_message(self, user_id, role, rule_id=None, content=None):
        from datetime import datetime, timezone
        now = datetime.now(timezone.utc).isoformat()
        if self.log_message_content:
            await self.execute("INSERT INTO history(user_id,role,rule_id,created_at,content) VALUES(?,?,?,?,?)",
                               (user_id,role,rule_id,now,content))
        else:
            await self.execute("INSERT INTO history(user_id,role,rule_id,created_at) VALUES(?,?,?,?)",
                               (user_id,role,rule_id,now))
    async def close(self):
        if self.conn: await self.conn.close(); self.conn = None
