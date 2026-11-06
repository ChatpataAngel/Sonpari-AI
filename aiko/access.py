"""Relationship-tier helpers.

BF access controls companion tone only. It deliberately does not grant owner-only
administrative permissions; those remain tied to the original Telegram OWNER_ID.
"""
from __future__ import annotations


def is_original_owner(settings, user_id: int | None) -> bool:
    return bool(user_id is not None and settings.owner_id is not None and user_id == settings.owner_id)


def has_bf_access(settings, user_id: int | None, row=None) -> bool:
    if is_original_owner(settings, user_id):
        return True
    if row is None:
        return False
    try:
        return bool(row["bf_access"])
    except (KeyError, IndexError, TypeError):
        return False


def relationship_label(settings, user_id: int | None, row=None) -> str:
    if is_original_owner(settings, user_id):
        return "Owner BF 👑💗"
    if has_bf_access(settings, user_id, row):
        return "BF 💗"
    return "Friend 🤝"
