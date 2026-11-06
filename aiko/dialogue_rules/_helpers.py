"""Shared rule helpers and response shape for the rule-only dialogue engine."""
from __future__ import annotations
import re
from typing import Iterable

Pools = dict[str, list[str]]
Rule = tuple[str, re.Pattern[str], Pools]

def rule(intent: str, pattern: str, hinglish: str | Iterable[str], hindi: str | Iterable[str], english: str | Iterable[str]) -> Rule:
    def as_list(value: str | Iterable[str]) -> list[str]:
        values = [value] if isinstance(value, str) else list(value)
        if not values or not all(isinstance(item, str) and item.strip() for item in values):
            raise ValueError(f"Rule '{intent}' must have non-empty response strings")
        return values
    return (intent, re.compile(pattern, re.IGNORECASE), {
        "hinglish": as_list(hinglish), "hi": as_list(hindi), "en": as_list(english),
    })
