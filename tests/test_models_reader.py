import pytest
from sqlalchemy.exc import IntegrityError

from app.extensions import db
from app.models import Reader


def test_reader_set_password_stores_hash_not_plaintext(app):
    with app.app_context():
        reader = Reader(
            name='Hash',
            surname='Check',
            email='hash.check@example.com',
            role='reader',
        )

        reader.set_password('Secret123!')

        assert reader.password_hash is not None
        assert reader.password_hash != 'Secret123!'


def test_reader_check_password_valid_and_invalid(app):
    with app.app_context():
        reader = Reader(
            name='Auth',
            surname='Check',
            email='auth.check@example.com',
            role='reader',
        )
        reader.set_password('Secret123!')

        assert reader.check_password('Secret123!') is True
        assert reader.check_password('wrong-password') is False


def test_reader_email_is_unique_constraint(app):
    with app.app_context():
        first = Reader(
            name='First',
            surname='User',
            email='unique.reader@example.com',
            role='reader',
        )
        first.set_password('Secret123!')
        db.session.add(first)
        db.session.commit()

        duplicate = Reader(
            name='Second',
            surname='User',
            email='unique.reader@example.com',
            role='reader',
        )
        duplicate.set_password('Secret123!')
        db.session.add(duplicate)

        with pytest.raises(IntegrityError):
            db.session.commit()

        db.session.rollback()
