"""Diagnose Aiko's Groq configuration without revealing the API key or chat history.

Run from the project root with: python scripts/check_groq.py
This sends only the fixed test message 'Reply with OK only.' to the configured model.
"""
from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

try:
    from dotenv import load_dotenv
except ImportError:
    print("ERROR: python-dotenv is missing. Activate Aiko's venv and install requirements.txt first.")
    raise SystemExit(2)

ROOT = Path(__file__).resolve().parents[1]
ENV_FILE = ROOT / ".env"
load_dotenv(dotenv_path=ENV_FILE, override=False)
BASE = "https://api.groq.com/openai/v1"
USER_AGENT = "AikoBot/24 Groq API diagnostic (https://console.groq.com/docs/api-reference)"
KEY = os.getenv("GROQ_API_KEY", "").strip()
MODEL = os.getenv("GROQ_MODEL", "openai/gpt-oss-20b").strip() or "openai/gpt-oss-20b"
ENABLED = os.getenv("GROQ_ENABLED", "true").strip().lower() not in {"0", "false", "no", "off"}


def safe_text(value: object, limit: int = 500) -> str:
    value = str(value or "")
    if KEY:
        value = value.replace(KEY, "[API KEY REDACTED]")
    value = re.sub(r"(?i)bearer\s+\S+", "Bearer [REDACTED]", value)
    value = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]", " ", value)
    value = re.sub(r"\s+", " ", value).strip()
    return value[:limit]


def request(method: str, url: str, payload: dict | None = None, timeout: float = 20) -> tuple[int, object, str]:
    body = json.dumps(payload).encode("utf-8") if payload is not None else None
    headers = {"Authorization": f"Bearer {KEY}", "Accept": "application/json", "User-Agent": USER_AGENT}
    if body is not None:
        headers["Content-Type"] = "application/json"
    req = Request(url, data=body, headers=headers, method=method)
    try:
        with urlopen(req, timeout=timeout) as response:
            raw = response.read(100_000).decode("utf-8", errors="replace")
            try:
                parsed = json.loads(raw)
            except json.JSONDecodeError:
                parsed = safe_text(raw)
            return response.status, parsed, response.headers.get("Content-Type", "")
    except HTTPError as exc:
        try:
            raw = exc.read(10_000).decode("utf-8", errors="replace")
        except OSError:
            raw = ""
        try:
            parsed = json.loads(raw) if raw else {}
        except json.JSONDecodeError:
            parsed = safe_text(raw)
        return exc.code, parsed, exc.headers.get("Content-Type", "") if exc.headers else ""


def print_error(payload: object, content_type: str) -> None:
    if isinstance(payload, dict):
        err = payload.get("error", payload)
        if isinstance(err, dict):
            code = err.get("code") or err.get("error_code")
            kind = err.get("type")
            message = err.get("message") or err.get("detail")
            bits = []
            if code:
                bits.append("code=" + safe_text(code, 100))
            if kind:
                bits.append("type=" + safe_text(kind, 100))
            if message:
                bits.append("message=" + safe_text(message, 600))
            if bits:
                print("  Provider details: " + "; ".join(bits))
                return
        print("  Error response: " + safe_text(json.dumps(payload, ensure_ascii=False), 600))
    elif payload:
        print("  Response body: " + safe_text(payload, 500))
    else:
        print("  Provider returned no readable error body. Content-Type: " + safe_text(content_type, 100))


def main() -> int:
    print("Aiko Groq diagnostic (does not print your key or private chat history)")
    print(f"Project folder: {ROOT}")
    print(f".env file exists: {'yes' if ENV_FILE.is_file() else 'NO'}")
    print(f"GROQ_ENABLED: {str(ENABLED).lower()}")
    print(f"GROQ_API_KEY present: {'yes' if bool(KEY) else 'NO'}")
    print(f"Configured model: {safe_text(MODEL, 120)}")

    if not KEY:
        print("\nRESULT: No GROQ_API_KEY was found in this process or the project's .env file.")
        print("Add GROQ_API_KEY=... to .env, save it, then rerun this script.")
        return 2
    if not ENABLED:
        print("\nRESULT: Groq is disabled. Set GROQ_ENABLED=true in .env to test it.")
        return 2

    print("\n1) Checking Groq authentication/model endpoint...")
    status, body, content_type = request("GET", BASE + "/models")
    print(f"   GET /models -> HTTP {status}")
    if status != 200:
        print_error(body, content_type)
        if isinstance(body, dict) and (str(body.get("code", "")) == "1010" or "browser's signature" in str(body.get("message", "")).lower() or "browser signature" in str(body.get("message", "")).lower()):
            print("\nRESULT: Cloudflare blocked this API client's signature before Groq authentication/model permissions could be checked. This is not evidence of an invalid API key. This version now sends an explicit Aiko API-client User-Agent; rerun this diagnostic. If 1010 persists, try without VPN/proxy or on another network and contact Groq support with the Cloudflare error details.")
        else:
            print("\nRESULT: The models endpoint did not return HTTP 200. Use the sanitized provider details above to identify the next step.")
        return 1
    data = body.get("data", []) if isinstance(body, dict) else []
    ids = [entry.get("id") for entry in data if isinstance(entry, dict) and isinstance(entry.get("id"), str)]
    print(f"   Model list received: {len(ids)} model ID(s)")
    print(f"   Configured model listed: {'yes' if MODEL in ids else 'no'}")

    print("\n2) Sending a tiny test request to the configured model...")
    payload = {
        "model": MODEL,
        "messages": [{"role": "user", "content": "Reply with OK only."}],
        "temperature": 0,
        "max_completion_tokens": 24,
        "reasoning_effort": "low",
        "reasoning_format": "hidden",
    }
    status, body, content_type = request("POST", BASE + "/chat/completions", payload)
    print(f"   POST /chat/completions -> HTTP {status}")
    if status == 200:
        print("\nRESULT: Groq works with this key and model. If Aiko still logs 403, it is likely running from a different project/.env/configuration than this diagnostic.")
        return 0

    print_error(body, content_type)
    if status == 403:
        cloudflare_1010 = isinstance(body, dict) and (str(body.get("code", "")) == "1010" or "browser's signature" in str(body.get("message", "")).lower() or "browser signature" in str(body.get("message", "")).lower())
        if cloudflare_1010:
            print("\nRESULT: Cloudflare blocked the client signature before a normal Groq API error could be returned. This is not evidence of a bad key/model. If it persists with the explicit User-Agent, test without VPN/proxy or on another network, then contact Groq support.")
        else:
            print("\nRESULT: Groq or an API gateway returned HTTP 403. If details say model_permission_blocked_project/org, allow the model in the matching Groq Limits page; otherwise follow the exact provider reason.")
    elif status == 401:
        print("\nRESULT: Groq did not accept the key. Generate a fresh key in Groq Console and replace GROQ_API_KEY in this project's .env.")
    elif status == 400:
        print("\nRESULT: The request was rejected as invalid. The provider detail above should identify the unsupported model or parameter.")
    else:
        print("\nRESULT: Check the provider detail above and retry after correcting the reported issue.")
    return 1


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (URLError, TimeoutError, OSError) as exc:
        print(f"\nNETWORK ERROR: {type(exc).__name__}. Check internet access/firewall, then retry.")
        raise SystemExit(3)
