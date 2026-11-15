"""Скрипт початкового заповнення бази даних із файлу seed.json."""

import json
import logging
import sqlite3
from contextlib import closing
from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field, ValidationError

from labs.lab03.database import get_connection, initialize_database
from labs.lab03.schemas import RecordCreate

logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(message)s")
logger = logging.getLogger("seed")

SEED_PATH = Path(__file__).resolve().parent / "data" / "seed.json"


class SeedCategory(BaseModel):
    """Модель перевірки категорії у початковому файлі."""

    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    id: int = Field(gt=0)
    name: str = Field(min_length=2, max_length=40)


class SeedPayload(BaseModel):
    """Модель перевірки структури seed.json."""

    model_config = ConfigDict(extra="forbid")

    categories: list[SeedCategory] = Field(min_length=1)
    records: list[RecordCreate] = Field(min_length=1)


def seed_database() -> None:
    """Заповнити порожню базу навчальними даними в одній транзакції."""
    initialize_database()

    if not SEED_PATH.exists():
        logger.error("Файл початкових даних не знайдено: %s", SEED_PATH)
        return

    try:
        raw_data = json.loads(SEED_PATH.read_text(encoding="utf-8"))
        payload = SeedPayload.model_validate(raw_data)
    except (json.JSONDecodeError, ValidationError) as err:
        logger.error("Помилка валідації seed.json: %s", err)
        return

    with closing(get_connection()) as connection:
        cat_count = connection.execute("SELECT COUNT(*) FROM categories").fetchone()[0]
        rec_count = connection.execute("SELECT COUNT(*) FROM records").fetchone()[0]

        if cat_count > 0 or rec_count > 0:
            logger.info(
                "База даних уже містить записи (%d категорій, %d записів). "
                "Повторне заповнення скасовано без змін.",
                cat_count,
                rec_count,
            )
            return

        try:
            with connection:
                connection.executemany(
                    "INSERT INTO categories (id, name) VALUES (?, ?)",
                    [(cat.id, cat.name) for cat in payload.categories],
                )
                connection.executemany(
                    """
                    INSERT INTO records
                        (code, title, category_id, value, status)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    [
                        (
                            rec.code,
                            rec.title,
                            rec.category_id,
                            rec.value,
                            rec.status,
                        )
                        for rec in payload.records
                    ],
                )
            logger.info(
                "Успішно додано %d категорій та %d записів.",
                len(payload.categories),
                len(payload.records),
            )
        except sqlite3.Error as err:
            logger.error("Помилка під час заповнення бази, зміни скасовано: %s", err)


if __name__ == "__main__":
    seed_database()
