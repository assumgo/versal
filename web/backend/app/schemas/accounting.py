"""Shared input and pagination contracts for company accounting catalogs."""
import re
from typing import Annotated, Generic, TypeVar

from pydantic import AfterValidator, BaseModel, ConfigDict, Field, model_validator


def normalize_account(value: str) -> str:
    value = value.strip()
    if value.endswith('.0'):
        value = value[:-2]
    return re.sub(r'\D', '', value)


def normalize_history(value: str) -> str:
    digits = re.sub(r'\D', '', value)
    return digits[-9:].zfill(9) if digits else '001000182'


def nonempty(value: str) -> str:
    value = value.strip()
    if not value:
        raise ValueError('Informe um valor não vazio')
    return value


NonEmpty = Annotated[str, AfterValidator(nonempty)]
AccountCode = Annotated[str, AfterValidator(normalize_account), AfterValidator(nonempty)]
Flag = Annotated[int, Field(strict=True, ge=0, le=1)]


class InputModel(BaseModel):
    model_config = ConfigDict(extra='forbid')


class PatchModel(InputModel):
    @model_validator(mode='after')
    def supplied_fields(self):
        if not self.model_fields_set or any(getattr(self, key) is None for key in self.model_fields_set):
            raise ValueError('Informe alterações não nulas')
        return self


T = TypeVar('T')


class Page(BaseModel, Generic[T]):
    items: list[T]
    total: int
    offset: int
    limit: int
