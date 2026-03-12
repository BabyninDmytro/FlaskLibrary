import time

from flask_login import LoginManager
from flask_sqlalchemy import SQLAlchemy


db = SQLAlchemy()
login_manager = LoginManager()


class SimpleTTLCache:
    def __init__(self):
        self._store = {}

    def init_app(self, app):
        return None

    def get(self, key):
        item = self._store.get(key)
        if item is None:
            return None

        expires_at, value = item
        if expires_at is not None and expires_at <= time.time():
            self._store.pop(key, None)
            return None

        return value

    def set(self, key, value, timeout=None):
        if timeout is None:
            expires_at = None
        else:
            expires_at = time.time() + timeout
        self._store[key] = (expires_at, value)

    def clear(self):
        self._store.clear()


cache = SimpleTTLCache()
