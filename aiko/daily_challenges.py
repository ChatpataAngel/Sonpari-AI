"""Deterministic, per-user daily challenge selection and streak calculations."""
from __future__ import annotations
from datetime import date, timedelta
import hashlib

CHALLENGES = [
    ("kindness", "Send one kind message to someone you appreciate."),
    ("water", "Take a short break and drink a glass of water."),
    ("stretch", "Stand up and stretch for two minutes."),
    ("gratitude", "Name one small thing that went well today."),
    ("learning", "Learn one new fact and explain it in your own words."),
    ("tidy", "Spend five minutes tidying one small area."),
    ("breathe", "Take five slow, comfortable breaths."),
    ("connect", "Check in with a friend without expecting an immediate reply."),
]


def challenge_for(user_id: int, day: date | None = None) -> tuple[str, str, str]:
    day = day or date.today()
    digest = hashlib.sha256(f"{int(user_id)}:{day.isoformat()}".encode()).digest()
    key, text = CHALLENGES[int.from_bytes(digest[:4], "big") % len(CHALLENGES)]
    return day.isoformat(), key, text


def next_streak(previous_last: str | None, current_streak: int, today: date | None = None) -> int:
    today = today or date.today()
    if previous_last == today.isoformat():
        return max(1, current_streak)
    if previous_last == (today - timedelta(days=1)).isoformat():
        return max(0, current_streak) + 1
    return 1
