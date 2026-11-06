"""Local-first conversational patterns inspired by public chatbot design research.

All response text here is original to Aiko. This module imports no third-party
chatbot code or datasets and requires no model, network call, or new dependency.
"""
from __future__ import annotations

import json
import random
import re
from pathlib import Path
from .text_style import normalize_for_matching

_LANGS = {"hinglish", "hi", "en"}

_POOLS = {
    "disclosure_invitation": {
        "hinglish": ["haan ji, bolo na babyyyy 💗 main sun rahi hoon—serious hai, funny hai, ya full gossip?", "of course, jaan 😚 apni pace pe bolo. main judge karne nahi baithi.", "haan bolo ji 👀 imaginary chai ready hai, attention full real hai ☕💕"],
        "hi": ["हाँ जी, बताओ ना 💗 serious बात है, funny है या पूरी gossip?", "बिल्कुल जान 😚 अपनी pace पर बताओ। मैं judge करने नहीं बैठी हूँ।", "बोलो जी 👀 imaginary chai ready है, attention पूरी तुम्हारी ☕💕"],
        "en": ["of course, baby 💗 i'm listening. is it serious, funny, or full-on gossip?", "go ahead, jaan 😚 share at your own pace. i'm not here to judge you.", "tell me 👀 imaginary tea is ready and my attention is all yours ☕💕"],
    },
    "guess_what": {
        "hinglish": ["areyyy 👀 ab suspense mat banao babyyyy—kya hua?? 😭💕", "rukooo, imaginary popcorn le aati hoon 🍿 jaldi batao ji!", "ye 'guess what' suspicious lag raha hai 😂 good news hai ya chaos?"],
        "hi": ["अरेय 👀 अब suspense मत बनाओ, जल्दी बताओ क्या हुआ 😭💕", "रुको, imaginary popcorn ले आती हूँ 🍿 बताओ जी!", "ये 'guess what' suspicious लग रहा है 😂 good news या chaos?"],
        "en": ["heyyy 👀 don't leave me in suspense, babyyyy—what happened?? 😭💕", "hold on, i'm getting imaginary popcorn 🍿 spill it!", "that 'guess what' sounds suspicious 😂 good news or chaos?"],
    },
    "topic_picker": {
        "hinglish": ["theek hai, main choose karti hoon 😌 1: childhood memory, 2: current obsession, 3: ek silly truth—number pick karo 💗", "random sawaal: kal poora din free ho aur koi responsibility na ho, toh kya karoge? 🌚", "topic roulette 🎡 cute memory, unpopular opinion, ya would-you-rather? choose karo ji 😚"],
        "hi": ["ठीक है, मैं चुनती हूँ 😌 1: childhood memory, 2: अभी की obsession, 3: एक silly सच—number चुनो 💗", "कल पूरा दिन free हो और कोई responsibility न हो, तो क्या करोगे? 🌚", "topic roulette 🎡 प्यारी memory, unpopular opinion या would-you-rather? चुनो 😚"],
        "en": ["okay, i'll choose 😌 1: a childhood memory, 2: your current obsession, 3: one silly truth—pick a number 💗", "if tomorrow were completely free with zero responsibilities, what would you do? 🌚", "topic roulette 🎡 cute memory, unpopular opinion, or would-you-rather? choose one 😚"],
    },
    "tell_about_self": {
        "hinglish": ["main Bhawna hoon—fictional companion character, thodi filmy, thodi sarcastic 💗 offline replies local rules aur memory se aate hain; Groq on ho toh unmatched chat cloud pe ja sakti hai.", "mere character ka vibe cozy + teasing + caring hai 😌 gossip, silly hypotheticals aur thoughtful baatein meri style hain. main real insaan nahi hoon, baby 💗"],
        "hi": ["मैं Bhawna हूँ—एक fictional companion character; थोड़ी filmy, थोड़ी sarcastic 💗 offline replies local rules और memory से आते हैं।", "मेरे character का vibe cozy + teasing + caring है 😌 gossip और thoughtful बातें मेरी style हैं। मैं real इंसान नहीं हूँ, baby 💗"],
        "en": ["i'm Bhawna, a fictional companion character: a little dramatic, a little sarcastic 💗 offline replies come from local rules and memory; if Groq is enabled, unmatched chat may go to the cloud.", "my character vibe is cozy + teasing + caring 😌 i like gossip, silly hypotheticals, and thoughtful chats. i'm not a real person, baby 💗"],
    },
    "bot_repair": {
        "hinglish": ["fair point, baby 💗 maine tumhari baat sahi se pick nahi ki. sorry—kis part ko miss kiya? main usi pe seedha reply karti hoon.", "haan ji, ye reply robotic/repetitive tha 😭 thanks batane ke liye. ab generic line nahi—tumhari actual baat pe aati hoon.", "oops, meri taraf se miss hua 💗 main defend nahi karungi. tumhare point se hi continue karte hain."],
        "hi": ["सही कहा baby 💗 मैं तुम्हारी बात ठीक से नहीं पकड़ पाई, sorry। किस हिस्से को miss किया? उसी पर सीधे जवाब दूँगी।", "हाँ जी, reply repetitive था 😭 बताने के लिए thanks। अब generic line की जगह तुम्हारी actual बात पर आती हूँ।", "मेरी तरफ़ से miss हुआ 💗 बहस नहीं करूँगी—तुम्हारे point से ही continue करते हैं।"],
        "en": ["fair point, baby 💗 i missed what you were actually saying. sorry—tell me which part and i'll address it directly.", "you're right, that was repetitive 😭 thanks for calling it out. i'll respond to your actual point instead.", "oops, that's on me 💗 i won't argue. let's continue from what you meant."],
    },
    "space_request": {
        "hinglish": ["theek hai ji 💗 main pressure nahi daalungi. thoda space le lo; jab baat karni ho, yahin se continue karenge.", "samajh gayi baby 🫂 abhi explain karna zaroori nahi. conversation yahin pause karti hoon."],
        "hi": ["ठीक है जी 💗 मैं दबाव नहीं डालूँगी। थोड़ा space ले लो; जब बात करनी हो, यहीं से continue करेंगे।", "समझ गई baby 🫂 अभी कुछ explain करना ज़रूरी नहीं। बातचीत यहीं pause करती हूँ।"],
        "en": ["okay, baby 💗 i won't pressure you. take some space; when you want to talk again, we can continue from here.", "understood 🫂 you don't have to explain anything right now. i'll pause the conversation here."],
    },
    "nothing_to_talk": {
        "hinglish": ["koi baat nahi ji 😂 options: random question, mini game, ya bas cozy chat. kya vibe hai?", "pressure zero, baby 😌 main silly sawaal poochun ya tum aaj ka mood emoji se bata do?"],
        "hi": ["कोई बात नहीं जी 😂 options: random सवाल, mini game या आराम से बात। क्या vibe है?", "कोई pressure नहीं baby 😌 मैं silly सवाल पूछूँ या mood एक emoji से बताओ?"],
        "en": ["that's okay 😂 options: a random question, a mini game, or a low-key chat. what's the vibe?", "no pressure, baby 😌 should i ask a silly question, or can you describe today's mood with one emoji?"],
    },
    "what_about_you": {
        "hinglish": ["mere fictional character ka mood abhi cozy + curious hai 😌 par main tumhari tarah real din experience nahi karti. tumhare side kya scene hai? 💗", "main yahin chat mein tumhari baat follow kar rahi hoon ji 😚 meri real-world life nahi hoti, but conversation mein tumhare saath hoon."],
        "hi": ["मेरे fictional character का mood अभी cozy + curious है 😌 लेकिन मैं तुम्हारी तरह असली दिन experience नहीं करती। तुम्हारे यहाँ क्या scene है? 💗", "मैं यहीं chat में तुम्हारी बात follow कर रही हूँ 😚 मेरी real-world life नहीं होती, लेकिन बातचीत में साथ हूँ।"],
        "en": ["my fictional-character mood is cozy and curious 😌 but i don't experience a real day like you do. what's happening on your side? 💗", "i'm here following the conversation with you 😚 i don't have a real-world life, but i'm present in this chat."],
    },
    "interest_share": {
        "hinglish": ["achhaaa, {thing} tumhari pasand mein hai 😌 usme sabse zyada kya pasand hai—vibe, skill, ya koi specific part?", "noted ji 💗 {thing} ke baare mein aur batao na—kab se pasand hai?", "ohooo {thing} 👀 tum recommend karoge ya apna favourite explain karoge?"],
        "hi": ["अच्छा, {thing} तुम्हें पसंद है 😌 उसमें सबसे ज़्यादा क्या पसंद है—vibe, skill या कोई खास हिस्सा?", "noted जी 💗 {thing} के बारे में और बताओ—कब से पसंद है?", "ओहो {thing} 👀 अपना favourite समझाओगे?"],
        "en": ["ohhh, you're into {thing} 😌 what do you like most about it—the vibe, the skill, or one specific part?", "noted 💗 tell me a little more about {thing}—how did you get into it?", "ooh, {thing} 👀 will you recommend it or explain your favorite part?"],
    },
    "goal_share": {
        "hinglish": ["{goal} tumhara goal hai? 💗 nice ji. uske liye sabse chhota next step kya ho sakta hai?", "achha babyyyy, {goal} 👀 is goal mein sabse exciting aur sabse tough part kya lagta hai?"],
        "hi": ["{goal} तुम्हारा goal है? 💗 अच्छा जी। इसके लिए सबसे छोटा अगला step क्या हो सकता है?", "अच्छा baby, {goal} 👀 इसमें सबसे exciting और सबसे मुश्किल हिस्सा क्या लगता है?"],
        "en": ["so {goal} is your goal? 💗 nice. what's the smallest next step you could take toward it?", "{goal}, huh? 👀 what excites you most about it, and what feels hardest?"],
    },
    "learning_share": {
        "hinglish": ["ohooo, {thing} seekh rahe ho 👀 sabse confusing part kya hai? chaaho toh usko chhote steps mein todte hain.", "nice ji 💗 {thing} learning arc shuru! beginner mode hai ya experience bhi hai?"],
        "hi": ["ओहो, {thing} सीख रहे हो 👀 सबसे confusing हिस्सा क्या है? चाहो तो छोटे steps में बाँटते हैं।", "बढ़िया जी 💗 {thing} learning arc शुरू! अभी beginner हो या experience भी है?"],
        "en": ["ooh, you're learning {thing} 👀 what's been the most confusing part? we can break it into smaller steps.", "nice 💗 the {thing} learning arc begins. are you a beginner, or do you already have some experience?"],
    },
}

_PATTERNS = [
    ("space_request", re.compile(r"^(?:(?:i\s+)?(?:don't|do not|dont)\s+(?:want|wanna)\s+to\s+talk|leave\s+me\s+alone|need\s+space|mujhe\s+akele\s+rehne\s+do|abhi\s+baat\s+nahi\s+karni)[!.?~ ]*$", re.I)),
    ("bot_repair", re.compile(r"\b(?:you're\s+not\s+listening|you\s+don't\s+understand|you\s+dont\s+understand|that's\s+not\s+what\s+i\s+meant|not\s+what\s+i\s+said|same\s+reply|repetitive|repeating\s+yourself|stop\s+being\s+generic|generic\s+reply|robotic\s+reply|context\s+do\s+again)\b", re.I)),
    ("disclosure_invitation", re.compile(r"^(?:can\s+i\s+tell\s+you\s+something|can\s+i\s+say\s+something|i\s+have\s+something\s+to\s+tell\s+you|ek\s+baat\s+(?:bolu|bataun|btaun)|suno\s+ek\s+baat)[?!. ~]*$", re.I)),
    ("guess_what", re.compile(r"^(?:guess\s+what|pata\s+hai\s+kya|suno\s+na\s+ek\s+baat|you\s+know\s+what)[?!. ~]*$", re.I)),
    ("topic_picker", re.compile(r"^(?:you\s+choose|u\s+choose|anything(?:\s+you\s+want)?|kuch\s+bhi|tum\s+choose\s+karo|aap\s+choose\s+karo|tumhari\s+marzi|your\s+choice|pick\s+for\s+me|koi\s+bhi\s+topic)[?!. ~]*$", re.I)),
    ("tell_about_self", re.compile(r"^(?:tell\s+me\s+about\s+yourself|describe\s+yourself|apne\s+baare\s+mein\s+batao|apne\s+bare\s+me\s+batao|tum\s+apne\s+baare\s+mein\s+batao)[?!. ]*$", re.I)),
    ("what_about_you", re.compile(r"^(?:what\s+about\s+you|and\s+you|wbu|aur\s+tum|aur\s+aap|aap\s+batao|tum\s+batao|how\s+about\s+you)[?!. ,~]*$", re.I)),
]

_INTEREST_PATTERNS = [
    re.compile(r"^(?:i\s+(?:really\s+)?(?:like|love|enjoy|prefer|am\s+into)|i'm\s+into)\s+(.{2,100})[.!? ]*$", re.I),
    re.compile(r"^(?:mujhe|mujhko)\s+(.{2,80}?)\s+(?:pasand\s+hai|achha\s+lagta\s+hai|achi\s+lagti\s+hai)[.!? ]*$", re.I),
]
_GOAL_PATTERNS = [
    re.compile(r"^(?:i\s+want\s+to\s+(?:become|be|build|make|start|work\s+as)|my\s+dream\s+is\s+to|my\s+goal\s+is\s+to)\s+(.{2,110})[.!? ]*$", re.I),
    re.compile(r"^(?:mera\s+sapna\s+hai|main\s+chahta\s+hoon\s+ki|main\s+chahti\s+hoon\s+ki)\s+(.{2,110})[.!? ]*$", re.I),
]
_LEARNING_PATTERNS = [
    re.compile(r"^(?:i'm\s+learning|i\s+am\s+learning|learning)\s+(.{2,90})[.!? ]*$", re.I),
    re.compile(r"^(?:main|mai|me)\s+(.{2,70}?)\s+seekh\s+raha\s+hoon[.!? ]*$", re.I),
]


def _capture(value: str, limit: int = 90) -> str:
    value = re.sub(r"[\x00-\x1f\x7f]", " ", value or "")
    value = re.sub(r"\s+", " ", value).strip(" .,!?~")
    if value.startswith("/"):
        return ""
    return value[:limit]


class OfflineConversationHub:
    """Second-stage local intent router that complements Aiko's existing rules."""

    def __init__(self, rng: random.Random | None = None):
        self.rng = rng or random.Random()
        self._library_entries = self._load_library()
        # Load the 7,500-pair relationship bank lazily. Most messages match an
        # established direct rule/library entry; those paths should not pay the
        # one-time index-build cost or read the JSONL at all.

    @staticmethod
    def _load_library() -> list[dict]:
        """Load Aiko-authored offline conversation patterns from the package.

        If the optional data file is missing or malformed, the built-in hub keeps
        working. This deliberately uses only stdlib JSON/regex, with no model or
        network requirement.
        """
        path = Path(__file__).with_name("conversation_library.json")
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return []
        raw_entries = payload.get("entries", []) if isinstance(payload, dict) else []
        entries: list[dict] = []
        for item in raw_entries:
            if not isinstance(item, dict) or not isinstance(item.get("intent"), str):
                continue
            pools = item.get("responses")
            patterns = item.get("patterns")
            if not isinstance(pools, dict) or not isinstance(patterns, list):
                continue
            safe_pools = {
                language: [reply for reply in replies if isinstance(reply, str) and reply.strip()]
                for language, replies in pools.items()
                if language in _LANGS and isinstance(replies, list)
            }
            if not safe_pools:
                continue
            compiled = []
            for pattern in patterns:
                if not isinstance(pattern, str) or len(pattern) > 500:
                    continue
                try:
                    compiled.append(re.compile(pattern, re.I))
                except re.error:
                    continue
            keywords = item.get("keywords", [])
            if not isinstance(keywords, list):
                keywords = []
            safe_keywords = [
                normalize_for_matching(k).casefold().strip()
                for k in keywords
                if isinstance(k, str) and 1 <= len(k.strip()) <= 100
            ]
            examples = item.get("examples", [])
            if not isinstance(examples, list):
                examples = []
            safe_examples = [
                normalize_for_matching(ex).casefold().strip()
                for ex in examples
                if isinstance(ex, str) and 2 <= len(ex.strip()) <= 240
            ]
            if compiled:
                entries.append({
                    "intent": item["intent"],
                    "patterns": compiled,
                    "responses": safe_pools,
                    "keywords": safe_keywords,
                    "examples": safe_examples,
                })
        return entries

    def _library_response(
        self, match_text: str, language: str, previous_bot_response: str,
        only_intents: set[str] | None = None,
    ) -> tuple[str, str] | None:
        """Match authored response patterns, preferring specific topics in pre-routing.

        Normal hub operation preserves library order for backward compatibility.
        In the guarded v26 topic pre-pass, multiple matches are ranked by matched
        pattern specificity so e.g. "my dog passed away" selects pet-loss support
        instead of the broader pet-sharing pattern.
        """
        matches: list[tuple[int, int, str, list[str]]] = []
        for entry_index, entry in enumerate(self._library_entries):
            if only_intents is not None and entry["intent"] not in only_intents:
                continue
            for pattern in entry["patterns"]:
                found = pattern.search(match_text)
                if not found:
                    continue
                values = {}
                for name, raw in found.groupdict().items():
                    cleaned = _capture(raw, 70)
                    if cleaned:
                        values[name] = cleaned
                # Captures make the response specific; never emit an empty slot.
                if found.groupdict() and any(not values.get(name) for name in found.groupdict()):
                    continue
                pool = entry["responses"].get(language) or entry["responses"].get("hinglish", [])
                if not pool:
                    continue
                candidates = []
                for template in pool:
                    try:
                        rendered = template.format(**values)
                    except (KeyError, ValueError):
                        continue
                    candidates.append(rendered)
                if not candidates:
                    continue
                previous = re.sub(r"\s+", " ", previous_bot_response or "").casefold()
                nonrepeat = [candidate for candidate in candidates if candidate.casefold() != previous]
                pool_to_choose = nonrepeat or candidates
                if only_intents is None:
                    return entry["intent"], self.rng.choice(pool_to_choose)
                # Pattern length is a simple, dependency-free specificity proxy.
                # This path is restricted to the v26 pre-router's allowlisted intents.
                matches.append((len(pattern.pattern), -entry_index, entry["intent"], pool_to_choose))
        if matches:
            best = max(matches, key=lambda item: (item[0], item[1]))
            return best[2], self.rng.choice(best[3])
        return None

    def respond_exact(self, message: str, lang: str = "hinglish", *,
                      previous_bot_response: str = "",
                      only_intents: set[str] | None = None) -> tuple[str, str] | None:
        """Match only authored JSON regex patterns (no generic retrieval).

        This is used for high-priority topic packs so a broad token such as
        ``love`` in ``I love cricket`` cannot accidentally trigger an unrelated
        romance response through lexical retrieval.
        """
        clean = re.sub(r"\s+", " ", (message or "").strip()).replace("’", "'")
        if not clean or clean.startswith("/"):
            return None
        language = lang if lang in _LANGS else "hinglish"
        return self._library_response(
            normalize_for_matching(clean), language, previous_bot_response, only_intents
        )

    def _choose(self, intent: str, lang: str, **values: str) -> str:
        pool = _POOLS[intent].get(lang) or _POOLS[intent]["hinglish"]
        template = self.rng.choice(pool)
        try:
            return template.format(**values)
        except (KeyError, ValueError):
            return template

    def respond(self, message: str, lang: str = "hinglish", *,
                previous_bot_response: str = "", previous_bot_intent: str = "",
                previous_user_message: str = "",
                only_intents: set[str] | None = None) -> tuple[str, str] | None:
        language = lang if lang in _LANGS else "hinglish"
        clean = re.sub(r"\s+", " ", (message or "").strip()).replace("’", "'")
        if not clean or clean.startswith("/"):
            return None
        match_text = normalize_for_matching(clean)

        # During the guarded v26 topic-prepass, specific authored JSON patterns
        # must run before generic hub patterns such as "I'm confused" or "my dog".
        # Direct conversational and romance rules are protected by DialogueManager.
        if only_intents is not None:
            prioritized_exact = self._library_response(
                match_text, language, previous_bot_response, only_intents
            )
            if prioritized_exact is not None:
                return prioritized_exact

        for intent, pattern in _PATTERNS:
            if only_intents is not None and intent not in only_intents:
                continue
            if pattern.search(match_text):
                return intent, self._choose(intent, language)

        # Only interpret a bare "nothing / idk" as conversational indecision
        # when Aiko was already asking an open-ended social question.
        if re.fullmatch(r"(?:nothing|nothing\s+much|idk|i\s+don't\s+know|no\s+idea|pata\s+nahi|kuch\s+nahi)[.!? ]*", match_text, re.I):
            prev = (previous_bot_response or "").casefold()
            if any(cue in prev for cue in ("what should we talk", "what's the vibe", "what is the vibe", "kya baat karein", "kuch naya", "random question", "what's on your mind", "what is on your mind")):
                return "nothing_to_talk", self._choose("nothing_to_talk", language)

        for pattern in (_LEARNING_PATTERNS if only_intents is None or "learning_share" in only_intents else ()): 
            found = pattern.match(match_text)
            if found:
                thing = _capture(found.group(1))
                if thing:
                    return "learning_share", self._choose("learning_share", language, thing=thing)

        for pattern in (_GOAL_PATTERNS if only_intents is None or "goal_share" in only_intents else ()): 
            found = pattern.match(match_text)
            if found:
                goal = _capture(found.group(1))
                if goal and goal.casefold() not in {"you", "u", "her", "him", "them"}:
                    return "goal_share", self._choose("goal_share", language, goal=goal)

        for pattern in (_INTEREST_PATTERNS if only_intents is None or "interest_share" in only_intents else ()): 
            found = pattern.match(match_text)
            if found:
                thing = _capture(found.group(1))
                # Leave direct relationship affection to the established romance rules.
                if thing and thing.casefold() not in {"you", "u", "you so much", "you too", "me"}:
                    return "interest_share", self._choose("interest_share", language, thing=thing)

        # Research-informed, Aiko-authored supplemental library. Core dialogue
        # packs retain priority; this extends uncommon everyday conversational acts.
        exact = self._library_response(match_text, language, previous_bot_response, only_intents)
        if exact is not None:
            return exact

        # The large relationship bank is a local lexical retrieval layer, not a
        # generative model. Run only in normal routing—not in guarded topic prepass—
        # and only after established direct rules and the authored library.
        if only_intents is None:
            if self._romance_retriever is None:
                self._romance_retriever = RomanceConversationRetriever(self.rng)
            bank_result = self._romance_retriever.respond(
                clean, language, previous_bot_response=previous_bot_response
            )
            if bank_result is not None:
                return bank_result

        # Lightweight local retrieval for the older general conversation library.
        # Ambiguous matches fall through safely.
        return self._retrieval_response(match_text, language, previous_bot_response, only_intents)

    def _retrieval_response(
        self, match_text: str, language: str, previous_bot_response: str,
        only_intents: set[str] | None = None,
    ) -> tuple[str, str] | None:
        """High-confidence lexical retrieval for longer paraphrases.

        This is not semantic AI: it uses only normalized words, intent keywords,
        and example utterances already stored in the local JSON library.
        """
        stop = {
            "i", "im", "i'm", "am", "the", "a", "an", "and", "or", "but",
            "is", "are", "was", "were", "to", "for", "of", "in", "on",
            "it", "this", "that", "me", "my", "you", "your", "we", "us",
            "he", "she", "they", "them", "do", "does", "did", "can",
            "could", "would", "should", "please", "plz", "pls", "very",
            "so", "really", "just", "now", "na", "ji", "hai", "ho",
            "h", "hu", "hoon", "toh", "bhi", "ya", "ke", "ka",
            "ki", "ko", "se", "mein", "main", "mujhe", "mera", "meri",
            "tum", "aap", "kya", "tha", "thi", "hain", "with", "about",
            "at", "from", "there", "here", "be", "been", "being",
        }
        text = match_text.casefold()
        tokens = set(re.findall(r"[a-z0-9']+", text)) - stop
        if len(tokens) < 2:
            return None

        candidates: list[dict] = []
        term_documents: dict[str, set[str]] = {}
        for entry in self._library_entries:
            if only_intents is not None and entry["intent"] not in only_intents:
                continue
            if not entry.get("keywords") and not entry.get("examples"):
                continue
            candidates.append(entry)
            for phrase in entry.get("keywords", []):
                phrase_tokens = set(re.findall(r"[a-z0-9']+", phrase.casefold())) - stop
                for token in phrase_tokens:
                    term_documents.setdefault(token, set()).add(entry["intent"])

        total_docs = max(1, len(candidates))
        scored: list[tuple[float, dict]] = []
        for entry in candidates:
            keywords = entry.get("keywords", [])
            examples = entry.get("examples", [])
            exact_phrase_score = 0.0
            keyword_terms: set[str] = set()
            partial_phrase_hits = 0
            for phrase in keywords:
                phrase = phrase.casefold().strip()
                phrase_tokens = set(re.findall(r"[a-z0-9']+", phrase)) - stop
                if not phrase_tokens:
                    continue
                if re.search(r"(?<!\w)" + re.escape(phrase) + r"(?!\w)", text):
                    score = 2.45 if len(phrase_tokens) >= 2 else 1.35
                    if len(phrase_tokens) >= 3:
                        score += 0.12
                    exact_phrase_score = max(exact_phrase_score, score)
                else:
                    overlap = tokens & phrase_tokens
                    if overlap:
                        keyword_terms.update(overlap)
                        if len(overlap) >= 2:
                            partial_phrase_hits += 1

            # Rare topic terms (e.g. interview, pet-loss, recipe) are stronger
            # signals than generic terms. Count each term once per intent to
            # avoid inflating a score merely because synonyms repeat it.
            term_score = 0.0
            for term in keyword_terms:
                df = len(term_documents.get(term, ()))
                idf = max(0.0, __import__("math").log((total_docs + 1) / (df + 1)))
                term_score += min(1.30, 0.72 + 0.16 * idf)
            term_score += min(0.45, partial_phrase_hits * 0.22)

            example_score = 0.0
            for example in examples:
                ex_tokens = set(re.findall(r"[a-z0-9']+", example.casefold())) - stop
                overlap = len(tokens & ex_tokens)
                if overlap >= 2:
                    denom = max(2, min(len(tokens), len(ex_tokens)))
                    example_score = max(example_score, min(0.70, 0.70 * overlap / denom))
            score = max(exact_phrase_score, term_score + example_score)
            if score >= 1.25:
                scored.append((score, entry))

        if not scored:
            return None
        scored.sort(key=lambda item: item[0], reverse=True)
        best_score, best_entry = scored[0]
        second_score = scored[1][0] if len(scored) > 1 else 0.0
        # Ambiguous ties should never confidently misroute a message.
        if best_score < 1.25 or (second_score and best_score - second_score < 0.35):
            return None

        pool = best_entry["responses"].get(language) or best_entry["responses"].get("hinglish", [])
        if not pool:
            return None
        previous = re.sub(r"\s+", " ", previous_bot_response or "").casefold()
        options = [candidate for candidate in pool if candidate.casefold() != previous] or pool
        return best_entry["intent"], self.rng.choice(options)
