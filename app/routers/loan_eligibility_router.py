from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.session import get_db
from app.schemas.loan_eligibility_schema import (
    LoanEligibilityCheckSchema,
    LoanEligibilityResponseSchema)
from app.services.loan_eligibility_service import LoanEligibilityService


router = APIRouter(
    prefix="/loan/eligibility",
    tags=["Loan Eligibility"])

@router.post("/check/{user_profile_id}",
    response_model=LoanEligibilityResponseSchema)

def check_eligibility(
    payload: LoanEligibilityCheckSchema,
    db: Session = Depends(get_db)
):
    return LoanEligibilityService.check_eligibility(
        db=db,
        payload=payload)


@router.get(
    "/{eligibility_id}",
    response_model=LoanEligibilityResponseSchema
)
def get_eligibility(
    eligibility_id: int,
    db: Session = Depends(get_db)
):
    eligibility = LoanEligibilityService.get_by_id(
        db=db,
        eligibility_id=eligibility_id
    )

    if not eligibility:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Eligibility not found"
        )

    return eligibility
