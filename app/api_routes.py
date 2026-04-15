import hashlib
import json

from flask import Blueprint, jsonify, redirect, request, url_for
from flask_login import current_user
from werkzeug.exceptions import Forbidden, HTTPException

from app.extensions import cache
from app.extensions import db
from app.models import Book
from app.services.annotation_service import (
    create_annotation,
    delete_annotation,
    get_annotation,
    list_book_annotations_desc,
    serialize_annotation,
    update_annotation,
)
from app.services.access_policy import (
    can_create_annotation,
    can_create_review,
    can_delete_annotation,
    can_delete_review,
    can_update_annotation,
    can_update_review,
    can_view_hidden_books,
)
from app.services.book_service import get_book_or_404, paginate_books, serialize_book
from app.services.review_service import (
    create_review,
    delete_review,
    get_review,
    get_review_or_404,
    list_book_reviews_desc,
    serialize_review,
    update_review,
)


bp = Blueprint('api', __name__)


def _build_api_response(payload, ttl=60):
    payload_json = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    etag = hashlib.sha256(payload_json.encode('utf-8')).hexdigest()

    response = jsonify(payload)
    response.set_etag(etag, weak=False)
    response.cache_control.public = True
    response.cache_control.max_age = ttl
    response.headers['Vary'] = 'Accept'

    return response.make_conditional(request)


def _cached_public_json(cache_key, payload_factory, ttl=60):
    payload = cache.get(cache_key)
    if payload is None:
        payload = payload_factory()
        cache.set(cache_key, payload, timeout=ttl)

    return _build_api_response(payload, ttl=ttl)


def _invalidate_api_cache():
    cache.clear()


def _json_error(status, message, details=None):
    payload = {'error': {'code': status, 'message': message}}
    if details is not None:
        payload['error']['details'] = details
    return jsonify(payload), status


def _get_book_for_api(book_id):
    include_hidden = can_view_hidden_books(current_user)
    try:
        return get_book_or_404(book_id, include_hidden=include_hidden)
    except HTTPException:
        hidden_book = db.session.get(Book, book_id)
        if hidden_book and hidden_book.is_hidden and not include_hidden:
            raise Forbidden('This book is hidden.')
        raise


@bp.errorhandler(HTTPException)
def handle_http_exception(error):
    message = error.description if getattr(error, 'description', None) else error.name
    return _json_error(error.code or 500, message)


@bp.route('/api/v1/books', methods=['GET'])
def books_collection():
    search_query = request.args.get('search', '').strip()
    page = max(request.args.get('page', 1, type=int), 1)
    per_page = min(max(request.args.get('per_page', 10, type=int), 1), 50)
    visibility_scope = 'librarian' if can_view_hidden_books(current_user) else 'public'

    cache_key = f'api:v1:books:{visibility_scope}:search={search_query}:page={page}:per_page={per_page}'

    def payload_factory():
        paginated = paginate_books(
            search_query=search_query,
            page=page,
            per_page=per_page,
            include_hidden=can_view_hidden_books(current_user),
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

    return _cached_public_json(cache_key, payload_factory)


@bp.route('/api/v1/books/<int:book_id>', methods=['GET'])
def book_details(book_id):
    visibility_scope = 'librarian' if can_view_hidden_books(current_user) else 'public'
    cache_key = f'api:v1:books:{book_id}:details:{visibility_scope}'

    def payload_factory():
        book = _get_book_for_api(book_id)
        reviews = [serialize_review(review) for review in list_book_reviews_desc(book)]
        annotations = [serialize_annotation(annotation) for annotation in list_book_annotations_desc(book)]

        payload = serialize_book(book)
        payload['reviews'] = reviews
        payload['annotations'] = annotations
        return payload

    return _cached_public_json(cache_key, payload_factory)


@bp.route('/api/v1/books/<int:book_id>/reviews', methods=['POST'])
def review_create(book_id):
    book = _get_book_for_api(book_id)
    if not can_create_review(current_user):
        return _json_error(401, 'Authentication required.')

    payload = request.get_json(silent=True) or {}
    text = str(payload.get('text', '')).strip()
    stars = payload.get('stars')

    errors = {}
    if not text:
        errors['text'] = 'Text is required.'
    elif len(text) > 200:
        errors['text'] = 'Text must be at most 200 characters.'

    if not isinstance(stars, int) or stars < 1 or stars > 5:
        errors['stars'] = 'Stars must be an integer between 1 and 5.'

    if errors:
        return _json_error(422, 'Validation failed.', errors)

    review = create_review(text=text, stars=stars, book_id=book.id, reviewer_id=current_user.id)
    _invalidate_api_cache()
    return jsonify(serialize_review(review)), 201


@bp.route('/api/v1/books/<int:book_id>/annotations', methods=['POST'])
def annotation_create(book_id):
    book = _get_book_for_api(book_id)
    if not current_user.is_authenticated:
        return _json_error(401, 'Authentication required.')
    if not can_create_annotation(current_user):
        return _json_error(403, 'Only librarians can add annotations.')

    payload = request.get_json(silent=True) or {}
    text = str(payload.get('text', '')).strip()

    if not text:
        return _json_error(422, 'Validation failed.', {'text': 'Text is required.'})
    if len(text) > 200:
        return _json_error(422, 'Validation failed.', {'text': 'Text must be at most 200 characters.'})

    annotation = create_annotation(text=text, book_id=book.id, reviewer_id=current_user.id)
    _invalidate_api_cache()
    return jsonify(serialize_annotation(annotation)), 201


@bp.route('/api/v1/readers/<int:user_id>', methods=['GET'])
def reader_profile(user_id):
    from app.services.reader_service import get_reader_or_404, serialize_reader

    cache_key = f'api:v1:readers:{user_id}'

    def payload_factory():
        reader = get_reader_or_404(user_id)
        return serialize_reader(reader)

    return _cached_public_json(cache_key, payload_factory)


@bp.route('/api/v1/reviews/<int:review_id>', methods=['GET'])
def review_details(review_id):
    cache_key = f'api:v1:reviews:{review_id}'

    def payload_factory():
        review = get_review_or_404(review_id)
        return serialize_review(review)

    return _cached_public_json(cache_key, payload_factory)


@bp.route('/api/v1/reviews/<int:review_id>', methods=['PATCH'])
def review_update(review_id):
    review = get_review(review_id)
    if review is None:
        return _json_error(404, 'There is no review with this ID.')
    if not current_user.is_authenticated:
        return _json_error(401, 'Authentication required.')
    if not can_update_review(current_user):
        return _json_error(403, 'Only librarians can update reviews.')

    payload = request.get_json(silent=True) or {}
    updates = {}

    if 'text' in payload:
        text = str(payload.get('text', '')).strip()
        if not text:
            return _json_error(422, 'Validation failed.', {'text': 'Text is required.'})
        if len(text) > 200:
            return _json_error(422, 'Validation failed.', {'text': 'Text must be at most 200 characters.'})
        updates['text'] = text

    if 'stars' in payload:
        stars = payload.get('stars')
        if not isinstance(stars, int) or stars < 1 or stars > 5:
            return _json_error(422, 'Validation failed.', {'stars': 'Stars must be an integer between 1 and 5.'})
        updates['stars'] = stars

    if not updates:
        return _json_error(400, 'No valid fields to update.')

    review = update_review(review, updates)
    _invalidate_api_cache()
    return jsonify(serialize_review(review))


@bp.route('/api/v1/reviews/<int:review_id>', methods=['DELETE'])
def review_delete(review_id):
    review = get_review(review_id)
    if review is None:
        return _json_error(404, 'There is no review with this ID.')
    if not current_user.is_authenticated:
        return _json_error(401, 'Authentication required.')
    if not can_delete_review(current_user):
        return _json_error(403, 'Only librarians can delete reviews.')

    delete_review(review)
    _invalidate_api_cache()
    return ('', 204)


@bp.route('/api/v1/annotations/<int:annotation_id>', methods=['PATCH'])
def annotation_update(annotation_id):
    annotation = get_annotation(annotation_id)
    if annotation is None:
        return _json_error(404, 'There is no annotation with this ID.')
    if not current_user.is_authenticated:
        return _json_error(401, 'Authentication required.')
    if not can_update_annotation(current_user):
        return _json_error(403, 'Only librarians can update annotations.')

    payload = request.get_json(silent=True) or {}
    if 'text' not in payload:
        return _json_error(400, 'No valid fields to update.')

    text = str(payload.get('text', '')).strip()
    if not text:
        return _json_error(422, 'Validation failed.', {'text': 'Text is required.'})
    if len(text) > 200:
        return _json_error(422, 'Validation failed.', {'text': 'Text must be at most 200 characters.'})

    annotation = update_annotation(annotation, text)
    _invalidate_api_cache()
    return jsonify(serialize_annotation(annotation))


@bp.route('/api/v1/annotations/<int:annotation_id>', methods=['DELETE'])
def annotation_delete(annotation_id):
    annotation = get_annotation(annotation_id)
    if annotation is None:
        return _json_error(404, 'There is no annotation with this ID.')
    if not current_user.is_authenticated:
        return _json_error(401, 'Authentication required.')
    if not can_delete_annotation(current_user):
        return _json_error(403, 'Only librarians can delete annotations.')

    delete_annotation(annotation)
    _invalidate_api_cache()
    return ('', 204)


@bp.route('/api/v1/books/<int:book_id>/data', methods=['GET'])
def book_details_legacy(book_id):
    return redirect(url_for('api.book_details', book_id=book_id), code=301)


@bp.route('/api/v1/books/<int:book_id>/toggle-hidden', methods=['POST'])
def toggle_book_hidden(book_id):
    if not current_user.is_authenticated:
        return _json_error(401, 'Authentication required.')
    if not can_view_hidden_books(current_user):
        return _json_error(403, 'Only librarians can change visibility.')

    target_book = get_book_or_404(book_id)
    target_book.is_hidden = not target_book.is_hidden
    db.session.commit()
    _invalidate_api_cache()

    return jsonify(
        {
            'book_id': target_book.id,
            'is_hidden': target_book.is_hidden,
            'button_label': 'Unhide book' if target_book.is_hidden else 'Hide book',
            'button_label_short': 'Unhide' if target_book.is_hidden else 'Hide',
        }
    )
