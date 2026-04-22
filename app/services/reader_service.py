from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy.orm import Session

from app.models import Reader
from app.repositories.reader_repository import ReaderRepository
from app.services.exceptions import ConflictError, NotFoundError


class ReaderAlreadyExistsError(ConflictError):
    pass


@dataclass(slots=True)
class ReaderRegistrationData:
    name: str
    surname: str
    email: str
    role: str
    password: str


class ReaderService:
    def __init__(self, session: Session, readers: ReaderRepository) -> None:
        self._session = session
        self._readers = readers

    def get_reader(self, reader_id: int) -> Reader | None:
        return self._readers.get_by_id(reader_id)

    def require_reader(self, reader_id: int, *, message: str = 'There is no user with this ID.') -> Reader:
        reader = self.get_reader(reader_id)
        if reader is None:
            raise NotFoundError(message)
        return reader

    def get_reader_by_email(self, email: str) -> Reader | None:
        return self._readers.get_by_email(email.strip())

    def authenticate(self, email: str, password: str) -> Reader | None:
        reader = self.get_reader_by_email(email)
        if reader is None or not reader.check_password(password):
            return None
        return reader

    def register_reader(self, data: ReaderRegistrationData) -> Reader:
        normalized = ReaderRegistrationData(
            name=data.name.strip(),
            surname=data.surname.strip(),
            email=data.email.strip(),
            role=data.role,
            password=data.password,
        )

        if self._readers.get_by_email(normalized.email) is not None:
            raise ReaderAlreadyExistsError('Email already registered.')

        reader = Reader(
            name=normalized.name,
            surname=normalized.surname,
            email=normalized.email,
            role=normalized.role,
        )
        reader.set_password(normalized.password)
        self._readers.add(reader)
        self._session.commit()
        return reader
