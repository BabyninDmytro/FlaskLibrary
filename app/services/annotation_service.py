from app.extensions import db
from app.models import Annotation


def list_book_annotations_desc(book):
    return book.annotations.order_by(Annotation.id.desc()).all()


def get_annotation(annotation_id):
    return Annotation.query.filter_by(id=annotation_id).first()


def create_annotation(text, book_id, reviewer_id):
    annotation = Annotation(text=text.strip(), book_id=book_id, reviewer_id=reviewer_id)
    db.session.add(annotation)
    db.session.commit()
    return annotation


def update_annotation(annotation, text):
    annotation.text = text
    db.session.commit()
    return annotation


def delete_annotation(annotation):
    db.session.delete(annotation)
    db.session.commit()


def serialize_annotation(annotation):
    return {
        'id': annotation.id,
        'text': annotation.text,
        'book_id': annotation.book_id,
        'reviewer_id': annotation.reviewer_id,
    }
