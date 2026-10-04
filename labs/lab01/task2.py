"""Завдання 2: Багаторівнева система контролю доступу (Варіант 8)."""

import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))
from shared.student import GROUP_NAME, STUDENT_NAME, VARIANT_NUMBER


def check_access(user_id: str, resource_level: int, users: dict, blocked: set):
    """Визначає право доступу користувача до ресурсу."""
    if user_id not in users:
        return "DENY (User not found)"
    if user_id in blocked:
        return "DENY (User is blocked)"

    user = users[user_id]
    if not user.get("active", False):
        return "DENY (Account inactive)"

    if user["clearance"] >= resource_level:
        return "ALLOW"
    return "DENY (Insufficient clearance)"


def run_task2() -> None:
    """Виконує симуляцію перевірки доступу для Варіанта 8."""
    print(f"\n--- Завдання 2 | Студент: {STUDENT_NAME} ({GROUP_NAME}) ---")
    print(f"Варіант: {VARIANT_NUMBER}\n")

    users = {
        "crypto_specialist": {
            "role": "cryptographer",
            "clearance": 4,
            "department": "Cryptography",
            "active": True,
        },
        "privacy_officer": {
            "role": "privacy_analyst",
            "clearance": 3,
            "department": "Privacy",
            "active": True,
        },
        "data_scientist": {
            "role": "data_analyst",
            "clearance": 2,
            "department": "Analytics",
            "active": True,
        },
        "field_engineer": {
            "role": "field_support",
            "clearance": 2,
            "department": "Field Ops",
            "active": True,
        },
        "test_account": {
            "role": "testing",
            "clearance": 1,
            "department": "QA",
            "active": False,
        },
    }

    resources = [
        ("encryption_keys", 4),
        ("privacy_policies", 3),
        ("anonymized_data", 2),
        ("field_reports", 2),
        ("crypto_algorithms", 4),
        ("consent_forms", 1),
        ("data_classification", 3),
        ("key_management", 4),
        ("statistical_models", 2),
        ("public_datasets", 1),
    ]

    security_levels = (
        "Unclassified",
        "For Official Use",
        "Confidential",
        "Secret",
    )
    blocked_users = {"test_account", "gdpr_violation", "data_breach_user"}

    print("Список зареєстрованих ресурсів у системі:")
    for res_name, lvl in resources:
        level_label = security_levels[lvl - 1]
        print(f" - {res_name:<22}: {level_label} (Рівень {lvl})")

    print("\nРезультати перевірки доступу:")
    test_users = list(users.keys()) + ["intruder_unknown"]
    for uid in test_users:
        for res_name, res_lvl in resources[:2]:  # Перевірка на перших двох ресурсах
            status = check_access(uid, res_lvl, users, blocked_users)
            print(f"User: {uid:<18} | Resource: {res_name:<16} | Status: {status}")


if __name__ == "__main__":
    run_task2()
