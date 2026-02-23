from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.session import get_db
from app.services.loan_application_summary_service import (
    LoanApplicationSummaryService)
from app.schemas.loan_application_summary import (
    LoanApplicationSummaryResponseSchema)

router = APIRouter(prefix="/loan/application",tags=["Loan Application Summary"])


@router.get(
    "/{application_id}/summary",
    response_model=LoanApplicationSummaryResponseSchema,
    responses={
        400: {
            "description": "Pending steps not completed",
            "content": {
                "application/json": {
                    "example": {
                        "detail": {
                            "pending_step": "DECLARATION",
                            "message": "Declaration not completed"
                        }
                    }
                }
            },
        },
        404: {
            "description": "Application not found"
        }
    }
)
def get_application_summary(
    application_id: int,
    db: Session = Depends(get_db)
):
    """
    Rules:
    - All mandatory steps must be completed
    - If any step is pending, API returns which step is missing
    - Summary is shown only after DECLARATION is completed
    """
    return LoanApplicationSummaryService.get_summary(
        db=db,
        application_id=application_id)
