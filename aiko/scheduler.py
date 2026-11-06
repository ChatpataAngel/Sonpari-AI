from __future__ import annotations
import random
from datetime import datetime, timezone
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError
from .mood import decay_inactive
from .utils import time_of_day
from .relationship import local_friend_greeting
class ProactiveScheduler:
    def __init__(self,db,engine,persona,settings,humanizer):
        self.db,self.engine,self.persona,self.settings,self.humanizer=db,engine,persona,settings,humanizer
    def _local_now(self, row):
        zone=(row["timezone"] if row and row["timezone"] else self.persona.get("timezone","UTC"))
        try: return datetime.now(ZoneInfo(zone))
        except (ZoneInfoNotFoundError,ValueError): return datetime.now(timezone.utc)
    def _quiet(self, local, row=None):
        # Per-user values override deployment-wide defaults. NULL disables the
        # per-user override, not the global quiet-hours policy.
        override = bool(row["quiet_override"]) if row is not None and "quiet_override" in row.keys() else False
        start = row["quiet_start"] if row is not None and "quiet_start" in row.keys() else None
        end = row["quiet_end"] if row is not None and "quiet_end" in row.keys() else None
        if override and (start is None or end is None):
            return False  # user explicitly opted out of quiet hours
        if not override:
            start,end=self.settings.quiet_hours_start,self.settings.quiet_hours_end
        return start <= local.hour < end if start < end else (local.hour >= start or local.hour < end)
    def _greeting_variants(self, kind, lang):
        # Prefer language-specific greeting overrides, fall back to English.
        if lang in ("hi","hinglish"):
            v=self.persona.get(f"greeting_overrides_{lang}") or {}
            if v.get(kind): return v[kind]
        return self.persona.get("greeting_overrides",{}).get(kind,[])
    async def proactive_check(self, context):
        if not self.settings.enable_proactive: return
        users=await self.db.fetchall("SELECT * FROM users WHERE proactive_enabled=1")
        now=datetime.now(timezone.utc)
        for row in users:
            local=self._local_now(row)
            if self._quiet(local,row): continue
            last=row["last_proactive"]
            if last:
                try:
                    last_dt=datetime.fromisoformat(last)
                    if last_dt.tzinfo is None: last_dt=last_dt.replace(tzinfo=timezone.utc)
                    elapsed=(now-last_dt).total_seconds()/60
                except ValueError: elapsed=999999
            else:
                # Do not proactively contact new users before a meaningful interaction.
                continue
            threshold=random.randint(self.settings.proactive_min_interval_minutes,self.settings.proactive_max_interval_minutes)
            if elapsed < threshold: continue
            lang=(row["lang"] if row["lang"] else "en")
            is_bf = (self.settings.owner_id is not None and row["user_id"] == self.settings.owner_id) or bool(row["bf_access"])
            if is_bf:
                pool=self.engine._proactive_for(lang)
                text=self.engine.render(random.choice(pool),{"name":row["display_name"] or "baby","mood":row["mood"],"time_of_day":time_of_day(local.hour)},lang=lang)
            else:
                text = local_friend_greeting("checkin", lang)
            try:
                await self.humanizer.send(context.bot,row["user_id"],text)
                await self.db.execute("UPDATE users SET last_proactive=? WHERE user_id=?",(now.isoformat(),row["user_id"]))
            except Exception: continue
    async def daily_tasks(self, context):
        await decay_inactive(self.db)
        # Keep a rotating set of validated local snapshots. Backups are never
        # packaged into releases and remain on the host's persistent disk only.
        import asyncio, logging
        from pathlib import Path
        from .backup import create_backup
        db_path = Path(self.db.path)
        try:
            await asyncio.to_thread(create_backup, db_path, db_path.parent / "backups", 7)
        except Exception as exc:
            logging.getLogger(__name__).error("Automatic database backup failed (%s)", type(exc).__name__)
            owner_id = getattr(self.settings, "owner_id", None)
            if owner_id:
                try:
                    await context.bot.send_message(owner_id, "⚠️ AIKO could not create its daily database backup. Check server storage and logs; your existing database was not intentionally modified.")
                except Exception:
                    pass
    async def reminder_check(self, context):
        """Deliver due user-created reminders; retry naturally if sending fails."""
        now=datetime.now(timezone.utc).isoformat()
        rows=await self.db.fetchall("SELECT id,user_id,message FROM reminders WHERE sent=0 AND due_at<=? ORDER BY due_at LIMIT 50",(now,))
        for row in rows:
            try:
                await context.bot.send_message(chat_id=row["user_id"],text="⏰ reminder time, ji: " + row["message"])
                await self.db.execute("UPDATE reminders SET sent=1 WHERE id=?",(row["id"],))
            except Exception:
                # Keep sent=0 so a transient Telegram failure can be retried.
                continue
    async def greeting_check(self, context):
        if not self.settings.enable_proactive: return
        rows=await self.db.fetchall("SELECT * FROM users WHERE proactive_enabled=1")
        for row in rows:
            if "greetings_enabled" in row.keys() and not row["greetings_enabled"]: continue
            local=self._local_now(row); hour=local.hour
            kind="morning" if 8<=hour<10 else ("night" if 22<=hour<23 else None)
            if not kind or self._quiet(local,row): continue
            day=local.date().isoformat()
            exists=await self.db.fetchone("SELECT 1 FROM daily_greetings WHERE user_id=? AND day=? AND kind=?",(row["user_id"],day,kind))
            if exists: continue
            lang=(row["lang"] if row["lang"] else "en")
            is_bf = (self.settings.owner_id is not None and row["user_id"] == self.settings.owner_id) or bool(row["bf_access"])
            if is_bf:
                variants=self._greeting_variants(kind,lang)
                if not variants:
                    continue
                text=self.engine.render(random.choice(variants),{"name":row["display_name"] or "baby","mood":row["mood"],"time_of_day":kind},lang=lang)
            else:
                text = local_friend_greeting("morning" if kind == "morning" else "night", lang)
            try:
                await self.humanizer.send(context.bot,row["user_id"],text)
                await self.db.execute("INSERT OR IGNORE INTO daily_greetings(user_id,day,kind) VALUES(?,?,?)",(row["user_id"],day,kind))
            except Exception: pass
