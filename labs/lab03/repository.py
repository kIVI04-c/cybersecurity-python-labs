"""Шар доступу до даних: параметризовані SQL-запити та транзакції."""

import sqlite3
from contextlib import closing
from typing import Any

from labs.lab03.database import get_connection


class NotFoundError(Exception):
    """Помилка: сутність у базі даних не знайдено."""


class ConflictError(Exception):
    """Помилка: конфлікт унікальності або обмежень цілісності."""


def list_categories() -> list[dict[str, Any]]:
    """Отримати список усіх категорій за зростанням id."""
    with closing(get_connection()) as connection:
        rows = connection.execute(
            "SELECT id, name FROM categories ORDER BY id ASC"
        ).fetchall()
        return [dict(row) for row in rows]


def create_category(name: str) -> dict[str, Any]:
    """Створити нову категорію."""
    with closing(get_connection()) as connection:
        try:
            with connection:
                cursor = connection.execute(
                    "INSERT INTO categories (name) VALUES (?)",
                    (name,),
                )
                category_id = cursor.lastrowid
                row = connection.execute(
                    "SELECT id, name FROM categories WHERE id = ?",
                    (category_id,),
                ).fetchone()
                return dict(row)
        except sqlite3.IntegrityError as err:
            raise ConflictError(f"Категорія з назвою '{name}' вже існує.") from err


def delete_category(category_id: int) -> None:
    """Видалити порожню категорію."""
    with closing(get_connection()) as connection:
        existing = connection.execute(
            "SELECT id FROM categories WHERE id = ?",
            (category_id,),
        ).fetchone()
        if existing is None:
            raise NotFoundError(f"Категорію з id={category_id} не знайдено.")

        try:
            with connection:
                connection.execute(
                    "DELETE FROM categories WHERE id = ?",
                    (category_id,),
                )
        except sqlite3.IntegrityError as err:
            raise ConflictError(
                "Неможливо видалити категорію, оскільки вона містить записи."
            ) from err


def _fetch_record_with_join(
    connection: sqlite3.Connection, record_id: int
) -> dict[str, Any] | None:
    """Внутрішня функція вибірки запису разом із назвою категорії."""
    row = connection.execute(
        """
        SELECT
            r.id,
            r.code,
            r.title,
            r.category_id,
            c.name AS category_name,
            r.value,
            r.status
        FROM records r
        JOIN categories c ON r.category_id = c.id
        WHERE r.id = ?
        """,
        (record_id,),
    ).fetchone()
    return dict(row) if row is not None else None


def get_record_by_id(record_id: int) -> dict[str, Any]:
    """Отримати один запис за його id."""
    with closing(get_connection()) as connection:
        record = _fetch_record_with_join(connection, record_id)
        if record is None:
            raise NotFoundError(f"Запис з id={record_id} не знайдено.")
        return record


def list_records(
    category_id: int | None = None,
    status: str | None = None,
    min_value: float | None = None,
    q: str | None = None,
    limit: int = 20,
    offset: int = 0,
) -> list[dict[str, Any]]:
    """Отримати список записів із фільтрами та пагінацією."""
    conditions: list[str] = []
    params: list[Any] = []

    if category_id is not None:
        conditions.append("r.category_id = ?")
        params.append(category_id)
    if status is not None:
        conditions.append("r.status = ?")
        params.append(status)
    if min_value is not None:
        conditions.append("r.value >= ?")
        params.append(min_value)
    if q is not None:
        conditions.append("instr(r.title, ?) > 0")
        params.append(q)

    where_clause = f"WHERE {' AND '.join(conditions)}" if conditions else ""
    query = f"""
        SELECT
            r.id,
            r.code,
            r.title,
            r.category_id,
            c.name AS category_name,
            r.value,
            r.status
        FROM records r
        JOIN categories c ON r.category_id = c.id
        {where_clause}
        ORDER BY r.id ASC
        LIMIT ? OFFSET ?
    """
    params.extend([limit, offset])

    with closing(get_connection()) as connection:
        rows = connection.execute(query, params).fetchall()
        return [dict(row) for row in rows]


def create_record(data: dict[str, Any]) -> dict[str, Any]:
    """Створити новий запис вимірювання."""
    with closing(get_connection()) as connection:
        category = connection.execute(
            "SELECT id FROM categories WHERE id = ?",
            (data["category_id"],),
        ).fetchone()
        if category is None:
            raise NotFoundError(f"Категорію з id={data['category_id']} не знайдено.")

        try:
            with connection:
                cursor = connection.execute(
                    """
                    INSERT INTO records
                        (code, title, category_id, value, status)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (
                        data["code"],
                        data["title"],
                        data["category_id"],
                        data["value"],
                        data["status"],
                    ),
                )
                record_id = int(cursor.lastrowid)
                created = _fetch_record_with_join(connection, record_id)
                assert created is not None
                return created
        except sqlite3.IntegrityError as err:
            raise ConflictError(f"Запис із кодом '{data['code']}' вже існує.") from err


def update_record(record_id: int, data: dict[str, Any]) -> dict[str, Any]:
    """Повністю оновити змінювані поля запису."""
    with closing(get_connection()) as connection:
        existing = connection.execute(
            "SELECT id FROM records WHERE id = ?",
            (record_id,),
        ).fetchone()
        if existing is None:
            raise NotFoundError(f"Запис з id={record_id} не знайдено.")

        category = connection.execute(
            "SELECT id FROM categories WHERE id = ?",
            (data["category_id"],),
        ).fetchone()
        if category is None:
            raise NotFoundError(f"Категорію з id={data['category_id']} не знайдено.")

        try:
            with connection:
                connection.execute(
                    """
                    UPDATE records
                    SET code = ?, title = ?, category_id = ?,
                        value = ?, status = ?
                    WHERE id = ?
                    """,
                    (
                        data["code"],
                        data["title"],
                        data["category_id"],
                        data["value"],
                        data["status"],
                        record_id,
                    ),
                )
                updated = _fetch_record_with_join(connection, record_id)
                assert updated is not None
                return updated
        except sqlite3.IntegrityError as err:
            raise ConflictError(f"Запис із кодом '{data['code']}' вже існує.") from err


def delete_record(record_id: int) -> None:
    """Видалити запис за id."""
    with closing(get_connection()) as connection, connection:
        cursor = connection.execute(
            "DELETE FROM records WHERE id = ?",
            (record_id,),
        )
        if cursor.rowcount == 0:
            raise NotFoundError(f"Запис з id={record_id} не знайдено.")


def create_records_bulk(
    records_data: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Атомарно додати пакет записів у межах однієї транзакції."""
    with closing(get_connection()) as connection:
        try:
            with connection:
                created_ids: list[int] = []
                for item in records_data:
                    category = connection.execute(
                        "SELECT id FROM categories WHERE id = ?",
                        (item["category_id"],),
                    ).fetchone()
                    if category is None:
                        raise NotFoundError(
                            f"Категорію з id={item['category_id']} не знайдено."
                        )

                    cursor = connection.execute(
                        """
                        INSERT INTO records
                            (code, title, category_id, value, status)
                        VALUES (?, ?, ?, ?, ?)
                        """,
                        (
                            item["code"],
                            item["title"],
                            item["category_id"],
                            item["value"],
                            item["status"],
                        ),
                    )
                    created_ids.append(int(cursor.lastrowid))

                result: list[dict[str, Any]] = []
                for rec_id in created_ids:
                    rec = _fetch_record_with_join(connection, rec_id)
                    assert rec is not None
                    result.append(rec)
                return result
        except sqlite3.IntegrityError as err:
            raise ConflictError(
                "Конфлікт унікальності: дублікат code у базі або всередині пакета."
            ) from err
