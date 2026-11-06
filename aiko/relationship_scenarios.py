"""Opt-in local multi-turn couple and romance scenarios.

All script text is original to Aiko. No model, network request, or extra package
is used. Adult scenes are fictional, non-graphic, and explicitly consent-forward.
"""
from __future__ import annotations

import json
import random
import re
from pathlib import Path
from typing import Any

from .text_style import normalize_for_matching

_LANGS = ("hinglish", "hi", "en")
_STOP_EXACT = re.compile(
    r"^(?:no|nope|nah|stop|stop roleplay|end scene|end the scene|pause|red|yellow|"
    r"not comfortable|i'm not comfortable|i am not comfortable|i don't want to continue|"
    r"i do not want to continue|don't continue|do not continue|that's enough|enough|"
    r"bas|bas karo|ruk jao|ruko|mujhe nahi karna|ab nahi|scene band karo|roleplay band karo)[.!\s~💗🫂😭😂]*$",
    re.I,
)
_STOP_PHRASE = re.compile(
    r"\b(?:please stop|stop this scene|stop the roleplay|end this roleplay|"
    r"i want to stop|i need to stop|not feeling comfortable|i feel uncomfortable|"
    r"change my mind|i changed my mind|let's stop|lets stop|pause the scene|"
    r"scene stop karo|roleplay rok do|ab ruk jao|mujhe uncomfortable lag raha)\b",
    re.I,
)
_NORMAL_CHAT = re.compile(
    r"^(?:normal chat|back to normal|exit roleplay|leave roleplay|end roleplay|"
    r"switch to normal chat|stop roleplay mode|scene se bahar|normal baat karo)[.!\s]*$",
    re.I,
)
_TOPIC_CHANGE = re.compile(
    r"\b(?:weather forecast|what is the capital|define \w+|translate this|"
    r"python code|debug this|groq api|api key|latest news|write code|solve this equation|"
    r"exam timetable|job interview question|calculate \d|search the web)\b",
    re.I,
)
_POSITIVE = re.compile(r"\b(?:yes|yeah|yep|yess+|haan|han|haanji|bilkul|sure|of course|i'd love to|i would love to|sounds good|okay|ok ji|done|kiss me|hug me|come here|i agree)\b", re.I)
_SHY = re.compile(r"\b(?:shy|blush|blushing|sharma|sharma gaya|sharma gayi|embarrassed|nervous|☺|🙈|🥹)\b", re.I)
_PLAYFUL = re.compile(r"\b(?:tease|teasing|flirt|flirting|troublemaker|you wish|challenge|prove it|bold|😏|😈)\b", re.I)
_UNSURE = re.compile(r"\b(?:maybe|not sure|i don't know|dont know|unsure|nervous|slow down|a little scared|confused|comfortable nahi|pata nahi)\b", re.I)


class RelationshipScenarioEngine:
    """Run explicit multi-turn local scenarios without hijacking normal chat."""

    def __init__(self, rng: random.Random | None = None):
        self.rng = rng or random.Random()
        self.scenes = self._load_scenes()
        self.sessions: dict[int, dict[str, Any]] = {}
        self._by_id = {scene["id"]: scene for scene in self.scenes}

    @staticmethod
    def _load_scenes() -> list[dict[str, Any]]:
        path = Path(__file__).with_name("relationship_scenarios.json")
        try:
            raw = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return []
        items = raw.get("scenes", []) if isinstance(raw, dict) else []
        scenes: list[dict[str, Any]] = []
        seen: set[str] = set()
        for scene in items:
            if not isinstance(scene, dict) or not isinstance(scene.get("id"), str):
                continue
            if scene["id"] in seen:
                continue
            start = scene.get("start")
            turns = scene.get("turns")
            triggers = scene.get("triggers")
            reactions = scene.get("reactions")
            if not isinstance(start, dict) or not isinstance(turns, list) or not turns or not isinstance(triggers, list):
                continue
            if not all(isinstance(start.get(lang), str) and start[lang].strip() for lang in _LANGS):
                continue
            safe_turns = []
            valid = True
            for turn in turns:
                if not isinstance(turn, dict):
                    valid = False
                    break
                pools: dict[str, list[str]] = {}
                for lang in _LANGS:
                    pool = turn.get(lang)
                    if not isinstance(pool, list) or not pool or not all(isinstance(x, str) and x.strip() for x in pool):
                        valid = False
                        break
                    pools[lang] = pool
                if not valid:
                    break
                safe_turns.append(pools)
            if not valid:
                continue
            compiled = []
            for trigger in triggers:
                if not isinstance(trigger, str) or len(trigger) > 300:
                    continue
                try:
                    compiled.append(re.compile(trigger, re.I))
                except re.error:
                    continue
            if not compiled:
                continue
            safe_reactions = {}
            if isinstance(reactions, dict):
                for lang in _LANGS:
                    langdata = reactions.get(lang, {})
                    if not isinstance(langdata, dict):
                        continue
                    safe_reactions[lang] = {
                        category: [x for x in pool if isinstance(x, str)]
                        for category, pool in langdata.items()
                        if isinstance(category, str) and isinstance(pool, list) and pool
                    }
            normalized = dict(scene)
            normalized.update({"triggers": compiled, "turns": safe_turns, "reactions": safe_reactions})
            scenes.append(normalized)
            seen.add(scene["id"])
        return scenes

    @staticmethod
    def _lang(language: str) -> str:
        return language if language in _LANGS else "hinglish"

    def _start_match(self, text: str) -> dict[str, Any] | None:
        candidate = normalize_for_matching(text).strip().strip(" .!?~\t\r\n")
        # Keep triggers deliberately opt-in: ordinary flirt messages should use
        # Aiko's normal dialogue rules, not silently enter a scripted scene.
        for scene in self.scenes:
            for pattern in scene["triggers"]:
                if pattern.fullmatch(candidate):
                    return scene
        return None

    def respond(self, user_id: int, message: str, language: str = "hinglish") -> tuple[str, str] | None:
        text = (message or "").strip()
        if not text or text.startswith("/"):
            return None
        lang = self._lang(language)
        scene = self._start_match(text)
        if scene is not None:
            self.sessions[user_id] = {"scene_id": scene["id"], "turn": 0}
            return f"scene_{scene['id']}", scene["start"][lang]

        session = self.sessions.get(user_id)
        if session is None:
            return None

        normalized = normalize_for_matching(text).strip().strip(" .!?~\t\r\n")
        if _STOP_EXACT.fullmatch(normalized) or _STOP_PHRASE.search(normalized):
            self.sessions.pop(user_id, None)
            stop_reply = {
                "hinglish": "theek hai ji, scene yahin stop 💗 no explanation needed. Hum normal chat par aa gaye—tumhari comfort first.",
                "hi": "ठीक है जी, scene यहीं stop 💗 कारण बताना ज़रूरी नहीं। अब normal chat—तुम्हारी comfort पहले।",
                "en": "of course, the scene stops here 💗 no explanation needed. We’re back to normal chat; your comfort comes first.",
            }
            return "scene_stopped", stop_reply[lang]
        if _NORMAL_CHAT.fullmatch(normalized) or _TOPIC_CHANGE.search(normalized):
            self.sessions.pop(user_id, None)
            return None

        active = self._by_id.get(session.get("scene_id", ""))
        if active is None:
            self.sessions.pop(user_id, None)
            return None
        turn_index = int(session.get("turn", 0))
        if turn_index >= len(active["turns"]):
            self.sessions.pop(user_id, None)
            return None

        category = "default"
        if _UNSURE.search(normalized):
            category = "unsure"
        elif _SHY.search(normalized):
            category = "shy"
        elif _PLAYFUL.search(normalized):
            category = "playful"
        elif _POSITIVE.search(normalized):
            category = "positive"

        base_pool = active["turns"][turn_index][lang]
        base = self.rng.choice(base_pool)
        reaction_pools = active.get("reactions", {}).get(lang, {})
        prefixes = reaction_pools.get(category) or reaction_pools.get("default") or []
        prefix = self.rng.choice(prefixes) if prefixes else ""
        response = f"{prefix}{base}".strip()
        session["turn"] = turn_index + 1
        intent = f"scene_{active['id']}"
        if session["turn"] >= len(active["turns"]):
            self.sessions.pop(user_id, None)
            # Tell the caller this scene has reached its scripted end.
            intent += "_complete"
        return intent, response
