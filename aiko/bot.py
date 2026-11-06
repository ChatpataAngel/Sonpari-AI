from __future__ import annotations
import asyncio, logging, time, random
from collections import defaultdict, deque
from datetime import datetime, timezone
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, ContextTypes, filters
from .config import load_settings, load_yaml, validate_persona
from .database import Database
from .engine import ResponseEngine
from .memory import Memory
from .humanizer import Humanizer
from .scheduler import ProactiveScheduler
from .mood import apply_effect, time_mood
from .utils import time_of_day
from .language import LanguageTracker, parse_language_request, SUPPORTED_LANGUAGES
from .dialogue import DialogueManager
from .text_style import apply_texting_style
from .local_brain import LocalBrain
from .conversation_learning import LocalConversationLearning
from .web_research import WebResearcher, WebSearchUnavailable
from .translator import UniversalTranslator, translation_command
from .multi_ai import MultiAIClient
from pathlib import Path
from . import i18n
from . import commands
from .access import has_bf_access
from .relationship import local_friend_reply

RATE_BUCKETS=defaultdict(deque)

# Intents that produce adult-themed replies (suggestive flirting, sensual romance,
# adult teasing, intimate atmosphere). These are gated behind /adult opt-in.
ADULT_CONTENT_INTENTS = {
    "dark_flirt", "gothic_romance", "consensual_power_play", "safer_sex_conversation",
    "adult_aftercare", "adult_roleplay_preferences", "playful_possessive_flirt",
    "adult_flirt_tone", "adult_intimacy_mood_check", "consensual_adult_teasing",
    "sexual_flirt", "romantic_roleplay_setup",
}
# Consent/boundary intents are never gated — users can always ask about limits.
ADULT_BOUNDARY_INTENTS = {
    "adult_consent_talk", "not_ready_for_intimacy", "intimate_photo_privacy",
    "kiss_consent", "intimacy_after_no", "safe_roleplay_stop",
}

def begin_user_turn(app, user_id: int) -> int:
    """Mark a new turn so slower, older web replies cannot arrive out of order."""
    generations = app.bot_data.setdefault("message_generations", {})
    generation = int(generations.get(user_id, 0)) + 1
    generations[user_id] = generation
    return generation

def is_current_user_turn(app, user_id: int, generation: int) -> bool:
    return app.bot_data.get("message_generations", {}).get(user_id) == generation

def allowed_user(update, context):
    """Friends may chat without a pass; BF access changes tone, not availability."""
    return bool(update and update.effective_user)


async def maybe_provider_failure_alert(app, bot, client):
    """Notify the configured owner after repeated full-chain AI failures, rate-limited by the client."""
    if not client or not hasattr(client, "should_alert_failure") or not client.should_alert_failure():
        return
    owner_id = app.bot_data["settings"].owner_id
    if not owner_id:
        return
    try:
        await bot.send_message(
            chat_id=owner_id,
            text=("⚠️ AIKO provider alert: the configured AI fallback chain has failed repeatedly. "
                  "Local replies are still available. Use /health and /ai_status to inspect provider availability. "
                  "No user message content is included in this alert.")
        )
    except Exception as exc:
        logging.getLogger(__name__).warning("Could not deliver provider alert (%s)", type(exc).__name__)


async def process_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not allowed_user(update, context):
        return
    msg = update.effective_message
    user = update.effective_user
    chat = update.effective_chat
    if not msg or not msg.text or not user:
        return
    now = time.monotonic()
    bucket = RATE_BUCKETS[user.id]
    while bucket and now - bucket[0] >= 60:
        bucket.popleft()
    settings = context.application.bot_data["settings"]
    if len(bucket) >= settings.max_messages_per_minute:
        return
    bucket.append(now)

    app = context.application
    db = app.bot_data["db"]
    persona = app.bot_data["persona"]
    engine = app.bot_data["engine"]
    memory = app.bot_data["memory"]
    turn_generation = begin_user_turn(app, user.id)
    await db.ensure_user(user.id, user.username, user.full_name, persona.get("timezone"))
    row = await db.get_user(user.id)
    conversation_learning = app.bot_data.get("conversation_learning")
    learning_enabled = bool(row["learning_enabled"]) if row and "learning_enabled" in row.keys() else True
    memory_enabled = bool(row["memory_enabled"]) if row and "memory_enabled" in row.keys() else True
    prior_context = conversation_learning.context_for(user.id) if conversation_learning and learning_enabled else {}
    if conversation_learning and learning_enabled:
        conversation_learning.observe(user.id, "user", msg.text)
        prior_context["preferences"] = conversation_learning.context_for(user.id).get("preferences", {})

    is_bf_user = has_bf_access(settings, user.id, row)
    timestamp = datetime.now(timezone.utc).isoformat()
    await db.execute(
        "UPDATE users SET message_count=message_count+1,last_seen=?,last_proactive=? WHERE user_id=?",
        (timestamp, timestamp, user.id),
    )

    tracker = app.bot_data["languages"]
    dialogue = app.bot_data["dialogue"]
    requested_language = parse_language_request(msg.text)
    tracker.seed(user.id, row["lang"] or settings.default_lang)
    if requested_language in SUPPORTED_LANGUAGES:
        dialogue.preferred_language[user.id] = requested_language
        tracker.set(user.id, requested_language)
        lang = requested_language
        await db.execute("UPDATE users SET lang=?, lang_preference=? WHERE user_id=?", (lang, lang, user.id))
    elif requested_language == "auto":
        dialogue.preferred_language.pop(user.id, None)
        await db.execute("UPDATE users SET lang_preference='auto' WHERE user_id=?", (user.id,))
        lang = tracker.observe(user.id, msg.text)
    elif row["lang_preference"] == "auto":
        lang = tracker.observe(user.id, msg.text)
    elif row["lang_preference"] in SUPPORTED_LANGUAGES:
        lang = row["lang_preference"]
        dialogue.preferred_language[user.id] = lang
        tracker.set(user.id, lang)
    else:
        lang = "hinglish"
        tracker.set(user.id, lang)
    lang = dialogue.effective_language(user.id, lang)
    if lang != row["lang"]:
        await db.execute("UPDATE users SET lang=? WHERE user_id=?", (lang, user.id))

    # Factual questions use a concise research digest; relationship and casual
    # prompts use conversation/persona-aware reply inspiration. Search runs in a
    # worker thread so a slow provider does not block Telegram's event loop.
    web_researcher=app.bot_data["web_researcher"]
    web_mode=web_researcher.get_mode(user.id)
    learning_for_search = conversation_learning if learning_enabled else None
    search_warning=None
    try:
        web_response=None
        should_auto_search = web_researcher.should_search(msg.text, web_mode, context=prior_context)
        if not is_bf_user:
            should_auto_search = should_auto_search and web_researcher.is_research_question(msg.text, context=prior_context)
        if should_auto_search:
            web_response=await asyncio.to_thread(
                web_researcher.answer, msg.text, lang, prior_context, persona,
                learning_for_search, user.id, web_mode,
            )
    except WebSearchUnavailable as exc:
        logging.getLogger(__name__).info("Web research unavailable: %s",exc)
        search_warning=f"🔎 Web search abhi connect nahi ho paayi ji; main local reply se continue kar rahi hoon 💗"
        web_response=None
    # If a newer message arrived during a slow web lookup, discard this stale turn.
    if not is_current_user_turn(app, user.id, turn_generation):
        return
    if web_response:
        # Mirror learned short forms/stretched letters for conversational reply
        # inspiration, but keep factual research digests readable and source-faithful.
        if not web_researcher.is_research_question(msg.text, prior_context):
            web_response = apply_texting_style(web_response, prior_context.get("preferences", {}))
        # Research summaries were being split into many delayed Telegram messages.
        # New user turns could arrive between chunks ("Baby stop") and results then
        # appeared out of order. Send one concise, bounded message instead.
        web_response = web_response[:3900]
        app.bot_data["humanizer"].vary(user.id,web_response)
        dialogue.note_response(user.id,web_response,"web_research")
        if conversation_learning and learning_enabled and not web_researcher.is_research_question(msg.text, prior_context):
            # Store conversational replies; factual result digests are already captured
            # in search-learning metadata and must not pollute the chat-intent history.
            conversation_learning.observe(user.id, "assistant", web_response)
        await db.log_message(user.id,"user","web_research",msg.text)
        await db.log_message(user.id,"bot","web_research",web_response)
        if not is_current_user_turn(app, user.id, turn_generation):
            return
        await context.bot.send_message(chat_id=chat.id,text=web_response,disable_web_page_preview=True)
        return

    # Remember useful facts for both tiers before selecting the role-specific reply path.
    if memory_enabled:
        await memory.remember_from_message(user.id, msg.text)
    # Friend-mode conversations are intentionally platonic. They can still use
    # factual web research above and the AI fallback, but never enter the BF romance rules.
    if not is_bf_user:
        multi_ai = app.bot_data.get("multi_ai")
        friend_response = None
        if multi_ai:
            try:
                friend_response = await asyncio.to_thread(
                    multi_ai.reply,
                    msg.text,
                    lang,
                    prior_context.get("recent_messages", []),
                    relationship_role="friend",
                )
            except Exception as exc:
                logging.getLogger(__name__).warning(
                    "Friend-mode AI fallback failed (%s); using local response", type(exc).__name__
                )
        if friend_response is None and multi_ai:
            await maybe_provider_failure_alert(app, context.bot, multi_ai)
        if not is_current_user_turn(app, user.id, turn_generation):
            return
        response = friend_response or local_friend_reply(msg.text, lang)
        response = apply_texting_style(response, prior_context.get("preferences", {}))
        app.bot_data["humanizer"].vary(user.id, response)
        dialogue.note_response(user.id, response, "friend_mode")
        if conversation_learning and learning_enabled:
            conversation_learning.observe(user.id, "assistant", response)
        await db.log_message(user.id, "user", "friend_mode", msg.text)
        await db.log_message(user.id, "bot", "friend_mode", response)
        if not is_current_user_turn(app, user.id, turn_generation):
            return
        await app.bot_data["humanizer"].send(
            context.bot, chat.id, response, persona["speech_style"]["max_message_length"], False
        )
        return

    row=await db.get_user(user.id)
    state={"affection":row["affection"],"mood":row["mood"]}
    local_hour=datetime.now().hour
    context_data={"name":row["display_name"] or user.first_name or "baby","stored_name":row["display_name"],
                  "mood":row["mood"],"time_of_day":time_of_day(local_hour)}

    # Specific, conversational Hinglish intents take priority over broad YAML
    # keywords. This prevents unrelated replies to kisses, jokes and short answers.
    direct=dialogue.respond(user.id,msg.text,lang=lang)
    result=None
    use_groq_fallback=False
    # Adult-mode gating: adult-content intents require the user to have opted in.
    # Stop/boundary requests always take priority and disable adult mode.
    if direct and direct.intent == "stop_request":
        await db.execute("UPDATE users SET adult_mode=0 WHERE user_id=?", (user.id,))
    if direct and direct.intent in ADULT_CONTENT_INTENTS:
        adult_enabled = False
        if not adult_enabled:
            template = (
                "main abhi adult-themed replies ke liye available nahi hoon 🫂💗 "
                "is bot mein romantic/adult mode available nahi hai "
                "(confirmation chahiye). abhi ke liye main normal, non-adult baatein karungi."
            )
            rule_id = "dialogue:adult_gated"
            multi = False
            direct = None  # skip effect application below
    if direct:
        template=direct.text; rule_id="dialogue:"+direct.intent; multi=False
        if direct.intent in {"kiss","love","affectionate_reaction","compliment"}:
            await apply_effect(db,user.id,2,"flirty" if direct.intent in {"kiss","compliment"} else "affectionate","dialogue:"+direct.intent)
    else:
        result=engine.match(msg.text,state,user.id,lang=lang)
        if result:
            template=result.response; rule_id=result.rule_id; effect=result.rule.get("mood_effect",{})
            await apply_effect(db,user.id,int(effect.get("affection",0) or 0),effect.get("mood"),"rule:"+rule_id)
            multi=bool(result.rule.get("multi_message",False))
        else:
            reflected=engine.apply_reflection(msg.text,context_data,lang=lang)
            if reflected:
                template=reflected
                rule_id="reflection"
            else:
                template=dialogue.fallback(user.id,msg.text,lang=lang)
                rule_id="dialogue_fallback"
                use_groq_fallback=True
            multi=False
    # Remember a conversational prompt so short answers such as "aap" can be
    # interpreted as a response to the preceding question.
    if any(x in template.lower() for x in ("what part matters most", "sabse zyada kya", "what matters most")):
        dialogue.note_intent(user.id,"what_matters")
    fact=await memory.recall_random(user.id)
    context_data["fact"]=fact or "something you told me"
    response=template if direct else engine.render(template,context_data,lang=lang)
    if use_groq_fallback:
        multi_ai=app.bot_data.get("multi_ai")
        if multi_ai:
            try:
                ai_response=await asyncio.to_thread(
                    multi_ai.reply, msg.text, lang,
                    prior_context.get("recent_messages", []),
                )
            except Exception as exc:
                # AI is optional; a failure must never break a Telegram reply.
                logging.getLogger(__name__).warning(
                    "Multi-AI fallback failed (%s); keeping local reply", type(exc).__name__
                )
                ai_response=None
            if ai_response is None:
                await maybe_provider_failure_alert(app, context.bot, multi_ai)
            if not is_current_user_turn(app, user.id, turn_generation):
                return
            if ai_response:
                response=ai_response
                rule_id="multi_ai_fallback"
    response=apply_texting_style(response, prior_context.get("preferences", {}))
    if search_warning:
        response=f"{search_warning}\n\n{response}"
    recent=app.bot_data["humanizer"].recent[user.id]
    if response in recent and result:
        alternatives=[x for x in result.responses if engine.render(x,context_data,lang=lang) not in recent]
        if alternatives: response=engine.render(random.choice(alternatives),context_data,lang=lang)
    if not is_current_user_turn(app, user.id, turn_generation):
        return
    app.bot_data["humanizer"].vary(user.id,response)
    dialogue.note_response(user.id,response,rule_id)
    if conversation_learning and learning_enabled:
        conversation_learning.observe(user.id, "assistant", response)
    await db.log_message(user.id,"user",rule_id,msg.text)
    await db.log_message(user.id,"bot",rule_id,response)
    if not is_current_user_turn(app, user.id, turn_generation):
        return
    await app.bot_data["humanizer"].send(context.bot,chat.id,response,persona["speech_style"]["max_message_length"],multi)
    # DEBUG: log bot's permitted scopes
    # logging.getLogger(__name__).debug("BOT SEND: chat_type=%s chat.id=%s", chat.type, getattr(chat,"id","-1"))
async def media_reply(update,context):
    if not allowed_user(update,context): return
    user=update.effective_user; msg=update.effective_message; app=context.application
    await app.bot_data["db"].ensure_user(user.id,user.username,user.full_name,app.bot_data["persona"].get("timezone"))
    kind="photo" if msg.photo else "sticker" if msg.sticker else "voice" if msg.voice else "animation" if msg.animation else "document"
    row=await app.bot_data["db"].get_user(user.id)
    tracker=app.bot_data["languages"]
    tracker.seed(user.id,row["lang"] if row else "en")
    lang=tracker.get(user.id)
    pool=i18n.media_pool(kind,lang)
    await app.bot_data["humanizer"].send(context.bot,update.effective_chat.id,random.choice(pool))
async def post_init(app):
    settings=app.bot_data["settings"]
    app.bot_data["db"]=await Database(settings.db_path,settings.log_message_content).open()
    # Preserve existing stored language/profile values during startup. Schema
    # migrations add defaults without rewriting saved user preferences.
    persona=load_yaml(settings.persona_file); validate_persona(persona)
    app.bot_data["persona"]=persona
    app.bot_data["engine"]=ResponseEngine(persona,settings.rules_files)
    app.bot_data["memory"]=Memory(app.bot_data["db"])
    app.bot_data["humanizer"]=Humanizer(persona["speech_style"]["max_message_length"])
    app.bot_data["languages"]=LanguageTracker()
    brain_path=Path(settings.db_path).parent / "local_brain.json"
    app.bot_data["local_brain"]=LocalBrain(brain_path)
    app.bot_data["dialogue"]=DialogueManager(brain=app.bot_data["local_brain"])
    app.bot_data["web_researcher"]=WebResearcher(Path(settings.db_path).parent / "web_preferences.json")
    app.bot_data["conversation_learning"]=LocalConversationLearning(Path(settings.db_path).parent / "conversation_learning.json")
    app.bot_data["translator"]=UniversalTranslator()
    app.bot_data["multi_ai"]=MultiAIClient(persona=persona)
    logging.getLogger(__name__).info(
        "Multi-AI fallback enabled providers: %s",
        [p.name for p in app.bot_data["multi_ai"]._enabled_providers],
    )
    scheduler=ProactiveScheduler(app.bot_data["db"],app.bot_data["engine"],persona,settings,app.bot_data["humanizer"])
    app.bot_data["scheduler"]=scheduler
    if app.job_queue:
        app.job_queue.run_repeating(scheduler.proactive_check,interval=60,first=30,name="proactive-check")
        app.job_queue.run_repeating(scheduler.greeting_check,interval=300,first=45,name="greetings")
        app.job_queue.run_repeating(scheduler.reminder_check,interval=30,first=10,name="reminders")
        app.job_queue.run_daily(scheduler.daily_tasks,time=__import__("datetime").time(hour=0,minute=10),name="daily-decay")
async def post_shutdown(app):
    db=app.bot_data.get("db")
    if db: await db.close()
def command_guard(handler):
    async def guarded_handler(update, context):
        if not allowed_user(update, context):
            return
        # Commands may be a user's very first interaction, so create the local
        # profile before handlers write facts, journals or reminders.
        user=update.effective_user
        if user and context.application.bot_data.get("db") and context.application.bot_data.get("persona"):
            await context.application.bot_data["db"].ensure_user(
                user.id, user.username, user.full_name,
                context.application.bot_data["persona"].get("timezone"))
        return await handler(update, context)
    return guarded_handler

async def rps_callback(update, context):
    query=update.callback_query
    if not query or not allowed_user(update,context): return
    await query.answer()
    import random
    user=query.data.split(":",1)[1]
    bot=random.choice(["rock","paper","scissors"])
    labels={"rock":"🪨 rock","paper":"📄 paper","scissors":"✂️ scissors"}
    outcome="draw 😌" if user==bot else "you win 😭💕" if (user,bot) in {("rock","scissors"),("paper","rock"),("scissors","paper")} else "i win 😈 rematch?"
    await query.edit_message_text(f"you: {labels[user]}\nme: {labels[bot]}\n{outcome}")

async def web_cmd(update:Update,context:ContextTypes.DEFAULT_TYPE):
    """Configure automatic web research for the current Telegram user."""
    user=update.effective_user
    # A mode change should also prevent any older in-flight web answer from arriving later.
    begin_user_turn(context.application, user.id)
    researcher=context.application.bot_data["web_researcher"]
    if context.args and context.args[0].lower()=="test":
        result=await asyncio.to_thread(researcher.test_primary_provider)
        await update.effective_message.reply_text(result)
        return
    if not context.args or context.args[0].lower()=="status":
        mode=researcher.get_mode(user.id)
        await update.effective_message.reply_text(
            f"Web research mode: {mode} 🔎\n"
            f"{researcher.provider_status()}\n"
            "/web status — show provider configuration (does not test live connectivity)\n/web test — test FreeSerp live using a fixed public query, not your chat\n"
            "/web auto — search factual questions + (in BF mode) companion-reply inspiration\n"
            "/web always — factual search for everyone; BF mode may use companion-reply inspiration, Friends stay platonic\n"
            "/web off — disable automatic search\n"
            "/search <question or message> — search once for facts or reply inspiration\n"
            "/context — view the local conversation-learning summary\n"
            "/forgetchat — clear the saved conversation context and search-learning\n\n"
            "Privacy: search sends the query text to external search providers. Don't search passwords, private chats, addresses, or other sensitive information."
        )
        return
    mode=context.args[0].lower()
    if not researcher.set_mode(user.id,mode):
        await update.effective_message.reply_text("Choose one: /web auto, /web always, or /web off.")
        return
    descriptions={"auto":"facts + (BF mode only) companion-reply inspiration","always":"factual search for everyone; BF mode may use companion-reply inspiration","off":"automatic web search disabled"}
    await update.effective_message.reply_text(f"Saved ji 💗 Web mode is now '{mode}' ({descriptions[mode]}). Use /search for a one-time search.")


async def search_cmd(update:Update,context:ContextTypes.DEFAULT_TYPE):
    """Search the complete text supplied after /search."""
    if not context.args:
        await update.effective_message.reply_text("Usage: /search <your complete question or prompt>\nExample: /search What changed in Python 3.14?")
        return
    app=context.application
    researcher=app.bot_data["web_researcher"]
    turn_generation = begin_user_turn(app, update.effective_user.id)
    prompt=" ".join(context.args)
    dialogue=app.bot_data["dialogue"]
    lang=dialogue.effective_language(update.effective_user.id,"hinglish")
    learning=app.bot_data.get("conversation_learning")
    user_row = await app.bot_data["db"].get_user(update.effective_user.id)
    learning_enabled = bool(user_row["learning_enabled"]) if user_row and "learning_enabled" in user_row.keys() else True
    if not learning_enabled: learning = None
    prior_context=learning.context_for(update.effective_user.id) if learning else {}
    if learning:
        learning.observe(update.effective_user.id,"user",prompt)
        prior_context["preferences"] = learning.context_for(update.effective_user.id).get("preferences", {})
    row = await app.bot_data["db"].get_user(update.effective_user.id)
    is_bf_user = has_bf_access(app.bot_data["settings"], update.effective_user.id, row)
    # Explicit /search still works for facts for everyone, but must not turn a
    # Friend's romantic prompt into couple-style inspiration from search snippets.
    if not is_bf_user and not researcher.is_research_question(prompt, prior_context):
        final_response = local_friend_reply(prompt, lang)
        if learning:
            learning.observe(update.effective_user.id, "assistant", final_response)
        await update.effective_message.reply_text(final_response)
        return
    try:
        response=await asyncio.to_thread(
            researcher.answer, prompt, lang, prior_context, app.bot_data.get("persona"),
            learning, update.effective_user.id, "always",  # explicit /search can be reply inspiration or factual research
        )
    except WebSearchUnavailable as exc:
        if is_current_user_turn(context.application, update.effective_user.id, turn_generation):
            await update.effective_message.reply_text("Free web search abhi unavailable hai ji 😕 local replies continue karenge; provider error details hide rakhe hain.")
        return
    if not is_current_user_turn(context.application, update.effective_user.id, turn_generation):
        return
    final_response=(response or "Useful results nahi mile ji; ek shorter ya more specific query try karte hain 🔎💗")[:3900]
    if learning and not researcher.is_research_question(prompt, prior_context):
        final_response = apply_texting_style(final_response, prior_context.get("preferences", {}))
        learning.observe(update.effective_user.id,"assistant",final_response)
    await update.effective_message.reply_text(final_response,disable_web_page_preview=True)



async def translate_cmd(update:Update,context:ContextTypes.DEFAULT_TYPE):
    """Translate text on explicit request; ordinary chat is never auto-sent."""
    begin_user_turn(context.application, update.effective_user.id)
    translator=context.application.bot_data.get("translator")
    if translator is None:
        translator=UniversalTranslator()
        context.application.bot_data["translator"]=translator
    raw=" ".join(context.args).strip()
    response=await asyncio.to_thread(translation_command, raw, translator)
    # Stay below Telegram's message ceiling and never split translation output.
    await update.effective_message.reply_text(response[:3900], disable_web_page_preview=True)


async def context_cmd(update:Update,context:ContextTypes.DEFAULT_TYPE):
    """Show what the local conversation learner has retained."""
    learning=context.application.bot_data.get("conversation_learning")
    if not learning:
        await update.effective_message.reply_text("Local chat-learning is not initialized yet.")
        return
    summary=learning.summary(update.effective_user.id)
    prefs=learning.context_for(update.effective_user.id).get("preferences", {})
    await update.effective_message.reply_text(f"Local brain 🧠\n{summary}\nLearned preferences: {prefs}\nUse /forgetchat to clear this user’s context and search-learning.")


async def forgetchat_cmd(update:Update,context:ContextTypes.DEFAULT_TYPE):
    """Clear local conversation history and web-search learning for this user."""
    learning=context.application.bot_data.get("conversation_learning")
    if learning:
        learning.forget(update.effective_user.id)
    await update.effective_message.reply_text("Theek hai ji 🧹💗 saved chat context, topic history, preferences, and search-learning cleared locally.")

def build_application(settings):
    app=Application.builder().token(settings.token).post_init(post_init).post_shutdown(post_shutdown).build()
    app.bot_data["settings"]=settings
    app.add_handler(CommandHandler("start",command_guard(commands.start)))
    app.add_handler(CommandHandler("help",command_guard(commands.help_cmd)))
    app.add_handler(CommandHandler("mood",command_guard(commands.mood_cmd)))
    app.add_handler(CommandHandler("affection",command_guard(commands.affection_cmd)))
    app.add_handler(CommandHandler("stats",command_guard(commands.stats_cmd)))
    app.add_handler(CommandHandler("role",command_guard(commands.role_cmd)))
    app.add_handler(CommandHandler("bfusers",command_guard(commands.bfusers_cmd)))
    app.add_handler(CommandHandler("checkin",command_guard(commands.checkin_cmd)))
    app.add_handler(CommandHandler("quiet",command_guard(commands.quiet_cmd)))
    app.add_handler(CommandHandler("loud",command_guard(commands.loud_cmd)))
    app.add_handler(CommandHandler("context",command_guard(context_cmd)))
    app.add_handler(CommandHandler("forgetchat",command_guard(forgetchat_cmd)))
    app.add_handler(CommandHandler("name",command_guard(commands.name_cmd)))
    app.add_handler(CommandHandler("reset",command_guard(commands.reset_cmd)))
    app.add_handler(CommandHandler("confirm_reset",command_guard(commands.confirm_reset)))
    app.add_handler(CommandHandler("forget",command_guard(commands.forget_cmd)))
    app.add_handler(CommandHandler("confirm_forget",command_guard(commands.confirm_forget)))
    app.add_handler(CommandHandler("debug",command_guard(commands.debug_cmd)))
    app.add_handler(CommandHandler("reload",command_guard(commands.reload_cmd)))
    app.add_handler(CommandHandler("broadcast",command_guard(commands.broadcast_cmd)))
    app.add_handler(CommandHandler("memory",command_guard(commands.memory_cmd)))
    app.add_handler(CommandHandler("forgetall",command_guard(commands.forgetall_cmd)))
    app.add_handler(CommandHandler("confirm_forgetall",command_guard(commands.confirm_forgetall)))
    app.add_handler(CommandHandler("joke",command_guard(commands.joke_cmd)))
    app.add_handler(CommandHandler("games",command_guard(commands.games_cmd)))
    app.add_handler(CommandHandler("riddle",command_guard(commands.riddle_cmd)))
    app.add_handler(CommandHandler("answer",command_guard(commands.answer_cmd)))
    app.add_handler(CommandHandler("rps",command_guard(commands.rps_cmd)))
    app.add_handler(CommandHandler("export",command_guard(commands.export_cmd)))
    app.add_handler(CommandHandler("personality",command_guard(commands.personality_cmd)))
    app.add_handler(CommandHandler("journal",command_guard(commands.journal_cmd)))
    app.add_handler(CommandHandler("confirm_journal_clear",command_guard(commands.confirm_journal_clear)))
    app.add_handler(CommandHandler("remind",command_guard(commands.remind_cmd)))
    app.add_handler(CommandHandler("owner",command_guard(commands.owner_cmd)))
    app.add_handler(CommandHandler("settings",command_guard(commands.settings_cmd)))
    app.add_handler(CommandHandler("ai_status",command_guard(commands.ai_status_cmd)))
    app.add_handler(CommandHandler("health",command_guard(commands.health_cmd)))
    app.add_handler(CommandHandler("backup",command_guard(commands.backup_cmd)))
    app.add_handler(CommandHandler("revoke",command_guard(commands.revoke_cmd)))
    app.add_handler(CommandHandler("prefs",command_guard(commands.prefs_cmd)))
    app.add_handler(CommandHandler("privacy",command_guard(commands.privacy_cmd)))
    app.add_handler(CommandHandler("daily",command_guard(commands.daily_cmd)))
    app.add_handler(CommandHandler("complete",command_guard(commands.complete_cmd)))
    app.add_handler(CommandHandler("streak",command_guard(commands.streak_cmd)))
    app.add_handler(CommandHandler("badges",command_guard(commands.badges_cmd)))
    app.add_handler(CommandHandler("trivia",command_guard(commands.trivia_cmd)))
    app.add_handler(CommandHandler("triviaanswer",command_guard(commands.triviaanswer_cmd)))
    app.add_handler(CommandHandler("web",command_guard(web_cmd)))
    app.add_handler(CommandHandler("search",command_guard(search_cmd)))
    app.add_handler(CommandHandler("translate",command_guard(translate_cmd)))
    app.add_handler(CallbackQueryHandler(rps_callback, pattern=r"^rps:(rock|paper|scissors)$"))
    app.add_handler(MessageHandler(filters.PHOTO|filters.Sticker.ALL|filters.VOICE|filters.ANIMATION|filters.Document.ALL,media_reply))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND,process_text))
    return app
def main():
    try: settings=load_settings()
    except ValueError as exc:
        raise SystemExit(f"Configuration error: {exc}") from exc
    logging.basicConfig(level=getattr(logging,settings.log_level,logging.INFO),
                        format="%(asctime)s %(levelname)s %(name)s: %(message)s")
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger(__name__).info("Starting Aiko; message content logging=%s",settings.log_message_content)
    app=build_application(settings)
    app.run_polling(allowed_updates=Update.ALL_TYPES,drop_pending_updates=False)
