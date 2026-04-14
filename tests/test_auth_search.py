from sqlalchemy import select

from app.extensions import db
from app.models import Book, Reader


def login(client, email='test.user@example.com', password='Secret123!'):
    return client.post(
        '/login',
        data={'email': email, 'password': password},
        follow_redirects=False,
    )

def home_search(client, query):
    # use current search query parameter
    return client.get(f'/home?search={query}', follow_redirects=True)


def ensure_guest(client):
    client.get('/logout', follow_redirects=False)

    with client.session_transaction() as session:
        session.clear()

    if hasattr(client, 'cookie_jar'):
        client.cookie_jar.clear()
        return

    cookie_store = getattr(client, '_cookies', None)
    if cookie_store is not None:
        cookie_store.clear()


def test_login_with_invalid_password_shows_flash(client, user):
    ensure_guest(client)

    response = client.post(
        '/login',
        data={'email': 'test.user@example.com', 'password': 'wrong-pass'},
        follow_redirects=True,
    )

    assert response.status_code == 200
    assert b'Invalid email or password.' in response.data


def test_authenticated_user_is_redirected_from_login(client, user):
    login_response = login(client)
    assert login_response.status_code == 302

    response = client.get('/login', follow_redirects=False)

    assert response.status_code == 302
    assert '/home' in response.headers['Location']


def test_register_creates_user_and_redirects_to_home(client, app):
    response = client.post(
        '/register',
        data={
            'name': 'New',
            'surname': 'Reader',
            'email': 'new.reader@example.com',
            'role': 'reader',
            'password': 'StrongPass123!',
            'password2': 'StrongPass123!',
        },
        follow_redirects=False,
    )

    assert response.status_code == 302
    assert '/home' in response.headers['Location']

    with app.app_context():
        created = db.session.scalar(select(Reader).filter_by(email='new.reader@example.com'))
        assert created is not None
        assert created.role == 'reader'


def test_register_duplicate_email_shows_error(client, user):
    response = client.post(
        '/register',
        data={
            'name': 'Dup',
            'surname': 'User',
            'email': 'test.user@example.com',
            'role': 'reader',
            'password': 'StrongPass123!',
            'password2': 'StrongPass123!',
        },
        follow_redirects=True,
    )

    assert response.status_code == 200
    assert b'Email already registered.' in response.data


def test_home_search_single_term_filters_results(client, user, books):
    login(client)

    response = home_search(client, 'Gamma')

    assert response.status_code == 200
    assert b'Gamma Notes' in response.data
    assert b'Alpha Book' not in response.data


def test_home_search_multiple_terms_matches_across_fields(client, user, app):
    with app.app_context():
        db.session.add_all(
            [
                Book(
                    title='Space Journal',
                    author_name='Lina',
                    author_surname='Moroz',
                    month='April',
                    year=2021,
                ),
                Book(
                    title='Space Adventures',
                    author_name='Ira',
                    author_surname='Shevchenko',
                    month='May',
                    year=2020,
                ),
            ]
        )
        db.session.commit()

    login(client)
    response = home_search(client, 'Space%20Moroz')

    assert response.status_code == 200
    assert b'Space Journal' in response.data
    assert b'Space Adventures' not in response.data


def test_home_pagination_limits_to_10_per_page(client, user, app):
    with app.app_context():
        db.session.add_all(
            [
                Book(
                    title=f'Paginated Book {i:02d}',
                    author_name='Author',
                    author_surname='Load',
                    month='January',
                    year=2024,
                )
                for i in range(1, 13)
            ]
        )
        db.session.commit()

    login(client)

    page_1 = client.get('/home?page=1', follow_redirects=True)
    page_2 = client.get('/home?page=2', follow_redirects=True)

    assert page_1.status_code == 200
    assert page_2.status_code == 200

    assert b'Paginated Book 01' in page_1.data
    assert b'Paginated Book 10' in page_1.data
    assert b'Paginated Book 11' not in page_1.data

    assert b'Paginated Book 11' in page_2.data
    assert b'Paginated Book 12' in page_2.data


def test_home_hides_hidden_books_for_reader(client, user, app):
    with app.app_context():
        db.session.add_all(
            [
                Book(
                    title='Visible Shelf Book',
                    author_name='A',
                    author_surname='B',
                    month='January',
                    year=2024,
                    is_hidden=False,
                ),
                Book(
                    title='Hidden Shelf Book',
                    author_name='A',
                    author_surname='B',
                    month='January',
                    year=2024,
                    is_hidden=True,
                ),
            ]
        )
        db.session.commit()

    login(client)
    response = client.get('/home', follow_redirects=True)

    assert response.status_code == 200
    assert b'Visible Shelf Book' in response.data
    assert b'Hidden Shelf Book' not in response.data


def test_home_search_hides_hidden_books_for_reader(client, user, app):
    with app.app_context():
        db.session.add_all(
            [
                Book(
                    title='Unique Visible Result',
                    author_name='A',
                    author_surname='B',
                    month='January',
                    year=2024,
                    is_hidden=False,
                ),
                Book(
                    title='Unique Hidden Result',
                    author_name='A',
                    author_surname='B',
                    month='January',
                    year=2024,
                    is_hidden=True,
                ),
            ]
        )
        db.session.commit()

    login(client)
    response = home_search(client, 'Unique')

    assert response.status_code == 200
    assert b'Unique Visible Result' in response.data
    assert b'Unique Hidden Result' not in response.data
