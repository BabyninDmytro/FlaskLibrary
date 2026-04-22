from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from flask_sqlalchemy.pagination import Pagination
from sqlalchemy.orm import Session

from app.models import Book
from app.repositories.book_repository import BookRepository
from app.services.access_policy import can_create_book, can_update_book, can_view_hidden_books
from app.services.exceptions import AuthenticationRequiredError, ConflictError, NotFoundError, PermissionDeniedError


class BookAlreadyExistsError(ConflictError):
    pass


@dataclass(slots=True)
class BookWriteData:
    title: str
    author_name: str
    author_surname: str
    original_language: str
    translation_language: str
    first_publication: str
    genre: str
    month: str
    year: int
    cover_image: str = ''
    is_hidden: bool = False


class BookService:
    def __init__(self, session: Session, books: BookRepository) -> None:
        self._session = session
        self._books = books

    def paginate_books(
        self,
        search_query: str = '',
        *,
        page: int = 1,
        per_page: int = 10,
        include_hidden: bool = True,
    ) -> Pagination:
        return self._books.paginate(
            search_query,
            page=page,
            per_page=per_page,
            include_hidden=include_hidden,
        )

    def get_book(self, book_id: int, *, include_hidden: bool = True) -> Book | None:
        return self._books.get_by_id(book_id, include_hidden=include_hidden)

    def require_book(
        self,
        book_id: int,
        *,
        include_hidden: bool = True,
        message: str = 'There is no book with this ID.',
    ) -> Book:
        book = self.get_book(book_id, include_hidden=include_hidden)
        if book is None:
            raise NotFoundError(message)
        return book

    def get_book_for_actor(
        self,
        book_id: int,
        actor: Any,
        *,
        message: str = 'There is no book with this ID.',
    ) -> Book:
        visible_book = self.get_book(book_id, include_hidden=can_view_hidden_books(actor))
        if visible_book is not None:
            return visible_book

        hidden_book = self.get_book(book_id, include_hidden=True)
        if hidden_book is not None and hidden_book.is_hidden and not can_view_hidden_books(actor):
            raise PermissionDeniedError('This book is hidden.')

        raise NotFoundError(message)

    def create_book(self, actor: Any, data: BookWriteData) -> Book:
        if not can_create_book(actor):
            raise PermissionDeniedError('Only librarians can add books.')

        normalized = self._normalize_book_data(data)
        self._ensure_unique_title(normalized.title)

        book = Book(
            title=normalized.title,
            author_name=normalized.author_name,
            author_surname=normalized.author_surname,
            original_language=normalized.original_language,
            translation_language=normalized.translation_language,
            first_publication=normalized.first_publication,
            genre=normalized.genre,
            month=normalized.month,
            year=normalized.year,
            cover_image=normalized.cover_image,
            is_hidden=normalized.is_hidden,
        )
        self._books.add(book)
        self._session.commit()
        return book

    def update_book(self, actor: Any, book_id: int, data: BookWriteData) -> Book:
        if not can_update_book(actor):
            raise PermissionDeniedError('Only librarians can edit books.')

        book = self.require_book(book_id)
        normalized = self._normalize_book_data(data)
        existing_book = self._books.get_by_title(normalized.title)
        if existing_book is not None and existing_book.id != book.id:
            raise BookAlreadyExistsError('A book with this title already exists.')

        book.title = normalized.title
        book.author_name = normalized.author_name
        book.author_surname = normalized.author_surname
        book.original_language = normalized.original_language
        book.translation_language = normalized.translation_language
        book.first_publication = normalized.first_publication
        book.genre = normalized.genre
        book.month = normalized.month
        book.year = normalized.year
        book.cover_image = normalized.cover_image
        book.is_hidden = normalized.is_hidden
        self._session.commit()
        return book

    def toggle_book_hidden(self, actor: Any, book_id: int) -> Book:
        if not getattr(actor, 'is_authenticated', False):
            raise AuthenticationRequiredError('Authentication required.')
        if not can_view_hidden_books(actor):
            raise PermissionDeniedError('Only librarians can change visibility.')

        book = self.require_book(book_id)
        book.is_hidden = not book.is_hidden
        self._session.commit()
        return book

    def _ensure_unique_title(self, normalized_title: str) -> None:
        if self._books.get_by_title(normalized_title) is not None:
            raise BookAlreadyExistsError('A book with this title already exists.')

    @staticmethod
    def _normalize_book_data(data: BookWriteData) -> BookWriteData:
        return BookWriteData(
            title=data.title.strip(),
            author_name=data.author_name.strip(),
            author_surname=data.author_surname.strip(),
            original_language=data.original_language.strip(),
            translation_language=data.translation_language.strip(),
            first_publication=data.first_publication.strip(),
            genre=data.genre.strip(),
            month=data.month,
            year=data.year,
            cover_image=data.cover_image.strip() or 'book_covers/default.svg',
            is_hidden=bool(data.is_hidden),
        )
