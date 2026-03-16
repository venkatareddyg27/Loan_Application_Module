from sqlalchemy.orm import Session
from datetime import datetime, timezone
import random
import hashlib
from fastapi import HTTPException
import logging

#  REDIS ENABLED
from app.core.redis_client import redis_client

#  TWILIO
from twilio.rest import Client
from app.core.config import settings

from app.db_models.loan_application_steps import LoanApplicationStepTracker
from app.db_models.loan_application import LoanApplication
from app.repositories.loan_application_reference_repo import LoanApplicationReferenceRepository
from app.core.enums import LoanApplicationStep, enum_value

# ==========================================
# REDIS CONFIG
# ==========================================
COOLDOWN_SECONDS = 30
OTP_EXPIRY_SECONDS = 300
MAX_ATTEMPTS = 3
MAX_OTP_PER_IP_10_MIN = 5
MAX_RESENDS = 3

logger = logging.getLogger(__name__)


# ==========================================
# TWILIO CLIENT
# ==========================================
twilio_client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)


class ReferenceOTPService:

    @staticmethod
    def _otp_key(reference_id: int):
        return f"ref_otp:{reference_id}"

    @staticmethod
    def _ip_key(ip: str):
        return f"otp_ip:{ip}"

    @staticmethod
    def _resend_key(reference_id: int):
        return f"ref_resend:{reference_id}"

    # ==============================
    # SEND OTP
    # ==============================
    @staticmethod
    def send_reference_otp(db: Session, reference_id: int, client_ip: str):

        reference = LoanApplicationReferenceRepository.get_by_id(db, reference_id)
        if not reference:
            raise HTTPException(status_code=404, detail="Reference not found")

        if not reference.mobile_number:
            raise HTTPException(status_code=400, detail="Reference mobile number missing")

        otp_key    = ReferenceOTPService._otp_key(reference_id)
        ip_key     = ReferenceOTPService._ip_key(client_ip)
        resend_key = ReferenceOTPService._resend_key(reference_id)

        # ✅ Cooldown Check
        if redis_client.exists(otp_key):
            ttl = redis_client.ttl(otp_key)
            if ttl > (OTP_EXPIRY_SECONDS - COOLDOWN_SECONDS):
                remaining = COOLDOWN_SECONDS - (OTP_EXPIRY_SECONDS - ttl)
                raise HTTPException(
                    status_code=400,
                    detail=f"Please wait {remaining} seconds before requesting OTP again"
                )

        # ✅ IP Rate Limit
        ip_count = redis_client.get(ip_key)
        if ip_count and int(ip_count) >= MAX_OTP_PER_IP_10_MIN:
            raise HTTPException(
                status_code=429,
                detail="Too many OTP requests from this IP"
            )

        redis_client.incr(ip_key)
        redis_client.expire(ip_key, 600)

        # ✅ Resend Limit
        resend_count = redis_client.get(resend_key)
        if resend_count and int(resend_count) >= MAX_RESENDS:
            raise HTTPException(
                status_code=400,
                detail="Maximum OTP resend attempts reached"
            )

        redis_client.incr(resend_key)
        redis_client.expire(resend_key, OTP_EXPIRY_SECONDS)

        # ✅ Generate OTP
        otp_plain  = str(random.randint(100000, 999999))
        hashed_otp = hashlib.sha256(otp_plain.encode()).hexdigest()

        redis_client.hset(otp_key, mapping={
            "otp":      hashed_otp,
            "attempts": 0
        })
        redis_client.expire(otp_key, OTP_EXPIRY_SECONDS)

        # ✅ Print OTP in terminal (DEV ONLY)
        print(f"\n========== OTP (DEV ONLY) ==========")
        print(f"Reference ID : {reference_id}")
        print(f"Mobile       : {reference.mobile_number}")
        print(f"OTP          : {otp_plain}")
        print(f"====================================\n")

        # ✅ Fix mobile number format for Twilio (+91XXXXXXXXXX)
        mobile = reference.mobile_number.strip().replace(" ", "")
        if not mobile.startswith("+"):
            mobile = "+" + mobile
        if not mobile.startswith("+91"):
            mobile = "+91" + mobile.lstrip("+")

        # ✅ TWILIO SMS SENDING
        try:
            message = twilio_client.messages.create(
                body=f"Your OTP is {otp_plain}. Valid for 5 minutes. Do not share it.",
                from_=settings.TWILIO_PHONE_NUMBER,
                to=mobile
            )

            logger.info(f"OTP sent via Twilio for reference {reference_id} to {mobile} | SID: {message.sid}")

        except Exception as e:
            redis_client.delete(otp_key)
            logger.error(f"Twilio error for reference {reference_id}: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail=f"SMS sending failed: {str(e)}"
            )

        return {
            "message": "OTP sent successfully"
        }

    # ==============================
    # RESEND OTP
    # ==============================
    @staticmethod
    def resend_reference_otp(db: Session, reference_id: int, client_ip: str):

        reference = LoanApplicationReferenceRepository.get_by_id(db, reference_id)
        if not reference:
            raise HTTPException(status_code=404, detail="Reference not found")

        if reference.is_verified:
            raise HTTPException(
                status_code=400,
                detail="Reference already verified"
            )

        return ReferenceOTPService.send_reference_otp(
            db,
            reference_id,
            client_ip
        )

    # ==============================
    # VERIFY OTP
    # ==============================
    @staticmethod
    def verify_reference_otp(db: Session, payload, client_ip: str):

        otp_key = ReferenceOTPService._otp_key(payload.reference_id)

        data = redis_client.hgetall(otp_key)

        if not data:
            raise HTTPException(
                status_code=400,
                detail="OTP expired or not found"
            )

        attempts = int(data.get("attempts", 0))

        if attempts >= MAX_ATTEMPTS:
            redis_client.delete(otp_key)
            raise HTTPException(
                status_code=400,
                detail="OTP attempts exceeded"
            )

        hashed_input = hashlib.sha256(
            payload.otp_code.encode()
        ).hexdigest()

        if data["otp"] != hashed_input:
            redis_client.hincrby(otp_key, "attempts", 1)
            raise HTTPException(
                status_code=400,
                detail="Invalid OTP"
            )

        # ✅ SUCCESS
        redis_client.delete(otp_key)

        reference = LoanApplicationReferenceRepository.get_by_id(
            db, payload.reference_id
        )

        if not reference:
            raise HTTPException(status_code=404, detail="Reference not found")

        reference.is_verified = True
        db.commit()

        ReferenceOTPService.update_application_step_if_references_verified(
            db,
            reference.application_id
        )

        return {
            "reference_id": payload.reference_id,
            "verified":     True,
            "verified_at":  datetime.now(timezone.utc)
        }

    # ==============================
    # UPDATE APPLICATION STEP
    # ==============================
    @staticmethod
    def update_application_step_if_references_verified(
        db: Session,
        application_id: int
    ):

        references = LoanApplicationReferenceRepository.get_by_application_id(
            db, application_id
        )

        if not references:
            return

        if all(ref.is_verified for ref in references):

            tracker = db.query(LoanApplicationStepTracker).filter_by(
                application_id=application_id
            ).first()

            if not tracker:
                return

            tracker.references_completed = True
            tracker.last_completed_step  = enum_value(LoanApplicationStep.REFERENCES)
            tracker.current_step         = enum_value(LoanApplicationStep.DECLARATION)

            application = db.get(LoanApplication, application_id)
            if application:
                application.current_step = enum_value(LoanApplicationStep.DECLARATION)

            db.commit()