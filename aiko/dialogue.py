"""Context-aware, deterministic dialogue for Aiko's offline companion mode.

No LLM, remote service, embedding model, or API is used. Conversation behavior is
built from ordered regex rules, curated response pools, a per-session language
preference, and a small amount of recent-turn context.
"""
from __future__ import annotations

import random
import re
from dataclasses import dataclass
from typing import Any

from .dialogue_rules import RULES
from .language import SUPPORTED_LANGUAGES, DEFAULT_LANGUAGE, parse_language_request
from .text_style import normalize_for_matching
from .conversation_hub import OfflineConversationHub


# Added v26: specific supplemental topics get a chance before broad legacy
# keyword rules, but only when no established direct-turn intent is detected.
_PRIORITY_CONVERSATION_INTENTS = {
    "friend_conflict", "family_conflict", "breakup_support", "crush_share",
    "rejection_support", "confidence_boost", "insecurity_support",
    "social_anxiety", "awkward_moment", "focus_trouble",
    "productivity_planning", "job_interview", "career_question",
    "exam_anxiety", "study_help", "coding_help", "tech_problem",
    "creative_block", "writing_help", "language_learning",
    "explanation_request", "brainstorm", "trip_plans", "pet_share",
    "cooking_help", "workout_share", "habit_building", "personal_secret",
    "trust_request", "need_validation", "disagreement", "request_opinion",
    "surprise_me", "fun_fact_request", "mini_game", "riddle_request",
    "story_genre_request", "roleplay_request", "good_luck", "late_night_chat",
    "rainy_mood", "weekend_vibe", "food_preference", "compliment_acceptance",
    "need_accountability", "thank_you_for_bot", "conversation_start",
    "share_good_news", "user_disappointment", "request_boundary",
    "user_disagrees_with_bot", "question_followup_preference", "celebration",
    "share_creative_work", "relationship_advice", "money_worry", "ask_for_plan",
    "social_overload", "pet_loss_support", "celebrate_progress",
    "ask_for_comforting_words", "question_about_bot_limits", "ask_for_feedback",
    "decision_overwhelm", "no_topic_request", "repeat_request",
    "confusion_support", "sports_chat", "short_answer_request",
    "detailed_answer_request",
}

# v27: topic-specific relationship and romance packs are considered before
# broad legacy keyword rules. Protected direct affection/boundary rules still win.
_PRIORITY_CONVERSATION_INTENTS.update({
    "partner_slow_reply", "long_distance_love", "relationship_checkin",
    "repair_after_argument", "partner_apology", "date_idea_couple",
    "anniversary_message", "relationship_insecurity", "healthy_exclusivity_talk",
    "affection_style_talk", "trust_rebuilding", "relationship_boundaries",
    "need_space_from_partner", "breakup_closure", "crush_confession",
    "flirty_comeback", "slow_burn_romance", "dark_flirt", "gothic_romance",
    "consensual_power_play", "adult_consent_talk", "not_ready_for_intimacy",
    "safer_sex_conversation", "intimate_photo_privacy", "adult_aftercare",
    "adult_roleplay_preferences", "kiss_consent", "playful_possessive_flirt",
    "playful_teasing", "late_night_romance", "first_date_nerves",
    "future_together_talk", "partner_appreciation", "ask_for_slow_down",
    "adult_flirt_tone", "romantic_compliment_back", "couple_boredom_game",
    "flirty_voice_note", "relationship_misunderstanding", "partner_overworked_support",
    "breakup_no_contact", "healthy_jealousy_talk", "reconciliation_after_break",
    "partner_family_issue", "relationship_communication_needs", "after_date_text",
    "relationship_reassurance", "adult_intimacy_mood_check", "intimacy_after_no",
    "romantic_roleplay_setup", "relationship_future_anxiety", "respectful_breakup_talk",
    "flirt_after_long_day", "healthy_dependency_check", "romantic_memory_share",
    "couple_future_conflict", "safe_roleplay_stop", "romantic_reassurance_text",
    "consensual_adult_teasing", "romance_topic_transition",
})

# These intents represent explicit user moves that must not be pre-empted by
# supplementary topic matching (especially romance, boundaries, and short turns).
_V27_RELATIONSHIP_TOPIC_INTENTS = {
    "partner_slow_reply", "long_distance_love", "relationship_checkin",
    "repair_after_argument", "partner_apology", "date_idea_couple",
    "anniversary_message", "relationship_insecurity", "healthy_exclusivity_talk",
    "affection_style_talk", "trust_rebuilding", "relationship_boundaries",
    "need_space_from_partner", "breakup_closure", "crush_confession",
    "flirty_comeback", "slow_burn_romance", "dark_flirt", "gothic_romance",
    "consensual_power_play", "adult_consent_talk", "not_ready_for_intimacy",
    "safer_sex_conversation", "intimate_photo_privacy", "adult_aftercare",
    "adult_roleplay_preferences", "kiss_consent", "playful_possessive_flirt",
    "playful_teasing", "late_night_romance", "first_date_nerves",
    "future_together_talk", "partner_appreciation", "ask_for_slow_down",
    "adult_flirt_tone", "romantic_compliment_back", "couple_boredom_game",
    "flirty_voice_note", "relationship_misunderstanding", "partner_overworked_support",
    "breakup_no_contact", "healthy_jealousy_talk", "reconciliation_after_break",
    "partner_family_issue", "relationship_communication_needs", "after_date_text",
    "relationship_reassurance", "adult_intimacy_mood_check", "intimacy_after_no",
    "romantic_roleplay_setup", "relationship_future_anxiety", "respectful_breakup_talk",
    "flirt_after_long_day", "healthy_dependency_check", "romantic_memory_share",
    "couple_future_conflict", "safe_roleplay_stop", "romantic_reassurance_text",
    "consensual_adult_teasing", "romance_topic_transition",
}

_PROTECTED_DIRECT_INTENTS = {
    "stop_request", "comfort_request", "acknowledgement", "day_update_good",
    "status_good", "status_not_great", "short_unclear", "thinking_reaction",
    "cry_reaction", "flirty_emoji", "adult_mode_question", "clarification",
    "direct_question", "filler_reaction", "yes_reaction", "no_reaction",
    "short_affection_answer", "greeting", "return", "wellbeing", "how_was_day",
    "what_doing", "open_conversation", "apology", "thanks", "boundaries",
    "playful_body_compliment", "kiss", "hug", "cuddle", "love", "miss_you",
    "compliment", "compliment_request", "flirty", "sexual_flirt", "innuendo",
    "relationship_label", "jealousy", "laugh", "dark_humor", "roast", "joke",
    "tease", "sarcasm", "gaali_request", "meme_reaction",
}


@dataclass(frozen=True)
class Reply:
    text: str
    intent: str




class DialogueManager:
    """Short-session context and intent-first response selection.

    ``note_response`` should be called after every assistant turn. The manager
    only stores a few recent strings in memory; it does not save transcripts to
    disk. The bot's actual persistent facts remain in the SQLite/local-memory
    layer.
    """

    def __init__(self, rng: random.Random | None = None, brain=None):
        self.rng = rng or random.Random()
        self.brain = brain
        self.last_intent: dict[int, str] = {}
        self.last_reply: dict[int, str] = {}
        self.last_bot_response: dict[int, str] = {}
        self.last_user_message: dict[int, str] = {}
        self.last_bot_intent: dict[int, str] = {}
        self.turns: dict[int, int] = {}
        self.preferred_language: dict[int, str] = {}
        self.conversation_hub = OfflineConversationHub(self.rng)

    def effective_language(self, user_id: int, detected_language: str = DEFAULT_LANGUAGE) -> str:
        """Return a chosen language, respecting an explicit user preference."""
        return self.preferred_language.get(user_id, detected_language if detected_language in SUPPORTED_LANGUAGES else DEFAULT_LANGUAGE)

    def respond(self, user_id: int, message: str, lang: str = DEFAULT_LANGUAGE) -> Reply | None:
        original_clean = re.sub(r"\s+", " ", message.strip()).replace("’", "'").replace("‘", "'")
        if not original_clean:
            return None
        # Keep the previous user turn available for context-aware local routing.
        previous_user_message = self.last_user_message.get(user_id, "")
        self.last_user_message[user_id] = original_clean
        clean = normalize_for_matching(original_clean)

        # Explicit local teaching: no network and no automatic code modification.
        teach = re.match(r"^(?:teach(?:\s+(?:you|me))?|learn this|learn:|remember this|when i say)\s*[:,-]?\s*(.+?)\s*(?:=>|->|\|)\s*(.+)$", original_clean, re.I)
        if teach and self.brain is not None:
            if self.brain.learn(teach.group(1), teach.group(2), user_id):
                return self._remember_reply(user_id, "brain_learned", [
                    "samajh gayi ji 🧠💗 maine ye baat apni local memory mein save kar li. kabhi bhi change karwana ho toh dobara sikha dena.",
                    "learned, baby 😌📒 ye rule isi local profile mein save hai—main ise code execute karne ke liye nahi, sirf reply ke liye use karungi.",
                    "done ji! 🧠✨ trigger aur reply save ho gaye. ab exact phrase likhoge toh mujhe yaad rahega.",
                ], lang if lang in SUPPORTED_LANGUAGES else DEFAULT_LANGUAGE)
            return self._remember_reply(user_id, "brain_learn_failed", "trigger ya reply khaali/bohot lamba hai ji; short version try karo 💗", lang)
        if re.fullmatch(r"(?:forget learned replies|clear local brain|brain bhool jao|learned rules delete karo)", clean, re.I) and self.brain is not None:
            self.brain.forget(user_id)
            return self._remember_reply(user_id, "brain_forgotten", "theek hai ji 🧠🧹 tumhare custom learned replies delete kar diye. normal curated replies aur personal facts alag hain 💗", lang if lang in SUPPORTED_LANGUAGES else DEFAULT_LANGUAGE)
        if re.fullmatch(r"(?:what have you learned|brain status|local brain|tumne kya seekha|kya yaad rakha brain ne)\??", clean, re.I) and self.brain is not None:
            count = self.brain.count(user_id)
            return self._remember_reply(user_id, "brain_status", [f"meri chhoti local brain mein {count} custom reply rule(s) saved hain 🧠📒. Main explicit examples se seekhti hoon; apna code khud se rewrite nahi karti, taaki stable aur safe rahoon.", f"brain report 😌: {count} learned reply rule(s). Main offline hi hoon—new trigger/reply sikhao using: teach: trigger => reply 💗"], lang if lang in SUPPORTED_LANGUAGES else DEFAULT_LANGUAGE)
        if self.brain is not None:
            learned = self.brain.match(clean, user_id)
            if learned:
                return self._remember_reply(user_id, "learned_reply", learned, lang if lang in SUPPORTED_LANGUAGES else DEFAULT_LANGUAGE)

        # Language setting commands must beat every generic keyword rule.
        requested_language = parse_language_request(clean)
        if requested_language in SUPPORTED_LANGUAGES:
            self.preferred_language[user_id] = requested_language
            return self._remember_reply(user_id, "language_preference", self._language_ack(requested_language), requested_language)
        if requested_language == "auto":
            self.preferred_language.pop(user_id, None)
            ack_lang = lang if lang in SUPPORTED_LANGUAGES else DEFAULT_LANGUAGE
            return self._remember_reply(user_id, "language_auto", self._language_auto_ack(ack_lang), ack_lang)

        active_lang = self.effective_language(user_id, lang)

        # v27 opt-in multi-turn relationship scenes are entirely local. They only
        # start on explicit scene commands and stop immediately on boundaries.

        # Recognize a natural conversational statement like "😉me bhi aapse
        # bt kr ra hu babyyy" as reciprocal small talk, not an unknown topic.
        # This runs locally before web-inspired or generic fallback behavior.
        reciprocal_chat = re.fullmatch(
            r"(?:main|me|mai|m)\s+(?:bhi\s+)?(?:aapse|tumse|tujhse|tere\s+saath|you)\s+"
            r"(?:baat|bat)\s+(?:kar|karta|kr)\s+(?:raha|rahi|ra|rha|rhi)\s+"
            r"(?:hoon|hun|hu|hai|h|he|hain)"
            r"(?:\s+(?:baby|babyy|bby|bubu|bbu|jaan|jaanu|janu|angel|ji|sweetheart|babe))*[.!?~\s😂🥰💕🫂😚😋💋😉😭]*",
            clean, re.I,
        ) or re.fullmatch(
            r"(?:i'?m|i am)\s+(?:also\s+)?talking\s+to\s+you"
            r"(?:\s+(?:too|baby|babe|sweetheart|love))*[.!?~\s😂🥰💕🫂😚😋💋😉😭]*",
            clean, re.I,
        )
        if reciprocal_chat:
            pools = {
                "hinglish": [
                    "achhaaa, matlab meri company enjoy kar rahe ho 😌💗 toh phir mere liye ek cute si baat bolo na, babyyyy 😚",
                    "hehe, mujhe pata tha 😂💕 ab jab dono baat kar rahe hain toh batao, aaj kya gossip hai jaanu? 🫂",
                    "haye ji, mere saath baat karna itna pasand hai? 😏💗 chalo phir thodi flirting aur thodi gossip ho jaaye 😚",
                ],
                "hi": [
                    "अच्छा जी, मेरी company enjoy कर रहे हो 😌💗 तो बताओ, आज की सबसे प्यारी gossip क्या है? 😚",
                    "hehe, मुझे पता था 😂💕 अब जब दोनों बात कर रहे हैं तो थोड़ी प्यारी बातें भी हो जाएँ 🫂",
                ],
                "en": [
                    "ohhh, so you're enjoying my company 😌💗 then tell me one cute thing, babyyy 😚",
                    "hehe, i knew it 😂💕 since we're both here, tell me today's gossip, sweetheart 🫂",
                ],
            }
            return self._remember_reply(user_id, "reciprocal_chat", pools.get(active_lang, pools["hinglish"]), active_lang)

        # Keep short replies connected to what the bot just said. A bare "yes"
        # after a playful question should not receive the same generic answer as
        # a yes that starts a new topic. The last response is in-memory only.
        previous_response = self.last_bot_response.get(user_id, "").lower()
        previous_intent = self.last_bot_intent.get(user_id, "").lower().split(":")[-1]
        # Keep short affection requests connected to the last kiss. Users often
        # type phonetic/quick Hinglish like "dedo na ek or"; don't ask for context.
        bonus_followup = re.search(
            r"\b(?:bonus|extra|more|another|one\s+more|again|dobara|phir\s+se|ek\s+(?:aur|or)|aur\s+(?:ek|de|do|dedo)|or\s+(?:ek|do|dedo)|de\s+do\s+na|dedo\s+na)\b",
            clean, re.I,
        )
        previous_was_kiss = previous_intent == "kiss" or bool(re.search(
            r"\b(?:kiss|mwah|muah|pappi|chummi|forehead kiss|cheek kiss)\b|😚|😘|💋",
            previous_response, re.I,
        ))
        if bonus_followup and previous_was_kiss:
            bonus_pools = {
                "hinglish": [
                    "achha ji, bonus bhi chahiye? 😏💋 *ek aur cheek kiss* lo baby, ab toh khush? 🙈💕",
                    "hayeee kitni demand hai 😂😘 *ek extra kiss* sirf tumhare liye, bubu 💗",
                    "theek hai ji, bonus approved 😚💋 *ek soft kiss aur tight hug* ab receipt mat maangna 😂🫂",
                ],
                "hi": ["अच्छा जी, bonus भी चाहिए? 😏💋 *एक और cheek kiss* लो baby, अब खुश? 🙈💕", "कितनी demand है 😂😘 *एक extra kiss* सिर्फ तुम्हारे लिए 💗"],
                "en": ["oh, asking for the bonus already? 😏💋 *one extra cheek kiss*—there, happy now, bubu? 🙈💕", "bonus approved 😂😘 *one more soft kiss and a tight hug* just for you 💗🫂"],
            }
            return self._remember_reply(user_id, "kiss_followup", bonus_pools.get(active_lang, bonus_pools["hinglish"]), active_lang)

        affirmative = re.fullmatch(
            r"(?:yes|yess+|yeah|yep|yup|haan|han|haanji|hanji|ji haan|bilkul|of course)[!. ]*",
            clean, re.I,
        )
        if affirmative and (previous_intent == "kiss" or any(phrase in previous_response for phrase in (
            "written application", "happy now", "ab khush", "aur kiss", "another kiss",
        ))):
            choices = {
                "hinglish": [
                    "achha ji, written application bhi bharwaoge? 😭 form ka naam: 'bhawna se extra kisses ki darkhaast' 😂😘",
                    "haan ji, ek aur virtual kiss approved 😚 lekin paperwork ka drama tum sambhalna 🌚💕",
                    "itni jaldi 'yes'? 😂 *ek aur cheek kiss* lo ji, ab stamp bhi laga doon? 😘",
                ],
                "hi": [
                    "अच्छा जी, written application भी भरवाओगे? 😭 नाम होगा: 'Bhawna से extra kisses की दरख़ास्त' 😂😘",
                    "हाँ जी, एक और virtual kiss approved 😚 paperwork का drama तुम संभालना 🌚💕",
                    "इतनी जल्दी 'yes'? 😂 *एक और cheek kiss* लो जी, stamp भी लगा दूँ? 😘",
                ],
                "en": [
                    "oh, we're filing paperwork for extra kisses now? 😭 application approved, troublemaker 😂😘",
                    "yes ji, one more virtual kiss approved 😚 you can handle the paperwork drama 🌚💕",
                    "that was a quick yes 😂 *one more cheek kiss*—shall i stamp the form too? 😘",
                ],
            }
            return self._remember_reply(user_id, "affirmative_followup", choices.get(active_lang, choices["hinglish"]), active_lang)

        # Context-sensitive replies should run before the general expression list.
        if self.last_intent.get(user_id) == "what_matters" and re.fullmatch(
            r"(?:aap|tum|you|of\s+course\s+you|obviously\s+you|bas\s+tum|sirf\s+tum)[.! 💗🥹]*",
            clean,
            re.I,
        ):
            affection_pools = next((pools for intent, _pattern, pools in RULES if intent == "short_affection_answer"), None)
            return self._pick(user_id, "affectionate_reaction", active_lang, affection_pools)

        # Route specific v26 topics before legacy keyword catch-alls (such as
        # any occurrence of "lunch" or "job") only when this is not an explicit
        # direct turn like a greeting, boundary, affection, or roleplay cue.
        protected_direct = any(
            intent in _PROTECTED_DIRECT_INTENTS and pattern.search(clean)
            for intent, pattern, _pools in RULES
        )
        relationship_topic = None  # disabled in the Sonpari-AI public-safe edition

        # Preserve the v26 priority pre-pass for general topics, while keeping
        # direct greetings/affection/boundaries ahead of generic supplements.
        if not protected_direct:
            prioritized = self.conversation_hub.respond(
                original_clean, active_lang,
                previous_bot_response=self.last_bot_response.get(user_id, ""),
                previous_bot_intent=self.last_bot_intent.get(user_id, ""),
                previous_user_message=previous_user_message,
                only_intents=_PRIORITY_CONVERSATION_INTENTS,
            )
            if prioritized is not None:
                intent, text = prioritized
                return self._remember_reply(user_id, intent, text, active_lang)

        for intent, pattern, pools in RULES:
            if pattern.search(clean):
                if intent == "clarification":
                    return self._contextual_clarification(user_id, active_lang, pools)
                if intent == "filler_reaction" and re.fullmatch(r"(?:are+y+|arre+|are+)", clean, re.I):
                    arey_pools = {
                        "hinglish": ["arey kya ji 😂 itna suspense mat banao, poori baat bolo na", "arey, ab toh cliffhanger pe chhod diya 😭 aage bhi bolo", "haan baby, main sun rahi hoon 👀 ab aage bhi bolo"],
                        "hi": ["अरे क्या जी 😂 इतना suspense मत बनाओ, पूरी बात बताओ", "अरे, cliffhanger पर छोड़ दिया 😭 आगे भी बोलो", "हाँ जान, सुन रही हूँ 👀 आगे भी बोलो"],
                        "en": ["hey, don't leave me on a cliffhanger 😂 tell me the rest", "you can't just say 'arey' and disappear dramatically 😭 go on", "i'm listening 👀 don't make me guess"],
                    }
                    return self._pick(user_id, "filler_reaction", active_lang, arey_pools)
                if intent == "short_affection_answer" and self.last_intent.get(user_id) == "what_matters":
                    return self._pick(user_id, "affectionate_reaction", active_lang, pools)
                if intent == "acknowledgement" and previous_intent in {"love", "kiss", "hug", "flirty", "innuendo", "sexual_flirt"}:
                    contextual_ack = {
                        "hinglish": [
                            "bas itna sa 'acha ji'? 😭 meri itni sweet line ka review bhi de do, baby 💗",
                            "achha ji, ab sharma ke topic change mat karna 😂 tumhari baari—kuch cute bolo",
                            "haye, 'acha ji' bolke bach nahi sakte 😏 compliment return bhi karna padega",
                        ],
                        "hi": [
                            "बस इतना सा 'अच्छा जी'? 😭 मेरी sweet line का review भी दे दो, baby 💗",
                            "अच्छा जी, अब शर्माकर topic change मत करना 😂 अब तुम्हारी बारी है",
                            "'अच्छा जी' बोलकर बच नहीं सकते 😏 एक compliment वापस भी दो",
                        ],
                        "en": [
                            "just 'okay ji'? 😭 at least review my sweet line, baby 💗",
                            "don't get shy and change the topic now 😂 your turn—say something cute",
                            "you can't escape with just 'okay ji' 😏 return one compliment",
                        ],
                    }
                    return self._pick(user_id, "acknowledgement", active_lang, {
                        "hinglish": contextual_ack["hinglish"],
                        "hi": contextual_ack["hi"],
                        "en": contextual_ack["en"],
                    })
                reply = self._pick(user_id, intent, active_lang, pools)
                self.last_intent[user_id] = intent
                self.turns[user_id] = self.turns.get(user_id, 0) + 1
                return reply

        # Second-stage local coverage for conversational moves not in the
        # established rule packs; remains available with Groq and web disabled.
        hub_reply = self.conversation_hub.respond(
            original_clean, active_lang,
            previous_bot_response=self.last_bot_response.get(user_id, ""),
            previous_bot_intent=self.last_bot_intent.get(user_id, ""),
            previous_user_message=previous_user_message,
        )
        if hub_reply is not None:
            intent, text = hub_reply
            return self._remember_reply(user_id, intent, text, active_lang)

        # Very short emoji-only reactions should still get a warm response,
        # but unknown ordinary text can continue to the main YAML rule engine.
        if len(clean.split()) <= 3 and any(ch in original_clean for ch in "😂🤣😅😆😭💀🌚😏🥹💕"):
            # Check the original message for emojis because normalize_for_matching
            # may strip a leading reaction emoji to let anchored rules match.
            return self._pick(user_id, "laugh", active_lang)
        return None

    def note_intent(self, user_id: int, intent: str) -> None:
        """Record a prompt intent so the next short answer can be contextual."""
        self.last_intent[user_id] = intent

    def note_response(self, user_id: int, response: str, intent: str = "") -> None:
        """Remember the latest assistant turn for clarification and repetition fixes."""
        self.last_bot_response[user_id] = re.sub(r"\s+", " ", response.strip())[-600:]
        self.last_bot_intent[user_id] = intent

    def fallback(self, user_id: int, message: str, lang: str = DEFAULT_LANGUAGE) -> str:
        """Return a safe conversational fallback when neither rule engine matches."""
        language = self.effective_language(user_id, lang)
        clean = (message or "").strip()
        # Reference the user's actual last turn instead of inventing a random topic.
        if language == "hi":
            choices = [
                "हम्म, मैं तुम्हारी बात समझना चाहती हूँ—थोड़ा और बताओ ना 💗",
                "अच्छा जी 😭 शायद मैं बात पकड़ नहीं पाई। एक बार दूसरे तरीके से समझाओ?",
                "मैं सुन रही हूँ, जान। तुम्हारा मतलब क्या था?",
                "ये नया topic है मेरे लिए 😅 थोड़ा context दे दो, फिर साथ में बात करते हैं।",
                "अरे, मेरे offline दिमाग़ को एक hint चाहिए 😂 किस हिस्से पर बात करें?",
            ]
        elif language == "en":
            choices = [
                "hmm, i want to understand you properly—tell me a little more? 💗",
                "i think i missed your point 😭 can you phrase it another way?",
                "i'm listening, baby. what did you mean by that?",
                "that's a new topic for my little offline brain 😅 give me a hint and we'll figure it out",
                "give me one tiny clue 😂 which part should we talk about?",
            ]
        else:
            choices = [
                "hmm, main tumhari baat sahi se samajhna chahti hoon—thoda aur batao na 💗",
                "arey, shayad main point miss kar gayi 😭 ek baar doosre tareeke se bolo?",
                "main sun rahi hoon baby, tumhara matlab kya tha?",
                "ye mere offline dimaag ke liye naya topic hai 😅 thoda context do, saath mein samjhenge",
                "bas ek chhota sa hint de do 😂 kis part pe baat karein?",
            ]
        last = self.last_reply.get(user_id)
        options = [item for item in choices if item != last] or choices
        result = self.rng.choice(options)
        self.last_reply[user_id] = result
        self.last_intent[user_id] = "fallback"
        return result

    def _contextual_clarification(self, user_id: int, lang: str, pools) -> Reply:
        """Repair vague previous turns instead of stacking another vague question."""
        previous = self.last_bot_response.get(user_id, "").lower()
        if any(x in previous for x in ("what do you think", "is baare mein", "is baare me", "kis baare", "opinion")):
            if lang == "hi":
                text = "अरे, मैंने ही थोड़ा vague सवाल पूछ लिया 😭 मेरा मतलब था—आज तुम्हारे साथ क्या हुआ और अभी mood कैसा है?"
            elif lang == "en":
                text = "i made that question too vague, my bad 😭 i just meant: how's your day going and what's on your mind?"
            else:
                text = "arey, maine hi vague sawaal pooch liya 😭 mera matlab tha—aaj tumhare saath kya hua aur abhi mood kaisa hai?"
        elif any(x in previous for x in ("kaise ho", "how are you", "how's your day", "kya haal")):
            if lang == "hi":
                text = "बस तुम्हारा हाल पूछ रही थी जी 😭 mood कैसा है और दिन कैसा जा रहा है?"
            elif lang == "en":
                text = "i was just checking in 😭 how are you actually feeling, and how's the day going?"
            else:
                text = "bas tumhara haal pooch rahi thi ji 😭 mood kaisa hai aur din kaisa ja raha hai?"
        elif any(x in previous for x in ("kya chal raha", "aur batao", "tell me more", "what's up", "what is up")):
            if lang == "hi":
                text = "कुछ specific नहीं जी 😂 बस तुम्हारी day ki gossip सुननी थी—आज क्या scene है?"
            elif lang == "en":
                text = "nothing specific 😂 i just wanted your life update—what's the scene today?"
            else:
                text = "kuch specific nahi ji 😂 bas tumhari day ki gossip sunni thi—aaj kya scene hai?"
        else:
            options = pools.get(lang) or pools.get("hinglish") or next(iter(pools.values()))
            text = self._choose_text(user_id, options)
        return self._remember_reply(user_id, "clarification", text, lang)

    def _language_ack(self, language: str) -> list[str]:
        return {
            "hinglish": [
                "haan ji, ab se Hinglish mein hi baat karungi 😭💗 agar kabhi switch karna ho toh bas bol dena",
                "done, baby 😌 ab natural Hinglish mode on—robotic textbook Hindi nahi, promise 😂",
                "pakka ji 💗 Hinglish hi rahegi. ab batao, tum kya keh rahe the?",
            ],
            "hi": [
                "बिल्कुल जी 💗 अब से हिंदी में बात करूँगी। अगर भाषा बदलनी हो तो बस कह देना।",
                "ठीक है जान 😌 अब हिंदी में बात करेंगे—बताओ, क्या चल रहा है?",
            ],
            "en": [
                "of course, ji 💗 i'll stick to English from now on. just tell me if you'd like to switch again",
                "done, baby 😌 English mode on—what were you telling me?",
            ],
        }[language]

    def _language_auto_ack(self, language: str) -> list[str]:
        if language == "hi":
            return ["ठीक है जी, अब messages के हिसाब से भाषा चुनूँगी 💗", "ठीक है, language preference हटा दी—अब तुम जिस भाषा में लिखोगे, उसी में जवाब देने की कोशिश करूँगी।"]
        if language == "en":
            return ["okay ji, i'll follow the language you use from now on 💗", "done—automatic language selection is back on. i'll follow your messages."]
        return ["theek hai ji, ab tum jis language mein likhoge usi ke hisaab se reply karungi 💗", "done baby, auto language mode wapas on 😌"]

    def _remember_reply(self, user_id: int, intent: str, choices: list[str] | str, lang: str) -> Reply:
        text = self._choose_text(user_id, [choices] if isinstance(choices, str) else choices)
        self.last_intent[user_id] = intent
        self.turns[user_id] = self.turns.get(user_id, 0) + 1
        return Reply(text, intent)

    def _pick(self, user_id: int, intent: str, lang: str, pools=None) -> Reply:
        if pools is None:
            for key, _pattern, candidate in RULES:
                if key == intent:
                    pools = candidate
                    break
        pools = pools or RULES[0][2]
        language = lang if lang in pools else DEFAULT_LANGUAGE
        choices = pools[language]
        text = self._choose_text(user_id, choices)
        self.last_intent[user_id] = intent
        self.turns[user_id] = self.turns.get(user_id, 0) + 1
        return Reply(text=text, intent=intent)

    def _choose_text(self, user_id: int, choices: list[str]) -> str:
        previous = self.last_reply.get(user_id)
        alternatives = [item for item in choices if item != previous] or choices
        text = self.rng.choice(alternatives)
        self.last_reply[user_id] = text
        return text
