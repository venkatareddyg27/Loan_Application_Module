from sqlalchemy import (
    Column,
    ForeignKey,
    DECIMAL,
    String,
    Text,
    DateTime,
    Integer,
    Enum as SqlEnum)
from sqlalchemy.orm import relationship
from datetime import datetime
from app.core.session import Base
from app.core.enums import EligibilityStatusEnum


class LoanEligibility(Base):
    __tablename__ = "loan_eligibility"

    id = Column(Integer, primary_key=True, index=True)

    user_profile_id = Column(
        ForeignKey("user_profiles.id"),
        nullable=False)

    eligibility_status = Column(
        SqlEnum(EligibilityStatusEnum, name="eligibility_status_enum"),
        nullable=False)

    income_used = Column(DECIMAL(12, 2), nullable=True)
    existing_emi = Column(DECIMAL(12, 2), default=0.00)
    proposed_emi = Column(DECIMAL(12, 2), nullable=True)
    foir_ratio = Column(DECIMAL(5, 2), nullable=True)
    max_allowed_foir = Column(DECIMAL(5, 2), default=0.50)
    previous_credit_score_used = Column(Integer, nullable=True)
    credit_score_used = Column(Integer, nullable=True)
    bureau_name = Column(String(50))
    max_eligible_amount = Column(DECIMAL(12, 2), default=0.00)
    max_eligible_emi = Column(DECIMAL(12, 2), default=0.00)
    failure_reason = Column(Text)
    previously_checked_at = Column(DateTime, nullable=True)
    latest_checked_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    user = relationship("UserProfile", back_populates="loan_eligibility")

    loan_applications = relationship(
        "LoanApplication",
        back_populates="eligibility",
        cascade="all, delete-orphan")
