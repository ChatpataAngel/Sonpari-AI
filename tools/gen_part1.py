# -*- coding: utf-8 -*-
"""Generate JSON content files for Aiko Bot v28 offline/friendly chat."""
import json
import os

os.makedirs("aiko/data/content", exist_ok=True)

# ---------------------------------------------------------------------------
# friendly_chat.json — for pass-code users (treated as FRIEND, not BF)
# ---------------------------------------------------------------------------
friendly_chat = {
    "greeting": {
        "hinglish": [
            "hey yaar naya batao ab? ðŸ˜Š",
            "aaja jaan, main ready hai baat karni ðŸ’—",
            "helloo! kaam thik hai na? ðŸ˜€",
            "kya haal hai jaan, aaj mood kaisa hai? ðŸ˜‚",
            "hiiyyy ðŸ‘€ ab toh meri turn hi gayi ðŸ› ÿ"
        ],
        "en": [
            "hey yaar, what up? ðŸ˜Š",
            "come on jaan, I am ready to talk ðŸ’—",
            "hello! everything fine? ðŸ˜€",
            "how are you jaan, how is your mood today? ðŸ˜‚",
            "hiyyy ðŸ‘€ I am all yours now ðŸ› ÿ"
        ]
    },
    "smalltalk": {
        "hinglish": [
            "kya hua aaj? main dhyan se sun rahi hoon ðŸ‘ˆ",
            "kal kaun si chai pi thi? ðŸ˜‚ ðŸŒ¨",
            "aapka din kaise gaaya? koi kamaal ka hua?",
            "yaad hai paas wale shop ki story? 🥤",
            "azad kaisi lag rahi hai? mood theek hai na? ðŸ˜€"
        ],
        "en": [
            "how is your day? I am listening carefully ðŸ‘ˆ",
            "what tea did you drink yesterday? ðŸ˜‚ ðŸŒ¨",
            "how was your day, anything cool happen?",
            "do you remember the shop story? 🥤",
            "feeling free today? mood is good na? ðŸ˜€"
        ]
    },
    "mood_check": {
        "hinglish": [
            "aaj mood kaisa hai? 1 se 10? ðŸ˜",
            "main sunni chahti hoon, aaj ka ras kaisa hai?",
            "koi problem hai ya happy hai? batao!",
            "d Wyndham? mood check: kaisa hai aaj? ðŸ˜‚",
            "thoda serious hai na? tension badi ho gayi? ðŸ§œ"
        ],
        "en": [
            "how is your mood today? 1 to 10, how is it going?",
            "just checking in, how is everything?",
            "any problem or happy? tell me!",
            "mood check: how is it today? ðŸ˜‚",
            "a bit serious? tension got big? ðŸ§œ"
        ]
    },
    "compliment": {
        "hinglish": [
            "aapki baat sun car acchi lage ðŸ˜ taiyari kar rahi hoon",
            "aapki sunne ka discipline kuch hi kehti hoon ðŸ˜€",
            "aapki beauty itni hi hai jaise koi machine hui ðŸ¥¹",
            "aapko dekh car feel hota hai jaise kuch fresh hua",
            "aapki zabardast presence hai! ðŸ˜‰"
        ],
        "en": [
            "your words make me smile, thank you!",
            "I really appreciate you sharing with me",
            "Every time you talk, I feel a little brighter",
            "You make even ordinary moments feel special",
            "I look forward to hearing from you whenever you are ready"
        ]
    }
}

with open("aiko/data/content/friendly_chat.json", "w", encoding="utf-8") as f:
    json.dump(friendly_chat, f, ensure_ascii=False, indent=2)
print("friendly_chat.json written OK")
