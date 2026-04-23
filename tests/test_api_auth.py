from sqlalchemy import select

from app.extensions import db
from app.models import Book, Reader, Review


def _bearer_headers(access_token: str) -> dict[str, str]:
    return {'Authorization': f'Bearer {access_token}'}


def _api_login(client, *, email: str, password: str = 'Secret123!') -> dict[str, object]:
    response = client.post(
        '/api/v1/auth/login',
        json={'email': email, 'password': password},
        follow_redirects=False,
    )
    assert response.status_code == 200
    return response.get_json()


def test_api_auth_login_returns_access_and_refresh_tokens(client, user):
    response = client.post(
        '/api/v1/auth/login',
        json={'email': user, 'password': 'Secret123!'},
        follow_redirects=False,
    )

    assert response.status_code == 200
    assert response.is_json

    payload = response.get_json()
    assert payload['token_type'] == 'Bearer'
    assert payload['access_token']
    assert payload['refresh_token']
    assert payload['access_expires_at']
    assert payload['refresh_expires_at']
    assert payload['reader']['email'] == user


def test_api_auth_login_rejects_invalid_credentials(client, user):
    response = client.post(
        '/api/v1/auth/login',
        json={'email': user, 'password': 'wrong-password'},
        follow_redirects=False,
    )

    assert response.status_code == 401
    assert response.is_json
    assert response.get_json()['error']['message'] == 'Invalid email or password.'


def test_api_auth_me_returns_current_reader_for_bearer_token(client, user):
    tokens = _api_login(client, email=user)

    response = client.get(
        '/api/v1/auth/me',
        headers=_bearer_headers(tokens['access_token']),
        follow_redirects=False,
    )

    assert response.status_code == 200
    assert response.is_json
    assert response.get_json()['email'] == user


def test_api_auth_refresh_rotates_refresh_token(client, user):
    tokens = _api_login(client, email=user)

    response = client.post(
        '/api/v1/auth/refresh',
        json={'refresh_token': tokens['refresh_token']},
        follow_redirects=False,
    )

    assert response.status_code == 200
    assert response.is_json

    refreshed = response.get_json()
    assert refreshed['access_token'] != tokens['access_token']
    assert refreshed['refresh_token'] != tokens['refresh_token']
    assert refreshed['reader']['email'] == user


def test_api_auth_refresh_token_reuse_revokes_session(client, user):
    tokens = _api_login(client, email=user)
    refreshed = client.post(
        '/api/v1/auth/refresh',
        json={'refresh_token': tokens['refresh_token']},
        follow_redirects=False,
    ).get_json()

    reuse_response = client.post(
        '/api/v1/auth/refresh',
        json={'refresh_token': tokens['refresh_token']},
        follow_redirects=False,
    )

    assert reuse_response.status_code == 401
    assert reuse_response.is_json
    assert reuse_response.get_json()['error']['message'] == 'Refresh token has been revoked.'

    me_response = client.get(
        '/api/v1/auth/me',
        headers=_bearer_headers(refreshed['access_token']),
        follow_redirects=False,
    )
    assert me_response.status_code == 401


def test_api_auth_logout_revokes_access_and_refresh_tokens(client, user):
    tokens = _api_login(client, email=user)

    logout_response = client.post(
        '/api/v1/auth/logout',
        headers=_bearer_headers(tokens['access_token']),
        follow_redirects=False,
    )

    assert logout_response.status_code == 204

    me_response = client.get(
        '/api/v1/auth/me',
        headers=_bearer_headers(tokens['access_token']),
        follow_redirects=False,
    )
    assert me_response.status_code == 401

    refresh_response = client.post(
        '/api/v1/auth/refresh',
        json={'refresh_token': tokens['refresh_token']},
        follow_redirects=False,
    )
    assert refresh_response.status_code == 401


def test_api_bearer_token_can_create_review_without_session_login(client, app, user):
    tokens = _api_login(client, email=user)

    with app.app_context():
        book = Book(title='Bearer Review Book', author_name='B', author_surname='R', month='April', year=2026)
        db.session.add(book)
        db.session.commit()
        book_id = book.id

    response = client.post(
        f'/api/v1/books/{book_id}/reviews',
        headers=_bearer_headers(tokens['access_token']),
        json={'text': 'Created via bearer token', 'stars': 5},
        follow_redirects=False,
    )

    assert response.status_code == 201
    assert response.is_json
    assert response.get_json()['text'] == 'Created via bearer token'

    with app.app_context():
        reader = db.session.scalar(select(Reader).filter_by(email=user))
        stored = db.session.scalar(
            select(Review).filter_by(book_id=book_id, reviewer_id=reader.id, text='Created via bearer token')
        )
        assert stored is not None
