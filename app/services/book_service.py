from sqlalchemy import String, and_, cast, or_, select

from app.extensions import db
from app.models import Book


def build_books_query(search_query=''):
    query = select(Book)

    if search_query:
        terms = [term for term in search_query.split() if term]
        term_filters = []

        for term in terms:
            lookup = f'%{term}%'
            term_filters.append(
                or_(
                    Book.title.ilike(lookup),
                    Book.author_name.ilike(lookup),
                    Book.author_surname.ilike(lookup),
                    Book.month.ilike(lookup),
                    cast(Book.year, String).ilike(lookup),
                )
            )

        if term_filters:
            query = query.where(and_(*term_filters))

    return query


def paginate_books(search_query='', page=1, per_page=10):
    query = build_books_query(search_query)
    query = query.order_by(Book.year.desc(), Book.month.asc(), Book.title.asc())
    return db.paginate(
        query,
        page=page,
        per_page=per_page,
        error_out=False,
    )


def get_book_or_404(book_id, description='There is no book with this ID.'):
    return db.first_or_404(select(Book).filter_by(id=book_id), description=description)


def serialize_book(book):
    return {
        'id': book.id,
        'title': book.title,
        'author_name': book.author_name,
        'author_surname': book.author_surname,
        'month': book.month,
        'year': book.year,
        'cover_image': book.cover_image,
    }
