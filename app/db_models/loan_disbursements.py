from sqlalchemy import Column, Integer, Numeric, String, DateTime, ForeignKey, Enum
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.core.session import Base
from app.core.enums import DisbursementStatusEnum,PaymentModeEnum

class LoanDisbursement(Base):
    __tablename__ = "loan_disbursements"

    id = Column(Integer, primary_key=True, index=True)

    application_id = Column(
        ForeignKey("loan_applications.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    amount = Column(Numeric(12, 2), nullable=False)

    payment_reference_id = Column(String, nullable=True)

    payment_status = Column(
        Enum(DisbursementStatusEnum),
        default=DisbursementStatusEnum.INITIATED,
        nullable=False
    )

    payment_mode = Column(Enum(PaymentModeEnum))

    retry_count = Column(Integer, default=0)  # retry tracker
    last_retry_at = Column(DateTime, nullable=True)

    initiated_at = Column(DateTime, server_default=func.now())
    completed_at = Column(DateTime, nullable=True)

    loan_application = relationship(
        "LoanApplication",
        back_populates="disbursements"
    )