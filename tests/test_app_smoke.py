from app import load_user
from extensions import db
from models import Reader


def test_app_initializes_with_expected_core_config(app):
    assert app is not None
    assert app.config['TESTING'] is True
    assert app.config['WTF_CSRF_ENABLED'] is False
    assert app.config['SQLALCHEMY_DATABASE_URI'].startswith('sqlite:///')
    assert 'main' in app.blueprints


def test_user_loader_resolves_existing_user_by_id(app):
    with app.app_context():
        reader = Reader(
            name='Loader',
            surname='Check',
            email='loader.check@example.com',
            role='reader',
        )
        reader.set_password('Secret123!')
        db.session.add(reader)
        db.session.commit()

        loaded = load_user(reader.id)

        assert loaded is not None
        assert loaded.id == reader.id
        assert loaded.email == 'loader.check@example.com'


def test_user_loader_returns_none_for_missing_user(app):
    with app.app_context():
        assert load_user(999999) is None
