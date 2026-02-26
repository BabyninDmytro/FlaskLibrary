from app.extensions import db
from app.models import Annotation, Book, Reader, Review

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

    response = client.post(
        f'/book/{book_id}',
        data={'review-text': 'Guest review', 'review-stars': 3, 'review-submit': '1'},
        follow_redirects=False,
    )

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
        data={'review-text': 'Should not persist', 'review-stars': 9, 'review-submit': '1'},
        follow_redirects=True,
    )

    assert response.status_code == 200

    with app.app_context():
        stored = Review.query.filter_by(book_id=book_id, text='Should not persist').first()
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
        stored = Annotation.query.filter_by(book_id=book_id, text='A compact and useful annotation').first()
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
        stored = Annotation.query.filter_by(book_id=book_id, text='Reader annotation attempt').first()
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
        assert Annotation.query.filter_by(book_id=book_id, text='Guest note').first() is None


def test_book_read_route_redirects_guest_for_missing_book(client):
    response = client.get('/book/999999/read', follow_redirects=False)

    assert response.status_code == 302
    assert '/login' in response.headers['Location']




def test_api_book_data_returns_json_payload(client, app, user):
    with app.app_context():
        reader = Reader.query.filter_by(email=user).first()
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


def test_book_page_route_remains_html_after_rest_migration(client, app):
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

    response = client.get(f'/book/{book_id}', follow_redirects=False)

    assert response.status_code == 200
    assert b'<html' in response.data
    assert b'HTML Book Page' in response.data


def test_book_read_route_shows_annotations_in_expected_order(client, app, user):
    login_response = login(client)
    assert login_response.status_code == 302

    with app.app_context():
        reader = Reader.query.filter_by(email=user).first()
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
    assert b'Lorem ipsum' in response.data
    assert response.data.count(b'Back to book page') == 2

    assert 'Опис:'.encode('utf-8') not in response.data
    assert 'Текст книги'.encode('utf-8') not in response.data
    assert b'Contents' in response.data
    assert 'Розділ 1'.encode('utf-8') in response.data
    assert b'href="#chapter-1"' in response.data

    title_index = response.data.index(b'Readable Book')
    description_index = response.data.index(b'Oksana R')
    cover_index = response.data.index('Обкладинка книги'.encode('utf-8'))
    annotations_index = response.data.index('Анотації'.encode('utf-8'))
    contents_index = response.data.index(b'Contents')
    chapter_link_index = response.data.index('Розділ 1'.encode('utf-8'))
    book_text_index = response.data.index(b'id="chapter-1"')

    assert title_index < description_index < cover_index < annotations_index < contents_index < chapter_link_index < book_text_index


def test_book_page_shows_read_now_button_and_hides_annotation_feed(client, app, user):
    login_response = login(client)
    assert login_response.status_code == 302

    with app.app_context():
        reader = Reader.query.filter_by(email=user).first()
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

    response = client.get(f'/book/{book_id}', follow_redirects=True)

    assert response.status_code == 200
    assert f'/book/{book_id}/read'.encode() in response.data
    assert b'Hidden on details page' not in response.data



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
    assert 'Розділ 1'.encode('utf-8') in response.data
    assert b'id="chapter-1"' in response.data
    assert 'Текст книги'.encode('utf-8') not in response.data


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
        reader = Reader.query.filter_by(email=user).first()
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
        reader = Reader.query.filter_by(email=user).first()
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
        reader = Reader.query.filter_by(email=user).first()
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



def test_api_review_patch_returns_403_for_non_owner(client, app, user):
    with app.app_context():
        owner = Reader.query.filter_by(email=user).first()
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
    login_response = login(client, email='intruder@example.com', password='Secret123!')
    assert login_response.status_code == 302

    response = client.patch(f'/api/v1/reviews/{review_id}', json={'text': 'Hacked'}, follow_redirects=False)

    assert response.status_code == 403



def test_api_review_patch_returns_422_for_invalid_data(client, app, user):
    ensure_guest(client)
    login_response = login(client, email=user, password='Secret123!')
    assert login_response.status_code == 302

    with app.app_context():
        reader = Reader.query.filter_by(email=user).first()
        book = Book(title='Invalid Patch', author_name='E', author_surname='F', month='July', year=2024)
        db.session.add(book)
        db.session.commit()
        review = Review(text='Valid text', stars=4, book_id=book.id, reviewer_id=reader.id)
        db.session.add(review)
        db.session.commit()
        review_id = review.id

    response = client.patch(f'/api/v1/reviews/{review_id}', json={'stars': 9}, follow_redirects=False)

    assert response.status_code == 422
    assert response.is_json



def test_api_review_patch_updates_owned_review(client, app, user):
    ensure_guest(client)
    login_response = login(client, email=user, password='Secret123!')
    assert login_response.status_code == 302

    with app.app_context():
        reader = Reader.query.filter_by(email=user).first()
        book = Book(title='Owned Patch', author_name='G', author_surname='H', month='August', year=2024)
        db.session.add(book)
        db.session.commit()
        review = Review(text='Before update', stars=2, book_id=book.id, reviewer_id=reader.id)
        db.session.add(review)
        db.session.commit()
        review_id = review.id

    response = client.patch(
        f'/api/v1/reviews/{review_id}',
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
        reader = Reader.query.filter_by(email=user).first()
        book = Book(title='Delete Review Book', author_name='I', author_surname='J', month='September', year=2024)
        db.session.add(book)
        db.session.commit()
        review = Review(text='Delete me', stars=3, book_id=book.id, reviewer_id=reader.id)
        db.session.add(review)
        db.session.commit()
        review_id = review.id

    response = client.delete(f'/api/v1/reviews/{review_id}', follow_redirects=False)

    assert response.status_code == 401



def test_api_review_delete_removes_owned_review(client, app, user):
    ensure_guest(client)
    login_response = login(client, email=user, password='Secret123!')
    assert login_response.status_code == 302

    with app.app_context():
        reader = Reader.query.filter_by(email=user).first()
        book = Book(title='Owned Delete Review', author_name='K', author_surname='L', month='October', year=2024)
        db.session.add(book)
        db.session.commit()
        review = Review(text='Delete owned', stars=1, book_id=book.id, reviewer_id=reader.id)
        db.session.add(review)
        db.session.commit()
        review_id = review.id

    response = client.delete(f'/api/v1/reviews/{review_id}', follow_redirects=False)

    assert response.status_code == 204

    with app.app_context():
        assert Review.query.filter_by(id=review_id).first() is None



def test_api_annotation_patch_and_delete_for_owner(client, app, user):
    ensure_guest(client)
    login_response = login(client, email=user, password='Secret123!')
    assert login_response.status_code == 302

    with app.app_context():
        reader = Reader.query.filter_by(email=user).first()
        book = Book(title='Annotation Mutations', author_name='M', author_surname='N', month='November', year=2024)
        db.session.add(book)
        db.session.commit()
        annotation = Annotation(text='Before note', book_id=book.id, reviewer_id=reader.id)
        db.session.add(annotation)
        db.session.commit()
        annotation_id = annotation.id

    patch_response = client.patch(
        f'/api/v1/annotations/{annotation_id}',
        json={'text': 'After note'},
        follow_redirects=False,
    )
    assert patch_response.status_code == 200
    assert patch_response.get_json()['text'] == 'After note'

    delete_response = client.delete(f'/api/v1/annotations/{annotation_id}', follow_redirects=False)
    assert delete_response.status_code == 204

    with app.app_context():
        assert Annotation.query.filter_by(id=annotation_id).first() is None



def test_api_annotation_patch_returns_401_403_422(client, app, user):
    with app.app_context():
        owner = Reader.query.filter_by(email=user).first()
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

    login_response = login(client, email='another.intruder@example.com', password='Secret123!')
    assert login_response.status_code == 302
    forbidden = client.patch(f'/api/v1/annotations/{annotation_id}', json={'text': 'x'}, follow_redirects=False)
    assert forbidden.status_code == 403

    ensure_guest(client)
    login_response = login(client, email=user, password='Secret123!')
    assert login_response.status_code == 302
    invalid = client.patch(f'/api/v1/annotations/{annotation_id}', json={'text': ''}, follow_redirects=False)
    assert invalid.status_code == 422



def test_api_annotation_delete_returns_404_for_missing_annotation(client):
    response = client.delete('/api/v1/annotations/999999', follow_redirects=False)

    assert response.status_code == 404


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
    login_response = login(client, email=user, password='Secret123!')
    assert login_response.status_code == 302

    with app.app_context():
        reader = Reader.query.filter_by(email=user).first()
        book = Book(title='Create Review Success', author_name='CC', author_surname='DD', month='Feb', year=2024)
        db.session.add(book)
        db.session.commit()
        book_id = book.id
        reader_id = reader.id

    invalid = client.post(
        f'/api/v1/books/{book_id}/reviews',
        json={'text': '', 'stars': 9},
        follow_redirects=False,
    )
    assert invalid.status_code == 422

    success = client.post(
        f'/api/v1/books/{book_id}/reviews',
        json={'text': 'Created via API', 'stars': 4},
        follow_redirects=False,
    )
    assert success.status_code == 201
    payload = success.get_json()
    assert payload['text'] == 'Created via API'
    assert payload['stars'] == 4
    assert payload['reviewer_id'] == reader_id



def test_api_create_annotation_validation_and_success(client, app, user):
    ensure_guest(client)
    login_response = login(client, email=user, password='Secret123!')
    assert login_response.status_code == 302

    with app.app_context():
        reader = Reader.query.filter_by(email=user).first()
        book = Book(title='Create Annotation Success', author_name='EE', author_surname='FF', month='Mar', year=2024)
        db.session.add(book)
        db.session.commit()
        book_id = book.id
        reader_id = reader.id

    invalid = client.post(
        f'/api/v1/books/{book_id}/annotations',
        json={'text': ''},
        follow_redirects=False,
    )
    assert invalid.status_code == 422

    success = client.post(
        f'/api/v1/books/{book_id}/annotations',
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
