from __future__ import annotations

from flask import Blueprint, jsonify, request
from flask.typing import ResponseReturnValue
from marshmallow import Schema, ValidationError as MarshmallowValidationError
from werkzeug.exceptions import HTTPException

from app.schemas import login_request_schema, normalize_schema_errors, refresh_request_schema
from app.serializers import serialize_reader
from app.services.auth_service import ApiActor
from app.services.exceptions import AuthenticationRequiredError, BadRequestError, ServiceError, ValidationError
from app.services.factories import build_auth_service
from app.services.token_service import TokenPair


bp = Blueprint('api_auth', __name__)


def _auth_service():
    return build_auth_service()


def _json_payload() -> dict[str, object]:
    payload = request.get_json(silent=True)
    if payload is None:
        return {}
    if not isinstance(payload, dict):
        raise BadRequestError('Request body must be a JSON object.')
    return dict(payload)


def _validated_payload(schema: Schema) -> dict[str, object]:
    try:
        loaded = schema.load(_json_payload())
    except MarshmallowValidationError as error:
        raise ValidationError('Validation failed.', details=normalize_schema_errors(error.messages)) from error
    return dict(loaded)


def _json_error(status: int, message: str, details: dict[str, object] | None = None) -> ResponseReturnValue:
    payload: dict[str, object] = {'error': {'code': status, 'message': message}}
    if details is not None:
        payload['error']['details'] = details
    return jsonify(payload), status


def _bearer_token() -> str:
    authorization = request.headers.get('Authorization', '').strip()
    if not authorization:
        raise AuthenticationRequiredError('Authentication required.')

    scheme, _, token = authorization.partition(' ')
    token_value = token.strip()
    if scheme.lower() != 'bearer' or not token_value:
        raise AuthenticationRequiredError('Authorization header must use Bearer token.')
    return token_value


def _token_payload(tokens: TokenPair, reader_payload: dict[str, object]) -> dict[str, object]:
    return {
        'token_type': tokens.token_type,
        'access_token': tokens.access_token,
        'refresh_token': tokens.refresh_token,
        'access_expires_at': tokens.access_expires_at.isoformat(),
        'refresh_expires_at': tokens.refresh_expires_at.isoformat(),
        'reader': reader_payload,
    }


def _require_bearer_actor() -> ApiActor:
    return _auth_service().authenticate_access_token(_bearer_token())


@bp.errorhandler(ServiceError)
def handle_service_error(error: ServiceError) -> ResponseReturnValue:
    details = dict(error.details) if error.details is not None else None
    return _json_error(error.status_code, error.message, details)


@bp.errorhandler(HTTPException)
def handle_http_exception(error: HTTPException) -> ResponseReturnValue:
    message = error.description if getattr(error, 'description', None) else error.name
    return _json_error(error.code or 500, message)


@bp.route('/api/v1/auth/login', methods=['POST'])
def login() -> ResponseReturnValue:
    payload = _validated_payload(login_request_schema)
    reader, tokens = _auth_service().login(
        email=payload['email'],
        password=payload['password'],
        user_agent=request.user_agent.string or None,
        ip_address=request.remote_addr,
    )
    return jsonify(_token_payload(tokens, serialize_reader(reader)))


@bp.route('/api/v1/auth/refresh', methods=['POST'])
def refresh() -> ResponseReturnValue:
    payload = _validated_payload(refresh_request_schema)
    reader, tokens = _auth_service().refresh(
        refresh_token=payload['refresh_token'],
        user_agent=request.user_agent.string or None,
        ip_address=request.remote_addr,
    )
    return jsonify(_token_payload(tokens, serialize_reader(reader)))


@bp.route('/api/v1/auth/logout', methods=['POST'])
def logout() -> ResponseReturnValue:
    actor = _require_bearer_actor()
    if actor.session_id is None:
        raise AuthenticationRequiredError('Authentication required.')

    _auth_service().revoke_session(actor.session_id)
    return '', 204


@bp.route('/api/v1/auth/me', methods=['GET'])
def me() -> ResponseReturnValue:
    actor = _require_bearer_actor()
    reader = _auth_service().get_reader_for_actor(actor)
    return jsonify(serialize_reader(reader))
