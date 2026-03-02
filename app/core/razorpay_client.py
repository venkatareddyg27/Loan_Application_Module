import razorpay
import logging
from typing import Dict, Any
from app.core.config import settings

logger = logging.getLogger(__name__)


class RazorpayClient:

    _client = None

    @classmethod
    def get_client(cls):
        """
        Singleton Razorpay client instance
        """
        if cls._client is None:
            cls._client = razorpay.Client(
                auth=(
                    settings.RAZORPAY_KEY_ID,
                    settings.RAZORPAY_KEY_SECRET
                )
            )
        return cls._client


    # CONTACT

    @classmethod
    def create_contact(cls, payload: Dict[str, Any]) -> Dict[str, Any]:
        try:
            client = cls.get_client()
            return client.contact.create(payload)
        except Exception as e:
            logger.error(f"Razorpay Contact Creation Failed: {str(e)}")
            raise


    # FUND ACCOUNT

    @classmethod
    def create_fund_account(cls, payload: Dict[str, Any]) -> Dict[str, Any]:
        try:
            client = cls.get_client()
            return client.fund_account.create(payload)
        except Exception as e:
            logger.error(f"Razorpay Fund Account Creation Failed: {str(e)}")
            raise


    # PAYOUT

    @classmethod
    def create_payout(cls, payload: Dict[str, Any]) -> Dict[str, Any]:
        try:
            client = cls.get_client()
            return client.payout.create(payload)
        except Exception as e:
            logger.error(f"Razorpay Payout Failed: {str(e)}")
            raise