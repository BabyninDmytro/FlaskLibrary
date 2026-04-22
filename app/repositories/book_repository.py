from __future__ import annotations

from flask_sqlalchemy.pagination import Pagination
from sqlalchemy import String, and_, cast, or_, select
from sqlalchemy.orm import Session
from sqlalchemy.sql import Select

from app.extensions import db
from app.models import Book


class BookRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def build_search_statement(self, search_query: str = '', *, include_hidden: bool = True) -> Select:
        statement = select(Book)

        if not include_hidden:
            statement = statement.where(Book.is_hidden.is_(False))

        if not search_query:
            return statement

        terms = [term for term in search_query.split() if term]
        term_filters = []

        for term in terms:
            lookup = f'%{term}%'
            term_filters.append(
                or_(
                    Book.title.ilike(lookup),
                    Book.author_name.ilike(lookup),
                    Book.author_surname.ilike(lookup),
                    Book.original_language.ilike(lookup),
                    Book.translation_language.ilike(lookup),
                    Book.first_publication.ilike(lookup),
                    Book.genre.ilike(lookup),
                    Book.month.ilike(lookup),
                    cast(Book.year, String).ilike(lookup),
                )
            )

        if term_filters:
            statement = statement.where(and_(*term_filters))

        return statement

    def paginate(
        self,
        search_query: str = '',
        *,
        page: int = 1,
        per_page: int = 10,
        include_hidden: bool = True,
    ) -> Pagination:
        statement = self.build_search_statement(search_query, include_hidden=include_hidden)
        statement = statement.order_by(Book.year.desc(), Book.month.asc(), Book.title.asc())
        return db.paginate(statement, page=page, per_page=per_page, error_out=False)

    def get_by_id(self, book_id: int, *, include_hidden: bool = True) -> Book | None:
        statement = select(Book).where(Book.id == book_id)
        if not include_hidden:
            statement = statement.where(Book.is_hidden.is_(False))
        return self._session.execute(statement).scalar_one_or_none()

    def get_by_title(self, title: str) -> Book | None:
        statement = select(Book).where(Book.title == title)
        return self._session.execute(statement).scalar_one_or_none()

    def add(self, book: Book) -> None:
        self._session.add(book)
