from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from ..database import Base

class Beneficiary(Base):
    __tablename__ = "beneficiaries"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"))
    name = Column(String(128), nullable=False)
    account_number = Column(String(32), nullable=False)
    bank_name = Column(String(128), nullable=True)
    
    # owner relationship (optional)
    user = relationship("User", back_populates="beneficiaries", lazy="selectin")
