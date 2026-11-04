from datetime import datetime

from pydantic import AwareDatetime, BaseModel, ConfigDict, Field, model_validator


class ReservationCreate(BaseModel):
    model_config = ConfigDict(extra='forbid')

    room_id: int = Field(ge=1)
    title: str = Field(min_length=1, max_length=120)
    starts_at: AwareDatetime
    ends_at: AwareDatetime

    @model_validator(mode='after')
    def ends_after_start(self) -> 'ReservationCreate':
        title = self.title.strip()
        if not title:
            raise ValueError('Informe o título')
        self.title = title
        if self.ends_at <= self.starts_at:
            raise ValueError('O fim precisa ser posterior ao início')
        return self


class ReservationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    room_id: int
    room_name: str
    user_id: int
    user_name: str
    title: str
    starts_at: datetime
    ends_at: datetime
    mine: bool
