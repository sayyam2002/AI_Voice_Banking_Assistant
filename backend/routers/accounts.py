# backend/routers/accounts.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List

from ..db.database import get_db
from ..db.models.account import Account
from ..schemas.user import AccountOut
from .auth import get_current_user

router = APIRouter()

@router.get("/balance", response_model=List[AccountOut])
async def get_balances(current_user = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """
    Return all accounts for the current user.
    """
    q = select(Account).where(Account.user_id == current_user.id)
    res = await db.execute(q)
    accounts = res.scalars().all()
    return accounts

@router.get("/{account_id}", response_model=AccountOut)
async def get_account_details(account_id: int, current_user = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    q = select(Account).where(Account.id == account_id, Account.user_id == current_user.id)
    res = await db.execute(q)
    acc = res.scalars().first()
    if not acc:
        raise HTTPException(404, "Account not found")
    return acc
