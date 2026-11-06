"""Small persistent, offline learning layer for Aiko.

It learns explicit user-approved phrase -> reply pairs and keeps lightweight
usage counts. It never edits Python code, downloads models, or executes learned text.
"""
from __future__ import annotations
import json
import re
from pathlib import Path
from .text_style import normalize_for_matching

class LocalBrain:
    def __init__(self, path: str | Path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.data = {"learned": {}, "stats": {}}
        try:
            loaded = json.loads(self.path.read_text(encoding="utf-8")) if self.path.exists() else {}
            if isinstance(loaded, dict):
                self.data["learned"] = loaded.get("learned", {}) if isinstance(loaded.get("learned", {}), dict) else {}
                self.data["stats"] = loaded.get("stats", {}) if isinstance(loaded.get("stats", {}), dict) else {}
        except (OSError, json.JSONDecodeError):
            pass

    @staticmethod
    def normalize(text: str) -> str:
        return re.sub(r"\s+", " ", normalize_for_matching(text).casefold().strip().strip(".!? "))

    def learn(self, trigger: str, reply: str, user_id: int | str = "local") -> bool:
        trigger, reply = trigger.strip(), reply.strip()
        if not trigger or not reply or len(trigger) > 180 or len(reply) > 600:
            return False
        key = f"{user_id}:{self.normalize(trigger)}"
        self.data["learned"][key] = {"trigger": trigger, "reply": reply, "uses": 0}
        self._save()
        return True

    def match(self, message: str, user_id: int | str = "local") -> str | None:
        normalized = self.normalize(message)
        # User-specific knowledge first; local terminal profile is the fallback.
        for key in (f"{user_id}:{normalized}", f"local:{normalized}"):
            item = self.data["learned"].get(key)
            if isinstance(item, dict) and item.get("reply"):
                item["uses"] = int(item.get("uses", 0)) + 1
                self.data["stats"][key] = int(self.data["stats"].get(key, 0)) + 1
                self._save()
                return str(item["reply"])
        return None

    def count(self, user_id: int | str = "local") -> int:
        prefix = f"{user_id}:"
        return sum(1 for key in self.data["learned"] if key.startswith(prefix))

    def forget(self, user_id: int | str = "local") -> None:
        prefix = f"{user_id}:"
        self.data["learned"] = {k:v for k,v in self.data["learned"].items() if not k.startswith(prefix)}
        self.data["stats"] = {k:v for k,v in self.data["stats"].items() if not k.startswith(prefix)}
        self._save()

    def _save(self) -> None:
        tmp = self.path.with_suffix(self.path.suffix + ".tmp")
        tmp.write_text(json.dumps(self.data, ensure_ascii=False, indent=2), encoding="utf-8")
        tmp.replace(self.path)
