from fastapi import APIRouter, Request
import hmac
import hashlib
from app.core.config import settings

router = APIRouter()


@router.post("/razorpay-webhook")
async def razorpay_webhook(request: Request):

    body = await request.body()
    signature = request.headers.get("X-Razorpay-Signature")

    expected_signature = hmac.new(
        settings.RAZORPAY_KEY_SECRET.encode(),
        body,
        hashlib.sha256
    ).hexdigest()

    if not hmac.compare_digest(signature, expected_signature):
        return {"error": "Invalid signature"}

    data = await request.json()

    event = data.get("event")

    if event == "payout.processed":
        payout_id = data["payload"]["payout"]["entity"]["id"]
        # Update DB → mark DISBURSED

    elif event == "payout.failed":
        # Update DB → mark FAILED

        return {"status": "ok"}