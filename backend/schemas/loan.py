from pydantic import BaseModel

class LoanBase(BaseModel):
    loan_type: str
    interest_rate: float
    min_amount: int
    max_amount: int
    tenure: str

    class Config:
        from_attributes = True

class LoanOut(LoanBase):
    id: int
