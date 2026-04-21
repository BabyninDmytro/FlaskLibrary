from app.forms import AnnotationForm, BookContentForm, BookCreateForm, BookUpdateForm, LoginForm, RegistrationForm, ReviewForm


def test_registration_form_valid_data(app):
    with app.test_request_context(
        '/register',
        method='POST',
        data={
            'name': 'Test',
            'surname': 'User',
            'email': 'valid.user@example.com',
            'role': 'reader',
            'password': 'Secret123!',
            'password2': 'Secret123!',
        },
    ):
        form = RegistrationForm()

        assert form.validate() is True


def test_registration_form_requires_all_fields(app):
    with app.test_request_context('/register', method='POST', data={}):
        form = RegistrationForm()

        assert form.validate() is False
        assert 'This field is required.' in form.name.errors
        assert 'This field is required.' in form.surname.errors
        assert 'This field is required.' in form.email.errors
        assert 'This field is required.' in form.role.errors
        assert 'This field is required.' in form.password.errors
        assert 'This field is required.' in form.password2.errors


def test_registration_form_password_confirmation_must_match(app):
    with app.test_request_context(
        '/register',
        method='POST',
        data={
            'name': 'Test',
            'surname': 'User',
            'email': 'valid.user@example.com',
            'role': 'reader',
            'password': 'Secret123!',
            'password2': 'Different123!',
        },
    ):
        form = RegistrationForm()

        assert form.validate() is False
        assert 'Field must be equal to password.' in form.password2.errors


def test_registration_form_rejects_invalid_email_and_role(app):
    with app.test_request_context(
        '/register',
        method='POST',
        data={
            'name': 'Test',
            'surname': 'User',
            'email': 'not-an-email',
            'role': 'admin',
            'password': 'Secret123!',
            'password2': 'Secret123!',
        },
    ):
        form = RegistrationForm()

        assert form.validate() is False
        assert any('Invalid email address.' in error for error in form.email.errors)
        assert 'Not a valid choice.' in form.role.errors


def test_login_form_valid_data(app):
    with app.test_request_context(
        '/login',
        method='POST',
        data={'email': 'valid.user@example.com', 'password': 'Secret123!'},
    ):
        form = LoginForm()

        assert form.validate() is True


def test_login_form_requires_fields_and_valid_email(app):
    with app.test_request_context(
        '/login',
        method='POST',
        data={'email': 'invalid-email', 'password': ''},
    ):
        form = LoginForm()

        assert form.validate() is False
        assert any('Invalid email address.' in error for error in form.email.errors)
        assert 'This field is required.' in form.password.errors


def test_review_form_requires_text_and_stars(app):
    with app.test_request_context('/book/1', method='POST', data={'review-text': '', 'review-stars': ''}):
        form = ReviewForm(prefix='review')

        assert form.validate() is False
        assert 'This field is required.' in form.text.errors
        assert 'This field is required.' in form.stars.errors


def test_review_form_rejects_invalid_stars_choice(app):
    with app.test_request_context('/book/1', method='POST', data={'review-text': 'Loved this one', 'review-stars': 7}):
        form = ReviewForm(prefix='review')

        assert form.validate() is False
        assert 'Not a valid choice.' in form.stars.errors


def test_review_form_valid_text(app):
    with app.test_request_context('/book/1', method='POST', data={'review-text': 'Loved this one', 'review-stars': 4}):
        form = ReviewForm(prefix='review')

        assert form.validate() is True



def test_annotation_form_requires_text(app):
    with app.test_request_context('/book/1', method='POST', data={'annotation-text': ''}):
        form = AnnotationForm(prefix='annotation')

        assert form.validate() is False
        assert 'This field is required.' in form.text.errors


def test_annotation_form_valid_text(app):
    with app.test_request_context('/book/1', method='POST', data={'annotation-text': 'Great summary for readers'}):
        form = AnnotationForm(prefix='annotation')

        assert form.validate() is True


def test_book_create_form_valid_data(app):
    with app.test_request_context(
        '/books/new',
        method='POST',
        data={
            'title': 'Crime and Punishment',
            'author_name': 'Fyodor',
            'author_surname': 'Dostoevsky',
            'original_language': 'Russian',
            'translation_language': 'English',
            'first_publication': '1866',
            'genre': 'Psychological fiction, Philosophical novel',
            'month': 'February',
            'year': '2026',
            'cover_image': '',
            'is_hidden': 'y',
        },
    ):
        form = BookCreateForm()

        assert form.validate() is True


def test_book_create_form_requires_main_fields(app):
    with app.test_request_context('/books/new', method='POST', data={}):
        form = BookCreateForm()

        assert form.validate() is False
        assert 'This field is required.' in form.title.errors
        assert 'This field is required.' in form.author_name.errors
        assert 'This field is required.' in form.author_surname.errors
        assert 'This field is required.' in form.original_language.errors
        assert 'This field is required.' in form.translation_language.errors
        assert 'This field is required.' in form.first_publication.errors
        assert 'This field is required.' in form.genre.errors
        assert 'This field is required.' in form.year.errors


def test_book_create_form_rejects_invalid_month_and_year(app):
    with app.test_request_context(
        '/books/new',
        method='POST',
        data={
            'title': 'Invalid Book',
            'author_name': 'Test',
            'author_surname': 'Author',
            'original_language': 'English',
            'translation_language': 'English',
            'first_publication': '2024',
            'genre': 'Fiction',
            'month': 'Smarch',
            'year': '0',
        },
    ):
        form = BookCreateForm()

        assert form.validate() is False
        assert 'Not a valid choice.' in form.month.errors
        assert any('Number must be between 1 and 9999.' in error for error in form.year.errors)


def test_book_content_form_requires_html(app):
    with app.test_request_context('/book/1/content/edit', method='POST', data={'html_content': ''}):
        form = BookContentForm()

        assert form.validate() is False
        assert 'This field is required.' in form.html_content.errors


def test_book_content_form_accepts_html(app):
    with app.test_request_context(
        '/book/1/content/edit',
        method='POST',
        data={'html_content': '<html><body><h1>Book</h1><p>Summary</p></body></html>'},
    ):
        form = BookContentForm()

        assert form.validate() is True


def test_book_update_form_valid_data(app):
    with app.test_request_context(
        '/book/1/edit',
        method='POST',
        data={
            'title': 'Updated Book',
            'author_name': 'Updated',
            'author_surname': 'Author',
            'original_language': 'Ukrainian',
            'translation_language': 'English',
            'first_publication': '1999',
            'genre': 'Novel',
            'month': 'June',
            'year': '2028',
            'cover_image': 'book_covers/default.svg',
            'is_hidden': 'y',
        },
    ):
        form = BookUpdateForm()

        assert form.validate() is True


def test_book_update_form_requires_main_fields(app):
    with app.test_request_context('/book/1/edit', method='POST', data={}):
        form = BookUpdateForm()

        assert form.validate() is False
        assert 'This field is required.' in form.title.errors
        assert 'This field is required.' in form.author_name.errors
        assert 'This field is required.' in form.author_surname.errors
        assert 'This field is required.' in form.original_language.errors
        assert 'This field is required.' in form.translation_language.errors
        assert 'This field is required.' in form.first_publication.errors
        assert 'This field is required.' in form.genre.errors
        assert 'This field is required.' in form.year.errors
