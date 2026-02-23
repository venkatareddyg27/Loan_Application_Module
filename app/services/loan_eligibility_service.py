from fastapi import HTTPException, status
from decimal import Decimal, ROUND_HALF_UP
from sqlalchemy.orm import Session

from app.db_models.user_profiles import UserProfile
from app.db_models.loan_eligibility import LoanEligibility
from app.schemas.loan_eligibility_schema import LoanEligibilityCheckSchema
from app.core.enums import EligibilityStatusEnum
from app.services.loan_calculator import (
    calculate_emi,
    validate_loan_request)

MAX_FOIR = Decimal("0.50")
MAX_MULTIPLIER = Decimal("20")


class LoanEligibilityService:

    @staticmethod
    def calculate_emi(principal: Decimal, tenure_months: int) -> Decimal:
        emi = calculate_emi(
            principal=float(principal),
            tenure_months=int(tenure_months)
        )
        return Decimal(str(emi)).quantize(
            Decimal("0.01"),
            rounding=ROUND_HALF_UP)

    @staticmethod
    def check_eligibility(db: Session, payload: LoanEligibilityCheckSchema):

        profile = db.query(UserProfile).filter(
            UserProfile.id == payload.user_profile_id
        ).first()

        if not profile:
            raise HTTPException(
                status_code=404,
                detail="User profile not found")

        income = Decimal(str(profile.monthly_income))
        existing_emi = Decimal(str(payload.existing_emi or 0))

        try:
            validate_loan_request(
                principal=float(payload.requested_amount),
                tenure_months=int(payload.requested_tenure_months)
            )
        except ValueError as e:
            raise HTTPException(
                status_code=400,
                detail=str(e)
            )

        emi = LoanEligibilityService.calculate_emi(
            principal=Decimal(str(payload.requested_amount)),
            tenure_months=payload.requested_tenure_months)

        foir = ((existing_emi + emi) / income).quantize(
            Decimal("0.0001"),
            rounding=ROUND_HALF_UP)

        if foir > MAX_FOIR:
            status_value = EligibilityStatusEnum.REJECTED
            max_amount = Decimal("0.00")
            reason = "FOIR exceeded"
        else:
            status_value = EligibilityStatusEnum.ELIGIBLE
            max_amount = (income * MAX_MULTIPLIER).quantize(
                Decimal("0.01"),
                rounding=ROUND_HALF_UP)
            reason = None

        eligibility = LoanEligibility(
            user_profile_id=payload.user_profile_id,
            income_used=income,
            proposed_emi=emi,
            existing_emi=existing_emi,
            foir_ratio=foir,
            max_eligible_amount=max_amount,
            eligibility_status=status_value,
            failure_reason=reason)

        db.add(eligibility)
        db.commit()
        db.refresh(eligibility)

        return eligibility

    @staticmethod
    def validate_and_fetch(
        db: Session,
        eligibility_id: int,
    ) -> LoanEligibility:

        eligibility = db.query(LoanEligibility).filter(
            LoanEligibility.id == eligibility_id
        ).first()

        if not eligibility:
            raise HTTPException(
                status_code=400,
                detail="Invalid eligibility id"
            )

        if eligibility.eligibility_status != EligibilityStatusEnum.ELIGIBLE:
            raise HTTPException(
                status_code=400,
                detail=eligibility.failure_reason or "User not eligible"
            )

        return eligibility

    @staticmethod
    def get_by_id(db: Session, eligibility_id: int):

        eligibility = db.query(LoanEligibility).filter(
            LoanEligibility.id == eligibility_id
        ).first()

        if not eligibility:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Loan eligibility record not found"
            )

        return eligibility