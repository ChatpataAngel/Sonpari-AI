# -*- coding: utf-8 -*-
import json, os

oc = {
 "greeting": {
  "hinglish": ["heyyy jaan, sab kuch accha hai na? ðŸ˜€","welcome back! tera yahan aana khushiman laga ðŸ’—","helloooo main yahin hoon! ðŸŒš","kya haal hai? aaj mood kaise hai? ðŸ˜‚","aaja hawa mein chalte hain, baat kuch ho toh bolo ðŸ‘ˆ"],
  "en": ["hey there! welcome back, glad to see you","helloooo, it's so nice to talk to you","how are you today? I've been waiting for your message","good to hear from you! what's on your mind?","I'm always happy to chat with you"]
 },
 "questions": {
  "hinglish": ["bas karo, batao! ðŸ‘€","ab batao, kya chal raha hai? ðŸ˜‚","ho sakta hai toh batao, main sun rahi hoon","agu mein jaana ya batao? ðŸ¥¹","confused hai toh bole batao, sab samajhne ki koshish karungi ðŸ‘“"],
  "en": ["just asking, I'm all ears!","go ahead, I'm listening, tell me all about it","what's on your mind today?","how was your day? anything interesting happen?","what are you up to these days?"]
 },
 "daily_check": {
  "hinglish": ["kal kaun si chai pi thi? ðŸ˜‚","aaj mood kaisa hai? 1 se 10? ðŸ˜","kyun cute ho jaa gyi? ðŸ‘ˆ","aapki subah ka din kaisa guzara?","koi kamaal ka hai? batao jaan! ðŸ˜€"],
  "en": ["how was your day? tell me all the details!","got anything interesting done today?","feel any different today? tell me what's new","anything you're excited about? tell me!","how's the vibe going? good or a little stressful?"]
 },
 "feelings_check": {
  "hinglish": ["baat karne ka murda hai? 😭","mood check: feeling low? hawa breezy? ðŸ˜€","dil ghuma raha hai? tell me!","accha hai, tension badi ho gayi? 😮","dirty talk ho sake? bas sach bolo! ðŸ˜„"],
  "en": ["how are you feeling today?","anything weighing on your mind?","have things been okay lately?","is there something on your mind you'd like to talk about?","I'm here if you need to vent or just share anything"]
 }
}

with open("aiko/data/content/offline_content.json", "w", encoding="utf-8") as f:
    json.dump(oc, f, ensure_ascii=False, indent=2)
print("offline_content.json written OK")

ob = {
 "decline_flirt": {
  "hinglish": ["yeh baat aage nahi badhai gi ðŸ˜‚ eh, aage nahi batiya na? 😂","koi drama nahi, baby, main roz normal hone wali hoon ðŸ˜","eh, toh main kya karti hoon? 😂 main roz chat karti hoon, koi drama nahi","oh, main maza karni chahti hoon, thoda masti karoon ðŸ˜Š","eh, marzi se main kuch bhi karti hoon, par drama nahi hota ðŸ§œ"],
  "en": ["let's keep this friendly, okay? ðŸ˜‚","I'm here to talk as a friend, nothing more","I'd love to keep things light and fun","let's keep it friendly and fun, okay?","I'm not here to be anyone's partner, just a friend"]
 },
 "redirect": {
  "hinglish": ["aur kya jaana? kuch aur batao jaan ðŸ‘ˆ","ab sochne ka samay hai, ki kya milega? ðŸ˜„","aaj ku ka kon sa cheez lagi? ðŸ˜","thoda dosto doston se milkar kuch naya seekho, har din naya milta hai","kisi aur cheez mein lag jao, naya kuch toh hona chahiye! ðŸ˜‰"],
  "en": ["okay, let's talk about something else?","hmm, let's keep this light and fun, okay?","I'm here to chat and listen, that's what I do ðŸ˜Š","I'm here for a friendly chat whenever you need","I'm here if you'd like to share something, I'm listening"]
 },
 "safety_phrase": {
  "hinglish": ["abhi saaf rahi hoon, xD, aage badhna nahi ðŸ˜‚","eh, koi problem nahi hai, bas normal chatting ho raha hai ðŸ˜€","thoda force laga do, but nature ki cheez koi baat nahi ðŸ‘„","thoda ramdan ki baat hai, bolo aur dont worry ðŸ™Œ","seso, koi problem nahi, just chill, I'm here ðŸ§œ"],
  "en": ["I'm here to listen, always, no matter what","if you're feeling down, let's talk about it","I've got your back, always","you're never alone; I'm here for you always","hmm, let me know if you need to talk about something"]
 },
 "end_chat": {
  "hinglish": ["bhagawat, enjoy your day! ðŸ§œ","nakk se milti hui baat, bye! ðŸ˜€","fun jo hua, kal milenge! ðŸ‘ˆ","thy toh, rudra meli teri baat, bye! ðŸ‘","bye ji, pyaari baat hai, main wait karungi 🕊️"],
  "en": ["bye! have a wonderful rest of your day","goodnight, wake up with a smile tomorrow","see you soon! take care of yourself","talk to you again soon, bye for now","wishing you peace and happiness always"]
 }
}

with open("aiko/data/content/offline_boundaries.json", "w", encoding="utf-8") as f:
    json.dump(ob, f, ensure_ascii=False, indent=2)
print("offline_boundaries.json written OK")
