<div align="center">

# 🔐 Privacy & Safe Deployment

**What Sonpari-AI stores, what leaves your device, and how to deploy it responsibly.**

</div>

---

## 🔑 Secrets & Configuration

- **Keep `.env` private.** Never distribute a live Telegram token.
- **`OWNER_ID`** identifies the original owner. Chat is available to all users in platonic Friend mode; `OWNER_CODE` only unlocks BF-style replies. Owner-only administrative actions still require `OWNER_ID`.
- **Set `OWNER_CODE` only in private deployment settings** — never send it in group chats.

---

## 📦 What's Stored Locally

### SQLite database

The local SQLite database can contain **user IDs, preferences, and extracted facts**. Treat it as private data.

- **`LOG_MESSAGE_CONTENT=false`** prevents message text from being stored in history. Metadata is still stored for bot features.
- **Journal entries and reminder text** remain in SQLite until cleared or the user profile is deleted.

### Terminal mode files

| File | Contents |
| :-- | :-- |
| `data/offline_memory.json` | Extracted facts |
| `data/local_brain.json` | Taught pairs |
| `data/conversation_learning.json` | Bounded chat history, topic summary, search-learning record |

`/context` shows a brief summary; `/forgetchat` clears the learning record for the current profile.

---

## 🛂 User Data Controls

| Command | Effect |
| :-- | :-- |
| `/forget` | Deletes extracted facts |
| `/forgetall` + `/confirm_forgetall` | Deletes the user row and associated rows via SQLite foreign-key cascades |
| `/forgetchat` | Clears per-user conversation context, learned local replies, search preference, and session language state |
| `/export` | Exports local profile and facts — **review before sharing** |
| `/memory` | Displays saved facts and a summary of local context |
| `/prefs memory off` | Disables future automatic fact extraction (existing facts remain until `/forget` or `/forgetall`) |
| `/prefs learning off` | Stops storing conversation-context messages and clears existing per-user context; `/prefs learning on` starts a fresh context |
| `/prefs timezone <IANA-name>` | Sets timezone for scheduled messages |
| `/prefs quiet HH-HH` | Configures quiet hours |
| `/prefs greetings on\|off` | Toggles greetings |
| `/quiet` / `/loud` | Pauses / resumes all proactive messages |

> `/export` includes locally stored conversation context, profile/preferences, facts, journal, reminders, mood log, and challenge rewards. Authentication fields are omitted.

---

## 🌐 External Services

> ⚠️ **Local-first storage does not mean external providers never see a prompt.** AI provider fallback and web search may transmit the active user prompt to the configured provider. **Do not send passwords, access tokens, or highly sensitive data.**

### Telegram mode

Uses Telegram's servers. **Not** a fully offline or end-to-end-encrypted channel.

### Web search

- **English queries** are sent to external providers.
- **FreeSerp** is tried first via its keyless JSON endpoint.
- **SearXNG** fallback runs only when `AIKO_SEARXNG_URL` is explicitly configured.
- **`ddgs`** is a fallback; HTML scraping is disabled unless `AIKO_ENABLE_DDG_HTML_FALLBACK=true`.
- **Reply inspiration queries** contain a semantic paraphrase of the current message, a compact context cue, and non-identifying character traits — not the raw chat transcript.
- **Factual research** can send the current question and a shorter keyword query.
- `/web off` disables automatic search; explicit `/search <prompt>` still initiates a one-time search.

> 🚨 Search providers see the query and request metadata — **keyless does not mean anonymous.** Never search passwords, Telegram tokens, private conversations, addresses, or other sensitive text.

### Universal translator

- `/translate` sends **only the text supplied to that command** to an external translation provider.
- Uses configured `AIKO_TRANSLATE_URL` if set, then falls back to a keyless Google Translate web endpoint.
- The fallback is **unofficial** and may be unavailable or rate-limited.
- Ordinary chat messages are **not** automatically translated or sent to these providers.
- Translations are cached in memory for up to ten minutes; translated text is **not** written to disk by the translator module itself.

> Do not submit passwords, tokens, addresses, or other sensitive content for translation.

### Groq chat completion (v20)

- Called **only** when an ordinary chat message gets no match from local direct dialogue, YAML rules, or reflection rules.
- Requires `GROQ_API_KEY` and `GROQ_ENABLED` not set to `false`.
- Sends the current message plus up to **eight recent local conversation turns**.
- Common credential, email, phone, long-numeric, and path patterns are redacted first — **redaction is heuristic** and cannot guarantee removal of every sensitive detail.

> Do not send highly sensitive material if this feature is enabled. Set `GROQ_ENABLED=false` or remove `GROQ_API_KEY` to disable — local replies continue to work.

---

## 💾 Backups

Local SQLite backups can contain profile data and should be treated as private. They are excluded from source releases and Docker build contexts. Store copies off-host securely if intended for disaster recovery.

---

## 🎭 Fictional Character Notice

This is a **fictional character**. Do not present it as a real person or use it to deceive someone.

---

<div align="center">
<sub>Questions or concerns? Reach out via the creator links in the main README.</sub>
</div>
