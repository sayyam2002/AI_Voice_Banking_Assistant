# backend/schemas/user.py
from pydantic import BaseModel, EmailStr
from typing import Optional, List

class AccountOut(BaseModel):
    id: int
    account_type: str
    balance: float
    currency: str
    account_number: str

    class Config:
        orm_mode = True

class UserCreate(BaseModel):
    username: str
    password: str
    full_name: Optional[str]
    email: Optional[EmailStr]

class UserOut(BaseModel):
    id: int
    username: str
    full_name: Optional[str]
    email: Optional[EmailStr]
    accounts: Optional[List[AccountOut]] = []

    class Config:
        orm_mode = True
