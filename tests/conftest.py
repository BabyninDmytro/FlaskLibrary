import pytest


from app import app as flask_app
from extensions import db, login_manager
from models import Book, Reader


@pytest.fixture(scope='session')
def app(tmp_path_factory):
    db_file = tmp_path_factory.mktemp('db') / 'test.db'

    flask_app.config.update(
        TESTING=True,
        LOGIN_DISABLED=False,
        WTF_CSRF_ENABLED=False,
        SQLALCHEMY_DATABASE_URI=f"sqlite:///{db_file}",
    )
    # Ensure flask-login does not bypass auth checks in testing.
    login_manager._login_disabled = False

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
