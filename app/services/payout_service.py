from decimal import Decimal
from app.core.razorpay_client import RazorpayClient
from app.core.config import settings


class RazorpayPayoutService:

    @staticmethod
    def create_contact(user):

        payload = {
            "name": user.full_name,
            "email": user.email,
            "contact": user.phone_number,
            "type": "customer"
        }

        return RazorpayClient.create_contact(payload)

    @staticmethod
    def create_fund_account(contact_id, bank):

        payload = {
            "contact_id": contact_id,
            "account_type": "bank_account",
            "bank_account": {
                "name": bank.account_holder_name,
                "ifsc": bank.ifsc_code,
                "account_number": bank.account_number
            }
        }

        return RazorpayClient.create_fund_account(payload)

    @staticmethod
    def initiate_payout(amount: Decimal, fund_account_id: str, reference: str):

        payload = {
            "account_number": settings.RAZORPAY_ACCOUNT_NUMBER,
            "fund_account_id": fund_account_id,
            "amount": int(amount * 100),  # convert to paise
            "currency": "INR",
            "mode": "IMPS",
            "purpose": "loan_disbursement",
            "reference_id": reference,
            "queue_if_low_balance": True
        }

        return RazorpayClient.create_payout(payload)