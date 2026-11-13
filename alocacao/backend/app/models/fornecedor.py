from datetime import datetime

from sqlalchemy import Boolean, DateTime, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base


class Fornecedor(Base):
    __tablename__ = 'fornecedores'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    razao_social: Mapped[str] = mapped_column(String(180), nullable=False, index=True)
    nome_fantasia: Mapped[str] = mapped_column(String(180), nullable=False)
    documento: Mapped[str] = mapped_column(String(14), unique=True, nullable=False, index=True)
    ativo: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )
