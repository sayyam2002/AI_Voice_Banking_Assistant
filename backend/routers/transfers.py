# backend/routers/transfers.py
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, insert
from sqlalchemy.exc import SQLAlchemyError
from decimal import Decimal
from ..db.database import get_db
from ..db.models.user import User
from ..db.models.account import Account
from ..db.models.transaction import Transaction
from ..core.security import verify_password
from .auth import get_current_user
from typing import Dict

router = APIRouter()

class TransferBody(BaseModel):
    recipient: str
    amount: float
    currency: str = "USD"
    pin: str

@router.post("/", summary="Make a money transfer")
async def make_transfer(body: TransferBody, current_user = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    # Validate PIN
    if not current_user.pin_hash:
        raise HTTPException(400, "PIN not set. Please set PIN before transfers.")
    if not verify_password(body.pin, current_user.pin_hash):
        raise HTTPException(401, "Invalid PIN")

    # Use primary account (first) as sender
    q = select(Account).where(Account.user_id == current_user.id).limit(1)
    res = await db.execute(q)
    sender = res.scalars().first()
    if not sender:
        raise HTTPException(404, "Sender account not found")

    amount_dec = Decimal(str(body.amount))

    if sender.balance < amount_dec:
        raise HTTPException(400, "Insufficient funds")

    try:
        # Start transactional update
        # debit sender
        new_balance = Decimal(sender.balance) - amount_dec
        stmt = update(Account).where(Account.id == sender.id).values(balance=new_balance)
        await db.execute(stmt)

        # create transaction record (debit)
        new_tx = Transaction(
            user_id = current_user.id,
            description = f"Transfer to {body.recipient}",
            amount = -amount_dec,
            type = "debit",
            category = "Transfer",
            status = "completed"
        )
        db.add(new_tx)

        # commit the transaction
        await db.commit()

        return {
            "status": "success",
            "message": f"Transferred {body.currency} {body.amount} to {body.recipient}",
            "new_balance": float(new_balance),
            "transaction_id": new_tx.id
        }
    except SQLAlchemyError as e:
        await db.rollback()
        raise HTTPException(500, f"Transfer failed: {str(e)}")
