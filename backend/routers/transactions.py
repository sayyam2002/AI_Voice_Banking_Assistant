# backend/routers/transactions.py
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from typing import List, Optional

from ..db.database import get_db
from ..db.models.transaction import Transaction
from ..schemas.user import AccountOut  # reuse or create a Transaction schema if you prefer
from .auth import get_current_user

router = APIRouter()

@router.get("/", summary="List transactions for current user")
async def list_transactions(
    limit: int = Query(50, le=500),
    offset: int = Query(0, ge=0),
    current_user = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    q = select(Transaction).where(Transaction.user_id == current_user.id).order_by(desc(Transaction.date)).limit(limit).offset(offset)
    res = await db.execute(q)
    txs = res.scalars().all()
    # convert Decimal to float for amounts if needed in serialization
    def tx_to_dict(tx):
        return {
            "id": tx.id,
            "date": tx.date.isoformat() if tx.date else None,
            "description": tx.description,
            "amount": float(tx.amount),
            "type": tx.type,
            "category": tx.category,
            "status": tx.status
        }
    return [tx_to_dict(t) for t in txs]

@router.get("/{transaction_id}", summary="Get single transaction")
async def get_transaction(transaction_id: int, current_user=Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    q = select(Transaction).where(Transaction.id == transaction_id, Transaction.user_id == current_user.id)
    res = await db.execute(q)
    tx = res.scalars().first()
    if not tx:
        raise HTTPException(404, "Transaction not found")
    return {
        "id": tx.id,
        "date": tx.date.isoformat() if tx.date else None,
        "description": tx.description,
        "amount": float(tx.amount),
        "type": tx.type,
        "category": tx.category,
        "status": tx.status
    }
