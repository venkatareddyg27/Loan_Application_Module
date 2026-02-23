from sqlalchemy.orm import Session
from app.db_models.loan_application_purpose import LoanApplicationPurpose


class LoanApplicationPurposeRepository:

    @staticmethod
    def get_by_application_id(db: Session, application_id):
        return (
            db.query(LoanApplicationPurpose)
            .filter(LoanApplicationPurpose.application_id == application_id)
            .first())

    @staticmethod
    def create(db: Session, purpose: LoanApplicationPurpose):
        db.add(purpose)
        db.commit()
        db.refresh(purpose)
        return purpose

    @staticmethod
    def update(db: Session):
        db.commit()
