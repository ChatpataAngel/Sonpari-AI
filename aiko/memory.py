from __future__ import annotations
import re, random
from datetime import datetime, timezone

FACT_PATTERNS = [
 (re.compile(r"\bmy name is (?P<value>[A-Za-z][A-Za-z '\-]{0,39})",re.I), "name"),
 (re.compile(r"\bcall me (?P<value>[A-Za-z][A-Za-z '\-]{0,39})",re.I), "name"),
 (re.compile(r"\bi(?:'m| am) (?P<value>[A-Za-z][A-Za-z '\-]{0,39})\b",re.I), "identity"),
 (re.compile(r"\bi (?:like|love|hate) (?P<value>[^.!?\n]{1,80})",re.I), "preference"),
 (re.compile(r"\bmy favorite (?P<key>[A-Za-z ]{2,30}) is (?P<value>[^.!?\n]{1,80})",re.I), None),
 (re.compile(r"\bi work at (?P<value>[^.!?\n]{1,80})",re.I), "workplace"),
 (re.compile(r"\bi work as (?P<value>[^.!?\n]{1,80})",re.I), "occupation"),
 (re.compile(r"\bi live in (?P<value>[^.!?\n]{1,80})",re.I), "location"),
 (re.compile(r"\bmy birthday is (?P<value>[^.!?\n]{1,40})",re.I), "birthday"),
 (re.compile(r"\bi have (?:a|an) (?P<value>[^.!?\n]{1,60})",re.I), "has"),
 (re.compile(r"\bi(?:'m| am) (?P<value>\d{1,3}) years old\b",re.I), "age"),
]
def extract_facts(message: str) -> list[tuple[str,str]]:
    found=[]
    for pattern, fixed_key in FACT_PATTERNS:
        m=pattern.search(message)
        if not m: continue
        value=" ".join(m.group("value").strip(" \t.,!?").split())
        if not value: continue
        key=(m.group("key").strip().lower().replace(" ","_") if "key" in m.groupdict() and m.groupdict().get("key") else fixed_key)
        if fixed_key == "preference":
            lower=message.lower()
            verb=re.search(r"\bi (like|love|hate)\b",lower)
            key=(verb.group(1) + "_") if verb else "preference_"
            key += value[:32].lower().replace(" ","_")
        if key == "identity" and value.lower() in {"sad","happy","tired","hungry","bored","angry","stressed","anxious","okay","fine","excited","sleepy"}:
            continue
        if key == "name" and len(value.split()) > 4: continue
        found.append((str(key),value))
    # preserve first key only, except separately keyed preferences/favorites
    dedup={}
    for key,value in found: dedup[key]=value
    return list(dedup.items())

class Memory:
    def __init__(self, db): self.db=db
    async def remember_from_message(self,user_id:int,message:str) -> list[tuple[str,str,str|None]]:
        changes=[]
        now=datetime.now(timezone.utc).isoformat()
        for key,value in extract_facts(message):
            old=await self.db.fetchone("SELECT value FROM facts WHERE user_id=? AND key=?",(user_id,key))
            if old and old["value"] == value: continue
            await self.db.execute("""INSERT INTO facts(user_id,key,value,created_at) VALUES(?,?,?,?)
            ON CONFLICT(user_id,key) DO UPDATE SET value=excluded.value,created_at=excluded.created_at""",(user_id,key,value,now))
            changes.append((key,value,old["value"] if old else None))
        return changes
    async def recall_random(self,user_id:int) -> str|None:
        rows=await self.db.fetchall("SELECT key,value FROM facts WHERE user_id=?",(user_id,))
        if not rows: return None
        row=random.choice(rows)
        return f"{row['key'].replace('_',' ')} is {row['value']}"
    async def recall_by_key(self,user_id:int,key:str) -> str|None:
        row=await self.db.fetchone("SELECT value FROM facts WHERE user_id=? AND key=?",(user_id,key.lower()))
        return row["value"] if row else None
    async def all_facts(self,user_id:int):
        return await self.db.fetchall("SELECT key,value FROM facts WHERE user_id=? ORDER BY key",(user_id,))
    async def forget(self,user_id:int):
        await self.db.execute("DELETE FROM facts WHERE user_id=?",(user_id,))
