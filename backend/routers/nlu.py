# backend/routers/nlu.py
from fastapi import APIRouter, HTTPException
import httpx
from pydantic import BaseModel

router = APIRouter()

class NluRequest(BaseModel):
    text: str

@router.post("/detect-intent")
async def detect_intent(payload: NluRequest):
    """
    Proxy to Rasa NLU (expects Rasa server running at http://localhost:5005).
    Returns a normalized structure: {intent, confidence, parameters, response_text (optional)}
    """
    rasa_url = "http://localhost:5005/model/parse"
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(rasa_url, json={"text": payload.text})
            resp.raise_for_status()
            data = resp.json()
    except Exception as e:
        raise HTTPException(502, f"NLU service error: {e}")

    intent = data.get("intent", {}).get("name", "fallback")
    confidence = data.get("intent", {}).get("confidence", 0.0)
    entities = data.get("entities", [])

    params = {}
    for ent in entities:
        params[ent.get("entity")] = ent.get("value")

    # Basic mapping to friendly response_text; you can customize or call a response generator later
    response_text = None
    if intent == "greet":
        response_text = "Hello! I'm your AI banking assistant."
    elif intent == "goodbye":
        response_text = "Goodbye!"
    elif intent == "check_balance":
        response_text = "Let me check your balance."
    elif intent == "get_history":
        response_text = "Fetching your recent transactions..."
    elif intent == "ask_loan":
        response_text = "I can help with loan options."

    return {"intent": intent, "confidence": confidence, "parameters": params, "response_text": response_text}
