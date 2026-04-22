from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Review


class ReviewRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def list_for_book_desc(self, book_id: int) -> list[Review]:
        statement = select(Review).filter_by(book_id=book_id).order_by(Review.id.desc())
        return list(self._session.execute(statement).scalars().all())

    def get_by_id(self, review_id: int) -> Review | None:
        statement = select(Review).filter_by(id=review_id)
        return self._session.execute(statement).scalar_one_or_none()

    def add(self, review: Review) -> None:
        self._session.add(review)

    def delete(self, review: Review) -> None:
        self._session.delete(review)
