from fastapi import FastAPI, HTTPException, Depends, Header, File, UploadFile
from pydantic import BaseModel
from typing import Optional, List
from fastapi.middleware.cors import CORSMiddleware
from speechbrain.inference.speaker import SpeakerRecognition
import torchaudio
import torch
import os
import httpx
from datetime import datetime, timedelta
import random

# --- Load Model ---
print("Loading speaker verification model...")
speaker_verification_model = SpeakerRecognition.from_hparams(
    source="speechbrain/spkrec-ecapa-voxceleb", 
    savedir="pretrained_models/spkrec-ecapa-voxceleb"
)
print("✓ Speaker model loaded successfully")

app = FastAPI(title="NeoBank Advanced API", version="3.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Models ---
class UserLogin(BaseModel):
    username: str
    password: str

class TransferBody(BaseModel):
    recipient: str
    amount: float
    currency: str = "USD"
    pin: str

class NluRequest(BaseModel):
    text: str

class PinVerification(BaseModel):
    pin: str

class BillPayment(BaseModel):
    biller: str
    amount: float
    account_number: str

# --- Enhanced Mock Database ---
MOCK_DB = {
    "user123": {
        "password": "password123",
        "username": "user123",
        "full_name": "Alex Johnson",
        "email": "alex.johnson@email.com",
        "phone": "+1-555-0123",
        "voice_embedding": None,
        "pin": "1234",
        "accounts": [
            {
                "account_id": "ACC001",
                "account_type": "checking",
                "balance": 5230.50,
                "currency": "USD",
                "account_number": "****5678"
            },
            {
                "account_id": "ACC002",
                "account_type": "savings",
                "balance": 12450.00,
                "currency": "USD",
                "account_number": "****9012"
            }
        ],
        "transactions": [
            {
                "id": "TXN001",
                "date": "2025-11-19",
                "description": "Salary Deposit",
                "amount": 3500.00,
                "type": "credit",
                "category": "Income",
                "status": "completed"
            },
            {
                "id": "TXN002",
                "date": "2025-11-18",
                "description": "Amazon Purchase",
                "amount": -89.99,
                "type": "debit",
                "category": "Shopping",
                "status": "completed"
            },
            {
                "id": "TXN003",
                "date": "2025-11-17",
                "description": "Starbucks",
                "amount": -5.75,
                "type": "debit",
                "category": "Food & Dining",
                "status": "completed"
            },
            {
                "id": "TXN004",
                "date": "2025-11-16",
                "description": "Electric Bill",
                "amount": -125.00,
                "type": "debit",
                "category": "Utilities",
                "status": "completed"
            },
            {
                "id": "TXN005",
                "date": "2025-11-15",
                "description": "Transfer from Savings",
                "amount": 500.00,
                "type": "credit",
                "category": "Transfer",
                "status": "completed"
            }
        ],
        "beneficiaries": ["John Doe", "Jane Smith", "Mom", "Dad"],
        "cards": [
            {
                "card_number": "****4532",
                "card_type": "Debit",
                "expiry": "12/26",
                "status": "active"
            }
        ]
    }
}

MOCK_LOANS = [
    {
        "loan_type": "personal",
        "interest_rate": 5.5,
        "min_amount": 1000,
        "max_amount": 50000,
        "tenure": "1-5 years"
    },
    {
        "loan_type": "home",
        "interest_rate": 3.8,
        "min_amount": 50000,
        "max_amount": 500000,
        "tenure": "5-30 years"
    },
    {
        "loan_type": "auto",
        "interest_rate": 4.2,
        "min_amount": 5000,
        "max_amount": 75000,
        "tenure": "1-7 years"
    }
]

# --- Security ---
async def get_current_user(authorization: str = Header(...)):
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid authorization scheme")
    token = authorization.split(" ")[1]
    if token == "MOCK_TOKEN_FOR_USER123":
        return MOCK_DB["user123"]
    raise HTTPException(status_code=401, detail="Invalid token")

# --- Authentication Endpoints ---

@app.post("/auth/login")
def login(user: UserLogin):
    """User login with username and password"""
    db_user = MOCK_DB.get(user.username)
    if not db_user or db_user["password"] != user.password:
        raise HTTPException(status_code=400, detail="Incorrect username or password")
    
    return {
        "access_token": "MOCK_TOKEN_FOR_USER123",
        "token_type": "bearer",
        "user": {
            "username": db_user["username"],
            "full_name": db_user["full_name"],
            "email": db_user["email"]
        }
    }

@app.post("/auth/enroll-voice")
async def enroll_voice(
    file1: UploadFile = File(...), 
    file2: UploadFile = File(...), 
    file3: UploadFile = File(...),
    user_data: dict = Depends(get_current_user)
):
    """Enroll user's voice biometric"""
    try:
        embeddings = []
        for i, file in enumerate([file1, file2, file3]):
            temp_path = f"temp_enroll_{i}.wav"
            with open(temp_path, "wb") as f:
                f.write(await file.read())
            
            waveform, sample_rate = torchaudio.load(temp_path)
            if sample_rate != 16000:
                waveform = torchaudio.functional.resample(waveform, sample_rate, 16000)
            
            # Normalize audio
            waveform = waveform / (torch.max(torch.abs(waveform)) + 1e-8)
            
            emb = speaker_verification_model.encode_batch(waveform)
            embeddings.append(emb)
            os.remove(temp_path)

        avg_emb = torch.mean(torch.stack(embeddings), dim=0)
        user_data["voice_embedding"] = avg_emb.squeeze().tolist()
        
        print(f"✓ Voice enrolled for user: {user_data['username']}")
        return {
            "status": "success",
            "message": "Voice enrolled successfully",
            "enrolled_at": datetime.now().isoformat()
        }

    except Exception as e:
        print(f"✗ Enrollment error: {e}")
        raise HTTPException(status_code=500, detail=f"Enrollment failed: {str(e)}")

@app.post("/auth/verify-voice")
async def verify_voice(
    file: UploadFile = File(...),
    user_data: dict = Depends(get_current_user)
):
    """Verify user's voice against enrolled biometric"""
    if not user_data["voice_embedding"]:
        raise HTTPException(
            status_code=400,
            detail="No voice ID found. Please enroll first."
        )

    try:
        temp_path = "temp_verify.wav"
        with open(temp_path, "wb") as f:
            f.write(await file.read())

        waveform, sample_rate = torchaudio.load(temp_path)
        if sample_rate != 16000:
            waveform = torchaudio.functional.resample(waveform, sample_rate, 16000)
        
        # Normalize audio
        waveform = waveform / (torch.max(torch.abs(waveform)) + 1e-8)
        
        new_emb = speaker_verification_model.encode_batch(waveform)
        stored_emb = torch.tensor(user_data["voice_embedding"]).unsqueeze(0).unsqueeze(0)
        
        score = speaker_verification_model.similarity(new_emb, stored_emb)
        score_val = score.item()
        os.remove(temp_path)
        
        # Threshold: 0.15 for more permissive verification
        threshold = 0.15
        is_match = score_val > threshold
        
        print(f"Voice verification | Score: {score_val:.4f} | Threshold: {threshold} | Match: {is_match}")

        if is_match:
            return {
                "status": "success",
                "message": "Voice verified successfully",
                "score": round(score_val, 4),
                "confidence": "high" if score_val > 0.3 else "medium"
            }
        else:
            raise HTTPException(
                status_code=401,
                detail=f"Voice verification failed. Similarity score: {score_val:.3f}"
            )

    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        print(f"✗ Verification error: {e}")
        raise HTTPException(status_code=500, detail="Verification error occurred")

@app.post("/auth/verify-pin")
def verify_pin(pin_data: PinVerification, user_data: dict = Depends(get_current_user)):
    """Verify user's PIN"""
    if pin_data.pin == user_data["pin"]:
        return {
            "status": "success",
            "message": "PIN verified successfully"
        }
    else:
        raise HTTPException(status_code=401, detail="Incorrect PIN")

# --- Account Management Endpoints ---

@app.get("/accounts/balance")
def get_balance(user_data: dict = Depends(get_current_user)):
    """Get all account balances"""
    return user_data["accounts"]

@app.get("/accounts/{account_id}")
def get_account_details(account_id: str, user_data: dict = Depends(get_current_user)):
    """Get specific account details"""
    account = next((acc for acc in user_data["accounts"] if acc["account_id"] == account_id), None)
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")
    return account

@app.get("/accounts/history")
def get_history(user_data: dict = Depends(get_current_user)):
    """Get transaction history"""
    return user_data["transactions"]

@app.get("/transactions/{transaction_id}")
def get_transaction(transaction_id: str, user_data: dict = Depends(get_current_user)):
    """Get specific transaction details"""
    txn = next((t for t in user_data["transactions"] if t["id"] == transaction_id), None)
    if not txn:
        raise HTTPException(status_code=404, detail="Transaction not found")
    return txn

# --- Transfer & Payment Endpoints ---

@app.post("/transfer")
def make_transfer(transfer: TransferBody, user_data: dict = Depends(get_current_user)):
    """Execute money transfer with PIN verification"""
    # Verify PIN server-side
    if transfer.pin != user_data["pin"]:
        raise HTTPException(status_code=401, detail="Invalid PIN for transfer")

    primary = user_data["accounts"][0]
    
    if primary["balance"] < transfer.amount:
        raise HTTPException(status_code=400, detail="Insufficient funds")
    
    # Process transfer
    primary["balance"] -= transfer.amount
    
    # Add transaction record
    new_transaction = {
        "id": f"TXN{random.randint(100, 999)}",
        "date": datetime.now().strftime("%Y-%m-%d"),
        "description": f"Transfer to {transfer.recipient}",
        "amount": -transfer.amount,
        "type": "debit",
        "category": "Transfer",
        "status": "completed"
    }
    user_data["transactions"].insert(0, new_transaction)
    
    print(f"✓ Transfer completed: ${transfer.amount} to {transfer.recipient}")
    
    return {
        "status": "success",
        "message": f"Transferred {transfer.currency} {transfer.amount} to {transfer.recipient}",
        "new_balance": primary["balance"],
        "transaction_id": new_transaction["id"],
        "timestamp": datetime.now().isoformat()
    }

@app.get("/beneficiaries")
def get_beneficiaries(user_data: dict = Depends(get_current_user)):
    """Get list of saved beneficiaries"""
    return {"beneficiaries": user_data["beneficiaries"]}

@app.post("/beneficiaries")
def add_beneficiary(name: str, user_data: dict = Depends(get_current_user)):
    """Add new beneficiary"""
    if name not in user_data["beneficiaries"]:
        user_data["beneficiaries"].append(name)
    return {"status": "success", "beneficiaries": user_data["beneficiaries"]}

# --- Loan Endpoints ---

@app.get("/loans/info")
def get_loans():
    """Get available loan products"""
    return MOCK_LOANS

@app.get("/loans/{loan_type}")
def get_loan_details(loan_type: str):
    """Get specific loan product details"""
    loan = next((l for l in MOCK_LOANS if l["loan_type"] == loan_type), None)
    if not loan:
        raise HTTPException(status_code=404, detail="Loan type not found")
    return loan

# --- NLU Integration ---

@app.post("/detect-intent")
async def detect_intent(request: NluRequest):
    """Detect user intent from natural language"""
    try:
        # Call Rasa NLU
        async with httpx.AsyncClient() as client:
            rasa_response = await client.post(
                "http://localhost:5005/model/parse",
                json={"text": request.text}
            )
            nlu_data = rasa_response.json()

        intent = nlu_data.get("intent", {}).get("name", "fallback")
        entities = nlu_data.get("entities", [])
        confidence = nlu_data.get("intent", {}).get("confidence", 0)
        
        # Parse entities
        params = {}
        for entity in entities:
            params[entity["entity"]] = entity["value"]

        # Generate responses
        responses = {
            "greet": "Hello! I'm your AI banking assistant. How can I help you today?",
            "goodbye": "Goodbye! Have a secure day.",
            "check_balance": "Let me check your balance for you.",
            "get_history": "Retrieving your recent transactions...",
            "ask_loan": "I can help you explore our loan options.",
            "transfer_funds": "I'll help you transfer money securely.",
            "fallback": "I didn't quite understand that. Could you rephrase?"
        }
        
        response_text = responses.get(intent, "Processing your request...")
        
        # Refine transfer response
        if intent == "transfer_funds":
            if "amount" not in params or "person" not in params:
                response_text = "Please specify the recipient and amount for the transfer."

        return {
            "intent": intent,
            "parameters": params,
            "confidence": round(confidence, 3),
            "response_text": response_text
            }
        
    except Exception as e:
        print(f"✗ NLU Error: {e}")
        raise HTTPException(status_code=500, detail=f"NLU service error: {str(e)}")

# --- User Profile ---

@app.get("/profile")
def get_profile(user_data: dict = Depends(get_current_user)):
    """Get user profile information"""
    return {
        "username": user_data["username"],
        "full_name": user_data["full_name"],
        "email": user_data["email"],
        "phone": user_data["phone"],
        "voice_enrolled": user_data["voice_embedding"] is not None,
        "accounts_count": len(user_data["accounts"]),
        "cards": user_data["cards"]
    }

# --- Health Check ---

@app.get("/health")
def health_check():
    """API health check"""
    return {
        "status": "healthy",
        "service": "NeoBank Advanced API",
        "version": "3.0.0",
        "voice_auth": "enabled",
        "timestamp": datetime.now().isoformat()
    }