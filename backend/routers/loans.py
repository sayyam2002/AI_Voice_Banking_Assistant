# backend/routers/loans.py
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from ..db.database import get_db
from ..db.models.loan import Loan
from .auth import get_current_user
from typing import List

router = APIRouter()

@router.get("/info", summary="List available loan products")
async def list_loans(db: AsyncSession = Depends(get_db)):
    q = select(Loan)
    res = await db.execute(q)
    loans = res.scalars().all()
    return [{"loan_type": l.loan_type, "interest_rate": l.interest_rate, "min_amount": l.min_amount, "max_amount": l.max_amount, "tenure": l.tenure} for l in loans]

@router.get("/{loan_type}", summary="Get loan details")
async def get_loan_details(loan_type: str, db: AsyncSession = Depends(get_db)):
    q = select(Loan).where(Loan.loan_type == loan_type)
    res = await db.execute(q)
    loan = res.scalars().first()
    if not loan:
        raise HTTPException(404, "Loan type not found")
    return {"loan_type": loan.loan_type, "interest_rate": loan.interest_rate, "min_amount": loan.min_amount, "max_amount": loan.max_amount, "tenure": loan.tenure}
