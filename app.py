from datetime import datetime
import os, logging
from flask import Flask, flash, redirect, render_template, request, url_for
from flask_login import LoginManager, UserMixin, login_required, login_user, logout_user
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm
from werkzeug.security import check_password_hash, generate_password_hash
from wtforms import BooleanField, PasswordField, SelectField, StringField, SubmitField
from wtforms.validators import DataRequired, Email, EqualTo


logging.basicConfig(level=logging.DEBUG, format='%(levelname)s: %(message)s')

base_dir = os.path.abspath(os.path.dirname(__file__))
instance_dir = os.path.join(base_dir, 'instance')
app = Flask(__name__, instance_relative_config=True, instance_path=instance_dir)
app.config['SECRET_KEY'] = 'you-will-never-guess'

os.makedirs(app.instance_path, exist_ok=True)
db_path = os.path.join(app.instance_path, 'myDB.db')
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False #to supress warning

db = SQLAlchemy(app)

if os.path.exists(db_path):
    logging.info('DB ' + db_path + 'is exists')
else:
    logging.info('DB ' + db_path + 'is not exists')

login_manager = LoginManager()
login_manager.login_view = 'login'
login_manager.init_app(app)

#declaring the Book model
class Book(db.Model):
    id = db.Column(db.Integer, primary_key = True) #primary key column
    title = db.Column(db.String(80), index = True, unique = True) # book title
    author_name = db.Column(db.String(50), index = True, unique = False)
    author_surname = db.Column(db.String(80), index = True, unique = False) #author surname
    month = db.Column(db.String(20), index = True, unique = False) #the month of the book suggestion
    year = db.Column(db.Integer, index = True, unique = False) #the year of the book suggestion
    reviews = db.relationship('Review', backref = 'book', lazy = 'dynamic', cascade = "all, delete, delete-orphan") #relationship of Books and Reviews
    annotations = db.relationship('Annotation', backref='book', lazy='dynamic', cascade = "all, delete, delete-orphan")
    #Get a nice printout for Book objects
    def __repr__(self):
        return "{} in: {},{}".format(self.id, self.month, self.year)

#Add your columns for the Reader model here below.
class Reader(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key = True)
    name = db.Column(db.String(50), index = True, unique = False)
    surname = db.Column(db.String(80), unique = False, index = True)
    email = db.Column(db.String(120), unique = True, index = True)
    password_hash = db.Column(db.String(128))
    role = db.Column(db.String(20), index=True, default='reader')
    joined_at = db.Column(db.DateTime(), default=datetime.utcnow, index=True)
    reviews = db.relationship('Review', backref='reviewer', lazy = 'dynamic', cascade = "all, delete, delete-orphan")
    annotations = db.relationship('Annotation', backref='author', lazy='dynamic', cascade = "all, delete, delete-orphan")
    #get a nice printout for Reader objects
    def __repr__(self):
        return "Reader ID: {}, email: {}".format(self.id, self.email)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

#declaring the Review model
class Review(db.Model):
    id = db.Column(db.Integer, primary_key = True) #primary key column, automatically generated IDs
    stars = db.Column(db.Integer, unique = False) #a review's rating
    text = db.Column(db.String(200), unique = False) #a review's text
    book_id = db.Column(db.Integer, db.ForeignKey('book.id')) #foreign key column
    reviewer_id = db.Column(db.Integer, db.ForeignKey('reader.id'))
    #get a nice printout for Review objects
    def __repr__(self):
        return "Review ID: {}, {} stars {}".format(self.id, self.stars, self.book_id)

#declaring the Annotation model
class Annotation(db.Model):
    id = db.Column(db.Integer, primary_key = True)
    text = db.Column(db.String(200), unique = False)
    reviewer_id = db.Column(db.Integer, db.ForeignKey('reader.id'))
    book_id = db.Column(db.Integer, db.ForeignKey('book.id'))
    #get a nice printout for Annotation objects
    def __repr__(self):
        return '<Annotation {}-{}:{} >'.format(self.reviewer_id, self.book_id, self.text)

class RegistrationForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired()])
    surname = StringField('Surname', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired(), Email()])
    role = SelectField(
        'Role',
        choices=[('reader', 'Reader'), ('librarian', 'Librarian')],
        validators=[DataRequired()],
    )
    password = PasswordField('Password', validators=[DataRequired()])
    password2 = PasswordField('Repeat Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Register')


class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember = BooleanField('Remember Me')
    submit = SubmitField('Login')


@login_manager.user_loader
def load_user(user_id):
    return db.session.get(Reader, int(user_id))


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
