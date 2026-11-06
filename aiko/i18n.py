from __future__ import annotations
from .language import DEFAULT_LANGUAGE

# Single-string UI messages (commands, memory acknowledgements, ...).
# Placeholders use ``{name}`` style and are filled by ``text()``.
STRINGS = {
    "start": {
        "en": "heyyy, i'm {name}~ your cozy fictional chat buddy. tell me about your day 💕",
        "hi": "हेय्य, मैं {name} हूँ~ तुम्हारी कोज़ी काल्पनिक चैट बडी। अपने दिन के बारे में बताओ 💕",
        "hinglish": "heyyy ji~ main {name} hoon, tumhari fictional offline chat companion 💕 batao, din kaisa tha? 🙈",
    },
    "help": {
        "en": "commands: /role /pass <code> /unpass /checkin <1-10> /mood /affection /stats /name <name> /memory /forget /forgetall /export /joke /games /riddle /rps /daily /complete /streak /badges /trivia /triviaanswer /prefs /privacy /health /backup /revoke /personality /quiet /loud /reset /web auto|always|off /search <prompt> /translate <target> | <text> /help 💗\n/pass unlocks BF-style chat in private messages; /role shows your current Friend/BF mode. /translate translates text to a requested language; this sends only the requested text to a keyless external translation service. /web controls English web queries + reply inspiration; /search searches one prompt. /context shows local conversation learning; /forgetchat clears it. Destructive actions ask for confirmation.",
        "hi": "कमांड: /role /pass <code> /unpass /checkin <1-10> /mood /affection /stats /name <नाम> /memory /forget /forgetall /export /joke /games /riddle /rps /daily /complete /streak /badges /trivia /triviaanswer /prefs /privacy /health /backup /revoke /personality /quiet /loud /reset /web auto|always|off /search <prompt> /translate <target> | <text> /help 💗",
        "hinglish": "commands: /role /pass <code> /unpass /checkin <1-10> /mood /affection /stats /name <naam> /memory /forget /forgetall /export /joke /games /riddle /rps /daily /complete /streak /badges /trivia /triviaanswer /prefs /privacy /health /backup /revoke /personality /quiet /loud /reset /web auto|always|off /search <prompt> /translate <target> | <text> /help 💗\n/pass private chat mein BF-style replies unlock karta hai; /role current mode dikhata hai. /translate translates text to a requested language; this sends only the requested text to a keyless external translation service. /web English web search aur reply-inspiration control karta hai; /search ek prompt search karta hai. /context local learning dikhata hai; /forgetchat usse clear karta hai. /forgetall confirmation maangega.",
    },
    "mood_neutral": {
        "en": "pretty calm right now~",
        "hi": "अभी काफ़ी शांत हूँ~",
        "hinglish": "abhi kaafi shaant hoon~",
    },
    "mood_happy": {
        "en": "i'm feeling sunny today ✨",
        "hi": "आज मूड बहुत अच्छा है ✨",
        "hinglish": "aaj mood bahut acha hai ✨",
    },
    "mood_playful": {
        "en": "i'm in a teasing little mood~",
        "hi": "थोड़ी शरारती मूड में हूँ~",
        "hinglish": "thodi shararati mood mein hoon~",
    },
    "mood_flirty": {
        "en": "maybe a little blushy, don't get smug 😳",
        "hi": "शायद थोड़ी शरमा रही हूँ, ज़्यादा मत मुस्कुरा 😳",
        "hinglish": "shayad thodi sharma rahi hoon, zyada mat muskura 😳",
    },
    "mood_sleepy": {
        "en": "sleepy... coffee would help",
        "hi": "नींद आ रही है... कॉफी से मदद मिलेगी",
        "hinglish": "neend aa rahi hai... coffee se madad milegi",
    },
    "mood_worried": {
        "en": "a little concerned, but i'm listening",
        "hi": "थोड़ी चिंतित हूँ, पर सुन रही हूँ",
        "hinglish": "thodi chintit hoon, par sun rahi hoon",
    },
    "mood_pouty": {
        "en": "hmph. tiny pout mode.",
        "hi": "ह्म्फ। छोटा सा नखरे मोड।",
        "hinglish": "hmph. chhota sa nakhre mode.",
    },
    "mood_affectionate": {
        "en": "soft and affectionate today 💗",
        "hi": "आज नरम और प्यार भरी मूड में 💗",
        "hinglish": "aaj narm aur pyaar bhari mood mein 💗",
    },
    "aff_distant": {
        "en": "we're still getting to know each other~",
        "hi": "हम अभी एक-दूसरे को जानने लगे हैं~",
        "hinglish": "hum abhi ek-doosre ko jaanne lage hain~",
    },
    "aff_warm": {
        "en": "i'm getting comfy chatting with you 💗",
        "hi": "तुमसे बात करके अच्छा लग रहा है 💗",
        "hinglish": "tumse baat karke acha lag raha hai 💗",
    },
    "aff_affectionate": {
        "en": "you're becoming a familiar little comfort",
        "hi": "तुम एक प्यारी आदत बन रहे हो",
        "hinglish": "tum ek pyaari aadat ban rahe ho",
    },
    "aff_deeply_attached": {
        "en": "you're very dear to this cozy corner of mine 🫂",
        "hi": "तुम मेरे इस कोज़ी कोने के बहुत क़रीब हो 🫂",
        "hinglish": "tum mere is cozy kone ke bahut qareeb ho 🫂",
    },
    "stats": {
        "en": "Stats\nAffection: {affection}/100\nMood: {mood}\nDays together: {days}\nMessages: {messages}\nFacts stored: {facts}",
        "hi": "आँकड़े\nप्यार: {affection}/100\nमूड: {mood}\nसाथ के दिन: {days}\nसंदेश: {messages}\nसहेजे तथ्य: {facts}",
        "hinglish": "Stats\nAffection: {affection}/100\nMood: {mood}\nSaath ke din: {days}\nMessages: {messages}\nSaved facts: {facts}",
    },
    "no_stats": {
        "en": "no stats yet—try /start first.",
        "hi": "अभी कोई आँकड़े नहीं—पहले /start करो।",
        "hinglish": "abhi koi stats nahi—pehle /start karo.",
    },
    "quiet": {
        "en": "okay, i'll stay quiet unless you message me 💗",
        "hi": "ठीक है, जब तक तुम मैसेज नहीं करते मैं चुप रहूँगी 💗",
        "hinglish": "theek hai, jab tak tum message nahi karte main chup rahungi 💗",
    },
    "loud": {
        "en": "okayyy~ little check-ins are back on ✨",
        "hi": "ओकेए~ छोटी-छोटी चेक-इन वापस शुरू ✨",
        "hinglish": "okayyy~ chhoti-chhoti check-ins waapas shuru ✨",
    },
}

STRINGS.update({
    "name_usage": {
        "en": "use /name followed by the name you'd like me to use~",
        "hi": "/name के बाद वो नाम लिखो जो तुम चाहते हो मैं इस्तेमाल करूँ~",
        "hinglish": "/name ke baad wo naam likho jo tum chahte ho main istemaal karoon~",
    },
    "name_set": {
        "en": "got it, {name} 💕",
        "hi": "समझ गई, {name} 💕",
        "hinglish": "samajh gayi, {name} 💕",
    },
    "reset_ask": {
        "en": "reset my mood and affection? say /confirm_reset if you're sure.",
        "hi": "मूड और प्यार रीसेट कर दूँ? अगर पक्का है तो /confirm_reset बोलो।",
        "hinglish": "mood aur affection reset kar doon? agar pakka hai to /confirm_reset bolo.",
    },
    "reset_none": {
        "en": "nothing waiting to reset~",
        "hi": "रीसेट के लिए कुछ नहीं बाकी~",
        "hinglish": "reset ke liye kuch nahi baaki~",
    },
    "reset_done": {
        "en": "fresh start, gently~ 💗",
        "hi": "नई शुरुआत, नरमी से~ 💗",
        "hinglish": "nayi shuruaat, narmi se~ 💗",
    },
    "forget_ask": {
        "en": "this deletes every saved fact about you. use /confirm_forget if you're sure.",
        "hi": "इससे तुम्हारे बारे में हर सहेजा तथ्य मिट जाएगा। पक्का हो तो /confirm_forget करो।",
        "hinglish": "isse tumhare baare mein har saved fact mit jaayega. pakka ho to /confirm_forget karo.",
    },
    "forget_none": {
        "en": "nothing waiting to forget~",
        "hi": "भूलने के लिए कुछ नहीं बाकी~",
        "hinglish": "bhoolne ke liye kuch nahi baaki~",
    },
    "forget_done": {
        "en": "all saved facts are gone. clean slate 🫂",
        "hi": "सारे सहेजे तथ्य मिट गए। साफ़ शुरुआत 🫂",
        "hinglish": "saare saved facts mit gaye. saaf shuruaat 🫂",
    },
    "memory_new": {
        "en": "got it, {value} 💗 i'll keep that in mind.",
        "hi": "समझ गई, {value} 💗 मैं याद रखूँगी।",
        "hinglish": "samajh gayi, {value} 💗 main yaad rakhungi.",
    },
    "memory_old": {
        "en": "wait, i thought you said {old}? 👀 okay, i'll update that~",
        "hi": "रुको, तुमने तो {old} कहा था? 👀 ठीक है, अपडेट करती हूँ~",
        "hinglish": "ruko, tumne to {old} kaha tha? 👀 theek hai, update karti hoon~",
    },
})


# Media acknowledgement pools keyed by attachment kind then language.
MEDIA = {
    "photo": {
        "en": ["oooh, a photo! tell me the story behind it~ 💕",
               "i can't inspect the image, but i'm curious what it shows"],
        "hi": ["ओह, एक फोटो! पीछे की कहानी बताओ~ 💕",
               "मैं इमेज नहीं देख सकती, पर दिखाती क्या है यह जानती हूँ"],
        "hinglish": ["ooh, ek photo! peeche ki kahani batao~ 💕",
                     "main image inspect nahi kar sakti, par dikhati kya hai ye jaan-na chahti hoon"],
    },
    "sticker": {
        "en": ["sticker received!! ✨", "that sticker has a whole personality"],
        "hi": ["स्टिकर मिला!! ✨", "इस स्टिकर में पूरी personality है"],
        "hinglish": ["sticker mila!! ✨", "is sticker mein poori personality hai"],
    },
    "voice": {
        "en": ["i can't listen to voice notes here—could you type the important bit?"],
        "hi": ["यहाँ मैं वॉइस नोट नहीं सुन सकती—ज़रूरी बात टाइप कर दोगे?"],
        "hinglish": ["yahan main voice note nahi sun sakti—zaroori baat type kar doge?"],
    },
    "animation": {
        "en": ["hehe, a little animation~", "i can't analyze it, but tell me what happens in it"],
        "hi": ["हेहे, एक छोटी सी एनिमेशन~", "मैं इसे एनालाइज़ नहीं कर सकती, पर अंदर क्या होता है बताओ"],
        "hinglish": ["hehe, ek chhoti si animation~", "main ise analyze nahi kar sakti, par andar kya hota hai batao"],
    },
    "document": {
        "en": ["file received~ what would you like me to know about it?",
               "i won't download it, but you can describe it to me"],
        "hi": ["फाइल मिली~ इसमें क्या बताना चाहोगे?",
               "मैं इसे डाउनलोड नहीं करूँगी, पर तुम मुझे बता सकते हो"],
        "hinglish": ["file mili~ ismein kya bataana chahoge?",
                     "main ise download nahi karungi, par tum mujhe bata sakte ho"],
    },
}


def text(key: str, lang: str, **kwargs) -> str:
    """Return a localized single string, filling ``{placeholders}``.

    Falls back to English when the language or key is missing.
    """
    table = STRINGS.get(key, {})
    value = table.get(lang) or table.get(DEFAULT_LANGUAGE, "")
    if kwargs:
        try:
            return value.format(**kwargs)
        except (KeyError, IndexError, ValueError):
            return value
    return value


def media_pool(kind: str, lang: str) -> list[str]:
    """Return the media acknowledgement pool for a kind/language (English fallback)."""
    pools = MEDIA.get(kind) or MEDIA["document"]
    return pools.get(lang) or pools.get(DEFAULT_LANGUAGE) or ["received~"]

