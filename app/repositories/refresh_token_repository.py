from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import RefreshTokenSession


class RefreshTokenRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def get_by_session_id(self, session_id: str) -> RefreshTokenSession | None:
        statement = select(RefreshTokenSession).where(RefreshTokenSession.session_id == session_id)
        return self._session.execute(statement).scalar_one_or_none()

    def add(self, token_session: RefreshTokenSession) -> None:
        self._session.add(token_session)
