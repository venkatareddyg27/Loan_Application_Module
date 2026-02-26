from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from app.core.session import get_db
from app.schemas.loan_application_references_otp import (
    ReferenceOTPSendRequest,
    ReferenceOTPVerifyRequest,
    ReferenceOTPVerifyResponse)
from app.services.reference_otp_service import ReferenceOTPService

router = APIRouter(
    prefix="/loan/application",
    tags=["Reference OTP"])


def get_client_ip(request: Request):
    return (
        request.headers.get("X-Forwarded-For", "").split(",")[0].strip()
        or request.headers.get("X-Real-IP")
        or (request.client.host if request.client else "unknown")
    )

@router.post(
    "/references/send-otp",
    operation_id="reference_send_otp"
)
def send_reference_otp(
    payload: ReferenceOTPSendRequest,
    request: Request,
    db: Session = Depends(get_db)
):
    client_ip = get_client_ip(request)

    return ReferenceOTPService.send_reference_otp(
        db=db,
        reference_id=payload.reference_id,
        client_ip=client_ip
    )


@router.post(
    "/references/resend-otp",
    operation_id="reference_resend_otp"
)
def resend_reference_otp(
    payload: ReferenceOTPSendRequest,
    request: Request,
    db: Session = Depends(get_db)
):
    client_ip = get_client_ip(request)

    return ReferenceOTPService.resend_reference_otp(
        db=db,
        reference_id=payload.reference_id,
        client_ip=client_ip
    )


@router.post(
    "/references/verify-otp",
    response_model=ReferenceOTPVerifyResponse,
    operation_id="reference_verify_otp"
)
def verify_reference_otp(
    payload: ReferenceOTPVerifyRequest,
    request: Request,
    db: Session = Depends(get_db)
):
    client_ip = get_client_ip(request)

    return ReferenceOTPService.verify_reference_otp(
        db=db,
        payload=payload,
        client_ip=client_ip
    )