from __future__ import annotations
from datetime import datetime, timezone
from pathlib import Path
from telegram import Update
from telegram.ext import ContextTypes
from .mood import affection_tier
from . import i18n
from .access import has_bf_access, is_original_owner, relationship_label
from .preferences import LANGUAGES, parse_quiet_hours, validate_timezone
from .daily_challenges import challenge_for, next_streak
from .engine import ResponseEngine
import hmac

def _lang_for(context, update) -> str:
    """Resolve the sticky language for a command (no text to detect)."""
    app = context.application
    tracker = app.bot_data.get("languages")
    if tracker:
        uid = update.effective_user.id
        return tracker.get(uid, "en")
    return "en"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    app = context.application
    user = update.effective_user
    chat = update.effective_chat
    if not user or not chat:
        return
    db = app.bot_data["db"]
    await db.ensure_user(user.id, user.username, user.full_name, app.bot_data["persona"].get("timezone"))
    row = await db.get_user(user.id)
    settings = app.bot_data["settings"]
    role = relationship_label(settings, user.id, row)
    lang = _lang_for(context, update)
    welcome = i18n.text("start", lang, name=app.bot_data["persona"]["name"])
    role_text = (
        f"\n\nYour mode: {role}\n"
        "• Friends can chat normally in platonic mode.\n"
        "• Enter the shared pass privately with /pass <code> to unlock BF-style chat.\n"
        "• Use /role anytime to check your mode; use /unpass to return to Friend mode.\n"
        "• BF mode is a chat style, not administrator access."
    )
    await app.bot_data["humanizer"].send(context.bot, chat.id, welcome + role_text)

async def help_cmd(update,context):
    await update.effective_message.reply_text(i18n.text("help",_lang_for(context,update)))
async def mood_cmd(update,context):
    row=await context.application.bot_data["db"].get_user(update.effective_user.id)
    mood=row["mood"] if row else "neutral"
    lang=_lang_for(context,update)
    await update.effective_message.reply_text(i18n.text("mood_"+mood,lang))
async def affection_cmd(update,context):
    row=await context.application.bot_data["db"].get_user(update.effective_user.id)
    tier=affection_tier(row["affection"] if row else 10)
    lang=_lang_for(context,update)
    await update.effective_message.reply_text(i18n.text("aff_"+tier.replace(" ","_"),lang))
async def stats_cmd(update,context):
    app=context.application; db=app.bot_data["db"]; uid=update.effective_user.id
    row=await db.get_user(uid); facts=await db.fetchone("SELECT COUNT(*) n FROM facts WHERE user_id=?",(uid,))
    lang=_lang_for(context,update)
    if not row: await update.effective_message.reply_text(i18n.text("no_stats",lang)); return
    first=datetime.fromisoformat(row["first_seen"]); days=max(0,(datetime.now(timezone.utc)-first.replace(tzinfo=first.tzinfo or timezone.utc)).days)
    await update.effective_message.reply_text(i18n.text("stats",lang,affection=row["affection"],mood=row["mood"],days=days,messages=row["message_count"],facts=facts["n"]))
async def quiet_cmd(update,context):
    await context.application.bot_data["db"].execute("UPDATE users SET proactive_enabled=0 WHERE user_id=?",(update.effective_user.id,))
    await update.effective_message.reply_text(i18n.text("quiet",_lang_for(context,update)))

async def pass_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Verify the configured shared BF code, with persistent attempt throttling."""
    from datetime import timedelta
    app = context.application
    user = update.effective_user
    chat = update.effective_chat
    if not user or not chat:
        return
    settings = app.bot_data["settings"]
    db = app.bot_data["db"]

    async def hide_code_message():
        try:
            await update.effective_message.delete()
        except Exception:
            # Telegram/API permissions can prevent deletion; never fail access logic for this.
            pass

    if is_original_owner(settings, user.id):
        if context.args:
            await hide_code_message()
            await context.bot.send_message(chat_id=chat.id, text="👑💗 you're the original owner, so BF mode is always enabled. Admin powers remain tied to your OWNER_ID.")
        else:
            await update.effective_message.reply_text("👑💗 you're the original owner, so BF mode is always enabled. Admin powers remain tied to your OWNER_ID.")
        return
    if chat.type != "private":
        if context.args:
            await hide_code_message()
            await context.bot.send_message(chat_id=chat.id, text="🔐 for privacy, please send /pass <code> in my private chat, not in a group.")
        else:
            await update.effective_message.reply_text("🔐 for privacy, please send /pass <code> in my private chat, not in a group.")
        return
    row = await db.get_user(user.id)
    if row and has_bf_access(settings, user.id, row):
        await update.effective_message.reply_text("💗 BF mode is already enabled for you. Use /unpass to switch back to Friend mode.")
        return
    code = " ".join(context.args).strip()
    if not code:
        await update.effective_message.reply_text("to unlock BF-style companion chat, send /pass <code> in this private chat. Friends can already chat normally 🤝")
        return
    now = datetime.now(timezone.utc)
    attempt = await db.fetchone("SELECT attempts, window_started, locked_until FROM pass_attempts WHERE user_id=?", (user.id,))
    locked_until = None
    if attempt and attempt["locked_until"]:
        try:
            locked_until = datetime.fromisoformat(attempt["locked_until"])
            if locked_until > now:
                minutes = max(1, int((locked_until - now).total_seconds() // 60) + 1)
                await hide_code_message()
                await context.bot.send_message(chat_id=chat.id, text=f"🔒 too many incorrect attempts. Try again in about {minutes} minute(s).")
                return
        except ValueError:
            locked_until = None
    if attempt:
        try:
            window_start = datetime.fromisoformat(attempt["window_started"])
        except ValueError:
            window_start = now - timedelta(hours=1)
    else:
        window_start = now
    if attempt and now - window_start < timedelta(minutes=10) and not (locked_until and locked_until <= now):
        count = int(attempt["attempts"])
    else:
        count = 0
        window_start = now
    expected = settings.owner_code or ""
    if expected and hmac.compare_digest(code.encode("utf-8"), expected.encode("utf-8")):
        await db.execute("UPDATE users SET bf_access=1 WHERE user_id=?", (user.id,))
        await db.execute("DELETE FROM pass_attempts WHERE user_id=?", (user.id,))
        await hide_code_message()
        await context.bot.send_message(chat_id=chat.id, text="💗 pass accepted — BF-style companion mode is unlocked!\nYou can switch back anytime with /unpass. This does not grant admin commands or access to anyone else's data.")
        return
    await hide_code_message()
    count += 1
    new_locked_until = (now + timedelta(minutes=10)).isoformat() if count >= 5 else None
    await db.execute("INSERT INTO pass_attempts(user_id,attempts,window_started,locked_until) VALUES(?,?,?,?) ON CONFLICT(user_id) DO UPDATE SET attempts=excluded.attempts,window_started=excluded.window_started,locked_until=excluded.locked_until", (user.id, count, window_start.isoformat(), new_locked_until))
    suffix = " Too many attempts; locked for 10 minutes." if new_locked_until else f" Attempts remaining before cooldown: {5-count}."
    await context.bot.send_message(chat_id=chat.id, text="❌ that pass didn't match. You're still welcome here in Friend mode 🤝" + suffix)


async def unpass_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    app = context.application
    user = update.effective_user
    if not user:
        return
    settings = app.bot_data["settings"]
    if is_original_owner(settings, user.id):
        await update.effective_message.reply_text("👑 the original owner always keeps BF mode.")
        return
    db = app.bot_data["db"]
    await db.execute("UPDATE users SET bf_access=0 WHERE user_id=?", (user.id,))
    await update.effective_message.reply_text("done 🤝 you're back in Friend mode. You can unlock BF mode again with /pass <code>.")


async def role_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    app = context.application
    user = update.effective_user
    if not user:
        return
    row = await app.bot_data["db"].get_user(user.id)
    settings = app.bot_data["settings"]
    role = relationship_label(settings, user.id, row)
    if is_original_owner(settings, user.id):
        detail = "You're the configured original owner and always receive BF-style chat."
    elif has_bf_access(settings, user.id, row):
        detail = "Your shared pass has been verified, so BF-style chat is enabled."
    else:
        detail = "You're welcome to chat as a friend. A pass is optional and only changes the conversation style."
    await update.effective_message.reply_text(f"🎭 Your AIKO role: {role}\n{detail}\n\n/pass <code> — unlock BF mode (private chat only)\n/unpass — return to Friend mode")


async def bfusers_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """List BF-tier profiles; restricted to the real configured owner."""
    app = context.application
    if not is_original_owner(app.bot_data["settings"], update.effective_user.id if update.effective_user else None):
        await update.effective_message.reply_text("⛔ this list is only available to the configured original owner.")
        return
    rows = await app.bot_data["db"].fetchall(
        "SELECT user_id, username, display_name FROM users WHERE bf_access=1 ORDER BY display_name, user_id LIMIT 100"
    )
    lines = ["💗 BF-tier users (not admin accounts):"]
    lines.append(f"• Original owner ID: {app.bot_data['settings'].owner_id}")
    if rows:
        for row in rows:
            name = row["display_name"] or ("@" + row["username"] if row["username"] else "User")
            lines.append(f"• {name} — ID {row['user_id']}")
    else:
        lines.append("• No verified pass users yet.")
    await update.effective_message.reply_text("\n".join(lines))


async def checkin_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Persist a simple 1–10 mood check-in using the existing profile table."""
    if not context.args or not context.args[0].isdigit() or not 1 <= int(context.args[0]) <= 10:
        await update.effective_message.reply_text("🌤️ mood check-in: use /checkin <1-10>\n1 = very low, 5 = okay, 10 = amazing. Your rating is saved to your local profile.")
        return
    score = int(context.args[0])
    mood = "worried" if score <= 3 else "neutral" if score <= 6 else "happy" if score <= 8 else "playful"
    await context.application.bot_data["db"].execute(
        "UPDATE users SET mood=?, mood_updated=? WHERE user_id=?",
        (mood, datetime.now(timezone.utc).isoformat(), update.effective_user.id),
    )
    message = {"worried": "🫂 thanks for checking in. want to talk about what's making today hard?", "neutral": "🙂 got it — steady/okay. hope the day gets a little better.", "happy": "✨ love that! what's been the best part of your day?", "playful": "🎉 amazing energy! what's got you feeling this good?"}[mood]
    await update.effective_message.reply_text(f"saved mood: {score}/10 ({mood}).\n{message}")

async def loud_cmd(update,context):
    await context.application.bot_data["db"].execute("UPDATE users SET proactive_enabled=1 WHERE user_id=?",(update.effective_user.id,))
    await update.effective_message.reply_text(i18n.text("loud",_lang_for(context,update)))
async def name_cmd(update, context):
    name = " ".join(context.args).strip()
    lang = _lang_for(context, update)
    if not name or len(name) > 60:
        await update.effective_message.reply_text(i18n.text("name_usage", lang))
        return
    await context.application.bot_data["db"].execute(
        "UPDATE users SET display_name=? WHERE user_id=?", (name, update.effective_user.id)
    )
    await update.effective_message.reply_text(i18n.text("name_set", lang, name=name))


async def reset_cmd(update, context):
    context.user_data["confirm_reset"] = True
    await update.effective_message.reply_text(i18n.text("reset_ask", _lang_for(context, update)) + "\nConfirm with /confirm_reset.")


async def owner_cmd(update, context):
    app = context.application
    user = update.effective_user
    settings = app.bot_data["settings"]
    if not user:
        return
    if not is_original_owner(settings, user.id):
        await update.effective_message.reply_text(
            "👑 AIKO's original owner is configured privately. Your chat role is shown by /role."
        )
        return
    await update.effective_message.reply_text(
        "👑💗 Original Owner / BF mode\n"
        f"Telegram user ID: {settings.owner_id}\n"
        f"Configured username: @{settings.owner_username or 'not-set'}\n"
        "Only this original owner can use owner-only administration commands."
    )

async def confirm_reset(update,context):
    lang=_lang_for(context,update)
    if not context.user_data.pop("confirm_reset",False):
        await update.effective_message.reply_text(i18n.text("reset_none",lang)); return
    await context.application.bot_data["db"].execute("UPDATE users SET affection=10,mood='neutral',mood_updated=? WHERE user_id=?",(datetime.now(timezone.utc).isoformat(),update.effective_user.id))
    await update.effective_message.reply_text(i18n.text("reset_done",lang))
async def forget_cmd(update,context):
    context.user_data["confirm_forget"]=True
    await update.effective_message.reply_text(i18n.text("forget_ask",_lang_for(context,update)))
async def confirm_forget(update,context):
    lang=_lang_for(context,update)
    if not context.user_data.pop("confirm_forget",False):
        await update.effective_message.reply_text(i18n.text("forget_none",lang)); return
    await context.application.bot_data["memory"].forget(update.effective_user.id)
    await update.effective_message.reply_text(i18n.text("forget_done",lang))
def owner_only(update,context):
    owner=context.application.bot_data["settings"].owner_id
    return owner is not None and update.effective_user and update.effective_user.id==owner
async def debug_cmd(update,context):
    if not owner_only(update,context): return
    msg=" ".join(context.args).strip()
    lang=_lang_for(context,update)
    if not msg: await update.effective_message.reply_text("usage: /debug <message>"); return
    result=context.application.bot_data["engine"].debug_match(msg,{"affection":100},lang=lang)
    if result: await update.effective_message.reply_text(f"rule={result.rule_id}\npriority={result.priority}\nweight={result.weight}\nscore={result.score}\nlang={lang}")
    else:
        reflected=context.application.bot_data["engine"].apply_reflection(msg,lang=lang)
        await update.effective_message.reply_text("reflection rule" if reflected else "fallback (no direct rule)")
async def reload_cmd(update,context):
    if not owner_only(update,context): return
    from .config import load_yaml, validate_persona
    app=context.application
    try:
        persona=load_yaml(app.bot_data["settings"].persona_file); validate_persona(persona)
        # Build the replacement engine first; only swap it into live state on success
        # so a failed reload cannot partially change runtime state.
        new_engine=ResponseEngine(persona,app.bot_data["settings"].rules_files)
        app.bot_data["engine"]=new_engine
        app.bot_data["persona"]=persona
        await update.effective_message.reply_text("persona and rules reloaded ✨")
    except Exception as exc: await update.effective_message.reply_text(f"reload failed: {exc}")
async def broadcast_cmd(update,context):
    if not owner_only(update,context): return
    msg=" ".join(context.args).strip()
    if not msg: await update.effective_message.reply_text("usage: /broadcast <text>"); return
    rows=await context.application.bot_data["db"].fetchall("SELECT user_id FROM users")
    sent=0
    for row in rows:
        try: await context.bot.send_message(row["user_id"],msg); sent+=1
        except Exception: pass
    await update.effective_message.reply_text(f"broadcast sent to {sent} chats.")

async def memory_cmd(update, context):
    app=context.application; uid=update.effective_user.id
    facts=await app.bot_data["memory"].all_facts(uid)
    learning = app.bot_data.get("conversation_learning")
    summary = learning.summary(uid) if learning else "No conversation-context store is enabled."
    if not facts:
        await update.effective_message.reply_text("meri memory notebook abhi khaali hai ji 💗\n\n" + summary + "\n\nUse /forget to clear saved facts or /forgetall to erase your local profile and context.")
        return
    lines=["meri local memory notebook 📒💗"]
    for row in facts[:30]:
        lines.append(f"• {row['key'].replace('_',' ')}: {row['value']}")
    lines.append("\n" + summary)
    lines.append("\nremove saved facts with /forget; delete all your bot data with /forgetall")
    await update.effective_message.reply_text("\n".join(lines))

async def forgetall_cmd(update, context):
    context.user_data["confirm_forgetall"] = True
    await update.effective_message.reply_text("are you sure? this deletes your saved facts, conversation metadata, and profile from the local database. reply /confirm_forgetall to confirm.")

async def confirm_forgetall(update, context):
    if not context.user_data.pop("confirm_forgetall", False):
        await update.effective_message.reply_text("there's no pending delete request.")
        return
    uid=update.effective_user.id
    await context.application.bot_data["db"].execute("DELETE FROM users WHERE user_id=?",(uid,))
    dialogue = context.application.bot_data.get("dialogue")
    if dialogue:
        dialogue.last_intent.pop(uid, None)
        dialogue.last_reply.pop(uid, None)
        dialogue.preferred_language.pop(uid, None)
    learning = context.application.bot_data.get("conversation_learning")
    if learning:
        learning.forget(uid)
    brain = context.application.bot_data.get("local_brain")
    if brain:
        brain.forget(uid)
    languages = context.application.bot_data.get("languages")
    if languages and hasattr(languages, "forget"):
        languages.forget(uid)
    tracker = context.application.bot_data.get("dialogue")
    if tracker:
        for attr in ("last_intent", "last_reply", "preferred_language"):
            value = getattr(tracker, attr, None)
            if isinstance(value, dict): value.pop(uid, None)
    researcher = context.application.bot_data.get("web_researcher")
    if researcher:
        researcher.forget_user(uid)
    # Clear all transient per-user state after authorization and deletion are complete.
    context.user_data.clear()
    await update.effective_message.reply_text("done ji. your local profile, saved facts, chat-learning context, and search preference have been cleared 🫂")

async def joke_cmd(update, context):
    import random
    jokes = [
        "meri sleep schedule itni kharaab hai ki alarm bhi mujhe dekh ke snooze ho jaata hai 💀",
        "meri productivity aur haunted house mein same baat hai: dono mein andar jaane ka mann nahi karta 😂💀",
        "life ne mujhe lemons diye, maine unka screenshot leke socha kal deal karungi 😭",
        "mera bank balance itna mysterious hai ki main khud usse milne appointment leti hoon 💀",
        "main overthink itna karti hoon ki apne hi thoughts ko terms and conditions bhej doon 😂",
    ]
    await update.effective_message.reply_text(random.choice(jokes))

async def games_cmd(update, context):
    await update.effective_message.reply_text("chalo ji, game time 🎮\n/riddle — solve a riddle\n/answer <your guess> — answer the current riddle\n/rps <rock|paper|scissors> — quick match\n/joke — dark-ish joke (no real-person targeting)")

RIDDLES = [
    ("the more you take, the more you leave behind. what am i?", "footsteps"),
    ("what has keys but can't open locks?", "piano"),
    ("what gets wetter the more it dries?", "towel"),
    ("what has a face and two hands but no arms or legs?", "clock"),
]
async def riddle_cmd(update, context):
    import random
    question, answer = random.choice(RIDDLES)
    context.user_data["riddle_answer"] = answer
    await update.effective_message.reply_text("paheli time 😏 " + question + "\nanswer dene ke liye /answer <guess> use karo")

async def answer_cmd(update, context):
    answer=context.user_data.get("riddle_answer")
    guess=" ".join(context.args).strip().lower()
    if not answer:
        await update.effective_message.reply_text("pehle /riddle chalao ji 😌")
    elif not guess:
        await update.effective_message.reply_text("usage: /answer <your guess>")
    elif guess == answer or (answer == "footsteps" and guess in {"steps", "foot steps"}):
        context.user_data.pop("riddle_answer",None)
        row = await context.application.bot_data["db"].get_user(update.effective_user.id)
        bf_mode = has_bf_access(context.application.bot_data["settings"], update.effective_user.id, row)
        reward = "tumhe ek virtual kiss milti hai 😘" if bf_mode else "you get bragging rights and a virtual trophy 🏆"
        await update.effective_message.reply_text(f"arre waah! sahi jawab 🏆 {reward}")
    else:
        await update.effective_message.reply_text("hehe, galat 😈 ek aur try karo ya /riddle se nayi paheli lo")

async def rps_cmd(update, context):
    import random
    from telegram import InlineKeyboardButton, InlineKeyboardMarkup
    choices={"rock":"🪨 rock", "paper":"📄 paper", "scissors":"✂️ scissors"}
    if not context.args or context.args[0].lower() not in choices:
        keyboard=[[InlineKeyboardButton(label, callback_data="rps:"+key) for key,label in choices.items()]]
        await update.effective_message.reply_text("choose your move 😏", reply_markup=InlineKeyboardMarkup(keyboard))
        return
    user=context.args[0].lower(); bot=random.choice(list(choices))
    outcome="draw 😌" if user==bot else "you win 😭💕" if (user,bot) in {("rock","scissors"),("paper","rock"),("scissors","paper")} else "i win 😈 rematch?"
    await update.effective_message.reply_text(f"you: {choices[user]}\nme: {choices[bot]}\n{outcome}")

async def export_cmd(update, context):
    import io, json
    uid=update.effective_user.id; db=context.application.bot_data["db"]
    user=await db.get_user(uid); facts=await context.application.bot_data["memory"].all_facts(uid)
    journal=await db.fetchall("SELECT entry,created_at FROM journal_entries WHERE user_id=? ORDER BY id",(uid,))
    reminders=await db.fetchall("SELECT message,due_at,created_at,sent FROM reminders WHERE user_id=? ORDER BY id",(uid,))
    moods=await db.fetchall("SELECT old_mood,new_mood,reason,created_at FROM mood_log WHERE user_id=? ORDER BY id",(uid,))
    checkins=await db.fetchall("SELECT challenge_date,challenge_key,completed,points,completed_at FROM challenge_progress WHERE user_id=? ORDER BY challenge_date",(uid,))
    streak = await db.fetchone("SELECT current_streak,best_streak,last_completed,total_points FROM challenge_streaks WHERE user_id=?",(uid,))
    badges = await db.fetchall("SELECT badge_key,earned_at FROM challenge_badges WHERE user_id=? ORDER BY earned_at",(uid,))
    learning = context.application.bot_data.get("conversation_learning")
    context_data = learning.export_user(uid) if learning else {}
    profile = dict(user) if user else None
    if profile:
        for private_key in ("pass_code", "owner_code"):
            profile.pop(private_key, None)
    payload={"profile":profile,"facts":[dict(x) for x in facts],
             "journal_entries":[dict(x) for x in journal],"reminders":[dict(x) for x in reminders],
             "mood_log":[dict(x) for x in moods],"daily_challenges":[dict(x) for x in checkins],
             "challenge_streak":dict(streak) if streak else None,
             "badges":[dict(x) for x in badges],
             "conversation_context":context_data,
             "note":"This export includes your locally stored conversation context. Authentication secrets are excluded."}
    data=json.dumps(payload,ensure_ascii=False,indent=2).encode("utf-8")
    await update.effective_message.reply_document(document=io.BytesIO(data),filename="aiko-my-data.json",caption="your local Aiko data export 📦")

async def personality_cmd(update, context):
    choices={"soft":"soft", "playful":"playful", "dark":"dark-humor"}
    if not context.args or context.args[0].lower() not in choices:
        await update.effective_message.reply_text("choose a style: /personality soft, /personality playful, or /personality dark")
        return
    style=choices[context.args[0].lower()]
    context.user_data["personality_style"]=style
    await update.effective_message.reply_text(f"done ji 💗 personality style for this session: {style}")


async def journal_cmd(update, context):
    from datetime import datetime, timezone
    uid=update.effective_user.id; db=context.application.bot_data["db"]
    args=" ".join(context.args).strip()
    if args.lower()=="clear":
        context.user_data["confirm_journal_clear"]=True
        await update.effective_message.reply_text("delete all journal entries? confirm with /confirm_journal_clear")
        return
    if args:
        if len(args)>2000:
            await update.effective_message.reply_text("journal entries must be under 2000 characters.")
            return
        await db.execute("INSERT INTO journal_entries(user_id,entry,created_at) VALUES(?,?,?)",(uid,args,datetime.now(timezone.utc).isoformat()))
        await update.effective_message.reply_text("saved in your local journal 📓💗 use /journal to review recent entries.")
        return
    rows=await db.fetchall("SELECT id,entry,created_at FROM journal_entries WHERE user_id=? ORDER BY id DESC LIMIT 5",(uid,))
    if not rows:
        await update.effective_message.reply_text("journal abhi khaali hai. add an entry with /journal <what happened today>")
        return
    lines=["your last journal entries 📓"]
    for row in rows:
        stamp=row["created_at"][:16].replace("T"," ")
        lines.append(f"\n{stamp} — {row['entry']}")
    lines.append("\nclear all entries with /journal clear, then /confirm_journal_clear")
    await update.effective_message.reply_text("\n".join(lines))

async def confirm_journal_clear(update, context):
    if not context.user_data.pop("confirm_journal_clear",False):
        await update.effective_message.reply_text("there's no pending journal deletion.")
        return
    await context.application.bot_data["db"].execute("DELETE FROM journal_entries WHERE user_id=?",(update.effective_user.id,))
    await update.effective_message.reply_text("journal cleared from local storage 🫂")

# ─── Adult-mode gating ─────────────────────────────────────────────────────
# Adult-themed replies (suggestive flirting, sensual romance, adult teasing)
# are disabled by default. A user must explicitly opt in with /adult on
# (confirmation required). Stop/boundary requests always take priority.
async def adult_cmd(update, context):
    """Show or change adult-mode preference for the current user."""
    app=context.application
    settings=app.bot_data["settings"]
    uid=update.effective_user.id
    db=app.bot_data["db"]
    lang=_lang_for(context,update)

    row=await db.get_user(uid)
    if not has_bf_access(settings, uid, row):
        await update.effective_message.reply_text("adult-themed roleplay settings are only available in BF mode. Friend mode stays platonic 🤝💗")
        return
    current = bool(row["adult_mode"]) if row is not None else False
    enabled = settings.adult_mode_enabled or current

    if not context.args:
        await update.effective_message.reply_text(
            f"adult mode is currently {'on' if enabled else 'off'}. "
            f"use /adult on or /adult off (enabling requires confirmation)."
        )
        return

    sub=context.args[0].lower()
    if sub=="status":
        source = "global default" if settings.adult_mode_enabled else ("your choice" if current else "off")
        await update.effective_message.reply_text(
            f"adult mode: {'on' if enabled else 'off'} ({source}). use /adult on or /adult off."
        )
        return
    if sub=="on":
        if enabled:
            await update.effective_message.reply_text("adult mode is already enabled for you 💗")
            return
        context.user_data["confirm_adult_on"]=True
        await update.effective_message.reply_text(
            "adult-themed replies (suggestive flirting, sensual romance, adult teasing) "
            "are disabled by default. confirm with /confirm_adult_on to enable for your chat. "
            "you can disable anytime with /adult off."
        )
        return
    if sub=="off":
        if not enabled:
            await update.effective_message.reply_text("adult mode is already off 💗")
            return
        context.user_data["confirm_adult_off"]=True
        await update.effective_message.reply_text(
            "confirm with /confirm_adult_off to disable adult-themed replies for your chat."
        )
        return
    await update.effective_message.reply_text("usage: /adult on | /adult off | /adult status")

async def confirm_adult_on(update, context):
    lang=_lang_for(context,update)
    row = await context.application.bot_data["db"].get_user(update.effective_user.id)
    if not has_bf_access(context.application.bot_data["settings"], update.effective_user.id, row):
        context.user_data.pop("confirm_adult_on", None)
        await update.effective_message.reply_text("BF mode is required for adult-themed roleplay settings. Friend mode stays platonic 🤝💗")
        return
    if not context.user_data.pop("confirm_adult_on",False):
        await update.effective_message.reply_text("no pending adult-mode enablement."); return
    uid=update.effective_user.id
    await context.application.bot_data["db"].execute(
        "UPDATE users SET adult_mode=1 WHERE user_id=?",(uid,))
    await update.effective_message.reply_text(
        "adult mode enabled for your chat 💗 adult-themed replies (suggestive flirting, "
        "sensual romance, adult teasing) are now allowed. use /adult off to disable."
    )

async def confirm_adult_off(update, context):
    lang=_lang_for(context,update)
    if not context.user_data.pop("confirm_adult_off",False):
        await update.effective_message.reply_text("no pending adult-mode disablement."); return
    uid=update.effective_user.id
    await context.application.bot_data["db"].execute(
        "UPDATE users SET adult_mode=0 WHERE user_id=?",(uid,))
    await update.effective_message.reply_text(
        "adult mode disabled for your chat 🫂 adult-themed replies are now turned off. "
        "use /adult on to re-enable."
    )

async def remind_cmd(update, context):
    import re
    from datetime import datetime, timezone, timedelta
    if len(context.args)<2:
        await update.effective_message.reply_text("usage: /remind <10m|2h|1d> <reminder text>\nexample: /remind 30m drink water")
        return
    match=re.fullmatch(r"(\d{1,5})(m|h|d)",context.args[0].lower())
    if not match:
        await update.effective_message.reply_text("use a duration like 10m, 2h or 1d.")
        return
    amount=int(match.group(1)); unit=match.group(2)
    seconds=amount*{"m":60,"h":3600,"d":86400}[unit]
    if seconds<60 or seconds>30*86400:
        await update.effective_message.reply_text("reminders must be between 1 minute and 30 days.")
        return
    message=" ".join(context.args[1:]).strip()
    if len(message)>500:
        await update.effective_message.reply_text("please keep reminder text under 500 characters.")
        return
    now=datetime.now(timezone.utc); due=now+timedelta(seconds=seconds)
    await context.application.bot_data["db"].execute("INSERT INTO reminders(user_id,message,due_at,created_at,sent) VALUES(?,?,?,?,0)",(update.effective_user.id,message,due.isoformat(),now.isoformat()))
    await update.effective_message.reply_text(f"done ji ⏰ i'll remind you in {amount}{unit}: {message}")

async def settings_cmd(update, context):
    await update.effective_message.reply_text(
        "your settings ⚙️\n/role — see Friend/BF chat mode\n/pass <code> — unlock BF-style chat (private chat only)\n/unpass — return to Friend mode\n/prefs — set language, time zone, quiet hours and greetings\n/checkin <1-10> — save today's mood\n/quiet — pause proactive messages\n/loud — enable proactive messages\n/personality soft|playful|dark — choose this-session style\n/name <name> — set your display name\n/adult on|off|status — gate adult-themed replies (opt-in, confirmation required)\n/memory — review saved facts and context\n/privacy — see data controls\n/forget — delete facts\n/forgetall — delete your local profile and persistent context\n/export — export your data\n/daily, /complete, /streak, /badges — daily challenge and rewards\n/trivia, /triviaanswer — quick quiz\n/owner — show owner information\n/ai_status and /health — owner diagnostics"
    )

async def prefs_cmd(update, context):
    """Persistent per-user language, time zone, quiet-hours and greeting preferences."""
    uid = update.effective_user.id
    db = context.application.bot_data["db"]
    args = list(context.args or [])
    row = await db.get_user(uid)
    if not args or args[0].lower() in {"show", "status"}:
        row = row or {}
        qstart, qend = row["quiet_start"], row["quiet_end"]
        if row["quiet_override"]:
            quiet = "off" if qstart is None or qend is None else f"{int(qstart):02d}-{int(qend):02d}"
        else:
            quiet = f"deployment default {context.application.bot_data['settings'].quiet_hours_start:02d}-{context.application.bot_data['settings'].quiet_hours_end:02d}"
        await update.effective_message.reply_text(
            "⚙️ Your saved preferences\n"
            f"Language: {row['lang_preference'] or row['lang'] or 'hinglish'}\n"
            f"Time zone: {row['timezone_preference'] or row['timezone'] or 'UTC'}\n"
            f"Quiet hours: {quiet} (local time)\n"
            f"Proactive messages: {'on' if row['proactive_enabled'] else 'off'}\n"
            f"Daily greetings: {'on' if row['greetings_enabled'] else 'off'}\n"
            f"Auto fact memory: {'on' if row['memory_enabled'] else 'off'}\n"
            f"Conversation learning: {'on' if row['learning_enabled'] else 'off'}\n\n"
            "Set: /prefs language en|hi|hinglish|auto\n"
            "/prefs timezone Asia/Kolkata\n/prefs quiet 23-08  (or quiet off)\n"
            "/prefs greetings on|off\n/prefs memory on|off\n/prefs learning on|off\n/quiet and /loud pause/resume all proactive messages"
        )
        return
    action = args[0].lower()
    if action in {"language", "lang"}:
        value = args[1].lower() if len(args) > 1 else ""
        if value not in LANGUAGES:
            await update.effective_message.reply_text("Use /prefs language en, hi, hinglish, or auto.")
            return
        await db.execute("UPDATE users SET lang_preference=?, lang=? WHERE user_id=?", (value, "hinglish" if value == "auto" else value, uid))
        tracker = context.application.bot_data.get("languages")
        if tracker and value != "auto": tracker.set(uid, value)
        dialogue = context.application.bot_data.get("dialogue")
        if dialogue and value == "auto": dialogue.preferred_language.pop(uid, None)
        await update.effective_message.reply_text(f"🌐 Saved language preference: {value}.")
    elif action in {"timezone", "tz"}:
        value = " ".join(args[1:])
        try: value = validate_timezone(value)
        except ValueError as exc:
            await update.effective_message.reply_text(str(exc)); return
        await db.execute("UPDATE users SET timezone=?, timezone_preference=? WHERE user_id=?", (value, value, uid))
        await update.effective_message.reply_text(f"🕰️ Time zone saved as {value}. Quiet hours and greetings use this local time.")
    elif action == "quiet":
        try: start, end = parse_quiet_hours(" ".join(args[1:]))
        except ValueError as exc:
            await update.effective_message.reply_text(str(exc)); return
        await db.execute("UPDATE users SET quiet_start=?, quiet_end=?, quiet_override=1 WHERE user_id=?", (start, end, uid))
        value = "off" if start is None else f"{start:02d}-{end:02d}"
        await update.effective_message.reply_text(f"🌙 Your local quiet hours are now {value}.")
    elif action in {"greetings", "greeting"}:
        value = args[1].lower() if len(args) > 1 else ""
        if value not in {"on", "off"}:
            await update.effective_message.reply_text("Use /prefs greetings on or /prefs greetings off."); return
        await db.execute("UPDATE users SET greetings_enabled=? WHERE user_id=?", (1 if value == "on" else 0, uid))
        await update.effective_message.reply_text(f"🔔 Daily greetings are {value}.")
    elif action in {"memory", "learning"}:
        value = args[1].lower() if len(args) > 1 else ""
        if value not in {"on", "off"}:
            await update.effective_message.reply_text(f"Use /prefs {action} on or /prefs {action} off."); return
        column = "memory_enabled" if action == "memory" else "learning_enabled"
        await db.execute(f"UPDATE users SET {column}=? WHERE user_id=?", (1 if value == "on" else 0, uid))
        if value == "off" and action == "learning":
            learner = context.application.bot_data.get("conversation_learning")
            if learner: learner.forget(uid)
        await update.effective_message.reply_text(f"🔐 Automatic {action} is now {value}." + (" Existing saved data is retained; use /forgetall to erase it." if value == "off" and action == "memory" else ""))
    else:
        await update.effective_message.reply_text("Usage: /prefs [language|timezone|quiet|greetings] ...")


async def privacy_cmd(update, context):
    await update.effective_message.reply_text(
        "🔐 Your AIKO privacy controls\n"
        "• /memory — inspect saved facts and conversation-context summary\n"
        "• /export — download a JSON export of your profile, facts, journal, reminders, mood log and saved context\n"
        "• /forget — delete saved facts after confirmation\n"
        "• /forgetall — erase your local database profile and per-user context after confirmation\n"
        "• /quiet — pause proactive messages; /loud resumes them\n"
        "• /prefs memory off — stop automatic fact extraction; /prefs learning off — stop local conversation-context storage\n"
        "Your messages may be sent to the AI provider configured by the bot owner when AI replies are used. Avoid sharing passwords, tokens, or highly sensitive details."
    )


async def revoke_cmd(update, context):
    settings = context.application.bot_data["settings"]
    if not owner_only(update, context):
        await update.effective_message.reply_text("⛔ owner only."); return
    if not context.args or not context.args[0].isdigit():
        await update.effective_message.reply_text("Usage: /revoke <telegram_user_id> — revokes BF mode but does not block chat."); return
    target = int(context.args[0])
    if target == settings.owner_id:
        await update.effective_message.reply_text("The original owner's BF role cannot be revoked."); return
    db = context.application.bot_data["db"]
    await db.execute("UPDATE users SET bf_access=0 WHERE user_id=?", (target,))
    await db.execute("DELETE FROM pass_attempts WHERE user_id=?", (target,))
    await update.effective_message.reply_text(f"✅ BF access revoked for user {target}. They can still chat in Friend mode.")


async def backup_cmd(update, context):
    if not owner_only(update, context):
        await update.effective_message.reply_text("⛔ owner only."); return
    import asyncio
    from .backup import create_backup
    settings = context.application.bot_data["settings"]
    path = Path(settings.db_path)
    try:
        result = await asyncio.to_thread(create_backup, path, path.parent / "backups", 7)
    except Exception as exc:
        await update.effective_message.reply_text(f"❌ Backup failed ({type(exc).__name__}). Check server logs and storage permissions.")
        return
    await update.effective_message.reply_text(f"✅ Database backup created and validated: {result.name}. Keep the backups directory private and off public releases.")


async def health_cmd(update, context):
    if not owner_only(update, context):
        await update.effective_message.reply_text("⛔ owner only."); return
    app = context.application
    db = app.bot_data.get("db")
    try:
        row = await db.fetchone("PRAGMA integrity_check")
        db_status = row[0] if row else "unknown"
    except Exception as exc:
        db_status = f"error ({type(exc).__name__})"
    client = app.bot_data.get("multi_ai")
    statuses = client.get_status() if client else {}
    active = [name for name, state in statuses.items() if state["enabled"] and state["available"]]
    lines = ["🩺 AIKO health report", f"Database integrity: {db_status}", f"Configured AI providers available (cooldown-free): {', '.join(active) if active else 'none'}"]
    if client and hasattr(client, "health_summary"):
        lines.append(client.health_summary())
    if db_status != "ok": lines.append("⚠️ Database integrity is not OK; stop and back up the database before attempting repairs.")
    await update.effective_message.reply_text("\n".join(lines))


DAILY_TRIVIA = [
    ("Which planet is known as the Red Planet?", ["Venus", "Mars", "Jupiter", "Mercury"], "mars"),
    ("How many sides does a hexagon have?", ["5", "6", "7", "8"], "6"),
    ("Which gas do plants absorb during photosynthesis?", ["Oxygen", "Nitrogen", "Carbon dioxide", "Helium"], "carbon dioxide"),
    ("What is the largest ocean on Earth?", ["Atlantic", "Indian", "Arctic", "Pacific"], "pacific"),
    ("What is 9 × 7?", ["56", "63", "72", "79"], "63"),
]
DAILY_TASKS = [
    ("kindness", "Send one kind message to someone you appreciate."),
    ("water", "Take a short break and drink a glass of water."),
    ("learning", "Learn one new fact and explain it in your own words."),
    ("gratitude", "Name one small thing that went well today."),
    ("stretch", "Stand up and stretch for two minutes."),
]

async def daily_cmd(update, context):
    import random
    from datetime import date
    uid = update.effective_user.id
    db = context.application.bot_data["db"]
    row = await db.get_user(uid)
    try:
        from zoneinfo import ZoneInfo
        today = datetime.now(ZoneInfo((row["timezone"] if row else None) or "UTC")).date()
    except Exception:
        today = datetime.now(timezone.utc).date()
    day, key, text = challenge_for(uid, today)
    saved = await db.fetchone("SELECT completed FROM challenge_progress WHERE user_id=? AND challenge_date=?", (uid, day))
    await db.execute("INSERT OR IGNORE INTO challenge_progress(user_id,challenge_date,challenge_key) VALUES(?,?,?)", (uid, day, key))
    suffix = "✅ Already completed today — nice work!" if saved and saved["completed"] else "When you're done, send /complete. This is optional; no streak penalty for taking a day off."
    await update.effective_message.reply_text(f"🌟 Your daily challenge ({day})\n{text}\n\n{suffix}")

async def complete_cmd(update, context):
    from datetime import timedelta
    uid = update.effective_user.id
    db = context.application.bot_data["db"]
    row = await db.get_user(uid)
    try:
        from zoneinfo import ZoneInfo
        today = datetime.now(ZoneInfo((row["timezone"] if row else None) or "UTC")).date()
    except Exception:
        today = datetime.now(timezone.utc).date()
    day, key, _ = challenge_for(uid, today)
    await db.execute("INSERT OR IGNORE INTO challenge_progress(user_id,challenge_date,challenge_key) VALUES(?,?,?)", (uid, day, key))
    progress = await db.fetchone("SELECT completed FROM challenge_progress WHERE user_id=? AND challenge_date=?", (uid, day))
    if progress and progress["completed"]:
        await update.effective_message.reply_text("✅ You've already completed today's challenge. Keep it gentle and enjoy your day!"); return
    stamp = datetime.now(timezone.utc).isoformat()
    streak = await db.fetchone("SELECT current_streak,best_streak,last_completed,total_points FROM challenge_streaks WHERE user_id=?", (uid,))
    if streak and streak["last_completed"] == day:
        current = max(1, int(streak["current_streak"] or 0))
    else:
        current = next_streak(streak["last_completed"] if streak else None, int(streak["current_streak"] or 0) if streak else 0, today)
    best = max(current, int(streak["best_streak"] or 0) if streak else 0)
    total = int(streak["total_points"] or 0) if streak else 0
    updated = await db.execute("UPDATE challenge_progress SET completed=1,points=10,completed_at=? WHERE user_id=? AND challenge_date=? AND completed=0", (stamp, uid, day))
    if getattr(updated, "rowcount", 1) == 0:
        await update.effective_message.reply_text("✅ You've already completed today's challenge."); return
    await db.execute("INSERT INTO challenge_streaks(user_id,current_streak,best_streak,last_completed,total_points) VALUES(?,?,?,?,10) ON CONFLICT(user_id) DO UPDATE SET current_streak=excluded.current_streak,best_streak=excluded.best_streak,last_completed=excluded.last_completed,total_points=challenge_streaks.total_points+10", (uid, current, best, day))
    badge_defs = []
    if total == 0: badge_defs.append(("first_step", "🌱 First Step"))
    if current >= 3: badge_defs.append(("streak_3", "🔥 3-Day Streak"))
    if current >= 7: badge_defs.append(("streak_7", "🏅 7-Day Streak"))
    if current >= 30: badge_defs.append(("streak_30", "👑 30-Day Streak"))
    if total + 10 >= 100: badge_defs.append(("points_100", "⭐ 100 Points"))
    new_badges = []
    for badge_key, label in badge_defs:
        inserted = await db.execute("INSERT OR IGNORE INTO challenge_badges(user_id,badge_key,earned_at) VALUES(?,?,?)", (uid, badge_key, stamp))
        if getattr(inserted, "rowcount", 0) > 0: new_badges.append(label)
    award_text = "\nNew badge: " + ", ".join(new_badges) if new_badges else ""
    await update.effective_message.reply_text(f"🎉 Challenge completed! +10 points\n🔥 Current streak: {current} day(s)\n🏅 Best streak: {best} day(s)\n⭐ Total points: {total + 10}{award_text}")

async def badges_cmd(update, context):
    rows = await context.application.bot_data["db"].fetchall("SELECT badge_key,earned_at FROM challenge_badges WHERE user_id=? ORDER BY earned_at", (update.effective_user.id,))
    labels = {"first_step":"🌱 First Step", "streak_3":"🔥 3-Day Streak", "streak_7":"🏅 7-Day Streak", "streak_30":"👑 30-Day Streak", "points_100":"⭐ 100 Points"}
    if not rows:
        await update.effective_message.reply_text("🎖️ No badges yet. Complete /daily and /complete to earn your first badge."); return
    lines = ["🎖️ Your AIKO badges"] + [f"{labels.get(r['badge_key'], r['badge_key'])} — {r['earned_at'][:10]}" for r in rows]
    await update.effective_message.reply_text("\n".join(lines))

async def streak_cmd(update, context):
    uid = update.effective_user.id
    row = await context.application.bot_data["db"].fetchone("SELECT current_streak,best_streak,total_points,last_completed FROM challenge_streaks WHERE user_id=?", (uid,))
    if not row:
        await update.effective_message.reply_text("🌱 No completed challenges yet. Use /daily to start one — streaks are for encouragement, not pressure."); return
    await update.effective_message.reply_text(f"🏆 Your challenge stats\nCurrent streak: {row['current_streak']} day(s)\nBest streak: {row['best_streak']} day(s)\nTotal points: {row['total_points']}\nLast completed: {row['last_completed']}")

async def trivia_cmd(update, context):
    import random
    q, options, answer = random.choice(DAILY_TRIVIA)
    context.user_data["trivia_answer"] = answer
    context.user_data["trivia_options"] = [opt.lower() for opt in options]
    labels = ["A", "B", "C", "D"]
    lines = ["🧠 Quick trivia", q] + [f"{labels[i]}. {opt}" for i, opt in enumerate(options)]
    lines.append("Reply with /triviaanswer <answer or letter>.")
    await update.effective_message.reply_text("\n".join(lines))

async def triviaanswer_cmd(update, context):
    answer = context.user_data.get("trivia_answer")
    guess = " ".join(context.args).strip().lower()
    if not answer:
        await update.effective_message.reply_text("Start a quiz first with /trivia."); return
    if not guess:
        await update.effective_message.reply_text("Usage: /triviaanswer <answer or A/B/C/D>"); return
    options = context.user_data.get("trivia_options", [])
    letter_map = {"a": 0, "b": 1, "c": 2, "d": 3}
    valid_letter = guess in letter_map and len(options) > letter_map[guess] and options[letter_map[guess]] == answer
    if guess == answer or valid_letter:
        context.user_data.pop("trivia_answer", None)
        context.user_data.pop("trivia_options", None)
        await update.effective_message.reply_text("✅ Correct! Nice one 🧠✨")
    else:
        await update.effective_message.reply_text("Not quite 😄 try again, or start a fresh one with /trivia.")

async def ai_status_cmd(update, context):
    """Show status of all AI providers in the fallback chain."""
    if not owner_only(update, context):
        return
    multi_ai = context.application.bot_data.get("multi_ai")
    if not multi_ai:
        await update.effective_message.reply_text("Multi-AI client not initialized.")
        return
    status = multi_ai.get_status()
    lines = ["🤖 **Multi-AI Provider Status**\n"]
    for name, info in status.items():
        status_emoji = "✅" if info["enabled"] and info["available"] else "⚠️" if info["enabled"] else "❌"
        cooldown = f" (cooldown: {info['cooldown_remaining']}s)" if info["cooldown_remaining"] > 0 else ""
        lines.append(f"{status_emoji} **{name}**: {'Enabled' if info['enabled'] else 'Disabled'} | Model: {info['default_model']}{cooldown}")
    lines.append("\nProviders are attempted in order until one succeeds. This is configuration/cooldown status, not a live health check.")
    await update.effective_message.reply_text("\n".join(lines), parse_mode="Markdown")
