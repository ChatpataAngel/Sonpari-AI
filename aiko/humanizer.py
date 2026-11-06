from __future__ import annotations
import asyncio, random, re
from collections import defaultdict, deque
from telegram.constants import ChatAction
class Humanizer:
    def __init__(self,max_length=180):
        self.max_length=max_length; self.recent=defaultdict(lambda:deque(maxlen=3))
    def vary(self,user_id:int,text:str)->str:
        # Re-roll is handled by the caller; this method remembers the chosen text.
        self.recent[user_id].append(text); return text
    def split(self,text:str)->list[str]:
        sentences=re.split(r"(?<=[.!?])\s+",text.strip())
        chunks=[]; current=""
        for sentence in sentences:
            if not sentence: continue
            if len(sentence)>self.max_length:
                parts=[sentence[i:i+self.max_length] for i in range(0,len(sentence),self.max_length)]
            else: parts=[sentence]
            for part in parts:
                if current and len(current)+1+len(part)<=self.max_length: current += " "+part
                else:
                    if current: chunks.append(current)
                    current=part
        if current: chunks.append(current)
        return chunks or [text[:self.max_length]]
    async def send(self, bot, chat_id:int, text:str, max_length:int|None=None, multi_message=False):
        max_length=max_length or self.max_length
        pieces=[p.strip() for p in text.split("|") if p.strip()] if multi_message and "|" in text else self.split(text) if len(text)>max_length else [text]
        for i,piece in enumerate(pieces):
            await bot.send_chat_action(chat_id=chat_id,action=ChatAction.TYPING)
            delay=min(0.6+len(piece)*0.035,4.0)+random.uniform(0.0,0.35)
            await asyncio.sleep(delay)
            await bot.send_message(chat_id=chat_id,text=piece)
            if i<len(pieces)-1: await asyncio.sleep(random.uniform(0.8,1.5))
