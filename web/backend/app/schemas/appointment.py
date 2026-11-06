from datetime import date, time

from pydantic import BaseModel, ConfigDict, Field, field_serializer, field_validator


class AppointmentCreate(BaseModel):
    model_config = ConfigDict(extra='forbid')

    scheduled_date: date
    starts_at: time
    title: str = Field(min_length=1, max_length=120)
    details: str | None = Field(default=None, max_length=500)

    @field_validator('title', mode='before')
    @classmethod
    def strip_title(cls, value: object) -> object:
        if not isinstance(value, str):
            return value
        stripped = value.strip()
        if not stripped:
            raise ValueError('Informe o título do agendamento')
        return stripped

    @field_validator('details', mode='before')
    @classmethod
    def strip_details(cls, value: object) -> object:
        if not isinstance(value, str):
            return value
        return value.strip() or None


class AppointmentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    company_id: int
    scheduled_date: date
    starts_at: time
    title: str
    details: str | None

    @field_serializer('starts_at')
    def serialize_time(self, value: time) -> str:
        return value.strftime('%H:%M')
