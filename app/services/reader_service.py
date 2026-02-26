from app.models import Reader


def get_reader_or_404(user_id, description='There is no user with this ID.'):
    return Reader.query.filter_by(id=user_id).first_or_404(description=description)


def get_reader_by_email(email):
    return Reader.query.filter_by(email=email).first()


def serialize_reader(reader):
    return {
        'id': reader.id,
        'name': reader.name,
        'surname': reader.surname,
        'email': reader.email,
        'role': reader.role,
        'joined_at': reader.joined_at.isoformat() if reader.joined_at else None,
    }
