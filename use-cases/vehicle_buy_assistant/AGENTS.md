# Agent Documentation: Vehicle Buy Assistant

## Architecture Overview

The Vehicle Buy Assistant uses a multi-agent orchestration pattern where a supervisor routes user requests to specialized agents.

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

Purpose: Collect user preferences through conversation.

### 2. Market Agent (`agents/market_agent.py`)

Purpose: Search for vehicles matching user preferences.

### 3. Recommendation Agent (`agents/recommendation_agent.py`)

Purpose: Rank vehicles and provide explainable recommendations.

---

## Memory Management

### Non-Volatile Cache
Stores user preferences across sessions.

### Volatile Cache
Stores temporary data for current request.

---

## Tools Used

### Vehicle Database Tool
- Path: `tools/vehicle_search.py`
- Purpose: Load and search the vehicle database

---

## Integration Points

### WhatsApp Interface
- File: `interface/whatsapp_app.py`
- Integration: Uses Agent Kernel's WhatsApp support

### CLI Interface
- File: `main.py`
- Purpose: Testing and demonstration
