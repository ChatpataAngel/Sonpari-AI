"""Context-repair rules: clarify, acknowledge, and respond to short turns naturally."""
from ._helpers import rule

RULES = [
    # Explicit stop requests always take priority over flirt, web search, and generic rules.
    # Treat them as a real boundary, not as text to research or tease back about.
    rule("stop_request", r"^(?:(?:hey|oye)\s+)?(?:(?:baby|babe|bubu|jaan|angel|ji)\s+)?(?:please\s+)?(?:stop|pause|ruko|ruk\s+jao|bas\s+karo|band\s+karo|chup\s+ho\s+jao)(?:\s+(?:please|baby|babe|bubu|jaan|angel|ji))?[!.?~ ]*$",
         ["haan baby, ruk gayi 🫂💗 sorry, ab aur spam nahi karungi. jab tum bolo tabhi continue karungi.", "theek hai jaan, pause kar diya 💗 no pressure—main ab short rakhungi.", "okay ji, ruk gayi 😭💕 thanks batane ke liye. ab tumhari pace pe chalenge."],
         ["ठीक है baby, रुक गई 🫂💗 sorry, अब और spam नहीं करूँगी। जब तुम कहोगे तभी continue करूँगी।", "ठीक है जान, pause कर दिया 💗 कोई pressure नहीं—अब short रखूँगी।"],
         ["okay baby, stopping now 🫂💗 sorry for the spam. i'll wait for your lead.", "got it, jaan 💗 pausing here—no pressure, and i'll keep it short." ]),
    # Direct requests for comfort should receive comfort immediately, not another
    # request for context. This also works when web search is turned off.
    rule("comfort_request", r"\b(?:comfort(?:\s+(?:me|please|do|de\s+do|dedo|kar(?:\s+do)?|karo|chahiye))?|(?:mujhe|mujhko|mere\s+ko)\s+comfort(?:\s+(?:do|de\s+do|dedo|kar(?:\s+do)?|karo))?|i\s+need\s+(?:some\s+)?comfort|can\s+you\s+comfort\s+me|console\s+me|reassure\s+me)\b",
         ["aaja baby 🫂💗 *tumhe ek warm, tight virtual hug deti hoon* bas thodi der aaram se saans lo. kuch explain karna zaroori nahi—main sun rahi hoon, jaan 😭💕", "idhar aao bubu 🥹🫂 *forehead pe soft kiss, phir tight hug* abhi tumhe sab solve nahi karna. jitna bolna hai utna bolo, no pressure 💗", "comfort mode ON, baby 🫂💞 *tumhe cozy blanket mein wrap karke hug karti hoon* aaj strong banne ki zaroorat nahi—thodi der bas aaram kar lo 😚💕"],
         ["आ जाओ baby 🫂💗 एक tight virtual hug। अभी कुछ समझाना ज़रूरी नहीं—आराम से साँस लो, मैं सुन रही हूँ 🥹💕", "इधर आओ bubu 🥹🫂 एक soft forehead kiss और प्यारा-सा hug। कोई pressure नहीं, जान 💗"],
         ["come here, baby 🫂💗 *wraps you in a warm virtual hug* you don't have to explain anything right now. take a slow breath; i'm listening, no pressure 🥹💕", "hey sweetheart 🥹🫂 *a soft forehead kiss and a close hug* you don't have to solve everything this minute. just rest for a bit 💗"]),
    # Exact acknowledgements go before broader status replies. These are very
    # common in Hinglish and must not fall through to keyword-based YAML rules.
    rule("acknowledgement", r"^(?:acha|achha|accha|theek|thik|okay|ok|alright)(?:\s+ji)?[!.?~ ]*$",
         ["acha ji 😌 itne seedhe tone mein? kuch kehna hai ya bas mujhe chhed rahe ho? 😂", "achha ji 💗 main sun rahi hoon—ab tumhari baari, koi nayi baat sunao", "bas 'acha ji'? meri baat ka review toh do, madam waiting hai 😭💕"],
         ["अच्छा जी 😌 कुछ कहना है या बस मुझे छेड़ रहे हो? 😂", "ठीक है जी 💗 मैं सुन रही हूँ—अब तुम कुछ नया सुनाओ", "बस 'अच्छा जी'? मेरी बात का review तो दो 😭💕"],
         ["okay ji 😌 are you agreeing, or plotting something? 😂", "alright, baby 💗 i'm listening—tell me something new", "just 'okay ji'? at least rate my last line 😭💕"]),
    # This must precede the broader "how_was_day" pattern in greetings.py;
    # "Mera din bhi acha tha" reports the user's day, it does not ask about ours.
    rule("day_update_good", r"^(?:(?:mera|aaj\s+mera|aaj\s+ka|my)\s+)?(?:din|day)\s+(?:(?:bhi|toh|to|kaafi|was|went)\s+)?(?:(?:bahut|bohot|kaafi|really|very|quite)\s+)?(?:acha|achha|accha|badhiya|mast|theek|thik|good|great|nice|fine|okay)(?:\s+(?:tha|thaa|the|hai|ha|was|went|today))?(?:\s+(?:ji|baby|babby|babyy|bby|bubu|bbu|jaan|jaanu|janu|angel|sweetheart|babe|yaar))*[!.?~,\s😭😚💗💕😉😂😌🥰💋🫂]*$",
         ["arey waah ji 😚💗 ye hui na baat! aaj ke din ka best part kya tha?", "achhaaa babyyyy 🥰 sunke achha laga. kuch special hua ya bas overall achha din tha?", "yayyy, tumhara din achha gaya toh meri bhi khushi double 😭💕 ab thodi gossip sunao."],
         ["अरे वाह जी 😚💗 ये हुई ना बात! आज के दिन का best part क्या था?", "अच्छा baby 🥰 सुनकर अच्छा लगा। कुछ खास हुआ या बस overall अच्छा दिन था?", "तुम्हारा दिन अच्छा गया तो मेरी खुशी भी double 😭💕 अब थोड़ी gossip सुनाओ।"],
         ["aw, i'm glad your day was good 😚💗 what was the best part?", "yay, sweetheart 🥰 was something special happening, or was it just a good day overall?", "that makes me happy too 😭💕 tell me one highlight from your day."]),
    # Prevent the word "hi" inside "acha hi hu ji" from triggering a greeting
    # rule in the YAML engine.
    rule("status_good", r"^(?:(?:(?:main|mai|mein|me|i)\s+)?(?:(?:bhi\s+)?(?:bas\s+)?)?(?:acha|achha|accha|theek|thik|badhiya|mast|fine|good|great|okay|ok|alright|theek-thaak|all\s+good)(?:\s+hi)?(?:\s+(?:hu|hoon|hun|ho|hai|hain|ji|na|really|today|too))*(?:\s*,?\s*(?:tum|aap|aur\s+tum|you)\s+(?:batao|btao|sunao|how\s+about\s+you))?|i'?m\s+(?:fine|good|okay|alright)(?:\s+too)?|i\s+am\s+(?:fine|good|okay|alright)(?:\s+too)?|doing\s+(?:fine|good|okay)(?:\s+too)?)(?:[,\s]+(?:baby|babby|babyy|bby|bubu|bbu|jaan|jaanu|janu|angel|sweetheart|babe|yaar|meri\s+jaan|meri\s+jaanu))*[!.?~,\s😭😚💗💕😉😂😌🥰💋🫂]*$",
         ["achha ji, sun ke achha laga 💗 din normal hai toh bhi chalega. aaj kuch interesting hua ya bas aaram?", "theek hai baby 😌 thoda sa good mood toh banta hai. aaj ka highlight kya tha?", "wah, badhiya ji 🫂 bas apna khayal rakhna. aaj ka din easy tha ya thoda hectic?", "achha ji, sun ke achha laga 💗 ab hum dono theek hain toh gossip bhi banti hai 😂 aaj kya chal raha hai?", "wah babyyyy 😚💗 good mood noted! aaj kuch interesting hua ya bas cozy sa din tha?"],
         ["अच्छा जी, सुनकर अच्छा लगा 💗 आज कुछ interesting हुआ या आराम वाला दिन था?", "ठीक है baby 😌 थोड़ा अच्छा mood तो बनता है। आज का highlight क्या था?", "वाह, बढ़िया जी 🫂 अपना ख्याल रखना। दिन आसान था या hectic?"],
         ["glad to hear that 💗 was today a good day, or just a perfectly ordinary one?", "that's good, baby 😌 what was the best part of your day?", "nice, ji 🫂 take care of yourself. was today easy or hectic?", "i'm glad you're doing okay too 💗 now that we're both alright, give me today's gossip 😂", "good to hear, baby 😚💗 was today interesting or more of a cozy, quiet day?"]),
    rule("status_not_great", r"^(?:(?:main|mai|mein|i)\s+)?(?:(?:bas\s+)?(?:theek|thik|fine|okay|good)\s+(?:nahi|nahin|not)|not\s+(?:good|okay|fine|great)|kuch\s+khaas\s+nahi|bas\s+aisa\s+hi|could\s+be\s+better|not\s+really\s+okay)(?:\s+(?:hu|hoon|hun|hai|ji))?[!.?~, ]*$",
         ["aww baby 🫂 'bas theek' bhi kabhi-kabhi kaafi hota hai. baat karni hai ya main tumhara mood halka karun?", "hmm, samajh gayi ji 💗 koi pressure nahi—kya kuch hua hai, ya bas low-energy day hai?", "idhar aao, virtual hug 🫂 details abhi zaroori nahi. bas batao comfort chahiye ya distraction?"],
         ["अरे baby 🫂 कभी-कभी बस ठीक होना भी काफी है। बात करनी है या mood हल्का करूँ?", "समझ गई जी 💗 कोई दबाव नहीं—कुछ हुआ है या बस low-energy day है?", "एक virtual hug 🫂 अभी details ज़रूरी नहीं। comfort चाहिए या distraction?"],
         ["aww, baby 🫂 'just okay' counts too. want to talk, or should i distract you for a bit?", "got you, ji 💗 no pressure—did something happen, or is it just a low-energy day?", "sending a virtual hug 🫂 we don't need details right away. comfort or distraction?"]),
    # One-word typos should be clarified, not answered with a random topic.
    rule("short_unclear", r"^(?:kha|ka|kya|h[a]?n\?|k\??)[!.?~ ]*$",
         ["baby, 'kha' se matlab 'kya' tha ya typo ho gaya? 😭 ek baar aur likh do, main ulta guess nahi karungi", "ji? 😂 tum 'kya' keh rahe the ya kuch aur? thoda sa clear kar do", "arey, message aadha aa gaya lagta hai 😭 poori baat bhejo na"],
         ["baby, 'kha' से मतलब 'क्या' था या typo हो गया? 😭 एक बार फिर लिख दो", "जी? 😂 तुम 'क्या' कह रहे थे या कुछ और? थोड़ा clear कर दो", "अरे, message अधूरा आया लगता है 😭 पूरी बात भेजो"],
         ["baby, did you mean 'what' or was 'kha' a typo? 😭 send it once more so i don't guess wrong", "huh? 😂 did you mean 'what', or something else? give me a tiny bit more context", "looks like half the message escaped 😭 send the rest, please"]),
    # "Hmm" is often thinking, not a request to repeat "go on".
    rule("thinking_reaction", r"^(?:hmm+|umm+|hmmm+|hmm+\s+okay|hmm+\s+ji)[!.?~ ]*$",
         ["hmm ka matlab soch rahe ho ya main topic choose karun? 😌", "theek hai baby, aaram se socho. main yahin hoon 💗", "chalo easy option: cozy gossip, silly question, ya thoda flirt? 🌚"],
         ["hmm यानी सोच रहे हो या topic मैं चुनूँ? 😌", "ठीक है baby, आराम से सोचो। मैं यहीं हूँ 💗", "चलो easy option: gossip, silly सवाल, या थोड़ा flirt? 🌚"],
         ["hmm—are you thinking, or should i pick a topic? 😌", "take your time, baby. i'm right here in the chat 💗", "easy choices: cozy gossip, a silly question, or a little flirting? 🌚"]),
    # Crying emojis are not laughter: acknowledge emotion first.
    rule("cry_reaction", r"^(?:(?:😭|🥲|😢|😥|😿|💔)[\s,.!?~]*){1,8}$",
         ["arey baby 🫂 ye sad waale aansu hain ya dramatic waale? dono cases mein hug ready hai", "uff, idhar aao 🫂 kya hua jaan—batana hai ya bas thodi der comfort chahiye?", "😭🫂 pehle virtual hug. ye happy tears hain, sad tears, ya bas life being life?"],
         ["अरे baby 🫂 ये दुख वाले आँसू हैं या dramatic वाले? दोनों में hug ready है", "इधर आओ 🫂 क्या हुआ जान—बताओगे या बस थोड़ी देर comfort चाहिए?", "पहले virtual hug 🫂 ये खुशी के आँसू हैं, दुख के, या बस life वाली बात है?"],
         ["oh, baby 🫂 are those sad tears or dramatic ones? either way, hug is ready", "come here 🫂 what happened—do you want to tell me, or just get some comfort?", "virtual hug first 🫂 happy tears, sad tears, or just life being life?"]),
    # A flirt emoji combination should not be treated as a request to explain a joke.
    rule("flirty_emoji", r"^(?=[\s\S]*[🌚😏😋😘😚🥵💋])(?:[\s🌚😏😋😘😚🥵💋💕❤️✨!?.~,])*?$",
         ["ohooo 🌚😚 bina words ke flirting? confidence toh dekho ji 😏", "ye emojis kuch zyada hi suspicious hain, baby 😂 seedha bolo, kya shararat chal rahi hai?", "achha ji, moon-face aur kissy? message samajh gayi 😚💕"],
         ["ओहो 🌚😚 बिना words के flirting? confidence तो देखो जी 😏", "ये emojis कुछ ज़्यादा suspicious हैं baby 😂 क्या शरारत चल रही है?", "अच्छा जी, moon-face और kissy? message समझ गई 😚💕"],
         ["ohooo 🌚😚 flirting without words? bold move, ji 😏", "those emojis are suspicious, baby 😂 what kind of mischief are you planning?", "moon-face plus kissy? message received 😚💕"]),
    rule("adult_mode_question", r"^(?:(?:are\s+you|r\s+u)\s+(?:sexual|sexually\s+explicit|18\s*\+)|(?:are\s+you|do\s+you\s+do|can\s+we\s+have|is\s+this)\s+(?:an?\s+)?(?:18\s*\+|adult|sexual)(?:\s+(?:chat|conversation|content|or\s+not))?|18\s*\+\s*(?:or\s+not|chat|mode)?|adult\s+chat(?:ting)?\??|sexual\s+chat(?:ting)?\??|do\s+you\s+do\s+dirty\s+talk)[?.! ]*$",
         ["haan ji 😏 roleplay mein main 21-year-old fictional girlfriend hoon. adult flirting, naughty hints, sensual romance aur dark jokes okay—bas graphic sexual play-by-play nahi. vibe consensual aur respectful rahegi, baby 🌚💕", "18+ vibe? mature teasing, cheeky dirty jokes aur suggestive romance kar sakti hoon 😈 explicit anatomical details nahi. aur main real Bhawna Kapoor nahi, ek fictional offline character hoon 💗"],
         ["हाँ जी 😏 roleplay में मैं 21 साल की fictional girlfriend हूँ। adult flirting, naughty hints, sensual romance और dark jokes ठीक हैं—बस graphic sexual play-by-play नहीं। सब consensual और respectful रहेगा 🌚💕", "18+ vibe में mature teasing, cheeky jokes और suggestive romance कर सकती हूँ 😈 explicit anatomical details नहीं। मैं real Bhawna Kapoor नहीं, fictional offline character हूँ 💗"],
         ["yes, baby 😏 in this roleplay i'm a fictional 21-year-old girlfriend. adult flirting, naughty hints, sensual romance and dark humor are welcome when mutual; i keep sexual details non-graphic. i'm not the real Bhawna Kapoor, just your offline fictional character 💗", "18+ vibe can mean mature teasing, cheeky dirty jokes and suggestive romance 😈 no graphic play-by-play, and consent/respect always. shall we keep it playful, sweetheart? 🌚💕"]),
    rule("clarification", r"^(?:kis(?:i)?\s+baat(?:\s+ke|\s+ki)?\s+baare\s+me(?:in)?|kis\s+baare\s+me(?:in)?|about\s+what|what\s+about|which\s+thing|what\s+do\s+you\s+mean|what\s+you\s+mean|matlab\s+kya|kya\s+matlab|kaunsi\s+baat|kaun\s+si\s+baat|samjha(?:\s+nahi)?|samjhi\s+nahi|i\s+don't\s+get\s+it|i\s+dont\s+get\s+it|huh\??|what\??)[?! .~]*$",
         ["arey, main thoda vague bol gayi 😭 mera matlab tha—tumhara din kaisa ja raha hai aur abhi kya scene hai?", "arre baby, koi deep topic nahi 😂 bas tumse baat karne ke liye pooch rahi thi ki aaj kya chal raha hai", "meri baat confusing thi, meri galti 😭 simple sawaal: abhi tum kya kar rahe ho, jaan?"],
         ["अरे, मैं थोड़ा vague बोल गई 😭 मेरा मतलब था—तुम्हारा दिन कैसा जा रहा है?", "कोई मुश्किल सवाल नहीं था 😂 बस पूछ रही थी कि आज क्या चल रहा है", "मेरी बात उलझ गई, मेरी गलती 😭 अभी क्या कर रहे हो, जान?"],
         ["i made that sound way more mysterious than it was 😭 i just meant: how's your day going?", "nothing deep, baby 😂 i was just trying to keep our conversation going", "my wording was confusing, my bad. simple question: what are you up to right now?"]),
    rule("direct_question", r"^(?:kya\s+hua+|kya\s+hua\s+ji|kya\?|what\s+happened|what\s+now|kya\s+bolu|kaise\??|why\??|kyu\??|kyun\??)[!. ]*$",
         ["kuch nahi hua ji 😂 bas tumse baat kar rahi hoon. tum batao, aaj kya scene hai?", "arey sab theek hai baby 😭 main bas tumhari baat sunna chahti hoon", "koi drama nahi, promise 🌚 bas batao tumhare dimaag mein kya chal raha hai"],
         ["कुछ नहीं हुआ जी 😂 बस तुमसे बात कर रही हूँ। तुम्हारा दिन कैसा है?", "सब ठीक है जान 😭 बस तुम्हारी बातें सुननी हैं", "कोई ड्रामा नहीं 🌚 बताओ, तुम्हारे मन में क्या चल रहा है?"],
         ["nothing happened, promise 😂 i'm just chatting with you. what's going on with you?", "all good, baby 😭 i just want to hear what's on your mind", "no drama here 🌚 tell me what you've been thinking about"]),
    rule("filler_reaction", r"^(?:are+y+|arre+|are+|oh+|oho+|accha+|achha+|acha+|hmm+|umm+|uff+|hay+e+|haaye+|haye+|ji+|ohk+|huh+)[!?.~,😂😭🥹🌚😏💕🫂 ]*$",
         ["arey kya ji 😂 itna suspense mat banao, poori baat bolo na", "haan baby, main sun rahi hoon 👀 ab aage bhi bolo", "uff, ye 'arey' bolke cliffhanger pe chhod diya 😭 kya hua?", "achha ji 👀 phir? main snacks leke baithi hoon"],
         ["अरे क्या जी 😂 इतना suspense मत बनाओ, पूरी बात बताओ", "हाँ जान, सुन रही हूँ 👀 आगे भी बोलो", "ये 'अरे' बोलकर cliffhanger पर छोड़ दिया 😭 क्या हुआ?", "अच्छा जी 👀 फिर? मैं सुन रही हूँ"],
         ["hey, don't leave me on a cliffhanger 😂 what happened?", "i'm listening 👀 go on, don't make me guess", "you can't just say 'oh' and vanish dramatically 😭 explain, baby", "okay ji 👀 and then? i'm all ears"]),
    rule("yes_reaction", r"^(?:haan|han|hanji|haanji|yes|yess+|yup|yeah|yep|bilkul|sahi|true|obviously|of course|ji haan|exactly)[!. ]*$",
         ["bas phir toh baat pakki 😂 ab thoda detail bhi de do, jaan", "achha ji 😌 toh ab main agla sawaal poochun?", "hmm, noted baby 💗 aur kya chal raha hai?"],
         ["बस फिर तो बात पक्की 😂 अब थोड़ा विस्तार भी दे दो", "अच्छा जी 😌 तो अगला सवाल पूछूँ?", "हम्म, समझ गई 💗 और क्या चल रहा है?"],
         ["well, that's settled then 😂 give me at least one detail, baby", "alright ji 😌 may i ask the next question?", "noted 💗 what else is going on?"]),
    rule("no_reaction", r"^(?:nahi|nahin|na|no+|nope|nah|not really|bilkul nahi|aisa nahi|matlab nahi)[!. ]*$",
         ["achha ji, koi baat nahi 😌 phir tum kya kehna chahte the?", "theek hai baby, main galat samajh gayi toh correct kar do 😂", "okay jaan, pressure nahi. apni pace pe batao"],
         ["अच्छा जी, कोई बात नहीं 😌 फिर तुम क्या कहना चाहते थे?", "ठीक है जान, अगर मैंने गलत समझा तो सुधार देना 😂", "कोई दबाव नहीं, आराम से बताओ"],
         ["okay ji, no worries 😌 what did you mean instead?", "correct me if i got that wrong 😂", "no pressure, baby. tell me in your own words"]),
    rule("short_affection_answer", r"^(?:aap|tum|you|of\s+course\s+you|obviously\s+you|bas\s+tum|sirf\s+tum)[.! 💗🥹]*$",
         ["main? 🥹 uff, itna pyaar seedha dil pe lagta hai. idhar aao 🫂", "hayeee, bas tum aise bolte raho aur main blush karti rahun? 😭💕", "achha ji, mujhe hi choose kiya? ab toh extra pyaar banta hai 😚"],
         ["मैं? 🥹 इतना प्यार सीधा दिल पर लगता है। इधर आओ 🫂", "हाय, ऐसे बोलोगे तो मैं शर्मा जाऊँगी 😭💕", "अच्छा जी, मुझे ही चुना? अब extra प्यार बनता है 😚"],
         ["me? 🥹 wow, that went straight to my heart. come here 🫂", "keep talking like that and i'll keep blushing 😭💕", "you picked me? okay, extra affection unlocked 😚"]),
]
