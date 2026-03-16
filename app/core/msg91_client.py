import requests
from app.core.config import settings

def send_msg91_otp(mobile_number: str, otp: str) -> dict:
    """
    Send OTP via MSG91 API.
    mobile_number: with country code, e.g. '919876543210'
    """
    url = "https://api.msg91.com/api/v5/otp"
    params = {
        "authkey": settings.MSG91_AUTH_KEY,
        "template_id": settings.MSG91_TEMPLATE_ID,
        "mobile": mobile_number,
        "otp": otp,
        "sender": settings.MSG91_SENDER_ID,
        "otp_expiry": OTP_EXPIRY_SECONDS // 60,  # in minutes
    }

    response = requests.get(url, params=params, timeout=10)
    return response.json()