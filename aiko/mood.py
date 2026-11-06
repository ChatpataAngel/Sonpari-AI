from __future__ import annotations
from datetime import datetime, timezone
from .utils import clamp, time_of_day
MOODS = {"neutral","happy","playful","flirty","sleepy","worried","pouty","affectionate"}
def affection_tier(value: int) -> str:
    value = clamp(value)
    if value <= 25: return "distant"
    if value <= 50: return "warm"
    if value <= 75: return "affectionate"
    return "deeply attached"
def time_mood(hour: int) -> str:
    if hour < 9: return "sleepy"
    if hour >= 23 or hour < 5: return "sleepy"
    return "neutral"
async def apply_effect(db, user_id: int, affection_delta: int = 0, mood: str | None = None, reason: str = "rule"):
    row = await db.get_user(user_id)
    if not row: return
    old_mood = row["mood"] or "neutral"
    new_affection = clamp(row["affection"] + int(affection_delta))
    new_mood = mood if mood in MOODS else old_mood
    await db.execute("UPDATE users SET affection=?, mood=?, mood_updated=? WHERE user_id=?",
                     (new_affection,new_mood,datetime.now(timezone.utc).isoformat(),user_id))
    if new_mood != old_mood:
        await db.execute("INSERT INTO mood_log(user_id,old_mood,new_mood,reason,created_at) VALUES(?,?,?,?,?)",
                         (user_id,old_mood,new_mood,reason,datetime.now(timezone.utc).isoformat()))
async def decay_inactive(db):
    now = datetime.now(timezone.utc)
    rows = await db.fetchall("SELECT user_id,affection,last_seen,mood,mood_updated FROM users")
    for row in rows:
        try:
            last = datetime.fromisoformat(row["last_seen"])
            if last.tzinfo is None: last = last.replace(tzinfo=timezone.utc)
            points = int(max(0,(now-last).total_seconds()) // 172800)
            if points: await db.execute("UPDATE users SET affection=?, mood=? WHERE user_id=?",
                                        (clamp(row["affection"]-points), "neutral", row["user_id"]))
            else:
                updated = datetime.fromisoformat(row["mood_updated"]) if row["mood_updated"] else now
                if updated.tzinfo is None: updated = updated.replace(tzinfo=timezone.utc)
                if (now-updated).total_seconds() >= 7200 and row["mood"] != "neutral":
                    await db.execute("UPDATE users SET mood='neutral' WHERE user_id=?", (row["user_id"],))
        except (ValueError, TypeError): continue
