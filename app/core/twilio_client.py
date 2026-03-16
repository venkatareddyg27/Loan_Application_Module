from twilio.rest import Client
from app.core.config import settings

twilio_client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)

def send_twilio_otp(mobile_number: str, otp: str):
    """
    Send OTP via Twilio.
    mobile_number: with country code, e.g. '+919876543210'
    """
    message = twilio_client.messages.create(
        body=f"Your OTP is {otp}. Valid for 5 minutes. Do not share it.",
        from_=settings.TWILIO_PHONE_NUMBER,
        to=mobile_number
    )
    return message.sid