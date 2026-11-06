# Architecture

## Message path

1. Telegram adapter or offline terminal receives text.
2. `LanguageTracker` chooses English, Hindi or Hinglish.
3. `Memory` extracts only supported explicit facts; storage is local SQLite.
4. `DialogueManager` checks precise conversational intents before broad rules.
5. `ResponseEngine` chooses a weighted YAML rule by priority and cooldown.
6. If all local paths miss, optional Groq AI can generate a natural reply from the current message and bounded recent chat context; errors fall back locally.
7. Mood/affection changes are persisted locally and the humanizer sends the reply.

## Why intent-first matching exists

Broad rules such as `pets`, `food` or generic fallback phrases can steal a message from its actual conversational meaning. Specific intents like a greeting, kiss request, laughter, innuendo or a short answer should be evaluated first. Unknown input should lead to a simple clarifying question, not a random unrelated statement.

## Optional Groq chat fallback and optional search

No model is downloaded or run locally. YAML regexes, curated templates, local state and weighted random choice handle known intent paths. If `GROQ_API_KEY` is set and `GROQ_ENABLED` is not false, only messages that have no direct-intent, YAML-rule, or reflection match may use Groq's hosted OpenAI-compatible chat-completions API. It receives the current text and up to eight recent turns after heuristic redaction of common sensitive patterns. The redaction cannot guarantee that all sensitive information is removed; remove the key or set `GROQ_ENABLED=false` to keep chat responses local. Terminal mode can run without the internet when `/web off` is set. In `/web auto` (default), factual questions query the full prompt and extracted keywords, while common relationship prompts (such as `I love you`, `I miss you`, compliments, comfort requests and apologies) query the original prompt plus a tailored search for girlfriend-style reply examples. Search results select a broad tone where possible; the bot then emits one original local template with emojis rather than a web-result digest. Snippet text is not copied verbatim as the chat reply. Other ordinary greetings remain local unless `/web always` is enabled. `/web always` searches non-factual everyday messages for response inspiration (not generic web-result dumps), while factual questions still return a concise source digest. Persona-identity questions, slash commands, language/style instructions, and explicit stop requests stay local. `LocalConversationLearning` persists a bounded recent transcript, recurring topic counts, style preferences, and search outcomes; relevant context is summarized in English for later reply-inspiration queries, and prior tone cues help vary subsequent replies. The full raw transcript remains local rather than being uploaded to the search provider. `/search <prompt>` searches once. Telegram delivers each research digest as a single message, and older search results are discarded if the user sends a newer turn before the search completes. Factual queries are formatted into a digest with titles, snippets, source links and a next-step note. Factual web digests depend on third-party providers; when an ordinary chat message has no local match, the optional Groq layer can compose a response, while web search remains a distinct routing path. Telegram mode needs internet for Telegram transport and optionally for web search.
