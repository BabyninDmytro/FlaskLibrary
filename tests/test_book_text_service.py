from app.extensions import db
from app.models import Book
from app.services.book_text_service import load_book_text_preview


def test_load_book_text_preview_for_existing_file(app):
    with app.app_context():
        preview = load_book_text_preview(15)

    assert preview is not None
    assert preview.summary.startswith('Crime and Punishment is a novel by Russian author Fyodor Dostoevsky')
    section_titles = {section.title for section in preview.sections}
    assert {'Plot & Themes', 'Literary Significance', 'Editions & Translations'} <= section_titles


def test_load_book_text_preview_returns_none_for_missing_file(app):
    with app.app_context():
        preview = load_book_text_preview(999)

    assert preview is None


def test_book_page_shows_preview_blocks(client, app, user):
    login_response = client.post(
        '/login',
        data={'email': user, 'password': 'Secret123!'},
        follow_redirects=False,
    )
    assert login_response.status_code == 302

    with app.app_context():
        book = Book(
            id=15,
            title='Crime and Punishment',
            author_name='Fyodor',
            author_surname='Dostoevsky',
            original_language='Russian',
            translation_language='English',
            first_publication='1866',
            genre='Psychological, philosophical novel',
            month='January',
            year=2024,
        )
        db.session.add(book)
        db.session.commit()

    response = client.get('/book/15')

    assert response.status_code == 200
    html = response.get_data(as_text=True)
    assert 'Fyodor Dostoevsky' in html
    assert 'Original Language:' in html
    assert 'Translation Language:' in html
    assert '1866' in html
    assert 'Plot &amp; Themes:' in html
