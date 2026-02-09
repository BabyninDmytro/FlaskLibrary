from app import app
from app import db, Reader, Book, Review, Annotation
from flask import render_template, request, url_for, redirect
from flask_login import login_required

@app.route('/home')
@login_required
def home():
  books = Book.query.all()
  return render_template('home.html', books = books)

@app.route('/profile/<int:user_id>')
def profile(user_id):
   reader = Reader.query.filter_by(id = user_id).first_or_404(description = "There is no user with this ID.")
   return render_template('profile.html', reader = reader)

@app.route('/books/<year>')
def books(year):
   books = Book.query.filter_by(year = year)
   return render_template('display_books.html', year = year, books = books)

@app.route('/reviews/<int:review_id>')
def reviews(review_id):
   review = Review.query.filter_by(id = review_id).first_or_404(description = "There is no user with this ID.")
   return render_template('_review.html', review = review)

@app.route('/book/<int:book_id>')
def book(book_id):
   book = Book.query.filter_by(id = book_id).first_or_404(description = "There is no book with this ID.")
   return render_template('book.html', book = book)


if __name__ == "__main__":
    app.run(debug=True)
