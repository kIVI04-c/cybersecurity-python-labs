"""Головний FastAPI-застосунок Лабораторної роботи №3 (Варіант 8)."""

import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from labs.lab03.config import DOMAIN_NAME, THRESHOLD, UNIT
from labs.lab03.database import initialize_database
from labs.lab03.routers import categories, records
from shared.student import GROUP_NAME, STUDENT_NAME, VARIANT_NUMBER

logging.basicConfig(
    level=logging.INFO,
    format="[%(levelname)s] %(name)s: %(message)s",
)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Ініціалізує структуру таблиць SQLite під час запуску сервера."""
    initialize_database()
    yield


app = FastAPI(
    title=f"Lab 03 API — {DOMAIN_NAME}",
    description=(
        f"Web API для обліку навчальних вимірювань відновлення сервісів "
        f"(Варіант {VARIANT_NUMBER}). Одиниця вимірювання: `{UNIT}`, "
        f"поріг реагування: `{THRESHOLD}` {UNIT}."
    ),
    version="1.0.0",
    lifespan=lifespan,
)


@app.get("/ping", tags=["System"], summary="Перевірка доступності API")
def ping() -> dict[str, str]:
    """Повертає статус доступності сервісу."""
    return {"status": "ok"}


@app.get("/student", tags=["System"], summary="Дані студента")
def get_student() -> dict[str, str | int]:
    """Повертає ПІБ, групу та варіант із shared/student.py."""
    return {
        "student_name": STUDENT_NAME,
        "group_name": GROUP_NAME,
        "variant_number": VARIANT_NUMBER,
    }


app.include_router(categories.router)
app.include_router(records.router)
