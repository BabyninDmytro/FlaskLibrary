from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required, login_user, logout_user
from sqlalchemy import String, and_, cast, or_

from app.extensions import db
from app.forms import LoginForm, RegistrationForm, ReviewForm
from app.models import Book, Reader, Review


bp = Blueprint('main', __name__)



@bp.route('/', methods=['GET'])
def init():
    if current_user.is_authenticated:
        return redirect(url_for('main.home'))

    return redirect(url_for('main.login'))


@bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.home'))

    form = LoginForm()
    if form.validate_on_submit():
        user = Reader.query.filter_by(email=form.email.data).first()
        if user and user.check_password(form.password.data):
            login_user(user, remember=form.remember.data)
            return redirect(url_for('main.home'))
        flash('Invalid email or password.', 'error')
    return render_template('login.html', form=form)


@bp.route('/register', methods=['GET', 'POST'])
def register():
    form = RegistrationForm()
    if form.validate_on_submit():
        existing_user = Reader.query.filter_by(email=form.email.data).first()
        if existing_user:
            flash('Email already registered.', 'error')
        else:
            reader = Reader(name=form.name.data, surname=form.surname.data, email=form.email.data, role=form.role.data)
            reader.set_password(form.password.data)
            db.session.add(reader)
            db.session.commit()
            login_user(reader)
            db.session.close()
            return redirect(url_for('main.home'))
    return render_template('register.html', title='Register', form=form)


@bp.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('main.login'))


@bp.route('/home')
@login_required
def home():
    if not current_user.is_authenticated:
        return redirect(url_for('main.login'))

    search_query = request.args.get('search', '').strip()
    page = request.args.get('page', 1, type=int)

    query = Book.query

    if search_query:
        terms = [term for term in search_query.split() if term]
        term_filters = []

        for term in terms:
            lookup = f'%{term}%'
            term_filters.append(
                or_(
                    Book.title.ilike(lookup),
                    Book.author_name.ilike(lookup),
                    Book.author_surname.ilike(lookup),
                    Book.month.ilike(lookup),
                    cast(Book.year, String).ilike(lookup),
                )
            )

        if term_filters:
            query = query.filter(and_(*term_filters))

    books = query.order_by(Book.year.desc(), Book.month.asc(), Book.title.asc()).paginate(page=page, per_page=10, error_out=False)

    return render_template('home.html', books=books, search_query=search_query)


@bp.route('/profile/<int:user_id>')
def profile(user_id):
    reader = Reader.query.filter_by(id=user_id).first_or_404(description="There is no user with this ID.")
    return render_template('profile.html', reader=reader)


@bp.route('/books/<year>')
def books(year):
    books = Book.query.filter_by(year=year)
    return render_template('display_books.html', year=year, books=books)


@bp.route('/reviews/<int:review_id>')
def reviews(review_id):
    review = Review.query.filter_by(id=review_id).first_or_404(description="There is no user with this ID.")
    return render_template('_review.html', review=review)


@bp.route('/book/<int:book_id>', methods=['GET', 'POST'])
def book(book_id):
    book = Book.query.filter_by(id=book_id).first_or_404(description="There is no book with this ID.")
    form = ReviewForm()

    if form.validate_on_submit():
        if not current_user.is_authenticated:
            flash('Please log in to add a review.', 'error')
            return redirect(url_for('main.login'))

        review = Review(text=form.text.data.strip(), stars=5, book_id=book.id, reviewer_id=current_user.id)
        db.session.add(review)
        db.session.commit()
        return redirect(url_for('main.book', book_id=book.id))

    return render_template('book.html', book=book, form=form)
