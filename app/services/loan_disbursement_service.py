from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from fastapi import HTTPException
from datetime import datetime

from app.db_models.loan_application import LoanApplication
from app.db_models.loan_disbursements import LoanDisbursement
from app.db_models.user_bank_details import UserBankDetails

from app.core.enums import (
    LoanApplicationStatus,
    DisbursementStatusEnum,
    PaymentModeEnum
)

from app.services.loan_calculator import calculate_loan_summary
from app.integrations.factory import PayoutProviderFactory


class LoanDisbursementService:

    @staticmethod
    def disburse_loan(
        db: Session,
        application_id: int,
        payment_mode: str,
        payment_provider: str
    ):

        # ---------------------------------------------------
        # 1️⃣ Lock loan row (prevent concurrent payouts)
        # ---------------------------------------------------
        loan = (
            db.query(LoanApplication)
            .filter(LoanApplication.id == application_id)
            .with_for_update()
            .first()
        )

        if not loan:
            raise HTTPException(
                status_code=404,
                detail="Loan application not found"
            )

        # ---------------------------------------------------
        # 2️⃣ Check if already disbursed
        # ---------------------------------------------------
        if loan.application_status == LoanApplicationStatus.DISBURSED:
            raise HTTPException(
                status_code=400,
                detail="Loan already disbursed"
            )

        # ---------------------------------------------------
        # 3️⃣ Prevent duplicate disbursement
        # ---------------------------------------------------
        existing_disbursement = (
            db.query(LoanDisbursement)
            .filter(LoanDisbursement.application_id == loan.id)
            .first()
        )

        if existing_disbursement:
            raise HTTPException(
                status_code=400,
                detail="Loan payout already initiated"
            )

        # ---------------------------------------------------
        # 4️⃣ Validate approval
        # ---------------------------------------------------
        if loan.application_status != LoanApplicationStatus.APPROVED:
            raise HTTPException(
                status_code=400,
                detail="Loan not approved for disbursement"
            )

        # ---------------------------------------------------
        # 5️⃣ Fetch verified bank
        # ---------------------------------------------------
        bank = (
            db.query(UserBankDetails)
            .filter(
                UserBankDetails.user_id == loan.user_profile_id,
                UserBankDetails.is_primary_bank == True,
                UserBankDetails.is_verified == True
            )
            .first()
        )

        if not bank:
            raise HTTPException(
                status_code=400,
                detail="Verified primary bank account not found"
            )

        # ---------------------------------------------------
        # 6️⃣ Calculate deductions
        # ---------------------------------------------------
        summary = calculate_loan_summary(
            float(loan.approved_amount),
            loan.requested_tenure_months
        )

        net_amount = summary["net_disbursement_amount"]

        # ---------------------------------------------------
        # 7️⃣ Get payout provider
        # ---------------------------------------------------
        provider = PayoutProviderFactory.get_provider(payment_provider)

        payout = provider.disburse(
            amount=net_amount,
            account_number=bank.account_number,
            ifsc=bank.ifsc_code,
            name=bank.account_holder_name,
            reference_id=f"loan_{loan.id}"
        )

        # ---------------------------------------------------
        # 8️⃣ Save disbursement record
        # ---------------------------------------------------
        disbursement = LoanDisbursement(
            application_id=loan.id,
            amount=net_amount,
            payment_reference_id=payout.get("id"),
            payment_status=DisbursementStatusEnum.INITIATED,
            payment_mode=PaymentModeEnum(payment_mode)
        )

        db.add(disbursement)

        # ---------------------------------------------------
        # 9️⃣ Update loan status
        # ---------------------------------------------------
        loan.payout_id = payout.get("id")
        loan.payout_status = payout.get("status", "processing")

        loan.application_status = LoanApplicationStatus.DISBURSED
        loan.disbursed_at = datetime.utcnow()

        # ---------------------------------------------------
        # 🔟 Commit safely
        # ---------------------------------------------------
        try:
            db.commit()
        except IntegrityError:
            db.rollback()
            raise HTTPException(
                status_code=400,
                detail="Disbursement already exists for this loan"
            )

        # ---------------------------------------------------
        # 1️⃣1️⃣ Response
        # ---------------------------------------------------
        return {
            "loan_id": loan.id,
            "payout_id": payout.get("id"),
            "payout_status": payout.get("status", "processing"),
            "payment_mode": payment_mode,
            "payment_provider":payment_provider,
            "message": "Loan disbursement initiated successfully"
        }