from pathlib import Path

from app import load_user
from app.extensions import db
from app.models import Reader


def test_app_initializes_with_expected_core_config(app):
    assert app is not None
    assert app.config['TESTING'] is False
    assert app.config['WTF_CSRF_ENABLED'] is False
    assert app.config['LOGIN_DISABLED'] is False
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


def _sqlite_path_from_uri(uri):
    assert uri.startswith('sqlite:///')
    return Path(uri.replace('sqlite:///', '', 1)).resolve()


def test_create_app_uses_project_instance_path_by_default():
    from app import create_app

    local_app = create_app({'TESTING': True})

    assert Path(local_app.instance_path).name == 'instance'
    assert _sqlite_path_from_uri(local_app.config['SQLALCHEMY_DATABASE_URI']).name == 'myDB.db'
    assert _sqlite_path_from_uri(local_app.config['SQLALCHEMY_DATABASE_URI']).parent.name == 'instance'


def test_create_app_supports_instance_and_db_env_overrides(monkeypatch, tmp_path):
    from app import create_app

    custom_instance = tmp_path / 'custom_instance'
    custom_db = custom_instance / 'custom.db'
    monkeypatch.setenv('FLASK_INSTANCE_PATH', str(custom_instance))
    monkeypatch.setenv('FLASK_DB_PATH', str(custom_db))

    local_app = create_app({'TESTING': True})

    assert Path(local_app.instance_path).resolve() == custom_instance.resolve()
    assert _sqlite_path_from_uri(local_app.config['SQLALCHEMY_DATABASE_URI']) == custom_db.resolve()
