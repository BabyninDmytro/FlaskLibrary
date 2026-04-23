from __future__ import annotations

from datetime import timedelta

from flask import current_app
from sqlalchemy.orm import Session

from app.extensions import db
from app.repositories import AnnotationRepository, BookRepository, ReaderRepository, RefreshTokenRepository, ReviewRepository
from app.services.auth_service import AuthService
from app.services.annotation_service import AnnotationService
from app.services.book_service import BookService
from app.services.reader_service import ReaderService
from app.services.review_service import ReviewService
from app.services.token_service import TokenService


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


def build_token_service() -> TokenService:
    secret_key = current_app.config.get('JWT_SECRET_KEY') or current_app.config['SECRET_KEY']
    access_minutes = int(current_app.config.get('JWT_ACCESS_TOKEN_EXPIRES_MINUTES', 15))
    refresh_days = int(current_app.config.get('JWT_REFRESH_TOKEN_EXPIRES_DAYS', 30))
    return TokenService(
        secret_key=secret_key,
        access_token_ttl=timedelta(minutes=access_minutes),
        refresh_token_ttl=timedelta(days=refresh_days),
    )


def build_auth_service(session: Session | None = None) -> AuthService:
    active_session = _resolve_session(session)
    return AuthService(
        session=active_session,
        readers=ReaderRepository(active_session),
        refresh_tokens=RefreshTokenRepository(active_session),
        token_service=build_token_service(),
    )
