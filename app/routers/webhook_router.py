from fastapi import APIRouter, Request, HTTPException, Depends
from sqlalchemy.orm import Session
import hmac
import hashlib
import json
import logging

from app.core.config import settings
from app.core.session import get_db
from app.services.loan_disbursement_service import LoanDisbursementService

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/razorpay-webhook")
async def razorpay_webhook(
    request: Request,
    db: Session = Depends(get_db)
):


    # 1️ Read Raw Body

    body = await request.body()
    signature = request.headers.get("X-Razorpay-Signature")

    if not signature:
        raise HTTPException(400, "Missing Razorpay signature header")


    # 2️ Verify Signature

    expected_signature = hmac.new(
        settings.RAZORPAY_SECRET.encode(),  # ensure correct variable name
        body,
        hashlib.sha256
    ).hexdigest()

    if not hmac.compare_digest(signature, expected_signature):
        logger.warning("Invalid Razorpay webhook signature")
        raise HTTPException(400, "Invalid signature")


    # 3️ Parse JSON Safely

    try:
        data = json.loads(body.decode())
    except Exception:
        raise HTTPException(400, "Invalid JSON payload")

    event = data.get("event")

    if not event:
        raise HTTPException(400, "Missing event type")

    logger.info(f"Razorpay Webhook Event Received: {event}")


    # 4️ Handle Payout Events

    if event in ["payout.processed", "payout.failed", "payout.reversed"]:

        payout_entity = data.get("payload", {}).get("payout", {}).get("entity", {})

        payout_id = payout_entity.get("id")
        payout_status = payout_entity.get("status")

        if not payout_id or not payout_status:
            raise HTTPException(400, "Invalid payout payload")

        #  Update Loan Based on Payout Status
        LoanDisbursementService.update_payout_status(
            db=db,
            payout_id=payout_id,
            status=payout_status
        )

        logger.info(
            f"Payout updated: payout_id={payout_id}, status={payout_status}"
        )

    else:
        # Ignore unrelated events safely
        logger.info(f"Ignored Razorpay event: {event}")


    # 5️ Always Respond 200 to Razorpay

    return {"status": "success"}