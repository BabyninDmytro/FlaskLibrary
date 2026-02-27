from sqlalchemy import select

from app.extensions import db
from app.models import Reader


def get_reader_or_404(user_id, description='There is no user with this ID.'):
    return db.first_or_404(select(Reader).filter_by(id=user_id), description=description)


def get_reader_by_email(email):
    stmt = select(Reader).filter_by(email=email)
    return db.session.execute(stmt).scalar_one_or_none()


def serialize_reader(reader):
    return {
        'id': reader.id,
        'name': reader.name,
        'surname': reader.surname,
        'email': reader.email,
        'role': reader.role,
        'joined_at': reader.joined_at.isoformat() if reader.joined_at else None,
    }
