from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base


class Alocacao(Base):
    """Vínculo de equipamento a colaborador. Ativa=True => status Alocado."""

    __tablename__ = 'alocacoes'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    equipamento_id: Mapped[int] = mapped_column(
        ForeignKey('equipamentos.id', ondelete='CASCADE'),
        nullable=False,
        index=True,
    )
    colaborador_id: Mapped[int | None] = mapped_column(ForeignKey('colaboradores.id'), nullable=True, index=True)
    ativa: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )

    equipamento = relationship('Equipamento', back_populates='alocacoes')
