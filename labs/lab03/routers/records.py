"""Маршрути API для роботи із записами вимірювань відновлення."""

import logging
import sqlite3
from typing import Annotated, Literal

from fastapi import APIRouter, Body, HTTPException, Path, Query, status

from labs.lab03 import repository
from labs.lab03.config import MAX_VALUE, MIN_VALUE
from labs.lab03.schemas import RecordCreate, RecordRead, RecordReplace

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/records", tags=["Records"])


@router.get(
    "",
    response_model=list[RecordRead],
    summary="Отримати список записів із фільтрами",
)
def get_records(
    category_id: int | None = Query(
        default=None, gt=0, description="Фільтр за ID категорії"
    ),
    status_filter: Literal["new", "in_progress", "done"] | None = Query(
        default=None, alias="status", description="Фільтр за статусом"
    ),
    min_value: float | None = Query(
        default=None,
        ge=MIN_VALUE,
        le=MAX_VALUE,
        allow_inf_nan=False,
        description="Мінімальна тривалість відновлення (хв)",
    ),
    q: str | None = Query(
        default=None,
        min_length=1,
        max_length=120,
        description="Буквальний пошук підрядка в title",
    ),
    limit: int = Query(
        default=20, ge=1, le=100, description="Кількість записів на сторінку"
    ),
    offset: int = Query(default=0, ge=0, description="Кількість пропущених записів"),
) -> list[dict]:
    """Повертає відфільтрований список записів з пагінацією."""
    try:
        return repository.list_records(
            category_id=category_id,
            status=status_filter,
            min_value=min_value,
            q=q,
            limit=limit,
            offset=offset,
        )
    except sqlite3.Error as err:
        logger.exception("Помилка БД при читанні списку записів")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Внутрішня помилка бази даних.",
        ) from err


@router.get(
    "/{record_id}",
    response_model=RecordRead,
    responses={404: {"description": "Запис не знайдено"}},
    summary="Отримати один запис за ID",
)
def get_record(
    record_id: int = Path(..., gt=0, description="ID запису (> 0)"),
) -> dict:
    """Повертає детальну інформацію про конкретний запис."""
    try:
        return repository.get_record_by_id(record_id)
    except repository.NotFoundError as err:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(err),
        ) from err
    except sqlite3.Error as err:
        logger.exception("Помилка БД при читанні запису")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Внутрішня помилка бази даних.",
        ) from err


@router.post(
    "",
    response_model=RecordRead,
    status_code=status.HTTP_201_CREATED,
    responses={
        404: {"description": "Вказану категорію не знайдено"},
        409: {"description": "Запис із таким code вже існує"},
    },
    summary="Створити новий запис",
)
def create_record(payload: RecordCreate) -> dict:
    """Створює новий запис вимірювання відновлення."""
    try:
        return repository.create_record(payload.model_dump())
    except repository.NotFoundError as err:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(err),
        ) from err
    except repository.ConflictError as err:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(err),
        ) from err
    except sqlite3.Error as err:
        logger.exception("Помилка БД при створенні запису")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Внутрішня помилка бази даних.",
        ) from err


@router.post(
    "/bulk",
    response_model=list[RecordRead],
    status_code=status.HTTP_201_CREATED,
    responses={
        404: {"description": "Категорію одного з елементів не знайдено"},
        409: {"description": "Дублікат code у базі або всередині пакета"},
    },
    summary="Пакетне додавання записів (транзакція)",
)
def create_records_bulk(
    records: Annotated[
        list[RecordCreate],
        Body(
            min_length=1,
            max_length=100,
            description="Список від 1 до 100 записів",
        ),
    ],
) -> list[dict]:
    """Атомарно створює пакет записів або скасовує всі при помилці."""
    try:
        return repository.create_records_bulk([item.model_dump() for item in records])
    except repository.NotFoundError as err:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(err),
        ) from err
    except repository.ConflictError as err:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(err),
        ) from err
    except sqlite3.Error as err:
        logger.exception("Помилка БД при пакетному додаванні")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Внутрішня помилка бази даних.",
        ) from err


@router.put(
    "/{record_id}",
    response_model=RecordRead,
    responses={
        404: {"description": "Запис або категорію не знайдено"},
        409: {"description": "Запис із таким code вже існує"},
    },
    summary="Повністю замінити змінювані поля запису",
)
def replace_record(
    payload: RecordReplace,
    record_id: int = Path(..., gt=0, description="ID запису (> 0)"),
) -> dict:
    """Оновлює всі змінювані поля існуючого запису."""
    try:
        return repository.update_record(record_id, payload.model_dump())
    except repository.NotFoundError as err:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(err),
        ) from err
    except repository.ConflictError as err:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(err),
        ) from err
    except sqlite3.Error as err:
        logger.exception("Помилка БД при оновленні запису")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Внутрішня помилка бази даних.",
        ) from err


@router.delete(
    "/{record_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={404: {"description": "Запис не знайдено"}},
    summary="Видалити запис",
)
def delete_record(
    record_id: int = Path(..., gt=0, description="ID запису (> 0)"),
) -> None:
    """Видаляє запис вимірювання за ID."""
    try:
        repository.delete_record(record_id)
    except repository.NotFoundError as err:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(err),
        ) from err
    except sqlite3.Error as err:
        logger.exception("Помилка БД при видаленні запису")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Внутрішня помилка бази даних.",
        ) from err
