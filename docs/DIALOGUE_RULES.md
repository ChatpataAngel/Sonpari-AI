# Offline dialogue rule packs

Aiko's conversational behavior is intentionally rule-based and works without an
AI model, API key, or internet access. Rule packs live in `aiko/dialogue_rules/`:

- `greetings.py`: greetings, language-neutral openers, and check-ins
- `contextual.py`: clarification, filler turns, yes/no replies, and short answers
- `romance.py`: hugs, kisses, affectionate responses, and light consensual flirting
- `humor.py`: jokes, dark-ish humor, roast prompts, sarcasm, and memes
- `support.py`: comfort, stress, apologies, boundaries, and thanks
- `daily.py`: daily life, school/work, food, sleep, entertainment and hobbies
- `social.py`: gossip, games, stories, opinions, success and advice

## Adding a rule

Use the shared `rule()` helper to compile an ordered regex and supply response
pools for `hinglish`, `hi` (Devanagari Hindi), and `en` (English). Add specific
rules before broad ones in the relevant pack. Avoid patterns that match a single
common word anywhere in a sentence; prefer anchored patterns for short replies.

Example:

```python
rule(
    "tea_or_coffee",
    r"\\b(?:tea|chai|coffee)\\b",
    ["chai ke bina system boot hi nahi hota ☕ tumhara kya?"],
    ["चाय के बिना system boot ही नहीं होता ☕ तुम्हारा क्या?"],
    ["my system won't boot without chai ☕ what about you?"],
)
```

`DialogueManager.note_response(user_id, text, intent)` should be called after
all assistant replies. It enables contextual clarifications so questions like
"Kis baare me?" do not receive a random follow-up question. Explicit language
requests such as "Hinglish me baat kro na" are detected before normal intents
and stay active for that session; `auto language` resumes normal detection.

Run checks with:

```bash
python -m pytest -q tests/test_dialogue.py tests/test_dialogue_expanded.py tests/test_language.py
```

Keep response text natural and short. The engine has no semantic understanding,
so phrase coverage and regression examples are the primary way to improve it.
