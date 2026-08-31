```markdown
# 🚗 Vehicle Buy Assistant

A conversational AI assistant designed to help users compare vehicles, understand their fit based on budget and lifestyle, and receive personalized recommendations through a simple CLI or WhatsApp-ready interface.

## 1. Problem Statement

Buying a car is one of the most stressful and expensive decisions many people make. Buyers often face:

- Too many options with inconsistent specifications and pricing
- Limited transparency around trade-offs between price, fuel efficiency, safety, and purpose
- Difficulty aligning personal needs with the right vehicle type
- Risk of choosing a car that does not match budget, usage, or lifestyle

This creates friction for everyday consumers and can lead to poor purchasing decisions. The problem is especially relevant to the goals of **SDG 9: Industry, Innovation, and Infrastructure** and **SDG 11: Sustainable Cities and Communities**, because better-informed mobility choices can lead to cleaner, more efficient, and more sustainable transportation decisions.

This project addresses that challenge by using AI to guide the buyer through a structured recommendation process, reduce uncertainty, and make vehicle selection more transparent and accessible.

---

## 2. Solution Overview

The Vehicle Buy Assistant is a multi-agent system that collects user preferences, searches a vehicle database, and generates explainable recommendations.

### Three specialized agents

1. **Profile Agent** — gathers the user’s budget, preferred vehicle type, usage context, and must-have features
2. **Market Agent** — searches the vehicle database and filters candidates based on the collected preferences
3. **Recommendation Agent** — ranks the matches and explains why each recommendation is a strong fit

### Key features

- Conversational interaction through a CLI interface, with WhatsApp-ready integration
- **Real-time vehicle listings from Riyasewana.lk** via the [Parse.bot API](https://parse.bot) (22,000+ live Sri Lankan car listings)
- Persistent memory for user preferences across sessions
- Intelligent vehicle matching using structured filtering and scoring
- Clear, explainable recommendations with supporting reasons
- Prices displayed in Sri Lankan Rupees (LKR) with city and mileage info

### Data sources

The assistant uses a **3-level priority chain** to always serve the freshest available data:

| Priority | Source | Details |
|----------|--------|---------|
| 1️⃣ | **Parse.bot API** | Live Riyasewana.lk listings via REST API — 22,308 real Sri Lankan car ads |
| 2️⃣ | **Web scraping** | Direct Riyasewana scraper as a secondary fallback |
| 3️⃣ | **Local database** | 25 curated Sri Lankan vehicles in `data/vehicles.json` — always works offline |

### Agent Kernel capabilities used

- Multi-agent orchestration
- Non-volatile cache for persistence
- Volatile cache for per-session state
- Tool integration for vehicle search logic
- WhatsApp integration readiness

---

## 3. Setup Instructions

### Prerequisites

- Python 3.12 or 3.13
- Git
- **Parse.bot API key** — for live Riyasewana listings (free tier available at [parse.bot](https://parse.bot))
- OpenAI API key (optional — for advanced cloud-backed conversational features)

### Installation steps

#### Step 1: Clone the repository

```bash
git clone https://github.com/tharushi03/agent-kernel.git
cd agent-kernel
```

#### Step 2: Install dependencies

```bash
pip install -r requirements.txt
```

#### Step 3: Navigate to the project directory

```bash
cd use-cases/vehicle_buy_assistant
```

#### Step 4: Set environment variables

**Parse.bot API key** (for live Riyasewana listings — get a free key at [parse.bot/signup](https://parse.bot/signup)):

```bash
# Linux / macOS / Git Bash
export PARSE_API_KEY=your-parse-api-key-here

# Windows Command Prompt
set PARSE_API_KEY=your-parse-api-key-here

# Windows PowerShell
$env:PARSE_API_KEY="your-parse-api-key-here"
```

**OpenAI API key** (optional):

```bash
export OPENAI_API_KEY=your-openai-api-key-here
```

> **Note:** If `PARSE_API_KEY` is not set, the assistant automatically falls back to web scraping and then to the local Sri Lankan vehicle database — so it always works.

---

## 4. How to Run the Solution

### CLI mode

```bash
python main.py
```

### Example conversation

```text
🚗 Welcome to the Vehicle Buy Assistant!
💡 Powered by Agent Kernel Memory Management

📡 Trying Parse.bot / Riyasewana API...
✅ Loaded 20 real-time listings from API!

Enter your name (or press Enter for new session): Tharushi
👋 Welcome! Let's find your perfect car!

You: under 6 million
Assistant: Great! What type of vehicle do you prefer?
           (SUV, Sedan, Truck, Electric, or Hybrid)

You: SUV
Assistant: What will you use the car for?
           (commuting, family, off-road, business)

You: family
Assistant: Any must-have features? (safety, backup camera, etc.)

You: good safety features
🔍 Searching for matching vehicles...

🚗 Top Recommendations:

1. Honda Vezel (2015) [Riyasewana API]
   💰 Price: Rs. 5,200,000
   🛣️ Mileage: 78,000 km
   📍 Location: Kandy
   ⛽ Fuel: Hybrid
   🛡️ Safety: 4/5
   📝 Honda Vezel Hybrid Z grade, excellent condition with sunroof
   ✅ Matches: Within budget, Matches SUV, Great for families

2. Daihatsu Terios (2016) [Riyasewana API]
   💰 Price: Rs. 3,900,000
   🛣️ Mileage: 76,000 km
   📍 Location: Anuradhapura
   ⛽ Fuel: Petrol
   🛡️ Safety: 3/5
   📝 Daihatsu Terios 4WD, great for rural and off-road use
   ✅ Matches: Within budget, Matches SUV, Great for families

💡 Available Commands: compare | financing | best value | export csv | report
```

### WhatsApp integration

The project includes a full WhatsApp integration layer built with **Agent Kernel's** `AgentWhatsAppRequestHandler` and OpenAI module support. It connects to the **Meta Cloud API** via webhook, routing every incoming WhatsApp message through the multi-agent pipeline.

> **Note:** A live Meta Business account is not required to review or demonstrate the integration. The code fully implements the correct webhook protocol — it can be activated simply by supplying the Meta credentials below.

---

#### How it works — Architecture

```
 WhatsApp User
      │  sends message
      ▼
 Meta Cloud API  ──(HTTPS POST webhook)──▶  Your Server (port 5000)
                                                   │
                                    AgentWhatsAppRequestHandler
                                                   │
                       ┌───────────────────────────┼───────────────────────────┐
                       ▼                           ▼                           ▼
                 ProfileAgent              MarketAgent             RecommendationAgent
             (collects budget,         (searches live             (ranks & explains
              type, usage,              Riyasewana                 top matches,
              features)                 listings)                  financing info)
                       └───────────────────────────┼───────────────────────────┘
                                                   │
                                         Parse.bot API
                                      (22,308 live listings)
                                                   │
                                    ◀─ reply sent back to WhatsApp User ─▶
```

---

#### Step 1 — Meta Developer Portal setup (conceptual)

Even without a live account, here is exactly what you would configure on
[developers.facebook.com](https://developers.facebook.com):

1. **Create a Meta App** → select *Business* type
2. **Add WhatsApp product** to your app
3. **Generate a permanent access token** from System User in Business Manager
4. **Configure the webhook** under WhatsApp → Configuration:
   - **Callback URL:** `https://your-server.com/webhook`
   - **Verify Token:** any secret string you choose _(must match `AK_WHATSAPP__VERIFY_TOKEN`)_
   - **Subscribe to:** `messages` field
5. **Note your Phone Number ID** from WhatsApp → API Setup

The webhook verification handshake (GET request with `hub.challenge`) is handled
automatically by `AgentWhatsAppRequestHandler` inside Agent Kernel — no manual code needed.

---

#### Step 2 — Set environment variables

```bash
# Linux / macOS / Git Bash
export PARSE_API_KEY="pmx_your_parse_api_key"         # Riyasewana live data
export AK_WHATSAPP__VERIFY_TOKEN="your_verify_token"  # matches Meta Portal setting
export AK_WHATSAPP__ACCESS_TOKEN="your_access_token"  # Meta permanent token
export AK_WHATSAPP__PHONE_NUMBER_ID="your_phone_id"   # from Meta API Setup
export AK_WHATSAPP__API_VERSION="v21.0"
export OPENAI_API_KEY="sk-..."                         # optional

# Windows PowerShell
$env:PARSE_API_KEY="pmx_your_parse_api_key"
$env:AK_WHATSAPP__VERIFY_TOKEN="your_verify_token"
$env:AK_WHATSAPP__ACCESS_TOKEN="your_access_token"
$env:AK_WHATSAPP__PHONE_NUMBER_ID="your_phone_id"
$env:AK_WHATSAPP__API_VERSION="v21.0"
```

---

#### Step 3 — Run the server

```bash
# Navigate to the project directory
cd use-cases/vehicle_buy_assistant

# Start the WhatsApp webhook server
python interface/whatsapp_app.py
```

Expected startup output:

```
=======================================================
  Vehicle Buy Assistant — WhatsApp Server
  Powered by Parse.bot / Riyasewana API
=======================================================

  Vehicle database: 30 listings loaded
  Data source:      Riyasewana API

  Required environment variables:
    PARSE_API_KEY              (Riyasewana live data)
    AK_WHATSAPP__VERIFY_TOKEN
    AK_WHATSAPP__ACCESS_TOKEN
    AK_WHATSAPP__PHONE_NUMBER_ID
    AK_WHATSAPP__API_VERSION   (e.g. v21.0)
    OPENAI_API_KEY             (optional)

  Starting server on port 5000...
=======================================================
```

> For local testing, use **ngrok** to expose port 5000 with a public HTTPS URL:
> ```bash
> ngrok http 5000
> ```
> Paste the ngrok URL as the Callback URL in the Meta Developer Portal.

---

#### Step 4 — Full WhatsApp conversation demo

```
BOT:  🚗 Welcome to Vehicle Buy Assistant!
      🇱🇰 Sri Lanka's smart car advisor (30 live listings from Riyasewana)
      💰 What's your budget?

USER: under 6 million

BOT:  Great! 💰
      🚗 What type of vehicle do you prefer?
      • 🚙 SUV  • 🌿 Hybrid  • ⚡ Electric  • 🏠 Hatchback  • 🛻 Truck

USER: SUV

BOT:  Excellent! 🎯
      🛣️ What will you mainly use it for?
      • 👨‍👩‍👧‍👦 Family  • 🚌 Commuting  • 🏔️ Off-road  • 💼 Business

USER: family

BOT:  Perfect! 👍
      ✨ Any must-have features?
      • 🛡️ Safety  • ⛽ Fuel efficiency  • 🌿 Hybrid  • 📱 Technology

USER: safety

BOT:  ✅ Got it! Searching live Riyasewana listings...

      🚗 Top 3 Matches from Riyasewana API:

      *1. Honda Vezel (2015)*
         💰 Rs. 5,200,000
         🛣️  78,000 km  |  📍 Kandy  |  ⛽ Hybrid
         🛡️ Safety: 4/5
         ✅ Within budget, Matches SUV, Great for families

      *2. Daihatsu Terios (2016)*
         💰 Rs. 3,900,000
         🛣️  76,000 km  |  📍 Anuradhapura  |  ⛽ Petrol
         🛡️ Safety: 3/5
         ✅ Within budget, Matches SUV, Great for families

      *3. Toyota Rush (2019)*
         💰 Rs. 5,800,000
         🛣️  44,000 km  |  📍 Kandy  |  ⛽ Petrol
         🛡️ Safety: 4/5
         ✅ Matches SUV, Great for families

      💡 Reply: compare | financing | more | restart

USER: financing

BOT:  💰 Financing Estimate — Honda Vezel
      🏷️ Vehicle Price:    Rs. 5,200,000
      📥 20% Down:         Rs. 1,040,000
      🏦 Loan Amount:      Rs. 4,160,000
      📅 Term: 60 months  |  📈 ~12% p.a.
      💳 Monthly Payment:  *Rs. 92,480*
```

---

#### Webhook implementation reference

| Component | What it does |
|-----------|--------------|
| `AgentWhatsAppRequestHandler` | Handles GET (webhook verification `hub.challenge`) and POST (message events) from Meta |
| `VehicleBuyAssistantWhatsApp` | 4-stage conversation state machine: greeting → profile → results → followup |
| `load_vehicle_database()` | Loads live Riyasewana data at startup via Parse.bot API with cache fallback |
| `search_vehicles_for_whatsapp()` | Scores vehicles against budget (LKR), type, usage and features |
| `format_vehicle_card()` | Formats each result as a clean WhatsApp message block |
| `financing_response()` | Calculates monthly EMI at ~12% p.a. over 60 months in LKR |
| `compare_response()` | Side-by-side comparison of top 3 matched vehicles |

### Project structure

```text
use-cases/vehicle_buy_assistant/
├── AGENTS.md
├── README.md
├── SPEC.md
├── main.py
├── requirements.txt
├── user_preferences.json
├── agents/
│   ├── __init__.py
│   ├── profile_agent.py
│   ├── market_agent.py
│   └── recommendation_agent.py
├── tools/
│   ├── __init__.py
│   ├── vehicle_api.py       ← Parse.bot API client (live Riyasewana data)
│   ├── vehicle_scraper.py   ← Web scraping fallback
│   ├── vehicle_search.py
│   ├── compare.py
│   ├── financing.py
│   ├── pii_handler.py
│   └── utils.py
├── interface/
│   ├── __init__.py
│   └── whatsapp_app.py
├── data/
│   ├── vehicles.json        ← 25 curated Sri Lankan vehicles (offline fallback)
│   └── cached_vehicles.json ← Auto-cached API responses
└── .venv/
```

---

## 🔧 Troubleshooting

### Python version issues

Agent Kernel requires Python 3.12 or 3.13. Check your version with:

```bash
python --version
```

If you are on Python 3.14, install Python 3.12 or 3.13 and rerun the project.

### Import errors

If you see a `ModuleNotFoundError`, ensure you are running from the correct directory:

```bash
cd use-cases/vehicle_buy_assistant
python main.py
```

### Config warning

The warning about a missing `config.yaml` file is generally harmless and can be ignored unless you need explicit custom configuration.

---

## 📊 Evaluation Criteria Alignment

| Criteria | How This Project Addresses It |
|----------|------------------------------|
| **Idea Value (40%)** | Solves a real and widespread problem with practical value for everyday vehicle buyers |
| **Agent Kernel Usage (30%)** | Uses multi-agent orchestration, memory management, tool integration, and WhatsApp-ready interfaces |
| **End Product (20%)** | Provides a functional CLI experience with a clear recommendation flow and reusable structure |
| **Documentation (10%)** | Includes clear setup, run instructions, system overview, and usage examples |

---

## 🤝 Submission

This project is prepared for the **IDEALIZE 2026 Mini-Competition**.

**Team Members:**
- [Your Name] - GitHub: [your-username]

**Repository:** https://github.com/[your-username]/agent-kernel/tree/develop/use-cases/vehicle_buy_assistant

**Demo Video:** [Link to your video]

---

## 📬 Contact

For questions, reach out via Discord or email kernel@yaala.ai.
```