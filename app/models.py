from __future__ import annotations

from datetime import datetime

from flask_login import UserMixin
from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import DynamicMapped, Mapped, mapped_column, relationship
from werkzeug.security import check_password_hash, generate_password_hash

from app.extensions import db


class Book(db.Model):
    __tablename__ = 'book'

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String(80), unique=True, index=True)
    author_name: Mapped[str] = mapped_column(String(50), index=True)
    author_surname: Mapped[str] = mapped_column(String(80), index=True)
    original_language: Mapped[str] = mapped_column(String(80), index=True, nullable=False, default='')
    translation_language: Mapped[str] = mapped_column(String(80), index=True, nullable=False, default='')
    first_publication: Mapped[str] = mapped_column(String(120), index=True, nullable=False, default='')
    genre: Mapped[str] = mapped_column(String(160), index=True, nullable=False, default='')
    month: Mapped[str] = mapped_column(String(20), index=True)
    year: Mapped[int] = mapped_column(Integer, index=True)
    cover_image: Mapped[str] = mapped_column(String(255), nullable=False, default='book_covers/default.svg')
    is_hidden: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, index=True)

    reviews: DynamicMapped[Review] = relationship(
        back_populates='book',
        lazy='dynamic',
        cascade='all, delete, delete-orphan',
    )
    annotations: DynamicMapped[Annotation] = relationship(
        back_populates='book',
        lazy='dynamic',
        cascade='all, delete, delete-orphan',
    )

    def __repr__(self) -> str:
        return f'Book(id={self.id}, month={self.month!r}, year={self.year!r})'


class Reader(UserMixin, db.Model):
    __tablename__ = 'reader'

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(50), index=True)
    surname: Mapped[str] = mapped_column(String(80), index=True)
    email: Mapped[str] = mapped_column(String(120), unique=True, index=True)
    password_hash: Mapped[str | None] = mapped_column(String(128))
    role: Mapped[str] = mapped_column(String(20), index=True, default='reader')
    joined_at: Mapped[datetime] = mapped_column(DateTime(), default=datetime.utcnow, index=True)

    reviews: DynamicMapped[Review] = relationship(
        back_populates='reviewer',
        lazy='dynamic',
        cascade='all, delete, delete-orphan',
    )
    annotations: DynamicMapped[Annotation] = relationship(
        back_populates='author',
        lazy='dynamic',
        cascade='all, delete, delete-orphan',
    )
    refresh_token_sessions: DynamicMapped[RefreshTokenSession] = relationship(
        back_populates='user',
        lazy='dynamic',
        cascade='all, delete, delete-orphan',
    )

    def __repr__(self) -> str:
        return f'Reader(id={self.id}, email={self.email!r})'

    def set_password(self, password: str) -> None:
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        if not self.password_hash:
            return False
        return check_password_hash(self.password_hash, password)


class Review(db.Model):
    __tablename__ = 'review'

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    stars: Mapped[int] = mapped_column(Integer)
    text: Mapped[str] = mapped_column(String(200))
    book_id: Mapped[int] = mapped_column(ForeignKey('book.id'))
    reviewer_id: Mapped[int] = mapped_column(ForeignKey('reader.id'))

    book: Mapped[Book] = relationship(back_populates='reviews')
    reviewer: Mapped[Reader] = relationship(back_populates='reviews')

    def __repr__(self) -> str:
        return f'Review(id={self.id}, stars={self.stars}, book_id={self.book_id})'


class Annotation(db.Model):
    __tablename__ = 'annotation'

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    text: Mapped[str] = mapped_column(String(200))
    reviewer_id: Mapped[int] = mapped_column(ForeignKey('reader.id'))
    book_id: Mapped[int] = mapped_column(ForeignKey('book.id'))

    author: Mapped[Reader] = relationship(back_populates='annotations')
    book: Mapped[Book] = relationship(back_populates='annotations')

    def __repr__(self) -> str:
        return f'Annotation(reviewer_id={self.reviewer_id}, book_id={self.book_id}, text={self.text!r})'


class RefreshTokenSession(db.Model):
    __tablename__ = 'refresh_token_session'

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey('reader.id'), index=True)
    session_id: Mapped[str] = mapped_column(String(32), unique=True, index=True)
    refresh_jti: Mapped[str] = mapped_column(String(32), unique=True, index=True)
    token_hash: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(), index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(), default=datetime.utcnow, index=True)
    last_used_at: Mapped[datetime | None] = mapped_column(DateTime())
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(), index=True)
    user_agent: Mapped[str | None] = mapped_column(String(255))
    ip_address: Mapped[str | None] = mapped_column(String(64))

    user: Mapped[Reader] = relationship(back_populates='refresh_token_sessions')

    def __repr__(self) -> str:
        return f'RefreshTokenSession(id={self.id}, user_id={self.user_id}, session_id={self.session_id!r})'
