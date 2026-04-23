from __future__ import annotations

import base64
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
import hashlib
import hmac
import json
from typing import Any
from uuid import uuid4

from app.services.exceptions import AuthenticationRequiredError


@dataclass(slots=True)
class TokenPair:
    access_token: str
    refresh_token: str
    access_expires_at: datetime
    refresh_expires_at: datetime
    token_type: str = 'Bearer'


class TokenService:
    def __init__(
        self,
        *,
        secret_key: str,
        access_token_ttl: timedelta,
        refresh_token_ttl: timedelta,
    ) -> None:
        self._secret_key = secret_key.encode('utf-8')
        self._access_token_ttl = access_token_ttl
        self._refresh_token_ttl = refresh_token_ttl

    def issue_access_token(self, *, user_id: int, role: str, session_id: str) -> tuple[str, datetime]:
        return self._issue_token(
            token_type='access',
            user_id=user_id,
            role=role,
            session_id=session_id,
            ttl=self._access_token_ttl,
        )

    def issue_refresh_token(self, *, user_id: int, role: str, session_id: str) -> tuple[str, str, datetime]:
        refresh_jti = self.new_id()
        token, expires_at = self._issue_token(
            token_type='refresh',
            user_id=user_id,
            role=role,
            session_id=session_id,
            ttl=self._refresh_token_ttl,
            jti=refresh_jti,
        )
        return token, refresh_jti, expires_at

    @staticmethod
    def new_id() -> str:
        return uuid4().hex

    @staticmethod
    def hash_token(token: str) -> str:
        return hashlib.sha256(token.encode('utf-8')).hexdigest()

    def decode_token(self, token: str, *, expected_type: str) -> dict[str, Any]:
        try:
            encoded_header, encoded_payload, encoded_signature = token.split('.')
        except ValueError as error:
            raise AuthenticationRequiredError('Invalid or expired token.') from error

        signing_input = f'{encoded_header}.{encoded_payload}'.encode('utf-8')
        expected_signature = self._sign(signing_input)
        try:
            actual_signature = self._decode_part(encoded_signature)
        except ValueError as error:
            raise AuthenticationRequiredError('Invalid or expired token.') from error

        if not hmac.compare_digest(expected_signature, actual_signature):
            raise AuthenticationRequiredError('Invalid or expired token.')

        header = self._load_json_part(encoded_header)
        payload = self._load_json_part(encoded_payload)

        if header.get('alg') != 'HS256' or header.get('typ') != 'JWT':
            raise AuthenticationRequiredError('Invalid or expired token.')
        if payload.get('type') != expected_type:
            raise AuthenticationRequiredError('Invalid or expired token.')

        exp = payload.get('exp')
        if not isinstance(exp, int):
            raise AuthenticationRequiredError('Invalid or expired token.')
        if exp <= int(datetime.now(timezone.utc).timestamp()):
            raise AuthenticationRequiredError('Invalid or expired token.')

        return payload

    def _issue_token(
        self,
        *,
        token_type: str,
        user_id: int,
        role: str,
        session_id: str,
        ttl: timedelta,
        jti: str | None = None,
    ) -> tuple[str, datetime]:
        now = datetime.now(timezone.utc)
        expires_at = now + ttl
        payload = {
            'sub': str(user_id),
            'role': role,
            'type': token_type,
            'jti': jti or self.new_id(),
            'session_id': session_id,
            'iat': int(now.timestamp()),
            'exp': int(expires_at.timestamp()),
        }
        header = {'alg': 'HS256', 'typ': 'JWT'}

        encoded_header = self._encode_json_part(header)
        encoded_payload = self._encode_json_part(payload)
        signing_input = f'{encoded_header}.{encoded_payload}'.encode('utf-8')
        encoded_signature = self._encode_part(self._sign(signing_input))
        return f'{encoded_header}.{encoded_payload}.{encoded_signature}', expires_at

    def _sign(self, payload: bytes) -> bytes:
        return hmac.new(self._secret_key, payload, hashlib.sha256).digest()

    @staticmethod
    def _encode_json_part(value: dict[str, Any]) -> str:
        return TokenService._encode_part(json.dumps(value, separators=(',', ':'), sort_keys=True).encode('utf-8'))

    @staticmethod
    def _load_json_part(value: str) -> dict[str, Any]:
        try:
            raw = TokenService._decode_part(value)
            data = json.loads(raw.decode('utf-8'))
        except (ValueError, json.JSONDecodeError, UnicodeDecodeError) as error:
            raise AuthenticationRequiredError('Invalid or expired token.') from error

        if not isinstance(data, dict):
            raise AuthenticationRequiredError('Invalid or expired token.')
        return data

    @staticmethod
    def _encode_part(value: bytes) -> str:
        return base64.urlsafe_b64encode(value).rstrip(b'=').decode('ascii')

    @staticmethod
    def _decode_part(value: str) -> bytes:
        padding = '=' * (-len(value) % 4)
        return base64.urlsafe_b64decode(f'{value}{padding}')
