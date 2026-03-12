from sqlalchemy.orm import Session
from datetime import datetime, timedelta

from app.db_models.loan_disbursements import LoanDisbursement
from app.core.enums import DisbursementStatusEnum
from app.integrations.factory import PayoutProviderFactory


class DisbursementRetryService:

    MAX_RETRIES = 3

    @staticmethod
    def retry_failed_disbursements(db: Session):

        disbursements = (
            db.query(LoanDisbursement)
            .filter(
                LoanDisbursement.payment_status.in_([
                    DisbursementStatusEnum.FAILED,
                    DisbursementStatusEnum.INITIATED
                ]),
                LoanDisbursement.retry_count < DisbursementRetryService.MAX_RETRIES
            )
            .all()
        )

        for disbursement in disbursements:

            provider = PayoutProviderFactory.get_provider(
                disbursement.payment_mode.value
            )

            payout = provider.disburse(
                amount=disbursement.amount,
                account_number="stored_account_number",
                ifsc="stored_ifsc",
                name="stored_name",
                reference_id=f"retry_{disbursement.application_id}"
            )

            disbursement.payment_reference_id = payout.get("id")
            disbursement.retry_count += 1
            disbursement.last_retry_at = datetime.utcnow()

        db.commit()