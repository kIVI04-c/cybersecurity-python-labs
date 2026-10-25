"""Головний модуль керування Лабораторною роботою №2."""

import argparse
from datetime import timedelta
from pathlib import Path

from labs.lab02.task1 import Admin, AuditLog, User, UserAccount
from labs.lab02.task2 import analyze_dns_log


def run_demo() -> None:
    """Демонстраційний сценарій для Завдання 1 (ООП)."""
    print("=" * 65)
    print("ДЕМОНСТРАЦІЯ ЗАВДАННЯ 1: ОБ'ЄКТНО-ОРІЄНТОВАНА СИСТЕМА ОБЛІКУ")
    print("=" * 65)

    # 1. Створення користувача та валідація email
    print("\n[1] Створення користувача та валідація email:")
    user = User(username="analyst_illia", email="illia.ivaniv@sec-corp.ua")
    user.set_password("SuperSecret2026!")
    print(f"Створено: {user}")

    try:
        user.email = "bad_email_format"
    except ValueError as e:
        print(f"[OK] Спіймано очікувану помилку валідації email: {e}")

    # 2. Робота з класом Admin
    print("\n[2] Перевірка прав адміністратора (Admin):")
    admin = Admin(username="admin_root", email="root.admin@sec-corp.ua")
    admin.set_password("RootAccess#99")
    admin.grant_permission("READ_CONFIDENTIAL_DB")
    admin.grant_permission("MANAGE_USERS")
    print(f"Адміністратор: {admin}")
    print(f"Має право MANAGE_USERS? {admin.has_permission('MANAGE_USERS')}")
    admin.revoke_permission("MANAGE_USERS")
    print(
        f"Після видалення: має право MANAGE_USERS? {admin.has_permission('MANAGE_USERS')}"
    )

    # 3. Автентифікація через UserAccount та AuditLog
    print("\n[3] Тестування UserAccount, автентифікації та журналу AuditLog:")
    audit = AuditLog()
    account = UserAccount(user=user, audit_log=audit)

    fail_res = account.login("analyst_illia", "WrongPassword", ip="192.168.1.55")
    print(f"Спроба входу з хибним паролем: {fail_res}")

    success_res = account.login("analyst_illia", "SuperSecret2026!", ip="192.168.1.55")
    print(f"Спроба входу з правильним паролем: {success_res}")
    print(f"Користувач авторизований? {account.is_authenticated()}")

    # 4. Доступ через індексатор __getitem__
    print("\n[4] Доступ через account['user'] (__getitem__):")
    print(f"Username через ключ: {account['user'].username}")

    # 5. Таймаут сесії та logout
    print("\n[5] Симуляція таймауту сесії та logout:")
    if account.session:
        account.session.last_activity -= timedelta(seconds=1000)
    print(f"Сесія активна після таймауту (1000 сек)? {account.is_authenticated()}")

    account.logout()
    print("Виконано logout.")

    # 6. Записи AuditLog
    print("\n[6] Усі події безпеки в AuditLog:")
    for rec in audit.show_all():
        ts = rec.timestamp.strftime("%Y-%m-%d %H:%M:%S")
        print(f" - [{ts}] Користувач: {rec.username:<15} Дія: {rec.action}")

    print("\nДемонстрацію успішно завершено.")


def main() -> None:
    """Точка входу для команд demo та analyze."""
    parser = argparse.ArgumentParser(description="Керування Лабораторною роботою №2")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # Підкоманда demo
    subparsers.add_parser("demo", help="Запустити демонстрацію класів ООП (Завдання 1)")

    # Підкоманда analyze
    analyze_parser = subparsers.add_parser(
        "analyze", help="Запустити CLI-утиліту DNS-аналізу (Завдання 2)"
    )
    analyze_parser.add_argument(
        "--dns-log",
        type=Path,
        required=True,
        help="Шлях до файлу DNS-логу",
    )
    analyze_parser.add_argument(
        "--blacklist",
        type=Path,
        default=Path("labs/lab02/data/blacklist.txt"),
        help="Шлях до чорного списку",
    )
    analyze_parser.add_argument(
        "--out-csv",
        type=Path,
        default=Path("labs/lab02/data/dns_alerts.csv"),
        help="Шлях для збереження результатів",
    )
    analyze_parser.add_argument(
        "--min-domain-len",
        type=int,
        default=30,
        help="Мінімальна довжина підозрілого домену",
    )

    args = parser.parse_args()

    if args.command == "demo":
        run_demo()
    elif args.command == "analyze":
        analyze_dns_log(
            log_file=args.dns_log,
            blacklist_file=args.blacklist,
            output_csv=args.out_csv,
            min_domain_len=args.min_domain_len,
        )


if __name__ == "__main__":
    main()
