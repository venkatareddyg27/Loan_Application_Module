from app.integrations.razorpay_payout import RazorpayPayoutProvider


class PayoutProviderFactory:

    @staticmethod
    def get_provider(provider_name: str):
        if provider_name == "razorpay":
            return RazorpayPayoutProvider()

        raise ValueError("Unsupported provider")