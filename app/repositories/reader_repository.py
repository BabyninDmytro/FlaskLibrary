from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Reader


class ReaderRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def get_by_id(self, reader_id: int) -> Reader | None:
        return self._session.get(Reader, reader_id, populate_existing=True)

    def get_by_email(self, email: str) -> Reader | None:
        statement = select(Reader).filter_by(email=email)
        return self._session.execute(statement).scalar_one_or_none()

    def add(self, reader: Reader) -> None:
        self._session.add(reader)
