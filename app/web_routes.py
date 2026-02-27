from flask import Blueprint, current_app, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required, login_user, logout_user
from jinja2 import TemplateNotFound
from werkzeug.exceptions import NotFound

from app.extensions import db
from app.forms import AnnotationForm, LoginForm, RegistrationForm, ReviewForm
from app.models import Reader
from app.services.annotation_service import create_annotation, list_book_annotations_desc
from app.services.book_service import get_book_or_404, paginate_books
from app.services.reader_service import get_reader_by_email, get_reader_or_404
from app.services.review_service import create_review, get_review_or_404, list_book_reviews_desc


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
        user = get_reader_by_email(form.email.data)
        if user and user.check_password(form.password.data):
            login_user(user, remember=form.remember.data)
            return redirect(url_for('main.home'))
        flash('Invalid email or password.', 'error')
    return render_template('login.html', form=form)


@bp.route('/register', methods=['GET', 'POST'])
def register():
    form = RegistrationForm()
    if form.validate_on_submit():
        existing_user = get_reader_by_email(form.email.data)
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
    books = paginate_books(search_query=search_query, page=page, per_page=10)

    return render_template('home.html', books=books, search_query=search_query)


@bp.route('/profile/<int:user_id>')
@login_required
def profile(user_id):
    reader = get_reader_or_404(user_id)
    return render_template('profile.html', reader=reader)


@bp.route('/reviews/<int:review_id>')
@login_required
def reviews(review_id):
    review = get_review_or_404(review_id, description="There is no user with this ID.")
    return render_template('_review.html', review=review)


@bp.route('/book/<int:book_id>', methods=['GET', 'POST'])
def book(book_id):
    try:
        book = get_book_or_404(book_id)
    except NotFound:
        if not current_user.is_authenticated:
            return redirect(url_for('main.login'))
        raise
    review_form = ReviewForm(prefix='review')
    annotation_form = AnnotationForm(prefix='annotation')

    if review_form.submit.data and review_form.validate_on_submit():
        if not current_user.is_authenticated:
            flash('Please log in to add a review.', 'error')
            return redirect(url_for('main.login'))

        create_review(
            text=review_form.text.data,
            stars=review_form.stars.data,
            book_id=book.id,
            reviewer_id=current_user.id,
        )
        return redirect(url_for('main.book', book_id=book.id))

    if annotation_form.submit.data and annotation_form.validate_on_submit():
        if not current_user.is_authenticated:
            flash('Please log in to add an annotation.', 'error')
            return redirect(url_for('main.login'))

        if current_user.role != 'librarian':
            flash('Only librarians can add annotations.', 'error')
            return redirect(url_for('main.home'))

        create_annotation(text=annotation_form.text.data, book_id=book.id, reviewer_id=current_user.id)
        return redirect(url_for('main.book', book_id=book.id))

    reviews = list_book_reviews_desc(book)

    return render_template(
        'book.html',
        book=book,
        review_form=review_form,
        annotation_form=annotation_form,
        reviews=reviews,
        is_librarian=current_user.is_authenticated and current_user.role == 'librarian',
    )


@bp.route('/book/<int:book_id>/read')
def book_read(book_id):
    try:
        book = get_book_or_404(book_id)
    except NotFound:
        if not current_user.is_authenticated:
            return redirect(url_for('main.login'))
        raise
    annotations = list_book_annotations_desc(book)

    book_template = f'book_reads/book_{book.id}_read.html'
    try:
        current_app.jinja_env.loader.get_source(current_app.jinja_env, book_template)
        return render_template(
            book_template,
            book=book,
            annotations=annotations,
            is_librarian=current_user.is_authenticated and current_user.role == 'librarian',
        )
    except TemplateNotFound:
        pass

    return render_template(
        'book_reads/book_default_read.html',
        book=book,
        annotations=annotations,
        is_librarian=current_user.is_authenticated and current_user.role == 'librarian',
    )


@bp.route('/book/<int:book_id>/toggle-hidden', methods=['POST'])
@login_required
def toggle_book_hidden(book_id):
    if current_user.role != 'librarian':
        flash('Only librarians can change visibility.', 'error')
        return redirect(url_for('main.home'))

    target_book = get_book_or_404(book_id)
    target_book.is_hidden = not target_book.is_hidden
    db.session.commit()
    return redirect(url_for('main.book', book_id=target_book.id))
