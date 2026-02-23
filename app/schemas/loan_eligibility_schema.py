from pydantic import BaseModel, Field
from decimal import Decimal
from datetime import datetime
from typing import Optional
from app.core.enums import EligibilityStatusEnum


class LoanEligibilityCheckSchema(BaseModel):
    user_profile_id: int
    requested_amount: Decimal = Field(
        ...,
        gt=0,
        description="Requested loan amount")
    requested_tenure_months: int = Field(
        ...,
        description="Tenure in months (3, 6, 9, or 12)")
    existing_emi: Optional[Decimal] = Field(
        default=Decimal("0"),
        ge=0,
        description="Existing EMI obligations per month")

    class Config:
        from_attributes = True


class LoanEligibilityResponseSchema(BaseModel):
    id: int
    user_profile_id: int

    # ── Income & EMI Details ──
    income_used: Optional[Decimal] = None
    existing_emi: Optional[Decimal] = None
    proposed_emi: Optional[Decimal] = None

    # ── FOIR Details ──
    foir_ratio: Optional[Decimal] = None
    max_allowed_foir: Optional[Decimal] = None

    # ── Credit Details ──
    credit_score_used: Optional[int] = None
    bureau_name: Optional[str] = None

    # ── Eligibility Result ──
    eligibility_status: EligibilityStatusEnum
    max_eligible_amount: Optional[Decimal] = None
    max_eligible_emi: Optional[Decimal] = None
    failure_reason: Optional[str] = None

    # ── Timestamp ──
    latest_checked_at: datetime

    class Config:
        from_attributes = True


class LoanEligibilityWithCalculatorSchema(BaseModel):

    # ── Eligibility ──
    eligibility: LoanEligibilityResponseSchema

    # ── Calculator Summary from loan_calculator.py ──
    loan_amount: float
    tenure_months: int
    interest_rate: float
    emi: float
    total_emi_paid: float
    processing_fee: float
    gst_on_processing_fee: float
    total_processing_charges: float
    total_customer_outflow: float

    class Config:
        from_attributes = True