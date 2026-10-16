from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.company import Company
from app.models.user import User, UserCompany


def require_company_access(db: Session, company_id: int, user: User) -> Company:
    """No role bypass: company data always requires an explicit membership."""
    company = db.scalar(select(Company).join(UserCompany).where(
        Company.id == company_id, UserCompany.user_id == user.id))
    if not user.is_active or company is None:
        # The same denial for an absent company prevents identifier enumeration.
        raise HTTPException(status_code=403, detail='Acesso negado')
    return company
