# Sonpari-AI

**Internal project name:** Sonpari  
**Production bot name:** Sonpari-AI

A local-first Telegram companion with casual Hinglish conversations, preferences, privacy controls, reminders, mood check-ins, daily challenges, quizzes, and offline-friendly response logic.

## Creator

**Created and developed by Chatpata Angel**

- GitHub: [@chatpataangel](https://github.com/chatpataangel)
- Instagram: [@chatpatadevpoppy](https://instagram.com/chatpatadevpoppy)
- Telegram: [@drangeljangra](https://t.me/drangeljangra)

## Important edition notes

This public release is branded as Sonpari-AI and uses a friendly, non-romantic companion persona. Adult-mode commands, relationship-scene handling, and the former romance retrieval dataset have been disabled or removed from this release.

The bot still requires Telegram's Bot API to communicate with Telegram. The conversation engine is designed to work locally; inspect optional modules and deployment settings before describing the whole application as fully offline.

## Quick start

1. Install Python 3.11 or newer.
2. Create a private `.env` from `.env.example`.
3. Set `TELEGRAM_BOT_TOKEN` using a token created with Telegram's official BotFather.
4. Set `OWNER_ID` to your numeric Telegram user ID.
5. Install dependencies: `python -m pip install -r requirements.txt`
6. Start: `python run.py`

Never commit `.env`, database files, logs, backups, or real user data.

## Data and privacy

- Runtime database and conversation-learning files are intentionally excluded from this repository.
- Message-content logging is disabled by default.
- Review `docs/PRIVACY.md` and the implementation before deploying to real users.
- Rotate any credential that has ever been included in a shared archive or public repository.

## Testing

Run:

```bash
python -m pip install -r requirements.txt
python scripts/check_dialogue_rules.py
python -m compileall -q aiko run.py
python -m pytest -q
```

A successful compile or dialogue-data check does not mean every workflow is production-verified. Check the test output and deployment configuration.

## License

All Rights Reserved. No permission is granted to copy, modify, redistribute, sublicense, or commercially use this project without prior written permission from the copyright holder.

Copyright (c) 2026 Chatpata Angel. All rights reserved.
