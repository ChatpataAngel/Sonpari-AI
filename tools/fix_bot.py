# -*- coding: utf-8 -*-
"""Fix bot.py to integrate JSON content loading for pass-code users."""
import re

with open('aiko/bot.py', 'r', encoding='utf-8') as f:
    src = f.read()

lines = src.split('\n')

# 1. Add import for offline_data after conversation_learning import
for i, line in enumerate(lines):
    if line.strip() == 'from .conversation_learning import LocalConversationLearning':
        # Insert after this line
        lines.insert(i + 1, 'from .offline_data import get_friendly_chat, pick')
        break

# 2. Find and modify the gating section
# Look for the pattern: has_pass = bool(row and row["pass_code"])
# and is_owner = (settings.owner_id is not None and uid==settings.owner_id)
# and the if not is_owner and not has_pass block

# We need to add pass-code user handling after the gating block
# Find "# ─── End gating; normal flow continues" 
for i, line in enumerate(lines):
    if '# ─── End gating; normal flow continues' in line:
        # Insert pass-code user handling BEFORE this line
        # The code block needs proper indentation
        pass_code_block = [
            '    # Pass-code users (but not owner) get friendly JSON-based chat, NOT BF talk',
            '    is_pass_user = (has_pass and not is_owner)',
            '    if is_pass_user:',
            '        # Pick a friendly response from the JSON content',
            '        lang = dialogue.effective_language(user.id, lang)',
            '        segment = random.choice(list(get_friendly_chat().keys()))',
            '        response = pick(segment, lang)',
            '        if response:',
            '            # Add a friendly note that this is a friend-mode reply',
            '            full_response = f"Friend mode: {response}"',
            '            await update.effective_message.reply_text(full_response)',
            '            # Save to conversation learning',
            '            conversation_learning = app.bot_data.get("conversation_learning")',
            '            if conversation_learning:',
            '                conversation_learning.observe(user.id, "assistant", full_response)',
            '            # Log the message',
            '            await db.log_message(user.id, "bot", "friendly_json", response)',
            '            # Skip normal dialogue routing',
            '            return',
        ]
        # Insert in reverse order so they appear in correct order
        for line in reversed(pass_code_block):
            lines.insert(i, line)
        break

with open('aiko/bot.py', 'w', encoding='utf-8') as f:
    f.write('\n'.join(lines))

print('bot.py modified OK')