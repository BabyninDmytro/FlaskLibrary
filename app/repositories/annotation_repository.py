from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Annotation


class AnnotationRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def list_for_book_desc(self, book_id: int) -> list[Annotation]:
        statement = select(Annotation).filter_by(book_id=book_id).order_by(Annotation.id.desc())
        return list(self._session.execute(statement).scalars().all())

    def get_by_id(self, annotation_id: int) -> Annotation | None:
        statement = select(Annotation).filter_by(id=annotation_id)
        return self._session.execute(statement).scalar_one_or_none()

    def add(self, annotation: Annotation) -> None:
        self._session.add(annotation)

    def delete(self, annotation: Annotation) -> None:
        self._session.delete(annotation)
