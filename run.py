#!/usr/bin/env python3
"""
Aiko Bot v28+ - Unified Entry Point
Supports: Telegram polling, Webhook (for 24/7 hosting), Health checks, Terminal mode
"""
from __future__ import annotations

import asyncio
import logging
import os
import sys
from aiko.bot import build_application, load_settings

# Optional web framework for health checks / webhooks
try:
    from aiohttp import web
    HAS_AIOHTTP = True
except ImportError:
    HAS_AIOHTTP = False
    web = None  # type: ignore

_LOG = logging.getLogger(__name__)


def _resolve_public_url() -> str | None:
    """Resolve the public webhook URL from platform-supported env vars."""
    for name in ("WEBHOOK_URL", "RENDER_EXTERNAL_URL", "RAILWAY_STATIC_URL"):
        url = os.getenv(name)
        if url:
            return url.rstrip("/")
    fly_app = os.getenv("FLY_APP_NAME")
    if fly_app:
        return f"https://{fly_app}.fly.dev"
    return None


async def health_check(request: "web.Request") -> "web.Response":
    """Readiness endpoint; do not report healthy before services initialize."""
    web_app = request.app
    tg_app = web_app.get("telegram_app")
    db = tg_app.bot_data.get("db") if tg_app is not None else None
    db_ready = bool(db is not None and getattr(db, "conn", None) is not None)
    mode = os.getenv("BOT_MODE", "polling").lower()
    webhook_ready = mode != "webhook" or bool(web_app.get("webhook_configured", False))
    ready = bool(tg_app is not None and tg_app.running and db_ready and webhook_ready)
    payload = {
        "status": "healthy" if ready else "starting",
        "bot": "AIKO v29",
        "mode": mode,
        "database_ready": db_ready,
        "webhook_configured": bool(web_app.get("webhook_configured", False)),
    }
    return web.json_response(payload, status=200 if ready else 503)


async def webhook_handler(request: "web.Request") -> "web.Response":
    """Handle Telegram webhook updates with secret-token verification."""
    tg_app = request.app["telegram_app"]
    secret_token = os.getenv("WEBHOOK_SECRET_TOKEN")
    if secret_token:
        provided = request.headers.get("X-Telegram-Bot-Api-Secret-Token", "")
        if provided != secret_token:
            _LOG.warning("Rejected webhook request with invalid secret token")
            return web.Response(status=403)
    try:
        data = await request.json()
        update_cls = request.app["update_class"]
        update = update_cls.de_json(data, tg_app.bot)
        await tg_app.process_update(update)
        return web.Response(status=200)
    except Exception as e:
        _LOG.error("Webhook request failed (%s)", type(e).__name__)
        return web.Response(status=500)


def setup_webhook_routes(app) -> "web.Application":
    """Setup aiohttp app with webhook + health endpoints."""
    if not HAS_AIOHTTP:
        raise RuntimeError("aiohttp required for webhook mode. Install: pip install aiohttp")

    web_app = web.Application()
    web_app["telegram_app"] = app
    web_app["update_class"] = app.update_class
    web_app["webhook_configured"] = False
    web_app.router.add_get("/health", health_check)
    web_app.router.add_post("/webhook", webhook_handler)
    web_app.router.add_get("/", health_check)  # Root also works for checks
    return web_app


def run_polling_mode(app):
    """Run in polling mode (default, works everywhere).

    Application.run_polling() is synchronous and owns the event loop;
    it must not be awaited inside an existing asyncio loop.
    """
    _LOG.info("Starting in polling mode...")
    app.run_polling(
        allowed_updates=app.bot_data["settings"].update_types if hasattr(app.bot_data["settings"], "update_types") else None,
        drop_pending_updates=False,
    )


async def run_webhook_mode(app, settings):
    """Run webhook mode with the same initialization and shutdown callbacks as polling."""
    if not HAS_AIOHTTP:
        raise RuntimeError("aiohttp is required for webhook mode. Install project requirements or use BOT_MODE=polling.")

    public_url = _resolve_public_url()
    if not public_url:
        raise RuntimeError(
            "WEBHOOK_URL (or RENDER_EXTERNAL_URL / RAILWAY_STATIC_URL / FLY_APP_NAME) "
            "is required in webhook mode"
        )

    secret_token = os.getenv("WEBHOOK_SECRET_TOKEN", "").strip()
    if not secret_token or len(secret_token) < 16 or len(secret_token) > 256 or not all(c.isalnum() or c in "_-" for c in secret_token):
        raise RuntimeError("Set WEBHOOK_SECRET_TOKEN to a random 16–256 character value using only letters, numbers, '_' or '-'.")

    _LOG.info("Starting in webhook mode...")
    runner = None
    initialized = False
    started = False
    try:
        await app.initialize()
        initialized = True
        # Application.run_polling normally invokes post_init automatically; the
        # custom aiohttp lifecycle must call it explicitly.
        if app.post_init:
            await app.post_init(app)
        await app.start()
        started = True

        web_app = setup_webhook_routes(app)
        webhook_path = "/webhook"
        await app.bot.set_webhook(f"{public_url}{webhook_path}", secret_token=secret_token)
        web_app["webhook_configured"] = True
        _LOG.info("Webhook configured on %s%s", public_url, webhook_path)

        port = int(os.getenv("PORT", "8080"))
        host = os.getenv("HOST", "0.0.0.0")
        runner = web.AppRunner(web_app)
        await runner.setup()
        site = web.TCPSite(runner, host, port)
        await site.start()
        _LOG.info("Webhook server listening on %s:%s", host, port)
        await asyncio.Event().wait()
    finally:
        if runner is not None:
            await runner.cleanup()
        if started:
            await app.stop()
        if initialized:
            await app.shutdown()
        # The framework does this for run_polling; custom lifecycle must too.
        if app.post_shutdown:
            await app.post_shutdown(app)


def run_terminal_mode():
    """Run in terminal/offline mode (no Telegram needed)."""
    _LOG.info("Starting in terminal mode...")
    from aiko.offline import main as offline_main
    offline_main()


def main():
    # Determine mode from environment BEFORE loading Telegram-only settings,
    # so terminal/offline mode does not require a Telegram token or owner ID.
    mode = os.getenv("BOT_MODE", "polling").lower()

    if mode in ("terminal", "offline"):
        run_terminal_mode()
        return

    # Telegram modes require settings (token etc.)
    try:
        settings = load_settings()
    except ValueError as exc:
        raise SystemExit(f"Configuration error: {exc}") from exc

    # Configure logging
    log_level = getattr(logging, settings.log_level.upper(), logging.INFO)
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    _LOG.info("Starting Aiko v28+; mode=%s; message content logging=%s", mode, settings.log_message_content)

    # Build Telegram application. post_init/post_shutdown are wired in
    # build_application(); the DB is opened exactly once inside post_init.
    app = build_application(settings)

    try:
        if mode == "webhook" and HAS_AIOHTTP:
            asyncio.run(run_webhook_mode(app, settings))
        else:
            if mode == "webhook" and not HAS_AIOHTTP:
                _LOG.warning("aiohttp is unavailable; using polling mode instead")
            # run_polling() is synchronous and owns the event loop.
            run_polling_mode(app)
    except KeyboardInterrupt:
        _LOG.info("Shutdown requested")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        _LOG.info("Shutdown requested")
    except Exception as e:
        _LOG.exception("Fatal error: %s", e)
        sys.exit(1)