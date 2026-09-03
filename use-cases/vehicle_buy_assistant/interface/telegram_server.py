# interface/telegram_server.py
"""
Real Telegram Webhook Server — Vehicle Buy Assistant
Uses FastAPI + uvicorn directly. Calls pydantic-ai Ollama agent directly
in the webhook handler (no agentkernel agent registry needed).

Run:
    python -X utf8 interface/telegram_server.py

Expose:
    cloudflared tunnel --url http://localhost:8000

Register webhook:
    curl "https://api.telegram.org/bot<TOKEN>/setWebhook
          ?url=<CLOUDFLARE_URL>/telegram/webhook"
"""

import os
import sys

# ── Force UTF-8 FIRST (before any print or import that might print) ──────────
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

import json
import httpx
from fastapi import FastAPI, Request, Response
import uvicorn
from dotenv import load_dotenv

# ── Load .env (project root first, then interface/) ───────────────────────────
_env_path = os.path.join(os.path.dirname(__file__), '..', '.env')
if os.path.exists(_env_path):
    load_dotenv(_env_path, override=True)
    print(f"[Config] Loaded .env from project root")
else:
    _env_path2 = os.path.join(os.path.dirname(__file__), '.env')
    if os.path.exists(_env_path2):
        load_dotenv(_env_path2, override=True)
        print(f"[Config] Loaded .env from interface/")
    else:
        print("[Config] No .env file found -- using system environment variables")

# ── Validate token ────────────────────────────────────────────────────────────
_token = os.environ.get("AK_TELEGRAM__BOT_TOKEN", "")
if not _token or _token == "your_bot_token_here":
    print("\n[Server] ERROR: Bot token not set.")
    print("[Server]   Edit .env and set: AK_TELEGRAM__BOT_TOKEN=your_token\n")
    sys.exit(1)
print(f"[Config] Bot token: {_token[:10]}...")

# ── Path setup (so tools/ is importable) ─────────────────────────────────────
BASE_DIR = os.path.join(os.path.dirname(__file__), '..')
sys.path.insert(0, BASE_DIR)

# ── Ollama agent (pydantic-ai 2.36 correct API) ───────────────────────────────
# OllamaModel and OpenAIChatModel both require OllamaProvider(base_url=...)
# in pydantic-ai 2.36. The bare string 'ollama' default raises UserError.
from pydantic_ai import Agent as PydanticAgent
from pydantic_ai.providers.ollama import OllamaProvider
from pydantic_ai.models.ollama import OllamaModel

_ollama_url = os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434")
print(f"[Ollama] Connecting to {_ollama_url} ...")

_model = OllamaModel(
    "llama3.2:latest",                              # exact name from `ollama list`
    provider=OllamaProvider(base_url=_ollama_url),  # required in pydantic-ai 2.36
)

vehicle_agent = PydanticAgent(
    _model,
    system_prompt="""You are a helpful car buying assistant for Sri Lankan users.
Help users find their perfect vehicle by asking about:
1. Budget (in Sri Lankan Rupees, LKR)
2. Vehicle type (SUV, Sedan, Truck, Electric, Hybrid, Hatchback)
3. Primary use (commuting, family, off-road, business)
4. Must-have features (safety, fuel efficiency, tech, comfort)

Be conversational, friendly, and concise. Always show prices in LKR.
Recommend visiting riyasewana.com to contact sellers directly."""
)
print("[Ollama] vehicle_agent ready (llama3.2 @ localhost:11434)")

# ── FastAPI app ───────────────────────────────────────────────────────────────
app = FastAPI(title="Vehicle Buy Assistant Telegram Bot")

@app.get("/")
@app.get("/health")
async def health():
    return {"status": "ok", "message": "Vehicle Buy Assistant is running", "model": "ollama:llama3.2"}

@app.post("/telegram/webhook")
async def webhook(request: Request):
    chat_id = None  # ensure always defined for error handler
    try:
        update = await request.json()
        print(f"[Webhook] Update {update.get('update_id', 'unknown')}")

        message = update.get('message', {})
        if not message:
            return Response(content="OK", status_code=200)

        chat_id = message.get('chat', {}).get('id')
        text = (message.get('text') or '').strip()

        if not chat_id or not text:
            return Response(content="OK", status_code=200)

        user_name = message.get('from', {}).get('first_name', 'there')
        print(f"[Webhook] chat={chat_id} user={user_name!r} text={text!r}")

        # /start command
        if text.lower() in ('/start', 'start'):
            await send_telegram_message(
                chat_id,
                f"Hello {user_name}! I'm your Vehicle Buy Assistant.\n\n"
                "Tell me your budget and what type of vehicle you're looking for "
                "and I'll find your perfect match from live Riyasewana.lk listings!"
            )
            return Response(content="OK", status_code=200)

        # /help command
        if text.lower() in ('/help', 'help'):
            await send_telegram_message(
                chat_id,
                "Just tell me:\n"
                "  - Budget (e.g. under Rs 5 million)\n"
                "  - Vehicle type (SUV, Sedan, Hybrid...)\n"
                "  - How you'll use it (family, commuting...)\n"
                "  - Any must-have features\n\n"
                "I'll search live Riyasewana listings and recommend the best match!"
            )
            return Response(content="OK", status_code=200)

        # Typing indicator (fire and forget)
        await send_telegram_action(chat_id, "typing")

        # Run the Ollama agent
        result = await vehicle_agent.run(text)
        response_text = str(result.data) if hasattr(result, 'data') else str(result)
        print(f"[Agent] Response ({len(response_text)} chars): {response_text[:80]}...")
        await send_telegram_message(chat_id, response_text)

    except Exception as e:
        print(f"[Webhook] Error: {type(e).__name__}: {e}")
        if chat_id:  # only reply if we know who to reply to
            await send_telegram_message(
                chat_id,
                f"Sorry, I had trouble processing that. Please try again.\n(Error: {str(e)[:120]})"
            )

    return Response(content="OK", status_code=200)


# ── Telegram Bot API helpers ──────────────────────────────────────────────────

async def send_telegram_message(chat_id: int, text: str):
    """Send a plain-text message to a Telegram chat."""
    token = os.environ.get("AK_TELEGRAM__BOT_TOKEN", "")
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    if len(text) > 4000:
        text = text[:3997] + "..."
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.post(url, json={
                "chat_id": chat_id,
                "text": text,
                # No parse_mode — plain text is safest (avoids HTML/Markdown errors)
            })
            if resp.status_code != 200:
                print(f"[Telegram] Send error {resp.status_code}: {resp.text[:200]}")
    except Exception as e:
        print(f"[Telegram] HTTP error: {e}")

async def send_telegram_action(chat_id: int, action: str = "typing"):
    """Send a chat action (non-critical — swallow all errors)."""
    token = os.environ.get("AK_TELEGRAM__BOT_TOKEN", "")
    url = f"https://api.telegram.org/bot{token}/sendChatAction"
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            await client.post(url, json={"chat_id": chat_id, "action": action})
    except Exception:
        pass


# ── Entry point ───────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print()
    print("=" * 60)
    print("  Vehicle Buy Assistant -- Telegram Bot")
    print("  AI  : pydantic-ai + Ollama (llama3.2)")
    print("  Data: live Riyasewana.lk listings")
    print("=" * 60)
    print("  Endpoints:")
    print("    GET  http://localhost:8000/health")
    print("    POST http://localhost:8000/telegram/webhook")
    print()
    print("  Expose publicly:")
    print("    cloudflared tunnel --url http://localhost:8000")
    print()
    print("  Register webhook:")
    print('    curl "https://api.telegram.org/bot<TOKEN>/setWebhook')
    print('          ?url=<CLOUDFLARE_URL>/telegram/webhook"')
    print("=" * 60)
    print("  Starting Uvicorn...")
    print()
    uvicorn.run(app, host="0.0.0.0", port=8000)