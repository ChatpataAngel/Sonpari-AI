from aiko.utils import clamp
from aiko.mood import affection_tier, time_mood
def test_affection_clamps():
    assert clamp(-20)==0
    assert clamp(150)==100
def test_tiers():
    assert affection_tier(10)=="distant"
    assert affection_tier(40)=="warm"
    assert affection_tier(60)=="affectionate"
    assert affection_tier(90)=="deeply attached"
def test_time_mood():
    assert time_mood(7)=="sleepy"
    assert time_mood(14)=="neutral"
    assert time_mood(23)=="sleepy"
