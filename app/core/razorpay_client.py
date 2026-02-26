import razorpay
from app.core.config import settings

client = razorpay.Client(
    auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET)
)

# IMPORTANT: Set RazorpayX base URL
client.set_app_details({
    "title": "LoanApp",
    "version": "1.0"
})