from app.extensions import db
from app.models import Book, Review

def login(client, email='test.user@example.com', password='Secret123!'):
    return client.post(
        '/login',
        data={'email': email, 'password': password},
        follow_redirects=False,
    )


def ensure_guest(client):
    client.get('/logout', follow_redirects=False)

    with client.session_transaction() as session:
        session.clear()

    # Clear remember/session cookies across Flask/Werkzeug client versions.
    if hasattr(client, 'cookie_jar'):
        client.cookie_jar.clear()
        return

    cookie_store = getattr(client, '_cookies', None)
    if cookie_store is not None:
        cookie_store.clear()


def test_root_redirects_guest_to_login(client):
    ensure_guest(client)
    response = client.get('/', follow_redirects=False)

    assert response.status_code == 302
    #assert '/login' in response.headers['Location'], f"Expected /login redirect for guest, got {response.headers.get('Location')}"


def test_root_redirects_authenticated_user_to_home(client, user):
    login_response = login(client)
    assert login_response.status_code == 302

    response = client.get('/', follow_redirects=False)

    assert response.status_code == 302
    assert '/home' in response.headers['Location']



def test_logout_requires_authentication(client):
    ensure_guest(client)
    response = client.get('/logout', follow_redirects=False)

    assert response.status_code == 302
    assert '/login' in response.headers['Location']


def test_logout_redirects_to_login_after_authentication(client, user):
    login_response = login(client)
    assert login_response.status_code == 302

    response = client.get('/logout', follow_redirects=False)

    assert response.status_code == 302
    assert '/login' in response.headers['Location']


def test_book_route_returns_404_for_missing_book(client):
    response = client.get('/book/999999', follow_redirects=False)

    assert response.status_code == 404


def test_profile_route_returns_404_for_missing_user(client):
    response = client.get('/profile/999999', follow_redirects=False)

    assert response.status_code == 404


def test_reviews_route_returns_404_for_missing_review(client):
    response = client.get('/reviews/999999', follow_redirects=False)

    assert response.status_code == 404


def test_book_route_can_create_review_for_authenticated_user(client, user, app):
    login_response = login(client)
    assert login_response.status_code == 302

    with app.app_context():
        book = Book(
            title='Reviewable Book',
            author_name='Dana',
            author_surname='K',
            month='July',
            year=2024,
        )
        db.session.add(book)
        db.session.commit()
        book_id = book.id

    response = client.post(
        f'/book/{book_id}',
        data={'text': 'My fresh review', 'stars': 4},
        follow_redirects=True,
    )

    assert response.status_code == 200
    assert b'My fresh review' in response.data

    with app.app_context():
        stored = Review.query.filter_by(book_id=book_id, text='My fresh review').first()
        assert stored is not None
        assert stored.stars == 4


def test_book_route_redirects_guest_when_posting_review(client, app):
    ensure_guest(client)

    with app.app_context():
        book = Book(
            title='Guests Cannot Review',
            author_name='Pavlo',
            author_surname='L',
            month='August',
            year=2024,
        )
        db.session.add(book)
        db.session.commit()
        book_id = book.id

    response = client.post(f'/book/{book_id}', data={'text': 'Guest review', 'stars': 3}, follow_redirects=False)

    assert response.status_code == 302
    assert '/login' in response.headers['Location']

    with app.app_context():
        assert Review.query.filter_by(book_id=book_id, text='Guest review').first() is None


def test_book_route_does_not_create_review_for_invalid_stars(client, user, app):
    login_response = login(client)
    assert login_response.status_code == 302

    with app.app_context():
        book = Book(
            title='Invalid Stars Book',
            author_name='Nadiia',
            author_surname='M',
            month='September',
            year=2024,
        )
        db.session.add(book)
        db.session.commit()
        book_id = book.id

    response = client.post(
        f'/book/{book_id}',
        data={'text': 'Should not persist', 'stars': 9},
        follow_redirects=True,
    )

    assert response.status_code == 200

    with app.app_context():
        stored = Review.query.filter_by(book_id=book_id, text='Should not persist').first()
        assert stored is None
