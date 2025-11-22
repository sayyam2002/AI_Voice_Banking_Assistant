# backend/app.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .routers import auth, accounts, transactions, loans, nlu, voice, transfers
from .core.config import settings

app = FastAPI(title=settings.PROJECT_NAME)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# routers


app.include_router(auth.router, prefix="/auth", tags=["auth"])
app.include_router(accounts.router, prefix="/accounts", tags=["accounts"])
app.include_router(transactions.router, prefix="/transactions", tags=["transactions"])
app.include_router(loans.router, prefix="/loans", tags=["loans"])
app.include_router(transfers.router, prefix="/transfer", tags=["transfer"])
app.include_router(nlu.router, prefix="/nlu", tags=["nlu"])
app.include_router(voice.router, prefix="/voice", tags=["voice"])
