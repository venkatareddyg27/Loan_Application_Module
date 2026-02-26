from fastapi import HTTPException
from sqlalchemy.orm import Session
from datetime import datetime

from app.db_models.loan_application import LoanApplication
from app.db_models.user_profiles import UserProfile
from app.db_models.user_bank_details import UserBankDetails

from app.core.enums import LoanApplicationStatus
from app.services.payout_service import RazorpayPayoutService


class LoanDisbursementService:

    @staticmethod
    def disburse_loan(db: Session, application_id: int):

        # 1️⃣ Fetch Loan
        loan = db.get(LoanApplication, application_id)

        if not loan:
            raise HTTPException(404, "Loan application not found")

        # 2️⃣ Status Validation
        if loan.application_status != LoanApplicationStatus.APPROVED:
            raise HTTPException(
                400,
                "Loan must be APPROVED before disbursement"
            )

        # 3️⃣ Prevent Double Disbursement
        if loan.payout_id:
            raise HTTPException(
                400,
                "Loan already disbursed"
            )

        # 4️⃣ Fetch User
        user: UserProfile = loan.user_profile

        if not user:
            raise HTTPException(400, "User profile not found")

        # 5️⃣ Get Primary Verified Bank
        primary_bank: UserBankDetails = next(
            (
                b for b in user.bank_details
                if b.is_primary and b.is_verified
            ),
            None
        )

        if not primary_bank:
            raise HTTPException(
                400,
                "No verified primary bank account found"
            )

        try:

            # 6️⃣ Create Razorpay Contact (If Not Exists)
            if not user.razorpay_contact_id:

                contact = RazorpayPayoutService.create_contact(user)

                user.razorpay_contact_id = contact["id"]
                db.commit()

            # 7️⃣ Create Fund Account (If Not Exists)
            if not primary_bank.razorpay_fund_account_id:

                fund_account = RazorpayPayoutService.create_fund_account(
                    user.razorpay_contact_id,
                    primary_bank
                )

                primary_bank.razorpay_fund_account_id = fund_account["id"]
                db.commit()

            # 8️⃣ Initiate Payout
            payout = RazorpayPayoutService.initiate_payout(
                loan.approved_amount,
                primary_bank.razorpay_fund_account_id,
                loan.id
            )

            # 9️⃣ Update Loan State
            loan.payout_id = payout["id"]
            loan.payout_status = payout["status"]
            loan.application_status = LoanApplicationStatus.DISBURSED
            loan.disbursed_at = datetime.utcnow()

            db.commit()

            return {
                "loan_id": loan.id,
                "payout_id": loan.payout_id,
                "payout_status": loan.payout_status,
                "disbursed_at": loan.disbursed_at
            }

        except Exception as e:
            db.rollback()

            raise HTTPException(
                500,
                f"Payout failed: {str(e)}"
            )