from app.integrations.razorpay_payout import RazorpayPayoutProvider
from app.integrations.paytm_payout import PaytmPayoutProvider
from app.integrations.mock_payout import MockPayoutProvider


class PayoutProviderFactory:

    @staticmethod
    def get_provider(provider_name: str):

        provider_name = provider_name.lower()

        if provider_name == "razorpay":
            return RazorpayPayoutProvider()

        if provider_name == "paytm":
            return PaytmPayoutProvider()

        if provider_name == "mock":
            return MockPayoutProvider()

        raise ValueError("Unsupported provider")