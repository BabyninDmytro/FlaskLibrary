from forms import LoginForm, RegistrationForm


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
