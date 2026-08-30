```markdown
# Technical Specification: Vehicle Buy Assistant

## Overview

A multi-agent AI system for personalized car recommendations. Built on Agent Kernel framework.

**Version:** 1.0.0
**Status:** Production-ready for competition

---

## System Requirements

### Software Requirements
- Python 3.12 or 3.13
- Agent Kernel 0.2.10+
- pip 24.0+

### Hardware Requirements
- Minimum: 2GB RAM
- Recommended: 4GB RAM
- Storage: 100MB

---

## Data Models

### Vehicle Object
```json
{
  "id": 1,
  "make": "Toyota",
  "model": "RAV4",
  "year": 2024,
  "type": "SUV",
  "price": 29500,
  "mpg": 28,
  "safety_rating": 5,
  "features": ["Backup Camera", "Adaptive Cruise"],
  "description": "Reliable family SUV"
}
```

### User Preferences
```json
{
  "budget": "under $30,000",
  "type": "SUV",
  "usage": "family",
  "features": "good safety features"
}
```

### Recommendation Result
```json
{
  "vehicle": {
    "make": "Toyota",
    "model": "RAV4",
    "price": 29500
  },
  "score": 8.5,
  "matches": ["Within budget", "Matches SUV"],
  "pros": ["High safety rating", "Good fuel efficiency"],
  "cons": ["Slightly above base model"],
  "summary": "Best overall choice for families"
}
```

---

## API Specifications

### Search Vehicles
**Endpoint:** `search_vehicles(preferences, vehicles)`

**Input:**
```python
preferences = {
    "budget": "under $30,000",
    "type": "SUV",
    "usage": "family",
    "features": "safety"
}
```

**Output:**
```python
[
    {
        "vehicle": {...},
        "score": 8.5,
        "matches": ["Within budget", "Matches SUV"]
    }
]
```

### Calculate EMI
**Endpoint:** `calculate_emi(price, down_payment, interest_rate, tenure)`

**Input:**
```python
price = 29500
down_payment = 5900  # 20%
interest_rate = 5.0  # 5% APR
tenure = 60  # months
```

**Output:**
```python
449.58  # Monthly EMI
```

---

## Agent Specifications

### Profile Agent
**Class:** `ProfileAgent`
**File:** `agents/profile_agent.py`
**Inherits:** `Agent`

**Abstract Methods Implemented:**
- `get_a2a_card()` - Returns agent metadata
- `get_description()` - Returns agent description

**Key Methods:**
- `run(session, request)` - Process user input
- `_extract_preferences(text)` - Parse user input

---

### Market Agent
**Class:** `MarketAgent`
**File:** `agents/market_agent.py`
**Inherits:** `Agent`

**Key Methods:**
- `search(preferences)` - Search vehicle database
- `_filter_by_budget(vehicles, budget)` - Filter by price
- `_filter_by_type(vehicles, type)` - Filter by vehicle type

---

### Recommendation Agent
**Class:** `RecommendationAgent`
**File:** `agents/recommendation_agent.py`
**Inherits:** `Agent`

**Key Methods:**
- `rank(vehicles, preferences)` - Score and rank vehicles
- `_calculate_score(vehicle, preferences)` - Calculate match score
- `_generate_pros_cons(vehicle, preferences)` - Generate explanation

---

## Tool Specifications

### Vehicle Search Tool
**File:** `tools/vehicle_search.py`

**Functions:**
```python
def load_vehicles() -> List[dict]
    """Load vehicle database from JSON"""

def search_vehicles(preferences: dict) -> List[dict]
    """Search and filter vehicles by preferences"""

def get_vehicle_details(vehicle_id: int) -> dict
    """Get full details for a specific vehicle"""
```

### Financing Tool
**File:** `tools/financing.py`

**Functions:**
```python
def calculate_emi(price: float, down: float, rate: float, tenure: int) -> float
    """Calculate monthly EMI"""

def calculate_total_cost(price: float, rate: float, tenure: int) -> float
    """Calculate total cost including interest"""
```

---

## Interface Specifications

### CLI Interface
**File:** `interface/cli.py`

**Commands:**
- Natural language input
- `exit` or `quit` - Exit program

**Flow:**
1. Show welcome message
2. Collect preferences
3. Search and show results
4. Reset for new search

### WhatsApp Interface
**File:** `interface/whatsapp_app.py`

**Setup Requirements:**
- Twilio account
- WhatsApp Business API
- Phone number verification

**Message Flow:**
1. Receive user message
2. Process through agents
3. Send response

---

## Configuration

### Environment Variables
```bash
OPENAI_API_KEY=your-key-here  # Optional
AK_GUARDRAIL_ENABLED=false    # Optional
AK_TELEMETRY_ENABLED=false    # Optional
```

### config.yaml (Optional)
```yaml
agentkernel:
  guardrail:
    enabled: false
  telemetry:
    enabled: false
```

---

## Error Handling

### Common Errors and Solutions

| Error | Cause | Solution |
|-------|-------|----------|
| `ModuleNotFoundError` | Wrong directory | Run from `use-cases/vehicle_buy_assistant/` |
| `Session() missing id` | Missing session ID | Use `Session(id="...")` |
| `config.yaml` warning | Missing config file | Ignore or create empty file |
| Abstract method error | Incomplete class | Implement all abstract methods |

---

## Testing

### Manual Testing
```bash
# Test CLI
python interface/cli.py

# Test with sample input
python -c "from main import search_vehicles; print(search_vehicles({'budget': '30000'}, load_vehicles()))"
```

### Expected Outputs
- Budget < $30,000: Should return Toyota RAV4, Honda CR-V, Ford Escape
- Budget > $40,000: Should return Tesla Model Y
- SUV preference: Should prioritize SUVs
- Safety preference: Should prioritize vehicles with 4-5 star safety

---

## Deployment

### Local Deployment
```bash
python main.py
```

### WhatsApp Deployment
```bash
python interface/whatsapp_app.py
```

### Docker Deployment (Optional)
```dockerfile
FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["python", "main.py"]
```

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0.0 | 2024-08-25 | Initial release for IDEALIZE 2026 |

---

## License

This project is licensed under the Agent Kernel open-source license. See LICENSE file for details.

---

## Contact

For technical questions: kernel@yaala.ai
For competition questions: IDEALIZE 2026 organizing committee
```