from sqlalchemy import select

from app.extensions import db
from app.models import Annotation, Book, Reader, Review

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


def test_protected_pages_send_no_store_cache_headers(client, user, app):
    login_response = login(client)
    assert login_response.status_code == 302

    with app.app_context():
        book = Book(
            title='No Cache Book',
            author_name='Ira',
            author_surname='N',
            month='November',
            year=2024,
        )
        db.session.add(book)
        db.session.commit()
        book_id = book.id

    response = client.get(f'/book/{book_id}', follow_redirects=False)

    assert response.status_code == 200
    assert response.headers['Cache-Control'] == 'no-store, no-cache, must-revalidate, max-age=0'
    assert response.headers['Pragma'] == 'no-cache'
    assert response.headers['Expires'] == '0'




def test_public_login_page_is_not_marked_no_store(client):
    ensure_guest(client)

    response = client.get('/login', follow_redirects=False)

    assert response.status_code == 200
    assert response.headers.get('Cache-Control') != 'no-store, no-cache, must-revalidate, max-age=0'

def test_book_route_redirects_guest_for_missing_book(client):
    response = client.get('/book/999999', follow_redirects=False)

    assert response.status_code == 302
    assert '/login' in response.headers['Location']


def test_profile_route_redirects_guest_for_missing_user(client):
    response = client.get('/profile/999999', follow_redirects=False)

    assert response.status_code == 302
    assert '/login' in response.headers['Location']


def test_reviews_route_redirects_guest_for_missing_review(client):
    response = client.get('/reviews/999999', follow_redirects=False)

    assert response.status_code == 302
    assert '/login' in response.headers['Location']


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
        data={'review-text': 'My fresh review', 'review-stars': 4, 'review-submit': '1'},
        follow_redirects=True,
    )

    assert response.status_code == 200
    assert b'My fresh review' in response.data
    assert b'review-stars' in response.data
    assert b'Stars:' not in response.data

    with app.app_context():
        stored = db.session.scalar(select(Review).filter_by(book_id=book_id, text='My fresh review'))
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

    response = client.post(
        f'/book/{book_id}',
        data={'review-text': 'Guest review', 'review-stars': 3, 'review-submit': '1'},
        follow_redirects=False,
    )

    assert response.status_code == 302
    assert '/login' in response.headers['Location']

    with app.app_context():
        assert db.session.scalar(select(Review).filter_by(book_id=book_id, text='Guest review')) is None


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
        data={'review-text': 'Should not persist', 'review-stars': 9, 'review-submit': '1'},
        follow_redirects=True,
    )

    assert response.status_code == 200

    with app.app_context():
        stored = db.session.scalar(select(Review).filter_by(book_id=book_id, text='Should not persist'))
        assert stored is None



def test_book_route_can_create_annotation_for_librarian(client, librarian, app):
    ensure_guest(client)
    login_response = login(client, email=librarian)
    assert login_response.status_code == 302

    with app.app_context():
        book = Book(
            title='Annotatable Book',
            author_name='Lena',
            author_surname='P',
            month='October',
            year=2024,
        )
        db.session.add(book)
        db.session.commit()
        book_id = book.id

    response = client.post(
        f'/book/{book_id}',
        data={'annotation-text': 'A compact and useful annotation', 'annotation-submit': '1'},
        follow_redirects=True,
    )

    assert response.status_code == 200
    assert b'Add your annotation' in response.data

    with app.app_context():
        stored = db.session.scalar(select(Annotation).filter_by(book_id=book_id, text='A compact and useful annotation'))
        assert stored is not None



def test_book_route_reader_cannot_annotate_and_does_not_see_annotation_form(client, user, app):
    ensure_guest(client)
    login_response = login(client)
    assert login_response.status_code == 302

    with app.app_context():
        book = Book(
            title='Reader Cannot Annotate',
            author_name='Lena',
            author_surname='P',
            month='October',
            year=2024,
        )
        db.session.add(book)
        db.session.commit()
        book_id = book.id

    page_response = client.get(f'/book/{book_id}', follow_redirects=True)
    assert page_response.status_code == 200
    assert b'Add your annotation' not in page_response.data

    post_response = client.post(
        f'/book/{book_id}',
        data={'annotation-text': 'Reader annotation attempt', 'annotation-submit': '1'},
        follow_redirects=False,
    )

    assert post_response.status_code == 302
    assert '/home' in post_response.headers['Location']

    with app.app_context():
        stored = db.session.scalar(select(Annotation).filter_by(book_id=book_id, text='Reader annotation attempt'))
        assert stored is None


def test_book_route_redirects_guest_when_posting_annotation(client, app):
    ensure_guest(client)

    with app.app_context():
        book = Book(
            title='Guests Cannot Annotate',
            author_name='Marta',
            author_surname='H',
            month='November',
            year=2024,
        )
        db.session.add(book)
        db.session.commit()
        book_id = book.id

    response = client.post(
        f'/book/{book_id}',
        data={'annotation-text': 'Guest note', 'annotation-submit': '1'},
        follow_redirects=False,
    )

    assert response.status_code == 302
    assert '/login' in response.headers['Location']

    with app.app_context():
        assert db.session.scalar(select(Annotation).filter_by(book_id=book_id, text='Guest note')) is None


def test_book_read_route_redirects_guest_for_missing_book(client):
    response = client.get('/book/999999/read', follow_redirects=False)

    assert response.status_code == 302
    assert '/login' in response.headers['Location']




def test_api_book_data_returns_json_payload(client, app, user):
    with app.app_context():
        reader = db.session.scalar(select(Reader).filter_by(email=user))
        book = Book(
            title='API Data Book',
            author_name='Ira',
            author_surname='B',
            month='January',
            year=2025,
            cover_image='book_covers/default.svg',
        )
        db.session.add(book)
        db.session.commit()

        review = Review(text='Useful API review', stars=5, book_id=book.id, reviewer_id=reader.id)
        annotation = Annotation(text='API annotation', book_id=book.id, reviewer_id=reader.id)
        db.session.add(review)
        db.session.add(annotation)
        db.session.commit()
        book_id = book.id

    response = client.get(f'/api/v1/books/{book_id}', follow_redirects=False)

    assert response.status_code == 200
    assert response.is_json

    payload = response.get_json()
    assert payload['id'] == book_id
    assert payload['title'] == 'API Data Book'
    assert payload['author_name'] == 'Ira'
    assert payload['author_surname'] == 'B'
    assert payload['month'] == 'January'
    assert payload['year'] == 2025
    assert payload['cover_image'] == 'book_covers/default.svg'
    assert len(payload['reviews']) == 1
    assert payload['reviews'][0]['text'] == 'Useful API review'
    assert payload['reviews'][0]['stars'] == 5
    assert len(payload['annotations']) == 1
    assert payload['annotations'][0]['text'] == 'API annotation'



def test_api_book_data_returns_404_for_missing_book(client):
    response = client.get('/api/v1/books/999999', follow_redirects=False)

    assert response.status_code == 404



def test_api_book_data_legacy_route_redirects(client, app):
    with app.app_context():
        book = Book(
            title='Legacy Data Route Book',
            author_name='Leo',
            author_surname='S',
            month='March',
            year=2025,
        )
        db.session.add(book)
        db.session.commit()
        book_id = book.id

    response = client.get(f'/api/v1/books/{book_id}/data', follow_redirects=False)

    assert response.status_code == 301
    assert response.headers['Location'].endswith(f'/api/v1/books/{book_id}')


def test_book_page_route_remains_html_after_rest_migration(client, app, user):
    with app.app_context():
        book = Book(
            title='HTML Book Page',
            author_name='Lia',
            author_surname='N',
            month='May',
            year=2025,
        )
        db.session.add(book)
        db.session.commit()
        book_id = book.id

    login_response = login(client)
    assert login_response.status_code == 302

    response = client.get(f'/book/{book_id}', follow_redirects=False)

    assert response.status_code == 200
    assert b'<html' in response.data
    assert b'HTML Book Page' in response.data


def test_book_read_route_shows_annotations_in_expected_order(client, app, user):
    login_response = login(client)
    assert login_response.status_code == 302

    with app.app_context():
        reader = db.session.scalar(select(Reader).filter_by(email=user))
        book = Book(
            title='Readable Book',
            author_name='Oksana',
            author_surname='R',
            month='December',
            year=2024,
        )
        db.session.add(book)
        db.session.commit()

        annotation = Annotation(text='Visible only on read page', reviewer_id=reader.id, book_id=book.id)
        db.session.add(annotation)
        db.session.commit()
        book_id = book.id

    response = client.get(f'/book/{book_id}/read', follow_redirects=True)

    assert response.status_code == 200
    assert b'Visible only on read page' in response.data
    assert b'Reading text has not been added for this book yet.' in response.data
    assert response.data.count(b'Back to book page') == 2
    assert response.data.count(b'Back to home') == 2

    assert 'Опис:'.encode('utf-8') not in response.data
    assert 'Текст книги'.encode('utf-8') not in response.data
    assert b'Contents' in response.data
    assert b'Reading contents have not been added for this book yet.' in response.data
    assert b'Readable Book' in response.data
    assert b'Oksana R' in response.data
    assert 'Обкладинка книги'.encode('utf-8') in response.data
    assert 'Анотації'.encode('utf-8') in response.data
    assert b'id="contents"' in response.data


def test_book_page_shows_read_now_button_and_hides_annotation_feed(client, app, user):
    login_response = login(client)
    assert login_response.status_code == 302

    with app.app_context():
        reader = db.session.scalar(select(Reader).filter_by(email=user))
        book = Book(
            title='Book Button Check',
            author_name='Iryna',
            author_surname='T',
            month='January',
            year=2025,
        )
        db.session.add(book)
        db.session.commit()

        annotation = Annotation(text='Hidden on details page', reviewer_id=reader.id, book_id=book.id)
        db.session.add(annotation)
        db.session.commit()
        book_id = book.id

    response = client.get(
        f'/book/{book_id}',
        headers={'Referer': '/home'},
        follow_redirects=True,
    )

    assert response.status_code == 200
    assert f'/book/{book_id}/read'.encode() in response.data
    assert b'Hidden on details page' not in response.data
    assert b'Book details' in response.data
    assert b'Back to home' in response.data
    assert b'href="/home"' in response.data



def test_seed_book_read_page_works(client, app, user):
    login_response = login(client)
    assert login_response.status_code == 302

    with app.app_context():
        book = Book(
            id=12,
            title='Seed-like Read Page',
            author_name='Olha',
            author_surname='Z',
            month='March',
            year=2026,
        )
        db.session.add(book)
        db.session.commit()

    response = client.get('/book/12/read', follow_redirects=True)

    assert response.status_code == 200
    assert 'Опис:'.encode('utf-8') not in response.data
    assert 'Обкладинка книги'.encode('utf-8') in response.data
    assert 'Анотації'.encode('utf-8') in response.data
    assert b'Contents' in response.data
    assert b'href="#ch1"' in response.data
    assert b'Chapter 1' in response.data
    assert b'Chapter 1 of Hundred Years of Solitude introduces the central situation and atmosphere.' in response.data
    assert b'id="contents"' in response.data
    assert 'Текст книги'.encode('utf-8') not in response.data


def test_book_read_uses_static_html_content_for_book_15(client, app, user):
    login_response = login(client)
    assert login_response.status_code == 302

    with app.app_context():
        book = db.session.get(Book, 15)
        if book is None:
            db.session.add(
                Book(
                    id=15,
                    title='Crime and Punishment',
                    author_name='Fyodor',
                    author_surname='Dostoevsky',
                    month='January',
                    year=2026,
                )
            )
            db.session.commit()

    response = client.get('/book/15/read', follow_redirects=True)

    assert response.status_code == 200
    assert b'Chapter 1' in response.data
    assert b'href="#ch1"' in response.data
    assert b'id="ch1"' in response.data
    assert b'Prototype excerpt for Crime and Punishment' in response.data
    assert b'Back to contents' in response.data


def test_api_books_collection_returns_paginated_items(client, app):
    with app.app_context():
        db.session.add_all(
            [
                Book(title='Api Alpha', author_name='A', author_surname='A', month='January', year=2024),
                Book(title='Api Beta', author_name='B', author_surname='B', month='February', year=2024),
                Book(title='Api Gamma', author_name='C', author_surname='C', month='March', year=2023),
            ]
        )
        db.session.commit()

    response = client.get('/api/v1/books?search=Api&page=1&per_page=2', follow_redirects=False)

    assert response.status_code == 200
    assert response.is_json
    payload = response.get_json()
    assert payload['search'] == 'Api'
    assert payload['pagination']['page'] == 1
    assert payload['pagination']['per_page'] == 2
    assert payload['pagination']['total'] == 3
    assert len(payload['items']) == 2



def test_api_reader_profile_returns_json(client, app, user):
    with app.app_context():
        reader = db.session.scalar(select(Reader).filter_by(email=user))
        reader_id = reader.id

    response = client.get(f'/api/v1/readers/{reader_id}', follow_redirects=False)

    assert response.status_code == 200
    assert response.is_json
    payload = response.get_json()
    assert payload['id'] == reader_id
    assert payload['email'] == user
    assert payload['role'] == 'reader'



def test_api_review_details_returns_json(client, app, user):
    with app.app_context():
        reader = db.session.scalar(select(Reader).filter_by(email=user))
        book = Book(title='Review API Book', author_name='R', author_surname='S', month='April', year=2024)
        db.session.add(book)
        db.session.commit()

        review = Review(text='Review API text', stars=4, book_id=book.id, reviewer_id=reader.id)
        db.session.add(review)
        db.session.commit()
        review_id = review.id

    response = client.get(f'/api/v1/reviews/{review_id}', follow_redirects=False)

    assert response.status_code == 200
    assert response.is_json
    payload = response.get_json()
    assert payload['id'] == review_id
    assert payload['text'] == 'Review API text'
    assert payload['stars'] == 4



def test_api_reader_profile_returns_404_for_missing_user(client):
    response = client.get('/api/v1/readers/999999', follow_redirects=False)

    assert response.status_code == 404



def test_api_review_details_returns_404_for_missing_review(client):
    response = client.get('/api/v1/reviews/999999', follow_redirects=False)

    assert response.status_code == 404


def test_api_review_patch_requires_authentication(client, app, user):
    ensure_guest(client)

    with app.app_context():
        reader = db.session.scalar(select(Reader).filter_by(email=user))
        book = Book(title='Patch Review Book', author_name='A', author_surname='B', month='May', year=2024)
        db.session.add(book)
        db.session.commit()
        review = Review(text='Old text', stars=3, book_id=book.id, reviewer_id=reader.id)
        db.session.add(review)
        db.session.commit()
        review_id = review.id

    response = client.patch(f'/api/v1/reviews/{review_id}', json={'text': 'New text'}, follow_redirects=False)

    assert response.status_code == 401
    assert response.is_json



def test_api_review_patch_returns_403_for_reader(client, app, user):
    with app.app_context():
        owner = db.session.scalar(select(Reader).filter_by(email=user))
        intruder = Reader(name='Intruder', surname='User', email='intruder@example.com', role='reader')
        intruder.set_password('Secret123!')
        db.session.add(intruder)

        book = Book(title='Forbidden Patch', author_name='C', author_surname='D', month='June', year=2024)
        db.session.add(book)
        db.session.commit()

        review = Review(text='Owner text', stars=2, book_id=book.id, reviewer_id=owner.id)
        db.session.add(review)
        db.session.commit()
        review_id = review.id

    ensure_guest(client)
    tokens = api_login(client, email='intruder@example.com', password='Secret123!')

    response = client.patch(
        f'/api/v1/reviews/{review_id}',
        headers=api_headers(tokens['access_token']),
        json={'text': 'Hacked'},
        follow_redirects=False,
    )

    assert response.status_code == 403
    assert response.get_json()['error']['message'] == 'Only librarians can update reviews.'



def test_api_review_patch_returns_422_for_invalid_data_librarian(client, app, user, librarian):
    ensure_guest(client)
    tokens = api_login(client, email=librarian, password='Secret123!')

    with app.app_context():
        reader = db.session.scalar(select(Reader).filter_by(email=user))
        book = Book(title='Invalid Patch', author_name='E', author_surname='F', month='July', year=2024)
        db.session.add(book)
        db.session.commit()
        review = Review(text='Valid text', stars=4, book_id=book.id, reviewer_id=reader.id)
        db.session.add(review)
        db.session.commit()
        review_id = review.id

    response = client.patch(
        f'/api/v1/reviews/{review_id}',
        headers=api_headers(tokens['access_token']),
        json={'stars': 9},
        follow_redirects=False,
    )

    assert response.status_code == 422
    assert response.is_json



def test_api_review_patch_updates_review_for_librarian(client, app, user, librarian):
    ensure_guest(client)
    tokens = api_login(client, email=librarian, password='Secret123!')

    with app.app_context():
        reader = db.session.scalar(select(Reader).filter_by(email=user))
        book = Book(title='Owned Patch', author_name='G', author_surname='H', month='August', year=2024)
        db.session.add(book)
        db.session.commit()
        review = Review(text='Before update', stars=2, book_id=book.id, reviewer_id=reader.id)
        db.session.add(review)
        db.session.commit()
        review_id = review.id

    response = client.patch(
        f'/api/v1/reviews/{review_id}',
        headers=api_headers(tokens['access_token']),
        json={'text': 'After update', 'stars': 5},
        follow_redirects=False,
    )

    assert response.status_code == 200
    payload = response.get_json()
    assert payload['text'] == 'After update'
    assert payload['stars'] == 5



def test_api_review_delete_requires_authentication(client, app, user):
    ensure_guest(client)

    with app.app_context():
        reader = db.session.scalar(select(Reader).filter_by(email=user))
        book = Book(title='Delete Review Book', author_name='I', author_surname='J', month='September', year=2024)
        db.session.add(book)
        db.session.commit()
        review = Review(text='Delete me', stars=3, book_id=book.id, reviewer_id=reader.id)
        db.session.add(review)
        db.session.commit()
        review_id = review.id

    response = client.delete(f'/api/v1/reviews/{review_id}', follow_redirects=False)

    assert response.status_code == 401



def test_api_review_delete_allows_reader_to_delete_own_review(client, app, user):
    ensure_guest(client)
    tokens = api_login(client, email=user, password='Secret123!')

    with app.app_context():
        reader = db.session.scalar(select(Reader).filter_by(email=user))
        book = Book(title='Owned Delete Review', author_name='K', author_surname='L', month='October', year=2024)
        db.session.add(book)
        db.session.commit()
        review = Review(text='Delete owned', stars=1, book_id=book.id, reviewer_id=reader.id)
        db.session.add(review)
        db.session.commit()
        review_id = review.id

    response = client.delete(
        f'/api/v1/reviews/{review_id}',
        headers=api_headers(tokens['access_token']),
        follow_redirects=False,
    )

    assert response.status_code == 204

    with app.app_context():
        assert db.session.scalar(select(Review).filter_by(id=review_id)) is None


def test_api_review_delete_allowed_for_librarian(client, app, user, librarian):
    ensure_guest(client)
    tokens = api_login(client, email=librarian, password='Secret123!')

    with app.app_context():
        owner = db.session.scalar(select(Reader).filter_by(email=user))
        book = Book(title='Librarian Delete Review', author_name='K', author_surname='L', month='October', year=2024)
        db.session.add(book)
        db.session.commit()
        review = Review(text='Delete as librarian', stars=1, book_id=book.id, reviewer_id=owner.id)
        db.session.add(review)
        db.session.commit()
        review_id = review.id

    response = client.delete(
        f'/api/v1/reviews/{review_id}',
        headers=api_headers(tokens['access_token']),
        follow_redirects=False,
    )

    assert response.status_code == 204

    with app.app_context():
        assert db.session.scalar(select(Review).filter_by(id=review_id)) is None



def test_api_annotation_patch_and_delete_for_reader(client, app, user):
    ensure_guest(client)
    tokens = api_login(client, email=user, password='Secret123!')

    with app.app_context():
        reader = db.session.scalar(select(Reader).filter_by(email=user))
        book = Book(title='Annotation Mutations', author_name='M', author_surname='N', month='November', year=2024)
        db.session.add(book)
        db.session.commit()
        annotation = Annotation(text='Before note', book_id=book.id, reviewer_id=reader.id)
        db.session.add(annotation)
        db.session.commit()
        annotation_id = annotation.id

    patch_response = client.patch(
        f'/api/v1/annotations/{annotation_id}',
        headers=api_headers(tokens['access_token']),
        json={'text': 'After note'},
        follow_redirects=False,
    )
    assert patch_response.status_code == 403
    assert patch_response.get_json()['error']['message'] == 'Only librarians can update annotations.'

    delete_response = client.delete(
        f'/api/v1/annotations/{annotation_id}',
        headers=api_headers(tokens['access_token']),
        follow_redirects=False,
    )
    assert delete_response.status_code == 403

    with app.app_context():
        assert db.session.scalar(select(Annotation).filter_by(id=annotation_id)) is not None



def test_api_annotation_patch_returns_401_403_422(client, app, user):
    with app.app_context():
        owner = db.session.scalar(select(Reader).filter_by(email=user))
        intruder = Reader(name='Another', surname='Intruder', email='another.intruder@example.com', role='reader')
        intruder.set_password('Secret123!')
        db.session.add(intruder)

        book = Book(title='Annotation Guard', author_name='O', author_surname='P', month='December', year=2024)
        db.session.add(book)
        db.session.commit()

        annotation = Annotation(text='Guarded', book_id=book.id, reviewer_id=owner.id)
        db.session.add(annotation)
        db.session.commit()
        annotation_id = annotation.id

    ensure_guest(client)
    unauth = client.patch(f'/api/v1/annotations/{annotation_id}', json={'text': 'x'}, follow_redirects=False)
    assert unauth.status_code == 401

    tokens = api_login(client, email='another.intruder@example.com', password='Secret123!')
    forbidden = client.patch(
        f'/api/v1/annotations/{annotation_id}',
        headers=api_headers(tokens['access_token']),
        json={'text': 'x'},
        follow_redirects=False,
    )
    assert forbidden.status_code == 403
    assert forbidden.get_json()['error']['message'] == 'Only librarians can update annotations.'

    ensure_guest(client)


def test_api_annotation_patch_returns_422_for_librarian(client, app, user, librarian):
    ensure_guest(client)
    tokens = api_login(client, email=librarian, password='Secret123!')

    with app.app_context():
        owner = db.session.scalar(select(Reader).filter_by(email=user))
        book = Book(title='Annotation Validation Librarian', author_name='O', author_surname='P', month='December', year=2024)
        db.session.add(book)
        db.session.commit()

        annotation = Annotation(text='Guarded', book_id=book.id, reviewer_id=owner.id)
        db.session.add(annotation)
        db.session.commit()
        annotation_id = annotation.id

    invalid = client.patch(
        f'/api/v1/annotations/{annotation_id}',
        headers=api_headers(tokens['access_token']),
        json={'text': ''},
        follow_redirects=False,
    )
    assert invalid.status_code == 422


def test_api_annotation_patch_updates_annotation_for_librarian(client, app, user, librarian):
    ensure_guest(client)
    tokens = api_login(client, email=librarian, password='Secret123!')

    with app.app_context():
        owner = db.session.scalar(select(Reader).filter_by(email=user))
        book = Book(title='Annotation Update Librarian', author_name='O', author_surname='P', month='December', year=2024)
        db.session.add(book)
        db.session.commit()

        annotation = Annotation(text='Before librarian edit', book_id=book.id, reviewer_id=owner.id)
        db.session.add(annotation)
        db.session.commit()
        annotation_id = annotation.id

    response = client.patch(
        f'/api/v1/annotations/{annotation_id}',
        headers=api_headers(tokens['access_token']),
        json={'text': 'After librarian edit'},
        follow_redirects=False,
    )
    assert response.status_code == 200
    assert response.get_json()['text'] == 'After librarian edit'



def test_api_annotation_delete_returns_404_for_missing_annotation(client, librarian):
    tokens = api_login(client, email=librarian, password='Secret123!')
    response = client.delete(
        '/api/v1/annotations/999999',
        headers=api_headers(tokens['access_token']),
        follow_redirects=False,
    )

    assert response.status_code == 404


def test_api_annotation_delete_allowed_for_librarian(client, app, user, librarian):
    ensure_guest(client)
    tokens = api_login(client, email=librarian, password='Secret123!')

    with app.app_context():
        owner = db.session.scalar(select(Reader).filter_by(email=user))
        book = Book(title='Librarian Delete Annotation', author_name='A', author_surname='B', month='Nov', year=2024)
        db.session.add(book)
        db.session.commit()
        annotation = Annotation(text='Delete note as librarian', book_id=book.id, reviewer_id=owner.id)
        db.session.add(annotation)
        db.session.commit()
        annotation_id = annotation.id

    response = client.delete(
        f'/api/v1/annotations/{annotation_id}',
        headers=api_headers(tokens['access_token']),
        follow_redirects=False,
    )
    assert response.status_code == 204

    with app.app_context():
        assert db.session.scalar(select(Annotation).filter_by(id=annotation_id)) is None


def test_api_book_404_uses_json_error_envelope(client):
    response = client.get('/api/v1/books/999999', follow_redirects=False)

    assert response.status_code == 404
    assert response.is_json
    payload = response.get_json()
    assert payload['error']['code'] == 404
    assert 'book' in payload['error']['message'].lower()



def test_api_reader_404_uses_json_error_envelope(client):
    response = client.get('/api/v1/readers/999999', follow_redirects=False)

    assert response.status_code == 404
    assert response.is_json
    payload = response.get_json()
    assert payload['error']['code'] == 404



def test_api_create_review_requires_authentication(client, app, user):
    ensure_guest(client)

    with app.app_context():
        book = Book(title='Create Review API', author_name='AA', author_surname='BB', month='Jan', year=2024)
        db.session.add(book)
        db.session.commit()
        book_id = book.id

    response = client.post(
        f'/api/v1/books/{book_id}/reviews',
        json={'text': 'Nice', 'stars': 5},
        follow_redirects=False,
    )

    assert response.status_code == 401
    assert response.is_json



def test_api_create_review_validation_and_success(client, app, user):
    ensure_guest(client)
    tokens = api_login(client, email=user, password='Secret123!')

    with app.app_context():
        reader = db.session.scalar(select(Reader).filter_by(email=user))
        book = Book(title='Create Review Success', author_name='CC', author_surname='DD', month='Feb', year=2024)
        db.session.add(book)
        db.session.commit()
        book_id = book.id
        reader_id = reader.id

    invalid = client.post(
        f'/api/v1/books/{book_id}/reviews',
        headers=api_headers(tokens['access_token']),
        json={'text': '', 'stars': 9},
        follow_redirects=False,
    )
    assert invalid.status_code == 422

    success = client.post(
        f'/api/v1/books/{book_id}/reviews',
        headers=api_headers(tokens['access_token']),
        json={'text': 'Created via API', 'stars': 4},
        follow_redirects=False,
    )
    assert success.status_code == 201
    payload = success.get_json()
    assert payload['text'] == 'Created via API'
    assert payload['stars'] == 4
    assert payload['reviewer_id'] == reader_id



def test_api_create_annotation_forbidden_for_reader(client, app, user):
    ensure_guest(client)
    tokens = api_login(client, email=user, password='Secret123!')

    with app.app_context():
        book = Book(title='Create Annotation Success', author_name='EE', author_surname='FF', month='Mar', year=2024)
        db.session.add(book)
        db.session.commit()
        book_id = book.id

    invalid = client.post(
        f'/api/v1/books/{book_id}/annotations',
        headers=api_headers(tokens['access_token']),
        json={'text': ''},
        follow_redirects=False,
    )
    assert invalid.status_code == 403

    success = client.post(
        f'/api/v1/books/{book_id}/annotations',
        headers=api_headers(tokens['access_token']),
        json={'text': 'Created annotation via API'},
        follow_redirects=False,
    )
    assert success.status_code == 403


def test_api_create_annotation_validation_and_success_for_librarian(client, app, librarian):
    ensure_guest(client)
    tokens = api_login(client, email=librarian, password='Secret123!')

    with app.app_context():
        reader = db.session.scalar(select(Reader).filter_by(email=librarian))
        book = Book(title='Create Annotation Success Librarian', author_name='EE', author_surname='FF', month='Mar', year=2024)
        db.session.add(book)
        db.session.commit()
        book_id = book.id
        reader_id = reader.id

    invalid = client.post(
        f'/api/v1/books/{book_id}/annotations',
        headers=api_headers(tokens['access_token']),
        json={'text': ''},
        follow_redirects=False,
    )
    assert invalid.status_code == 422

    success = client.post(
        f'/api/v1/books/{book_id}/annotations',
        headers=api_headers(tokens['access_token']),
        json={'text': 'Created annotation via API'},
        follow_redirects=False,
    )
    assert success.status_code == 201
    payload = success.get_json()
    assert payload['text'] == 'Created annotation via API'
    assert payload['reviewer_id'] == reader_id



def test_api_create_annotation_requires_authentication(client, app):
    ensure_guest(client)

    with app.app_context():
        book = Book(title='Create Annotation API', author_name='GG', author_surname='HH', month='Apr', year=2024)
        db.session.add(book)
        db.session.commit()
        book_id = book.id

    response = client.post(
        f'/api/v1/books/{book_id}/annotations',
        json={'text': 'Anon'},
        follow_redirects=False,
    )

    assert response.status_code == 401
    assert response.is_json


def test_api_books_collection_hides_hidden_books_for_reader(client, app, user):
    ensure_guest(client)
    tokens = api_login(client, email=user, password='Secret123!')

    with app.app_context():
        db.session.add_all(
            [
                Book(title='Visible API Book', author_name='A', author_surname='B', month='Jan', year=2025, is_hidden=False),
                Book(title='Hidden API Book', author_name='C', author_surname='D', month='Jan', year=2025, is_hidden=True),
            ]
        )
        db.session.commit()

    response = client.get(
        '/api/v1/books?search=API&page=1&per_page=10',
        headers=api_headers(tokens['access_token']),
        follow_redirects=False,
    )
    assert response.status_code == 200
    payload = response.get_json()
    assert payload['pagination']['total'] == 1
    assert payload['items'][0]['title'] == 'Visible API Book'


def test_api_book_details_returns_403_for_hidden_book_reader(client, app, user):
    ensure_guest(client)
    tokens = api_login(client, email=user, password='Secret123!')

    with app.app_context():
        book = Book(title='Hidden API Details', author_name='A', author_surname='B', month='Jan', year=2025, is_hidden=True)
        db.session.add(book)
        db.session.commit()
        book_id = book.id

    response = client.get(
        f'/api/v1/books/{book_id}',
        headers=api_headers(tokens['access_token']),
        follow_redirects=False,
    )
    assert response.status_code == 403
    payload = response.get_json()
    assert payload['error']['message'] == 'This book is hidden.'


def test_api_book_details_allows_hidden_book_for_librarian(client, app, librarian):
    ensure_guest(client)
    tokens = api_login(client, email=librarian, password='Secret123!')

    with app.app_context():
        book = Book(title='Hidden API Details Librarian', author_name='A', author_surname='B', month='Jan', year=2025, is_hidden=True)
        db.session.add(book)
        db.session.commit()
        book_id = book.id

    response = client.get(
        f'/api/v1/books/{book_id}',
        headers=api_headers(tokens['access_token']),
        follow_redirects=False,
    )
    assert response.status_code == 200
    assert response.get_json()['title'] == 'Hidden API Details Librarian'


def test_api_toggle_hidden_requires_librarian(client, app, user, librarian):
    with app.app_context():
        book = Book(title='API Toggle Hidden', author_name='A', author_surname='B', month='Jan', year=2025)
        db.session.add(book)
        db.session.commit()
        book_id = book.id

    ensure_guest(client)
    unauth = client.post(f'/api/v1/books/{book_id}/toggle-hidden', follow_redirects=False)
    assert unauth.status_code == 401

    reader_tokens = api_login(client, email=user, password='Secret123!')
    reader_forbidden = client.post(
        f'/api/v1/books/{book_id}/toggle-hidden',
        headers=api_headers(reader_tokens['access_token']),
        follow_redirects=False,
    )
    assert reader_forbidden.status_code == 403

    ensure_guest(client)
    librarian_tokens = api_login(client, email=librarian, password='Secret123!')
    success = client.post(
        f'/api/v1/books/{book_id}/toggle-hidden',
        headers=api_headers(librarian_tokens['access_token']),
        follow_redirects=False,
    )
    assert success.status_code == 200
    assert success.is_json
    assert success.get_json()['is_hidden'] is True


def test_api_toggle_hidden_returns_404_for_missing_book_for_librarian(client, librarian):
    ensure_guest(client)
    tokens = api_login(client, email=librarian, password='Secret123!')

    response = client.post(
        '/api/v1/books/999999/toggle-hidden',
        headers=api_headers(tokens['access_token']),
        follow_redirects=False,
    )

    assert response.status_code == 404
    assert response.is_json
    assert response.get_json()['error']['message']


def test_home_shows_librarian_controls_for_librarian(client, app, librarian):
    ensure_guest(client)
    login_response = login(client, email=librarian)
    assert login_response.status_code == 302

    with app.app_context():
        book = Book(title='Librarian Home Controls', author_name='A', author_surname='B', month='Jan', year=2025)
        db.session.add(book)
        db.session.commit()
        book_id = book.id

    response = client.get('/home', follow_redirects=True)

    assert response.status_code == 200
    assert f'/book/{book_id}/toggle-hidden'.encode() in response.data
    assert f'data-href="/book/{book_id}"'.encode() in response.data
    assert b'/books/new' in response.data


def test_create_book_page_redirects_reader_to_home(client, user):
    ensure_guest(client)
    login_response = login(client, email=user)
    assert login_response.status_code == 302

    response = client.get('/books/new', follow_redirects=False)

    assert response.status_code == 302
    assert '/home' in response.headers['Location']


def test_create_book_page_is_available_for_librarian(client, librarian):
    ensure_guest(client)
    login_response = login(client, email=librarian)
    assert login_response.status_code == 302

    response = client.get('/books/new', follow_redirects=False)

    assert response.status_code == 200
    assert b'Add a new book' in response.data
    assert b'Create book' in response.data


def test_librarian_can_create_book_from_form(client, app, librarian):
    ensure_guest(client)
    login_response = login(client, email=librarian)
    assert login_response.status_code == 302

    response = client.post(
        '/books/new',
        data={
            'title': 'New Catalog Book',
            'author_name': 'Lesia',
            'author_surname': 'Ukrainka',
            'original_language': 'Ukrainian',
            'translation_language': 'English',
            'first_publication': '1900',
            'genre': 'Drama, Poetry',
            'month': 'April',
            'year': '2026',
            'cover_image': '',
            'is_hidden': 'y',
        },
        follow_redirects=False,
    )

    assert response.status_code == 302
    assert '/edit' in response.headers['Location']

    with app.app_context():
        created = db.session.scalar(select(Book).filter_by(title='New Catalog Book'))
        assert created is not None
        assert created.author_name == 'Lesia'
        assert created.author_surname == 'Ukrainka'
        assert created.original_language == 'Ukrainian'
        assert created.translation_language == 'English'
        assert created.first_publication == '1900'
        assert created.genre == 'Drama, Poetry'
        assert created.month == 'April'
        assert created.year == 2026
        assert created.cover_image == 'book_covers/default.svg'
        assert created.is_hidden is True
        assert response.headers['Location'].endswith(f'/book/{created.id}/edit')


def test_librarian_cannot_create_duplicate_book_title(client, app, librarian):
    ensure_guest(client)
    login_response = login(client, email=librarian)
    assert login_response.status_code == 302

    with app.app_context():
        db.session.add(
            Book(
                title='Duplicate Book',
                author_name='Existing',
                author_surname='Author',
                original_language='English',
                translation_language='English',
                first_publication='2024',
                genre='Fiction',
                month='January',
                year=2025,
            )
        )
        db.session.commit()

    response = client.post(
        '/books/new',
        data={
            'title': 'Duplicate Book',
            'author_name': 'New',
            'author_surname': 'Author',
            'original_language': 'French',
            'translation_language': 'English',
            'first_publication': '2025',
            'genre': 'History',
            'month': 'February',
            'year': '2026',
            'cover_image': 'book_covers/custom.svg',
        },
        follow_redirects=True,
    )

    assert response.status_code == 200
    assert b'A book with this title already exists.' in response.data

    with app.app_context():
        stored = db.session.execute(select(Book).filter_by(title='Duplicate Book')).scalars().all()
        assert len(stored) == 1


def test_book_edit_page_redirects_reader_to_home(client, app, user):
    ensure_guest(client)
    login_response = login(client, email=user)
    assert login_response.status_code == 302

    with app.app_context():
        book = Book(title='Content Editor Reader Forbidden', author_name='A', author_surname='B', month='Jan', year=2025)
        db.session.add(book)
        db.session.commit()
        book_id = book.id

    response = client.get(f'/book/{book_id}/edit', follow_redirects=False)

    assert response.status_code == 302
    assert '/home' in response.headers['Location']


def test_book_edit_page_shows_metadata_and_html_blocks_for_librarian(client, app, librarian):
    ensure_guest(client)
    login_response = login(client, email=librarian)
    assert login_response.status_code == 302

    with app.app_context():
        book = Book(title='Starter Template Book', author_name='A', author_surname='B', month='Jan', year=2025)
        db.session.add(book)
        db.session.commit()
        book_id = book.id

    response = client.get(f'/book/{book_id}/edit', follow_redirects=False)

    assert response.status_code == 200
    assert b'Edit book: Starter Template Book' in response.data
    assert b'Book Data' in response.data
    assert b'Reading HTML' in response.data
    assert b'value="Starter Template Book"' in response.data
    assert b'Write a short summary for readers here.' in response.data
    assert b'&lt;h2&gt;Description&lt;/h2&gt;' in response.data
    assert b'Chapter 1' in response.data


def test_librarian_can_update_book_metadata_from_edit_page(client, app, librarian):
    ensure_guest(client)
    login_response = login(client, email=librarian)
    assert login_response.status_code == 302

    with app.app_context():
        book = Book(
            title='Editable Metadata Book',
            author_name='Old',
            author_surname='Author',
            original_language='English',
            translation_language='English',
            first_publication='2000',
            genre='Essay',
            month='May',
            year=2020,
            cover_image='book_covers/default.svg',
            is_hidden=False,
        )
        db.session.add(book)
        db.session.commit()
        book_id = book.id

    response = client.post(
        f'/book/{book_id}/edit',
        data={
            'meta-title': 'Updated Metadata Book',
            'meta-author_name': 'New',
            'meta-author_surname': 'Writer',
            'meta-original_language': 'French',
            'meta-translation_language': 'Ukrainian',
            'meta-first_publication': '1984',
            'meta-genre': 'Novel, Philosophy',
            'meta-month': 'October',
            'meta-year': '2029',
            'meta-cover_image': '',
            'meta-is_hidden': 'y',
            'meta-submit': '1',
        },
        follow_redirects=True,
    )

    assert response.status_code == 200
    assert b'Book details saved.' in response.data

    with app.app_context():
        updated = db.session.get(Book, book_id)
        assert updated.title == 'Updated Metadata Book'
        assert updated.author_name == 'New'
        assert updated.author_surname == 'Writer'
        assert updated.original_language == 'French'
        assert updated.translation_language == 'Ukrainian'
        assert updated.first_publication == '1984'
        assert updated.genre == 'Novel, Philosophy'
        assert updated.month == 'October'
        assert updated.year == 2029
        assert updated.cover_image == 'book_covers/default.svg'
        assert updated.is_hidden is True


def test_librarian_can_save_book_html_content_from_edit_page(client, app, librarian, tmp_path):
    ensure_guest(client)
    login_response = login(client, email=librarian)
    assert login_response.status_code == 302

    original_dir = app.config.get('BOOK_TEXT_DIR')
    app.config['BOOK_TEXT_DIR'] = str(tmp_path)

    try:
        with app.app_context():
            book = Book(title='Editable Content Book', author_name='A', author_surname='B', month='Jan', year=2025)
            db.session.add(book)
            db.session.commit()
            book_id = book.id

        html_content = """<!doctype html>
<html lang="en">
<head>
    <meta charset="utf-8">
    <title>Editable Content Book</title>
</head>
<body>
    <h1>Editable Content Book</h1>
    <p>Saved from the editor.</p>
    <h2>Plot &amp; Themes</h2>
    <p>Editor-generated preview section.</p>
    <h2 id="contents">Contents</h2>
    <ul>
        <li><a href="#part-1">Part 1</a></li>
    </ul>
    <h2>Text</h2>
    <section id="part-1">
        <h3>Part 1</h3>
        <p>The saved text is visible on the read page.</p>
        <p><a href="#contents">Back to contents</a></p>
    </section>
</body>
</html>"""

        response = client.post(
            f'/book/{book_id}/edit',
            data={'content-html_content': html_content, 'content-submit': '1'},
            follow_redirects=True,
        )

        assert response.status_code == 200
        assert b'Book HTML content saved.' in response.data

        saved_file = tmp_path / f'book-{book_id}.html'
        assert saved_file.exists()
        assert 'Saved from the editor.' in saved_file.read_text(encoding='utf-8')

        detail_response = client.get(f'/book/{book_id}', follow_redirects=False)
        assert detail_response.status_code == 200
        assert b'Saved from the editor.' in detail_response.data
        assert b'Editor-generated preview section.' in detail_response.data
        assert f'/book/{book_id}/edit'.encode() in detail_response.data

        read_response = client.get(f'/book/{book_id}/read', follow_redirects=False)
        assert read_response.status_code == 200
        assert b'href="#part-1"' in read_response.data
        assert b'The saved text is visible on the read page.' in read_response.data
    finally:
        if original_dir is None:
            app.config.pop('BOOK_TEXT_DIR', None)
        else:
            app.config['BOOK_TEXT_DIR'] = original_dir




def test_toggle_hidden_returns_json_for_ajax_requests(client, app, librarian):
    ensure_guest(client)
    login_response = login(client, email=librarian)
    assert login_response.status_code == 302

    with app.app_context():
        book = Book(title='Ajax Hidden Toggle', author_name='A', author_surname='B', month='Jan', year=2025)
        db.session.add(book)
        db.session.commit()
        book_id = book.id

    response = client.post(
        f'/book/{book_id}/toggle-hidden',
        headers={'X-Requested-With': 'XMLHttpRequest'},
        follow_redirects=False,
    )

    assert response.status_code == 200
    assert response.is_json
    payload = response.get_json()
    assert payload['book_id'] == book_id
    assert payload['is_hidden'] is True
    assert payload['button_label_short'] == 'Unhide'


def test_toggle_hidden_ajax_forbidden_for_reader(client, app, user):
    ensure_guest(client)
    login_response = login(client, email=user)
    assert login_response.status_code == 302

    with app.app_context():
        book = Book(title='Ajax Toggle Forbidden', author_name='A', author_surname='B', month='Jan', year=2025)
        db.session.add(book)
        db.session.commit()
        book_id = book.id

    response = client.post(
        f'/book/{book_id}/toggle-hidden',
        headers={'X-Requested-With': 'XMLHttpRequest'},
        follow_redirects=False,
    )

    assert response.status_code == 403
    assert response.is_json
    assert response.get_json()['error'] == 'Only librarians can change visibility.'


def test_toggle_hidden_non_ajax_still_returns_json(client, app, librarian):
    ensure_guest(client)
    login_response = login(client, email=librarian)
    assert login_response.status_code == 302

    with app.app_context():
        book = Book(title='Non Ajax Toggle', author_name='A', author_surname='B', month='Jan', year=2025)
        db.session.add(book)
        db.session.commit()
        book_id = book.id

    response = client.post(
        f'/book/{book_id}/toggle-hidden',
        follow_redirects=False,
    )

    assert response.status_code == 200
    assert response.is_json
    assert response.get_json()['book_id'] == book_id


def test_toggle_hidden_web_returns_not_found_for_missing_book(client, librarian):
    ensure_guest(client)
    login_response = login(client, email=librarian)
    assert login_response.status_code == 302

    response = client.post('/book/999999/toggle-hidden', follow_redirects=False)

    assert response.status_code == 404


def test_book_read_shows_annotation_delete_for_librarian(client, app, librarian):
    ensure_guest(client)
    login_response = login(client, email=librarian)
    assert login_response.status_code == 302

    with app.app_context():
        librarian_user = db.session.scalar(select(Reader).filter_by(email=librarian))
        book = Book(title='Librarian Read Controls', author_name='A', author_surname='B', month='Jan', year=2025)
        db.session.add(book)
        db.session.commit()

        annotation = Annotation(text='Moderation target', book_id=book.id, reviewer_id=librarian_user.id)
        db.session.add(annotation)
        db.session.commit()
        book_id = book.id
        annotation_id = annotation.id

    response = client.get(f'/book/{book_id}/read', follow_redirects=True)

    assert response.status_code == 200
    assert f'/annotations/{annotation_id}/delete'.encode() in response.data


def test_web_librarian_can_edit_review(client, app, user, librarian):
    ensure_guest(client)
    login_response = login(client, email=librarian, password='Secret123!')
    assert login_response.status_code == 302

    with app.app_context():
        reviewer = db.session.scalar(select(Reader).filter_by(email=user))
        book = Book(title='Web Edit Review', author_name='A', author_surname='B', month='Jan', year=2025)
        db.session.add(book)
        db.session.commit()

        review = Review(text='Before web edit', stars=2, book_id=book.id, reviewer_id=reviewer.id)
        db.session.add(review)
        db.session.commit()
        review_id = review.id

    response = client.post(
        f'/reviews/{review_id}/edit',
        data={'text': 'After web edit', 'stars': 5},
        follow_redirects=False,
    )
    assert response.status_code == 302

    with app.app_context():
        updated = db.session.scalar(select(Review).filter_by(id=review_id))
        assert updated.text == 'After web edit'
        assert updated.stars == 5


def test_web_reader_cannot_edit_review(client, app, user):
    ensure_guest(client)
    login_response = login(client, email=user, password='Secret123!')
    assert login_response.status_code == 302

    with app.app_context():
        reviewer = db.session.scalar(select(Reader).filter_by(email=user))
        book = Book(title='Web Edit Review Forbidden', author_name='A', author_surname='B', month='Jan', year=2025)
        db.session.add(book)
        db.session.commit()

        review = Review(text='Before forbidden edit', stars=2, book_id=book.id, reviewer_id=reviewer.id)
        db.session.add(review)
        db.session.commit()
        review_id = review.id

    response = client.post(
        f'/reviews/{review_id}/edit',
        data={'text': 'After forbidden edit', 'stars': 5},
        follow_redirects=False,
    )
    assert response.status_code == 302
    assert '/home' in response.headers['Location']

    with app.app_context():
        unchanged = db.session.scalar(select(Review).filter_by(id=review_id))
        assert unchanged.text == 'Before forbidden edit'
        assert unchanged.stars == 2


def test_web_librarian_can_edit_annotation(client, app, user, librarian):
    ensure_guest(client)
    login_response = login(client, email=librarian, password='Secret123!')
    assert login_response.status_code == 302

    with app.app_context():
        author = db.session.scalar(select(Reader).filter_by(email=user))
        book = Book(title='Web Edit Annotation', author_name='A', author_surname='B', month='Jan', year=2025)
        db.session.add(book)
        db.session.commit()

        annotation = Annotation(text='Before annotation edit', book_id=book.id, reviewer_id=author.id)
        db.session.add(annotation)
        db.session.commit()
        annotation_id = annotation.id

    response = client.post(
        f'/annotations/{annotation_id}/edit',
        data={'text': 'After annotation edit'},
        follow_redirects=False,
    )
    assert response.status_code == 302

    with app.app_context():
        updated = db.session.scalar(select(Annotation).filter_by(id=annotation_id))
        assert updated.text == 'After annotation edit'


def test_web_reader_cannot_edit_annotation(client, app, user):
    ensure_guest(client)
    login_response = login(client, email=user, password='Secret123!')
    assert login_response.status_code == 302

    with app.app_context():
        author = db.session.scalar(select(Reader).filter_by(email=user))
        book = Book(title='Web Edit Annotation Forbidden', author_name='A', author_surname='B', month='Jan', year=2025)
        db.session.add(book)
        db.session.commit()

        annotation = Annotation(text='Before forbidden annotation edit', book_id=book.id, reviewer_id=author.id)
        db.session.add(annotation)
        db.session.commit()
        annotation_id = annotation.id

    response = client.post(
        f'/annotations/{annotation_id}/edit',
        data={'text': 'After forbidden annotation edit'},
        follow_redirects=False,
    )
    assert response.status_code == 302
    assert '/home' in response.headers['Location']

    with app.app_context():
        unchanged = db.session.scalar(select(Annotation).filter_by(id=annotation_id))
        assert unchanged.text == 'Before forbidden annotation edit'


def test_web_reader_can_delete_own_review(client, app, user):
    ensure_guest(client)
    login_response = login(client, email=user, password='Secret123!')
    assert login_response.status_code == 302

    with app.app_context():
        reviewer = db.session.scalar(select(Reader).filter_by(email=user))
        book = Book(title='Own Review Delete', author_name='A', author_surname='B', month='Jan', year=2025)
        db.session.add(book)
        db.session.commit()

        review = Review(text='Delete me', stars=4, book_id=book.id, reviewer_id=reviewer.id)
        db.session.add(review)
        db.session.commit()
        review_id = review.id

    response = client.post(f'/reviews/{review_id}/delete', follow_redirects=False)
    assert response.status_code == 302

    with app.app_context():
        deleted = db.session.scalar(select(Review).filter_by(id=review_id))
        assert deleted is None


def test_web_reader_cannot_delete_other_users_review(client, app, user):
    ensure_guest(client)
    login_response = login(client, email=user, password='Secret123!')
    assert login_response.status_code == 302

    with app.app_context():
        owner = Reader(
            name='Another',
            surname='Owner',
            email='another.owner@example.com',
            role='reader',
        )
        owner.set_password('Secret123!')
        db.session.add(owner)

        book = Book(title='Other Review Delete', author_name='A', author_surname='B', month='Jan', year=2025)
        db.session.add(book)
        db.session.commit()

        review = Review(text='Should stay', stars=5, book_id=book.id, reviewer_id=owner.id)
        db.session.add(review)
        db.session.commit()
        review_id = review.id

    response = client.post(f'/reviews/{review_id}/delete', follow_redirects=False)
    assert response.status_code == 302
    assert '/home' in response.headers['Location']

    with app.app_context():
        remaining = db.session.scalar(select(Review).filter_by(id=review_id))
        assert remaining is not None


def test_book_page_has_no_inline_review_edit_form_for_librarian(client, app, user, librarian):
    ensure_guest(client)
    login_response = login(client, email=librarian, password='Secret123!')
    assert login_response.status_code == 302

    with app.app_context():
        reviewer = db.session.scalar(select(Reader).filter_by(email=user))
        book = Book(title='No Inline Edit Block', author_name='A', author_surname='B', month='Jan', year=2025)
        db.session.add(book)
        db.session.commit()

        review = Review(text='Visible review text', stars=3, book_id=book.id, reviewer_id=reviewer.id)
        db.session.add(review)
        db.session.commit()
        book_id = book.id

    response = client.get(f'/book/{book_id}', follow_redirects=True)
    assert response.status_code == 200
    assert b'Save review' not in response.data
    assert b'/reviews/' in response.data


def test_api_reader_can_delete_own_review(client, app, user):
    ensure_guest(client)
    tokens = api_login(client, email=user, password='Secret123!')

    with app.app_context():
        reviewer = db.session.scalar(select(Reader).filter_by(email=user))
        book = Book(title='API Own Delete', author_name='A', author_surname='B', month='Jan', year=2025)
        db.session.add(book)
        db.session.commit()

        review = Review(text='API delete me', stars=4, book_id=book.id, reviewer_id=reviewer.id)
        db.session.add(review)
        db.session.commit()
        review_id = review.id

    response = client.delete(
        f'/api/v1/reviews/{review_id}',
        headers=api_headers(tokens['access_token']),
    )
    assert response.status_code == 204

    with app.app_context():
        deleted = db.session.scalar(select(Review).filter_by(id=review_id))
        assert deleted is None


def test_api_reader_cannot_delete_other_users_review(client, app, user):
    ensure_guest(client)
    tokens = api_login(client, email=user, password='Secret123!')

    with app.app_context():
        owner = Reader(
            name='Api',
            surname='Owner',
            email='api.owner@example.com',
            role='reader',
        )
        owner.set_password('Secret123!')
        db.session.add(owner)

        book = Book(title='API Other Delete', author_name='A', author_surname='B', month='Jan', year=2025)
        db.session.add(book)
        db.session.commit()

        review = Review(text='API should stay', stars=2, book_id=book.id, reviewer_id=owner.id)
        db.session.add(review)
        db.session.commit()
        review_id = review.id

    response = client.delete(
        f'/api/v1/reviews/{review_id}',
        headers=api_headers(tokens['access_token']),
    )
    assert response.status_code == 403
    assert response.is_json
    assert response.get_json()['error']['message'] == 'You can delete only your own review unless you are a librarian.'

    with app.app_context():
        still_exists = db.session.scalar(select(Review).filter_by(id=review_id))
        assert still_exists is not None


def test_book_route_shows_hidden_access_denied_page_for_reader(client, user, app):
    ensure_guest(client)
    login_response = login(client, email=user)
    assert login_response.status_code == 302

    with app.app_context():
        book = Book(
            title='Reader Hidden Direct Access',
            author_name='A',
            author_surname='B',
            month='Jan',
            year=2025,
            is_hidden=True,
        )
        db.session.add(book)
        db.session.commit()
        book_id = book.id

    response = client.get(f'/book/{book_id}', follow_redirects=False)
    assert response.status_code == 403
    assert b'This book is hidden' in response.data
    assert b'Back to home' in response.data
    assert b'Logout' in response.data


def test_book_route_allows_hidden_book_for_librarian(client, app, librarian):
    ensure_guest(client)
    login_response = login(client, email=librarian)
    assert login_response.status_code == 302

    with app.app_context():
        book = Book(
            title='Librarian Hidden Direct Access',
            author_name='A',
            author_surname='B',
            month='Jan',
            year=2025,
            is_hidden=True,
        )
        db.session.add(book)
        db.session.commit()
        book_id = book.id

    response = client.get(f'/book/{book_id}', follow_redirects=False)
    assert response.status_code == 200


def test_book_read_route_shows_hidden_access_denied_page_for_reader(client, user, app):
    ensure_guest(client)
    login_response = login(client, email=user)
    assert login_response.status_code == 302

    with app.app_context():
        book = Book(
            title='Reader Hidden Read Access',
            author_name='A',
            author_surname='B',
            month='Jan',
            year=2025,
            is_hidden=True,
        )
        db.session.add(book)
        db.session.commit()
        book_id = book.id

    response = client.get(f'/book/{book_id}/read', follow_redirects=False)
    assert response.status_code == 403
    assert b'This book is hidden' in response.data
    assert b'Back to home' in response.data
    assert b'Logout' in response.data


def test_book_route_shows_custom_not_found_page_for_missing_book(client, user):
    ensure_guest(client)
    login_response = login(client, email=user)
    assert login_response.status_code == 302

    response = client.get('/book/999999', follow_redirects=False)

    assert response.status_code == 404
    assert b'Book not found' in response.data
    assert b'ID <strong>999999</strong>' in response.data
    assert b'Back to home' in response.data
    assert b'Logout' in response.data


def test_book_read_route_shows_custom_not_found_page_for_missing_book(client, user):
    ensure_guest(client)
    login_response = login(client, email=user)
    assert login_response.status_code == 302

    response = client.get('/book/999999/read', follow_redirects=False)

    assert response.status_code == 404
    assert b'Book not found' in response.data
    assert b'ID <strong>999999</strong>' in response.data
    assert b'Back to home' in response.data
    assert b'Logout' in response.data
