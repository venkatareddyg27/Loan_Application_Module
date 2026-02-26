from app.core.razorpay_client import client
from app.core.config import settings


class RazorpayPayoutService:

    @staticmethod
    def create_contact(user):
        return client.contact.create({
            "name": user.full_name,
            "type": "customer",
            "reference_id": f"user_{user.id}",
        })

    @staticmethod
    def create_fund_account(contact_id, bank):
        return client.fund_account.create({
            "contact_id": contact_id,
            "account_type": "bank_account",
            "bank_account": {
                "name": bank.account_holder_name,
                "ifsc": bank.ifsc_code,
                "account_number": bank.account_number
            }
        })

    @staticmethod
    def initiate_payout(amount, fund_account_id, loan_id):

        return client.payout.create({
            "account_number": settings.RAZORPAY_ACCOUNT_NUMBER,
            "fund_account_id": fund_account_id,
            "amount": int(amount * 100),
            "currency": "INR",
            "mode": "IMPS",
            "purpose": "payout",
            "queue_if_low_balance": True,
            "reference_id": f"loan_{loan_id}",
            "narration": "Loan Disbursement"
        })