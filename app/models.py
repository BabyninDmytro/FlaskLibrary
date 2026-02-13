from datetime import datetime

from flask_login import UserMixin
from werkzeug.security import check_password_hash, generate_password_hash

from app.extensions import db


class Book(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(80), index=True, unique=True)
    author_name = db.Column(db.String(50), index=True, unique=False)
    author_surname = db.Column(db.String(80), index=True, unique=False)
    month = db.Column(db.String(20), index=True, unique=False)
    year = db.Column(db.Integer, index=True, unique=False)
    cover_image = db.Column(db.String(255), nullable=False, default='book_covers/default.svg')
    reviews = db.relationship('Review', backref='book', lazy='dynamic', cascade="all, delete, delete-orphan")
    annotations = db.relationship('Annotation', backref='book', lazy='dynamic', cascade="all, delete, delete-orphan")

    def __repr__(self):
        return "{} in: {},{}".format(self.id, self.month, self.year)


class Reader(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), index=True, unique=False)
    surname = db.Column(db.String(80), unique=False, index=True)
    email = db.Column(db.String(120), unique=True, index=True)
    password_hash = db.Column(db.String(128))
    role = db.Column(db.String(20), index=True, default='reader')
    joined_at = db.Column(db.DateTime(), default=datetime.utcnow, index=True)
    reviews = db.relationship('Review', backref='reviewer', lazy='dynamic', cascade="all, delete, delete-orphan")
    annotations = db.relationship('Annotation', backref='author', lazy='dynamic', cascade="all, delete, delete-orphan")

    def __repr__(self):
        return "Reader ID: {}, email: {}".format(self.id, self.email)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class Review(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    stars = db.Column(db.Integer, unique=False)
    text = db.Column(db.String(200), unique=False)
    book_id = db.Column(db.Integer, db.ForeignKey('book.id'))
    reviewer_id = db.Column(db.Integer, db.ForeignKey('reader.id'))

    def __repr__(self):
        return "Review ID: {}, {} stars {}".format(self.id, self.stars, self.book_id)


class Annotation(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    text = db.Column(db.String(200), unique=False)
    reviewer_id = db.Column(db.Integer, db.ForeignKey('reader.id'))
    book_id = db.Column(db.Integer, db.ForeignKey('book.id'))

    def __repr__(self):
        return '<Annotation {}-{}:{} >'.format(self.reviewer_id, self.book_id, self.text)
