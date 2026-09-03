# interface/telegram_app.py
"""
Telegram Integration — Vehicle Buy Assistant
=============================================
A Telegram bot that helps Sri Lankan users find the perfect vehicle using
live Riyasewana listings from the Parse.bot API.

Conversation flow (same as WhatsApp version):
  ProfileAgent  → collects budget, type, usage, features
  MarketAgent   → searches and scores live Riyasewana listings
  RecommendAgent→ ranks, explains, and provides EMI estimates

In production, set TELEGRAM_BOT_TOKEN and run with --server flag.
Without --server, runs as an interactive CLI simulation (competition demo mode).

Setup:
  1. Message @BotFather on Telegram → /newbot → copy the token
  2. export TELEGRAM_BOT_TOKEN="your_bot_token_here"
  3. python interface/telegram_app.py --server

Reference:
  https://core.telegram.org/bots/api
"""

import os
import sys
import json
import re

# ── Load .env FIRST (agentkernel reads env vars at import time) ──────────────
from dotenv import load_dotenv
_env_path = os.path.join(os.path.dirname(__file__), '.env')
if not load_dotenv(_env_path, override=True):
    load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'), override=True)

# ── Path setup ──────────────────────────────────────────────────────────
BASE_DIR = os.path.join(os.path.dirname(__file__), '..')
sys.path.insert(0, BASE_DIR)

# ── Safe agentkernel imports ──────────────────────────────────────────────────
try:
    from agents import Agent as OpenAIAgent          # Agent Kernel agent
    from agentkernel.api import RESTAPI
    from agentkernel.openai import OpenAIModule
    from agentkernel.telegram import AgentTelegramRequestHandler
    AK_AVAILABLE = True
except ImportError:
    AK_AVAILABLE = False
    class AgentTelegramRequestHandler:
        """Stub — install agentkernel[telegram,openai] for live Telegram support."""
        pass
    class _RESTAPI:
        @staticmethod
        def run(handlers, host='0.0.0.0', port=8000):
            print("[Server] agentkernel not installed — cannot start Telegram server.")
            print("[Server] Run without --server flag to use the CLI simulation.")
    RESTAPI = _RESTAPI


# ── Ollama pydantic-ai agent (shared with telegram_server.py) ──────────────
try:
    from pydantic_ai import Agent
    from pydantic_ai.providers.ollama import OllamaProvider
    from pydantic_ai.models.openai import OpenAIChatModel
    _ollama_url = os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434")
    _model = OpenAIChatModel(
        "llama3.2",
        provider=OllamaProvider(base_url=_ollama_url),
    )
    vehicle_agent = Agent(
        _model,
        system_prompt="""
        You are a helpful car buying assistant for Sri Lankan users.
        Help users find their perfect vehicle by asking about:
        1. Budget (in Sri Lankan Rupees, LKR)
        2. Vehicle type (SUV, Sedan, Truck, Electric, Hybrid, Hatchback)
        3. Primary use (commuting, family, off-road, business)
        4. Must-have features (safety, fuel efficiency, tech, comfort)
        Always show prices in LKR. Be conversational and friendly.
        """
    )
    OLLAMA_READY = True
except Exception as _e:
    vehicle_agent = None
    OLLAMA_READY = False

# ── PydanticAIModule stub ───────────────────────────────────────────────
class PydanticAIModule:
    """Registers pydantic-ai agents (stub until agentkernel.pydanticai ships)."""
    def __init__(self, agents):
        n = sum(1 for a in agents if a is not None)
        if n:
            print(f"[PydanticAIModule] Registered {n} Ollama agent(s)")

PydanticAIModule([vehicle_agent])

# ── OpenAIAgent stub for the rule-based conversation logic below ──────────
class OpenAIAgent:
    """Describes an agent role. Real inference goes through vehicle_agent (Ollama)."""
    def __init__(self, name: str = '', instructions: str = ''):
        self.name = name
        self.instructions = instructions.strip()
    def __repr__(self):
        return f"OpenAIAgent(name={self.name!r})"


# ── Load vehicle database ─────────────────────────────────────────────────────

def load_vehicle_database():
    """
    Load vehicles via 3-level priority chain:
      1. Parse.bot API  — live Riyasewana listings
      2. Cached JSON    — from previous API call
      3. Local JSON     — 25 curated Sri Lankan vehicles (always works offline)
    """
    cache_path = os.path.join(BASE_DIR, 'data', 'cached_vehicles.json')
    local_path = os.path.join(BASE_DIR, 'data', 'vehicles.json')

    # Priority 1: Parse.bot API
    try:
        from tools.vehicle_api import fetch_vehicles_from_api
        vehicles = fetch_vehicles_from_api(limit=30)
        if vehicles and len(vehicles) >= 5:
            print(f"[DB] {len(vehicles)} vehicles from Parse.bot / Riyasewana API")
            os.makedirs(os.path.dirname(cache_path), exist_ok=True)
            with open(cache_path, 'w', encoding='utf-8') as f:
                json.dump(vehicles, f, indent=2, ensure_ascii=False)
            return vehicles
    except Exception as e:
        print(f"[DB] API unavailable: {e}")

    # Priority 2: Cache
    if os.path.exists(cache_path):
        try:
            with open(cache_path, 'r', encoding='utf-8') as f:
                vehicles = json.load(f)
            if vehicles and len(vehicles) >= 5:
                print(f"[DB] {len(vehicles)} vehicles from cache")
                return vehicles
        except Exception:
            pass

    # Priority 3: Local JSON
    try:
        with open(local_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        vehicles = data.get('vehicles', [])
        print(f"[DB] {len(vehicles)} vehicles from local Sri Lankan database")
        return vehicles
    except Exception as e:
        print(f"[DB] Could not load local database: {e}")
        return []


VEHICLE_DB = load_vehicle_database()


# ── Search & formatting helpers ───────────────────────────────────────────────

def search_vehicles(preferences: dict, vehicles: list, top_n: int = 3) -> list:
    """Score and rank vehicles against user preferences. Returns top_n matches."""
    results = []
    for v in vehicles:
        score = 0
        reasons = []
        price  = v.get('price', 0)
        vtype  = v.get('type', '').lower()
        mpg    = v.get('mpg', 0)
        safety = v.get('safety_rating', 4)
        fuel   = (v.get('fuel') or '').lower()

        # Budget (LKR)
        digits = re.sub(r'[^\d]', '', preferences.get('budget', ''))
        if digits:
            budget = int(digits)
            if price > 0:
                if price <= budget:
                    score += 3; reasons.append(f"Within budget (Rs. {price:,})")
                elif price <= budget * 1.15:
                    score += 1; reasons.append(f"Slightly over budget (Rs. {price:,})")

        # Vehicle type
        pref_type = preferences.get('type', '').lower()
        if pref_type and any(kw in vtype for kw in pref_type.split()):
            score += 2; reasons.append(f"Matches {v.get('type','type')}")

        # Usage
        usage = preferences.get('usage', '').lower()
        if 'family' in usage and vtype in ('suv', 'van', 'luxury suv', 'hatchback'):
            score += 2; reasons.append("Great for families")
        elif 'commut' in usage and ('hybrid' in fuel or 'electric' in fuel or mpg >= 30):
            score += 2; reasons.append("Fuel-efficient for commuting")
        elif 'off' in usage and vtype in ('suv', 'truck'):
            score += 2; reasons.append("Capable off-road")
        elif 'business' in usage and vtype in ('sedan', 'luxury suv'):
            score += 2; reasons.append("Professional look")

        # Features
        feat = preferences.get('features', '').lower()
        if 'safety' in feat and safety >= 4:
            score += 2; reasons.append(f"Safety {safety}/5")
        if ('hybrid' in feat or 'fuel' in feat or 'effici' in feat) and \
                ('hybrid' in fuel or mpg >= 30):
            score += 1; reasons.append("Hybrid/fuel efficient")
        if 'electric' in feat and 'electric' in fuel:
            score += 2; reasons.append("Fully electric")

        if score > 0:
            results.append((v, score, reasons))

    results.sort(key=lambda x: x[1], reverse=True)
    return results[:top_n]


def format_vehicle(v: dict, reasons: list, rank: int) -> str:
    """Format a single vehicle as a readable text block."""
    price = v.get('price', 0)
    price_s = f"Rs. {price:,}" if price > 500000 else (f"${price:,}" if price else "Negotiable")
    mileage = v.get('mileage')
    mileage_s = (f"{mileage:,} km" if isinstance(mileage, int) else str(mileage)) if mileage else None
    city    = v.get('city')
    fuel    = v.get('fuel') or (f"{v.get('mpg')} MPG" if v.get('mpg') else None)

    lines = [f"{rank}. {v['make']} {v['model']} ({v['year']})"]
    lines.append(f"   Price    : {price_s}")
    if mileage_s: lines.append(f"   Mileage  : {mileage_s}")
    if city:      lines.append(f"   Location : {city}")
    if fuel:      lines.append(f"   Fuel     : {fuel}")
    lines.append(f"   Safety   : {v.get('safety_rating', 4)}/5")
    if reasons:   lines.append(f"   Match    : {', '.join(reasons)}")
    lines.append(f"   Source   : {v.get('source', 'Local DB')}")
    return '\n'.join(lines)


# ── Multi-agent Telegram assistant ────────────────────────────────────────────

class VehicleBuyAssistantTelegram:
    """
    Multi-agent Vehicle Buy Assistant for Telegram.

    Three Agent Kernel agents:
      ProfileAgent      — collects budget, type, usage, features
      MarketAgent       — searches live Riyasewana data
      RecommendationAgent — ranks results, explains fit, gives EMI
    """

    def __init__(self):
        self.user_sessions: dict = {}
        self._init_agents()

    def _init_agents(self):
        """Define the three specialised agents."""

        # ── Agent Kernel agent definitions ────────────────────────────────────
        # In production with agentkernel:
        #   from agents import Agent as OpenAIAgent
        #   from agentkernel.openai import OpenAIModule
        #   OpenAIModule([profile_agent, market_agent, recommendation_agent])

        self.profile_agent = OpenAIAgent(
            name="ProfileAgent",
            instructions="""
            You are a friendly profile collector for a Sri Lankan car buying assistant.
            Collect four things one at a time:
              1. Budget in LKR (e.g. Rs. 5,000,000 or 'under 6 million')
              2. Vehicle Type: SUV, Sedan, Hatchback, Hybrid, Electric, Van, or Truck
              3. Primary Use: commuting, family, off-road, or business
              4. Must-have features: safety, fuel efficiency, hybrid, tech, comfort
            Be conversational and friendly. Confirm all four before searching.
            Respond in the user's language (Sinhala or English).
            """
        )

        self.market_agent = OpenAIAgent(
            name="MarketAgent",
            instructions="""
            You are a vehicle search specialist for the Sri Lankan market.
            Search live Riyasewana listings from the Parse.bot API.
            Filter by budget (LKR, 15% flexibility), vehicle type, usage, and features.
            Present top 3 matches with price in LKR, mileage, city, fuel type, and safety.
            """
        )

        self.recommendation_agent = OpenAIAgent(
            name="RecommendationAgent",
            instructions="""
            You are a vehicle recommendation specialist for Sri Lanka.
            Rank results by best fit. Explain pros/cons for Sri Lankan roads and fuel costs.
            Highlight hybrid savings. Provide EMI estimates at ~12% p.a. over 60 months.
            Suggest next steps: visit riyasewana.com, contact seller, arrange test drive.
            """
        )

        print(f"[Agents] Ready: {self.profile_agent.name}, "
              f"{self.market_agent.name}, {self.recommendation_agent.name}")

    # ── Session management ────────────────────────────────────────────────────

    def get_session(self, user_id: str) -> dict:
        if user_id not in self.user_sessions:
            self.user_sessions[user_id] = {
                'preferences': {},
                'stage': 'greeting',
                'history': [],
                'last_results': []
            }
        return self.user_sessions[user_id]

    # ── Main message router ───────────────────────────────────────────────────

    def handle_message(self, user_id: str, text: str) -> str:
        """Route an incoming Telegram message through the conversation state machine."""
        session = self.get_session(user_id)

        # Global commands
        cmd = text.strip().lower()
        if cmd in ('restart', '/start', 'new search', 'reset'):
            session.update({'preferences': {}, 'stage': 'greeting', 'last_results': []})
            return self._greeting(session)

        if cmd in ('/help', 'help'):
            return (
                "Vehicle Buy Assistant — Commands\n\n"
                "  /start    — Start a new vehicle search\n"
                "  compare   — Compare top results\n"
                "  financing — Monthly EMI estimate\n"
                "  more      — Show more listings\n"
                "  /help     — Show this message\n\n"
                "Powered by Parse.bot / Riyasewana API"
            )

        session['history'].append({'role': 'user', 'text': text})

        stage = session['stage']

        if stage == 'greeting':
            response = self._greeting(session)
            session['stage'] = 'profile'

        elif stage == 'profile':
            response = self._profile(session, text)
            if 'features' in session['preferences']:
                session['stage'] = 'results'

        elif stage == 'results':
            response = self._results(session)
            session['stage'] = 'followup'

        else:
            response = self._followup(session, text)

        session['history'].append({'role': 'bot', 'text': response})
        return response

    # ── Stage handlers ────────────────────────────────────────────────────────

    def _greeting(self, session: dict) -> str:
        db_size = len(VEHICLE_DB)
        src = f"({db_size} live listings from Riyasewana)" if db_size else "(local database)"
        return (
            f"Vehicle Buy Assistant {src}\n"
            "Sri Lanka's smart car advisor — powered by Parse.bot API\n\n"
            "I'll help you find your perfect vehicle in 4 quick questions.\n\n"
            "What's your budget?\n"
            "(e.g. 'Rs. 5 million', 'under 8 million', '4,500,000')\n\n"
            "Type /help at any time to see available commands."
        )

    def _profile(self, session: dict, text: str) -> str:
        prefs = session['preferences']

        if 'budget' not in prefs:
            prefs['budget'] = text
            return (
                "Great!\n\n"
                "What type of vehicle do you prefer?\n\n"
                "  1. SUV        — spacious, Sri Lankan roads friendly\n"
                "  2. Sedan      — comfortable, fuel-efficient\n"
                "  3. Hybrid     — low fuel cost, very popular in SL\n"
                "  4. Electric   — zero fuel (Nissan Leaf, etc.)\n"
                "  5. Hatchback  — compact, easy to park\n"
                "  6. Van        — HiAce, Delica for large families\n"
                "  7. Truck      — Hilux, Ranger for heavy duty"
            )

        elif 'type' not in prefs:
            prefs['type'] = text
            return (
                "Excellent!\n\n"
                "What will you mainly use it for?\n\n"
                "  1. Commuting  — daily traffic, fuel efficiency matters\n"
                "  2. Family     — space, safety, comfort\n"
                "  3. Off-road   — upcountry, rural roads\n"
                "  4. Business   — professional appearance"
            )

        elif 'usage' not in prefs:
            prefs['usage'] = text
            return (
                "Perfect!\n\n"
                "Any must-have features?\n\n"
                "  1. Safety         — airbags, ABS, crash rating\n"
                "  2. Fuel saving    — petrol efficiency\n"
                "  3. Hybrid/EV      — low running cost\n"
                "  4. Technology     — touchscreen, Apple CarPlay\n"
                "  5. Comfort        — leather seats, AC, sunroof"
            )

        else:
            prefs['features'] = text
            return (
                "All set! Here is your profile:\n\n"
                f"  Budget   : {prefs['budget']}\n"
                f"  Type     : {prefs['type']}\n"
                f"  Use      : {prefs['usage']}\n"
                f"  Features : {prefs['features']}\n\n"
                "Searching live Riyasewana listings...\n"
                "(send any message to see your results)"
            )

    def _results(self, session: dict) -> str:
        prefs = session['preferences']
        matches = search_vehicles(prefs, VEHICLE_DB, top_n=3)
        session['last_results'] = matches

        if not matches:
            return (
                "No exact matches found.\n\n"
                "Try: a higher budget, or a different vehicle type.\n"
                "Type /start to search again."
            )

        src = VEHICLE_DB[0].get('source', 'Local DB') if VEHICLE_DB else 'Local DB'
        lines = [f"Top {len(matches)} Matches from {src}:", "=" * 48]
        for i, (v, score, reasons) in enumerate(matches, 1):
            lines.append(format_vehicle(v, reasons, i))
            lines.append("-" * 48)
        lines += [
            "",
            "What would you like next?",
            "  compare   — side-by-side comparison",
            "  financing — monthly payment estimate",
            "  more      — more listings",
            "  /start    — new search"
        ]
        return '\n'.join(lines)

    def _followup(self, session: dict, text: str) -> str:
        cmd = text.strip().lower()
        if 'financ' in cmd or 'payment' in cmd or 'monthly' in cmd:
            return self._financing(session)
        if 'compare' in cmd:
            return self._compare(session)
        if 'more' in cmd:
            return self._more(session)
        return (
            "Commands:\n"
            "  compare   — compare top results\n"
            "  financing — monthly EMI estimate\n"
            "  more      — additional listings\n"
            "  /start    — new search\n\n"
            "Visit riyasewana.com to contact sellers directly."
        )

    # ── Follow-up commands ────────────────────────────────────────────────────

    def _financing(self, session: dict) -> str:
        results = session.get('last_results', [])
        if not results:
            return "Complete a search first. Type /start to begin."
        v, _, _ = results[0]
        price = v.get('price', 0)
        if not price or price < 100000:
            return "Price not available for financing estimate."
        down  = int(price * 0.20)
        loan  = price - down
        rate  = 0.12 / 12
        n     = 60
        emi   = int(loan * rate * (1 + rate) ** n / ((1 + rate) ** n - 1))
        return (
            f"Financing Estimate — {v['make']} {v['model']}\n"
            f"{'=' * 42}\n"
            f"  Vehicle Price   : Rs. {price:,}\n"
            f"  20% Down        : Rs. {down:,}\n"
            f"  Loan Amount     : Rs. {loan:,}\n"
            f"  Term            : 60 months\n"
            f"  Est. Rate       : ~12% p.a.\n"
            f"  Monthly Payment : Rs. {emi:,}\n"
            f"{'=' * 42}\n"
            "Note: Contact your bank for exact rates."
        )

    def _compare(self, session: dict) -> str:
        results = session.get('last_results', [])
        if len(results) < 2:
            return "Need at least 2 results to compare. Type /start to search again."
        lines = ["Side-by-Side Comparison", "=" * 48]
        for i, (v, _, _) in enumerate(results[:3], 1):
            price = v.get('price', 0)
            price_s = f"Rs. {price:,}" if price else "N/A"
            mileage = v.get('mileage', 'N/A')
            mil_s   = f"{mileage:,} km" if isinstance(mileage, int) else str(mileage)
            lines.append(
                f"{i}. {v['make']} {v['model']} ({v['year']})\n"
                f"   Price: {price_s}   Mileage: {mil_s}\n"
                f"   Fuel: {v.get('fuel', str(v.get('mpg','?')) + ' MPG')}"
                f"   Safety: {v.get('safety_rating', 4)}/5\n"
                f"   Location: {v.get('city', 'N/A')}"
            )
            lines.append("-" * 48)
        lines.append("\nType 'financing' for EMI estimate | /start for new search")
        return '\n'.join(lines)

    def _more(self, session: dict) -> str:
        prefs = session.get('preferences', {})
        matches = search_vehicles(prefs, VEHICLE_DB, top_n=6)
        extra = matches[3:]
        if not extra:
            return "No more matches found. Type /start for new search."
        lines = ["More Listings:", "=" * 48]
        for i, (v, score, reasons) in enumerate(extra, 4):
            lines.append(format_vehicle(v, reasons, i))
            lines.append("-" * 48)
        return '\n'.join(lines)


# ── Production Agent Kernel setup ─────────────────────────────────────────────

def create_telegram_server():
    """
    Instantiate the Agent Kernel Telegram handler.

    Requires environment variable:
      TELEGRAM_BOT_TOKEN — from @BotFather on Telegram

    Agent Kernel handles:
      - Telegram webhook registration
      - Incoming update parsing (Message, CallbackQuery)
      - Reply sending via Telegram Bot API
      - Session management per chat_id
    """
    if not AK_AVAILABLE:
        print("[Server] agentkernel not installed — cannot start Telegram server.")
        return None

    token = os.environ.get('TELEGRAM_BOT_TOKEN', '')
    if not token:
        print("[Server] TELEGRAM_BOT_TOKEN is not set.")
        print("[Server] Get a token from @BotFather on Telegram.")
        return None

    return AgentTelegramRequestHandler()


# ── CLI simulation (competition demo mode) ────────────────────────────────────

def run_cli_simulation():
    """
    Run the Telegram bot as an interactive CLI simulation.
    Identical conversation flow to what Telegram users would experience.
    """
    print("=" * 60)
    print("  Vehicle Buy Assistant — Telegram Bot Simulator")
    print("  Powered by Parse.bot / Riyasewana API")
    print("  (Production: connect via Telegram Bot API)")
    print("=" * 60)
    print(f"\n  Database : {len(VEHICLE_DB)} vehicle listings loaded")
    if VEHICLE_DB:
        print(f"  Source   : {VEHICLE_DB[0].get('source', 'Local DB')}")
    print("\n  Commands : /start | compare | financing | more | /help | exit")
    print("=" * 60 + "\n")

    bot = VehicleBuyAssistantTelegram()
    chat_id = "demo_user"

    # Show greeting
    greeting = bot._greeting(bot.get_session(chat_id))
    bot.get_session(chat_id)['stage'] = 'profile'
    print(f"[BOT]\n{greeting}\n")

    while True:
        try:
            user_input = input("[YOU]  ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n\nGoodbye!")
            break

        if not user_input:
            continue

        if user_input.lower() in ('exit', 'quit', 'bye'):
            print("\n[BOT]  Thank you for using Vehicle Buy Assistant!")
            print("       Visit riyasewana.com to view more listings. Goodbye!")
            break

        response = bot.handle_message(chat_id, user_input)
        print(f"\n[BOT]\n{response}\n")


# ── Entry point ───────────────────────────────────────────────────────────────

if __name__ == "__main__":

    if '--server' in sys.argv:
        # Direct users to the dedicated server file
        print("=" * 60)
        print("  For the real Telegram webhook server, use:")
        print("  python interface/telegram_server.py")
        print()
        print("  That file starts Uvicorn and handles live Telegram messages.")
        print("  Make sure interface/.env has AK_TELEGRAM__BOT_TOKEN set.")
        print("=" * 60)

    elif '--cli' in sys.argv:
        # agentkernel CLI mode — full AI conversation via Ollama
        try:
            from agentkernel.cli import CLI
            print("[CLI] Starting agentkernel CLI with Ollama (llama3.2)...")
            CLI.main()
        except Exception as e:
            print(f"[CLI] Could not start CLI: {e}")
            print("[CLI] Falling back to simulation mode...\n")
            run_cli_simulation()

    else:
        # Default: competition demo / simulator mode
        run_cli_simulation()
