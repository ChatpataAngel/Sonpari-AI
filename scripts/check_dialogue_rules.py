#!/usr/bin/env python3
"""Validate Aiko's offline rule packs and report their coverage; no network needed."""
from __future__ import annotations
from collections import Counter
from pathlib import Path
import sys

import yaml

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from aiko.dialogue_rules import RULES
from aiko.engine import ResponseEngine


def main() -> int:
    errors: list[str] = []
    intents = [intent for intent, _pattern, _pools in RULES]
    duplicates = [intent for intent, count in Counter(intents).items() if count > 1]
    if duplicates:
        errors.append("duplicate direct intents: " + ", ".join(duplicates))

    for intent, pattern, pools in RULES:
        if not intent:
            errors.append("an intent has an empty name")
        if set(pools) != {"hinglish", "hi", "en"}:
            errors.append(f"{intent}: expected hinglish, hi and en response pools")
            continue
        for language, responses in pools.items():
            if not responses or not all(isinstance(item, str) and item.strip() for item in responses):
                errors.append(f"{intent}/{language}: empty or invalid response")
        # Re-check the compiled expression's type to catch accidental data shape changes.
        if not hasattr(pattern, "search"):
            errors.append(f"{intent}: pattern is not compiled")

    try:
        persona = yaml.safe_load((ROOT / "config" / "persona.yaml").read_text(encoding="utf-8"))
        engine = ResponseEngine(persona, [str(ROOT / "config" / "rules.yaml")])
        yaml_rules = len(engine.rules)
        translations = sorted(engine.translations)
    except Exception as exc:  # noqa: BLE001 - report validation errors from YAML/regex compilation.
        errors.append(f"YAML response engine failed to load: {exc}")
        yaml_rules, translations = 0, []

    if errors:
        print("Dialogue validation FAILED:")
        for error in errors:
            print(f" - {error}")
        return 1

    print("Dialogue validation passed")
    print(f"Direct intents: {len(RULES)}")
    print(f"YAML engine rules: {yaml_rules}")
    print(f"Combined rule count: {len(RULES) + yaml_rules}")
    print("Translation sidecars: " + (", ".join(translations) if translations else "none"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
