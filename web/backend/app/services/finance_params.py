from sqlalchemy.orm import Session

from app.models import FinanceParam, User
from app.schemas.finance_params import FinanceParamCreate
from app.services.companies import save
from app.services.employees import require_active


def create(db: Session, company_id: int, payload: FinanceParamCreate, actor: User, ip: str | None) -> FinanceParam:
    require_active(db, company_id)
    values = payload.model_dump()
    row = FinanceParam(company_id=company_id, **values)
    db.add(row)
    save(db, row, actor, 'finance_param.create', 'finance_params', company_id, ip, values.keys())
    return row
