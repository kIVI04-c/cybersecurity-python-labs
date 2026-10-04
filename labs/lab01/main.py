"""Головний модуль запуску Лабораторної роботи №1."""

import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))

from labs.lab01.task1 import run_task1
from labs.lab01.task2 import run_task2
from labs.lab01.task3 import run_task3
from shared.student import GROUP_NAME, STUDENT_NAME, VARIANT_NUMBER


def main():
    """Точка входу для виконання завдань 1, 2 та 3."""
    print("=" * 60)
    print("Лабораторна робота №1")
    print(f"Виконав: {STUDENT_NAME} | Група: {GROUP_NAME} | Варіант: {VARIANT_NUMBER}")
    print("=" * 60)

    run_task1()
    print("\n" + "=" * 60)
    run_task2()
    print("\n" + "=" * 60)
    run_task3()
    print("\n" + "=" * 60)
    print("Всі завдання виконано успішно.")


if __name__ == "__main__":
    main()
