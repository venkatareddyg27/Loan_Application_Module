from fastapi import APIRouter, Depends, HTTPException
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
# Preview loan disbursement charges
# ---------------------------------------------------
@router.get(
    "/{application_id}",
    response_model=PreDisbursementResponseSchema,
    summary="Preview loan disbursement charges"
)
def preview_charges(
    application_id: int,
    db: Session = Depends(get_db)
):
    """
    Shows loan calculation preview before disbursement.

    Includes:
    - lender name
    - EMI
    - processing fee
    - GST
    - net disbursement amount
    """

    return PreDisbursementService.get_preview(
        db=db,
        application_id=application_id
    )


# ---------------------------------------------------
# Final loan disbursement
# ---------------------------------------------------
@router.post(
    "/{application_id}",
    response_model=DisbursementResponseSchema,
    summary="Disburse loan to borrower"
)
def disburse_loan(
    application_id: int,
    payload: DisbursementRequestSchema,
    db: Session = Depends(get_db)
):
    """
    Performs final loan disbursement.

    Steps:
    1. Validate loan application
    2. Calculate net disbursement amount
    3. Transfer funds via payment provider
    4. Update loan status to DISBURSED
    """

    try:

        result = LoanDisbursementService.disburse_loan(
            db=db,
            application_id=application_id,
            payment_mode=payload.payment_mode.value,
            payment_provider=payload.payment_provider.value
        )

        return result

    except ValueError as e:

        raise HTTPException(
            status_code=400,
            detail=str(e)
        )

    except Exception as e:

        print("DISBURSEMENT ERROR:", str(e))

        raise HTTPException(
            status_code=500,
            detail="Loan disbursement failed"
        )