from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.db_models.loan_application import LoanApplication
from app.db_models.loan_application_steps import LoanApplicationStepTracker
from app.db_models.user_profiles import UserProfile
from app.core.enums import LoanApplicationStep, enum_value
from app.services.loan_calculator import calculate_loan_summary
from app.schemas.loan_application_summary import *


class LoanApplicationSummaryService:

    @staticmethod
    def get_summary(db: Session, application_id: int):
        """
        Generates loan summary BEFORE submission.
        Locks summary after submission.
        """
        application = db.query(LoanApplication).filter(
            LoanApplication.id == application_id
        ).first()

        if not application:
            raise HTTPException(
                status_code=404,
                detail="Loan application not found"
            )

        if application.is_submitted:
            raise HTTPException(
                status_code=400,
                detail="Application already submitted. Summary locked."
            )
        if not application.approved_amount:
            raise HTTPException(
                status_code=400,
                detail="Eligible amount not available"
            )

        principal = float(application.approved_amount)
        profile = db.query(UserProfile).filter(
            UserProfile.id == application.user_profile_id
        ).first()

        if not profile:
            raise HTTPException(
                status_code=404,
                detail="User profile not found"
            )

        tracker = db.query(LoanApplicationStepTracker).filter_by(
            application_id=application_id
        ).first()

        if not tracker:
            raise HTTPException(
                status_code=400,
                detail="Application steps not initialized"
            )

        if not tracker.declaration_completed:
            raise HTTPException(
                status_code=400,
                detail={
                    "pending_step": enum_value(LoanApplicationStep.DECLARATION),
                    "message": "Declaration not completed"
                }
            )

        declaration = application.declaration

        if not declaration or not declaration.is_locked:
            raise HTTPException(
                status_code=400,
                detail={
                    "pending_step": enum_value(LoanApplicationStep.DECLARATION),
                    "message": "Declaration confirmation pending"
                }
            )

        try:
            loan_calc = calculate_loan_summary(
                principal=principal,
                tenure_months=application.requested_tenure_months
            )
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))

        user_summary = UserSummarySchema(
            user_id=application.user_profile_id,
            full_name=profile.full_name,
            mobile_number=getattr(profile, "mobile_number", None),
            email=profile.email
        )

        loan_details = LoanDetailsSummarySchema(
            approved_amount=principal,
            requested_tenure_months=loan_calc["tenure_months"],
            interest_rate=loan_calc["interest_rate"],
            emi_amount=loan_calc["emi"],
            total_repayment=loan_calc["total_repayment"],
            net_disbursement_amount=loan_calc["net_disbursement_amount"]
        )

        if not application.purpose:
            raise HTTPException(
                status_code=400,
                detail={
                    "pending_step": enum_value(LoanApplicationStep.PURPOSE),
                    "message": "Loan purpose not found"
                }
            )

        purpose = LoanPurposeSummarySchema(
            purpose=application.purpose.purpose_code.value
        )

        if not application.references or len(application.references) < 2:
            raise HTTPException(
                status_code=400,
                detail={
                    "pending_step": enum_value(LoanApplicationStep.REFERENCES),
                    "message": "At least 2 references required"
                }
            )

        reference_list = [
            ReferenceSummarySchema(
                name=ref.name,
                relationship=ref.relation_type,
                mobile_number=ref.mobile_number,
                is_mobile_verified=ref.is_verified
            )
            for ref in application.references
        ]

        verified_count = sum(ref.is_verified for ref in application.references)

        reference_status = ReferencesStatusSchema(
            total_required=2,
            total_added=len(application.references),
            verified_count=verified_count,
            remaining_to_verify=max(0, 2 - verified_count)
        )

        declaration_summary = DeclarationSummarySchema(
            has_existing_loans=declaration.has_existing_loans,
            has_credit_card=declaration.has_credit_card,
            has_default_history=declaration.has_default_history,
            declaration_accepted=declaration.agreed_terms
        )
        
        submission_status = SubmissionStatusSchema(
            last_completed_step=tracker.last_completed_step,
            can_submit=True,
            pending_steps=[]
        )

        return LoanApplicationSummaryResponseSchema(
            application_id=application.id,
            user=user_summary,
            loan_details=loan_details,
            purpose=purpose,
            references=reference_list,
            reference_status=reference_status,
            declaration=declaration_summary,
            submission_status=submission_status
        )