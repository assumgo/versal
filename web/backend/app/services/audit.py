from datetime import datetime

from sqlalchemy.orm import Session

from app.models.audit import AuditLog


def write_audit(
    db: Session, *, actor_id: int | None, action: str, entity: str,
    entity_id: int | None = None, company_id: int | None = None,
    details: dict | None = None, ip_address: str | None = None,
    created_at: datetime | None = None,
) -> AuditLog:
    """Stage an audit event in the caller's transaction.

    Callers must supply only explicitly permitted metadata, never credentials.
    """
    entry = AuditLog(actor_id=actor_id, company_id=company_id, action=action,
                     entity=entity, entity_id=entity_id, details=details,
                     ip_address=ip_address, created_at=created_at,
                     updated_at=created_at)
    db.add(entry)
    db.flush()
    return entry
