# backend/db/models/account.py
from sqlalchemy import Column, Integer, String, Numeric, ForeignKey
from sqlalchemy.orm import relationship
from ..database import Base

class Account(Base):
    __tablename__ = "accounts"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"))
    account_type = Column(String(32))
    balance = Column(Numeric(12,2), default=0)
    currency = Column(String(8), default="USD")
    account_number = Column(String(32), unique=True)

    owner = relationship("User", back_populates="accounts")
