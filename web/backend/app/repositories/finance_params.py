from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import FinanceParam


def list_for_company(db: Session, company_id: int, *, offset: int = 0, limit: int = 50) -> dict:
    scope = FinanceParam.company_id == company_id
    return {
        'items': db.scalars(select(FinanceParam).where(scope).order_by(
            FinanceParam.tipo.nulls_first(), FinanceParam.id).offset(offset).limit(limit)).all(),
        'total': db.scalar(select(func.count()).select_from(FinanceParam).where(scope)),
        'offset': offset, 'limit': limit,
    }
