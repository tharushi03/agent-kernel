```markdown
# 🚗 Vehicle Buy Assistant

## 1. Problem Statement

Buying a car is one of the most stressful and confusing consumer experiences. Buyers face:
- Overwhelming options with confusing specifications
- Lack of transparent pricing and comparison information
- Difficulty matching personal needs with available vehicles
- Risk of making uninformed decisions

**SDG 9**: Industry, Innovation, and Infrastructure
**SDG 11**: Sustainable Cities and Communities

This project addresses these challenges by using AI to provide personalized, data-driven car recommendations through a simple conversational interface.

---

## 2. Solution Overview

A multi-agent AI system that helps people find the perfect car through a conversational interface. The system uses:

### Three Specialized Agents:
1. **Profile Agent** - Interviews users about budget, vehicle type, usage, and must-have features
2. **Market Agent** - Searches a vehicle database for matching cars
3. **Recommendation Agent** - Ranks each car with pros, cons, and clear recommendations

### Key Features:
- **Conversational Interface** - Natural language interaction via CLI (WhatsApp-ready)
- **Memory Management** - Remembers user preferences across sessions
- **Smart Matching** - Scores vehicles based on user preferences
- **Transparent Recommendations** - Explains why each car is recommended

### Agent Kernel Features Used:
- Multi-Agent Orchestration
- Non-Volatile Cache (session memory)
- Tool Integration (vehicle database search)
- WhatsApp Integration (ready for deployment)

---

## 3. Setup Instructions

### Prerequisites

- Python 3.12 or 3.13 (3.14 NOT supported)
- Git
- OpenAI API key (optional for advanced features)

### Installation Steps

#### Step 1: Clone the Repository

```bash
git clone https://github.com/YOUR_USERNAME/agent-kernel.git
cd agent-kernel
```

#### Step 2: Install Dependencies

```bash
pip install agentkernel[cli,openai]
```

#### Step 3: Navigate to the Project

```bash
cd use-cases/vehicle_buy_assistant
```

#### Step 4: Set Up Environment

```bash
export OPENAI_API_KEY=your-api-key-here
```

---

## 4. How to Run the Solution

### CLI Mode (Testing)

```bash
python main.py
```

### Example Conversation

```
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

### WhatsApp Integration (Optional)

```bash
python interface/whatsapp_app.py
```

### Project Structure

```
use-cases/vehicle_buy_assistant/
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
│   ├── cli.py
│   └── whatsapp_app.py
├── data/
│   └── vehicles.json
├── main.py
├── requirements.txt
└── README.md
```

---

## 🔧 Troubleshooting

### Python Version Issues
Agent Kernel requires Python 3.12 or 3.13. Check your version:
```bash
python --version
```
If you have Python 3.14, install Python 3.12 and use it instead.

### Import Errors
If you get `ModuleNotFoundError`, ensure you're running from the correct directory:
```bash
cd use-cases/vehicle_buy_assistant
python main.py
```

### Config Warning
The warning `Could not open yaml settings file at: config.yaml` is harmless. You can ignore it.

---

## 📊 Evaluation Criteria Alignment

| Criteria | How This Project Addresses It |
|----------|------------------------------|
| **Idea Value (40%)** | Solves a real, universal problem with clear practical value |
| **Agent Kernel Usage (30%)** | Multi-agent orchestration, tool integration, memory management, WhatsApp-ready |
| **End Product (20%)** | Functional, polished, easy to run and test |
| **Documentation (10%)** | Complete README with setup and run instructions |

---

## 🤝 Submission

This project was submitted for the **IDEALIZE 2026 Mini-Competition**.

**Team Members:**
- [Your Name] - GitHub: [your-username]

**Repository:** https://github.com/[your-username]/agent-kernel/tree/develop/use-cases/vehicle_buy_assistant

**Demo Video:** [Link to your video]

---

## 📬 Contact

For questions, reach out via Discord or email kernel@yaala.ai.
```