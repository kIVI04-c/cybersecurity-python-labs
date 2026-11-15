"""Маршрути API для керування категоріями сервісів."""

import logging
import sqlite3

from fastapi import APIRouter, HTTPException, Path, status

from labs.lab03 import repository
from labs.lab03.schemas import CategoryCreate, CategoryRead

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/categories", tags=["Categories"])


@router.get(
    "",
    response_model=list[CategoryRead],
    summary="Отримати список категорій",
)
def get_categories() -> list[dict]:
    """Повертає всі категорії, відсортовані за зростанням id."""
    try:
        return repository.list_categories()
    except sqlite3.Error as err:
        logger.exception("Помилка БД при читанні категорій")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Внутрішня помилка бази даних.",
        ) from err


@router.post(
    "",
    response_model=CategoryRead,
    status_code=status.HTTP_201_CREATED,
    responses={409: {"description": "Категорія з такою назвою вже існує"}},
    summary="Створити категорію",
)
def create_category(payload: CategoryCreate) -> dict:
    """Створює нову категорію сервісів."""
    try:
        return repository.create_category(payload.name)
    except repository.ConflictError as err:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(err),
        ) from err
    except sqlite3.Error as err:
        logger.exception("Помилка БД при створенні категорії")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Внутрішня помилка бази даних.",
        ) from err


@router.delete(
    "/{category_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={
        404: {"description": "Категорію не знайдено"},
        409: {"description": "Категорія містить пов'язані записи"},
    },
    summary="Видалити порожню категорію",
)
def delete_category(
    category_id: int = Path(..., gt=0, description="ID категорії (> 0)"),
) -> None:
    """Видаляє категорію, якщо в ній немає жодного запису."""
    try:
        repository.delete_category(category_id)
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
        logger.exception("Помилка БД при видаленні категорії")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Внутрішня помилка бази даних.",
        ) from err
