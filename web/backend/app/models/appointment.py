from datetime import date, time

from sqlalchemy import Date, ForeignKey, Index, String, Text, Time
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, IdentityMixin, TimestampMixin
from app.models.room import Room


class Appointment(IdentityMixin, TimestampMixin, Base):
    __tablename__ = 'appointments'
    __table_args__ = (Index('ix_appointments_company_date', 'company_id', 'scheduled_date'),)
    company_id: Mapped[int | None] = mapped_column(ForeignKey('companies.id', ondelete='RESTRICT'), index=True)
    room_id: Mapped[int | None] = mapped_column(ForeignKey('rooms.id', ondelete='RESTRICT'), index=True)
    scheduled_date: Mapped[date] = mapped_column(Date)
    starts_at: Mapped[time] = mapped_column(Time)
    ends_at: Mapped[time] = mapped_column(Time)
    title: Mapped[str] = mapped_column(String(120))
    details: Mapped[str | None] = mapped_column(Text)
    room: Mapped[Room | None] = relationship()
