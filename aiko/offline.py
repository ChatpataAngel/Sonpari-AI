"""Run Aiko in a terminal without Telegram.

Dialogue generation is deterministic/rule-based. Free English web search can
support factual research or girlfriend-reply inspiration. Recent context and
search learning are retained locally between terminal sessions.
"""
from __future__ import annotations
import random
import json
from pathlib import Path
import yaml
from dotenv import load_dotenv
from .engine import ResponseEngine
from .dialogue import DialogueManager
from .text_style import apply_texting_style
from .language import detect_language, SUPPORTED_LANGUAGES
from .local_memory import LocalMemory
from .local_brain import LocalBrain
from .conversation_learning import LocalConversationLearning
from .web_research import WebResearcher, WebSearchUnavailable
from .translator import UniversalTranslator, translation_command
from .groq_chat import GroqChat

ROOT = Path(__file__).resolve().parent.parent

def main() -> None:
    load_dotenv(ROOT / ".env")
    persona = yaml.safe_load((ROOT / "config" / "persona.yaml").read_text(encoding="utf-8"))
    engine = ResponseEngine(persona, [str(ROOT / "config" / "rules.yaml")], random.Random())
    brain = LocalBrain(ROOT / "data" / "local_brain.json")
    web_researcher = WebResearcher(ROOT / "data" / "web_preferences.json")
    translator = UniversalTranslator()
    groq_chat = GroqChat()
    conversation_learning = LocalConversationLearning(ROOT / "data" / "conversation_learning.json")
    dialogue = DialogueManager(brain=brain)
    user_id = 1
    memory = LocalMemory(ROOT / "data" / "offline_memory.json")
    preferences_path = ROOT / "data" / "offline_preferences.json"
    try:
        saved_preferences = json.loads(preferences_path.read_text(encoding="utf-8")) if preferences_path.exists() else {}
    except (OSError, json.JSONDecodeError):
        saved_preferences = {}
    saved_language = saved_preferences.get("language") if isinstance(saved_preferences, dict) else None
    auto_language_mode = saved_language == "auto"
    if saved_language in SUPPORTED_LANGUAGES:
        dialogue.preferred_language[user_id] = saved_language
    groq_status = "on" if groq_chat.enabled else "off (add GROQ_API_KEY to .env to enable)"
    print(f"{persona.get('name', 'Bhawna')}: terminal chat ready. Type /help or /quit. Web research mode: {web_researcher.get_mode(user_id)}. Groq AI fallback: {groq_status}\n")
    while True:
        try:
            message = input("You: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nBhawna: bye ji, take care 💗")
            break
        if not message:
            continue
        low = message.lower()
        if low in {"/quit", "/exit", "quit", "exit"}:
            print("Bhawna: bye ji, take care 💗")
            break
        if low == "/help":
            print("Commands: /help, /mood, /joke, /kiss, /memory, /forget, /brain, /brainforget, /context, /forgetchat, /web [auto|always|off|status|test], /search <whole question or reply prompt>, /translate <target> | <text>, /quit. Teach replies: teach: trigger => reply\n")
            continue
        if low == "/context":
            print(f"Bhawna: local learning 🧠 — {conversation_learning.summary(user_id)} Preferences: {conversation_learning.context_for(user_id).get('preferences', {})}\n")
            continue
        if low == "/forgetchat":
            conversation_learning.forget(user_id)
            print("Bhawna: theek hai ji, saved chat context, topic history aur search-learning clear kar di 🧹💗\n")
            continue
        if low == "/translate" or low.startswith("/translate "):
            raw = message[len("/translate"):].strip()
            response = translation_command(raw, translator)
            print(f"Bhawna: {response}\n")
            continue
        if low == "/web" or low.startswith("/web "):
            parts = low.split()
            if len(parts) == 1:
                print(f"Bhawna: web mode abhi '{web_researcher.get_mode(user_id)}' hai ji 🔎. Options: /web auto, /web always, /web off, /web status.\n")
            elif len(parts) == 2 and parts[1].lower() == "status":
                print(f"Bhawna: {web_researcher.provider_status()}\n")
            elif len(parts) == 2 and parts[1].lower() == "test":
                print(f"Bhawna: {web_researcher.test_primary_provider()}\n")
            elif len(parts) == 2 and web_researcher.set_mode(user_id, parts[1]):
                desc = {"auto": "factual questions + girlfriend reply ideas", "always": "relevant substantial messages (identity/language/stop controls stay local)", "off": "automatic web search band"}[parts[1]]
                print(f"Bhawna: done ji 💗 web mode '{parts[1]}' set kar diya ({desc}). Explicit /search phir bhi kaam karega.\n")
            else:
                print("Bhawna: use /web auto, /web always, /web off, /web status, ya /web test.\n")
            continue
        if low.startswith("/search ") or low.startswith("search: "):
            prior_context = conversation_learning.context_for(user_id)
            prompt = message.split(" ", 1)[1] if " " in message else message
            conversation_learning.observe(user_id, "user", prompt)
            prior_context["preferences"] = conversation_learning.context_for(user_id).get("preferences", {})
            try:
                response = web_researcher.answer(
                    prompt, dialogue.effective_language(user_id, "hinglish"),
                    prior_context, persona, conversation_learning, user_id,
                    "always",  # explicit /search should support personal-reply inspiration too
                )
                final_response = response or "is prompt ke liye useful results nahi mile ji 😕"
                if not web_researcher.is_research_question(prompt, prior_context):
                    final_response = apply_texting_style(final_response, prior_context.get("preferences", {}))
                    conversation_learning.observe(user_id, "assistant", final_response)
                print(f"Bhawna: {final_response}\n")
            except WebSearchUnavailable as exc:
                failure = "abhi web search se reliable results nahi mil paaye ji 😕 main bina source ke facts invent nahi karungi. Thodi der baad ya specific keywords se try kar lena."
                conversation_learning.observe(user_id, "assistant", failure)
                print(f"Bhawna: {failure}\n")
            continue
        if low == "/memory":
            facts=memory.all()
            if facts:
                print("Bhawna: meri local memory 📒\n" + "\n".join(f"- {k.replace('_',' ')}: {v}" for k,v in facts.items()) + "\n")
            else:
                print("Bhawna: abhi memory khaali hai ji 💗\n")
            continue
        if low == "/forget":
            memory.forget()
            print("Bhawna: theek hai ji, local saved facts delete kar diye 🫂\n")
            continue
        if low == "/brain":
            print(f"Bhawna: local brain mein {brain.count(user_id)} learned reply rules saved hain 🧠. Sikhao: teach: trigger => reply\n")
            continue
        if low == "/brainforget":
            brain.forget(user_id)
            print("Bhawna: custom learned replies delete kar diye ji 🧠🧹\n")
            continue
        # Persist all conversational turns locally. The pre-turn snapshot captures
        # the prior exchanges before the current prompt is appended.
        prior_context = conversation_learning.context_for(user_id)
        conversation_learning.observe(user_id, "user", message)
        prior_context["preferences"] = conversation_learning.context_for(user_id).get("preferences", {})
        # Hinglish is the default voice even when the user's prompt is English.
        # Automatic detection is available only when the user explicitly enables it.
        if auto_language_mode:
            lang, confident = detect_language(message)
            if not confident:
                lang = "hinglish"
            lang = dialogue.effective_language(user_id, lang)
        else:
            lang = dialogue.effective_language(user_id, "hinglish")
        # Auto mode searches factual questions and common girlfriend-chat prompts for reply inspiration.
        search_warning = None
        web_mode = web_researcher.get_mode(user_id)
        if web_researcher.should_search(message, web_mode, context=prior_context):
            try:
                web_response = web_researcher.answer(
                    message, lang, prior_context, persona, conversation_learning, user_id, web_mode,
                )
            except WebSearchUnavailable as exc:
                web_response = None
                search_warning = "🔎 Web search abhi available nahi hai; local replies se continue kar rahi hoon 💗"
            if web_response:
                memory.remember(message)
                if not web_researcher.is_research_question(message, prior_context):
                    web_response = apply_texting_style(web_response, prior_context.get("preferences", {}))
                    conversation_learning.observe(user_id, "assistant", web_response)
                print(f"Bhawna: {web_response}\n")
                continue
        memory.remember(message)
        if low == "/mood":
            response = "abhi playful mood mein hoon 😌💕"
            conversation_learning.observe(user_id, "assistant", response)
            print(f"Bhawna: {response}\n")
            continue
        if low == "/joke":
            reply = dialogue.respond(user_id, "dark joke suna", lang) 
            response = reply.text if reply else 'meri life hi joke hai 💀'
            conversation_learning.observe(user_id, "assistant", response)
            print(f"Bhawna: {response}\n")
            continue
        if low == "/kiss":
            reply = dialogue.respond(user_id, "kiss dedo", lang)
            response = reply.text if reply else 'mwah 😘'
            conversation_learning.observe(user_id, "assistant", response)
            print(f"Bhawna: {response}\n")
            continue
        reply = dialogue.respond(user_id, message, lang)
        if reply:
            dialogue.note_response(user_id, reply.text, reply.intent)
            if reply.intent == "language_preference":
                auto_language_mode = False
                preferences_path.parent.mkdir(parents=True, exist_ok=True)
                preferences_path.write_text(
                    json.dumps({"language": dialogue.preferred_language.get(user_id)}, ensure_ascii=False, indent=2),
                    encoding="utf-8",
                )
            elif reply.intent == "language_auto":
                auto_language_mode = True
                preferences_path.parent.mkdir(parents=True, exist_ok=True)
                preferences_path.write_text(json.dumps({"language": "auto"}, indent=2), encoding="utf-8")
            styled_reply = apply_texting_style(reply.text, prior_context.get("preferences", {}))
            combined = f"{search_warning}\n\n{styled_reply}" if search_warning else styled_reply
            conversation_learning.observe(user_id, "assistant", combined)
            print(f"Bhawna: {combined}\n")
            continue
        state = {"affection": 60, "mood": "playful"}
        result = engine.match(message, state, user_id=user_id, lang=lang)
        if result:
            response = engine.render(result.response, {"name":"Angel", "stored_name":"Angel", "mood":"playful", "time_of_day":"night", "pet":"baby"}, lang=lang)
            response = apply_texting_style(response, prior_context.get("preferences", {}))
            dialogue.note_response(user_id, response, result.rule_id)
            if search_warning:
                response = f"{search_warning}\n\n{response}"
            conversation_learning.observe(user_id, "assistant", response)
            print(f"Bhawna: {response}\n")
        else:
            response = dialogue.fallback(user_id, message, lang)
            if groq_chat.enabled:
                ai_response = groq_chat.reply(
                    message, lang, persona, prior_context.get("recent_messages", [])
                )
                if ai_response:
                    response = ai_response
                    rule_id = "groq_fallback"
                else:
                    rule_id = "dialogue_fallback"
            else:
                rule_id = "dialogue_fallback"
            response = apply_texting_style(response, prior_context.get("preferences", {}))
            dialogue.note_response(user_id, response, rule_id)
            if search_warning:
                response = f"{search_warning}\n\n{response}"
            conversation_learning.observe(user_id, "assistant", response)
            print(f"Bhawna: {response}\n")

if __name__ == "__main__":
    main()
