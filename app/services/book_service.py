from sqlalchemy import String, and_, cast, or_, select

from app.extensions import db
from app.models import Book


class BookAlreadyExistsError(ValueError):
    pass


def build_books_query(search_query='', include_hidden=True):
    stmt = select(Book)

    if not include_hidden:
        stmt = stmt.where(Book.is_hidden.is_(False))

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
                    Book.original_language.ilike(lookup),
                    Book.translation_language.ilike(lookup),
                    Book.first_publication.ilike(lookup),
                    Book.genre.ilike(lookup),
                    Book.month.ilike(lookup),
                    cast(Book.year, String).ilike(lookup),
                )
            )

        if term_filters:
            stmt = stmt.where(and_(*term_filters))

    return stmt


def paginate_books(search_query='', page=1, per_page=10, include_hidden=True):
    stmt = build_books_query(search_query, include_hidden=include_hidden)
    stmt = stmt.order_by(Book.year.desc(), Book.month.asc(), Book.title.asc())
    return db.paginate(
        stmt,
        page=page,
        per_page=per_page,
        error_out=False,
    )


def get_book_or_404(book_id, description='There is no book with this ID.', include_hidden=True):
    stmt = select(Book).where(Book.id == book_id)
    if not include_hidden:
        stmt = stmt.where(Book.is_hidden.is_(False))
    return db.first_or_404(stmt, description=description)


def get_book_by_title(title):
    normalized_title = title.strip()
    stmt = select(Book).where(Book.title == normalized_title)
    return db.session.execute(stmt).scalar_one_or_none()


def create_book(
    *,
    title,
    author_name,
    author_surname,
    original_language,
    translation_language,
    first_publication,
    genre,
    month,
    year,
    cover_image='',
    is_hidden=False,
):
    normalized_title = title.strip()
    if get_book_by_title(normalized_title) is not None:
        raise BookAlreadyExistsError('A book with this title already exists.')

    book = Book(
        title=normalized_title,
        author_name=author_name.strip(),
        author_surname=author_surname.strip(),
        original_language=original_language.strip(),
        translation_language=translation_language.strip(),
        first_publication=first_publication.strip(),
        genre=genre.strip(),
        month=month,
        year=year,
        cover_image=cover_image.strip() or 'book_covers/default.svg',
        is_hidden=bool(is_hidden),
    )
    db.session.add(book)
    db.session.commit()
    return book


def update_book(
    book,
    *,
    title,
    author_name,
    author_surname,
    original_language,
    translation_language,
    first_publication,
    genre,
    month,
    year,
    cover_image='',
    is_hidden=False,
):
    normalized_title = title.strip()
    existing_book = get_book_by_title(normalized_title)
    if existing_book is not None and existing_book.id != book.id:
        raise BookAlreadyExistsError('A book with this title already exists.')

    book.title = normalized_title
    book.author_name = author_name.strip()
    book.author_surname = author_surname.strip()
    book.original_language = original_language.strip()
    book.translation_language = translation_language.strip()
    book.first_publication = first_publication.strip()
    book.genre = genre.strip()
    book.month = month
    book.year = year
    book.cover_image = cover_image.strip() or 'book_covers/default.svg'
    book.is_hidden = bool(is_hidden)
    db.session.commit()
    return book


def serialize_book(book):
    return {
        'id': book.id,
        'title': book.title,
        'author_name': book.author_name,
        'author_surname': book.author_surname,
        'original_language': book.original_language,
        'translation_language': book.translation_language,
        'first_publication': book.first_publication,
        'genre': book.genre,
        'month': book.month,
        'year': book.year,
        'cover_image': book.cover_image,
    }
