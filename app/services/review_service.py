from sqlalchemy import select

from app.extensions import db
from app.models import Review


def list_book_reviews_desc(book):
    stmt = select(Review).filter_by(book_id=book.id).order_by(Review.id.desc())
    return db.session.execute(stmt).scalars().all()


def get_review_or_404(review_id, description='There is no review with this ID.'):
    return db.first_or_404(select(Review).filter_by(id=review_id), description=description)


def get_review(review_id):
    stmt = select(Review).filter_by(id=review_id)
    return db.session.execute(stmt).scalar_one_or_none()


def create_review(text, stars, book_id, reviewer_id):
    review = Review(text=text.strip(), stars=stars, book_id=book_id, reviewer_id=reviewer_id)
    db.session.add(review)
    db.session.commit()
    return review


def update_review(review, updates):
    for key, value in updates.items():
        setattr(review, key, value)
    db.session.commit()
    return review


def delete_review(review):
    db.session.delete(review)
    db.session.commit()


def serialize_review(review):
    return {
        'id': review.id,
        'stars': review.stars,
        'text': review.text,
        'book_id': review.book_id,
        'reviewer_id': review.reviewer_id,
    }
