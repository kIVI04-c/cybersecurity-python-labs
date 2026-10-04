"""Завдання 3: Хешування, збереження в CSV та логування через декоратор."""

import csv
import hashlib
import json
import os
import sys
from datetime import datetime
from functools import wraps

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))
from shared.student import VARIANT_NUMBER

DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
USERS_CSV_PATH = os.path.join(DATA_DIR, "users.csv")
LOG_JSON_PATH = os.path.join(DATA_DIR, "log.json")

MIN_PASSWORD_LENGTH = 11
PERSONAL_SALT = str(VARIANT_NUMBER).zfill(5)  # "00008"


class ValidationError(Exception):
    """Помилка валідації довжини пароля."""


def generate_hash(password: str, salt: str = "00000") -> str:
    """Генерує хеш sha256 від конкатенації пароля та солі."""
    if not password or not salt:
        raise ValueError("Пароль та сіль не можуть бути порожніми.")
    if len(password) < MIN_PASSWORD_LENGTH:
        raise ValidationError(
            f"Пароль має містити щонайменше {MIN_PASSWORD_LENGTH} символів."
        )

    salted = f"{password}{salt}".encode()
    return hashlib.sha256(salted).hexdigest()


def create_user(username: str, password: str) -> tuple:
    """Створює запис користувача з персональною сіллю."""
    pwd_hash = generate_hash(password, salt=PERSONAL_SALT)
    return (username, pwd_hash)


def create_users(users_list: list) -> None:
    """Створює каталог data та записує список користувачів у CSV."""
    os.makedirs(DATA_DIR, exist_ok=True)
    with open(USERS_CSV_PATH, mode="w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["username", "password_hash"])
        for u, p in users_list:
            writer.writerow(create_user(u, p))


def read_users_db() -> list:
    """Зчитує CSV-базу користувачів."""
    users_db = []
    with open(USERS_CSV_PATH, mode="r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            users_db.append(row)
    return users_db


def log_event(func):
    """Декоратор для аудиту спроб авторизації у JSON-файл."""

    @wraps(func)
    def wrapper(*args, **kwargs):
        username = kwargs.get("username") if "username" in kwargs else args[0]
        try:
            result = func(*args, **kwargs)
            status = "success" if result else "failure"
        except Exception:
            status = "failure"
            raise
        finally:
            log_entry = {
                "event": "login",
                "user": username,
                "result": status,
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "args": list(args),
                "kwargs": kwargs,
            }
            logs = []
            if os.path.exists(LOG_JSON_PATH):
                try:
                    with open(LOG_JSON_PATH, "r", encoding="utf-8") as jf:
                        logs = json.load(jf)
                except (OSError, json.JSONDecodeError):
                    logs = []
            logs.append(log_entry)
            os.makedirs(DATA_DIR, exist_ok=True)
            with open(LOG_JSON_PATH, "w", encoding="utf-8") as jf:
                json.dump(logs, jf, indent=4, ensure_ascii=False)
        return result

    return wrapper


@log_event
def login(username: str, password: str) -> bool:
    """Автентифікує користувача за базою CSV."""
    if not username or not password:
        raise ValueError("Логін та пароль є обов'язковими для заповнення.")

    users_db = read_users_db()
    input_hash = generate_hash(password, salt=PERSONAL_SALT)

    for record in users_db:
        if record["username"] == username:
            return record["password_hash"] == input_hash
    return False


def run_task3() -> None:
    """Виконує повний цикл реєстрації, збереження, виводу та перевірки входу."""
    print("\n--- Завдання 3 | Хешування та безпечна автентифікація ---")

    users_to_register = [
        ("admin_user", "Compl3x!Pass1"),
        ("sec_analyst", "S0C_Analyst2026"),
        ("net_engineer", "Router#Secured99"),
        ("dev_ops", "Kubern3t3s_Clust3r"),
        ("qa_tester", "Aut0m@tion_T3st!"),
        ("crypto_lead", "Ellipt1c_Curv3_Key"),
        ("cloud_admin", "Aws_Azur3_Gcp2026"),
        ("audit_spec", "Compli@nc3_Ch3ck"),
        ("db_master", "Postgr3s_DBA#11"),
        ("intern_dev", "Jav@Script_Pyth0n"),
    ]

    try:
        create_users(users_to_register)
        print(f"[OK] База даних успішно створена: {USERS_CSV_PATH}")

        db = read_users_db()
        print("\nЗміст бази даних користувачів (users.csv):")
        print(f"{'Username':<15} | {'SHA-256 Hash'}")
        print("-" * 75)
        for r in db:
            print(f"{r['username']:<15} | {r['password_hash']}")

        print("\nТестування входу в систему:")
        # Успішний вхід
        auth1 = login("admin_user", "Compl3x!Pass1")
        print(f"Спроба 1 (admin_user, правильний пароль): {auth1}")

        # Невдалий вхід
        auth2 = login("admin_user", "WrongP@ssword1")
        print(f"Спроба 2 (admin_user, неправильний пароль): {auth2}")

        print(f"[OK] Журнал подій успішно оновлено: {LOG_JSON_PATH}")

    except (
        OSError,
        FileNotFoundError,
        PermissionError,
        ValidationError,
        ValueError,
    ) as e:
        print(f"[Помилка виконання]: {e}")


if __name__ == "__main__":
    run_task3()
