import pytest
from pathlib import Path

from flask import Flask

from extensions import db, login_manager
from models import Book, Reader
from routes import bp


@pytest.fixture(scope='session')
def app(tmp_path_factory):
    db_file = tmp_path_factory.mktemp('db') / 'test.db'
    template_dir = Path(__file__).resolve().parents[1] / 'templates'

    flask_app = Flask('test_app', template_folder=str(template_dir))
    flask_app.config.update(
        SECRET_KEY='test-secret-key',
        TESTING=True,
        LOGIN_DISABLED=False,
        WTF_CSRF_ENABLED=False,
        SQLALCHEMY_DATABASE_URI=f"sqlite:///{db_file}",
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
    )

    db.init_app(flask_app)
    login_manager.login_view = 'main.login'
    login_manager.init_app(flask_app)

    if 'main' not in flask_app.blueprints:
        flask_app.register_blueprint(bp)

    @login_manager.user_loader
    def load_user(user_id):
        return db.session.get(Reader, int(user_id))

    with flask_app.app_context():
        db.session.remove()
        db.drop_all()
        db.create_all()
        yield flask_app
        db.session.remove()
        db.drop_all()


@pytest.fixture(autouse=True)
def clean_db(app):
    with app.app_context():
        db.session.remove()
        for table in reversed(db.metadata.sorted_tables):
            db.session.execute(table.delete())
        db.session.commit()
        db.session.remove()

    yield

    with app.app_context():
        db.session.remove()


@pytest.fixture()
def client(app):
    return app.test_client()


@pytest.fixture()
def runner(app):
    return app.test_cli_runner()


@pytest.fixture()
def user(app):
    with app.app_context():
        reader = Reader(
            name='Test',
            surname='User',
            email='test.user@example.com',
            role='reader',
        )
        reader.set_password('Secret123!')
        db.session.add(reader)
        db.session.commit()
        email = reader.email
        db.session.remove()
        return email


@pytest.fixture()
def books(app):
    with app.app_context():
        created = [
            Book(title='Alpha Book', author_name='Ann', author_surname='A', month='January', year=2024),
            Book(title='Beta Story', author_name='Bob', author_surname='B', month='February', year=2023),
            Book(title='Gamma Notes', author_name='Cara', author_surname='C', month='March', year=2022),
        ]
        db.session.add_all(created)
        db.session.commit()
        titles = [book.title for book in created]
        db.session.remove()
        return titles
