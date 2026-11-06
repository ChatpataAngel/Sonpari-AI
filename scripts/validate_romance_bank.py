#!/usr/bin/env python3
"""Validate Aiko's generated romance bank and manifest without dependencies."""
from __future__ import annotations
import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BANK = ROOT / "aiko" / "romance_conversation_bank.jsonl"
MANIFEST = ROOT / "aiko" / "romance_conversation_bank_manifest.json"
REQUIRED = {"id", "intent", "style", "language", "user", "assistant", "anchors", "adult_only", "source", "license", "content_note"}
ALLOWED_LANGS = {"hinglish", "hi", "en"}


def main() -> int:
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    rows = [json.loads(line) for line in BANK.read_text(encoding="utf-8").splitlines() if line.strip()]
    errors = []
    if len(rows) != manifest.get("pair_count"):
        errors.append(f"pair count mismatch: {len(rows)} != {manifest.get('pair_count')}")
    prompts = [str(row.get("user", "")).casefold().strip() for row in rows]
    replies = [str(row.get("assistant", "")).casefold().strip() for row in rows]
    if len(set(prompts)) != len(rows):
        errors.append("duplicate user prompts detected")
    if len(set(replies)) < 5000:
        errors.append(f"reply variety below threshold: {len(set(replies))}")
    language_counts = Counter(row.get("language") for row in rows)
    if dict(language_counts) != manifest.get("language_pair_counts"):
        errors.append(f"language counts mismatch: {dict(language_counts)}")
    adult_count = sum(bool(row.get("adult_only")) for row in rows)
    if adult_count != manifest.get("adult_only_pair_count"):
        errors.append("adult_only count mismatch")
    if len({row.get("intent") for row in rows}) != manifest.get("topic_count"):
        errors.append("topic count mismatch")
    for i, row in enumerate(rows, 1):
        if not REQUIRED <= set(row):
            errors.append(f"row {i}: required field(s) missing")
            break
        if row.get("language") not in ALLOWED_LANGS:
            errors.append(f"row {i}: unsupported language")
            break
        if not str(row.get("user", "")).strip() or not str(row.get("assistant", "")).strip():
            errors.append(f"row {i}: empty prompt or reply")
            break
        if row.get("source") != "original_aiko_authored":
            errors.append(f"row {i}: unexpected provenance")
            break
    if errors:
        print("Romance bank validation FAILED:")
        for error in errors:
            print(f" - {error}")
        return 1
    print(f"Romance bank valid: {len(rows)} unique pairs, {len(set(replies))} unique replies, {manifest['topic_count']} topics.")
    print(f"Utterance messages: {manifest['utterance_message_count']}; languages: {dict(language_counts)}; adult-tagged pairs: {adult_count}.")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
