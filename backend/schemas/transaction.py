from pydantic import BaseModel
from datetime import datetime

class TransactionBase(BaseModel):
    description: str
    amount: float
    type: str
    category: str
    status: str

    class Config:
        from_attributes = True

class TransactionOut(TransactionBase):
    id: int
    date: datetime
