from __future__ import annotations
import os, re
from dataclasses import dataclass
from pathlib import Path
from typing import Any
import yaml
from dotenv import load_dotenv

@dataclass
class Settings:
    token: str
    db_path: str
    persona_file: str
    rules_files: list[str]
    default_lang: str
    log_level: str
    log_message_content: bool
    enable_proactive: bool
    quiet_hours_start: int
    quiet_hours_end: int
    proactive_min_interval_minutes: int
    proactive_max_interval_minutes: int
    max_messages_per_minute: int
    single_user_mode: bool
    owner_id: int | None
    owner_username: str
    owner_code: str
    adult_mode_enabled: bool

def _bool(name: str, default: bool) -> bool:
    raw = os.getenv(name, str(default)).strip().lower()
    if raw not in {"true","false","1","0","yes","no"}:
        raise ValueError(f"{name} must be true/false")
    return raw in {"true","1","yes"}

def _int(name: str, default: int, minimum: int, maximum: int) -> int:
    try: value = int(os.getenv(name, str(default)))
    except ValueError as exc: raise ValueError(f"{name} must be an integer") from exc
    if not minimum <= value <= maximum:
        raise ValueError(f"{name} must be between {minimum} and {maximum}")
    return value

def load_settings(env_file: str = ".env") -> Settings:
    load_dotenv(env_file)
    token = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
    if not token or not re.fullmatch(r"\d{5,}:[A-Za-z0-9_-]{20,}", token):
        raise ValueError("TELEGRAM_BOT_TOKEN is missing or malformed. Copy the token from @BotFather into .env.")
    owner_raw = os.getenv("OWNER_ID", "").strip()
    try: owner_id = int(owner_raw) if owner_raw else None
    except ValueError as exc: raise ValueError("OWNER_ID must be a numeric Telegram user ID") from exc
    minimum = _int("PROACTIVE_MIN_INTERVAL_MINUTES",180,1,10080)
    maximum = _int("PROACTIVE_MAX_INTERVAL_MINUTES",480,1,10080)
    if maximum < minimum: raise ValueError("PROACTIVE_MAX_INTERVAL_MINUTES must be >= PROACTIVE_MIN_INTERVAL_MINUTES")
    # OWNER_ID identifies the one true administrator. Other users may chat as
    # Friends, and a valid shared pass unlocks BF-style companion replies.
    # SINGLE_USER_MODE is retained for compatibility with older .env files but
    # no longer blocks friend-mode conversations.
    single_user_mode = _bool("SINGLE_USER_MODE", False)
    if owner_id is None:
        raise ValueError("OWNER_ID is required so Aiko can identify the original owner. Set it to your numeric Telegram user ID.")
    owner_code = os.getenv("OWNER_CODE", "bubuiloveyou").strip()
    if len(owner_code) < 4:
        raise ValueError("OWNER_CODE must be at least 4 characters")
    rules_files = [f.strip() for f in os.getenv("RULES_FILES","config/rules.yaml").split(";") if f.strip()]
    for rf in rules_files:
        if not Path(rf).is_file():
            raise ValueError(f"Configured rules file not found: {rf}")
    return Settings(
        token=token, db_path=os.getenv("DB_PATH","data/aiko.db"),
        persona_file=os.getenv("PERSONA_FILE","config/persona.yaml"),
        rules_files=rules_files,
        default_lang=os.getenv("DEFAULT_LANG","hinglish"),
        log_level=os.getenv("LOG_LEVEL","INFO").upper(),
        log_message_content=_bool("LOG_MESSAGE_CONTENT",False),
        enable_proactive=_bool("ENABLE_PROACTIVE",True),
        quiet_hours_start=_int("QUIET_HOURS_START",23,0,23),
        quiet_hours_end=_int("QUIET_HOURS_END",8,0,23),
        proactive_min_interval_minutes=minimum, proactive_max_interval_minutes=maximum,
        max_messages_per_minute=_int("MAX_MESSAGES_PER_MINUTE",12,1,120),
        single_user_mode=single_user_mode, owner_id=owner_id,
        owner_username=os.getenv("OWNER_USERNAME","").strip(),
        owner_code=owner_code,
        adult_mode_enabled=_bool("ADULT_MODE_ENABLED",False))

def load_yaml(path: str) -> dict[str, Any]:
    p = Path(path)
    if not p.is_file(): raise ValueError(f"Configuration file not found: {path}")
    try: data = yaml.safe_load(p.read_text(encoding="utf-8"))
    except yaml.YAMLError as exc: raise ValueError(f"Invalid YAML in {path}: {exc}") from exc
    if not isinstance(data, dict): raise ValueError(f"{path} must contain a YAML mapping")
    return data

def validate_persona(persona: dict[str, Any]) -> None:
    required = ["name","age","location","occupation","pronouns","timezone","speech_style","personality_traits"]
    missing = [key for key in required if key not in persona]
    if missing: raise ValueError("Persona missing required fields: " + ", ".join(missing))
    style = persona["speech_style"]
    if not isinstance(style, dict) or not isinstance(style.get("max_message_length"), int):
        raise ValueError("persona speech_style.max_message_length must be an integer")
