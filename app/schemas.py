from __future__ import annotations

from typing import Any

from marshmallow import EXCLUDE, RAISE, Schema, fields, validate, validates_schema, ValidationError as MarshmallowValidationError


def normalize_schema_errors(errors: dict[str, Any]) -> dict[str, object]:
    normalized: dict[str, object] = {}
    for field_name, messages in errors.items():
        if isinstance(messages, list) and len(messages) == 1:
            normalized[field_name] = str(messages[0])
            continue
        normalized[field_name] = messages
    return normalized


class StrictSchema(Schema):
    class Meta:
        unknown = RAISE


class ReaderSchema(StrictSchema):
    id = fields.Integer(required=True)
    name = fields.String(required=True)
    surname = fields.String(required=True)
    email = fields.Email(required=True)
    role = fields.String(required=True)
    joined_at = fields.DateTime(format='iso', allow_none=True)


class BookSchema(StrictSchema):
    id = fields.Integer(required=True)
    title = fields.String(required=True)
    author_name = fields.String(required=True)
    author_surname = fields.String(required=True)
    original_language = fields.String(allow_none=True)
    translation_language = fields.String(allow_none=True)
    first_publication = fields.String(allow_none=True)
    genre = fields.String(allow_none=True)
    month = fields.String(allow_none=True)
    year = fields.Integer(allow_none=True)
    cover_image = fields.String(allow_none=True)


class ReviewSchema(StrictSchema):
    id = fields.Integer(required=True)
    stars = fields.Integer(required=True)
    text = fields.String(required=True)
    book_id = fields.Integer(required=True)
    reviewer_id = fields.Integer(required=True)


class AnnotationSchema(StrictSchema):
    id = fields.Integer(required=True)
    text = fields.String(required=True)
    book_id = fields.Integer(required=True)
    reviewer_id = fields.Integer(required=True)


class LoginRequestSchema(StrictSchema):
    email = fields.Email(required=True)
    password = fields.String(required=True, validate=validate.Length(min=1))


class RefreshRequestSchema(StrictSchema):
    refresh_token = fields.String(required=True, validate=validate.Length(min=1))


class ReviewCreateRequestSchema(StrictSchema):
    text = fields.String(required=True, validate=validate.Length(min=1, max=200))
    stars = fields.Integer(required=True, strict=True, validate=validate.Range(min=1, max=5))


class ReviewUpdateRequestSchema(StrictSchema):
    text = fields.String(validate=validate.Length(min=1, max=200))
    stars = fields.Integer(strict=True, validate=validate.Range(min=1, max=5))

    @validates_schema
    def validate_has_update(self, data: dict[str, object], **_: object) -> None:
        if not data:
            raise MarshmallowValidationError({'_schema': ['At least one field must be provided.']})


class AnnotationRequestSchema(StrictSchema):
    text = fields.String(required=True, validate=validate.Length(min=1, max=200))


class AnnotationUpdateRequestSchema(StrictSchema):
    text = fields.String(validate=validate.Length(min=1, max=200))

    @validates_schema
    def validate_has_update(self, data: dict[str, object], **_: object) -> None:
        if not data:
            raise MarshmallowValidationError({'_schema': ['At least one field must be provided.']})


class LenientBookDumpSchema(BookSchema):
    class Meta:
        unknown = EXCLUDE


class LenientReviewDumpSchema(ReviewSchema):
    class Meta:
        unknown = EXCLUDE


class LenientAnnotationDumpSchema(AnnotationSchema):
    class Meta:
        unknown = EXCLUDE


class LenientReaderDumpSchema(ReaderSchema):
    class Meta:
        unknown = EXCLUDE


book_schema = LenientBookDumpSchema()
review_schema = LenientReviewDumpSchema()
annotation_schema = LenientAnnotationDumpSchema()
reader_schema = LenientReaderDumpSchema()

login_request_schema = LoginRequestSchema()
refresh_request_schema = RefreshRequestSchema()
review_create_request_schema = ReviewCreateRequestSchema()
review_update_request_schema = ReviewUpdateRequestSchema()
annotation_request_schema = AnnotationRequestSchema()
annotation_update_request_schema = AnnotationUpdateRequestSchema()
