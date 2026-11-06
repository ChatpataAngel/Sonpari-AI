# -*- coding: utf-8 -*-
"""Fix indentation in bot.py after the gating block."""
import sys

with open('aiko/bot.py', 'r', encoding='utf-8') as f:
    src = f.read()

lines = src.split('\n')

# Fix lines 104-122 (0-indexed 103-121): change from 6-space to 4-space indent
# These are the pass-code user handling lines
for i in range(103, min(122, len(lines))):
    line = lines[i]
    # Remove leading whitespace and add 4-space indent
    stripped = line.lstrip(' ')
    lines[i] = '    ' + stripped

# Fix line 123 (0-indexed 122): the timestamp line
if 122 < len(lines):
    line = lines[122]
    stripped = line.lstrip(' ')
    lines[122] = '    ' + stripped

new_src = '\n'.join(lines)

with open('aiko/bot.py', 'w', encoding='utf-8') as f:
    f.write(new_src)

print('Indentation fixed OK')
print(f'Total lines: {len(lines)}')