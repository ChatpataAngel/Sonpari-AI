from aiko.local_brain import LocalBrain
from aiko.dialogue import DialogueManager


def test_brain_persists_and_matches_per_user(tmp_path):
    path = tmp_path / "brain.json"
    brain = LocalBrain(path)
    assert brain.learn("our secret word", "chai and chaos", 7)
    assert brain.match("Our secret word!", 7) == "chai and chaos"
    assert brain.match("our secret word", 8) is None
    assert LocalBrain(path).match("our secret word", 7) == "chai and chaos"


def test_dialogue_can_be_taught_and_recall_learned_reply(tmp_path):
    brain = LocalBrain(tmp_path / "brain.json")
    dialogue = DialogueManager(brain=brain)
    taught = dialogue.respond(12, "teach: test phrase => custom answer", "hinglish")
    assert taught and taught.intent == "brain_learned"
    learned = dialogue.respond(12, "test phrase", "hinglish")
    assert learned and learned.intent == "learned_reply"
    assert learned.text == "custom answer"


def test_extra_response_pools_are_loaded():
    from aiko.dialogue_rules import RULES
    pools = next(pools for intent, _pattern, pools in RULES if intent == "kiss")
    assert len(pools["hinglish"]) >= 8
    assert len(pools["en"]) >= 8
