from pydantic import BaseModel, Field
from decimal import Decimal


class PreDisbursementResponseSchema(BaseModel):

    application_id: int

    lender_name: str | None = Field(
        None,
        description="Name of the lender approving the loan"
    )

    approved_amount: Decimal = Field(
        ...,
        description="Approved loan amount"
    )

    tenure_months: int
    interest_rate_percent: Decimal
    emi_amount: Decimal
    total_repayment: Decimal
    processing_fee: Decimal
    gst_on_processing_fee: Decimal
    total_processing_charges: Decimal
    net_disbursement_amount: Decimal

    class Config:
        from_attributes = True