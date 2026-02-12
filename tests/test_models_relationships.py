from app.extensions import db
from app.models import Annotation, Book, Reader, Review


def test_deleting_book_cascades_to_reviews_and_annotations(app):
    with app.app_context():
        reader = Reader(
            name='Cascade',
            surname='Reader',
            email='cascade.reader@example.com',
            role='reader',
        )
        reader.set_password('Secret123!')

        book = Book(
            title='Cascade Book',
            author_name='Iryna',
            author_surname='K',
            month='June',
            year=2024,
        )
        db.session.add_all([reader, book])
        db.session.commit()

        review = Review(stars=5, text='Great', book_id=book.id, reviewer_id=reader.id)
        annotation = Annotation(text='Important note', book_id=book.id, reviewer_id=reader.id)
        db.session.add_all([review, annotation])
        db.session.commit()

        assert Review.query.filter_by(book_id=book.id).count() == 1
        assert Annotation.query.filter_by(book_id=book.id).count() == 1

        db.session.delete(book)
        db.session.commit()

        assert Review.query.filter_by(book_id=book.id).count() == 0
        assert Annotation.query.filter_by(book_id=book.id).count() == 0
