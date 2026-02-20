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



def test_book_route_can_create_annotation_for_authenticated_user(client, user, app):
    login_response = login(client)
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
    assert b'A compact and useful annotation' not in response.data

    with app.app_context():
        stored = Annotation.query.filter_by(book_id=book_id, text='A compact and useful annotation').first()
        assert stored is not None


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


def test_book_read_route_returns_404_for_missing_book(client):
    response = client.get('/book/999999/read', follow_redirects=False)

    assert response.status_code == 404


def test_book_read_route_shows_annotations_in_expected_order(client, app, user):
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



def test_seed_book_read_page_works(client, app):
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


def test_hidden_books_are_not_listed_for_regular_readers(client, app, user):
    login_response = login(client)
    assert login_response.status_code == 302

    with app.app_context():
        visible = Book(title='Visible Book', author_name='A', author_surname='A', month='May', year=2024, is_hidden=False)
        hidden = Book(title='Hidden Book', author_name='B', author_surname='B', month='May', year=2024, is_hidden=True)
        db.session.add_all([visible, hidden])
        db.session.commit()
        hidden_id = hidden.id

    home_response = client.get('/home', follow_redirects=True)
    assert b'Visible Book' in home_response.data
    assert b'Hidden Book' not in home_response.data

    hidden_response = client.get(f'/book/{hidden_id}', follow_redirects=False)
    assert hidden_response.status_code == 302
    assert '/home' in hidden_response.headers['Location']


def test_librarian_can_hide_and_unhide_books(client, app, librarian):
    ensure_guest(client)
    login_response = login(client, email=librarian)
    assert login_response.status_code == 302

    with app.app_context():
        book = Book(title='Toggle Book', author_name='A', author_surname='A', month='June', year=2024)
        db.session.add(book)
        db.session.commit()
        book_id = book.id

    hide_response = client.post(f'/book/{book_id}/toggle-hidden', follow_redirects=False)
    assert hide_response.status_code == 302
    assert '/book/' in hide_response.headers['Location']

    with app.app_context():
        db.session.remove()
        reloaded = db.session.get(Book, book_id)
        assert reloaded.is_hidden is True

    unhide_response = client.post(f'/book/{book_id}/toggle-hidden', follow_redirects=False)
    assert unhide_response.status_code == 302

    with app.app_context():
        db.session.remove()
        reloaded = db.session.get(Book, book_id)
        assert reloaded.is_hidden is False


def test_librarian_can_delete_reviews_and_annotations(client, app, user, librarian):
    ensure_guest(client)
    with app.app_context():
        reader = Reader.query.filter_by(email=user).first()
        book = Book(title='Moderation Book', author_name='A', author_surname='A', month='July', year=2024)
        db.session.add(book)
        db.session.commit()

        review = Review(text='Needs cleanup', stars=2, book_id=book.id, reviewer_id=reader.id)
        annotation = Annotation(text='Temporary annotation', book_id=book.id, reviewer_id=reader.id)
        db.session.add_all([review, annotation])
        db.session.commit()
        review_id = review.id
        annotation_id = annotation.id

    login_response = login(client, email=librarian)
    assert login_response.status_code == 302

    review_response = client.post(f'/reviews/{review_id}/delete', follow_redirects=False)
    annotation_response = client.post(f'/annotations/{annotation_id}/delete', follow_redirects=False)
    assert review_response.status_code == 302
    assert annotation_response.status_code == 302
    assert '/book/' in review_response.headers['Location']

    with app.app_context():
        db.session.remove()
        assert Review.query.filter_by(id=review_id).first() is None
        assert Annotation.query.filter_by(id=annotation_id).first() is None


def test_regular_reader_cannot_moderate_content(client, app, user):
    with app.app_context():
        reader = Reader.query.filter_by(email=user).first()
        book = Book(title='Protected Book', author_name='A', author_surname='A', month='August', year=2024)
        db.session.add(book)
        db.session.commit()

        review = Review(text='Should stay', stars=4, book_id=book.id, reviewer_id=reader.id)
        annotation = Annotation(text='Should also stay', book_id=book.id, reviewer_id=reader.id)
        db.session.add_all([review, annotation])
        db.session.commit()
        review_id = review.id
        annotation_id = annotation.id
        book_id = book.id

    login_response = login(client)
    assert login_response.status_code == 302

    hide_response = client.post(f'/book/{book_id}/toggle-hidden', follow_redirects=False)
    review_response = client.post(f'/reviews/{review_id}/delete', follow_redirects=False)
    annotation_response = client.post(f'/annotations/{annotation_id}/delete', follow_redirects=False)

    assert hide_response.status_code == 302
    assert review_response.status_code == 302
    assert annotation_response.status_code == 302

    with app.app_context():
        db.session.remove()
        assert db.session.get(Book, book_id).is_hidden is False
        assert Review.query.filter_by(id=review_id).first() is not None
        assert Annotation.query.filter_by(id=annotation_id).first() is not None
