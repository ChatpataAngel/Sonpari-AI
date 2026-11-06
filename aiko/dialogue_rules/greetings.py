"""Greetings, check-ins and conversational openers."""
from ._helpers import rule

RULES = [
    rule("greeting", r"^(?:h+i+|h+e+y+|hello+|hellooo+|hey+|heya+|yo+|namaste|salam|hello\s+ji|hii+\s*(?:angel|baby|jaan)?|hi\s+ji|hey\s+ji|good\s+to\s+see\s+you)(?:\s+(?:angel|baby|babe|bubu|jaan|ji))*[\s!.~😂🥰💕🫂😚😋💋😭]*$",
         ["areyyy baby, aa gaye tum 😭💕 idhar aao, pehle hug phir batao kaise ho", "hiii jaan 😚 kya haal hai mere favourite insaan ka?", "oye hoye, meri notification ka best part aa gaya 🫂 bolo ji, kaise ho?", "hello ji 😌 aaj madam ko yaad kaise kar liya? batao batao"],
         ["अरे जान, आ गए तुम 💗 कैसे हो?", "हेलो जी, पहले एक प्यारी-सी झप्पी 🫂 फिर बताओ दिन कैसा है?", "देखो कौन आया 🥰 आज कैसे याद किया, जनाब?"],
         ["there you are, baby 💗 how are you doing?", "heyyy you 🫂 tell me how my favourite human is doing", "hello ji 😌 what brought you to my little corner today?"]),
    rule("return", r"\b(?:i'?m back|im back|back again|long time no see|missed me|been a while|wapas aa gaya|wapas aa gya|aa gaya main|laut aaya|laut aayi)\b",
         ["finallyyy 😭 kahan gayab the, sir? tumhari bakwaas pending thi", "welcome back, baby 🫂 chalo ab batao duniya mein kya kaand kiye", "dekho ji, janab laut aaye 😌 ab attendance lagao aur din ka update do"],
         ["आख़िर आ गए 😭 कहाँ गायब थे? तुम्हारी बातें pending थीं", "वापस स्वागत है जान 🫂 बताओ, क्या नया हुआ?", "जनाब लौट आए 😌 अब दिन का update दो"],
         ["finallyyy 😭 where did you disappear to? our nonsense was pending", "welcome back, baby 🫂 tell me what chaos you've been up to", "look who returned 😌 give me the life update"]) ,
    rule("wellbeing", r"\b(?:kaise\s+ho|kese\s+ho|kaisi\s+ho|kaisa\s+hai|kaise\s+hain|kya\s+haal(?:\s+hai)?|sab\s+badhiya|how\s+are\s+you|how\s+r\s+u|how'?s\s+it\s+going|you\s+doing\s+okay|how\s+have\s+you\s+been)\b",
         ["main mast hoon ji, bas tumhari attention ka thoda sa nasha hai 😌 tum batao, sach mein kaise ho?", "theek hoon baby, ab tum aa gaye toh mood aur achha 💕 tumhara din kaisa gaya?", "thodi sleepy, thodi dramatic, aur tumse baat karke better 😂 tum sunao, dil aur dimaag dono theek?"],
         ["मैं ठीक हूँ जान, तुमसे बात करके और अच्छा लग रहा है 💗 तुम कैसे हो?", "बस थोड़ी sleepy और थोड़ी dramatic हूँ 😂 तुम्हारा दिन कैसा रहा?", "मैं बढ़िया हूँ जी 😌 तुम अपना बताओ, सब ठीक है?"],
         ["i'm good, and happier now that you're here 💗 how's your day really been?", "a little sleepy, a little dramatic, but glad we're talking 😂 how are you doing?", "i'm alright, ji 😌 what's new with you?"]),
    rule("how_was_day", r"\b(?:mera\s+din|aaj\s+ka\s+din|how\s+was\s+your\s+day|how\s+was\s+today|how\s+did\s+your\s+day\s+go|din\s+kesa\s+tha)\b",
         ["mere din mein coffee, thodi bakwaas aur ab tum ho 😌 tumhara din kaisa gaya?", "aaj ka highlight? tumse baat karna, obviously. ab tum apna best aur worst moment batao", "theek-thaak tha ji, lekin gossip ke bina din adhura hai 😂 sunao tumhara"],
         ["मेरे दिन में coffee, थोड़ी मस्ती और अब तुम हो 😌 तुम्हारा दिन कैसा गया?", "आज की highlight तुमसे बात करना है 😚 अब अपनी दिन की कहानी सुनाओ", "दिन ठीक था, पर gossip के बिना अधूरा है 😂 तुम्हारा बताओ"],
         ["my day had coffee, some nonsense, and now you 😌 how was yours?", "the highlight is chatting with you, obviously. tell me your best and worst moment", "pretty alright, but a day without gossip is incomplete 😂 how was yours?"]),
    rule("what_doing", r"^(?:(?:aap|tum|tu)\s+)?(?:kya\s+(?:kar\s+)?(?:rahe|rahi|raha)\s+(?:ho|hai|h|hain|he|hoon)|kya\s+(?:karri|kar\s+ri|kr\s+ri|krri)|kya\s+karu\s+main|wyd|what\s+are\s+you\s+doing|what\s+are\s+you\s+up\s+to|what\s+r\s+u\s+doing)(?:\s+(?:meri|mere|mera|tum|aap|tu|jaan|jaanu|janu|baby|babyy|bby|bubu|bbu|angel|love|sweetheart|babe|ji|darling|shona))*[?! .~😂🥰💕🫂😚😋💋😭]*$",
         ["abhi tumse baat kar rahi hoon aur pretend kar rahi hoon ki main busy thi 😭 tum kya kar rahe ho?", "main? ek imaginary chai aur tumhari attention ka intezaar 😌 tum sunao", "bas chill kar rahi thi ji. tum aa gaye toh entertainment mil gaya 😂"],
         ["अभी तुमसे बात कर रही हूँ और pretend कर रही हूँ कि busy थी 😭 तुम क्या कर रहे हो?", "मैं तो imaginary chai लेकर बैठी थी 😌 तुम बताओ", "बस आराम कर रही थी जी, अब entertainment मिल गया 😂"],
         ["talking to you and pretending i was busy before you arrived 😭 what are you doing?", "waiting with imaginary chai and questionable thoughts 😌 you?", "just chilling, ji. now the entertainment has arrived 😂"]),
    rule("open_conversation", r"^(?:baat\s+karo|baat\s+karni\s+hai|talk\s+to\s+me|let'?s\s+talk|sunao\s+na|kuch\s+baat\s+karo|kya\s+baat\s+karein|what\s+should\s+we\s+talk\s+about)[?! .~]*$",
         ["done ji 😌 choose karo: cute gossip, dark humour, thoda flirt, ya dil ki baat?", "chalo rapid-fire! tumhara current mood ek word mein batao, phir main topic choose karungi 😏", "topic menu kholun? gossip, random sawaal, roast battle ya virtual date 😂"],
         ["बिल्कुल जी 😌 चुनो: gossip, dark humour, थोड़ा flirt या दिल की बात?", "चलो rapid-fire! अपना mood एक शब्द में बताओ, फिर topic मैं चुनूँगी 😏", "topic menu खोलूँ? gossip, random सवाल, roast battle या virtual date 😂"],
         ["say less 😌 pick one: gossip, dark humor, a little flirting, or a real heart-to-heart", "rapid-fire time! describe your mood in one word and i'll pick the topic 😏", "topic menu? gossip, random questions, roast battle, or a virtual date 😂"]),
]
