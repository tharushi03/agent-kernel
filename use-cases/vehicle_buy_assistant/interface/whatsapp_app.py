# interface/whatsapp_app.py
import os
from agentkernel.api import RESTAPI
from agentkernel.openai import OpenAIModule
from agentkernel.whatsapp import AgentWhatsAppRequestHandler
from agents import Agent as OpenAIAgent

# --- Define your Vehicle Buy Assistant agent ---
# You can either reuse the same agent logic from your CLI,
# or create a simple version here. We'll create a fresh one.
vehicle_agent = OpenAIAgent(
    name="VehicleBuyAssistant",
    instructions="""
    You are a helpful car buying assistant.
    Help users find their perfect vehicle by asking about:
    1. Budget
    2. Vehicle type (SUV, Sedan, Truck, Electric, Hybrid)
    3. Primary use (commuting, family, off-road, business)
    4. Must-have features (safety, backup camera, etc.)
    
    Be conversational and friendly. Provide clear recommendations.
    """
)

# Register the agent with Agent Kernel
OpenAIModule([vehicle_agent])

if __name__ == "__main__":
    # Create WhatsApp handler – it reads credentials from environment variables
    whatsapp_handler = AgentWhatsAppRequestHandler()
    
    # Run the REST API server on port 8000
    # The webhook endpoint will be: http://localhost:8000/whatsapp/webhook
    RESTAPI.run([whatsapp_handler])