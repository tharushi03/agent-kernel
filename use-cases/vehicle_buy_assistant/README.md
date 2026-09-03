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

- Conversational interaction through a CLI interface, with **Telegram bot** integration
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
- **Telegram bot integration** via `AgentTelegramRequestHandler`

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

### Telegram integration

The project includes a full **Telegram bot** integration built with **Agent Kernel's** `AgentTelegramRequestHandler` and OpenAI module support. Every incoming Telegram message is routed through the multi-agent pipeline.

> **Note:** A live Telegram bot account is not required to review the integration. The code implements the correct Agent Kernel bot protocol and can be activated simply by supplying a Bot Token from @BotFather.

---

#### How it works — Architecture

```
 Telegram User
      │  sends message
      ▼
 Telegram Bot API  ──(HTTPS POST webhook)──▶  Your Server (port 8000)
                                                    │
                                    AgentTelegramRequestHandler
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
                              ◀─ reply sent back to Telegram User ─▶
```

---

#### Step 1 — Create a Telegram Bot (via @BotFather)

1. Open Telegram and search for **@BotFather**
2. Send `/newbot`
3. Choose a name and username for your bot (e.g. `VehicleBuyAssistantBot`)
4. Copy the **Bot Token** — it looks like `123456789:ABCdef...`
5. *(Optional)* Set a description with `/setdescription` and a photo with `/setuserpic`

Agent Kernel's `AgentTelegramRequestHandler` handles all Telegram Bot API protocol details automatically (webhook registration, update parsing, reply sending).

---

#### Step 2 — Set environment variables

```bash
# Linux / macOS / Git Bash
export PARSE_API_KEY="pmx_your_parse_api_key"   # Riyasewana live data
export TELEGRAM_BOT_TOKEN="your_bot_token"      # from @BotFather
export OPENAI_API_KEY="sk-..."                  # optional

# Windows PowerShell
$env:PARSE_API_KEY="pmx_your_parse_api_key"
$env:TELEGRAM_BOT_TOKEN="your_bot_token"
$env:OPENAI_API_KEY="sk-..."
```

---

#### Step 3 — Run the server

```bash
# Navigate to the project directory
cd use-cases/vehicle_buy_assistant

# Start the Telegram webhook server
python interface/telegram_app.py --server
```

Expected startup output:

```
[Server] Starting Telegram webhook server on port 8000...
[Server] Webhook URL: http://your-server.com/telegram/webhook
[Server] Register this URL with Telegram Bot API:
  curl https://api.telegram.org/bot<TOKEN>/setWebhook
       ?url=https://your-server.com/telegram/webhook
[Server] Press Ctrl+C to stop.
```

> For local testing, use **ngrok** to expose port 8000:
> ```bash
> ngrok http 8000
> ```
> Then register the ngrok URL:
> ```bash
> curl "https://api.telegram.org/bot<TOKEN>/setWebhook?url=https://abc123.ngrok.io/telegram/webhook"
> ```

---

#### Step 4 — Competition demo (CLI simulation)

Run without `--server` to get an interactive CLI that shows the exact
conversation a Telegram user would experience:

```bash
python interface/telegram_app.py
```

```
============================================================
  Vehicle Buy Assistant — Telegram Bot Simulator
  Powered by Parse.bot / Riyasewana API
  (Production: connect via Telegram Bot API)
============================================================

  Database : 30 vehicle listings loaded
  Source   : Riyasewana API

  Commands : /start | compare | financing | more | /help | exit
============================================================

[BOT]
Vehicle Buy Assistant (30 live listings from Riyasewana)
Sri Lanka's smart car advisor — powered by Parse.bot API

I'll help you find your perfect vehicle in 4 quick questions.

What's your budget?
(e.g. 'Rs. 5 million', 'under 8 million', '4,500,000')

[YOU]  under 6 million

[BOT]
Great!

What type of vehicle do you prefer?
  1. SUV        — spacious, Sri Lankan roads friendly
  2. Sedan      — comfortable, fuel-efficient
  3. Hybrid     — low fuel cost, very popular in SL
  4. Electric   — zero fuel (Nissan Leaf, etc.)
  5. Hatchback  — compact, easy to park
  6. Van        — HiAce, Delica for large families

[YOU]  SUV
...(budget, type, usage, features collected)...

[BOT]
Top 3 Matches from Riyasewana API:
================================================
1. Honda Vezel (2015)
   Price    : Rs. 5,200,000
   Mileage  : 78,000 km
   Location : Kandy
   Fuel     : Hybrid
   Safety   : 4/5
   Match    : Within budget, Matches SUV, Great for families
------------------------------------------------
2. Daihatsu Terios (2016)
   Price    : Rs. 3,900,000
   Mileage  : 76,000 km
   Location : Anuradhapura
   Fuel     : Petrol
   Safety   : 3/5
   Match    : Within budget, Matches SUV, Great for families
------------------------------------------------

[YOU]  financing

[BOT]
Financing Estimate — Honda Vezel
==========================================
  Vehicle Price   : Rs. 5,200,000
  20% Down        : Rs. 1,040,000
  Loan Amount     : Rs. 4,160,000
  Term            : 60 months
  Est. Rate       : ~12% p.a.
  Monthly Payment : Rs. 92,480
==========================================
```

---

#### Implementation reference (`interface/telegram_app.py`)

| Component | What it does |
|-----------|--------------|
| `AgentTelegramRequestHandler` | Handles Telegram Bot API webhook updates (messages, commands) |
| `VehicleBuyAssistantTelegram` | 4-stage conversation state machine: greeting → profile → results → followup |
| `load_vehicle_database()` | Loads live Riyasewana data at startup via Parse.bot API with cache fallback |
| `search_vehicles()` | Scores vehicles against budget (LKR), type, usage and features |
| `format_vehicle()` | Formats each result as a clean text block |
| `_financing()` | Calculates monthly EMI at ~12% p.a. over 60 months in LKR |
| `_compare()` | Side-by-side comparison of top 3 matched vehicles |
| `OpenAIModule([...])` | Registers all 3 agents with Agent Kernel for AI-powered responses |

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
│   ├── telegram_app.py      ← Telegram bot (main messaging interface)
│   └── whatsapp_app.py      ← WhatsApp reference (kept for documentation)
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