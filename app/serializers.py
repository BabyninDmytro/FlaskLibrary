from __future__ import annotations

from typing import Any

from app.models import Annotation, Book, Reader, Review
from app.schemas import annotation_schema, book_schema, reader_schema, review_schema


def serialize_book(book: Book) -> dict[str, Any]:
    return dict(book_schema.dump(book))


def serialize_review(review: Review) -> dict[str, Any]:
    return dict(review_schema.dump(review))


def serialize_annotation(annotation: Annotation) -> dict[str, Any]:
    return dict(annotation_schema.dump(annotation))


def serialize_reader(reader: Reader) -> dict[str, Any]:
    return dict(reader_schema.dump(reader))
