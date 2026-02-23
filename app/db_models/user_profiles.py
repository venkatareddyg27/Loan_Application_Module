from datetime import datetime
from sqlalchemy import (
    Column, String, Date, DateTime,
    DECIMAL, Boolean, Index, Integer
)
from app.core.session import Base
from sqlalchemy.orm import relationship


class UserProfile(Base):
    __tablename__ = "user_profiles"

    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    auth_user_id = Column(String, nullable=True, unique=True)
    full_name = Column(String(150), nullable=False)
    dob = Column(Date, nullable=False)
    email = Column(String(120), unique=True, nullable=False, index=True)
    address = Column(String, nullable=False)
    employment_type = Column(String(50), nullable=False)
    monthly_income = Column(DECIMAL(12, 2), nullable=False)
    aadhaar_number = Column(String(12), nullable=False)
    pan_number = Column(String(10), unique=True, nullable=False, index=True)
    verified_name = Column(String(150), nullable=True)
    profile_status = Column(String(20), default="PROFILE_COMPLETED", nullable=False)
    pan_status = Column(String(20), default="PENDING", nullable=False)
    aadhaar_status = Column(String(20), default="PENDING", nullable=False)
    bank_status = Column(String(20), default="PENDING", nullable=False)
    identity_status = Column(String(20), default="PENDING", nullable=False)
    document_status = Column(String(20), default="PENDING", nullable=False)
    kyc_status = Column(String(20), default="INCOMPLETE", nullable=False)
    pan_locked = Column(Boolean, default=False, nullable=False)
    aadhaar_locked = Column(Boolean, default=False, nullable=False)
    dob_locked = Column(Boolean, default=False, nullable=False)
    name_locked = Column(Boolean, default=False, nullable=False)
    bank_locked = Column(Boolean, default=False, nullable=False)
    pan_verified_at = Column(DateTime, nullable=True)
    aadhaar_verified_at = Column(DateTime, nullable=True)
    bank_verified_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow,
                        onupdate=datetime.utcnow, nullable=False)

    __table_args__ = (
        Index('idx_status_composite', 'pan_status', 'aadhaar_status', 'bank_status'),
        Index('idx_kyc_status', 'kyc_status'),
        Index('idx_identity_status', 'identity_status'),)

    loan_applications = relationship(
        "LoanApplication",
        back_populates="user_profile",
        cascade="all, delete-orphan")

    loan_eligibility = relationship(
        "LoanEligibility",
        back_populates="user",
        cascade="all, delete-orphan")

    bank_details = relationship(
    "UserBankDetails",
    back_populates="user",
    cascade="all, delete-orphan")