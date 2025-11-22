from pydantic import BaseModel

class AccountBase(BaseModel):
    account_type: str
    balance: float
    currency: str
    account_number: str

    class Config:
        from_attributes = True

class AccountOut(AccountBase):
    id: int
