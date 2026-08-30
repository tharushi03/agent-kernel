# agents/profile_agent.py
from agentkernel import Agent, Session
from agentkernel.core import AgentRequestText

class ProfileAgent(Agent):
    """
    Collects user's car preferences.
    """
    
    def __init__(self):
        super().__init__(
            name="ProfileAgent",
            instructions="""
            You are a friendly car buying assistant.
            Ask the user about:
            1. Budget
            2. Vehicle type (SUV, Sedan, Truck)
            3. Primary use (commuting, family)
            4. Must-have features
            """
        )
    
    async def run(self, session: Session, request: AgentRequestText):
        # Get user's message
        user_input = request.text
        
        # Get memory (session cache)
        nv_cache = session.get_non_volatile_cache()
        preferences = nv_cache.get("car_preferences", {})
        
        # Simple response logic
        if "budget" in user_input.lower():
            preferences['budget'] = user_input
            nv_cache.set("car_preferences", preferences)
            return "Great! What type of vehicle do you prefer? (SUV, Sedan, Truck, or Electric?)"
        
        elif "suv" in user_input.lower() or "sedan" in user_input.lower() or "truck" in user_input.lower():
            preferences['type'] = user_input
            nv_cache.set("car_preferences", preferences)
            return "Thanks! What will you use the car for? (commuting, family, off-road, or business?)"
        
        elif "commuting" in user_input.lower() or "family" in user_input.lower():
            preferences['usage'] = user_input
            nv_cache.set("car_preferences", preferences)
            return "Perfect! Any must-have features? (backup camera, adaptive cruise, safety features, etc.)"
        
        else:
            return "Tell me more about what you're looking for in a car. What's your budget?"