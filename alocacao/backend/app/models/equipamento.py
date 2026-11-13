from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base


class Equipamento(Base):
    __tablename__ = 'equipamentos'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    descricao: Mapped[str] = mapped_column(String(200), nullable=False)
    marca: Mapped[str] = mapped_column(String(100), nullable=False)
    modelo: Mapped[str] = mapped_column(String(100), nullable=False)
    numero_serie: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    numero_patrimonio: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    mac_address: Mapped[str | None] = mapped_column(String(32), nullable=True)
    categoria_id: Mapped[int] = mapped_column(ForeignKey('categorias.id'), nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )

    categoria = relationship('Categoria')
    alocacoes = relationship(
        'Alocacao',
        back_populates='equipamento',
        cascade='all, delete-orphan',
        passive_deletes=True,
    )
