from __future__ import annotations

import hashlib
import json

from flask import Blueprint, jsonify, redirect, request, url_for
from flask.typing import ResponseReturnValue
from werkzeug.exceptions import HTTPException

from app.extensions import cache
from app.serializers import serialize_annotation, serialize_book, serialize_reader, serialize_review
from app.services.access_policy import can_view_hidden_books
from app.services.auth_service import AnonymousApiActor, ApiActor
from app.services.exceptions import AuthenticationRequiredError, BadRequestError, ServiceError
from app.services.factories import (
    build_annotation_service,
    build_auth_service,
    build_book_service,
    build_reader_service,
    build_review_service,
)


bp = Blueprint('api', __name__)


def _book_service():
    return build_book_service()


def _review_service():
    return build_review_service()


def _annotation_service():
    return build_annotation_service()


def _reader_service():
    return build_reader_service()


def _auth_service():
    return build_auth_service()


def _json_payload() -> dict[str, object]:
    payload = request.get_json(silent=True)
    if payload is None:
        return {}
    if not isinstance(payload, dict):
        raise BadRequestError('Request body must be a JSON object.')
    return dict(payload)


def _bearer_token() -> str | None:
    authorization = request.headers.get('Authorization', '').strip()
    if not authorization:
        return None

    scheme, _, token = authorization.partition(' ')
    token_value = token.strip()
    if scheme.lower() != 'bearer' or not token_value:
        raise AuthenticationRequiredError('Authorization header must use Bearer token.')
    return token_value


def _api_actor(*, required: bool = False) -> ApiActor | AnonymousApiActor:
    bearer_token = _bearer_token()
    if bearer_token is None:
        if required:
            raise AuthenticationRequiredError('Authentication required.')
        return AnonymousApiActor()

    try:
        return _auth_service().authenticate_access_token(bearer_token)
    except AuthenticationRequiredError:
        if required:
            raise
        return AnonymousApiActor()


def _build_api_response(payload, ttl=60) -> ResponseReturnValue:
    payload_json = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    etag = hashlib.sha256(payload_json.encode('utf-8')).hexdigest()

    response = jsonify(payload)
    response.set_etag(etag, weak=False)
    response.headers['Cache-Control'] = f'private, max-age={ttl}'
    response.headers['Vary'] = 'Accept, Authorization'

    return response.make_conditional(request)


def _cached_api_json(cache_key, payload_factory, ttl=60) -> ResponseReturnValue:
    payload = cache.get(cache_key)
    if payload is None:
        payload = payload_factory()
        cache.set(cache_key, payload, timeout=ttl)

    return _build_api_response(payload, ttl=ttl)


def _invalidate_api_cache() -> None:
    cache.clear()


def _json_error(status, message, details=None) -> ResponseReturnValue:
    payload: dict[str, object] = {'error': {'code': status, 'message': message}}
    if details is not None:
        payload['error']['details'] = details
    return jsonify(payload), status


@bp.errorhandler(ServiceError)
def handle_service_error(error) -> ResponseReturnValue:
    return _json_error(error.status_code, error.message, error.details)


@bp.errorhandler(HTTPException)
def handle_http_exception(error) -> ResponseReturnValue:
    message = error.description if getattr(error, 'description', None) else error.name
    return _json_error(error.code or 500, message)


@bp.route('/api/v1/books', methods=['GET'])
def books_collection() -> ResponseReturnValue:
    search_query = request.args.get('search', '').strip()
    page = max(request.args.get('page', 1, type=int), 1)
    per_page = min(max(request.args.get('per_page', 10, type=int), 1), 50)
    actor = _api_actor(required=True)
    visibility_scope = 'librarian' if can_view_hidden_books(actor) else 'reader'

    cache_key = f'api:v1:books:{visibility_scope}:search={search_query}:page={page}:per_page={per_page}'

    def payload_factory():
        paginated = _book_service().paginate_books(
            search_query=search_query,
            page=page,
            per_page=per_page,
            include_hidden=can_view_hidden_books(actor),
        )
        return {
            'items': [serialize_book(book) for book in paginated.items],
            'pagination': {
                'page': paginated.page,
                'per_page': paginated.per_page,
                'pages': paginated.pages,
                'total': paginated.total,
                'has_next': paginated.has_next,
                'has_prev': paginated.has_prev,
            },
            'search': search_query,
        }

    return _cached_api_json(cache_key, payload_factory)


@bp.route('/api/v1/books/<int:book_id>', methods=['GET'])
def book_details(book_id) -> ResponseReturnValue:
    actor = _api_actor(required=True)
    visibility_scope = 'librarian' if can_view_hidden_books(actor) else 'reader'
    cache_key = f'api:v1:books:{book_id}:details:{visibility_scope}'

    def payload_factory():
        book = _book_service().get_book_for_actor(book_id, actor)
        reviews = [serialize_review(review) for review in _review_service().list_book_reviews_desc(book.id)]
        annotations = [serialize_annotation(annotation) for annotation in _annotation_service().list_book_annotations_desc(book.id)]

        payload = serialize_book(book)
        payload['reviews'] = reviews
        payload['annotations'] = annotations
        return payload

    return _cached_api_json(cache_key, payload_factory)


@bp.route('/api/v1/books/<int:book_id>/reviews', methods=['POST'])
def review_create(book_id) -> ResponseReturnValue:
    actor = _api_actor(required=True)
    payload = _json_payload()
    review = _review_service().create_review(
        actor,
        book_id,
        text=payload.get('text', ''),
        stars=payload.get('stars'),
    )
    _invalidate_api_cache()
    return jsonify(serialize_review(review)), 201


@bp.route('/api/v1/books/<int:book_id>/annotations', methods=['POST'])
def annotation_create(book_id) -> ResponseReturnValue:
    actor = _api_actor(required=True)
    payload = _json_payload()
    annotation = _annotation_service().create_annotation(
        actor,
        book_id,
        text=payload.get('text', ''),
    )
    _invalidate_api_cache()
    return jsonify(serialize_annotation(annotation)), 201


@bp.route('/api/v1/readers/<int:user_id>', methods=['GET'])
def reader_profile(user_id) -> ResponseReturnValue:
    _api_actor(required=True)
    cache_key = f'api:v1:readers:{user_id}'

    def payload_factory():
        reader = _reader_service().require_reader(user_id)
        return serialize_reader(reader)

    return _cached_api_json(cache_key, payload_factory)


@bp.route('/api/v1/reviews/<int:review_id>', methods=['GET'])
def review_details(review_id) -> ResponseReturnValue:
    _api_actor(required=True)
    cache_key = f'api:v1:reviews:{review_id}'

    def payload_factory():
        review = _review_service().require_review(review_id)
        return serialize_review(review)

    return _cached_api_json(cache_key, payload_factory)


@bp.route('/api/v1/reviews/<int:review_id>', methods=['PATCH'])
def review_update(review_id) -> ResponseReturnValue:
    actor = _api_actor(required=True)
    payload = _json_payload()
    review_service = _review_service()

    if 'text' in payload and 'stars' in payload:
        review = review_service.update_review(actor, review_id, text=payload['text'], stars=payload['stars'])
    elif 'text' in payload:
        review = review_service.update_review(actor, review_id, text=payload['text'])
    elif 'stars' in payload:
        review = review_service.update_review(actor, review_id, stars=payload['stars'])
    else:
        review = review_service.update_review(actor, review_id)

    _invalidate_api_cache()
    return jsonify(serialize_review(review))


@bp.route('/api/v1/reviews/<int:review_id>', methods=['DELETE'])
def review_delete(review_id) -> ResponseReturnValue:
    actor = _api_actor(required=True)
    _review_service().delete_review(actor, review_id)
    _invalidate_api_cache()
    return ('', 204)


@bp.route('/api/v1/annotations/<int:annotation_id>', methods=['PATCH'])
def annotation_update(annotation_id) -> ResponseReturnValue:
    actor = _api_actor(required=True)
    payload = _json_payload()
    annotation_service = _annotation_service()

    if 'text' in payload:
        annotation = annotation_service.update_annotation(actor, annotation_id, text=payload['text'])
    else:
        annotation = annotation_service.update_annotation(actor, annotation_id)

    _invalidate_api_cache()
    return jsonify(serialize_annotation(annotation))


@bp.route('/api/v1/annotations/<int:annotation_id>', methods=['DELETE'])
def annotation_delete(annotation_id) -> ResponseReturnValue:
    actor = _api_actor(required=True)
    _annotation_service().delete_annotation(actor, annotation_id)
    _invalidate_api_cache()
    return ('', 204)


@bp.route('/api/v1/books/<int:book_id>/data', methods=['GET'])
def book_details_legacy(book_id) -> ResponseReturnValue:
    _api_actor(required=True)
    return redirect(url_for('api.book_details', book_id=book_id), code=301)


@bp.route('/api/v1/books/<int:book_id>/toggle-hidden', methods=['POST'])
def toggle_book_hidden(book_id) -> ResponseReturnValue:
    actor = _api_actor(required=True)
    target_book = _book_service().toggle_book_hidden(actor, book_id)
    _invalidate_api_cache()

    return jsonify(
        {
            'book_id': target_book.id,
            'is_hidden': target_book.is_hidden,
            'button_label': 'Unhide book' if target_book.is_hidden else 'Hide book',
            'button_label_short': 'Unhide' if target_book.is_hidden else 'Hide',
        }
    )
