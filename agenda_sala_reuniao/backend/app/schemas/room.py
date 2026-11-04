from pydantic import BaseModel, ConfigDict, Field, field_validator


class RoomCreate(BaseModel):
    model_config = ConfigDict(extra='forbid')

    name: str = Field(min_length=1, max_length=120)
    location: str = Field(default='', max_length=120)
    capacity: int = Field(ge=1, le=500)
    is_active: bool = True

    @field_validator('name', 'location')
    @classmethod
    def strip_text(cls, value: str) -> str:
        return value.strip()

    @field_validator('name')
    @classmethod
    def require_name(cls, value: str) -> str:
        if not value:
            raise ValueError('Informe o nome da sala')
        return value


class RoomUpdate(RoomCreate):
    pass


class RoomResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    location: str
    capacity: int
    is_active: bool
