from pydantic import BaseModel, condecimal, conint
from enum import Enum

class LoanPurpose(str, Enum):
    EDUCATION = "EDUCATION"
    BUSINESS = "BUSINESS"
    EMERGENCY = "EMERGENCY"
    OTHER = "OTHER"

class LoanSchema(BaseModel):
    client_id: str
    amount: condecimal(gt=0, le=1000000)  # Max 1,000,000 HTG
    duration_days: conint(gt=0, le=365)   # Max 1 an
    purpose: LoanPurpose
