from pydantic import BaseModel
from app.core.enums import PayoutProviderEnum, PaymentModeEnum


class DisbursementRequestSchema(BaseModel):
    payment_mode: PaymentModeEnum
    payment_provider: PayoutProviderEnum


class DisbursementResponseSchema(BaseModel):
    loan_id: int
    payout_id: str
    payout_status: str
    payment_mode: PaymentModeEnum
    payment_provider: PayoutProviderEnum
    message: str

    class Config:
        from_attributes = True