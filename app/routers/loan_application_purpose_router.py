from fastapi import APIRouter, Depends, Form
from sqlalchemy.orm import Session

from app.core.session import get_db
from app.core.enums import LoanPurpose
from app.schemas.loan_application_purpose import (
    LoanApplicationPurposeResponse)
from app.services.loan_application_purpose_service import (
    LoanApplicationPurposeService)

router = APIRouter(
    prefix="/loan/application",
    tags=["Loan Application Purpose"])


@router.put(
    "/{application_id}/purpose",
    response_model=LoanApplicationPurposeResponse)

def save_loan_purpose(
    application_id: int,
    purpose_code: LoanPurpose = Form(...),   
    purpose_description: str | None = Form(None),
    db: Session = Depends(get_db)):

    return LoanApplicationPurposeService.save_purpose(
        db=db,
        application_id=application_id,
        purpose_code=purpose_code,
        purpose_description=purpose_description)


@router.get(
    "/{application_id}/purpose",
    response_model=LoanApplicationPurposeResponse)

def get_loan_purpose(
    application_id: int,
    db: Session = Depends(get_db)):

    return LoanApplicationPurposeService.get_purpose(
        db=db,
        application_id=application_id)
