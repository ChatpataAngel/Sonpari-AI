<div align="center">

# 🧞‍♀️ Sonpari-AI

**A local-first Telegram companion — casual Hinglish conversations, thoughtful privacy controls, and a friendly, non-romantic persona.**

[![Python](https://img.shields.io/badge/python-3.11%2B-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![Telegram Bot API](https://img.shields.io/badge/Telegram-Bot%20API-26A5E4?logo=telegram&logoColor=white)](https://core.telegram.org/bots/api)
[![License](https://img.shields.io/badge/license-All%20Rights%20Reserved-critical)](#-license)

<sub>Internal project name: <code>Sonpari</code> &nbsp;•&nbsp; Production bot name: <code>Sonpari-AI</code></sub>

</div>

---

## ✨ Overview

Sonpari-AI is a companion bot built for relaxed, everyday conversations in Hinglish. It supports:

- 💬 Casual, preference-aware chat with a friendly persona
- 🔒 User-controlled privacy and data settings
- ⏰ Reminders and daily check-ins
- 🌤️ Mood tracking and daily challenges
- 🧠 Quizzes and lightweight games
- 📴 Offline-friendly response logic for the conversation engine

> **Note on "offline":** The bot still requires Telegram's Bot API to communicate with Telegram. The conversation engine is designed to work locally — but inspect the optional modules and deployment configuration before describing the whole application as fully offline.

---

## 👤 Creator

**Created and developed by Chatpata Angel**

| Platform | Handle |
| :-- | :-- |
| GitHub | [@chatpataangel](https://github.com/chatpataangel) |
| Instagram | [@chatpatadevpoppy](https://instagram.com/chatpatadevpoppy) |
| Telegram | [@drangeljangra](https://t.me/drangeljangra) |

---

## ⚠️ Edition Notes

This public release is branded as **Sonpari-AI** and ships with a **friendly, non-romantic companion persona**.

The following have been **disabled or removed** from this release:

- Adult-mode commands
- Relationship-scene handling
- The former romance retrieval dataset

---

## 🚀 Quick Start

1. **Install** Python 3.11 or newer.
2. **Configure** — copy `.env.example` to a private `.env` file.
3. **Set** `TELEGRAM_BOT_TOKEN` using a token created via Telegram's official [BotFather](https://t.me/BotFather).
4. **Set** `OWNER_ID` to your numeric Telegram user ID.
5. **Install dependencies:**
   ```bash
   python -m pip install -r requirements.txt
Run the bot:

bash
python run.py
🚫 Never commit .env, database files, logs, backups, or real user data.

🔐 Data & Privacy
Runtime databases and conversation-learning files are intentionally excluded from this repository.

Message-content logging is disabled by default.

Review docs/PRIVACY.md and the implementation before deploying to real users.

Rotate any credential that has ever appeared in a shared archive or public repository.

🧪 Testing
bash
python -m pip install -r requirements.txt
python scripts/check_dialogue_rules.py
python -m compileall -q aiko run.py
python -m pytest -q
A successful compile or dialogue-data check does not guarantee every workflow is production-verified. Always review the test output and deployment configuration.

📄 License
All Rights Reserved.

No permission is granted to copy, modify, redistribute, sublicense, or commercially use this project without prior written permission from the copyright holder.

© 2026 Chatpata Angel. All rights reserved.

text

### What changed and why

| Change | Benefit |
| :-- | :-- |
| **Centered header + badges** | Instantly signals "real project"; badges render on GitHub automatically |
| **Explicit `Overview` section** | Turns scattered feature mentions into a scannable list |
| **Blockquote callouts** | Draws the eye to the important caveats (offline claim, secret-handling) |
| **Creator as a table** | Cleaner than a bullet list, aligned handles |
| **Numbered Quick Start** | Reads like a proper setup guide rather than a checklist |
| **Edition Notes as its own section** | Legal/scope warnings deserve to be visible, not buried |
| **Consistent emoji use** | Stylish but restrained — one icon per section header only |
| **Footer copyright** | Reinforces the "All Rights Reserved" license with a clean closing line |

### Optional polish you could add later

- A **screenshot or demo GIF** right under the title (biggest single upgrade for a bot repo).
- A **`## Features`** table if you want more detail per capability.
- **GitHub Actions status badge** once you wire up CI.
- A short **`## Contributing`** note stating the project is not accepting contributions (matches your license).
