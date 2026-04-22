from __future__ import annotations

from typing import Any

from sqlalchemy.orm import Session

from app.models import Annotation, Book
from app.repositories.annotation_repository import AnnotationRepository
from app.repositories.book_repository import BookRepository
from app.services.access_policy import can_create_annotation, can_delete_annotation, can_update_annotation, can_view_hidden_books
from app.services.exceptions import (
    AuthenticationRequiredError,
    BadRequestError,
    NotFoundError,
    PermissionDeniedError,
    ValidationError,
)

_UNSET = object()


class AnnotationService:
    def __init__(self, session: Session, annotations: AnnotationRepository, books: BookRepository) -> None:
        self._session = session
        self._annotations = annotations
        self._books = books

    def list_book_annotations_desc(self, book_id: int) -> list[Annotation]:
        return self._annotations.list_for_book_desc(book_id)

    def get_annotation(self, annotation_id: int) -> Annotation | None:
        return self._annotations.get_by_id(annotation_id)

    def require_annotation(
        self,
        annotation_id: int,
        *,
        message: str = 'There is no annotation with this ID.',
    ) -> Annotation:
        annotation = self.get_annotation(annotation_id)
        if annotation is None:
            raise NotFoundError(message)
        return annotation

    def create_annotation(self, actor: Any, book_id: int, *, text: object) -> Annotation:
        book = self._require_accessible_book(book_id, actor)
        if not getattr(actor, 'is_authenticated', False):
            raise AuthenticationRequiredError('Authentication required.')
        if not can_create_annotation(actor):
            raise PermissionDeniedError('Only librarians can add annotations.')

        annotation = Annotation(
            text=self._normalize_text(text),
            book_id=book.id,
            reviewer_id=actor.id,
        )
        self._annotations.add(annotation)
        self._session.commit()
        return annotation

    def update_annotation(self, actor: Any, annotation_id: int, *, text: object = _UNSET) -> Annotation:
        annotation = self.require_annotation(annotation_id)
        if not getattr(actor, 'is_authenticated', False):
            raise AuthenticationRequiredError('Authentication required.')
        if not can_update_annotation(actor):
            raise PermissionDeniedError('Only librarians can update annotations.')
        if text is _UNSET:
            raise BadRequestError('No valid fields to update.')

        annotation.text = self._normalize_text(text)
        self._session.commit()
        return annotation

    def delete_annotation(self, actor: Any, annotation_id: int) -> int:
        annotation = self.require_annotation(annotation_id)
        if not getattr(actor, 'is_authenticated', False):
            raise AuthenticationRequiredError('Authentication required.')
        if not can_delete_annotation(actor):
            raise PermissionDeniedError('Only librarians can delete annotations.')

        book_id = annotation.book_id
        self._annotations.delete(annotation)
        self._session.commit()
        return book_id

    def _require_accessible_book(self, book_id: int, actor: Any) -> Book:
        book = self._books.get_by_id(book_id, include_hidden=can_view_hidden_books(actor))
        if book is not None:
            return book

        hidden_book = self._books.get_by_id(book_id, include_hidden=True)
        if hidden_book is not None and hidden_book.is_hidden and not can_view_hidden_books(actor):
            raise PermissionDeniedError('This book is hidden.')

        raise NotFoundError('There is no book with this ID.')

    @staticmethod
    def _normalize_text(value: object) -> str:
        text = str(value).strip()
        if not text:
            raise ValidationError('Validation failed.', details={'text': 'Text is required.'})
        if len(text) > 200:
            raise ValidationError('Validation failed.', details={'text': 'Text must be at most 200 characters.'})
        return text
