from __future__ import annotations

from sqlalchemy.orm import Session

from app.extensions import db
from app.repositories import AnnotationRepository, BookRepository, ReaderRepository, ReviewRepository
from app.services.annotation_service import AnnotationService
from app.services.book_service import BookService
from app.services.reader_service import ReaderService
from app.services.review_service import ReviewService


def _resolve_session(session: Session | None = None) -> Session:
    return session or db.session


def build_book_service(session: Session | None = None) -> BookService:
    active_session = _resolve_session(session)
    return BookService(session=active_session, books=BookRepository(active_session))


def build_reader_service(session: Session | None = None) -> ReaderService:
    active_session = _resolve_session(session)
    return ReaderService(session=active_session, readers=ReaderRepository(active_session))


def build_review_service(session: Session | None = None) -> ReviewService:
    active_session = _resolve_session(session)
    return ReviewService(
        session=active_session,
        books=BookRepository(active_session),
        reviews=ReviewRepository(active_session),
    )


def build_annotation_service(session: Session | None = None) -> AnnotationService:
    active_session = _resolve_session(session)
    return AnnotationService(
        session=active_session,
        annotations=AnnotationRepository(active_session),
        books=BookRepository(active_session),
    )
