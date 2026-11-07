<div align="center">

# 🎭 Offline Dialogue Rule Packs

**Aiko's conversation engine is rule-based and works without an AI model, API key, or internet.**

</div>

---

## 📚 Rule Packs

All rule packs live in `aiko/dialogue_rules/`.

| Pack | Covers |
| :-- | :-- |
| `greetings.py` | Greetings, language-neutral openers, check-ins |
| `contextual.py` | Clarification, filler turns, yes/no replies, short answers |
| `romance.py` | Hugs, kisses, affectionate responses, light consensual flirting |
| `humor.py` | Jokes, dark-ish humor, roast prompts, sarcasm, memes |
| `support.py` | Comfort, stress, apologies, boundaries, thanks |
| `daily.py` | Daily life, school/work, food, sleep, entertainment, hobbies |
| `social.py` | Gossip, games, stories, opinions, success, advice |

---

## ➕ Adding a Rule

Use the shared `rule()` helper. It compiles an **ordered regex** and accepts response pools for each language:

| Pool | Language |
| :-- | :-- |
| `hinglish` | Romanized Hinglish |
| `hi` | Devanagari Hindi |
| `en` | English |

### Guidelines

- **Order matters** — place specific rules **before** broad ones within a pack.
- **Avoid bare single-word matches** — a pattern that fires on one common word anywhere in a sentence causes false positives. Prefer anchored patterns for short replies.

### Example

```python
rule(
    "tea_or_coffee",
    r"\b(?:tea|chai|coffee)\b",
    ["chai ke bina system boot hi nahi hota ☕ tumhara kya?"],
    ["चाय के बिना system boot ही नहीं होता ☕ तुम्हारा क्या?"],
    ["my system won't boot without chai ☕ what about you?"],
)
```

---

## 🧠 Response Tracking

Call `DialogueManager.note_response(user_id, text, intent)` **after every assistant reply**. This enables contextual clarifications, so questions like *"Kis baare me?"* don't get a random follow-up question back.

### Language requests

- Explicit language requests (e.g. *"Hinglish me baat kro na"*) are detected **before** normal intents.
- They stay active for that session.
- `auto language` resumes normal detection.

---

## ✅ Running the Checks

```bash
python -m pytest -q tests/test_dialogue.py tests/test_dialogue_expanded.py tests/test_language.py
```

---

## 📝 Style Rules

> **Keep response text natural and short.** The engine has **no semantic understanding**, so phrase coverage and regression examples are the primary way to improve it.

---

<div align="center">
<sub>See <code>CONVERSATION_FIXES.md</code> for recent rule regressions and their fixes.</sub>
</div>
