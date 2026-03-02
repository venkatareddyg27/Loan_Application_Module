from pydantic import BaseModel, Field
from decimal import Decimal
from datetime import datetime
from typing import Optional

from app.core.enums import (
    PaymentModeEnum,
    DisbursementStatusEnum)


class DisbursementRequestSchema(BaseModel):
    payment_mode: str


class DisbursementResponseSchema(BaseModel):
    loan_id: int
    payout_id: str
    payout_status: str
    payment_mode: str
    message: str
    class Config:
        from_attributes = True