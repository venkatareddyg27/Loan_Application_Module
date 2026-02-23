from sqlalchemy.orm import Session
from datetime import datetime, timezone
from fastapi import HTTPException

from app.db_models.loan_application import LoanApplication
from app.db_models.loan_application_declaration import LoanApplicationDeclaration
from app.db_models.loan_application_steps import LoanApplicationStepTracker
from app.core.enums import LoanApplicationStep, enum_value
from app.services.loan_application_service import LoanApplicationService


class LoanApplicationDeclarationService:

    @staticmethod
    def save_declaration(
        db: Session,
        application_id: int,
        payload,
        ip_address: str,
        user_agent: str):
        application = db.get(LoanApplication, application_id)
        if not application:
            raise HTTPException(status_code=404, detail="Application not found")

        LoanApplicationService.ensure_editable(application)
        now = datetime.now(timezone.utc)
        declaration = application.declaration
        if not declaration:
            declaration = LoanApplicationDeclaration(
                application_id=application_id)
            db.add(declaration)

        # Update declaration fields
        declaration.agreed_terms = payload.agreed_terms
        declaration.consent_credit_check = payload.consent_credit_check
        declaration.consent_data_sharing = payload.consent_data_sharing
        declaration.has_existing_loans = payload.has_existing_loans
        declaration.has_credit_card = payload.has_credit_card
        declaration.has_default_history = payload.has_default_history
        declaration.terms_version = payload.terms_version
        declaration.privacy_policy_version = payload.privacy_policy_version
        declaration.ip_address = ip_address
        declaration.user_agent = user_agent
        declaration.consent_timestamp = now
        application.ip_address = ip_address
        tracker = db.query(LoanApplicationStepTracker).filter_by(
            application_id=application_id
        ).first()

        if not tracker:
            raise HTTPException(status_code=404, detail="Step tracker not found")

        # Workflow guard 
        if not tracker.references_completed:
            raise HTTPException(
                status_code=400,
                detail="Complete references step before declaration")

        # Mark declaration completed
        tracker.declaration_completed = True
        tracker.last_completed_step = enum_value(LoanApplicationStep.DECLARATION)
        declaration.is_locked = True  # Lock declaration after completion
        # Move workflow forward
        tracker.current_step = enum_value(LoanApplicationStep.SUMMARY)
        application.current_step = enum_value(LoanApplicationStep.SUMMARY)

        db.commit()
        db.refresh(declaration)
        db.refresh(tracker)
        db.refresh(application)

        return declaration
