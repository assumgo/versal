from sqlalchemy import ForeignKey, Index, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, IdentityMixin, TimestampMixin


class AuditLog(IdentityMixin, TimestampMixin, Base):
    __tablename__ = 'audit_logs'
    __table_args__ = (Index('ix_audit_logs_company_created', 'company_id', 'created_at'),)
    actor_id: Mapped[int | None] = mapped_column(ForeignKey('users.id', ondelete='RESTRICT'), index=True)
    company_id: Mapped[int | None] = mapped_column(ForeignKey('companies.id', ondelete='RESTRICT'))
    action: Mapped[str] = mapped_column(String(80))
    entity: Mapped[str] = mapped_column(String(80))
    entity_id: Mapped[int | None]
    details: Mapped[dict | None] = mapped_column(JSONB)
    ip_address: Mapped[str | None] = mapped_column(String(45))
