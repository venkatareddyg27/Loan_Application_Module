from pydantic import BaseModel, Field, ConfigDict
from typing import Optional
from app.core.enums import LoanPurpose


class LoanApplicationPurposeCreate(BaseModel):
    purpose_code: LoanPurpose
    purpose_description: Optional[str] = Field(
        default=None,
        max_length=500)
    
    
class LoanApplicationPurposeUpdate(BaseModel):
    purpose_code: Optional[LoanPurpose] = None
    purpose_description: Optional[str] = Field(
        default=None,
        max_length=500)
    
class LoanApplicationPurposeResponse(BaseModel):
    purpose_code: LoanPurpose
    purpose_description: Optional[str]
    model_config = ConfigDict(from_attributes=True)

class LoanPurposeSummary(BaseModel):
    purpose_code: LoanPurpose
    purpose_description: Optional[str]


