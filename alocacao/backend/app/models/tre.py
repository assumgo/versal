from datetime import datetime
from typing import Literal

from sqlalchemy import DateTime, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base

TreTipo = Literal['entrega', 'devolucao']


class Tre(Base):
    __tablename__ = 'tres'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    codigo: Mapped[str] = mapped_column(String(60), unique=True, nullable=False, index=True)
    tipo: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    colaborador_id: Mapped[int] = mapped_column(ForeignKey('colaboradores.id'), nullable=False, index=True)
    pdf_path: Mapped[str] = mapped_column(String(500), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), index=True)

    colaborador = relationship('Colaborador')
    itens = relationship('TreItem', back_populates='tre', cascade='all, delete-orphan')


class TreItem(Base):
    __tablename__ = 'tre_itens'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    tre_id: Mapped[int] = mapped_column(ForeignKey('tres.id', ondelete='CASCADE'), nullable=False, index=True)
    equipamento_id: Mapped[int | None] = mapped_column(ForeignKey('equipamentos.id'), nullable=True, index=True)
    alocacao_id: Mapped[int | None] = mapped_column(ForeignKey('alocacoes.id'), nullable=True, index=True)
    quantidade: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    categoria_nome: Mapped[str] = mapped_column(String(120), nullable=False, default='')
    descricao: Mapped[str] = mapped_column(String(300), nullable=False)
    marca: Mapped[str] = mapped_column(String(100), nullable=False, default='')
    modelo: Mapped[str] = mapped_column(String(100), nullable=False, default='')
    numero_patrimonio: Mapped[str] = mapped_column(String(100), nullable=False)

    tre = relationship('Tre', back_populates='itens')
