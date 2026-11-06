"""Persistent local conversation context and lightweight experience learning.

This is memory, not a trained model: it stores a bounded chat history, topic
frequency, simple style preferences, and summaries of prior web searches. Full
text stays on disk locally; web search receives only a compact relevant summary.
"""
from __future__ import annotations

import json
import re
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .text_style import detect_texting_style

_STOPWORDS = set("""the and for are but not you your you're she her his him they them this that with from have has had was were what when where why how who can could would should please thanks thank hello hi hey baby babe bubu jaan ji kya kon kaun hai hain ho hun hoon mai main mein mujhe tum tumse tumhe tumhara tumhari tumhare mera meri mere aur bhi na ab phir ek toh to ke ki ka par se mein me we our us it its i am do did does be been being a an of in on at as is or if so then just very really only all too much many more most some any all now today yesterday tomorrow""".split())
_COMMANDS = ("/web", "/search", "/help", "/quit", "/exit", "/memory", "/forget", "/brain", "/brainforget", "/mood", "/kiss", "/joke")
_SECRET_PATTERNS = (
    re.compile(r"\b(?:password|passwd|api[_ -]?key|token|secret)\s*[:=]?\s*\S+", re.I),
    re.compile(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", re.I),
    re.compile(r"\b(?:\+?\d[\d ()-]{8,}\d)\b"),
)


def _stamp() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _safe_local_text(value: Any, limit: int = 900) -> str:
    text = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]", " ", str(value or ""))
    return re.sub(r"\s+", " ", text).strip()[:limit]


def _web_safe_summary(value: Any, limit: int = 160) -> str:
    """Redact obvious secrets and contact details before creating web context."""
    text = _safe_local_text(value, 500)
    for pattern in _SECRET_PATTERNS:
        text = pattern.sub("[private detail removed]", text)
    # Don't pass long numeric identifiers, paths, or pasted stack traces to search.
    text = re.sub(r"\b\d{6,}\b", "[number removed]", text)
    text = re.sub(r"(?:[A-Za-z]:\\|/home/|/Users/)[^ ]+", "[local path removed]", text)
    return text[:limit].rstrip()


class LocalConversationLearning:
    """Bounded local memory of chats, topics, reply preferences and searches."""

    def __init__(self, path: str | Path, max_messages: int = 120):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.max_messages = max(20, int(max_messages))
        self._lock = threading.RLock()
        self.data: dict[str, Any] = {"version": 1, "users": {}}
        try:
            loaded = json.loads(self.path.read_text(encoding="utf-8")) if self.path.exists() else {}
            if isinstance(loaded, dict) and isinstance(loaded.get("users", {}), dict):
                self.data["users"] = loaded.get("users", {})
        except (OSError, json.JSONDecodeError):
            # Damaged local context should never stop the bot from starting.
            self.data["users"] = {}

    def _user(self, user_id: int | str) -> dict[str, Any]:
        users = self.data.setdefault("users", {})
        key = str(user_id)
        current = users.get(key)
        if not isinstance(current, dict):
            current = {"messages": [], "topics": {}, "preferences": {}, "searches": []}
            users[key] = current
        current.setdefault("messages", [])
        current.setdefault("topics", {})
        current.setdefault("preferences", {})
        current.setdefault("searches", [])
        return current

    def observe(self, user_id: int | str, role: str, text: str) -> None:
        role = "assistant" if role in {"assistant", "bot", "aiko", "bhawna"} else "user"
        text = _safe_local_text(text)
        if not text or (role == "user" and text.startswith(_COMMANDS)):
            return
        with self._lock:
            user = self._user(user_id)
            messages = user["messages"]
            # Avoid duplicate turns when platform retries an update.
            if messages and messages[-1].get("role") == role and messages[-1].get("text") == text:
                return
            messages.append({"role": role, "text": text, "at": _stamp()})
            user["messages"] = messages[-self.max_messages:]

            if role == "user":
                for token in re.findall(r"[a-zA-Z][a-zA-Z'-]{2,}", text.casefold()):
                    if token not in _STOPWORDS and token not in {"baby", "babe", "bubu", "jaan", "angel", "bhawna"}:
                        user["topics"][token] = min(999, int(user["topics"].get(token, 0)) + 1)
                # Learn message-format preferences (not personal attributes) so replies can
                # mirror the user's own short forms and expressive stretched letters.
                prefs = user["preferences"]
                texting_style = detect_texting_style(text)
                if texting_style.get("elongated_spelling"):
                    prefs["elongated_spelling"] = "on"
                if texting_style.get("short_forms"):
                    prefs["short_forms"] = "on"
                if re.search(r"\b(?:shorter|short reply|keep it short|briefly|short mein|chhota sa|thoda short)\b", text, re.I):
                    prefs["reply_length"] = "short"
                elif re.search(r"\b(?:longer|more detail|explain more|detail mein)\b", text, re.I):
                    prefs["reply_length"] = "normal"
                if re.search(r"\b(?:hinglish bolo|speak hinglish|reply in hinglish|hinglish mein)\b", text, re.I):
                    prefs["reply_language"] = "hinglish"
                elif re.search(r"\b(?:reply in english|speak english|english bolo)\b", text, re.I):
                    prefs["reply_language"] = "en"
                if re.search(r"\b(?:more emojis|add emojis|emoji zyada|zyada emojis)\b", text, re.I):
                    prefs["emoji_frequency"] = "high"
            # Bound topic vocabulary and search log to prevent unbounded files.
            if len(user["topics"]) > 120:
                user["topics"] = dict(sorted(user["topics"].items(), key=lambda kv: kv[1], reverse=True)[:90])
            self._save_locked()

    def context_for(self, user_id: int | str, max_messages: int = 12) -> dict[str, Any]:
        with self._lock:
            user = self._user(user_id)
            messages = user.get("messages", [])
            # Return copies so the caller cannot mutate our data outside the lock.
            recent = [dict(item) for item in messages[-max(2, min(24, max_messages)):]]
            topics = sorted(user.get("topics", {}).items(), key=lambda kv: int(kv[1]), reverse=True)[:12]
            searches = [dict(item) for item in user.get("searches", [])[-5:]]
            return {
                "recent_messages": recent,
                "topics": [key for key, _count in topics],
                "preferences": dict(user.get("preferences", {})),
                "recent_searches": searches,
            }

    def record_search(
        self,
        user_id: int | str,
        prompt: str,
        queries: list[str],
        results: list[dict[str, str]],
        intent: str | None,
        reply: str | None = None,
        failed: bool = False,
    ) -> None:
        with self._lock:
            user = self._user(user_id)
            source_text = " ".join(f"{x.get('title', '')} {x.get('body', '')}" for x in results).casefold()
            if re.search(r"\b(?:funny|humor|humour|witty|playful|teasing|joke)\b", source_text):
                tone = "playful"
            elif re.search(r"\b(?:flirty|romantic|affectionate|sweet)\b", source_text):
                tone = "flirty"
            else:
                tone = "sweet"
            item = {
                "at": _stamp(),
                "intent": _safe_local_text(intent or "research", 40),
                "prompt_summary": _web_safe_summary(prompt, 100),
                "queries": [_web_safe_summary(q, 180) for q in queries[:3]],
                "titles": [_web_safe_summary(x.get("title", ""), 100) for x in results[:3] if x.get("title")],
                "tone": tone,
                "success": bool(results) and not failed,
                "failed": bool(failed),
            }
            user["searches"].append(item)
            user["searches"] = user["searches"][-20:]
            # Search history itself becomes learned context for future searches.
            if item["success"]:
                user["topics"][item["intent"]] = min(999, int(user["topics"].get(item["intent"], 0)) + 1)
            self._save_locked()

    def summary(self, user_id: int | str) -> str:
        """Human-readable short summary, handy for /brain or debugging."""
        ctx = self.context_for(user_id)
        topics = ", ".join(ctx["topics"][:8]) or "no repeated topics yet"
        searches = len(ctx["recent_searches"])
        return f"Recent local context: {len(ctx['recent_messages'])} messages; recurring topics: {topics}; recent searches logged: {searches}."

    def export_user(self, user_id: int | str) -> dict[str, Any]:
        """Return a detached copy of the data stored for one user."""
        import copy
        with self._lock:
            user = self.data.get("users", {}).get(str(user_id), {})
            return copy.deepcopy(user) if isinstance(user, dict) else {}

    def forget(self, user_id: int | str) -> None:
        with self._lock:
            self.data.setdefault("users", {}).pop(str(user_id), None)
            self._save_locked()

    def _save_locked(self) -> None:
        try:
            tmp = self.path.with_suffix(self.path.suffix + ".tmp")
            tmp.write_text(json.dumps(self.data, ensure_ascii=False, indent=2), encoding="utf-8")
            tmp.replace(self.path)
        except OSError:
            # Learning is optional; conversation must continue if disk is read-only.
            pass
