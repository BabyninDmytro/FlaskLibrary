from __future__ import annotations

from typing import Any

from app.models import Annotation, Book, Reader, Review


def serialize_book(book: Book) -> dict[str, Any]:
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


def serialize_review(review: Review) -> dict[str, Any]:
    return {
        'id': review.id,
        'stars': review.stars,
        'text': review.text,
        'book_id': review.book_id,
        'reviewer_id': review.reviewer_id,
    }


def serialize_annotation(annotation: Annotation) -> dict[str, Any]:
    return {
        'id': annotation.id,
        'text': annotation.text,
        'book_id': annotation.book_id,
        'reviewer_id': annotation.reviewer_id,
    }


def serialize_reader(reader: Reader) -> dict[str, Any]:
    return {
        'id': reader.id,
        'name': reader.name,
        'surname': reader.surname,
        'email': reader.email,
        'role': reader.role,
        'joined_at': reader.joined_at.isoformat() if reader.joined_at else None,
    }
