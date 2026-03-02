from fastapi import HTTPException
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from datetime import datetime
from decimal import Decimal

from app.db_models.loan_application import LoanApplication
from app.db_models.user_profiles import UserProfile
from app.db_models.user_bank_details import UserBankDetails

from app.core.enums import LoanApplicationStatus
from app.integrations.factory import PayoutProviderFactory
from app.integrations.exceptions import PayoutIntegrationError


class LoanDisbursementService:

    @staticmethod
    def disburse_loan(
        db: Session,
        application_id: int,
        payment_mode: str
    ):
        try:
            # ---------------------------------------------------
            # 1️⃣ Lock Loan Row (Prevents double execution)
            # ---------------------------------------------------
            loan: LoanApplication = (
                db.query(LoanApplication)
                .filter(LoanApplication.id == application_id)
                .with_for_update()
                .first()
            )

            if not loan:
                raise HTTPException(404, "Loan application not found")

            requested_mode = payment_mode.upper() if payment_mode else None

            # ---------------------------------------------------
            # 2️⃣ Prepare Preview Response (ALWAYS returned safely)
            # ---------------------------------------------------
            preview_response = {
                "loan_id": loan.id,
                "amount": float(loan.approved_amount or 0),
                "payout_id": loan.payout_id,
                "payout_status": loan.payout_status,
                "current_status": loan.application_status.value,
                "payment_mode": requested_mode,
            }

            # ---------------------------------------------------
            # 3️⃣ Idempotent Handling (NO 400 errors)
            # ---------------------------------------------------

            # Already Disbursed
            if loan.application_status == LoanApplicationStatus.DISBURSED:
                return {
                    **preview_response,
                    "message": "Loan already disbursed."
                }

            # Payout already initiated
            if loan.application_status == LoanApplicationStatus.PAYOUT_INITIATED:
                return {
                    **preview_response,
                    "message": "Payout already initiated."
                }

            # Not approved yet
            if loan.application_status != LoanApplicationStatus.APPROVED:
                return {
                    **preview_response,
                    "message": "Loan not eligible for disbursement."
                }

            if not loan.approved_amount or loan.approved_amount <= 0:
                raise HTTPException(400, "Invalid approved amount")

            # ---------------------------------------------------
            # 4️⃣ Fetch User Profile
            # ---------------------------------------------------
            user: UserProfile = loan.user_profile

            if not user:
                raise HTTPException(400, "User profile not found")

            if requested_mode not in ["BANK", "UPI"]:
                raise HTTPException(400, "Invalid payment mode")

            # ---------------------------------------------------
            # 5️⃣ Select Verified Primary Method
            # ---------------------------------------------------
            primary_method: UserBankDetails = next(
                (
                    m for m in user.bank_details
                    if m.is_verified and
                    (
                        (requested_mode == "BANK" and m.is_primary_bank) or
                        (requested_mode == "UPI" and m.is_primary_upi)
                    )
                ),
                None
            )

            if not primary_method:
                raise HTTPException(
                    400,
                    f"No verified primary {requested_mode} method selected"
                )

            # ---------------------------------------------------
            # 6️⃣ Get Payout Provider
            # ---------------------------------------------------
            provider = PayoutProviderFactory.get_provider("razorpay")

            # ---------------------------------------------------
            # 7️⃣ Create Razorpay Contact (If Not Exists)
            # ---------------------------------------------------
            if not user.razorpay_contact_id:

                contact_payload = {
                    "name": user.full_name,
                    "email": user.email,
                    "contact": user.user.phone_number,
                    "type": "customer"
                }

                contact = provider.create_contact(contact_payload)

                user.razorpay_contact_id = contact["id"]
                db.flush()

            # ---------------------------------------------------
            # 8️⃣ Create Fund Account (If Not Exists)
            # ---------------------------------------------------
            if not primary_method.razorpay_fund_account_id:

                if requested_mode == "BANK":
                    fund_payload = {
                        "contact_id": user.razorpay_contact_id,
                        "account_type": "bank_account",
                        "bank_account": {
                            "name": primary_method.account_holder_name,
                            "ifsc": primary_method.ifsc_code,
                            "account_number": primary_method.account_number
                        }
                    }
                else:  # UPI
                    fund_payload = {
                        "contact_id": user.razorpay_contact_id,
                        "account_type": "vpa",
                        "vpa": {
                            "address": primary_method.upi_id
                        }
                    }

                fund_account = provider.create_fund_account(fund_payload)
                primary_method.razorpay_fund_account_id = fund_account["id"]
                db.flush()

            # ---------------------------------------------------
            # 9️⃣ Initiate Payout
            # ---------------------------------------------------
            reference_id = f"loan_{loan.id}_{int(datetime.utcnow().timestamp())}"

            payout_payload = provider.build_payout_payload(
                fund_account_id=primary_method.razorpay_fund_account_id,
                amount=Decimal(loan.approved_amount),
                reference=reference_id
            )

            payout = provider.initiate_payout(payout_payload)

            # ---------------------------------------------------
            # 🔟 Update Loan Status
            # ---------------------------------------------------
            loan.payout_id = payout.get("id")
            loan.payout_status = payout.get("status", "PENDING")
            loan.application_status = LoanApplicationStatus.PAYOUT_INITIATED
            loan.disbursed_at = None

            db.commit()

            return {
                "loan_id": loan.id,
                "amount": float(loan.approved_amount),
                "payout_id": loan.payout_id,
                "payout_status": loan.payout_status,
                "current_status": loan.application_status.value,
                "payment_mode": requested_mode,
                "message": "Payout initiated successfully. Awaiting webhook confirmation."
            }

        except HTTPException:
            db.rollback()
            raise

        except PayoutIntegrationError as e:
            db.rollback()
            raise HTTPException(500, str(e))

        except SQLAlchemyError as db_error:
            db.rollback()
            raise HTTPException(
                500,
                f"Database error during payout: {str(db_error)}"
            )

        except Exception as e:
            db.rollback()
            raise HTTPException(
                500,
                f"Payout failed: {str(e)}"
            )

    # ---------------------------------------------------
    # 🔄 Webhook Status Update
    # ---------------------------------------------------
    @staticmethod
    def update_payout_status(
        db: Session,
        payout_id: str,
        status: str
    ):

        loan = (
            db.query(LoanApplication)
            .filter(LoanApplication.payout_id == payout_id)
            .with_for_update()
            .first()
        )

        if not loan:
            return

        if loan.payout_status == status:
            return

        loan.payout_status = status

        if status in ["processed", "success"]:
            loan.application_status = LoanApplicationStatus.DISBURSED
            loan.disbursed_at = datetime.utcnow()

        elif status in ["failed", "reversed"]:
            loan.application_status = LoanApplicationStatus.PAYOUT_FAILED

        db.commit()