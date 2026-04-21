from flask_wtf import FlaskForm
from wtforms import BooleanField, IntegerField, PasswordField, RadioField, SelectField, StringField, SubmitField, TextAreaField
from wtforms.validators import DataRequired, Email, EqualTo, InputRequired, Length, NumberRange, Optional


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


class ReviewForm(FlaskForm):
    text = TextAreaField('Your review', validators=[DataRequired()])
    stars = RadioField(
        'Stars',
        choices=[('1', '1'), ('2', '2'), ('3', '3'), ('4', '4'), ('5', '5')],
        coerce=int,
        validators=[DataRequired()],
    )
    submit = SubmitField('Add review')


class AnnotationForm(FlaskForm):
    text = TextAreaField('Your annotation', validators=[DataRequired()])
    submit = SubmitField('Save annotation')


class BookCreateForm(FlaskForm):
    title = StringField('Title', validators=[DataRequired(), Length(max=80)])
    author_name = StringField('Author name', validators=[DataRequired(), Length(max=50)])
    author_surname = StringField('Author surname', validators=[DataRequired(), Length(max=80)])
    original_language = StringField('Original language', validators=[DataRequired(), Length(max=80)])
    translation_language = StringField('Translation language', validators=[DataRequired(), Length(max=80)])
    first_publication = StringField('First publication', validators=[DataRequired(), Length(max=120)])
    genre = TextAreaField('Genre', validators=[DataRequired(), Length(max=160)])
    month = SelectField(
        'Suggested month',
        choices=[
            ('January', 'January'),
            ('February', 'February'),
            ('March', 'March'),
            ('April', 'April'),
            ('May', 'May'),
            ('June', 'June'),
            ('July', 'July'),
            ('August', 'August'),
            ('September', 'September'),
            ('October', 'October'),
            ('November', 'November'),
            ('December', 'December'),
        ],
        validators=[DataRequired()],
    )
    year = IntegerField('Suggested year', validators=[InputRequired(), NumberRange(min=1, max=9999)])
    cover_image = StringField('Cover image path', validators=[Optional(), Length(max=255)])
    is_hidden = BooleanField('Create as hidden')
    submit = SubmitField('Create book')


class BookUpdateForm(FlaskForm):
    title = StringField('Title', validators=[DataRequired(), Length(max=80)])
    author_name = StringField('Author name', validators=[DataRequired(), Length(max=50)])
    author_surname = StringField('Author surname', validators=[DataRequired(), Length(max=80)])
    original_language = StringField('Original language', validators=[DataRequired(), Length(max=80)])
    translation_language = StringField('Translation language', validators=[DataRequired(), Length(max=80)])
    first_publication = StringField('First publication', validators=[DataRequired(), Length(max=120)])
    genre = TextAreaField('Genre', validators=[DataRequired(), Length(max=160)])
    month = SelectField(
        'Suggested month',
        choices=[
            ('January', 'January'),
            ('February', 'February'),
            ('March', 'March'),
            ('April', 'April'),
            ('May', 'May'),
            ('June', 'June'),
            ('July', 'July'),
            ('August', 'August'),
            ('September', 'September'),
            ('October', 'October'),
            ('November', 'November'),
            ('December', 'December'),
        ],
        validators=[DataRequired()],
    )
    year = IntegerField('Suggested year', validators=[InputRequired(), NumberRange(min=1, max=9999)])
    cover_image = StringField('Cover image path', validators=[Optional(), Length(max=255)])
    is_hidden = BooleanField('Hidden')
    submit = SubmitField('Save changes')


class BookContentForm(FlaskForm):
    html_content = TextAreaField('Book HTML', validators=[DataRequired()])
    submit = SubmitField('Save content')
