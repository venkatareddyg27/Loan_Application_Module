from datetime import datetime, timezone
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.db_models.loan_application import LoanApplication
from app.db_models.loan_application_steps import LoanApplicationStepTracker
from app.core.enums import (
    LoanApplicationStatus,
    LoanApplicationStep,
    enum_value,
    EligibilityStatusEnum,
)
from app.repositories import loan_application_repo
from app.core.reference_generator import generate_loan_reference_number
from app.services.loan_application_validation import validate_final_submission
from app.services.loan_eligibility_service import LoanEligibilityService
from app.schemas.loan_application import (
    LoanSubmitResponseSchema,
    LoanApplicationResponseSchema,
)
from app.services.loan_application_lock_manager_service import (
    ApplicationLockManager,
)
from app.services.loan_calculator import calculate_loan_summary


class LoanApplicationService:

    @staticmethod
    def ensure_editable(application: LoanApplication):
        if application.is_submitted:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Application already submitted. Editing not allowed."
            )

    @staticmethod
    def apply_loan(db: Session, data):

        # Fetch eligibility record
        eligibility = LoanEligibilityService.validate_and_fetch(
            db=db,
            eligibility_id=data.eligibility_id
        )

        # Reject if eligibility status is REJECTED
        if eligibility.eligibility_status == EligibilityStatusEnum.REJECTED:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=eligibility.failure_reason or
                "User is not eligible for the loan"
            )

        if not data.user_profile_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="user_profile_id is required"
            )

        eligible_amount = eligibility.max_eligible_amount

        if not eligible_amount:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Eligible amount not found for this eligibility record"
            )

        application = LoanApplication(
            user_profile_id=data.user_profile_id,
            eligibility_id=eligibility.id,
            reference_number=None,   
            approved_amount=eligible_amount,
            requested_tenure_months=data.requested_tenure_months,
            application_status=enum_value(LoanApplicationStatus.DRAFT),
            current_step=enum_value(LoanApplicationStep.LOAN_DETAILS),
            is_submitted=False,
            rejection_reason=None
        )

        db.add(application)
        db.flush()

        # Initialize Step Tracker
        tracker = LoanApplicationStepTracker(
            application_id=application.id,
            loan_details_completed=True,
            purpose_completed=False,
            references_completed=False,
            declaration_completed=False,
            current_step=enum_value(LoanApplicationStep.LOAN_DETAILS),
            last_completed_step=enum_value(LoanApplicationStep.LOAN_DETAILS)
        )

        db.add(tracker)
        db.commit()
        db.refresh(application)

        return {
            "application_id": application.id,
            "approved_amount": application.approved_amount,
            "eligibility_status": eligibility.eligibility_status,
            "eligible_amount": eligibility.max_eligible_amount,
            "next_step": application.current_step
        }

    @staticmethod
    def get_application(db: Session, application_id: int):

        application = loan_application_repo.get_by_id(db, application_id)

        if not application:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Loan application not found"
            )

        if not application.eligibility:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Eligibility record not linked to this application"
            )

        return LoanApplicationResponseSchema(
            application_id=application.id,
            application_status=application.application_status,
            current_step=application.current_step,

            #  Pull from eligibility table
            eligibility_status=application.eligibility.eligibility_status,
            eligible_amount=application.eligibility.max_eligible_amount,

            approved_amount=application.approved_amount,
            requested_tenure_months=application.requested_tenure_months,
            interest_rate=application.interest_rate
        )


    @staticmethod
    def submit_application(
        db: Session,
        application_id: int,
        confirm: bool
    ) -> LoanSubmitResponseSchema:

        if not confirm:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Confirmation required"
            )

        application = loan_application_repo.get_by_id(db, application_id)

        if not application:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Loan application not found"
            )

        if application.is_submitted:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Application already submitted"
            )

        tracker = db.query(LoanApplicationStepTracker).filter(
            LoanApplicationStepTracker.application_id == application.id
        ).first()

        if not tracker:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Application step tracker missing"
            )

        validate_final_submission(db, application, tracker)

        tracker.current_step = enum_value(LoanApplicationStep.SUBMITTED)
        tracker.last_completed_step = enum_value(LoanApplicationStep.SUMMARY)
        application.current_step = enum_value(LoanApplicationStep.SUBMITTED)

        loan_summary = calculate_loan_summary(
            principal=float(application.approved_amount),
            tenure_months=application.requested_tenure_months
        )

        application.reference_number = generate_loan_reference_number(db)

        application.application_status = enum_value(
            LoanApplicationStatus.SUBMITTED
        )
        application.is_submitted = True
        application.submitted_at = datetime.now(timezone.utc)

        application.interest_rate = loan_summary["interest_rate"]
        application.monthly_emi = loan_summary["emi"]
        application.processing_fee = loan_summary["processing_fee"]
        application.gst_amount = loan_summary["gst_on_processing_fee"]
        application.total_repayment = loan_summary["total_repayment"]

        ApplicationLockManager.lock_application(application)

        db.commit()
        db.refresh(application)

        return LoanSubmitResponseSchema(
            reference_number=application.reference_number,
            message="Loan application submitted successfully",
            expected_decision_time="24 hours"
        )