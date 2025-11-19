# main.py
from fastapi import FastAPI, HTTPException, Depends, Header
from pydantic import BaseModel      
from typing import Optional, List
from fastapi.middleware.cors import CORSMiddleware
from speechbrain.pretrained import SpeakerRecognition
from fastapi import File, UploadFile
import torchaudio
import os

# --- Load the Speaker Recognition Model (globally) ---
# This will download the model the first time it's run
print("Loading speaker verification model...")
speaker_verification_model = SpeakerRecognition.from_hparams(
    source="speechbrain/spkrec-ecapa-voxceleb", 
    savedir="pretrained_models/spkrec-ecapa-voxceleb"
)
print("Speaker model loaded.")

# --- Create the FastAPI app ---
app = FastAPI(
    title="Mock Banking API",
    description="A secure mock API for the AI Voice Assistant",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins (e.g., http://localhost:8001)
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods (POST, GET, OPTIONS)
    allow_headers=["*"],  # Allows all headers (Content-Type, Authorization)
)

# --- Pydantic Models (Data Validation) ---
class UserLogin(BaseModel):
    username: str
    password: str

class TransferBody(BaseModel):
    recipient: str
    amount: float
    currency: str = "USD"

class Balance(BaseModel):
    account_type: str
    balance: float
    currency: str

class HistoryItem(BaseModel):
    date: str
    description: str
    amount: float
    
class LoanInfo(BaseModel):
    loan_type: str
    interest_rate: float

# --- Mock Database ---
MOCK_DB = {
    "user123": {
        "password": "password123",
        "username": "user123",
        "full_name": "Alex Johnson",
        "accounts": [
            {"account_type": "checking", "balance": 5230.50, "currency": "USD"},
            {"account_type": "savings", "balance": 18400.00, "currency": "USD"}
        ],
        "history": [
            {"date": "2025-11-16", "description": "Starbucks", "amount": -5.75},
            {"date": "2025-11-15", "description": "Gas Station", "amount": -45.20},
            {"date": "2025-11-14", "description": "Paycheck Deposit", "amount": 2200.00}
        ]
    }
}

MOCK_LOANS = [
    {"loan_type": "personal", "interest_rate": 5.5},
    {"loan_type": "home", "interest_rate": 3.8},
    {"loan_type": "auto", "interest_rate": 4.2}
]

# --- Mock Security ---
# This is a simple "dependency" that checks for a valid mock token.
async def get_current_user(authorization: str = Header(...)):
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid authorization scheme")
    
    token = authorization.split(" ")[1]
    
    # In a real app, you'd validate a real JWT. Here, we just check our mock token.
    if token == "MOCK_TOKEN_FOR_USER123":
        return MOCK_DB["user123"]
    
    raise HTTPException(status_code=401, detail="Invalid token")

# --- API Endpoints ---

@app.get("/")
def read_root():
    return {"message": "Welcome to the Mock Banking API"}

@app.post("/auth/login", tags=["Authentication"])
def login(user: UserLogin):
    """
    Logs in a user and returns a mock JWT token.
    Use 'user123' and 'password123' to log in.
    """
    db_user = MOCK_DB.get(user.username)
    if not db_user or db_user["password"] != user.password:
        raise HTTPException(status_code=400, detail="Incorrect username or password")
    
    # In a real app, you would generate a JWT. We'll return a static mock token.
    return {"access_token": "MOCK_TOKEN_FOR_USER123", "token_type": "bearer"}

@app.get("/accounts/balance", tags=["Accounts"], response_model=List[Balance])
def get_balance(user_data: dict = Depends(get_current_user)):
    """
    Get all account balances for the authenticated user.
    """
    return user_data["accounts"]

@app.get("/accounts/history", tags=["Accounts"], response_model=List[HistoryItem])
def get_history(user_data: dict = Depends(get_current_user)):
    """
    Get transaction history for the authenticated user.
    """
    return user_data["history"]

@app.post("/transfer", tags=["Transactions"])
def make_transfer(transfer: TransferBody, user_data: dict = Depends(get_current_user)):
    """
    Simulates a fund transfer.
    """
    # Find the user's primary account and "deduct" the balance (simulated)
    primary_account = user_data["accounts"][0]
    if primary_account["balance"] < transfer.amount:
        raise HTTPException(status_code=400, detail="Insufficient funds")
    
    # In a real app, we'd update the DB. Here, we just return success.
    return {
        "status": "success",
        "message": f"Transferred {transfer.amount} {transfer.currency} to {transfer.recipient}",
        "new_balance": primary_account["balance"] - transfer.amount
    }

@app.get("/loans/info", tags=["Public"], response_model=List[LoanInfo])
def get_loan_info():
    """
    Get general information about available loan products. No auth required.
    """
    return MOCK_LOANS