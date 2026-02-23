from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.db_models.loan_application import LoanApplication
from app.db_models.loan_application_purpose import LoanApplicationPurpose
from app.db_models.loan_application_steps import LoanApplicationStepTracker
from app.repositories.loan_application_purpose_repo import (LoanApplicationPurposeRepository)
from app.core.enums import LoanApplicationStep, enum_value
from app.services.loan_application_service import LoanApplicationService


class LoanApplicationPurposeService:

    @staticmethod
    def save_purpose(
        db: Session,
        application_id: int,
        purpose_code,
        purpose_description):

        # validate application
        application = db.query(LoanApplication).filter(
            LoanApplication.id == application_id
        ).first()

        if not application:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Loan application not found")

        LoanApplicationService.ensure_editable(application)

        # get step tracker
        tracker = db.query(LoanApplicationStepTracker).filter(
            LoanApplicationStepTracker.application_id == application_id
        ).first()

        if not tracker:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Application steps not initialized")

        if not tracker.loan_details_completed:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Complete loan details before selecting purpose")

        existing = LoanApplicationPurposeRepository.get_by_application_id(
            db, application_id)

        # update existing purpose
        if existing:
            existing.purpose_code = purpose_code
            existing.purpose_description = purpose_description
            purpose = existing
        else:
            purpose = LoanApplicationPurpose(
                application_id=application_id,
                purpose_code=purpose_code,
                purpose_description=purpose_description)
            purpose = LoanApplicationPurposeRepository.create(db, purpose)

        # Step completion update
        tracker.purpose_completed = True
        tracker.last_completed_step = enum_value(LoanApplicationStep.PURPOSE)

        if tracker.current_step == enum_value(LoanApplicationStep.LOAN_DETAILS):
            next_step = enum_value(LoanApplicationStep.REFERENCES)
            tracker.current_step = next_step
            application.current_step = next_step

        db.commit()
        db.refresh(purpose)
        db.refresh(tracker)

        return purpose

    @staticmethod
    def get_purpose(db: Session, application_id: int):

        purpose = LoanApplicationPurposeRepository.get_by_application_id(
            db, application_id)

        if not purpose:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Purpose not found")

        return purpose
