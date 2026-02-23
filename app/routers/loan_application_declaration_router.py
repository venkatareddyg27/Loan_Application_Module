from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from app.core.session import get_db
from app.schemas.loan_application_declaration import (
    LoanApplicationDeclarationCreate,
    LoanApplicationDeclarationResponse)
from app.services.loan_application_declaration_service import (
    LoanApplicationDeclarationService)

router = APIRouter(
    prefix="/loan/application",
    tags=["Loan Application - Declaration"])


@router.put(
    "/{application_id}/declaration",
    response_model=LoanApplicationDeclarationResponse,
    operation_id="loan_application_submit_declaration")

def save_declaration(
    application_id: int,
    payload: LoanApplicationDeclarationCreate,
    request: Request,
    db: Session = Depends(get_db)
):

    client_ip = request.client.host if request.client else "unknown"
    user_agent = request.headers.get("user-agent")

    return LoanApplicationDeclarationService.save_declaration(
        db=db,
        application_id=application_id,
        payload=payload,
        ip_address=client_ip,
        user_agent=user_agent)
