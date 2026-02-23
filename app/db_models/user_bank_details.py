from sqlalchemy import (
    Column,
    Integer,
    String,
    Boolean,
    DateTime,
    ForeignKey,
    Enum,
    UniqueConstraint)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.core.session import Base
from app.core.enums import PaymentModeEnum


class UserBankDetails(Base):
    __tablename__ = "user_bank_details"

    id = Column(Integer, primary_key=True, index=True)

    user_id = Column(
        ForeignKey("user_profiles.id", ondelete="CASCADE"),
        nullable=False,
        index=True)

    #  Payment Mode (BANK / UPI)
    payment_mode = Column(
        Enum(PaymentModeEnum),
        nullable=False,
        index=True)

    #  BANK DETAILS
    account_number = Column(String(30), nullable=True)
    ifsc_code = Column(String(15), nullable=True)
    account_holder_name = Column(String(150), nullable=True)

    #  UPI DETAILS
    upi_id = Column(String(100), nullable=True)

    #  Verification
    is_verified = Column(Boolean, default=False, nullable=False)

    #  Primary payout method
    is_primary = Column(Boolean, default=True, nullable=False)

    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())

    #  Relationship
    user = relationship(
        "UserProfile",
        back_populates="bank_details")

    # Prevent duplicate account or UPI per user
    __table_args__ = (
        UniqueConstraint(
            "user_id",
            "account_number",
            name="uq_user_account_number"
        ),
        UniqueConstraint(
            "user_id",
            "upi_id",
            name="uq_user_upi_id"
        ),
    )
