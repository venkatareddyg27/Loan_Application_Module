from fastapi import APIRouter, Request, Header, HTTPException, Depends
from sqlalchemy.orm import Session
import hmac
import hashlib
import json

from app.core.session import get_db
from app.core.config import settings
from app.db_models.loan_disbursements import LoanDisbursement
from app.core.enums import DisbursementStatusEnum

router = APIRouter(prefix="/webhooks", tags=["Webhooks"])


def verify_signature(body: bytes, signature: str):

    generated_signature = hmac.new(
        settings.RAZORPAY_WEBHOOK_SECRET.encode(),
        body,
        hashlib.sha256
    ).hexdigest()

    if not hmac.compare_digest(generated_signature, signature):
        raise HTTPException(status_code=400, detail="Invalid webhook signature")


@router.post("/razorpay")
async def razorpay_webhook(
    request: Request,
    x_razorpay_signature: str = Header(None),
    db: Session = Depends(get_db)
):

    body = await request.body()

    # verify_signature(body, x_razorpay_signature)

    payload = json.loads(body)

    payout = payload["payload"]["payout"]["entity"]

    payout_id = payout["id"]

    disbursement = (
        db.query(LoanDisbursement)
        .filter(LoanDisbursement.payment_reference_id == payout_id)
        .first()
    )

    if disbursement:
        disbursement.payment_status = DisbursementStatusEnum.SUCCESS
        db.commit()

    return {"message": "Webhook processed"}