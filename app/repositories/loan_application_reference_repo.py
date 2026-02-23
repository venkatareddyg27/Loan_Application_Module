from sqlalchemy.orm import Session
from app.db_models.loan_application_references import LoanApplicationReference


class LoanApplicationReferenceRepository:

    @staticmethod
    def get_by_application_id(db: Session, application_id):
        return (
            db.query(LoanApplicationReference)
            .filter(LoanApplicationReference.application_id == application_id)
            .all())

    @staticmethod
    def get_by_id(db: Session, reference_id):
        return (
            db.query(LoanApplicationReference)
            .filter(LoanApplicationReference.id == reference_id)
            .first())

    @staticmethod
    def create(db: Session, reference: LoanApplicationReference):
        db.add(reference)
        db.commit()
        db.refresh(reference)
        return reference

    @staticmethod
    def delete_by_application_id(db: Session, application_id):
        db.query(LoanApplicationReference)\
        .filter_by(application_id=application_id)\
        .delete()
        db.commit()
