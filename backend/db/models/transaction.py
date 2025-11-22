# backend/db/models/transaction.py
from sqlalchemy import Column, Integer, String, Numeric, DateTime, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from ..database import Base

class Transaction(Base):
    __tablename__ = "transactions"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    date = Column(DateTime(timezone=True), server_default=func.now())
    description = Column(String(256))
    amount = Column(Numeric(12,2))
    type = Column(String(16))  # credit/debit
    category = Column(String(64))
    status = Column(String(32), default="completed")

    user = relationship("User", back_populates="transactions")
