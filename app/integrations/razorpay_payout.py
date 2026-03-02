import uuid
from decimal import Decimal


class RazorpayPayoutProvider:

    # ---------------------------------------------------------
    # 👤 Fake Contact Creation
    # ---------------------------------------------------------
    def create_contact(self, payload: dict) -> dict:
        return {
            "id": f"demo_contact_{uuid.uuid4().hex[:8]}",
            "entity": "contact"
        }

    # ---------------------------------------------------------
    # 🏦 Fake Fund Account Creation
    # ---------------------------------------------------------
    def create_fund_account(self, payload: dict) -> dict:
        return {
            "id": f"demo_fund_{uuid.uuid4().hex[:8]}",
            "entity": "fund_account"
        }

    # ---------------------------------------------------------
    # 💰 Build Payout Payload (Still Used by Service)
    # ---------------------------------------------------------
    def build_payout_payload(
        self,
        fund_account_id: str,
        amount: Decimal,
        reference: str
    ) -> dict:

        return {
            "fund_account_id": fund_account_id,
            "amount": float(amount),
            "reference_id": reference
        }

    # ---------------------------------------------------------
    # 🚀 Fake Payout
    # ---------------------------------------------------------
    def initiate_payout(self, payload: dict) -> dict:

        return {
            "id": f"demo_payout_{uuid.uuid4().hex[:10]}",
            "status": "processed",  # directly success
            "reference_id": payload.get("reference_id"),
            "amount": payload.get("amount"),
            "currency": "INR"
        }