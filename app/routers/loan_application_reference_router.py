from fastapi import APIRouter, Depends, Form
from sqlalchemy.orm import Session

from app.core.session import get_db
from app.core.enums import ReferenceRelation
from app.services.loan_application_reference_service import (
    LoanApplicationReferenceService)
from app.schemas.loan_application_references import (
    LoanApplicationReferenceResponse)

router = APIRouter(
    prefix="/loan/application",
    tags=["Loan Application References"])


@router.put(
    "/{application_id}/references",
    response_model=list[LoanApplicationReferenceResponse])

def save_references(
    application_id: int,

    # Reference 1
    ref1_name: str = Form(...),
    ref1_mobile_number: str = Form(...),
    ref1_relation_type: ReferenceRelation = Form(...),
    ref1_is_emergency_contact: bool = Form(...),

    # Reference 2
    ref2_name: str = Form(...),
    ref2_mobile_number: str = Form(...),
    ref2_relation_type: ReferenceRelation = Form(...),
    ref2_is_emergency_contact: bool = Form(...),

    db: Session = Depends(get_db)
):
    return LoanApplicationReferenceService.save_references_form(
        db,
        application_id,
        ref1_name,
        ref1_mobile_number,
        ref1_relation_type,
        ref1_is_emergency_contact,
        ref2_name,
        ref2_mobile_number,
        ref2_relation_type,
        ref2_is_emergency_contact)


@router.get(
    "/{application_id}/references",
    response_model=list[LoanApplicationReferenceResponse])

def get_references(
    application_id: int,
    db: Session = Depends(get_db)):
    
    return LoanApplicationReferenceService.get_references(
        db,
        application_id) 
    
