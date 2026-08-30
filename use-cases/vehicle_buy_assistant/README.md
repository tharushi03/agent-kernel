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
- Persistent memory for user preferences across sessions
- Intelligent vehicle matching using structured filtering and scoring
- Clear, explainable recommendations with supporting reasons

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
- OpenAI API key (optional for advanced or cloud-backed conversational features)

### Installation steps

#### Step 1: Clone the repository

```bash
git clone https://github.com/YOUR_USERNAME/agent-kernel.git
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

#### Step 4: Set the environment variable

```bash
export OPENAI_API_KEY=your-api-key-here
```

> Windows users should use `set` instead of `export`.

---

## 4. How to Run the Solution

### CLI mode

```bash
python main.py
```

### Example conversation

```text
🚗 Welcome to the Vehicle Buy Assistant!
Tell me what you're looking for, or type 'exit' to quit.

You: I want a car under $30,000
Assistant: What type of vehicle do you prefer? (SUV, Sedan, Truck, Electric)

You: SUV
Assistant: What will you use the car for? (commuting, family, off-road)

You: family
Assistant: Any must-have features? (safety, backup camera, etc.)

You: good safety features
🔍 Searching for matching vehicles...

🚗 Top Recommendations:

1. Toyota RAV4 (2024)
   💰 Price: $29,500
   ⛽ MPG: 28
   🛡️ Safety: 5/5
   ✅ Matches: Within budget, Matches SUV, Safety rating 5/5
   📝 Reliable family SUV with excellent safety

2. Honda CR-V (2024)
   💰 Price: $28,800
   ⛽ MPG: 27
   🛡️ Safety: 5/5
   ✅ Matches: Within budget, Matches SUV, Safety rating 5/5
   📝 Comfortable SUV with great safety tech

3. Ford Escape (2024)
   💰 Price: $26,500
   ⛽ MPG: 26
   🛡️ Safety: 4/5
   ✅ Matches: Within budget, Matches SUV, Safety rating 4/5
   📝 Affordable SUV with good fuel efficiency

💡 Would you like more details on any of these?
```

### WhatsApp integration (optional)

The project includes a WhatsApp-ready integration layer built with Agent Kernel’s request handler and OpenAI module support.

#### Setup

1. Set the required environment variables with your Meta credentials:

```bash
export AK_WHATSAPP__VERIFY_TOKEN=your_verify_token
export AK_WHATSAPP__ACCESS_TOKEN=your_permanent_access_token
export AK_WHATSAPP__PHONE_NUMBER_ID=your_phone_number_id
export AK_WHATSAPP__API_VERSION=v21.0
```

2. Install dependencies if needed:

```bash
pip install -r requirements.txt
```

3. Run the WhatsApp server:

```bash
python interface/whatsapp_app.py
```

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
│   └── vehicle_search.py
├── interface/
│   ├── __init__.py
│   ├── whatsapp_app.py
│   └── __init__.py
├── data/
│   └── vehicles.json
└── .
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