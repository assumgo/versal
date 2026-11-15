from datetime import date, datetime

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base


class Alocacao(Base):
    """Movimento de estoque de equipamento (entrega/devolução para colaborador ou local)."""

    __tablename__ = 'alocacoes'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    codigo: Mapped[str] = mapped_column(String(60), unique=True, nullable=False, index=True)
    tipo: Mapped[str] = mapped_column(String(20), nullable=False, index=True)  # entrega | devolucao
    destino_tipo: Mapped[str] = mapped_column(String(20), nullable=False, index=True)  # colaborador | local
    equipamento_id: Mapped[int] = mapped_column(
        ForeignKey('equipamentos.id', ondelete='CASCADE'),
        nullable=False,
        index=True,
    )
    quantidade: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    colaborador_id: Mapped[int | None] = mapped_column(ForeignKey('colaboradores.id'), nullable=True, index=True)
    local_id: Mapped[int | None] = mapped_column(ForeignKey('locais.id'), nullable=True, index=True)
    tre_id: Mapped[int | None] = mapped_column(ForeignKey('tres.id'), nullable=True, index=True)
    referencia_id: Mapped[int | None] = mapped_column(ForeignKey('alocacoes.id'), nullable=True, index=True)
    data_previsao: Mapped[date | None] = mapped_column(Date, nullable=True, index=True)
    ativa: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), index=True)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )

    equipamento = relationship('Equipamento', back_populates='alocacoes')
    colaborador = relationship('Colaborador')
    local = relationship('Local')
