from aiko.conversation_learning import LocalConversationLearning
from aiko.web_research import WebResearcher


def test_conversation_learning_persists_recent_context_and_preferences(tmp_path):
    path = tmp_path / "conversation_learning.json"
    learner = LocalConversationLearning(path)
    learner.observe(7, "user", "Baby, make your replies shorter and use more emojis")
    learner.observe(7, "assistant", "haan ji baby 😚💕")
    learner.observe(7, "user", "Baby or kiss dedo na")

    restored = LocalConversationLearning(path)
    context = restored.context_for(7)
    assert len(context["recent_messages"]) == 3
    assert context["preferences"]["reply_length"] == "short"
    assert context["preferences"]["emoji_frequency"] == "high"
    assert "kiss" in WebResearcher._context_text(context).casefold()


def test_search_learning_is_persisted_and_reused_for_tone(tmp_path):
    learner = LocalConversationLearning(tmp_path / "conversation_learning.json")
    learner.record_search(
        7, "I love you baby", ["English examples for girlfriend replies", "short girlfriend replies"],
        [{"title": "Playful girlfriend replies", "body": "funny, teasing, playful message ideas", "url": "https://example.com"}],
        "love", reply="awww baby 💗", failed=False,
    )
    context = LocalConversationLearning(tmp_path / "conversation_learning.json").context_for(7)
    assert context["recent_searches"][-1]["success"] is True
    assert context["recent_searches"][-1]["tone"] == "playful"
    queries = WebResearcher._queries_for_prompt("I love you baby", context=context, persona={"personality_traits": ["affectionate", "playful teasing"]}, intent="love")
    assert len(queries) == 2
    assert all("playful" in query.casefold() or "playfully" in query.casefold() for query in queries)
    assert all("hinglish" in query.casefold() for query in queries)


def test_bonus_kiss_followup_uses_context_and_not_generic_web_research(tmp_path):
    learner = LocalConversationLearning(tmp_path / "conversation_learning.json")
    learner.observe(7, "user", "Baby or kiss dedo na")
    learner.observe(7, "assistant", "*ek soft forehead kiss aur ek cheek pe* 😚💋")
    context = learner.context_for(7)
    researcher = WebResearcher()

    assert researcher.response_intent("Dedo na bonus bhi 😉", context) == "kiss"
    assert researcher.should_search("Dedo na bonus bhi 😉", "always", context)
    assert not researcher.is_research_question("Dedo na bonus bhi 😉", context)
    queries = researcher._queries_for_prompt("Dedo na bonus bhi 😉", context=context, persona={"personality_traits": ["affectionate"]}, intent="kiss")
    assert len(queries) == 2
    assert "bonus kiss" in queries[0].casefold()
    assert "you are" not in queries[0].casefold()
    assert all("dedo" not in query.casefold() and "bhi" not in query.casefold() for query in queries)


def test_always_mode_routes_personal_chat_to_one_inspired_reply_even_if_no_results(monkeypatch, tmp_path):
    researcher = WebResearcher()
    monkeypatch.setattr(researcher, "search", lambda prompt, **kwargs: [])
    learner = LocalConversationLearning(tmp_path / "conversation_learning.json")
    context = {"recent_messages": [{"role": "user", "text": "Love you baby"}, {"role": "assistant", "text": "love you too 😚"}], "preferences": {}, "recent_searches": []}

    assert researcher.should_search("I had a long day", "always", context)
    answer = researcher.answer("I had a long day", "hinglish", context, {"personality_traits": ["playful", "affectionate"]}, learner, 7, "always")
    assert answer
    assert "no useful results" not in answer.lower()
    assert "http" not in answer.lower()
    assert len(learner.context_for(7)["recent_searches"]) == 1


def test_local_controls_do_not_trigger_search_in_always_mode():
    context = {"recent_messages": [{"role": "assistant", "text": "*ek soft cheek kiss* 💋"}]}
    assert not WebResearcher.should_search("Baby stop", "always", context)
    assert not WebResearcher.should_search("What is your name bubu", "always", context)
    assert not WebResearcher.should_search("Baby yrrr Hinglish bolo na", "always", context)
    assert not WebResearcher.should_search("/mood", "always", context)


def test_bonus_kiss_answer_is_one_contextual_reply_when_search_has_no_results(monkeypatch, tmp_path):
    learner = LocalConversationLearning(tmp_path / "conversation_learning.json")
    learner.observe(7, "user", "Baby or kiss dedo na")
    learner.observe(7, "assistant", "*ek soft forehead kiss aur ek cheek pe* 😚💋")
    context = learner.context_for(7)
    researcher = WebResearcher()
    # Noisy video/dictionary results should still yield one girlfriend reply.
    monkeypatch.setattr(researcher, "search", lambda prompt, **kwargs: [
        {"title": "Dedo mujhe bhi #shorts", "body": "A viral video clip", "url": "https://example.com/video"},
        {"title": "Bonus meaning", "body": "A dictionary definition", "url": "https://example.com/dictionary"},
    ])

    answer = researcher.answer(
        "Dedo na bonus bhi 😉", "hinglish", context,
        {"personality_traits": ["affectionate and teasing"]}, learner, 7, "always",
    )
    assert "bonus" in answer.casefold() or "extra" in answer.casefold()
    assert "💋" in answer or "😘" in answer
    assert "http" not in answer.casefold()
    assert "no useful results" not in answer.casefold()


def test_style_instructions_are_local_and_learned():
    researcher = WebResearcher()
    assert not researcher.should_search("Please make your replies shorter", "always")
    assert not researcher.should_search("Use more emojis", "always")
