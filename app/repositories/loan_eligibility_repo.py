from sqlalchemy.orm import Session
from app.db_models.loan_eligibility import LoanEligibility
from uuid import UUID

class LoanEligibilityRepository:

    @staticmethod
    def create(db: Session, eligibility: LoanEligibility):
        db.add(eligibility)
        db.commit()
        db.refresh(eligibility)
        return eligibility

    @staticmethod
    def get_by_id(db: Session, eligibility_id: UUID):
        return db.query(LoanEligibility).filter(LoanEligibility.id == eligibility_id).first()
