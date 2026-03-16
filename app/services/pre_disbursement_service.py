from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.db_models.loan_application import LoanApplication
from app.services.loan_calculator import calculate_loan_summary
from app.db_models.lender import Lender


class PreDisbursementService:

    @staticmethod
    def get_preview(db: Session, application_id: int):

        application = db.get(LoanApplication, application_id)

        if not application:
            raise HTTPException(404, "Application not found")

        if not application.approved_amount:
            raise HTTPException(
                400,
                "Approved amount missing"
            )

        if not application.requested_tenure_months:
            raise HTTPException(
                400,
                "Tenure not found"
            )

        try:
            loan_calc = calculate_loan_summary(
                principal=application.approved_amount,
                tenure_months=application.requested_tenure_months
            )
        except ValueError as e:
            raise HTTPException(400, str(e))

        # Fetch lender
        lender = db.query(Lender).filter(
            Lender.id == application.lender_id 
        ).first()

        return {
            "application_id": application.id,
            "lender_name": lender.company_name if lender else None,
            "current_status": application.application_status.value,

            "approved_amount": loan_calc["approved_amount"],
            "tenure_months": loan_calc["tenure_months"],
            "interest_rate_percent": loan_calc["interest_rate"],
            "emi_amount": loan_calc["emi"],
            "total_repayment": loan_calc["total_repayment"],

            # Charges breakdown
            "processing_fee": loan_calc["processing_fee"],
            "gst_on_processing_fee": loan_calc["gst_on_processing_fee"],
            "total_processing_charges": loan_calc["total_processing_charges"],

            # Final payout amount
            "net_disbursement_amount": loan_calc["net_disbursement_amount"]
        }