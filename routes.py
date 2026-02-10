from flask import flash, redirect, render_template, url_for
from flask_login import login_required, login_user, logout_user

from app import app, db
from forms import LoginForm, RegistrationForm
from models import Book, Reader, Review


@app.route('/', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = Reader.query.filter_by(email=form.email.data).first()
        if user and user.check_password(form.password.data):
            login_user(user, remember=form.remember.data)
            return redirect(url_for('home'))
        flash('Invalid email or password.', 'error')
    return render_template('login.html', form=form)


@app.route('/register', methods=['GET', 'POST'])
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
            db.session.close()
            login_user(reader)
            return redirect(url_for('home'))
    return render_template('register.html', title='Register', form=form)


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))


@app.route('/home')
@login_required
def home():
    books = Book.query.all()
    return render_template('home.html', books=books)


@app.route('/profile/<int:user_id>')
def profile(user_id):
    reader = Reader.query.filter_by(id=user_id).first_or_404(description="There is no user with this ID.")
    return render_template('profile.html', reader=reader)


@app.route('/books/<year>')
def books(year):
    books = Book.query.filter_by(year=year)
    return render_template('display_books.html', year=year, books=books)


@app.route('/reviews/<int:review_id>')
def reviews(review_id):
    review = Review.query.filter_by(id=review_id).first_or_404(description="There is no user with this ID.")
    return render_template('_review.html', review=review)


@app.route('/book/<int:book_id>')
def book(book_id):
    book = Book.query.filter_by(id=book_id).first_or_404(description="There is no book with this ID.")
    return render_template('book.html', book=book)
