from sqlalchemy.orm import Session
from fastapi import HTTPException

from app.db_models.loan_application import LoanApplication
from app.db_models.loan_application_references import LoanApplicationReference
from app.db_models.loan_application_steps import LoanApplicationStepTracker
from app.core.enums import LoanApplicationStep, enum_value
from app.services.loan_application_service import LoanApplicationService


class LoanApplicationReferenceService:

    @staticmethod
    def save_references_form(
        db: Session,
        application_id: int,
        ref1_name,
        ref1_mobile_number,
        ref1_relation_type,
        ref1_is_emergency_contact,
        ref2_name,
        ref2_mobile_number,
        ref2_relation_type,
        ref2_is_emergency_contact):

        application = db.query(LoanApplication).filter(
            LoanApplication.id == application_id
        ).first()

        if not application:
            raise HTTPException(status_code=404, detail="Loan application not found")

        LoanApplicationService.ensure_editable(application)

        tracker = db.query(LoanApplicationStepTracker).filter_by(
            application_id=application_id
        ).first()

        if not tracker:
            raise HTTPException(status_code=400, detail="Application steps not initialized")

        if not tracker.purpose_completed:
            raise HTTPException(
                status_code=400,
                detail="Complete purpose step before adding references")

        try:
            # remove existing
            db.query(LoanApplicationReference).filter(
                LoanApplicationReference.application_id == application_id
            ).delete()

            new_refs = [
                LoanApplicationReference(
                    application_id=application_id,
                    name=ref1_name,
                    mobile_number=ref1_mobile_number,
                    relation_type=ref1_relation_type,
                    is_emergency_contact=ref1_is_emergency_contact,
                    is_verified=False
                ),
                LoanApplicationReference(
                    application_id=application_id,
                    name=ref2_name,
                    mobile_number=ref2_mobile_number,
                    relation_type=ref2_relation_type,
                    is_emergency_contact=ref2_is_emergency_contact,
                    is_verified=False
                )
            ]

            db.add_all(new_refs)

            tracker.references_saved = True
            tracker.last_completed_step = enum_value(LoanApplicationStep.REFERENCES)

            db.commit()

            for ref in new_refs:
                db.refresh(ref)

            return new_refs

        except Exception:
            db.rollback()
            raise HTTPException(status_code=500, detail="Failed to save references")

    @staticmethod
    def get_references(db: Session, application_id: int):

        refs = db.query(LoanApplicationReference).filter(
            LoanApplicationReference.application_id == application_id
        ).all()

        if not refs:
            raise HTTPException(status_code=404, detail="No references found")

        return refs
