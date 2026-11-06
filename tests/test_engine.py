import random, yaml, pytest
from aiko.engine import ResponseEngine
from aiko.language import detect_language, LanguageTracker
PERSONA={"name":"Aiko","speech_style":{"lowercase":True,"emoji_frequency":"low","signature_emojis":["💕"],"uses_tildes":False,"pet_names":["love"],"max_message_length":180}}
def make_rules(tmp_path,doc):
    p=tmp_path/"rules.yaml"; p.write_text(yaml.safe_dump(doc),encoding="utf-8"); return str(p)
def test_load_and_compile(tmp_path):
    path=make_rules(tmp_path,{"rules":[{"id":"hi","patterns":[r"\bhi\b"],"priority":1,"weight":1,"responses":["hey"]}]})
    engine=ResponseEngine(PERSONA,[path]); assert engine.match("hi").rule_id=="hi"
def test_duplicate_and_bad_regex_fail(tmp_path):
    doc={"rules":[{"id":"x","patterns":["("],"responses":["x"]}]}
    with pytest.raises(ValueError): ResponseEngine(PERSONA,[make_rules(tmp_path,doc)])
def test_priority_and_weighted_selection(tmp_path):
    doc={"rules":[{"id":"low","patterns":["hello"],"priority":1,"weight":1,"responses":["low"]},
                  {"id":"high","patterns":["hello"],"priority":10,"weight":1,"responses":["high"]}]}
    e=ResponseEngine(PERSONA,[make_rules(tmp_path,doc)],random.Random(2))
    assert e.match("hello").rule_id=="high"
def test_safe_render_missing_key(tmp_path):
    e=ResponseEngine(PERSONA,[make_rules(tmp_path,{"rules":[],"fallbacks":["hi {unknown}"]})])
    assert "{unknown}" in e.render("hi {unknown}")
def test_cooldown(tmp_path):
    doc={"rules":[{"id":"x","patterns":["hi"],"priority":1,"weight":1,"responses":["hello"],"cooldown_seconds":60}]}
    e=ResponseEngine(PERSONA,make_rules(tmp_path,doc))
    assert e.match("hi",user_id=7,now=100).rule_id=="x"
    assert e.match("hi",user_id=7,now=110) is None
def test_reflection(tmp_path):
    e=ResponseEngine(PERSONA,[make_rules(tmp_path,{"rules":[],"reflection_rules":[{"pattern":r"\bi feel (.+)","responses":["why {thing}?"]}],"fallbacks":["x"]})])
    assert "sad" in e.apply_reflection("i feel sad")
def test_reflection_repeated_regression(tmp_path):
    e=ResponseEngine(PERSONA,[make_rules(tmp_path,{"rules":[],"reflection_rules":[{"pattern":r"\bi feel (.+)","responses":["why {thing}?"]}],"fallbacks":["x"]})])
    assert "sad" in e.apply_reflection("i feel sad")


# ---- Language-aware response selection ------------------------------------
def _lang_persona():
    return {"name":"Aiko","speech_style":{"lowercase":True,"emoji_frequency":"low",
            "signature_emojis":["💕"],"uses_tildes":False,
            "pet_names":["love"],"pet_names_hi":["jaan"],"pet_names_hinglish":["yaar"],
            "max_message_length":180}}

def test_match_selects_language_pool(tmp_path):
    rules={"rules":[{"id":"hi","patterns":[r"\bhi\b"],"priority":1,"weight":1,
            "responses":["hello","hey"]}]}
    path=make_rules(tmp_path,rules)
    # Sidecar Hindi translation file next to rules.yaml.
    (tmp_path/"rules.hi.yaml").write_text(yaml.safe_dump({"rules":{"hi":["नमस्ते","हेलो"]}}),encoding="utf-8")
    e=ResponseEngine(_lang_persona(),[path],random.Random(1))
    en=e.match("hi",lang="en"); hi=e.match("hi",lang="hi")
    assert en.response in ["hello","hey"]
    assert hi.response in ["नमस्ते","हेलो"]
    assert hi.responses==["नमस्ते","हेलो"]

def test_missing_translation_falls_back_to_english(tmp_path):
    rules={"rules":[{"id":"hi","patterns":[r"\bhi\b"],"priority":1,"weight":1,"responses":["hello"]}]}
    path=make_rules(tmp_path,rules)
    e=ResponseEngine(_lang_persona(),[path])
    # No translation file present: all languages fall back to English.
    assert e.match("hi",lang="hi").response=="hello"
    assert e.match("hi",lang="hinglish").response=="hello"

def test_fallback_and_proactive_per_language(tmp_path):
    path=make_rules(tmp_path,{"rules":[],"fallbacks":["english fb"]})
    (tmp_path/"rules.hi.yaml").write_text(yaml.safe_dump({"fallbacks":["हिंदी fb"]}),encoding="utf-8")
    e=ResponseEngine(_lang_persona(),[path],random.Random(3))
    assert e.get_fallback(lang="hi")=="हिंदी fb"
    assert e.get_fallback(lang="en")=="english fb"

def test_render_pet_names_per_language(tmp_path):
    e=ResponseEngine(_lang_persona(),[make_rules(tmp_path,{"rules":[]})])
    assert e.render("hey {pet}",lang="en") in ["hey love"]
    assert e.render("hey {pet}",lang="hi")=="hey jaan"
    assert e.render("hey {pet}",lang="hinglish")=="hey yaar"

def test_invalid_translation_file_raises(tmp_path):
    path=make_rules(tmp_path,{"rules":[],"fallbacks":[]})
    (tmp_path/"rules.hi.yaml").write_text("rules: [this is not a mapping]",encoding="utf-8")
    with pytest.raises(ValueError):
        ResponseEngine(_lang_persona(),[path])


# ---- Language detection ----------------------------------------------------
@pytest.mark.parametrize("text,lang,confident", [
    ("hello how are you","en",True),
    ("kya haal hai","hinglish",True),
    ("मैं ठीक हूँ","hi",True),
    ("ok","hinglish",False),
    ("😂","hinglish",False),
])
def test_detect(text,lang,confident):
    assert detect_language(text)==(lang,confident)

def test_tracker_sticky_and_switch():
    t=LanguageTracker()
    assert t.observe(1,"kya kar rahe ho")=="hinglish"
    assert t.observe(1,"ok")=="hinglish"           # ambiguous keeps language
    assert t.observe(1,"hello there")=="en"        # switches on clear english
    assert t.observe(2,"ok")=="hinglish"           # first ambiguous -> hinglish default

