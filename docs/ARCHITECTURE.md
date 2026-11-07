<div align="center">

# 🏗️ Architecture

**How a message travels through Sonpari-AI.**

</div>

---

## 🛤️ Message Path

1. **Ingest** — Telegram adapter or offline terminal receives text
2. **Language** — `LanguageTracker` chooses English, Hindi, or Hinglish
3. **Memory** — `Memory` extracts only supported explicit facts; storage is local SQLite
4. **Intent** — `DialogueManager` checks **precise** conversational intents before broad rules
5. **Rules** — `ResponseEngine` chooses a weighted YAML rule by priority and cooldown
6. **Fallback** — If all local paths miss, optional **Groq** can generate a natural reply from the current message and bounded recent chat context; errors fall back locally
7. **Deliver** — Mood/affection changes are persisted locally; the humanizer sends the reply

---

## 🎯 Why Intent-First Matching Exists

> Broad rules such as `pets`, `food`, or generic fallback phrases can **steal a message** from its actual conversational meaning.

Specific intents — a greeting, kiss request, laughter, innuendo, or a short answer — should be evaluated **first**. Unknown input should lead to a simple clarifying question, **not** a random unrelated statement.

---

## 🤖 Optional Groq Fallback & Optional Search

No model is downloaded or run locally. YAML regexes, curated templates, local state, and weighted random choice handle known intent paths.

### Groq fallback

If `GROQ_API_KEY` is set and `GROQ_ENABLED` is not `false`, **only** messages with no direct-intent, YAML-rule, or reflection match may use Groq's hosted OpenAI-compatible chat-completions API. It receives:

- The current text
- Up to **eight recent turns**
- After heuristic redaction of common sensitive patterns

> ⚠️ Redaction **cannot guarantee** that all sensitive information is removed. Remove the key or set `GROQ_ENABLED=false` to keep chat responses local.

### Terminal mode

Runs without internet when `/web off` is set.

### Web search routing

| Mode | Behavior |
| :-- | :-- |
| `/web auto` (default) | Factual questions query the full prompt and extracted keywords. Common relationship prompts (e.g. `I love you`, `I miss you`, compliments, comfort requests, apologies) query the original prompt **plus** a tailored search for girlfriend-style reply examples |
| `/web always` | Searches **non-factual** everyday messages for response inspiration — not generic result dumps. Factual questions still return a concise source digest |
| `/web off` | Disables automatic search |

**Always stays local** regardless of mode:

- Persona-identity questions
- Slash commands
- Language/style instructions
- Explicit stop requests

### How search results are used

- Search results select a **broad tone** where possible
- The bot then emits **one original local template** with emojis — **not** a web-result digest
- **Snippet text is not copied verbatim** as the chat reply
- Ordinary greetings remain local unless `/web always` is enabled

### `LocalConversationLearning`

Persists:

- A bounded recent transcript
- Recurring topic counts
- Style preferences
- Search outcomes

Relevant context is summarized **in English** for later reply-inspiration queries, and prior tone cues help vary subsequent replies. **The full raw transcript remains local** — it is not uploaded to the search provider.

### Search commands

- `/search <prompt>` — searches once
- Telegram delivers each research digest as a **single message**
- Older search results are **discarded** if the user sends a newer turn before the search completes
- Factual queries are formatted into a digest with titles, snippets, source links, and a next-step note

### Dependencies

> Factual web digests depend on third-party providers. When an ordinary chat message has no local match, the optional Groq layer can compose a response — **web search remains a distinct routing path**. Telegram mode needs internet for Telegram transport and optionally for web search.

---

<div align="center">
<sub>See <code>PRIVACY.md</code> for exactly which data crosses the network boundary.</sub>
</div>
