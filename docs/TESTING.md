<div align="center">

# 🧪 Testing Checklist

**How to verify Sonpari-AI before you ship it.**

</div>

---

## ⚡ Quick Run

```bash
python -m pip install -r requirements.txt
python -m pytest -q
```

---

## 🎯 Regression Cases

Every one of these must pass — they're the phrases users actually type.

| Input | Expected behavior |
| :-- | :-- |
| `Hello ji` | Greeting response |
| `kaise ho` | Wellbeing response |
| `Kha chodu 🌚` | Playful, non-graphic innuendo — not a generic fallback |
| `baby kissi dedo` / `kiss dedo` | Kiss response |
| `😂umwaahhh babby` | Affectionate / laughing response |
| `kya huaa` | Coherent clarification |
| `aap` after affection prompt | Treated as follow-up |
| Memory-saving sentence | Still receives conversational reply — saving must not interrupt chat |
| Unauthorized user (single-user mode) | Blocked consistently across commands and handlers |
| `/forgetall` | Removes records **only** after explicit confirmation |

---

## 🛠️ Manual Tests Before Public Deployment

- [ ] Telegram rate limits
- [ ] Quiet hours
- [ ] Scheduler restart behavior
- [ ] Database restore from backup

### Additional Checks

- [ ] Reminder creation validates duration and length
- [ ] Due reminders retry after send errors
- [ ] Journal entries store locally and are deleted by confirmed journal clearing or `/forgetall`

---

## 💬 Dialogue Regression Suite

```bash
python -m pytest -q tests/test_dialogue.py tests/test_dialogue_expanded.py tests/test_language.py
```

Covers: language requests, context repair, greetings, short reactions, laughter, affectionate prompts, flirting, dark humor, and rule-pack validation.

> The **full** suite also includes SQLite integration and migration tests — install all of `requirements.txt` before running `python -m pytest -q`.

### Rule-pack validator (no network)

```bash
python scripts/check_dialogue_rules.py
```

Checks direct-intent pools, duplicates, and YAML loading.

---

## 🌐 Universal Translator Smoke Test

> ⚠️ **No private text** — the test uses a fixed sentence.

In terminal or Telegram:

1. `/translate status`
2. `/translate test` — translates `Hello, how are you?` to Hindi (no chat history used)

### Target-language parsing (offline)

Use `/translate help`, then verify:

- `/translate Spanish | I love you, baby`
- `/translate from Japanese to Hindi | こんにちは`
- `/translate fr | Bonjour`

> Unit tests mock both translation providers and verify cache and fallback behavior.

---

## 🤖 Optional Groq Fallback Tests

Groq tests **mock** the HTTP endpoint — no real API key or network traffic.

```bash
python -m pytest -q tests/test_groq_chat.py
```

### Manual smoke test

1. Set `GROQ_API_KEY` in `.env`
2. Send a novel everyday message not covered by local rules
3. Set `GROQ_ENABLED=false`
4. Confirm local fallback still replies

> A live call is optional and subject to account model access and rate limits.

---

## 🚀 v29 Release Checklist

Run before publishing:

```bash
python scripts/release_check.py
```

Runs Python compilation, dialogue-rule validation, romance-bank validation, and the full pytest suite. **Fails** if dependencies are missing or any test fails.

### v29-specific automated checks

`tests/test_v29_features.py` covers:

- Valid / invalid IANA zones
- Quiet-hour intervals (including cross-midnight)
- Deterministic daily challenge selection
- Streak continuity
- SQLite snapshot / restore integrity
- Invalid backup rejection
- Provider-failure alert cooldown

### Backup & restore

```bash
# Create and validate a rotating snapshot
scripts/backup_db.py backup data/aiko.db --keep 7

# Validate a snapshot
scripts/backup_db.py validate data/backups/<backup-name>.sqlite3

# Restore (stop the bot first)
scripts/backup_db.py restore <backup> data/aiko.db
```

> Restore validates source and staged restore, makes a pre-restore copy, and replaces the database atomically.

### Manual release walkthrough

- [ ] `/pass` from a private chat — five incorrect attempts, verify cooldown, then `/revoke`
- [ ] Confirm the pass **never** grants owner-only commands
- [ ] Set `/prefs timezone Asia/Kolkata`, `/prefs quiet 23-08`, `/prefs greetings off`, `/prefs memory off`, `/prefs learning off`
- [ ] Inspect `/prefs` — verify no unwanted proactive greetings / context
- [ ] `/forgetall` in a non-production test account — verify SQLite records **and** per-user JSON preferences / context are removed

> 🚨 **Live Telegram, AI-provider, and host filesystem persistence still require deployment-time smoke tests.** Local unit tests do not prove network or host availability.

---

<div align="center">
<sub>See <code>ARCHITECTURE.md</code> for the message flow these tests exercise.</sub>
</div>
