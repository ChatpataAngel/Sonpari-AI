from __future__ import annotations
import random
from typing import Sequence, TypeVar
T = TypeVar("T")
def weighted_choice(items: Sequence[T], weights: Sequence[float], rng: random.Random | None = None) -> T:
    if not items: raise ValueError("weighted_choice needs at least one item")
    if len(items) != len(weights): raise ValueError("items and weights lengths differ")
    clean = [max(0.0, float(w)) for w in weights]
    if sum(clean) <= 0: return (rng or random).choice(list(items))
    return (rng or random).choices(list(items), weights=clean, k=1)[0]
def clamp(value: int, low: int = 0, high: int = 100) -> int:
    return max(low, min(high, int(value)))
def time_of_day(hour: int) -> str:
    if 5 <= hour < 12: return "morning"
    if 12 <= hour < 17: return "afternoon"
    if 17 <= hour < 21: return "evening"
    return "night"
