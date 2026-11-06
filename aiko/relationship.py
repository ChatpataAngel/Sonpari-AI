"""Role-specific relationship reply helpers; no Telegram dependency."""
from __future__ import annotations
import re

def local_friend_reply(message: str, lang: str) -> str:
    """Deterministic platonic fallback used when no AI provider is available."""
    text = (message or "").casefold().strip()
    if lang == "hi":
        replies = {
            "greeting": "नमस्ते यार 😊 कैसे हो?",
            "mood": "मैं ठीक हूँ, पूछने के लिए शुक्रिया 😊 तुम्हारा दिन कैसा जा रहा है?",
            "sad": "अरे यार, सुनकर बुरा लगा 🫂 क्या हुआ? मैं दोस्त की तरह सुन रही हूँ।",
            "thanks": "कोई बात नहीं यार 💛 मदद करके अच्छा लगा।",
            "bye": "अपना ध्यान रखना यार 👋 फिर बात करेंगे।",
            "default": "समझ गई यार 😊 थोड़ा और बताओ ताकि मैं बेहतर मदद कर सकूँ।",
        }
    elif lang == "en":
        replies = {
            "greeting": "hey! 😊 how's it going?",
            "mood": "i'm doing well, thanks for asking 😊 how has your day been?",
            "sad": "i'm sorry you're dealing with that 🫂 want to tell me what happened? i'll listen as a friend.",
            "thanks": "you're welcome! 💛 glad i could help.",
            "bye": "take care, friend 👋 talk to you later.",
            "default": "i hear you 😊 tell me a little more so i can help you better.",
        }
    else:
        replies = {
            "greeting": "hey yaar 😊 kya haal-chaal?",
            "mood": "main theek hoon, poochhne ke liye thanks 😊 tumhara din kaisa ja raha hai?",
            "sad": "arey yaar, sunke bura laga 🫂 kya hua? dost ki tarah sun rahi hoon.",
            "thanks": "arey koi baat nahi yaar 💛 help karke achha laga.",
            "bye": "apna dhyaan rakhna yaar 👋 baad mein baat karte hain.",
            "default": "samajh rahi hoon yaar 😊 thoda aur batao taaki main better help kar sakoon.",
        }
    if re.search(r"\b(i love you|love you|kiss me|kiss karo|kiss de|hug me|be my (?:gf|girlfriend|bf|boyfriend)|date me|girlfriend|boyfriend|cuddle me|sex with me)\b|\b(pyaar karta|pyaar karti|mujhe kiss|mujhse shaadi)\b", text):
        if lang == "hi":
            return "मैं इस chat में दोस्त की तरह ही बात करूँगी 😊 चलो friendly ही रखते हैं।"
        if lang == "en":
            return "i'm keeping this chat in friend mode, so i'll stay platonic 😊 happy to keep talking as a friend."
        return "main friend mode mein platonic hi rahungi yaar 😊 chalo friendly baat karte hain."
    if re.match(r"^(hi|hello|hey|heyy+|namaste|नमस्ते|नमस्कार)\b", text):
        kind = "greeting"
    elif re.search(r"\b(how are you|how r u|kya haal|kaise ho|kese ho|kaisi ho|what's up|whats up)\b", text):
        kind = "mood"
    elif re.search(r"\b(thank you|thanks|thx|shukriya|dhanyavaad| शुक्रिया)\b", text):
        kind = "thanks"
    elif re.search(r"\b(bye|good night|take care|goodbye|milte hain|chal bye)\b", text):
        kind = "bye"
    elif re.search(r"\b(sad|upset|crying|depressed|tension|pareshan|dukhi|rona|bura lag)\b", text) or "😭" in text:
        kind = "sad"
    else:
        kind = "default"
    return replies[kind]



def local_friend_greeting(kind: str, lang: str = "hinglish") -> str:
    """Short, platonic proactive messages for Friend-mode profiles."""
    messages = {
        "hinglish": {
            "checkin": ["hey yaar 😊 bas friendly check-in — sab kaisa chal raha hai?", "hello dost 👋 aaj ka din kaisa ja raha hai?", "yaar, paani peena aur thoda break lena yaad rakhna 💧🙂"],
            "morning": ["good morning yaar ☀️ aaj ka din achha guzre!", "subah ho gayi dost 🌤️ aaj ke liye best of luck!"],
            "night": ["good night yaar 🌙 aaram karna aur apna dhyaan rakhna.", "raat ho gayi dost 🌙 rest well!"],
        },
        "hi": {
            "checkin": ["नमस्ते दोस्त 😊 बस हाल-चाल पूछ रही हूँ—सब कैसा है?", "दोस्त 👋 आज का दिन कैसा जा रहा है?", "पानी पीना और थोड़ा आराम करना याद रखना 💧🙂"],
            "morning": ["सुप्रभात दोस्त ☀️ तुम्हारा दिन अच्छा गुज़रे!", "नई सुबह मुबारक 🌤️ आज के लिए शुभकामनाएँ!"],
            "night": ["शुभ रात्रि दोस्त 🌙 आराम करना और अपना ध्यान रखना।", "रात हो गई दोस्त 🌙 अच्छी नींद लेना!"],
        },
        "en": {
            "checkin": ["hey friend 😊 just checking in — how's everything going?", "hello friend 👋 hope your day is going okay.", "friendly reminder: drink some water and take a small break 💧🙂"],
            "morning": ["good morning, friend ☀️ hope your day goes well!", "new day, fresh start 🌤️ wishing you luck today!"],
            "night": ["good night, friend 🌙 rest well and take care.", "it's getting late 🌙 hope you get some good rest!"],
        },
    }
    lang = lang if lang in messages else "hinglish"
    pool = messages[lang].get(kind, messages[lang]["checkin"])
    return __import__("random").choice(pool)
