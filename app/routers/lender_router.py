from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List

from app.core.session import get_db
from app.services.lender_service import LenderService
from app.schemas.lender import LenderApplicationListResponse

router = APIRouter(
    prefix="/lender",
    tags=["Lender Dashboard"]
)


def serialize_application(app):
    return {
        "application_id": app.id,
        "reference_number": app.reference_number,
        "approved_amount": float(app.approved_amount),
        "tenure_months": app.requested_tenure_months,
        "application_status": app.application_status.value,
        "submitted_at": app.submitted_at
    }

@router.get("/applications", response_model=List[LenderApplicationListResponse])
def view_submitted_applications(db: Session = Depends(get_db)):

    applications = LenderService.get_submitted_applications(db)
    return [serialize_application(app) for app in applications]

@router.get("/my-applications/{lender_id}", response_model=List[LenderApplicationListResponse])
def view_lender_applications(
    lender_id: int,
    db: Session = Depends(get_db)
):

    applications = LenderService.get_lender_applications(db, lender_id)
    return [serialize_application(app) for app in applications]

@router.post("/pick/{application_id}")
def pick_application(
    application_id: int,
    lender_id: int,
    db: Session = Depends(get_db)
):

    return LenderService.pick_application(db, application_id, lender_id)

@router.post("/approve/{application_id}")
def approve_application(
    application_id: int,
    lender_id: int,
    db: Session = Depends(get_db)
):

    return LenderService.approve_application(db, application_id, lender_id)


@router.post("/reject/{application_id}")
def reject_application(
    application_id: int,
    lender_id: int,
    rejection_reason: str,
    db: Session = Depends(get_db)
):

    return LenderService.reject_application(
        db,
        application_id,
        lender_id,
        rejection_reason
    )