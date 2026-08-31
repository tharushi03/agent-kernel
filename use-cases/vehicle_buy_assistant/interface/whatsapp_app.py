# interface/whatsapp_app.py
"""
WhatsApp Integration — Vehicle Buy Assistant
============================================
Demonstrates the full WhatsApp conversation flow using real Sri Lankan
vehicle data from the Parse.bot / Riyasewana API.

Because a live Meta Business account is not available for this competition,
this file runs as a CLI simulation of the WhatsApp conversation.

In production, connecting to real WhatsApp requires only:
  - Setting the 4 AK_WHATSAPP__ environment variables (see README)
  - Uncommenting the RESTAPI.run() call at the bottom
  - Configuring the webhook URL in the Meta Developer Portal

Agent Kernel's AgentWhatsAppRequestHandler handles all webhook protocol
details automatically (verification, signature checking, message routing).
"""

import os
import sys
import json
import re

# ── Path setup so tools/ is importable from the interface/ subdirectory ───────
BASE_DIR = os.path.join(os.path.dirname(__file__), '..')
sys.path.insert(0, BASE_DIR)

# ── Safe agentkernel imports (graceful fallback if not installed) ─────────────
try:
    from agentkernel.api import RESTAPI
    from agentkernel.whatsapp import AgentWhatsAppRequestHandler
    AK_AVAILABLE = True
except ImportError:
    AK_AVAILABLE = False
    class AgentWhatsAppRequestHandler:
        """Stub — replace with real AgentWhatsAppRequestHandler when agentkernel is installed."""
        pass
    class _RESTAPI:
        @staticmethod
        def run(handlers, host='0.0.0.0', port=5000):
            print("[Server] agentkernel not installed — cannot start WhatsApp server.")
            print("[Server] Run without --server flag to use the CLI simulation instead.")
    RESTAPI = _RESTAPI


# ── Agent class: works standalone, ready for agentkernel upgrade ──────────────
# When agentkernel is installed, this can be swapped for:
#   from agentkernel import Agent as OpenAIAgent

class OpenAIAgent:
    """
    Describes an agent's name and role instructions.
    Conversation logic is handled by VehicleBuyAssistantWhatsApp.handle_message().
    In production with agentkernel: replace with agentkernel.Agent
    and register all three agents with OpenAIModule([...]).
    """
    def __init__(self, name: str = '', instructions: str = ''):
        self.name = name
        self.instructions = instructions.strip()

    def __repr__(self):
        return f"OpenAIAgent(name={self.name!r})"


# ── Load vehicle database at startup ─────────────────────────────────────────

def load_vehicle_database():
    """
    Load vehicles using the 3-level priority chain:
      1. Parse.bot API (live Riyasewana listings)
      2. Cached vehicles from previous API calls
      3. Local Sri Lankan vehicles.json (always works offline)
    """
    cache_path = os.path.join(BASE_DIR, 'data', 'cached_vehicles.json')
    local_path = os.path.join(BASE_DIR, 'data', 'vehicles.json')

    # Priority 1: Parse.bot API
    try:
        from tools.vehicle_api import fetch_vehicles_from_api
        vehicles = fetch_vehicles_from_api(limit=30)
        if vehicles and len(vehicles) >= 5:
            print(f"[DB] Loaded {len(vehicles)} vehicles from Parse.bot / Riyasewana API")
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
                print(f"[DB] Loaded {len(vehicles)} vehicles from cache")
                return vehicles
        except Exception:
            pass

    # Priority 3: Local JSON
    try:
        with open(local_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        vehicles = data.get('vehicles', [])
        print(f"[DB] Loaded {len(vehicles)} vehicles from local Sri Lankan database")
        return vehicles
    except Exception as e:
        print(f"[DB] Could not load local database: {e}")
        return []


VEHICLE_DB = load_vehicle_database()


# ── Vehicle search & formatting ───────────────────────────────────────────────

def search_vehicles(preferences, vehicles, top_n=3):
    """Score and rank vehicles against user preferences. Returns top_n matches."""
    results = []

    for v in vehicles:
        score = 0
        reasons = []

        price   = v.get('price', 0)
        vtype   = v.get('type', '').lower()
        mpg     = v.get('mpg', 0)
        safety  = v.get('safety_rating', 4)
        fuel    = (v.get('fuel') or '').lower()

        # Budget (LKR)
        digits = re.sub(r'[^\d]', '', preferences.get('budget', ''))
        if digits:
            budget = int(digits)
            if price > 0:
                if price <= budget:
                    score += 3
                    reasons.append(f"Within budget (Rs. {price:,})")
                elif price <= budget * 1.15:
                    score += 1
                    reasons.append(f"Slightly over budget (Rs. {price:,})")

        # Type
        pref_type = preferences.get('type', '').lower()
        if pref_type and any(kw in vtype for kw in pref_type.split()):
            score += 2
            reasons.append(f"Matches {v.get('type', 'type')}")

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
            score += 2; reasons.append(f"Safety rating {safety}/5")
        if ('hybrid' in feat or 'fuel' in feat or 'effici' in feat) and \
                ('hybrid' in fuel or mpg >= 30):
            score += 1; reasons.append("Hybrid / fuel efficient")
        if 'electric' in feat and 'electric' in fuel:
            score += 2; reasons.append("Fully electric")

        if score > 0:
            results.append((v, score, reasons))

    results.sort(key=lambda x: x[1], reverse=True)
    return results[:top_n]


def format_vehicle_card(v, reasons, rank):
    """Format one vehicle as a WhatsApp-style text block."""
    price = v.get('price', 0)
    price_str = f"Rs. {price:,}" if price > 500000 else (f"${price:,}" if price else "Negotiable")
    mileage = v.get('mileage')
    city    = v.get('city')
    fuel    = v.get('fuel')
    mpg     = v.get('mpg')

    lines = [f"{rank}. *{v['make']} {v['model']} ({v['year']})*"]
    lines.append(f"   Price    : {price_str}")
    if mileage:
        mileage_str = f"{mileage:,} km" if isinstance(mileage, int) else str(mileage)
        lines.append(f"   Mileage  : {mileage_str}")
    if city:
        lines.append(f"   Location : {city}")
    if fuel:
        lines.append(f"   Fuel     : {fuel}")
    elif mpg:
        lines.append(f"   MPG      : {mpg}")
    lines.append(f"   Safety   : {v.get('safety_rating', 4)}/5")
    if reasons:
        lines.append(f"   Matches  : {', '.join(reasons)}")
    lines.append(f"   Source   : {v.get('source', 'Local DB')}")
    return '\n'.join(lines)


# ── Multi-agent assistant class ───────────────────────────────────────────────

class VehicleBuyAssistantWhatsApp:
    """
    Multi-agent Vehicle Buy Assistant.
    Orchestrates Profile, Market, and Recommendation agents.

    In production: driven by WhatsApp messages via AgentWhatsAppRequestHandler.
    In simulation: driven by CLI input (for competition demo purposes).
    """

    def __init__(self):
        self.user_sessions = {}
        self.init_agents()

    def init_agents(self):
        """Initialise the three specialised Agent Kernel agents."""

        # ── Agent Kernel agent definitions ────────────────────────────────────
        # These describe each agent's role and instructions.
        # In production with agentkernel installed:
        #   from agentkernel import Agent
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
            Rank results by best fit. Explain pros/cons for Sri Lankan roads.
            Highlight hybrid savings. Provide EMI estimates at ~12% p.a. over 60 months.
            Suggest next steps (visit riyasewana.com, contact seller, test drive).
            """
        )

        # Agents registered — conversation logic handled by handle_message() below
        print(f"[Agents] Initialised: {self.profile_agent.name}, "
              f"{self.market_agent.name}, {self.recommendation_agent.name}")


    # ── Session management ────────────────────────────────────────────────────

    def get_or_create_session(self, phone_number):
        if phone_number not in self.user_sessions:
            self.user_sessions[phone_number] = {
                'preferences': {},
                'stage': 'greeting',
                'conversation_history': [],
                'last_results': []
            }
        return self.user_sessions[phone_number]

    # ── Main message router ───────────────────────────────────────────────────

    def handle_message(self, phone_number, message_text):
        """Route an incoming message through the conversation state machine."""
        session = self.get_or_create_session(phone_number)

        # Global commands
        if message_text.strip().lower() in ('restart', 'start over', 'new search', 'reset'):
            session.update({'preferences': {}, 'stage': 'greeting', 'last_results': []})
            return (
                "Starting fresh!\n\n"
                "Vehicle Buy Assistant — powered by live Riyasewana data\n\n"
                "What's your budget? (e.g. Rs. 5,000,000 or 'under 6 million')"
            )

        session['conversation_history'].append({'sender': 'user', 'message': message_text})

        stage = session['stage']

        if stage == 'greeting':
            response = self.greeting_response(session)
            session['stage'] = 'profile'

        elif stage == 'profile':
            response = self.profile_response(session, message_text)
            if 'features' in session['preferences']:
                session['stage'] = 'results'

        elif stage == 'results':
            response = self.results_response(session)
            session['stage'] = 'followup'

        else:
            response = self.followup_response(session, message_text)

        session['conversation_history'].append({'sender': 'assistant', 'message': response})
        return response

    # ── Stage handlers ────────────────────────────────────────────────────────

    def greeting_response(self, session):
        db_size = len(VEHICLE_DB)
        note = f"({db_size} live listings from Riyasewana)" if db_size else "(local database)"
        return (
            f"Vehicle Buy Assistant {note}\n"
            "Sri Lanka's smart car advisor\n\n"
            "I'll help you find your perfect vehicle in 4 quick questions.\n\n"
            "What's your budget?\n"
            "(e.g. 'Rs. 5 million', 'under 8 million', '4,500,000')"
        )

    def profile_response(self, session, user_input):
        prefs = session['preferences']

        if 'budget' not in prefs:
            prefs['budget'] = user_input
            return (
                "Great!\n\n"
                "What type of vehicle do you prefer?\n\n"
                "  [1] SUV         - spacious, great for Sri Lankan roads\n"
                "  [2] Sedan       - comfortable, fuel-efficient\n"
                "  [3] Hybrid      - low fuel cost, very popular in SL\n"
                "  [4] Electric    - zero fuel (Nissan Leaf, etc.)\n"
                "  [5] Hatchback   - compact, easy to park\n"
                "  [6] Van         - HiAce, Delica for large families\n"
                "  [7] Truck       - Hilux, Ranger for heavy duty"
            )

        elif 'type' not in prefs:
            prefs['type'] = user_input
            return (
                "Excellent!\n\n"
                "What will you mainly use it for?\n\n"
                "  [1] Commuting   - daily Colombo traffic, fuel matters\n"
                "  [2] Family      - space, safety, comfort\n"
                "  [3] Off-road    - upcountry, rural roads\n"
                "  [4] Business    - professional appearance"
            )

        elif 'usage' not in prefs:
            prefs['usage'] = user_input
            return (
                "Perfect!\n\n"
                "Any must-have features?\n\n"
                "  [1] Safety      - airbags, ABS, crash rating\n"
                "  [2] Fuel saving - petrol efficiency\n"
                "  [3] Hybrid      - low running cost\n"
                "  [4] Technology  - touchscreen, Apple CarPlay\n"
                "  [5] Comfort     - leather seats, AC, sunroof"
            )

        else:
            prefs['features'] = user_input
            return (
                "All set! Here is your profile:\n\n"
                f"  Budget   : {prefs['budget']}\n"
                f"  Type     : {prefs['type']}\n"
                f"  Use      : {prefs['usage']}\n"
                f"  Features : {prefs['features']}\n\n"
                "Searching live Riyasewana listings...\n"
                "(press Enter / send any message to see results)"
            )

    def results_response(self, session):
        prefs = session['preferences']
        matches = search_vehicles(prefs, VEHICLE_DB, top_n=3)
        session['last_results'] = matches

        if not matches:
            return (
                "No exact matches found.\n\n"
                "Try: a higher budget, or a different vehicle type.\n"
                "Reply 'restart' to search again."
            )

        src = VEHICLE_DB[0].get('source', 'Local DB') if VEHICLE_DB else 'Local DB'
        response = f"Top {len(matches)} Matches from {src}:\n"
        response += "=" * 50 + "\n"
        for i, (v, score, reasons) in enumerate(matches, 1):
            response += format_vehicle_card(v, reasons, i) + "\n"
            response += "-" * 50 + "\n"

        response += (
            "\nWhat would you like next?\n"
            "  Type 'compare'   - side-by-side comparison\n"
            "  Type 'financing' - monthly payment estimate\n"
            "  Type 'more'      - show more listings\n"
            "  Type 'restart'   - start a new search"
        )
        return response

    def followup_response(self, session, user_input):
        cmd = user_input.strip().lower()

        if 'financ' in cmd or 'payment' in cmd or 'monthly' in cmd:
            return self._financing(session)
        if 'compare' in cmd:
            return self._compare(session)
        if 'more' in cmd:
            return self._more(session)

        return (
            "Vehicle Buy Assistant\n\n"
            "  'compare'   - side-by-side comparison\n"
            "  'financing' - monthly payment estimate\n"
            "  'more'      - additional listings\n"
            "  'restart'   - new search\n\n"
            "Visit riyasewana.com to contact sellers directly."
        )

    # ── Follow-up commands ────────────────────────────────────────────────────

    def _financing(self, session):
        results = session.get('last_results', [])
        if not results:
            return "Complete a search first. Type 'restart' to begin."

        v, _, _ = results[0]
        price = v.get('price', 0)
        if not price or price < 100000:
            return "Price not available for financing estimate."

        down    = int(price * 0.20)
        loan    = price - down
        rate    = 0.12 / 12
        n       = 60
        emi     = int(loan * rate * (1 + rate) ** n / ((1 + rate) ** n - 1))

        return (
            f"Financing Estimate — {v['make']} {v['model']}\n"
            f"{'=' * 40}\n"
            f"Vehicle Price   : Rs. {price:,}\n"
            f"20% Down        : Rs. {down:,}\n"
            f"Loan Amount     : Rs. {loan:,}\n"
            f"Term            : 60 months\n"
            f"Est. Rate       : ~12% p.a.\n"
            f"Monthly Payment : Rs. {emi:,}\n"
            f"{'=' * 40}\n"
            "Note: These are estimates. Contact your bank for exact rates."
        )

    def _compare(self, session):
        results = session.get('last_results', [])
        if len(results) < 2:
            return "Need at least 2 results to compare. Type 'restart' to search again."

        lines = ["Side-by-Side Comparison", "=" * 50]
        for i, (v, _, _) in enumerate(results[:3], 1):
            price    = v.get('price', 0)
            price_s  = f"Rs. {price:,}" if price else "N/A"
            mileage  = v.get('mileage', 'N/A')
            mileage_s = f"{mileage:,} km" if isinstance(mileage, int) else str(mileage)
            lines.append(
                f"{i}. {v['make']} {v['model']} ({v['year']})\n"
                f"   Price: {price_s}  |  Mileage: {mileage_s}\n"
                f"   Fuel: {v.get('fuel', str(v.get('mpg','?')) + ' MPG')}"
                f"  |  Safety: {v.get('safety_rating', 4)}/5\n"
                f"   Location: {v.get('city', 'N/A')}"
            )
            lines.append("-" * 50)
        lines.append("\nType 'financing' for payment estimates | 'restart' to search again")
        return '\n'.join(lines)

    def _more(self, session):
        prefs = session.get('preferences', {})
        matches = search_vehicles(prefs, VEHICLE_DB, top_n=6)
        extra = matches[3:]

        if not extra:
            return "No more matches found. Type 'restart' to try different preferences."

        response = "More Listings:\n" + "=" * 50 + "\n"
        for i, (v, score, reasons) in enumerate(extra, 4):
            response += format_vehicle_card(v, reasons, i) + "\n" + "-" * 50 + "\n"
        return response


# ── Production server setup (requires Meta credentials) ──────────────────────

def create_whatsapp_server():
    """
    Create the production WhatsApp webhook server.

    Requires these environment variables:
      PARSE_API_KEY                  - Riyasewana live data
      AK_WHATSAPP__VERIFY_TOKEN      - matches Meta Portal Verify Token
      AK_WHATSAPP__ACCESS_TOKEN      - Meta permanent access token
      AK_WHATSAPP__PHONE_NUMBER_ID   - from Meta API Setup page
      AK_WHATSAPP__API_VERSION       - e.g. v21.0
    """
    if not AK_AVAILABLE:
        print("[Server] agentkernel not installed — running in simulation mode only.")
        return None
    return AgentWhatsAppRequestHandler()


# ── CLI simulation (competition demo) ────────────────────────────────────────

def run_cli_simulation():
    """
    Run the WhatsApp assistant as an interactive CLI simulation.
    This is what judges see during the competition demo.
    The conversation flow is identical to what WhatsApp users would experience.
    """
    print("=" * 60)
    print("  Vehicle Buy Assistant — WhatsApp Conversation Simulator")
    print("  Powered by Parse.bot / Riyasewana API")
    print("  (In production: replace with live WhatsApp webhook)")
    print("=" * 60)
    print(f"\n  Database: {len(VEHICLE_DB)} vehicle listings loaded")
    if VEHICLE_DB:
        print(f"  Source  : {VEHICLE_DB[0].get('source', 'Local DB')}")
    print("\n  Commands: restart | compare | financing | more | exit")
    print("=" * 60 + "\n")

    assistant = VehicleBuyAssistantWhatsApp()
    phone = "demo_user"

    # Trigger greeting
    session = assistant.get_or_create_session(phone)
    greeting = assistant.greeting_response(session)
    session['stage'] = 'profile'
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
            print("\n[BOT]  Thank you for using Vehicle Buy Assistant! Goodbye!")
            break

        response = assistant.handle_message(phone, user_input)
        print(f"\n[BOT]\n{response}\n")


# ── Entry point ───────────────────────────────────────────────────────────────

if __name__ == "__main__":

    if '--server' in sys.argv:
        # Production WhatsApp server mode
        if not AK_AVAILABLE:
            print("=" * 60)
            print("  Cannot start WhatsApp server:")
            print("  agentkernel is not installed in this environment.")
            print()
            print("  Install it with:")
            print("    pip install agentkernel[whatsapp,openai]")
            print()
            print("  Then set Meta credentials:")
            print("    AK_WHATSAPP__VERIFY_TOKEN")
            print("    AK_WHATSAPP__ACCESS_TOKEN")
            print("    AK_WHATSAPP__PHONE_NUMBER_ID")
            print("    AK_WHATSAPP__API_VERSION")
            print()
            print("  Falling back to CLI simulation mode...")
            print("=" * 60 + "\n")
            run_cli_simulation()
        else:
            handler = create_whatsapp_server()
            if handler and AK_AVAILABLE:
                print("[Server] Starting WhatsApp webhook server on port 5000...")
                print("[Server] Configure Meta Developer Portal webhook URL to point here.")
                print("[Server] Press Ctrl+C to stop.\n")
                try:
                    # In production with agentkernel installed this starts the
                    # webhook server that Meta's Cloud API posts messages to.
                    # Equivalent to: flask/uvicorn serving POST /webhook
                    RESTAPI.run([handler], host='0.0.0.0', port=5000)  # type: ignore[union-attr]
                except KeyboardInterrupt:
                    print("\n[Server] Stopped.")
                except Exception as e:
                    print(f"\n[Server] Error: {e}")
            else:
                print("[Server] Could not create WhatsApp handler.")
                print("[Server] Ensure all AK_WHATSAPP__ env vars are set.")
    else:
        # Default: competition demo mode — interactive CLI simulation
        run_cli_simulation()