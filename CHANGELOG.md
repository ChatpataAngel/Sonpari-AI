# Changelog

## Version 28.1 — Friend/BF relationship access and role-safe chat (28 October 2026)

- Anyone can start a normal, platonic Friend-mode conversation without a pass. The original `OWNER_ID` and users who verify the shared `OWNER_CODE` receive BF-style companion replies.
- Added private-chat `/pass <code>` verification that stores only a BF-access flag, `/unpass`, `/role`, original-owner-only `/bfusers`, and persistent `/checkin 1-10`.
- Kept administrative authority attached strictly to `OWNER_ID`; passing the shared code changes companion tone only.
- Added a role-aware AI system prompt, deterministic Friend-mode fallback and platonic proactive greetings, including safe behavior for explicit `/search` prompts.
- Fixed broken startup syntax, repaired `/name`, supplied the missing `/reset` and `/owner` handlers, migrated existing databases to the new role column, fixed adult-mode column access, and corrected webhook startup/shutdown callbacks.
- Removed private runtime database/WAL and local conversation-learning data from the distributable archive. SQLite role schema is created/migrated on startup.
- Added role and Friend-mode regression tests. Full database tests require `aiosqlite`; they could not be run in the offline audit environment.

## Version 28 — expanded local romance conversation bank (16 October 2026)

- Added `aiko/romance_conversation_bank.jsonl` with 7,500 unique, original user→assistant pairs (15,000 utterance messages), covering 75 romantic/relationship intents in Hinglish, Hindi, and English. The bank has 5,640 distinct assistant reply strings and 1,800 adult-tagged non-graphic examples.
- Added `aiko/romance_retrieval.py`, a dependency-free, cached lexical retriever. Existing direct dialogue rules and exact conversation-library patterns retain priority; ambiguous bank matches fall through to the existing general retrieval/fallback.
- Added `scripts/generate_romance_bank.py` and a validation/test suite for reproducible generation, unique prompts, language distribution, adult-content metadata, command isolation, and avoiding unrelated-topic hijacks.
- Reviewed public girlfriend/roleplay and dialogue datasets including Natasha, PIPPA, NSFW DPO preference pairs, Japanese 5.3k roleplay, EmpatheticDialogues, DailyDialog, and existing offline pattern-bot architecture. See `docs/ROMANCE_DATASET_RESEARCH_V28.md` for links, what the datasets actually contain, and licensing decisions.
- Third-party dialogue rows are not bulk-copied. The included 7,500 pairs are original Aiko-authored, template-expanded conversation examples informed by topic/style research—not a claim that 7,500 web-sourced rows were individually reviewed.
- No language model, new runtime dependency, network connection, or API key is needed for the local bank. Groq remains optional.
- Adult-tagged replies are suggestive but non-graphic, use fictional adult characters, and emphasize mutual comfort and consent.

## Version 26 — research-backed offline response expansion (15 October 2026)

- Reviewed representative rule-based chatbot engines, local retrieval systems, intent/dialogue managers, companion persona/context systems, persistent-memory frameworks, dialogue datasets, and actual offline inference runtimes. Added an expanded source and licence audit in `docs/CONVERSATION_RESEARCH.md`. This is a curated review, not a claim to have enumerated every GitHub repository or every web resource.
- Expanded `aiko/conversation_library.json` from 23 entries to 94 unique topics with 567 Aiko-authored static response variants in Hinglish, Hindi, and English. No third-party chatbot source code, dataset turns, model weights, or community character cards are bundled.
- Enhanced the local dialogue hub's broad topic coverage using keywords and authored examples, and preserved a finite, transparent no-model/no-network path. Optional Groq still supports open-domain responses when enabled.
- Added a guarded topic-specific pre-router ahead of generic keyword catch-alls while protecting explicit user-turn intents such as stop requests, greetings, check-ins, affection, flirting and romance. This fixes collisions where a single word in a longer sentence could otherwise hijack the reply.
- Added regression tests for library scale, multilingual response pools, broad paraphrase coverage, and high-priority existing conversation behavior.
- No new runtime dependency, local model download, or API key requirement was added.

## v25 — playful banter and refusal fallback
- Added a specific local Hinglish/Hindi/English rule for clearly playful, non-graphic adult body compliments, so the reported example gets a natural in-character response before Groq is called.
- Clarified the Groq prompt for consensual, non-graphic adult banter and added a style example.
- Bare generic model refusals now fall back to Aiko's already-generated local response instead of being shown verbatim. Other substantive model answers are unchanged.

4 — Groq Cloudflare 1010 diagnostics (15 October 2026)

- Added an explicit, clearly identified Aiko API-client User-Agent and Accept header to Groq requests instead of relying on Python's generic urllib identity. This may help if an edge rule is classifying the generic client; it cannot override a server-side block.
- Diagnostics now distinguish Cloudflare error 1010 (client-signature block) from Groq model-permission failures.
- Groq chat logs now recognize common top-level Cloudflare error JSON and HTML 1010 pages without logging the full response, API key, or chat prompt.
- Added regression coverage for Cloudflare 1010 and request headers.
- No new third-party runtime dependency.

# Changelog

## Version 28.1 — Friend/BF relationship access and role-safe chat (28 October 2026)

- Anyone can start a normal, platonic Friend-mode conversation without a pass. The original `OWNER_ID` and users who verify the shared `OWNER_CODE` receive BF-style companion replies.
- Added private-chat `/pass <code>` verification that stores only a BF-access flag, `/unpass`, `/role`, original-owner-only `/bfusers`, and persistent `/checkin 1-10`.
- Kept administrative authority attached strictly to `OWNER_ID`; passing the shared code changes companion tone only.
- Added a role-aware AI system prompt, deterministic Friend-mode fallback and platonic proactive greetings, including safe behavior for explicit `/search` prompts.
- Fixed broken startup syntax, repaired `/name`, supplied the missing `/reset` and `/owner` handlers, migrated existing databases to the new role column, fixed adult-mode column access, and corrected webhook startup/shutdown callbacks.
- Removed private runtime database/WAL and local conversation-learning data from the distributable archive. SQLite role schema is created/migrated on startup.
- Added role and Friend-mode regression tests. Full database tests require `aiosqlite`; they could not be run in the offline audit environment.

## Version 22 — Groq 403 diagnostics (15 October 2026)

- Groq HTTP errors now log the provider's short structured error code/type/message, sanitized and bounded, so 403 permission failures can be diagnosed without exposing the API key, prompt, or raw response body.
- Local fallback behavior is unchanged: a provider error never stops local conversation.
- Added a regression test for Groq's structured model-permission error response.

## Version 21 — expanded offline conversation library (15 October 2026)

- Added the first schema-versioned `aiko/conversation_library.json` with 23 original Aiko-authored supplemental conversational skills; v26 later expands this to 94 topics.
- Added supplementary coverage for low mood, stress/overwhelm, loneliness, fatigue, anxiety, self-pride, success, setbacks, boredom, sleeplessness, procrastination, motivation, venting, no-advice listening, reassurance, decision support, prompts/questions, changing topics, company, plans, recommendations, small wins, and transparent questions about how Aiko works.
- Wired the local library into `OfflineConversationHub` only after the existing direct dialogue packs have had priority; slash commands remain outside this matcher.
- Added `docs/CONVERSATION_RESEARCH.md` with representative GitHub research, source links, license notes, and an extension guide. No third-party chatbot source code or dialogue dataset was copied into the pack.
- Added regression tests for schema/data integrity, multilingual routing, dynamic choices, command isolation, hub fallback resilience, and existing romance priority.
- No additional third-party runtime dependency. The library works fully offline with `GROQ_ENABLED=false`; the optional Groq fallback remains unchanged.

## Version 20 — optional Groq chat fallback

- Added optional Groq-hosted AI for ordinary chat that receives no match from the existing direct dialogue, YAML rule engine, or reflection rules.
- Existing greetings, relationship intents, curated rule replies, explicit `/search`, and `/translate` remain on their existing paths. `/web always` does not cause casual AI replies to search the web.
- When `GROQ_API_KEY` is absent, `GROQ_ENABLED=false`, the request times out, or Groq returns an error, Aiko continues using its local fallback.
- Uses Groq's OpenAI-compatible chat-completions endpoint with model configurable via `GROQ_MODEL` (default `openai/gpt-oss-20b`); no SDK dependency was added.
- Only uses external AI for fallback replies, sends bounded recent chat context, and redacts obvious API keys/tokens, email addresses, phone numbers, long numeric IDs, and local paths before submission. Chat text/context may still be sent to Groq for a fallback reply; disable it to keep chat responses local.
- Added offline terminal-mode support, `.env.example` settings, documentation, and unit tests. The real `.env` and API key are not included in archives.

## v19 — Hinglish check-in fix

- Fixed the exact follow-up `😉me bhi aapse bt kr ra hu babyyy`: leading reaction emojis no longer block anchored intent matching, and common shortcuts normalize to `main bhi aapse baat kar raha hoon baby` for matching only.
- Added a dedicated local `reciprocal_chat` response so statements like “I'm also talking to you, baby” get a playful, natural Hinglish reply rather than the generic “give me more context” fallback.
- Marked reciprocal small-talk statements as local-only in web routing, including `/web always`; they no longer invoke FreeSerp or the web reply composer. Explicit `/search ...` still overrides this on purpose.
- Preserved emoji-only reaction handling while allowing leading emojis to be ignored by anchored text-intent matching.
- Added regression tests for normalization, multi-turn dialogue flow, and no-web routing of affectionate conversation.
- No model, API key, paid service or new dependency added.

## v15 — Expressive texting style (October 2026)

- Added a lightweight `aiko/text_style.py` normalizer for intent matching. It recognizes stretched spellings (`babyyyy`, `soooo`, `keseee`), short forms (`u`, `ur`, `r`, `hru`, `ily`, `idk`, `rn`, `pls/plz`, `bby`), and common Hinglish text abbreviations without rewriting the original message stored in local history.
- Direct dialogue, weighted YAML rules/reflections, local learned-trigger matching, and web-search intent routing now share the same normalization so stylized greetings/check-ins/affection requests are less likely to fall through to a generic response or trigger an irrelevant search.
- The local conversation learner now remembers whether a user prefers stretched letters and short forms. It saves those style preferences with existing local conversation preferences; expressive conversational replies gently mirror that style, while factual search digests remain readable and source-faithful.
- Expanded greeting handling for pet names and emojis (for example, `hiiiiii babyyyy 😚`).
- Added regression tests for stylized greetings, Hinglish wellbeing, love, compliments, kiss requests, keyless web-routing behavior, local brain trigger matching, and persistent reply-style preferences.
- No AI model, paid service, API key, or network dependency was added for this feature. The rules remain deterministic and offline.
- Validation: 121 targeted non-database tests pass; dialogue validation and Python compilation pass.

## v14 — Hinglish check-in routing fix (October 2026)

- Fixed `/web always` misclassifying everyday status messages such as `Kese ho babyy 😚😚💋` as generic web-inspiration requests.
- Added local routing coverage for `kese/kaise/kaisi/kaisa ho` and conversational variants such as `Aap kese ho me to acha hu`; these now use the existing `wellbeing` dialogue rule and do not hit the web.
- Explicit `/search ...` remains available when the user deliberately wants to search the same words.
- Added regression tests to ensure web modes (`auto` and `always`) leave these check-ins local and the direct reply is not the generic context fallback.

## v13 — Keyless search provider stabilization (October 2026)

- Added FreeSerp's documented keyless JSON endpoint as the default web-search provider (`index=web`, English query, bounded result count).
- Added optional SearXNG JSON search through `AIKO_SEARXNG_URL`; no random public instances are hard-coded, and public hosts must use HTTPS. SearXNG format=JSON can be disabled on public instances and may return 403.
- Kept `ddgs` as a fallback. DuckDuckGo HTML scraping is now opt-in (`AIKO_ENABLE_DDG_HTML_FALLBACK=true`) rather than a routine path likely to be blocked.
- Added a five-minute in-memory cache for successful and empty queries to reduce repeat traffic and duplicate requests.
- Normalized provider result formats; provider 403/network errors stay internal. Failed factual searches return a concise Hinglish no-results response instead of a raw exception. Social prompts continue using local girlfriend-style templates when all providers fail.
- Added `/web status` to terminal and Telegram mode to display configured provider order without issuing a live network request; terminal mode now loads optional search configuration from `.env`.
- Added tests for FreeSerp endpoint parameters and JSON normalization, provider fallback order, non-leaking 403 handling, and query caching.
- No LLM, cloud AI model, API key, or paid inference dependency added.

## v10 — Web response routing and chat-flow repair

- Keep direct identity/persona questions, language-switch instructions, and explicit stop requests local even when `/web always` is enabled.
- Added an explicit `stop_request` reply that acknowledges the boundary instead of searching for songs or unrelated topics.
- Send a web research digest as one Telegram message instead of delayed chunks that could interleave with later prompts.
- Track per-user turn generations so results from an older slow search are discarded after a newer message or web-mode change.
- Updated documentation and added regression tests for identity questions, stop requests, language controls, and explicit `/search` overrides.
- Validation: 94 targeted tests pass; dialogue validation passes. Full suite collection still requires `aiosqlite`.

## Web-inspired girlfriend replies (v8)

- Auto mode now searches common relationship prompts (for example, “I love you”, “I miss you”, compliments, comfort requests, apologies and good news) for matching reply inspiration.
- Added tailored second queries aimed at girlfriend-style replies rather than factual definitions.
- Romantic/social prompts now return one original emoji-rich local reply; retrieved titles/snippets only steer broad tone and are not copied into the response.
- If a web provider is unavailable, relationship chat falls back to local responses instead of failing or returning a research dump.
- Added regression tests for love-message routing, query shaping, output style and offline fallback.

## v7 — Hinglish research detection and search fallback

- Auto mode now recognizes informal Hinglish fact questions such as `ye shakespear kon h`, `kon hai Shakespeare`, and common variants of `kaun/kon`.
- Corrects common Shakespeare misspellings in the separate keyword query while preserving the full original prompt as the first search.
- Added a dependency-free DuckDuckGo HTML search fallback for systems where `ddgs` is not installed or its provider fails.
- Search failure no longer prints an extra warning and then a second unrelated fallback reply; the warning is combined with one local reply.
- Added regression tests for Hinglish detection, keyword cleanup and operation without the `ddgs` package.
- Validation: 84 non-database tests pass and dialogue validation passes. Full suite collection still requires `aiosqlite`.

# Changelog

## Version 28.1 — Friend/BF relationship access and role-safe chat (28 October 2026)

- Anyone can start a normal, platonic Friend-mode conversation without a pass. The original `OWNER_ID` and users who verify the shared `OWNER_CODE` receive BF-style companion replies.
- Added private-chat `/pass <code>` verification that stores only a BF-access flag, `/unpass`, `/role`, original-owner-only `/bfusers`, and persistent `/checkin 1-10`.
- Kept administrative authority attached strictly to `OWNER_ID`; passing the shared code changes companion tone only.
- Added a role-aware AI system prompt, deterministic Friend-mode fallback and platonic proactive greetings, including safe behavior for explicit `/search` prompts.
- Fixed broken startup syntax, repaired `/name`, supplied the missing `/reset` and `/owner` handlers, migrated existing databases to the new role column, fixed adult-mode column access, and corrected webhook startup/shutdown callbacks.
- Removed private runtime database/WAL and local conversation-learning data from the distributable archive. SQLite role schema is created/migrated on startup.
- Added role and Friend-mode regression tests. Full database tests require `aiosqlite`; they could not be run in the offline audit environment.

## Offline companion upgrade

- Added an intent-first dialogue manager for natural Hinglish greetings, wellbeing, kisses, playful innuendo, laughter, dark jokes, comfort and short follow-ups.
- Fixed message routing so memory extraction no longer interrupts normal replies.
- Replaced odd translated fallback phrases with concise, more natural prompts.
- Added a no-network terminal chat mode (`python -m aiko.offline`) and a local JSON fact store.
- Added local memory review, complete data deletion confirmation, JSON export, journal entries, reminders, jokes, riddles, rock-paper-scissors and personality-session settings.
- Added persistent reminder and journal tables to SQLite; reminder delivery retries after send errors.
- Applied the single-user access guard consistently to command handlers and callbacks.
- Made owner-only mode the default and require an `OWNER_ID` when enabled.
- Replaced bundled credential examples with placeholders and excluded runtime databases, `.env`, caches and bytecode from the release archive.
- Clarified that Bhawna is a fictional adult character, not a real person, and kept flirting suggestive rather than graphically explicit.
- Added architecture, testing and privacy docs plus dialogue/local-memory regression tests.

## Conversation flow repair

- Expanded direct conversational coverage to 62 curated intent rules across seven Python rule packs, with Hinglish, Devanagari Hindi and English response pools.
- Added explicit language switching for requests such as “Hinglish me baat kro na”, with a session preference that beats message-by-message language guesses.
- Added context-aware clarification for “Kis baare me?”, “what do you mean?”, and similar confusion turns.
- Added dedicated handling for “Areey”, short confirmations/denials, laughter plus affection, and other common Hinglish chat turns.
- Replaced confusing generic fallback prompts with conversational clarification prompts in all three language pools.
- Added expanded dialogue regression tests and `docs/DIALOGUE_RULES.md` for maintaining rule packs.

## v2.2 — October 2026 conversation repair

- Added a dedicated status-answer intent so `Acha hi hu ji` cannot trigger a YAML greeting because of the embedded word `hi`.
- Added contextual handling for acknowledgements, one-word typos, flirty emoji-only messages, and crying emoji-only messages.
- Added replies for direct adult-mode questions and explicit sexual innuendo. Responses explain that Aiko supports suggestive non-graphic flirting, not graphic sexual descriptions.
- Made `Yes` after a kiss stay in the kiss/consent context instead of returning a generic acknowledgement.
- Fixed the `18+` regex so the trailing plus sign no longer breaks the match.
- Added a separate persisted explicit language preference for Telegram users and local terminal mode, so short English phrases do not cancel a previously chosen Hinglish setting. Added a distinct thinking reaction for “Hmm”.
- Added regression tests for every conversation failure in the latest sample.


## v4 — Adult-flirty character tuning
- Made the fictional character's adult age (21) and roleplay status clearer.
- Expanded mature, consensual suggestive flirting and slow-burn romantic dialogue.
- Improved direct answers to questions about 18+ chat.
- Kept sexual descriptions non-graphic and added explicit respect/consent boundaries.

## v5 — Expanded responses and local learning brain

- Added a second wave of hand-written alternatives for common greetings, check-ins, hugs, kisses, love, missing someone, compliments, flirting, adult suggestive banter, dark humor and goodnight replies in Hinglish, Hindi and English.
- Added `aiko/local_brain.py`, a small persistent JSON brain that learns explicit trigger → reply pairs per user, stores simple use counts, and can be cleared without erasing personal facts.
- Added teaching syntax: `teach: trigger => reply` (also accepts `learn this`, `learn:`, `remember this`, and `when I say`). In Telegram mode learned pairs are stored locally beside the configured database; offline mode uses `data/local_brain.json`.
- Added `/brain` and `/brainforget` to terminal mode, plus conversational brain status and forget commands.
- The brain never downloads a model, calls a cloud API, executes learned text, or rewrites source code. Improvements stay explicit, local and testable.
- Validation: 74 targeted tests pass. Full test collection still needs the `aiosqlite` dependency, which is missing in this build environment.

## v6 — Optional free web research

- Added free DDGS metasearch for factual prompts and user-specified `/search` queries.
- Searches the complete prompt plus a compact keyword query, then formats result snippets, source links, and a deterministic next-step note.
- Added `/web auto|always|off` in terminal and Telegram modes, with persistent per-profile settings.
- Web results are clearly labeled as snippets; there is no LLM, paid API, or autonomous source-code editing.
- Hardened response expansion loading to accept language dictionaries and flat/list payloads, avoiding the earlier `.items()` crash.
- Added tests for search routing, preference persistence, result formatting, and the expansion-loader regression.


## v9 — English web queries, Hinglish-first replies

- Web-search queries now use English phrasing for common Hinglish fact questions and English-language girlfriend-reply inspiration. English prompts are preserved as full-prompt searches; topic keywords are also searched separately.
- Removed Hinglish/Devanagari grammar from generated search queries where common patterns can be recognized; preserved proper names and technical terms.
- Made Hinglish the implicit primary response language even when a user writes an English message. Explicit Hindi/English selection still wins, and an explicit auto-detect mode remains available.
- Updated terminal and Telegram language preference handling plus regression coverage for English query construction.


## v11 — Context-aware reply inspiration and local conversation learning

- Added `aiko/conversation_learning.py`: persistent, per-profile bounded chat history, recurring topic counts, simple user reply-style preferences, and search-result/tone history. The learner does not train a model or rewrite source code.
- Passed relevant recent context and the fictional persona style into English reply-inspiration searches. The raw full transcript stays local; queries include a compact context summary and a shorter variant.
- Added context-sensitive follow-up intent detection, including “Dedo na bonus bhi” after a kiss exchange, so relationship messages return one Hinglish, emoji-rich reply instead of generic results for words such as “bonus” or “dedo.”
- Made `/web always` search non-factual chat for response inspiration, while factual questions still return compact result digests. Local identity questions, language/style settings, slash commands and stop requests are not auto-searched.
- Added `/context` and `/forgetchat` to inspect/clear local conversation learning in terminal and Telegram modes.
- Added regression tests for persistent context, search learning, contextual bonus-kiss replies, English query construction, and local controls.

## v12 — Affection follow-ups and direct comfort requests

- Added recognition for quick/phonetic Hinglish kiss follow-ups such as `Dedo na ek or 😉` when the preceding turns include a kiss. Web inspiration searches now receive a semantic “bonus kiss” description and noisy video results never appear in the reply.
- Added a dedicated `comfort` response intent and local `comfort_request` rule for prompts such as `Comfort dedo aap`, `comfort me`, and `mujhe comfort do`.
- Direct comfort replies give reassurance, a virtual hug and permission not to explain anything immediately; they do not ask for more context as their primary response.
- Irrelevant humorous search snippets and past learned tones cannot turn a direct comfort request into teasing.
- Added regression tests for the exact follow-up/comfort failures, including deliberately noisy search results.
- Validation: targeted conversational/search tests pass; full test collection still requires `aiosqlite`.


## v16 — Hinglish what-doing routing and FreeSerp diagnostics

- Fixed the exact report `Kya kr rhi h meri jaanu`: `kr`, `rhe/rhi/rha`, and contextually abbreviated `h` are normalized for matching without changing the original saved message.
- Expanded the direct `what_doing` intent to accept trailing pet names and common shortened forms.
- Exempted informal Hinglish `what are you doing?` messages from web search, including `/web always`, so ordinary girlfriend conversation stays local.
- Added `/web test` to terminal and Telegram. It checks FreeSerp using a fixed public Shakespeare query, without sending the user's chat, and gives safe diagnostic feedback. `/web status` remains a configuration-only view.
- Validation: 125 targeted non-database tests passed; dialogue validation and Python compilation passed. Live FreeSerp check from the build environment could not connect due to a network/DNS/TLS issue, so run `/web test` on the user's Windows PC to verify their connection.


## v18 — Universal Translator

- Added `/translate` to terminal and Telegram with auto source detection, target names/codes, explicit source/target syntax, provider status, supported-language examples, and a fixed-phrase connectivity test.
- Added a keyless translator provider chain: optional configured LibreTranslate-compatible HTTPS endpoint, then Google Translate's public web endpoint. No new runtime dependencies or chat AI model.
- Added bounded in-memory caching, 4,500-character input limit, request spacing, no-op same-language handling, and generic provider-failure messages that do not echo the prompt or raw HTTP errors.
- Translation is explicit-only; normal chat remains local/rule-based to preserve privacy, Hinglish personality, and response performance.

## v19 — Positive check-in and day-update repair

- Added a `status_good` matcher for reply variants such as `Me bhi thik hu babby 😚`, including short Hinglish forms and affectionate suffixes.
- Added a separate `day_update_good` intent for `Mera din bhi acha tha`, so Bhawna reacts to the user's good day instead of treating it as a question about her own day.
- Marked both message classes as local conversation in `auto` and `always` web modes, avoiding needless web calls and the generic search-composer fallback. Explicit `/search ...` still overrides local routing.
- Added regression coverage for the exact check-in sequence, common variations, and web-routing behavior.
- No new AI model, API, or runtime dependency added.
- Validation: 143 targeted non-database tests passed; dialogue validation and Python compilation passed. Live Telegram integration remains untested in this environment.

## v27 — Relationship and adult-conversation expansion

- Added 60 original relationship/GF-BF/adult-conversation intents to `aiko/conversation_library.json`, yielding 154 total intents and 1,107 total reply strings in Hinglish, Hindi, and English.
- Added 12 opt-in, multi-turn local scenes including cozy couple conversation, long-distance date, conflict repair, slow-burn romance, dark/gothic flirtation, first date, future planning, respectful breakup closure, consensual adult roleplay checks, intimacy-boundary dialogue, aftercare, and playful adult flirting.
- Adult-only scenarios are fictional, non-graphic, and consent-forward. Stop/pause and boundary requests end the scene immediately.
- Added a research and license register at `docs/RELATIONSHIP_AND_ADULT_CONVERSATION_RESEARCH.md`. No raw unlicensed Hinglish/roleplay dataset entries or external chatbot source code were copied.
- All added packs are local and require no language model, network request, or added dependency. Groq remains optional for unmatched prompts.

## v29 — Reliability, privacy controls, schedules and companion games

- Added schema version 5 with idempotent migration columns for per-user quiet-hour overrides, greeting preferences, automatic fact memory, and conversation-learning opt-outs. Existing profile values are no longer bulk-reset at startup.
- Added a validated pre-migration SQLite snapshot, rotating daily backups, an owner-only `/backup`, integrity checks, and a stop-the-bot restore/validate CLI (`scripts/backup_db.py`). Restore snapshots the current database before replacement.
- Hardened `/pass` with private-chat-only entry, deletion of passcode command messages when Telegram permits, persistent five-attempt/ten-minute throttling, and `/revoke <user_id>` for the original owner. BF role never grants admin rights.
- Added `/prefs` for language, IANA time zone, local quiet hours, scheduled greetings, fact memory and conversation learning; added `/privacy` and expanded per-user `/export` data.
- Expanded `/forgetall` and `/forgetchat` to clear per-user conversation context, learned replies, search preferences and in-memory language/intent state.
- Added deterministic per-user daily challenges, completion points, streak tracking, and persistent milestone badges, plus `/trivia` and `/triviaanswer`.
- Added AI provider outcome metrics, `/health`, and owner alerts after repeated complete AI-chain failures; ordinary chat remains on local fallback when providers fail.
- Webhook mode now requires `WEBHOOK_SECRET_TOKEN`, uses a neutral `/webhook` URL instead of exposing the Telegram bot token in the path, validates Telegram's secret header, and reports readiness only after initialization.
- Added `scripts/release_check.py` for syntax, rule, romance-bank, and full regression-suite checks.
- Validation in this build environment: Python compilation passed; 195 tests passed with `tests/test_database.py` excluded. The full suite could not be run because `aiosqlite` and `python-telegram-bot` are not installed and package-index networking is unavailable; live Telegram/webhook behavior remains unverified.
