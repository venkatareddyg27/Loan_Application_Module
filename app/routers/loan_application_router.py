from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.schemas.loan_application import (
    LoanApplicationCreateSchema,
    LoanSubmitRequestSchema,
    LoanSubmitResponseSchema,
    LoanApplicationCreateResponseSchema,
    LoanApplicationResponseSchema)
from app.services.loan_application_service import LoanApplicationService
from app.core.session import get_db

router = APIRouter(
    prefix="/loan/application",
    tags=["Apply Loan & Submit Application"])

# APPLY LOAN
@router.post("/apply", response_model=LoanApplicationCreateResponseSchema)
def apply(
    data: LoanApplicationCreateSchema,
    db: Session = Depends(get_db)
):
    return LoanApplicationService.apply_loan(db, data)


# SUBMIT APPLICATION
@router.post("/{application_id}/submit", response_model=LoanSubmitResponseSchema)
def submit(
    application_id: int,
    data: LoanSubmitRequestSchema,
    db: Session = Depends(get_db)
):
    return LoanApplicationService.submit_application(
        db, application_id, data.confirm)


# GET APPLICATION
@router.get("/{application_id}", response_model=LoanApplicationResponseSchema)
def get_loan_application(
    application_id: int,
    db: Session = Depends(get_db)
):
    return LoanApplicationService.get_application(db, application_id)
