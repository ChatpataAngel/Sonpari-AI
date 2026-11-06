# Privacy and safe deployment

- Keep `.env` private. Never distribute a live Telegram token.
- Set `OWNER_ID` to identify the original owner. Chat is available to all users in platonic Friend mode; the configured `OWNER_CODE` only unlocks BF-style replies. Owner-only administrative actions still require `OWNER_ID`. Set the shared code in private deployment settings and do not send it in group chats.
- The local SQLite database can contain user IDs, preferences and extracted facts. Treat it as private data.
- `LOG_MESSAGE_CONTENT=false` prevents message text from being stored in history; metadata is still stored for bot features.
- `/forget` deletes extracted facts. `/forgetall` plus `/confirm_forgetall` deletes the user row and associated rows through SQLite foreign-key cascades.
- `/export` exports the local profile and facts. Check it before sharing.
- Telegram mode uses Telegram's servers; it is not a fully offline or end-to-end-encrypted channel.
- Terminal mode stores extracted facts in `data/offline_memory.json`, taught pairs in `data/local_brain.json`, and a bounded local chat history/topic summary/search-learning record in `data/conversation_learning.json`. `/context` shows a brief summary; `/forgetchat` clears that learning record for the current profile.
- Web search sends English queries to external providers. FreeSerp is tried first via its keyless JSON endpoint; the optional SearXNG fallback runs only when `AIKO_SEARXNG_URL` is explicitly configured. `ddgs` is a fallback and HTML scraping is disabled unless `AIKO_ENABLE_DDG_HTML_FALLBACK=true`. For girlfriend-style reply inspiration, queries contain a semantic paraphrase of the current message, a compact relevant context cue, and non-identifying character-style traits—not the raw full chat transcript. Factual research can send the current question and a shorter keyword query. `/web off` disables automatic search; explicit `/search <prompt>` still initiates a one-time search. Search providers can see the query and request metadata, so keyless does not mean anonymous. Never search passwords, Telegram tokens, private conversations, addresses, or other sensitive text.
- This is a fictional character. Do not present it as a real person or use it to deceive someone.

- Journal entries and reminder text are stored in SQLite until cleared or the user profile is deleted.


## Universal translator

The `/translate` command sends only the text supplied to that command to an external translation provider. It uses a configured `AIKO_TRANSLATE_URL` endpoint if one is set, followed by a keyless Google Translate web endpoint fallback. The fallback is unofficial and can be unavailable or rate-limited. Ordinary chat messages are not automatically translated or sent to these translation providers. Translation results are cached in memory for up to ten minutes; translated text is not written to disk by the translator module itself. Do not submit passwords, tokens, addresses, or other sensitive content for translation.


## Optional Groq chat completion (v20)

If `GROQ_API_KEY` is configured and `GROQ_ENABLED` is not false, a hosted Groq model is called only when an ordinary chat message gets no match from local direct dialogue, YAML rules, or reflection rules. In that case, the current message plus up to eight recent local conversation turns are sent to Groq to generate a reply. Common patterns for credentials/tokens, email addresses, phone numbers, long numeric identifiers, and local paths are redacted first, but redaction is heuristic and cannot guarantee removal of every sensitive detail. Do not send highly sensitive material if this feature is enabled. Set `GROQ_ENABLED=false` or remove `GROQ_API_KEY` to disable it; local replies continue to work. Keep `.env` private.


## v29 per-user controls

- `/prefs memory off` disables future automatic fact extraction for that profile. Existing facts are retained until the user removes them with `/forget` or `/forgetall`.
- `/prefs learning off` stops storing further local conversation-context messages and clears existing per-user context. `/prefs learning on` starts a fresh context.
- `/memory` displays saved facts and a summary of local context; `/export` downloads an export that includes the locally stored conversation context, profile/preferences, facts, journal, reminders, mood log, and challenge rewards. Authentication fields are omitted.
- `/forgetchat` clears per-user conversation context, learned local replies, search preference and session language state. `/forgetall` additionally deletes the user's profile and database records after explicit confirmation.
- `/prefs timezone <IANA-name>`, `/prefs quiet HH-HH`, and `/prefs greetings on|off` govern optional scheduled messages. `/quiet` and `/loud` pause/resume all proactive messages.
- AI provider fallback and web search may transmit the active user prompt to the configured external provider. Local-first storage does not imply that external providers never receive a prompt. Do not send passwords, access tokens, or highly sensitive data.
- Local SQLite backups can contain profile data and should be treated as private. They are excluded from source releases and Docker build contexts. Store copies off-host securely if they are intended for disaster recovery.
