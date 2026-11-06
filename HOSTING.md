# Aiko Bot v28+ - Free 24/7 Hosting Configurations
# Choose ONE platform and follow its setup guide below.

# ═══════════════════════════════════════════════════════════════════════════
# OPTION 1: RENDER (Recommended - Easiest Free 24/7)
# ═══════════════════════════════════════════════════════════════════════════
# 1. Push this repo to GitHub
# 2. Go to https://render.com → New → Web Service → Connect GitHub repo
# 3. Settings:
#    - Build Command: pip install -r requirements.txt
#    - Start Command: python run.py
#    - Environment: Python 3.11+
# 4. Add Environment Variables from .env.example (including OWNER_ID, OWNER_CODE, WEBHOOK_SECRET_TOKEN and optionally AI provider keys)
# 5. For webhook mode, also set WEBHOOK_SECRET_TOKEN to a random 32+ character secret and BOT_MODE=webhook. The /webhook route validates Telegram's secret header; the bot token is not placed in the URL.
# 6. Render gives you: https://your-app.onrender.com (sleeps after 15min inactive)
#    → To prevent sleep: Use cron-job.org or uptimerobot.com to ping /health every 10min

# render.yaml (auto-detected by Render)
# ────────────────────────────────────────────────────────────────────────────
# services:
#   - type: web
#     name: aiko-bot
#     env: python
#     plan: free
#     buildCommand: "pip install -r requirements.txt"
#     startCommand: "python run.py"
#     envVars:
#       - key: PYTHON_VERSION
#         value: 3.11.9
#       # Add your keys in Render dashboard, not here!
#     healthCheckPath: /health


# ═══════════════════════════════════════════════════════════════════════════
# OPTION 2: RAILWAY (Good Free Tier, No Sleep)
# ═══════════════════════════════════════════════════════════════════════════
# 1. Go to https://railway.app → New Project → Deploy from GitHub
# 2. Railway auto-detects Python, uses requirements.txt
# 3. Add env vars in Variables tab, including TELEGRAM_BOT_TOKEN, OWNER_ID, OWNER_CODE, WEBHOOK_SECRET_TOKEN and optional AI keys
# 4. Free tier: $5 credit/month (enough for 24/7 small bot)
# 5. No auto-sleep on free tier!

# railway.json
# ────────────────────────────────────────────────────────────────────────────
# {
#   "$schema": "https://railway.app/railway.schema.json",
#   "build": { "builder": "NIXPACKS" },
#   "deploy": {
#     "startCommand": "python run.py",
#     "healthcheckPath": "/health",
#     "healthcheckTimeout": 30,
#     "restartPolicyType": "ON_FAILURE"
#   }
# }


# ═══════════════════════════════════════════════════════════════════════════
# OPTION 3: FLY.IO (Free allowance, always-on)
# ═══════════════════════════════════════════════════════════════════════════
# 1. Install flyctl: https://fly.io/docs/hands-on/install-flyctl/
# 2. fly launch --name aiko-bot --region bom (or your region)
# 3. fly secrets set TELEGRAM_BOT_TOKEN=... OWNER_ID=... OWNER_CODE=... WEBHOOK_SECRET_TOKEN=... GROQ_API_KEY=... etc
# 4. fly deploy
# 5. Free: 3 shared-cpu-1x VMs, 160GB bandwidth/month

# fly.toml
# ────────────────────────────────────────────────────────────────────────────
# app = "aiko-bot"
# primary_region = "bom"
# 
# [build]
#   builder = "paketobuildpacks/builder:base"
# 
# [env]
#   PYTHON_VERSION = "3.11"
# 
# [http_service]
#   internal_port = 8080
#   force_https = true
#   auto_stop_machines = false
#   auto_start_machines = true
#   min_machines_running = 1
# 
# [[vm]]
#   memory = "256mb"
#   cpu_kind = "shared"
#   cpus = 1


# ═══════════════════════════════════════════════════════════════════════════
# OPTION 4: GOOGLE CLOUD RUN (Free tier: 2M requests/month)
# ═══════════════════════════════════════════════════════════════════════════
# 1. gcloud auth login && gcloud config set project YOUR_PROJECT
# 2. gcloud run deploy aiko-bot --source . --region asia-south1 --allow-unauthenticated
# 3. Set env vars in Cloud Console → Cloud Run → your-service → Variables
# 4. Free tier includes CPU only during requests (cold starts ~2s)

# Dockerfile.cloudrun
# ────────────────────────────────────────────────────────────────────────────
# FROM python:3.11-slim
# WORKDIR /app
# COPY requirements.txt .
# RUN pip install --no-cache-dir -r requirements.txt
# COPY . .
# ENV PORT=8080
# CMD ["python", "run.py"]


# ═══════════════════════════════════════════════════════════════════════════
# OPTION 5: Koyeb (Free tier, no sleep)
# ═══════════════════════════════════════════════════════════════════════════
# 1. Go to https://koyeb.com → Create App → GitHub
# 2. Build: pip install -r requirements.txt
# 3. Run: python run.py
# 4. Free: 1 nano instance (512MB RAM), no sleep


# ═══════════════════════════════════════════════════════════════════════════
# OPTION 6: REPLIT (Always-on with paid, or use UptimeRobot)
# ═══════════════════════════════════════════════════════════════════════════
# 1. Import from GitHub on replit.com
# 2. Add Secrets (Environment Variables) in Replit Secrets tab
# 3. Run: python run.py
# 4. Free tier sleeps; use UptimeRobot to ping replit URL every 5min

# .replit
# ────────────────────────────────────────────────────────────────────────────
# modules = ["python-3.11"]
# run = "python run.py"
# entrypoint = "main.py"
# hidden = [".env", "data", "*.db", "*.db-*", "__pycache__", "*.pyc"]


# ═══════════════════════════════════════════════════════════════════════════
# KEEP-ALIVE SETUP (for platforms that sleep: Render, Replit, etc.)
# ═══════════════════════════════════════════════════════════════════════════
# 1. Deploy and get your public URL (e.g., https://aiko-bot.onrender.com)
# 2. Go to https://uptimerobot.com (free) or https://cron-job.org (free)
# 3. Add monitor:
#    - URL: https://your-app.onrender.com/health
#    - Interval: 5-10 minutes
#    - Method: GET
# 4. This prevents the free tier from spinning down

# The /health endpoint is added in run.py (see below)