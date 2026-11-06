"""Offline retrieval over Aiko's original relationship conversation examples.

This is a dependency-free lexical retriever, not a generative model. The bank
contains original user/assistant message pairs and stays fully on-device.
"""
from __future__ import annotations

import json
import math
import random
import re
from collections import defaultdict
from functools import lru_cache
from pathlib import Path
from typing import Any

from .text_style import normalize_for_matching

_LANGS = ("hinglish", "hi", "en")
_TOKEN_RE = re.compile(r"[a-z0-9']+|[\u0900-\u097f]+", re.I)
_STOP = set("""
i im i'm me my mine you your yours we us our ours he she they them his her their
it its the a an and or but is are was were be been being to of for in on at with
about this that these those do did does can could would should please pls plz very
just really so too as if then now hey hi hello baby babyyy babe jaan jaanu ji
hoon ho hai tha thi hain theek toh na bhi ek ki ke ka tum aap mera meri mujhe
tumhe tumhari mein main se par aur mein aaj suno sunoo yaar sach bolun baat
क्या है हैं हूं हूँ मैं तुम तुम्हारी तुम्हारे तुम्हें मुझे हम हमारा हमारी एक और की का के को से पर में पर यह ये वो तो भी बस आज बहुत थोड़ा थोड़ी अगर कि ना जी जान सुनो सच कहूँ कहूँ
""".split())


@lru_cache(maxsize=50000)
def _normalized(value: str) -> str:
    return normalize_for_matching(value or "").casefold()


@lru_cache(maxsize=50000)
def _tokens(value: str) -> frozenset[str]:
    normalized = _normalized(value or "")
    return frozenset(token for token in _TOKEN_RE.findall(normalized) if token not in _STOP and len(token) > 1)


class RomanceConversationRetriever:
    """High-confidence match against a local JSONL bank of conversation pairs."""

    def __init__(self, rng: random.Random | None = None, *, data_path: str | Path | None = None):
        self.rng = rng or random.Random()
        self.path = Path(data_path) if data_path else Path(__file__).with_name("romance_conversation_bank.jsonl")
        self.rows: list[dict[str, Any]] = []
        self._doc_tokens: list[set[str]] = []
        self._normalized_prompts: list[str] = []
        self._multiword_anchors: list[list[str]] = []
        self._postings: dict[str, set[int]] = defaultdict(set)
        self._df: dict[str, int] = defaultdict(int)
        self._pools: dict[str, dict[str, list[str]]] = defaultdict(lambda: defaultdict(list))
        self._styles: dict[str, str] = {}
        self._families: dict[str, str] = {}
        self._anchors_by_intent: dict[str, set[str]] = defaultdict(set)
        self._load()

    def _load(self) -> None:
        try:
            with self.path.open("r", encoding="utf-8") as stream:
                for line in stream:
                    try:
                        row = json.loads(line)
                    except json.JSONDecodeError:
                        continue
                    if not isinstance(row, dict):
                        continue
                    intent, language = row.get("intent"), row.get("language")
                    user, assistant = row.get("user"), row.get("assistant")
                    if not all(isinstance(x, str) and x.strip() for x in (intent, language, user, assistant)):
                        continue
                    if language not in _LANGS:
                        continue
                    if len(user) > 800 or len(assistant) > 1400:
                        continue
                    index = len(self.rows)
                    self.rows.append(row)
                    self._normalized_prompts.append(_normalized(user))
                    doc_tokens = set(_tokens(user))
                    anchors = row.get("anchors", [])
                    if isinstance(anchors, list):
                        clean_anchors = [_normalized(x).strip() for x in anchors
                                         if isinstance(x, str) and x.strip()]
                        anchor_tokens = set().union(*(_tokens(x) for x in clean_anchors)) if clean_anchors else set()
                        self._multiword_anchors.append([x for x in clean_anchors if len(_tokens(x)) >= 2])
                    else:
                        anchor_tokens = set()
                        self._multiword_anchors.append([])
                    doc_tokens.update(anchor_tokens)
                    self._doc_tokens.append(doc_tokens)
                    self._styles[intent] = str(row.get("style", "warm"))
                    self._families[intent] = str(row.get("family", "romance"))
                    self._anchors_by_intent[intent].update(anchor_tokens)
                    self._pools[intent][language].append(assistant)
        except OSError:
            return

        for index, doc_tokens in enumerate(self._doc_tokens):
            for token in doc_tokens:
                self._postings[token].add(index)
                self._df[token] += 1
        self._num_docs = max(1, len(self.rows))

    @staticmethod
    def _lang(language: str) -> str:
        return language if language in _LANGS else "hinglish"

    def respond(self, message: str, language: str = "hinglish", *, previous_bot_response: str = "") -> tuple[str, str] | None:
        original = (message or "").strip()
        if not original or original.startswith("/") or len(original) > 1000 or not self.rows:
            return None
        query = _tokens(original)
        if len(query) < 2:
            return None

        # Only terms that occur in the local corpus participate in ranking. Unknown
        # words (names, typos, random slang) must not drown out meaningful overlap.
        known = {token for token in query if token in self._postings}
        if not known:
            return None
        query_weights = {
            token: 1.0 + math.log((self._num_docs + 1) / (self._df.get(token, 0) + 1))
            for token in known
        }
        total_weight = sum(query_weights.values()) or 1.0
        candidates: set[int] = set()
        for token in known:
            candidates.update(self._postings.get(token, ()))
        if not candidates:
            return None

        # Rank by intent rather than by one duplicated template row. The row-level
        # candidate remains available for exact phrase matching and diagnostics.
        best_by_intent: dict[str, tuple[float, int, int]] = {}
        normalized_query = _normalized(original)
        for index in candidates:
            row = self.rows[index]
            intent = row["intent"]
            doc = self._doc_tokens[index]
            overlap = known & doc
            if not overlap:
                continue
            # At least two distinct informative terms are required, except for a
            # uniquely identifying rare slang/anchor in a longer message.
            rare_single = False
            if len(overlap) == 1 and len(_TOKEN_RE.findall(normalized_query)) >= 4:
                only = next(iter(overlap))
                rare_single = self._df.get(only, self._num_docs) <= 100
            if len(overlap) < 2 and not rare_single:
                continue
            weight = sum(query_weights[token] for token in overlap)
            score = weight / total_weight
            prompt = self._normalized_prompts[index]
            if normalized_query == prompt:
                score = 1.5
            elif len(normalized_query) >= 8 and normalized_query in prompt:
                score += 0.12
            # Exact multiword anchors receive a small precision bonus, but a single
            # broad word such as "love" can never route a message by itself.
            if any(re.search(r"(?<!\w)" + re.escape(anchor) + r"(?!\w)", normalized_query)
                   for anchor in self._multiword_anchors[index]):
                score += 0.06
            old = best_by_intent.get(intent)
            row_info = (score, index, len(overlap))
            if old is None or row_info[0] > old[0]:
                best_by_intent[intent] = row_info

        if not best_by_intent:
            return None
        ranked = sorted(best_by_intent.items(), key=lambda item: item[1][0], reverse=True)
        best_intent, (best_score, best_index, overlap_count) = ranked[0]
        if best_score < 0.48 or overlap_count < 2 and best_score < 0.80:
            return None
        if len(ranked) > 1:
            second_intent, (second_score, _second_index, _second_overlap) = ranked[1]
            if best_score - second_score < 0.07:
                # For near ties, prefer a common family/style only when the text
                # itself strongly hits multiple anchors. Otherwise fall through.
                same_family = self._families.get(best_intent) == self._families.get(second_intent)
                # Slang anchors can intentionally be shared across adult-flirt
                # intents (e.g. a body compliment that is also suggestive). If
                # both candidates are the same narrow family and the token match
                # is very strong, choose a local variation instead of falling
                # all the way back to a generic reply.
                if not (same_family and best_score >= 0.78):
                    return None

        lang = self._lang(language)
        pool = self._pools.get(best_intent, {}).get(lang) or self._pools.get(best_intent, {}).get("hinglish", [])
        if not pool:
            return None
        previous = re.sub(r"\s+", " ", previous_bot_response or "").casefold()
        options = [item for item in pool if re.sub(r"\s+", " ", item).casefold() != previous] or pool
        return f"romance_bank_{best_intent}", self.rng.choice(options)
