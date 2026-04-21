from flask import Blueprint, flash, jsonify, redirect, render_template, request, url_for
from flask_login import current_user, login_required, login_user, logout_user
from werkzeug.exceptions import NotFound

from app.extensions import db
from app.forms import AnnotationForm, LoginForm, RegistrationForm, ReviewForm
from app.models import Book, Reader
from app.services.annotation_service import (
    create_annotation,
    delete_annotation as delete_annotation_service,
    get_annotation,
    list_book_annotations_desc,
    update_annotation as update_annotation_service,
)
from app.services.access_policy import (
    can_create_annotation,
    can_create_review,
    can_delete_annotation,
    can_delete_review,
    can_update_annotation,
    can_update_review,
    can_view_hidden_books,
    is_librarian,
)
from app.services.book_service import get_book_or_404, paginate_books
from app.services.book_text_service import load_book_read_content, load_book_text_preview
from app.services.reader_service import get_reader_by_email, get_reader_or_404
from app.services.review_service import (
    create_review,
    delete_review as delete_review_service,
    get_review,
    get_review_or_404,
    list_book_reviews_desc,
    update_review as update_review_service,
)


bp = Blueprint('main', __name__)

def _is_librarian():
    return is_librarian(current_user)


def _render_hidden_book_access_denied():
    return (
        render_template(
            'hidden_book_access_denied.html',
            home_url=url_for('main.home'),
            logout_url=url_for('main.logout'),
        ),
        403,
    )


def _render_book_not_found(book_id):
    return (
        render_template(
            'book_not_found.html',
            book_id=book_id,
            home_url=url_for('main.home'),
            logout_url=url_for('main.logout'),
        ),
        404,
    )


@bp.app_context_processor
def inject_role_flags():
    return {'is_librarian': _is_librarian()}



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
    books = paginate_books(
        search_query=search_query,
        page=page,
        per_page=10,
        include_hidden=can_view_hidden_books(current_user),
    )

    return render_template('home.html', books=books, search_query=search_query, is_librarian=_is_librarian())


@bp.route('/profile/<int:user_id>')
@login_required
def profile(user_id):
    reader = get_reader_or_404(user_id)
    return render_template('profile.html', reader=reader)


@bp.route('/reviews/<int:review_id>')
@login_required
def reviews(review_id):
    review = get_review_or_404(review_id, description="There is no user with this ID.")
    return render_template('_review.html', review=review, is_librarian=_is_librarian())


@bp.route('/book/<int:book_id>', methods=['GET', 'POST'])
@login_required
def book(book_id):
    try:
        book = get_book_or_404(book_id, include_hidden=can_view_hidden_books(current_user))
    except NotFound:
        if not current_user.is_authenticated:
            return redirect(url_for('main.login'))
        hidden_book = db.session.get(Book, book_id)
        if hidden_book and hidden_book.is_hidden and not can_view_hidden_books(current_user):
            return _render_hidden_book_access_denied()
        return _render_book_not_found(book_id)
    review_form = ReviewForm(prefix='review')
    annotation_form = AnnotationForm(prefix='annotation')

    if review_form.submit.data and review_form.validate_on_submit():
        if not can_create_review(current_user):
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

        if not can_create_annotation(current_user):
            flash('Only librarians can add annotations.', 'error')
            return redirect(url_for('main.home'))

        create_annotation(text=annotation_form.text.data, book_id=book.id, reviewer_id=current_user.id)
        return redirect(url_for('main.book', book_id=book.id))

    reviews = list_book_reviews_desc(book)
    book_text_preview = load_book_text_preview(book.id)

    return render_template(
        'book.html',
        book=book,
        review_form=review_form,
        annotation_form=annotation_form,
        reviews=reviews,
        book_text_preview=book_text_preview,
        is_librarian=_is_librarian(),
    )


@bp.route('/book/<int:book_id>/read')
@login_required
def book_read(book_id):
    try:
        book = get_book_or_404(book_id, include_hidden=can_view_hidden_books(current_user))
    except NotFound:
        if not current_user.is_authenticated:
            return redirect(url_for('main.login'))
        hidden_book = db.session.get(Book, book_id)
        if hidden_book and hidden_book.is_hidden and not can_view_hidden_books(current_user):
            return _render_hidden_book_access_denied()
        return _render_book_not_found(book_id)
    annotations = list_book_annotations_desc(book)
    read_content = load_book_read_content(book.id)

    return render_template(
        'book_reads/book_default_read.html',
        book=book,
        annotations=annotations,
        read_content=read_content,
        is_librarian=_is_librarian(),
    )


@bp.route('/book/<int:book_id>/toggle-hidden', methods=['POST'])
@login_required
def toggle_book_hidden(book_id):
    if not _is_librarian():
        return jsonify({'error': 'Only librarians can change visibility.'}), 403

    target_book = get_book_or_404(book_id)
    target_book.is_hidden = not target_book.is_hidden
    db.session.commit()

    return jsonify(
        {
            'book_id': target_book.id,
            'is_hidden': target_book.is_hidden,
            'button_label': 'Unhide book' if target_book.is_hidden else 'Hide book',
            'button_label_short': 'Unhide' if target_book.is_hidden else 'Hide',
        }
    )


@bp.route('/reviews/<int:review_id>/delete', methods=['POST'], endpoint='delete_review')
@login_required
def delete_review(review_id):
    review = get_review(review_id)
    if review is None:
        flash('Review not found.', 'error')
        return redirect(url_for('main.home'))
    if not can_delete_review(current_user, review):
        flash('You can delete only your own review unless you are a librarian.', 'error')
        return redirect(url_for('main.home'))

    delete_review_service(review)
    return redirect(request.referrer or url_for('main.book', book_id=review.book_id))


@bp.route('/annotations/<int:annotation_id>/delete', methods=['POST'], endpoint='delete_annotation')
@login_required
def delete_annotation(annotation_id):
    if not can_delete_annotation(current_user):
        flash('Only librarians can delete annotations.', 'error')
        return redirect(url_for('main.home'))

    annotation = get_annotation(annotation_id)
    if annotation is None:
        flash('Annotation not found.', 'error')
        return redirect(url_for('main.home'))

    book_id = annotation.book_id
    delete_annotation_service(annotation)
    return redirect(request.referrer or url_for('main.book_read', book_id=book_id))


@bp.route('/reviews/<int:review_id>/edit', methods=['POST'])
@login_required
def edit_review(review_id):
    if not can_update_review(current_user):
        flash('Only librarians can edit reviews.', 'error')
        return redirect(url_for('main.home'))

    review = get_review(review_id)
    if review is None:
        flash('Review not found.', 'error')
        return redirect(url_for('main.home'))

    text = request.form.get('text', '').strip()
    stars = request.form.get('stars', type=int)

    if not text:
        flash('Review text is required.', 'error')
        return redirect(request.referrer or url_for('main.book', book_id=review.book_id))
    if len(text) > 200:
        flash('Review text must be at most 200 characters.', 'error')
        return redirect(request.referrer or url_for('main.book', book_id=review.book_id))
    if stars not in (1, 2, 3, 4, 5):
        flash('Review stars must be between 1 and 5.', 'error')
        return redirect(request.referrer or url_for('main.book', book_id=review.book_id))

    update_review_service(review, {'text': text, 'stars': stars})
    return redirect(request.referrer or url_for('main.book', book_id=review.book_id))


@bp.route('/annotations/<int:annotation_id>/edit', methods=['POST'])
@login_required
def edit_annotation(annotation_id):
    if not can_update_annotation(current_user):
        flash('Only librarians can edit annotations.', 'error')
        return redirect(url_for('main.home'))

    annotation = get_annotation(annotation_id)
    if annotation is None:
        flash('Annotation not found.', 'error')
        return redirect(url_for('main.home'))

    text = request.form.get('text', '').strip()
    if not text:
        flash('Annotation text is required.', 'error')
        return redirect(request.referrer or url_for('main.book_read', book_id=annotation.book_id))
    if len(text) > 200:
        flash('Annotation text must be at most 200 characters.', 'error')
        return redirect(request.referrer or url_for('main.book_read', book_id=annotation.book_id))

    update_annotation_service(annotation, text)
    return redirect(request.referrer or url_for('main.book_read', book_id=annotation.book_id))
