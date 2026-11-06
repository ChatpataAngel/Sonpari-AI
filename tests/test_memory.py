from aiko.memory import extract_facts
def test_name_fact():
    assert ("name","Alex") in extract_facts("my name is Alex")
def test_like_fact():
    facts=extract_facts("i like pizza")
    assert any(k.startswith("like_") and v=="pizza" for k,v in facts)
def test_favorite_fact():
    assert ("color","blue") in extract_facts("my favorite color is blue")
def test_work_and_location():
    facts=extract_facts("i work as a designer")
    assert ("occupation","a designer") in facts
    assert ("location","Tokyo") in extract_facts("i live in Tokyo")
def test_mood_words_not_identity_facts():
    assert not extract_facts("i'm sad")
