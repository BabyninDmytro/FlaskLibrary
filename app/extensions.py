from __future__ import annotations

import time
from collections.abc import Hashable
from typing import Any

from flask import Flask
from flask_login import LoginManager
from flask_sqlalchemy import SQLAlchemy


db: SQLAlchemy = SQLAlchemy()
login_manager: LoginManager = LoginManager()


class SimpleTTLCache:
    def __init__(self) -> None:
        self._store: dict[Hashable, tuple[float | None, Any]] = {}

    def init_app(self, app: Flask) -> None:
        return None

    def get(self, key: Hashable) -> Any | None:
        item = self._store.get(key)
        if item is None:
            return None

        expires_at, value = item
        if expires_at is not None and expires_at <= time.time():
            self._store.pop(key, None)
            return None

        return value

    def set(self, key: Hashable, value: Any, timeout: int | float | None = None) -> None:
        if timeout is None:
            expires_at = None
        else:
            expires_at = time.time() + timeout
        self._store[key] = (expires_at, value)

    def clear(self) -> None:
        self._store.clear()


cache: SimpleTTLCache = SimpleTTLCache()
