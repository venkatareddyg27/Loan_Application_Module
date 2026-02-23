from sqlalchemy.orm import Session
from datetime import datetime, timedelta, timezone
import random
import hashlib
from fastapi import HTTPException

from app.db_models.loan_application_references_otp import ReferenceMobileOTP
from app.db_models.loan_application_steps import LoanApplicationStepTracker
from app.db_models.loan_application import LoanApplication
from app.repositories.loan_application_reference_repo import LoanApplicationReferenceRepository
from app.core.enums import LoanApplicationStep, enum_value


COOLDOWN_SECONDS = 30
MAX_OTP_PER_IP_10_MIN = 5
OTP_EXPIRY_MINUTES = 5
MAX_ATTEMPTS = 3


class ReferenceOTPService:

    @staticmethod
    def send_reference_otp(db: Session, reference_id: int, client_ip: str):

        reference = LoanApplicationReferenceRepository.get_by_id(db, reference_id)
        if not reference:
            raise HTTPException(status_code=404, detail="Reference not found")

        now = datetime.now(timezone.utc)

        # Cooldown check
        cooldown_time = now - timedelta(seconds=COOLDOWN_SECONDS)

        recent_otp = db.query(ReferenceMobileOTP).filter(
            ReferenceMobileOTP.reference_id == reference_id,
            ReferenceMobileOTP.created_at >= cooldown_time
        ).first()

        if recent_otp:
            raise HTTPException(
                status_code=400,
                detail="Please wait before requesting OTP again"
            )

        # IP rate limit
        ten_min_ago = now - timedelta(minutes=10)

        otp_count = db.query(ReferenceMobileOTP).filter(
            ReferenceMobileOTP.ip_address == client_ip,
            ReferenceMobileOTP.created_at >= ten_min_ago
        ).count()

        if otp_count >= MAX_OTP_PER_IP_10_MIN:
            raise HTTPException(
                status_code=429,
                detail="Too many OTP requests from this IP"
            )

        # Invalidate old unused OTPs
        old_otps = db.query(ReferenceMobileOTP).filter(
            ReferenceMobileOTP.reference_id == reference_id,
            ReferenceMobileOTP.is_used == False
        ).all()

        for otp in old_otps:
            otp.is_used = True

        # Generate OTP
        otp_plain = str(random.randint(100000, 999999))
        hashed_otp = hashlib.sha256(otp_plain.encode()).hexdigest()

        new_otp = ReferenceMobileOTP(
            reference_id=reference_id,
            otp_code=hashed_otp,
            expires_at=now + timedelta(minutes=OTP_EXPIRY_MINUTES),
            attempts=0,
            is_used=False,
            ip_address=client_ip
        )

        db.add(new_otp)
        db.commit()

        #  Replace this with SMS provider integration
        print(f"Reference OTP (Dev Mode): {otp_plain}")

        return {"message": "OTP sent successfully"}

    @staticmethod
    def verify_reference_otp(db: Session, payload, client_ip: str):

        now = datetime.now(timezone.utc)

        otp = db.query(ReferenceMobileOTP).filter(
            ReferenceMobileOTP.reference_id == payload.reference_id,
            ReferenceMobileOTP.is_used == False
        ).order_by(ReferenceMobileOTP.created_at.desc()).first()

        if not otp:
            raise HTTPException(
                status_code=400,
                detail="No active OTP found"
            )

        if otp.expires_at < now:
            otp.is_used = True
            db.commit()
            raise HTTPException(
                status_code=400,
                detail="OTP expired. Please request new OTP."
            )

        if otp.attempts >= MAX_ATTEMPTS:
            otp.is_used = True
            db.commit()
            raise HTTPException(
                status_code=400,
                detail="OTP attempts exceeded"
            )

        hashed_input = hashlib.sha256(
            payload.otp_code.encode()
        ).hexdigest()

        if otp.otp_code != hashed_input:
            otp.attempts += 1
            db.commit()
            raise HTTPException(
                status_code=400,
                detail="Invalid OTP"
            )

        # SUCCESS
        otp.is_used = True
        otp.verified_at = now
        otp.reference.is_verified = True

        db.commit()
        db.refresh(otp.reference)

        # Update step if all references verified
        ReferenceOTPService.update_application_step_if_references_verified(
            db,
            otp.reference.application_id)

        return {
            "reference_id": payload.reference_id,
            "verified": True,
            "verified_at": otp.verified_at
        }

    @staticmethod
    def update_application_step_if_references_verified(
        db: Session,
        application_id
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
            tracker.last_completed_step = enum_value(
                LoanApplicationStep.REFERENCES
            )
            tracker.current_step = enum_value(
                LoanApplicationStep.DECLARATION
            )

            application = db.get(LoanApplication, application_id)
            if application:
                application.current_step = enum_value(
                    LoanApplicationStep.DECLARATION
                )

            db.commit()
