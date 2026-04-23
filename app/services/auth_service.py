from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
import hmac

from sqlalchemy.orm import Session

from app.models import Reader, RefreshTokenSession
from app.repositories.reader_repository import ReaderRepository
from app.repositories.refresh_token_repository import RefreshTokenRepository
from app.services.exceptions import AuthenticationRequiredError, ValidationError
from app.services.token_service import TokenPair, TokenService


@dataclass(slots=True)
class ApiActor:
    id: int
    role: str
    is_authenticated: bool = True
    session_id: str | None = None


@dataclass(slots=True)
class AnonymousApiActor:
    id: int | None = None
    role: str | None = None
    is_authenticated: bool = False
    session_id: str | None = None


@dataclass(slots=True)
class IssuedTokenSession:
    session: RefreshTokenSession
    refresh_token: str
    refresh_expires_at: datetime


class AuthService:
    def __init__(
        self,
        session: Session,
        readers: ReaderRepository,
        refresh_tokens: RefreshTokenRepository,
        token_service: TokenService,
    ) -> None:
        self._session = session
        self._readers = readers
        self._refresh_tokens = refresh_tokens
        self._token_service = token_service

    def actor_from_reader(self, reader: Reader) -> ApiActor:
        return ApiActor(id=reader.id, role=reader.role, session_id=None)

    def login(
        self,
        *,
        email: object,
        password: object,
        user_agent: str | None = None,
        ip_address: str | None = None,
    ) -> tuple[Reader, TokenPair]:
        normalized_email = str(email).strip()
        normalized_password = str(password)

        if not normalized_email:
            raise ValidationError('Validation failed.', details={'email': 'Email is required.'})
        if not normalized_password:
            raise ValidationError('Validation failed.', details={'password': 'Password is required.'})

        reader = self._readers.get_by_email(normalized_email)
        if reader is None or not reader.check_password(normalized_password):
            raise AuthenticationRequiredError('Invalid email or password.')

        issued_session = self._new_token_session(reader, user_agent=user_agent, ip_address=ip_address)
        self._refresh_tokens.add(issued_session.session)
        tokens = self._issue_tokens(reader, issued_session)
        self._session.commit()
        return reader, tokens

    def refresh(
        self,
        *,
        refresh_token: object,
        user_agent: str | None = None,
        ip_address: str | None = None,
    ) -> tuple[Reader, TokenPair]:
        token_value = str(refresh_token).strip()
        if not token_value:
            raise ValidationError('Validation failed.', details={'refresh_token': 'Refresh token is required.'})

        payload = self._token_service.decode_token(token_value, expected_type='refresh')
        session_id = self._claim_str(payload, 'session_id')
        refresh_jti = self._claim_str(payload, 'jti')
        reader = self._require_reader(payload)
        token_session = self._require_active_session(session_id)
        if token_session.user_id != reader.id:
            raise AuthenticationRequiredError('Authentication required.')

        if token_session.refresh_jti != refresh_jti:
            token_session.revoked_at = datetime.utcnow()
            self._session.commit()
            raise AuthenticationRequiredError('Refresh token has been revoked.')

        token_hash = self._token_service.hash_token(token_value)
        if not hmac.compare_digest(token_session.token_hash, token_hash):
            token_session.revoked_at = datetime.utcnow()
            self._session.commit()
            raise AuthenticationRequiredError('Refresh token has been revoked.')

        new_refresh_token, new_refresh_jti, refresh_expires_at = self._token_service.issue_refresh_token(
            user_id=reader.id,
            role=reader.role,
            session_id=token_session.session_id,
        )
        access_token, access_expires_at = self._token_service.issue_access_token(
            user_id=reader.id,
            role=reader.role,
            session_id=token_session.session_id,
        )

        token_session.refresh_jti = new_refresh_jti
        token_session.token_hash = self._token_service.hash_token(new_refresh_token)
        token_session.expires_at = refresh_expires_at.replace(tzinfo=None)
        token_session.last_used_at = datetime.utcnow()
        token_session.user_agent = user_agent
        token_session.ip_address = ip_address
        self._session.commit()

        return reader, TokenPair(
            access_token=access_token,
            refresh_token=new_refresh_token,
            access_expires_at=access_expires_at,
            refresh_expires_at=refresh_expires_at,
        )

    def authenticate_access_token(self, token: str) -> ApiActor:
        payload = self._token_service.decode_token(token, expected_type='access')
        session_id = self._claim_str(payload, 'session_id')
        token_session = self._require_active_session(session_id)
        reader = self._require_reader(payload)
        if token_session.user_id != reader.id:
            raise AuthenticationRequiredError('Authentication required.')
        return ApiActor(id=reader.id, role=reader.role, session_id=token_session.session_id)

    def revoke_session(self, session_id: str) -> None:
        token_session = self._require_active_session(session_id)
        token_session.revoked_at = datetime.utcnow()
        self._session.commit()

    def get_reader_for_actor(self, actor: ApiActor) -> Reader:
        reader = self._readers.get_by_id(actor.id)
        if reader is None:
            raise AuthenticationRequiredError('Authentication required.')
        return reader

    def _new_token_session(
        self,
        reader: Reader,
        *,
        user_agent: str | None = None,
        ip_address: str | None = None,
    ) -> IssuedTokenSession:
        session_id = self._token_service.new_id()
        refresh_token, refresh_jti, refresh_expires_at = self._token_service.issue_refresh_token(
            user_id=reader.id,
            role=reader.role,
            session_id=session_id,
        )
        token_session = RefreshTokenSession(
            user_id=reader.id,
            session_id=session_id,
            refresh_jti=refresh_jti,
            token_hash=self._token_service.hash_token(refresh_token),
            expires_at=refresh_expires_at.replace(tzinfo=None),
            user_agent=user_agent,
            ip_address=ip_address,
        )
        return IssuedTokenSession(
            session=token_session,
            refresh_token=refresh_token,
            refresh_expires_at=refresh_expires_at,
        )

    def _issue_tokens(self, reader: Reader, issued_session: IssuedTokenSession) -> TokenPair:
        access_token, access_expires_at = self._token_service.issue_access_token(
            user_id=reader.id,
            role=reader.role,
            session_id=issued_session.session.session_id,
        )
        return TokenPair(
            access_token=access_token,
            refresh_token=issued_session.refresh_token,
            access_expires_at=access_expires_at,
            refresh_expires_at=issued_session.refresh_expires_at,
        )

    def _require_active_session(self, session_id: str) -> RefreshTokenSession:
        token_session = self._refresh_tokens.get_by_session_id(session_id)
        if token_session is None:
            raise AuthenticationRequiredError('Authentication required.')
        if token_session.revoked_at is not None:
            raise AuthenticationRequiredError('Authentication required.')
        if token_session.expires_at <= datetime.utcnow():
            raise AuthenticationRequiredError('Authentication required.')
        return token_session

    def _require_reader(self, payload: dict[str, object]) -> Reader:
        user_id = self._claim_int(payload, 'sub')
        reader = self._readers.get_by_id(user_id)
        if reader is None:
            raise AuthenticationRequiredError('Authentication required.')
        return reader

    @staticmethod
    def _claim_str(payload: dict[str, object], key: str) -> str:
        value = payload.get(key)
        if not isinstance(value, str) or not value:
            raise AuthenticationRequiredError('Authentication required.')
        return value

    @staticmethod
    def _claim_int(payload: dict[str, object], key: str) -> int:
        value = payload.get(key)
        if isinstance(value, int):
            return value
        if isinstance(value, str) and value.isdigit():
            return int(value)
        raise AuthenticationRequiredError('Authentication required.')
