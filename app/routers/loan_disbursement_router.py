from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.session import get_db
from app.services.loan_disbursement_service import LoanDisbursementService
from app.services.pre_disbursement_service import PreDisbursementService

from app.schemas.loan_disbursement_schema import (
    DisbursementResponseSchema,
    DisbursementRequestSchema,
)

from app.schemas.loan_predisbursement_schema import (
    PreDisbursementResponseSchema,
)

router = APIRouter(
    prefix="/admin/disbursement",
    tags=["Loan Disbursement"]
)


# ---------------------------------------------------
# 🔍 Pre-Disbursement Preview (Charges, Net Amount)
# ---------------------------------------------------
@router.get(
    "/{application_id}",
    response_model=PreDisbursementResponseSchema
)
def preview_charges(
    application_id: int,
    db: Session = Depends(get_db)
):
    return PreDisbursementService.get_preview(
        db,
        application_id
    )


# ---------------------------------------------------
# 💸 Final Disbursement
# ---------------------------------------------------
@router.post(
    "/{application_id}",
    response_model=DisbursementResponseSchema
)
def disburse(
    application_id: int,
    payload: DisbursementRequestSchema,
    db: Session = Depends(get_db)
):
    return LoanDisbursementService.disburse_loan(
        db=db,
        application_id=application_id,
        payment_mode=payload.payment_mode
    )