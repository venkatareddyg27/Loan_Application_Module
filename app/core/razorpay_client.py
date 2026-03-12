import razorpay
import logging
from typing import Dict, Any, Optional
from razorpay.errors import BadRequestError, ServerError

from app.core.config import settings

logger = logging.getLogger(__name__)


class RazorpayClient:
    """
    Centralized Razorpay client for all Razorpay operations
    """

    _client: Optional[razorpay.Client] = None

    @classmethod
    def get_client(cls) -> razorpay.Client:
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


    @classmethod
    def create_contact(cls, payload: Dict[str, Any]) -> Dict[str, Any]:
        try:
            client = cls.get_client()
            response = client.contact.create(payload)

            logger.info(f"Contact created successfully: {response.get('id')}")
            return response

        except BadRequestError as e:
            logger.error(f"Razorpay Contact Bad Request: {str(e)}")
            raise Exception("Invalid contact request")

        except ServerError as e:
            logger.error(f"Razorpay Server Error: {str(e)}")
            raise Exception("Razorpay server error")

        except Exception as e:
            logger.exception("Unexpected error while creating contact")
            raise e


    @classmethod
    def create_fund_account(cls, payload: Dict[str, Any]) -> Dict[str, Any]:
        try:
            client = cls.get_client()
            response = client.fund_account.create(payload)

            logger.info(f"Fund account created: {response.get('id')}")
            return response

        except BadRequestError as e:
            logger.error(f"Razorpay Fund Account Bad Request: {str(e)}")
            raise Exception("Invalid fund account request")

        except Exception as e:
            logger.exception("Unexpected error while creating fund account")
            raise e


    @classmethod
    def create_payout(cls, payload: Dict[str, Any]) -> Dict[str, Any]:
        try:
            client = cls.get_client()
            response = client.payout.create(payload)

            logger.info(f"Payout created: {response.get('id')}")
            return response

        except BadRequestError as e:
            logger.error(f"Razorpay Payout Bad Request: {str(e)}")
            raise Exception("Invalid payout request")

        except ServerError as e:
            logger.error(f"Razorpay Server Error: {str(e)}")
            raise Exception("Razorpay server error")

        except Exception as e:
            logger.exception("Unexpected error while creating payout")
            raise e


    @classmethod
    def create_payment_link(cls, payload: Dict[str, Any]) -> Dict[str, Any]:
        try:
            client = cls.get_client()
            response = client.payment_link.create(payload)

            logger.info(f"Payment link created: {response.get('id')}")
            return response

        except BadRequestError as e:
            logger.error(f"Razorpay Payment Link Bad Request: {str(e)}")
            raise Exception("Invalid payment link request")

        except Exception as e:
            logger.exception("Unexpected error while creating payment link")
            raise e