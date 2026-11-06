"""Small JSON memory store for the no-network terminal mode."""
from __future__ import annotations
import json
from pathlib import Path
from .memory import extract_facts

class LocalMemory:
    def __init__(self, path: str | Path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.data: dict[str, str] = {}
        if self.path.exists():
            try:
                loaded = json.loads(self.path.read_text(encoding="utf-8"))
                if isinstance(loaded, dict):
                    self.data = {str(k): str(v) for k, v in loaded.items()}
            except (OSError, json.JSONDecodeError):
                # A damaged memory file should not stop the chat from starting.
                self.data = {}

    def remember(self, message: str) -> list[tuple[str, str]]:
        changes=[]
        for key, value in extract_facts(message):
            if self.data.get(key) != value:
                self.data[key] = value
                changes.append((key,value))
        if changes:
            self._save()
        return changes

    def all(self) -> dict[str, str]:
        return dict(self.data)

    def forget(self) -> None:
        self.data.clear()
        self._save()

    def _save(self) -> None:
        self.path.write_text(json.dumps(self.data, ensure_ascii=False, indent=2), encoding="utf-8")
