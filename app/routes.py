from flask import Blueprint, current_app, flash, redirect, render_template, request, session, url_for
from flask_login import current_user, login_required, login_user, logout_user
from jinja2 import TemplateNotFound
from sqlalchemy import String, and_, cast, or_

from app.extensions import db
from app.forms import AnnotationForm, LoginForm, RegistrationForm, ReviewForm
from app.models import Annotation, Book, Reader, Review


bp = Blueprint('main', __name__)


def _is_librarian(user):
    if not user.is_authenticated:
        return False

    user_id = session.get('_user_id')
    if not user_id:
        return False

    persisted_user = db.session.get(Reader, int(user_id))
    return persisted_user is not None and persisted_user.role == 'librarian'



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
    is_librarian = _is_librarian(current_user)

    if not is_librarian:
        query = query.filter_by(is_hidden=False)

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

    return render_template('home.html', books=books, search_query=search_query, is_librarian=is_librarian)


@bp.route('/profile/<int:user_id>')
@login_required
def profile(user_id):
    reader = Reader.query.filter_by(id=user_id).first_or_404(description="There is no user with this ID.")
    return render_template('profile.html', reader=reader)


@bp.route('/books/<year>')
@login_required
def books(year):
    books = Book.query.filter_by(year=year)
    is_librarian = _is_librarian(current_user)
    if not is_librarian:
        books = books.filter_by(is_hidden=False)
    return render_template('display_books.html', year=year, books=books, is_librarian=is_librarian)


@bp.route('/reviews/<int:review_id>')
@login_required
def reviews(review_id):
    review = Review.query.filter_by(id=review_id).first_or_404(description="There is no user with this ID.")
    return render_template('_review.html', review=review, is_librarian=_is_librarian(current_user))


@bp.route('/book/<int:book_id>', methods=['GET', 'POST'])
@login_required
def book(book_id):
    book = Book.query.filter_by(id=book_id).first_or_404(description="There is no book with this ID.")
    is_librarian = _is_librarian(current_user)
    if book.is_hidden and not is_librarian:
        return redirect(url_for('main.home'))
    review_form = ReviewForm(prefix='review')
    annotation_form = AnnotationForm(prefix='annotation')

    if review_form.submit.data and review_form.validate_on_submit():
        if not current_user.is_authenticated:
            flash('Please log in to add a review.', 'error')
            return redirect(url_for('main.login'))

        review = Review(
            text=review_form.text.data.strip(),
            stars=review_form.stars.data,
            book_id=book.id,
            reviewer_id=current_user.id,
        )
        db.session.add(review)
        db.session.commit()
        return redirect(url_for('main.book', book_id=book.id))

    if annotation_form.submit.data and annotation_form.validate_on_submit():
        if not current_user.is_authenticated:
            flash('Please log in to add an annotation.', 'error')
            return redirect(url_for('main.login'))

        if not is_librarian:
            return redirect(url_for('main.home'))

        annotation = Annotation(text=annotation_form.text.data.strip(), book_id=book.id, reviewer_id=current_user.id)
        db.session.add(annotation)
        db.session.commit()
        return redirect(url_for('main.book', book_id=book.id))

    reviews = book.reviews.order_by(Review.id.desc()).all()

    return render_template(
        'book.html',
        book=book,
        review_form=review_form,
        annotation_form=annotation_form,
        reviews=reviews,
        is_librarian=is_librarian,
    )


@bp.route('/book/<int:book_id>/read')
@login_required
def book_read(book_id):
    book = Book.query.filter_by(id=book_id).first_or_404(description="There is no book with this ID.")
    is_librarian = _is_librarian(current_user)
    if book.is_hidden and not is_librarian:
        return redirect(url_for('main.home'))
    annotations = book.annotations.order_by(Annotation.id.desc()).all()

    book_template = f'book_reads/book_{book.id}_read.html'
    try:
        current_app.jinja_env.loader.get_source(current_app.jinja_env, book_template)
        return render_template(book_template, book=book, annotations=annotations, is_librarian=is_librarian)
    except TemplateNotFound:
        pass

    return render_template('book_reads/book_default_read.html', book=book, annotations=annotations, is_librarian=is_librarian)


@bp.route('/book/<int:book_id>/toggle-hidden', methods=['POST'])
@login_required
def toggle_book_hidden(book_id):
    if not _is_librarian(current_user):
        return redirect(url_for('main.home'))

    book = Book.query.filter_by(id=book_id).first_or_404(description="There is no book with this ID.")
    book.is_hidden = not book.is_hidden
    db.session.commit()

    return redirect(request.referrer or url_for('main.book', book_id=book.id))


@bp.route('/reviews/<int:review_id>/delete', methods=['POST'])
@login_required
def delete_review(review_id):
    if not _is_librarian(current_user):
        return redirect(url_for('main.home'))

    review = Review.query.filter_by(id=review_id).first_or_404(description="There is no review with this ID.")
    book_id = review.book_id
    db.session.delete(review)
    db.session.commit()

    return redirect(request.referrer or url_for('main.book', book_id=book_id))


@bp.route('/annotations/<int:annotation_id>/delete', methods=['POST'])
@login_required
def delete_annotation(annotation_id):
    if not _is_librarian(current_user):
        return redirect(url_for('main.home'))

    annotation = Annotation.query.filter_by(id=annotation_id).first_or_404(description="There is no annotation with this ID.")
    book_id = annotation.book_id
    db.session.delete(annotation)
    db.session.commit()

    return redirect(request.referrer or url_for('main.book_read', book_id=book_id))
