from pydantic import BaseModel, ConfigDict, Field
from typing import Optional
from decimal import Decimal
from app.core.enums import LoanApplicationStep, LoanTenureMonths


class LoanApplicationCreateSchema(BaseModel):
    user_profile_id: int
    eligibility_id: int
    requested_tenure_months: LoanTenureMonths

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "user_profile_id": "",
                "eligibility_id": "",
                "requested_tenure_months": 3
            }
        }
    )


class LoanApplicationCreateResponseSchema(BaseModel):
    application_id: int
    next_step: LoanApplicationStep


class LoanApplicationUpdateSchema(BaseModel):
    interest_rate: Optional[Decimal] = None
    monthly_emi: Optional[Decimal] = None
    processing_fee: Optional[Decimal] = None
    gst_amount: Optional[Decimal] = None
    total_repayment: Optional[Decimal] = None
    lender_name: Optional[str] = None
    current_step: Optional[str] = None


class LoanSubmitRequestSchema(BaseModel):
    confirm: bool


class LoanSubmitResponseSchema(BaseModel):
    reference_number: str
    message: str
    expected_decision_time: str

    class Config:
        from_attributes = True


class LoanApplicationResponseSchema(BaseModel):
    application_id: int
    application_status: str
    approved_amount: Decimal
    requested_tenure_months: int
    interest_rate: Optional[Decimal] = None