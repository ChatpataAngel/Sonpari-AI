"""Curated, offline dialogue rules. Add new packs here; no model/API needed."""
from collections.abc import Mapping, Sequence

from .greetings import RULES as GREETING_RULES
from .contextual import RULES as CONTEXT_RULES
from .support import RULES as SUPPORT_RULES
from .romance import RULES as ROMANCE_RULES
from .humor import RULES as HUMOR_RULES
from .daily import RULES as DAILY_RULES
from .social import RULES as SOCIAL_RULES

# Order is intentional: short, specific and conversational patterns first.
RULES = (
    CONTEXT_RULES
    + GREETING_RULES
    + SUPPORT_RULES
    + ROMANCE_RULES
    + HUMOR_RULES
    + DAILY_RULES
    + SOCIAL_RULES
)


def apply_response_expansions(rules, extras):
    """Merge extra reply pools, accepting both multilingual maps and flat lists.

    Preferred format: {intent: {language: [replies]}}. A flat list of strings
    is treated as Hinglish-only so Hindi/English chats do not receive mismatched
    text. Unknown intents/languages and malformed entries are safely ignored.
    """
    rule_by_intent = {intent: pools for intent, _pattern, pools in rules}
    intent_aliases = {
        "goodnight": "good_night",
        "good_night": "goodnight",
        "goodmorning": "good_morning",
        "good_morning": "goodmorning",
    }

    if not isinstance(extras, Mapping):
        return

    for intent, payload in extras.items():
        pools = rule_by_intent.get(intent)
        if pools is None:
            pools = rule_by_intent.get(intent_aliases.get(intent, ""))
        if not isinstance(pools, Mapping):
            continue

        if isinstance(payload, Mapping):
            language_pools = payload
        elif isinstance(payload, (list, tuple)):
            # Convenience format for quickly adding default Hinglish replies.
            if all(isinstance(item, str) for item in payload):
                language_pools = {"hinglish": payload}
            else:
                # Also accept a list of {"language": ..., "responses": [...]}
                # entries or a list of language-to-responses dictionaries.
                language_pools = {}
                for item in payload:
                    if not isinstance(item, Mapping):
                        continue
                    if isinstance(item.get("language"), str):
                        language_pools[item["language"]] = item.get("responses", [])
                    else:
                        language_pools.update(item)
        else:
            continue

        for language, responses in language_pools.items():
            if language not in pools:
                continue
            if isinstance(responses, str):
                responses = [responses]
            if not isinstance(responses, (list, tuple)):
                continue
            additions = [reply.strip() for reply in responses if isinstance(reply, str) and reply.strip()]
            pools[language].extend(additions)


# Load the curated second wave of alternatives.
from .response_expansions import EXTRA as _EXTRA_RESPONSES
apply_response_expansions(RULES, _EXTRA_RESPONSES)
