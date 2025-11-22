# backend/db/models/loan.py
from sqlalchemy import Column, Integer, String, Float
from ..database import Base

class Loan(Base):
    __tablename__ = "loans"
    id = Column(Integer, primary_key=True)
    loan_type = Column(String(32), unique=True)
    interest_rate = Column(Float)
    min_amount = Column(Integer)
    max_amount = Column(Integer)
    tenure = Column(String(64))
