# backend/db/models/user.py
from sqlalchemy import Column, Integer, String, JSON, DateTime
from sqlalchemy.sql import func
from ..database import Base
from sqlalchemy.orm import relationship
from .beneficiary import Beneficiary

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(64), unique=True, index=True, nullable=False)
    password_hash = Column(String(256), nullable=False)
    full_name = Column(String(128))
    email = Column(String(128), unique=True, index=True)
    phone = Column(String(32))
    pin_hash = Column(String(128))
    voice_embedding = Column(JSON, nullable=True)  # store numeric vector as JSON
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    accounts = relationship("Account", back_populates="owner", cascade="all, delete-orphan")
    transactions = relationship("Transaction", back_populates="user", cascade="all, delete-orphan")
    beneficiaries = relationship("Beneficiary", back_populates="user")