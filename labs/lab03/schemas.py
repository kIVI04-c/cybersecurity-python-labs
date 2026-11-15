"""Pydantic-моделі для валідації запитів і формування відповідей API."""

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from labs.lab03.config import MAX_VALUE, MIN_VALUE


class CategoryCreate(BaseModel):
    """Модель створення категорії."""

    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    name: str = Field(
        min_length=2,
        max_length=40,
        description="Унікальна назва сервісу/категорії",
    )


class CategoryRead(BaseModel):
    """Модель відповіді для категорії."""

    id: int
    name: str


class RecordCreate(BaseModel):
    """Модель створення запису вимірювання."""

    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    code: str = Field(
        min_length=3,
        max_length=40,
        description="Унікальний код запису (наприклад, V08-01)",
    )
    title: str = Field(
        min_length=3,
        max_length=120,
        description="Назва вимірювання відновлення",
    )
    category_id: int = Field(gt=0, description="ID існуючої категорії")
    value: float = Field(
        ge=MIN_VALUE,
        le=MAX_VALUE,
        allow_inf_nan=False,
        description="Тривалість відновлення у хвилинах (>= 0)",
    )
    status: Literal["new", "in_progress", "done"] = Field(
        description="Стан перевірки вимірювання"
    )


class RecordReplace(RecordCreate):
    """Модель повної заміни запису (PUT)."""


class RecordRead(RecordCreate):
    """Модель відповіді для запису з назвою категорії."""

    id: int
    category_name: str
