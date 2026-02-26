from app.extensions import db
from app.models import Review


def list_book_reviews_desc(book):
    return book.reviews.order_by(Review.id.desc()).all()


def get_review_or_404(review_id, description='There is no review with this ID.'):
    return Review.query.filter_by(id=review_id).first_or_404(description=description)


def get_review(review_id):
    return Review.query.filter_by(id=review_id).first()


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
