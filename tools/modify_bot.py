# -*- coding: utf-8 -*-
"""Modify bot.py to integrate JSON content loading for pass-code users."""
import json

src = open('aiko/bot.py', encoding='utf-8').read()

# 1. Add import for offline_data after existing imports
# Find the line with "from .conversation_learning import LocalConversationLearning"
# and add the offline_data import after it
import_marker = "from .conversation_learning import LocalConversationLearning"
import_addition = """from .conversation_learning import LocalConversationLearning

from .offline_data import get_friendly_chat, pick"""

src = src.replace(import_marker, import_addition)

# 2. After the gating block, add pass-code user routing
# Find "# ─── End gating; normal flow continues" and add code before it
old_section = """# ─── End gating; normal flow continues ────────────────────────────────────
    timestamp=datetime.now(timezone.utc).isoformat()"""

new_section = """# ─── End gating; normal flow continues ────────────────────────────────────
      # Pass-code users (but not owner) get friendly JSON-based chat, NOT BF talk
      is_pass_user = (has_pass and not is_owner)
      if is_pass_user:
          # Pick a friendly response from the JSON content
          lang = dialogue.effective_language(user.id, lang)
          segment = random.choice(list(get_friendly_chat().keys()))
          response = pick(segment, lang)
          if response:
              # Add a friendly note that this is a friend-mode reply
              full_response = f"Friend mode: {response}"
              await update.effective_message.reply_text(full_response)
              # Save to conversation learning
              conversation_learning = app.bot_data.get('conversation_learning')
              if conversation_learning:
                  conversation_learning.observe(user.id, 'assistant', full_response)
              # Log the message
              await db.log_message(user.id, 'bot', 'friendly_json', response)
              # Skip normal dialogue routing
              return
      timestamp=datetime.now(timezone.utc).isoformat()"""

src = src.replace(old_section, new_section)

with open('aiko/bot.py', 'w', encoding='utf-8') as f:
    f.write(src)

print('bot.py modified OK')