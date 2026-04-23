from sqlalchemy import select

from app.extensions import db
from app.models import Book, Reader, Review


def login(client, email='test.user@example.com', password='Secret123!'):
    return client.post(
        '/login',
        data={'email': email, 'password': password},
        follow_redirects=False,
    )


def api_login(client, email='test.user@example.com', password='Secret123!'):
    response = client.post(
        '/api/v1/auth/login',
        json={'email': email, 'password': password},
        follow_redirects=False,
    )
    assert response.status_code == 200
    return response.get_json()


def api_headers(access_token: str) -> dict[str, str]:
    return {'Authorization': f'Bearer {access_token}'}


def test_api_books_collection_sets_cache_headers_and_etag(client, app, user):
    tokens = api_login(client)

    with app.app_context():
        db.session.add(Book(title='Cache Me', author_name='A', author_surname='B', month='January', year=2024))
        db.session.commit()

    response = client.get(
        '/api/v1/books?search=Cache&page=1&per_page=10',
        headers=api_headers(tokens['access_token']),
        follow_redirects=False,
    )

    assert response.status_code == 200
    assert response.headers.get('Cache-Control') == 'private, max-age=60'
    assert response.headers.get('ETag')


def test_api_books_collection_returns_304_for_matching_if_none_match(client, app, user):
    tokens = api_login(client)

    with app.app_context():
        db.session.add(Book(title='ETag Book', author_name='A', author_surname='B', month='February', year=2024))
        db.session.commit()

    first = client.get(
        '/api/v1/books?search=ETag&page=1&per_page=10',
        headers=api_headers(tokens['access_token']),
        follow_redirects=False,
    )
    etag = first.headers.get('ETag')

    second = client.get(
        '/api/v1/books?search=ETag&page=1&per_page=10',
        headers={'Authorization': f"Bearer {tokens['access_token']}", 'If-None-Match': etag},
        follow_redirects=False,
    )

    assert second.status_code == 304
    assert not second.data


def test_api_books_collection_uses_server_side_cache_until_invalidation(client, app, user):
    tokens = api_login(client)

    with app.app_context():
        db.session.add(Book(title='Server Cache Book', author_name='A', author_surname='B', month='March', year=2024))
        db.session.commit()

    first = client.get(
        '/api/v1/books?search=Server&page=1&per_page=10',
        headers=api_headers(tokens['access_token']),
        follow_redirects=False,
    )
    assert first.status_code == 200
    assert first.get_json()['pagination']['total'] == 1

    with app.app_context():
        db.session.add(Book(title='Server Cache Book 2', author_name='A', author_surname='B', month='March', year=2024))
        db.session.commit()

    second = client.get(
        '/api/v1/books?search=Server&page=1&per_page=10',
        headers=api_headers(tokens['access_token']),
        follow_redirects=False,
    )
    assert second.status_code == 200
    assert second.get_json()['pagination']['total'] == 1


def test_api_mutation_invalidates_book_details_cache(client, app, user, librarian):
    tokens = api_login(client, email=librarian)

    with app.app_context():
        reader = db.session.scalar(select(Reader).filter_by(email=user))
        book = Book(title='Invalidate Book', author_name='I', author_surname='N', month='April', year=2024)
        db.session.add(book)
        db.session.commit()
        review = Review(text='Old', stars=3, book_id=book.id, reviewer_id=reader.id)
        db.session.add(review)
        db.session.commit()
        review_id = review.id
        book_id = book.id

    before = client.get(
        f'/api/v1/books/{book_id}',
        headers=api_headers(tokens['access_token']),
        follow_redirects=False,
    )
    assert before.status_code == 200
    assert before.get_json()['reviews'][0]['text'] == 'Old'

    patch_response = client.patch(
        f'/api/v1/reviews/{review_id}',
        headers=api_headers(tokens['access_token']),
        json={'text': 'Updated from cache invalidation test'},
        follow_redirects=False,
    )
    assert patch_response.status_code == 200

    after = client.get(
        f'/api/v1/books/{book_id}',
        headers=api_headers(tokens['access_token']),
        follow_redirects=False,
    )
    assert after.status_code == 200
    assert after.get_json()['reviews'][0]['text'] == 'Updated from cache invalidation test'
    assert after.headers.get('ETag') != before.headers.get('ETag')
