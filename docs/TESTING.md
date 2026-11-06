# Testing checklist

Run `python -m pytest -q` after installing `requirements.txt`.

Important regression cases:

- `Hello ji` receives a greeting.
- `kaise ho` receives a wellbeing response.
- `Kha chodu 🌚` receives playful, non-graphic innuendo rather than a generic fallback.
- `baby kissi dedo` and `kiss dedo` receive a kiss response.
- `😂umwaahhh babby` receives an affectionate/laughing response.
- `kya huaa` receives a coherent clarification.
- A short answer such as `aap` after an affection prompt is treated as a follow-up.
- A sentence that saves a memory still receives a conversational response; memory saving must not interrupt normal chat.
- Unauthorized users are blocked consistently across commands and message handlers in single-user mode.
- `/forgetall` removes user records only after explicit confirmation.

Also manually test Telegram rate limits, quiet hours, scheduler restart behavior and database restore from backup before public deployment.

- Reminder creation validates duration and length; due reminders are retried after send errors.
- Journal entries are stored locally and deleted by confirmed journal clearing or `/forgetall`.

## Dialogue regression checks

The conversation-specific tests include language requests, context repair, greetings, short reactions, laughter, affectionate prompts, flirting, dark humor, and rule-pack validation:

```bash
python -m pytest -q tests/test_dialogue.py tests/test_dialogue_expanded.py tests/test_language.py
```

The full test suite includes SQLite integration and migration tests, so install all dependencies from `requirements.txt` before running `python -m pytest -q`.

Run the rule-pack validator to check direct-intent pools, duplicates and YAML loading without any network calls:

```bash
python scripts/check_dialogue_rules.py
```


### Universal translator smoke test (no private text)

In terminal or Telegram, run `/translate status`, then `/translate test`. The test translates the fixed sentence `Hello, how are you?` to Hindi and does not use chat history. To test target-language parsing without network access, use `/translate help` and verify examples such as `/translate Spanish | I love you, baby`, `/translate from Japanese to Hindi | こんにちは`, and `/translate fr | Bonjour`. Unit tests mock both translation providers and verify cache and fallback behavior.


### Optional Groq fallback tests

The Groq integration tests mock the HTTP endpoint and never require a real API key or send network traffic:

```bash
python -m pytest -q tests/test_groq_chat.py
```

Manual smoke test: configure `GROQ_API_KEY` in `.env` and send a novel everyday message that is not covered by a local rule. Then set `GROQ_ENABLED=false` and confirm local fallback still replies. A live call is optional and subject to the account's model access and rate limits.


## v29 release checklist

Use `python scripts/release_check.py` before publishing. It runs Python compilation, dialogue-rule validation, romance-bank validation, and the complete pytest suite. It fails the release check if dependencies are missing or any test fails.

Additional checks included by v29:

- `tests/test_v29_features.py`: valid/invalid IANA zones, quiet-hour intervals including cross-midnight ranges, deterministic daily challenge selection, streak continuity, SQLite snapshot/restore integrity, invalid backup rejection, and provider-failure alert cooldown behavior.
- `scripts/backup_db.py backup data/aiko.db --keep 7`: creates and integrity-validates a rotating snapshot.
- `scripts/backup_db.py validate data/backups/<backup-name>.sqlite3`: validates a snapshot.
- Stop the bot, then `scripts/backup_db.py restore <backup> data/aiko.db`: validates the source and staged restore, makes a pre-restore copy, and replaces the database atomically.
- Test `/pass` from a private chat, five incorrect attempts followed by the cooldown, `/revoke`, and verify the pass never grants owner-only commands.
- Set `/prefs timezone Asia/Kolkata`, `/prefs quiet 23-08`, `/prefs greetings off`, `/prefs memory off`, `/prefs learning off`; inspect `/prefs`, and verify no unwanted proactive greetings/context are generated.
- Test `/forgetall` in a non-production test account; verify SQLite records and per-user JSON preferences/context are removed.
- Live Telegram, AI-provider, and host filesystem persistence still require deployment-time smoke tests; local unit tests do not prove network or host availability.
