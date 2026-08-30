```markdown
# Agent Documentation: Vehicle Buy Assistant

## Architecture Overview

The Vehicle Buy Assistant uses a **multi-agent orchestration pattern** where a supervisor routes user requests to specialized agents.

```
┌─────────────────────────────────────────────────────────────────┐
│                    USER INTERFACE (CLI/WhatsApp)               │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    ORCHESTRATOR AGENT                          │
│              (Routes to appropriate agents)                    │
└─────────────────────────────────────────────────────────────────┘
                              │
        ┌─────────────────────┼─────────────────────┐
        ▼                     ▼                     ▼
┌───────────────┐   ┌───────────────────┐   ┌───────────────┐
│  PROFILE      │   │  MARKET           │   │  RECOMMEND    │
│  AGENT        │──▶│  AGENT            │──▶│  AGENT        │
│ (Collects     │   │ (Searches         │   │ (Ranks &      │
│  preferences) │   │  vehicles)        │   │  explains)    │
└───────────────┘   └───────────────────┘   └───────────────┘
        │                     │                     │
        ▼                     ▼                     ▼
┌─────────────────────────────────────────────────────────────────┐
│                    OUTPUT: Recommendations                     │
└─────────────────────────────────────────────────────────────────┘
```

---

## Agent Details

### 1. Profile Agent (`agents/profile_agent.py`)

**Purpose:** Collect user preferences through conversation.

**Role:** First point of contact. Guides the user through a structured interview.

**Key Responsibilities:**
- Ask about budget
- Ask about vehicle type (SUV, Sedan, Truck, Electric)
- Ask about primary use (commuting, family, off-road)
- Ask about must-have features
- Store preferences in Non-Volatile Cache

**Input:** Natural language user messages
**Output:** Structured preference data

**Agent Kernel Features Used:**
- Non-Volatile Cache (persists across sessions)
- Conversational state management

---

### 2. Market Agent (`agents/market_agent.py`)

**Purpose:** Search for vehicles matching user preferences.

**Role:** Connects to the vehicle database and filters results.

**Key Responsibilities:**
- Load vehicle database
- Filter vehicles by budget, type, features
- Score each vehicle based on match quality
- Return top matches

**Input:** User preferences
**Output:** Ranked list of vehicles with scores

**Agent Kernel Features Used:**
- Tool integration (database search)
- Volatile Cache (intermediate results)

---

### 3. Recommendation Agent (`agents/recommendation_agent.py`)

**Purpose:** Rank vehicles and provide explainable recommendations.

**Role:** Final decision support. Makes recommendations understandable.

**Key Responsibilities:**
- Calculate weighted scores
- Generate pros and cons
- Provide clear summaries
- Suggest next steps

**Input:** Ranked vehicle list
**Output:** Final recommendations with explanations

**Agent Kernel Features Used:**
- Tool integration (scoring engine)
- Output formatting

---

## Agent Communication Flow

```
User Input
    │
    ▼
Profile Agent ─────────────────────────────────────┐
    │                                              │
    ▼                                              │
Market Agent (uses Vehicle Database Tool)          │
    │                                              │
    ▼                                              │
Recommendation Agent (uses Scoring Tool)           │
    │                                              │
    ▼                                              │
Final Response to User ◄───────────────────────────┘
```

---

## Memory Management

### Non-Volatile Cache
Stores user preferences across sessions:
- Budget
- Vehicle type
- Usage
- Features

### Volatile Cache
Stores temporary data for current request:
- Search results
- Intermediate scores
- Filtered lists

---

## Tools Used

### Vehicle Database Tool
- **Path:** `tools/vehicle_search.py`
- **Purpose:** Load and search vehicle database
- **Data Source:** `data/vehicles.json`
- **Functions:**
  - `load_vehicles()` - Loads JSON database
  - `search_vehicles(preferences)` - Filters and scores vehicles

### Financing Calculator Tool
- **Path:** `tools/financing.py`
- **Purpose:** Calculate monthly payments
- **Formula:** EMI = P × r × (1+r)ⁿ / ((1+r)ⁿ - 1)

---

## Integration Points

### WhatsApp Interface
- **File:** `interface/whatsapp_app.py`
- **Integration:** Uses Agent Kernel's WhatsApp support
- **Setup:** Requires Twilio account

### CLI Interface
- **File:** `interface/cli.py`
- **Purpose:** Testing and demonstration
- **Features:** Full conversation flow

---

## Running the Agents

### CLI Mode
```bash
python interface/cli.py
```

### WhatsApp Mode
```bash
python interface/whatsapp_app.py
```

### Individual Agent Testing
```bash
python -c "from agents.profile_agent import ProfileAgent; agent = ProfileAgent()"
```

---

## Extending the System

### Adding a New Agent
1. Create new agent file in `agents/`
2. Inherit from `Agent` class
3. Implement required methods
4. Register with orchestrator

### Adding a New Tool
1. Create new tool file in `tools/`
2. Define functions for tool operations
3. Import and use in agents

### Adding More Vehicle Data
1. Edit `data/vehicles.json`
2. Follow the existing format
3. Add fields as needed

---

## Performance Considerations

- **Database Size:** Currently 5 vehicles. Can scale to 100+.
- **Response Time:** < 1 second for search and scoring
- **Memory Usage:** ~50MB for Python runtime

---

## Security

- No user data stored permanently
- Session data cleared when user exits
- No external API calls (unless WhatsApp enabled)
- OpenAI API key optional and not required for basic functionality
```