from __future__ import annotations

from typing import Any

from sqlalchemy.orm import Session

from app.models import Book, Review
from app.repositories.book_repository import BookRepository
from app.repositories.review_repository import ReviewRepository
from app.services.access_policy import can_create_review, can_delete_review, can_update_review, can_view_hidden_books
from app.services.exceptions import (
    AuthenticationRequiredError,
    BadRequestError,
    NotFoundError,
    PermissionDeniedError,
    ValidationError,
)

_UNSET = object()


class ReviewService:
    def __init__(self, session: Session, books: BookRepository, reviews: ReviewRepository) -> None:
        self._session = session
        self._books = books
        self._reviews = reviews

    def list_book_reviews_desc(self, book_id: int) -> list[Review]:
        return self._reviews.list_for_book_desc(book_id)

    def get_review(self, review_id: int) -> Review | None:
        return self._reviews.get_by_id(review_id)

    def require_review(self, review_id: int, *, message: str = 'There is no review with this ID.') -> Review:
        review = self.get_review(review_id)
        if review is None:
            raise NotFoundError(message)
        return review

    def create_review(self, actor: Any, book_id: int, *, text: object, stars: object) -> Review:
        book = self._require_accessible_book(book_id, actor)
        if not can_create_review(actor):
            raise AuthenticationRequiredError('Authentication required.')

        review = Review(
            text=self._normalize_text(text, field_name='text'),
            stars=self._normalize_stars(stars),
            book_id=book.id,
            reviewer_id=actor.id,
        )
        self._reviews.add(review)
        self._session.commit()
        return review

    def update_review(
        self,
        actor: Any,
        review_id: int,
        *,
        text: object = _UNSET,
        stars: object = _UNSET,
    ) -> Review:
        review = self.require_review(review_id)
        if not getattr(actor, 'is_authenticated', False):
            raise AuthenticationRequiredError('Authentication required.')
        if not can_update_review(actor):
            raise PermissionDeniedError('Only librarians can update reviews.')

        updates: dict[str, str | int] = {}
        if text is not _UNSET:
            updates['text'] = self._normalize_text(text, field_name='text')
        if stars is not _UNSET:
            updates['stars'] = self._normalize_stars(stars)
        if not updates:
            raise BadRequestError('No valid fields to update.')

        for key, value in updates.items():
            setattr(review, key, value)

        self._session.commit()
        return review

    def delete_review(self, actor: Any, review_id: int) -> int:
        review = self.require_review(review_id)
        if not getattr(actor, 'is_authenticated', False):
            raise AuthenticationRequiredError('Authentication required.')
        if not can_delete_review(actor, review):
            raise PermissionDeniedError('You can delete only your own review unless you are a librarian.')

        book_id = review.book_id
        self._reviews.delete(review)
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
    def _normalize_text(value: object, *, field_name: str) -> str:
        text = str(value).strip()
        if not text:
            raise ValidationError('Validation failed.', details={field_name: 'Text is required.'})
        if len(text) > 200:
            raise ValidationError('Validation failed.', details={field_name: 'Text must be at most 200 characters.'})
        return text

    @staticmethod
    def _normalize_stars(value: object) -> int:
        if not isinstance(value, int) or value < 1 or value > 5:
            raise ValidationError('Validation failed.', details={'stars': 'Stars must be an integer between 1 and 5.'})
        return value
