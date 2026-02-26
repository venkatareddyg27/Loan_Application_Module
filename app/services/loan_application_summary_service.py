from fastapi import HTTPException
from sqlalchemy.orm import Session, joinedload

from app.db_models.loan_application import LoanApplication
from app.db_models.loan_application_steps import LoanApplicationStepTracker
from app.db_models.user_profiles import UserProfile
from app.core.enums import LoanApplicationStep, enum_value
from app.services.loan_calculator import calculate_loan_summary
from app.schemas.loan_application_summary import *


class LoanApplicationSummaryService:

    @staticmethod
    def get_summary(db: Session, application_id: int):

        # Load related data efficiently
        application = db.query(LoanApplication).options(
            joinedload(LoanApplication.eligibility),
            joinedload(LoanApplication.purpose),
            joinedload(LoanApplication.references),
            joinedload(LoanApplication.declaration)
        ).filter(
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

        # =====================================================
        # Eligibility Section (FIXED)
        # =====================================================
        if not application.eligibility:
            raise HTTPException(
                status_code=400,
                detail="Eligibility record not linked to this application"
            )

        eligibility_enum = application.eligibility.eligibility_status
        eligible_amount = float(application.eligibility.max_eligible_amount)

        if eligible_amount <= 0:
            raise HTTPException(
                status_code=400,
                detail="Eligible amount not available"
            )

        # Convert enum to boolean
        is_eligible = True if eligibility_enum.name == "ELIGIBLE" else False

        # Use calculated interest rate or default
        interest_rate = float(application.interest_rate or 25)

        # Optional Risk Category Logic
        risk_category = None
        credit_score = application.eligibility.credit_score_used
        if credit_score:
            if credit_score >= 750:
                risk_category = "LOW"
            elif credit_score >= 650:
                risk_category = "MEDIUM"
            else:
                risk_category = "HIGH"

        eligibility_summary = EligibilitySummarySchema(
            eligible=is_eligible,
            max_loan_amount=eligible_amount,
            interest_rate=interest_rate,   # ✅ CHANGED FIELD NAME
            risk_category=risk_category
        )

        principal = eligible_amount

        # =====================================================
        # User Section
        # =====================================================
        profile = db.query(UserProfile).filter(
            UserProfile.id == application.user_profile_id
        ).first()

        if not profile:
            raise HTTPException(
                status_code=404,
                detail="User profile not found"
            )

        user_summary = UserSummarySchema(
            user_id=application.user_profile_id,
            full_name=profile.full_name,
            mobile_number=getattr(profile, "mobile_number", None),
            email=profile.email
        )

        # =====================================================
        # Step Validation
        # =====================================================
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

        # =====================================================
        # Loan Calculation
        # =====================================================
        try:
            loan_calc = calculate_loan_summary(
                principal=principal,
                tenure_months=application.requested_tenure_months
            )
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))

        loan_details = LoanDetailsSummarySchema(
            approved_amount=principal,
            requested_tenure_months=loan_calc["tenure_months"],
            interest_rate=loan_calc["interest_rate"],
            emi_amount=loan_calc["emi"],
            total_repayment=loan_calc["total_repayment"],
            processing_fee=loan_calc.get("processing_fee"),
            gst_on_processing_fee=loan_calc.get("gst_on_processing_fee"),
            total_processing_charges=loan_calc.get("total_processing_charges"),
            lender_name=None
        )

        # =====================================================
        # Purpose Section
        # =====================================================
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

        # =====================================================
        # References Section
        # =====================================================
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

        # =====================================================
        # Declaration Section
        # =====================================================
        declaration_summary = DeclarationSummarySchema(
            has_existing_loans=declaration.has_existing_loans,
            has_credit_card=declaration.has_credit_card,
            has_default_history=declaration.has_default_history,
            declaration_accepted=declaration.agreed_terms
        )

        # =====================================================
        # Submission Status
        # =====================================================
        submission_status = SubmissionStatusSchema(
            last_completed_step=tracker.last_completed_step,
            can_submit=True,
            pending_steps=[]
        )

        # =====================================================
        # Final Response
        # =====================================================
        return LoanApplicationSummaryResponseSchema(
            application_id=application.id,
            user=user_summary,
            eligibility=eligibility_summary,
            loan_details=loan_details,
            purpose=purpose,
            references=reference_list,
            reference_status=reference_status,
            declaration=declaration_summary,
            submission_status=submission_status
        )