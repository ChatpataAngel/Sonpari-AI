import asyncio
import os
import tempfile
import aiosqlite
from aiko.database import Database


async def _run():
    path = os.path.join(tempfile.mkdtemp(), "t.db")
    db = await Database(path).open()
    await db.ensure_user(5, "u", "Test", "UTC")
    row = await db.get_user(5)
    assert row["lang"] == "hinglish", row["lang"]
    await db.execute("UPDATE users SET lang=? WHERE user_id=?", ("hi", 5))
    row = await db.get_user(5)
    assert row["lang"] == "hi"
    await db.close()

    # Simulate an OLD database created before the lang column existed.
    old_path = os.path.join(tempfile.mkdtemp(), "old.db")
    conn = await aiosqlite.connect(old_path)
    await conn.execute("""CREATE TABLE users(user_id INTEGER PRIMARY KEY, username TEXT,
        display_name TEXT, first_seen TEXT NOT NULL, last_seen TEXT NOT NULL,
        message_count INTEGER DEFAULT 0, affection INTEGER DEFAULT 10,
        mood TEXT DEFAULT 'neutral', mood_updated TEXT, last_proactive TEXT,
        proactive_enabled INTEGER DEFAULT 1, timezone TEXT)""")
    await conn.execute("INSERT INTO users(user_id,first_seen,last_seen) VALUES(9,'x','y')")
    await conn.commit()
    await conn.close()

    # Re-opening through Database must migrate and add the lang column.
    db2 = await Database(old_path).open()
    row = await db2.get_user(9)
    assert row["lang"] == "hinglish", row["lang"]  # existing row gets the default
    await db2.close()
    print("DB migration test passed")


def test_lang_column_migration():
    asyncio.run(_run())
