import uuid
from decimal import Decimal
from typing import Dict, Any

from app.integrations.base_payout import BasePayoutProvider


class RazorpayPayoutProvider(BasePayoutProvider):

    # ---------------------------------------------------------
    # Fake Contact Creation
    # ---------------------------------------------------------
    def create_contact(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "id": f"demo_contact_{uuid.uuid4().hex[:8]}",
            "entity": "contact"
        }

    # ---------------------------------------------------------
    # Fake Fund Account Creation
    # ---------------------------------------------------------
    def create_fund_account(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "id": f"demo_fund_{uuid.uuid4().hex[:8]}",
            "entity": "fund_account"
        }

    # ---------------------------------------------------------
    # Fake Payout
    # ---------------------------------------------------------
    def initiate_payout(self, payload: Dict[str, Any]) -> Dict[str, Any]:

        return {
            "id": f"demo_payout_{uuid.uuid4().hex[:10]}",
            "status": "processed",
            "reference_id": payload.get("reference_id"),
            "amount": payload.get("amount"),
            "currency": "INR"
        }

    # ---------------------------------------------------------
    # Build Payout Payload
    # ---------------------------------------------------------
    def build_payout_payload(
        self,
        fund_account_id: str,
        amount: Decimal,
        reference: str
    ) -> Dict[str, Any]:

        return {
            "fund_account_id": fund_account_id,
            "amount": float(amount),
            "reference_id": reference
        }

    # ---------------------------------------------------------
    # MAIN DISBURSE METHOD (Required by BasePayoutProvider)
    # ---------------------------------------------------------
    def disburse(
        self,
        amount,
        account_number,
        ifsc,
        name,
        reference_id
    ) -> Dict[str, Any]:

        # 1️⃣ Create Contact
        contact = self.create_contact({
            "name": name
        })

        # 2️⃣ Create Fund Account
        fund_account = self.create_fund_account({
            "contact_id": contact["id"],
            "account_number": account_number,
            "ifsc": ifsc
        })

        # 3️⃣ Build Payout Payload
        payout_payload = self.build_payout_payload(
            fund_account_id=fund_account["id"],
            amount=Decimal(amount),
            reference=reference_id
        )

        # 4️⃣ Initiate Payout
        payout = self.initiate_payout(payout_payload)

        return payout