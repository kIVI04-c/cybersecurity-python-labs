"""Завдання 1: Об'єктно-орієнтована модель користувача та облікового запису."""

import hashlib
import hmac
import os
import re
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

# Константи безпеки
HASH_ITERATIONS = 100_000
SESSION_TIMEOUT_SEC = 900  # 15 хвилин


class User:
    """Клас звичайного користувача системи."""

    def __init__(self, username: str, email: str, role: str = "user"):
        self.username = username
        self._email = ""
        self.email = email  # Викликає setter із валідацією
        self.role = role
        self.active = True
        self.__password_salt = os.urandom(16)
        self.__password_hash = b""

    @property
    def email(self) -> str:
        """Повертає поточний email."""
        return self._email

    @email.setter
    def email(self, new_email: str) -> None:
        """Перевіряє коректність email перед збереженням."""
        # Латинська літера на початку, 3-64 символи локальної частини, далі @ і домен
        pattern = r"^[a-zA-Z][a-zA-Z0-9_.]{2,63}@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$"
        if not re.match(pattern, new_email):
            raise ValueError(f"Некоректний формат email: {new_email}")
        self._email = new_email

    def set_password(self, password: str) -> None:
        """Безпечно хешує пароль за алгоритмом PBKDF2."""
        if not password:
            raise ValueError("Пароль не може бути порожнім.")
        self.__password_hash = hashlib.pbkdf2_hmac(
            "sha256",
            password.encode("utf-8"),
            self.__password_salt,
            HASH_ITERATIONS,
        )

    def check_password(self, password: str) -> bool:
        """Порівнює пароль із хешем за сталий час."""
        if not self.__password_hash or not password:
            return False
        test_hash = hashlib.pbkdf2_hmac(
            "sha256",
            password.encode("utf-8"),
            self.__password_salt,
            HASH_ITERATIONS,
        )
        return hmac.compare_digest(self.__password_hash, test_hash)

    def deactivate(self) -> None:
        """Деактивує користувача."""
        self.active = False

    def __str__(self) -> str:
        status = "Active" if self.active else "Inactive"
        return f"User({self.username}, email={self.email}, role={self.role}, status={status})"


class Admin(User):
    """Клас адміністратора, що успадковує User та додає список прав."""

    def __init__(
        self,
        username: str,
        email: str,
        permissions: set | None = None,
    ):
        super().__init__(username, email, role="admin")
        self.permissions = set(permissions) if permissions else set()

    def grant_permission(self, permission: str) -> None:
        """Додає нове право доступу."""
        self.permissions.add(permission)

    def revoke_permission(self, permission: str) -> None:
        """Видаляє право доступу."""
        self.permissions.discard(permission)

    def has_permission(self, permission: str) -> bool:
        """Перевіряє наявність права доступу."""
        return permission in self.permissions

    def __str__(self) -> str:
        base_str = super().__str__()
        perms_str = ", ".join(sorted(self.permissions)) or "None"
        return f"{base_str} [Permissions: {perms_str}]"


class Session:
    """Клас для відстеження активної сесії користувача."""

    def __init__(self, ip: str):
        self.ip = ip
        now = datetime.now(timezone.utc)
        self.login_time = now
        self.last_activity = now

    def touch(self) -> None:
        """Оновлює час останньої активності сесії."""
        self.last_activity = datetime.now(timezone.utc)

    def is_active(self, timeout_sec: int) -> bool:
        """Перевіряє, чи не минув таймаут активності."""
        if timeout_sec <= 0:
            raise ValueError("Таймаут має бути додатним числом.")
        now = datetime.now(timezone.utc)
        return (now - self.last_activity) <= timedelta(seconds=timeout_sec)


@dataclass
class AuditRecord:
    """Окремий запис у журналі подій аудиту."""

    timestamp: datetime
    username: str
    action: str


class AuditLog:
    """Клас для ведення журналу подій безпеки."""

    def __init__(self):
        self.records: list[AuditRecord] = []

    def add_log(self, username: str, action: str) -> None:
        """Додає подію до журналу (час у форматі UTC)."""
        record = AuditRecord(
            timestamp=datetime.now(timezone.utc),
            username=username,
            action=action,
        )
        self.records.append(record)

    def show_all(self) -> list[AuditRecord]:
        """Повертає список усіх записів."""
        return self.records


class UserAccount:
    """Клас облікового запису, що об'єднує User, Session та AuditLog (композиція)."""

    def __init__(self, user: User, audit_log: AuditLog | None = None):
        self.user = user
        self.session: Session | None = None
        self.audit_log = audit_log if audit_log is not None else AuditLog()

    def login(self, username: str, password: str, ip: str) -> bool:
        """Перевіряє автентифікацію та створює сесію у разі успіху."""
        if not self.user.active or self.user.username != username:
            self.audit_log.add_log(username, "login_failure")
            return False

        if self.user.check_password(password):
            self.session = Session(ip=ip)
            self.session.touch()
            self.audit_log.add_log(username, "login_success")
            return True

        self.audit_log.add_log(username, "login_failure")
        return False

    def is_authenticated(self) -> bool:
        """Перевіряє, чи є активна сесія та чи не вийшов її час."""
        if self.session is None:
            return False
        return self.session.is_active(SESSION_TIMEOUT_SEC)

    def logout(self) -> None:
        """Завершує активну сесію та записує подію в аудит."""
        if self.session is not None:
            self.audit_log.add_log(self.user.username, "logout")
            self.session = None

    def __getitem__(self, key: str):
        """Дозволяє отримувати атрибути через квадратні дужки account['user']."""
        if key == "user":
            return self.user
        if key == "session":
            return self.session
        if key == "audit_log":
            return self.audit_log
        raise KeyError(f"Невідомий або заборонений ключ: {key}")

    def __setitem__(self, key: str, value):
        """Дозволяє змінювати дозволені атрибути з перевіркою типу."""
        if key == "user":
            if not isinstance(value, User):
                raise TypeError("Значення для 'user' має бути екземпляром User.")
            self.user = value
        elif key == "session":
            if value is not None and not isinstance(value, Session):
                raise TypeError("Значення для 'session' має бути Session або None.")
            self.session = value
        elif key == "audit_log":
            if not isinstance(value, AuditLog):
                raise TypeError("Значення для 'audit_log' має бути AuditLog.")
            self.audit_log = value
        else:
            raise KeyError(f"Невідомий ключ: {key}")
