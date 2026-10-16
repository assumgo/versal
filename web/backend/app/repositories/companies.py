from sqlalchemy import select
from sqlalchemy.orm import Session
from app.models.company import Company
from app.models.user import UserCompany


def list_for_user(db: Session, user_id: int):
    return db.scalars(select(Company).join(UserCompany).where(
        UserCompany.user_id == user_id).order_by(Company.id)).all()


def lock_company(db: Session, company_id: int) -> Company:
    return db.scalar(select(Company).where(Company.id == company_id).with_for_update()
                     .execution_options(populate_existing=True))
