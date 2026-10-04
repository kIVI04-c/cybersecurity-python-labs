"""Завдання 1: Комплексний аналізатор надійності паролів (Варіант 8)."""

import os
import random
import string
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))
from shared.student import GROUP_NAME, STUDENT_NAME, VARIANT_NUMBER


def evaluate_password_strength(
    password: str,
    criteria: dict,
    forbidden: set,
    all_passwords: list,
) -> str:
    """Оцінює рівень надійності пароля за заданими критеріями."""
    min_len = criteria["min_length"]

    if password in forbidden or len(password) < min_len:
        return "Заборонений"

    has_digit = any(c.isdigit() for c in password)
    has_upper = any(c.isupper() for c in password)
    has_lower = any(c.islower() for c in password)
    has_special = any(c in string.punctuation for c in password)

    satisfies_all = (
        len(password) >= min_len
        and (not criteria.get("require_digits") or has_digit)
        and (not criteria.get("require_upper") or has_upper)
        and (not criteria.get("require_special") or has_special)
    )

    if satisfies_all:
        is_unique = all_passwords.count(password) == 1
        if len(password) >= min_len + 4 and is_unique:
            return "Дуже сильний"
        return "Сильний"

    satisfies_any = has_digit or has_upper or has_lower or has_special
    if satisfies_any and len(password) >= min_len:
        return "Середній"

    return "Слабкий"


def run_task1() -> None:
    """Виконує аналіз паролів для Варіанта 8."""
    print(f"\n--- Завдання 1 | Студент: {STUDENT_NAME} ({GROUP_NAME}) ---")
    print(f"Варіант: {VARIANT_NUMBER}\n")

    passwords = [
        "ThreatH@nt3r",
        "weak123",
        "P3n3trat10n@Test",
        "visitor",
        "Cyber@Defense2023",
        "normal",
        "Incident@R3sponse",
        "standard",
        "Risk@Analysis",
        "typical",
    ]
    criteria = {
        "min_length": 10,
        "require_digits": True,
        "require_upper": True,
        "require_special": True,
    }
    forbidden_passwords = {
        "weak123",
        "visitor",
        "normal",
        "standard",
        "typical",
        "admin",
    }

    # Генерація 3 випадкових індексів і додавання дублікатів
    random_indices = [random.randint(0, len(passwords) - 1) for _ in range(3)]
    for idx in random_indices:
        passwords.append(passwords[idx])

    print(f"{'Пароль':<25} | {'Довжина':<8} | {'Оцінка стійкості'}")
    print("-" * 55)

    for pwd in passwords:
        strength = evaluate_password_strength(
            pwd, criteria, forbidden_passwords, passwords
        )
        print(f"{pwd:<25} | {len(pwd):<8} | {strength}")


if __name__ == "__main__":
    run_task1()
