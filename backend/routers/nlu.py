import json
import google.generativeai as genai
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from ..core.config import settings

router = APIRouter()

# Configure Gemini
genai.configure(api_key=settings.GEMINI_API_KEY)

# We use gemini-1.5-flash for low latency, formatted strictly as JSON
model = genai.GenerativeModel(
    model_name="gemini-2.5-flash",
    generation_config={"response_mime_type": "application/json"},
)

class NluRequest(BaseModel):
    text: str

@router.post("/detect-intent")
async def detect_intent(payload: NluRequest):
    """
    Uses Google Gemini to analyze text and return structured Intent/Entity data.
    Replaces the deprecated Rasa local server.
    """
    try:
        # 1. Construct the System Prompt
        # We tell Gemini exactly how to map user text to intents and parameters
        prompt = f"""
        You are the NLU engine for a Banking App.
        Analyze the following user input: "{payload.text}"

        Your task is to extract the INTENT and PARAMETERS.

        Allowed Intents:
        - greet (e.g., "Hi", "Hello")
        - goodbye (e.g., "Bye", "See you")
        - check_balance (e.g., "How much money do I have?", "Check balance")
        - get_history (e.g., "Show recent transactions", "Last 5 expenses")
        - ask_loan (e.g., "I need a loan", "Loan rates")
        - transfer_money (e.g., "Send 500 to John", "Transfer money")
        - set_pin (e.g., "I want to change my pin")
        - fallback (if the input makes no sense or is unrelated to banking)

        Output Schema (JSON only):
        {{
            "intent": "string",
            "confidence": float (0.0 to 1.0),
            "parameters": {{
                "recipient": "string (optional)",
                "amount": "number (optional)",
                "currency": "string (optional, default USD)"
            }},
            "response_text": "A friendly, short natural language response acknowledging the request."
        }}
        """

        # 2. Call Gemini
        response = await model.generate_content_async(prompt)
        
        # 3. Parse the JSON result
        # Since we forced response_mime_type="application/json", proper JSON is guaranteed
        result_json = json.loads(response.text)

        return {
            "intent": result_json.get("intent", "fallback"),
            "confidence": result_json.get("confidence", 1.0),
            "parameters": result_json.get("parameters", {}),
            "response_text": result_json.get("response_text", "I'm not sure I understood that.")
        }

    except Exception as e:
        # Fallback if Gemini fails or times out
        print(f"Gemini NLU Error: {e}")
        return {
            "intent": "fallback", 
            "confidence": 0.0, 
            "parameters": {}, 
            "response_text": "System is currently unavailable. Please try again."
        }