import os

from app import create_app
from app.db_schema import ensure_database_schema
from app.extensions import db
from app.models import Annotation, Book, Reader, Review


app = create_app()
DEFAULT_PASSWORD = 'Secret123!'


def safe_commit():
    try:
        db.session.commit()
    except Exception:
        db.session.rollback()


with app.app_context():
    db_path = os.path.join(app.instance_path, 'myDB.db')
    os.makedirs(app.instance_path, exist_ok=True)
    db.session.remove()
    db.engine.dispose()
    if os.path.exists(db_path):
        os.remove(db_path)

    ensure_database_schema()

    readers_data = [
        {'id': 123, 'name': 'Ann', 'surname': 'Adams', 'email': 'ann.adams@example.com', 'role': 'librarian'},
        {'id': 345, 'name': 'Sam', 'surname': 'Adams', 'email': 'sam.adams@example.edu'},
        {'id': 450, 'name': 'Kim', 'surname': 'Smalls', 'email': 'kim.smalls@example.com'},
        {'id': 568, 'name': 'Sam', 'surname': 'Smalls', 'email': 'sam.smalls@example.com'},
        {'id': 753, 'name': 'Nova', 'surname': 'Yeni', 'email': 'nova.yeni@example.edu'},
        {'id': 653, 'name': 'Tom', 'surname': 'Grey', 'email': 'tom.grey@example.com'},
        {'id': 811, 'name': 'Lina', 'surname': 'Moroz', 'email': 'lina.moroz@example.com'},
        {'id': 812, 'name': 'Oleh', 'surname': 'Kravets', 'email': 'oleh.kravets@example.com'},
        {'id': 813, 'name': 'Marta', 'surname': 'Bondar', 'email': 'marta.bondar@example.net'},
        {'id': 814, 'name': 'Ira', 'surname': 'Shevchenko', 'email': 'ira.shevchenko@example.org'},
    ]
    readers = []
    for row in readers_data:
        reader = Reader(
            id=row['id'],
            name=row['name'],
            surname=row['surname'],
            email=row['email'],
            role=row.get('role', 'reader'),
        )
        reader.set_password(DEFAULT_PASSWORD)
        readers.append(reader)

    db.session.add_all(readers)
    safe_commit()

    books_data = [
        {'id': 12, 'title': 'Hundred Years of Solitude', 'author_name': 'Gabriel', 'author_surname': 'García Márquez', 'original_language': 'Spanish', 'translation_language': 'English', 'first_publication': '1967', 'genre': 'Magic realism, Family saga, Literary fiction', 'month': 'April', 'year': 2020, 'cover_image': 'book_covers/book-12.svg'},
        {'id': 13, 'title': 'The Stranger', 'author_name': 'Albert', 'author_surname': 'Camus', 'original_language': 'French', 'translation_language': 'English', 'first_publication': '1942', 'genre': 'Philosophical fiction, Existentialism, Absurdism', 'month': 'May', 'year': 2020, 'cover_image': 'book_covers/book-13.svg'},
        {'id': 14, 'title': 'The Book of Why', 'author_name': 'Judea', 'author_surname': 'Pearl', 'original_language': 'English', 'translation_language': 'English', 'first_publication': '2018', 'genre': 'Non-fiction, Science, Statistics, Philosophy of science', 'month': 'September', 'year': 2019, 'cover_image': 'book_covers/book-14.svg'},
        {'id': 15, 'title': 'Crime and Punishment', 'author_name': 'Fyodor', 'author_surname': 'Dostoevsky', 'original_language': 'Russian', 'translation_language': 'English', 'first_publication': '1866', 'genre': 'Psychological fiction, Philosophical novel, Crime fiction', 'month': 'February', 'year': 2018, 'cover_image': 'book_covers/book-15.svg'},
        {'id': 16, 'title': 'The Trial', 'author_name': 'Franz', 'author_surname': 'Kafka', 'original_language': 'German', 'translation_language': 'English', 'first_publication': '1925', 'genre': 'Absurdist fiction, Dystopian fiction, Legal fiction', 'month': 'March', 'year': 2018, 'cover_image': 'book_covers/book-16.svg'},
        {'id': 17, 'title': 'The Plague', 'author_name': 'Albert', 'author_surname': 'Camus', 'original_language': 'French', 'translation_language': 'English', 'first_publication': '1947', 'genre': 'Philosophical fiction, Existentialism, Allegory', 'month': 'July', 'year': 2019, 'cover_image': 'book_covers/book-17.svg'},
        {'id': 18, 'title': 'Demian', 'author_name': 'Hermann', 'author_surname': 'Hesse', 'original_language': 'German', 'translation_language': 'English', 'first_publication': '1919', 'genre': 'Bildungsroman, Psychological fiction, Philosophical fiction', 'month': 'June', 'year': 2018, 'cover_image': 'book_covers/book-18.svg'},
        {'id': 19, 'title': 'Guns, Germs, and Steel', 'author_name': 'Jared', 'author_surname': 'Diamond', 'original_language': 'English', 'translation_language': 'English', 'first_publication': '1997', 'genre': 'Non-fiction, History, Anthropology, Geography', 'month': 'August', 'year': 2019, 'cover_image': 'book_covers/book-19.svg'},
        {'id': 20, 'title': 'Atomic Habits', 'author_name': 'James', 'author_surname': 'Clear', 'original_language': 'English', 'translation_language': 'English', 'first_publication': '2018', 'genre': 'Self-help, Productivity, Psychology', 'month': 'January', 'year': 2021, 'cover_image': 'book_covers/book-20.svg'},
        {'id': 21, 'title': 'Sapiens', 'author_name': 'Yuval Noah', 'author_surname': 'Harari', 'original_language': 'Hebrew', 'translation_language': 'English', 'first_publication': '2011', 'genre': 'Non-fiction, History, Anthropology, Popular science', 'month': 'March', 'year': 2021, 'cover_image': 'book_covers/book-21.svg'},
        {'id': 22, 'title': 'The Name of the Rose', 'author_name': 'Umberto', 'author_surname': 'Eco', 'original_language': 'Italian', 'translation_language': 'English', 'first_publication': '1980', 'genre': 'Historical mystery, Postmodern fiction, Detective fiction', 'month': 'October', 'year': 2017, 'cover_image': 'book_covers/book-22.svg'},
        {'id': 23, 'title': 'Thinking, Fast and Slow', 'author_name': 'Daniel', 'author_surname': 'Kahneman', 'original_language': 'English', 'translation_language': 'English', 'first_publication': '2011', 'genre': 'Non-fiction, Psychology, Behavioral economics', 'month': 'November', 'year': 2022, 'cover_image': 'book_covers/book-23.svg'},
        {'id': 24, 'title': 'The Master and Margarita', 'author_name': 'Mikhail', 'author_surname': 'Bulgakov', 'original_language': 'Russian', 'translation_language': 'English', 'first_publication': '1967', 'genre': 'Satirical fiction, Fantasy, Philosophical fiction', 'month': 'December', 'year': 2020, 'cover_image': 'book_covers/book-24.svg'},
        {'id': 25, 'title': 'Brave New World', 'author_name': 'Aldous', 'author_surname': 'Huxley', 'original_language': 'English', 'translation_language': 'English', 'first_publication': '1932', 'genre': 'Dystopian fiction, Science fiction, Social satire', 'month': 'April', 'year': 2017, 'cover_image': 'book_covers/book-25.svg'},
        {'id': 26, 'title': 'Flowers for Algernon', 'author_name': 'Daniel', 'author_surname': 'Keyes', 'original_language': 'English', 'translation_language': 'English', 'first_publication': '1966', 'genre': 'Science fiction, Psychological fiction, Tragedy', 'month': 'May', 'year': 2022, 'cover_image': 'book_covers/book-26.svg'},
        {'id': 27, 'title': 'The Brothers Karamazov', 'author_name': 'Fyodor', 'author_surname': 'Dostoevsky', 'original_language': 'Russian', 'translation_language': 'English', 'first_publication': '1880', 'genre': 'Philosophical novel, Psychological fiction, Family drama', 'month': 'June', 'year': 2016, 'cover_image': 'book_covers/book-27.svg'},
        {'id': 28, 'title': 'Meditations', 'author_name': 'Marcus', 'author_surname': 'Aurelius', 'original_language': 'Greek', 'translation_language': 'English', 'first_publication': '180', 'genre': 'Philosophy, Stoicism, Personal reflections', 'month': 'July', 'year': 2021, 'cover_image': 'book_covers/book-28.svg'},
        {'id': 29, 'title': 'The Little Prince', 'author_name': 'Antoine', 'author_surname': 'de Saint-Exupéry', 'original_language': 'French', 'translation_language': 'English', 'first_publication': '1943', 'genre': 'Novella, Fable, Philosophical fiction', 'month': 'August', 'year': 2015, 'cover_image': 'book_covers/book-29.svg'},
        {'id': 30, 'title': 'The Myth of Sisyphus', 'author_name': 'Albert', 'author_surname': 'Camus', 'original_language': 'French', 'translation_language': 'English', 'first_publication': '1942', 'genre': 'Philosophy, Existentialism, Essay', 'month': 'September', 'year': 2023, 'cover_image': 'book_covers/book-30.svg'},
    ]

    db.session.add_all([Book(**row) for row in books_data])
    safe_commit()

    reviews_data = [
        {'id': 111, 'text': 'This book is amazing.', 'stars': 5, 'reviewer_id': 123, 'book_id': 12},
        {'id': 112, 'text': 'The story is hard to follow.', 'stars': 3, 'reviewer_id': 345, 'book_id': 12},
        {'id': 113, 'text': 'Quietly devastating and deep.', 'stars': 5, 'reviewer_id': 450, 'book_id': 13},
        {'id': 114, 'text': 'Strong existential vibe.', 'stars': 4, 'reviewer_id': 653, 'book_id': 13},
        {'id': 115, 'text': 'Complicated but rewarding.', 'stars': 4, 'reviewer_id': 812, 'book_id': 14},
        {'id': 116, 'text': 'Clear examples and practical logic.', 'stars': 5, 'reviewer_id': 813, 'book_id': 14},
        {'id': 117, 'text': 'Heavy and emotional read.', 'stars': 5, 'reviewer_id': 814, 'book_id': 15},
        {'id': 118, 'text': 'Hard to put down.', 'stars': 5, 'reviewer_id': 753, 'book_id': 15},
        {'id': 119, 'text': 'Anxious atmosphere from start to finish.', 'stars': 4, 'reviewer_id': 568, 'book_id': 16},
        {'id': 120, 'text': 'Strange but memorable.', 'stars': 4, 'reviewer_id': 811, 'book_id': 16},
        {'id': 121, 'text': 'Simple language, big ideas.', 'stars': 5, 'reviewer_id': 345, 'book_id': 17},
        {'id': 122, 'text': 'Very relevant to modern times.', 'stars': 5, 'reviewer_id': 123, 'book_id': 17},
        {'id': 123, 'text': 'Could not finish the book.', 'stars': 3, 'reviewer_id': 753, 'book_id': 18},
        {'id': 124, 'text': 'Good coming-of-age style narrative.', 'stars': 4, 'reviewer_id': 450, 'book_id': 18},
        {'id': 125, 'text': 'A bit dry in places.', 'stars': 3, 'reviewer_id': 568, 'book_id': 19},
        {'id': 126, 'text': 'Taught me a lot about history.', 'stars': 5, 'reviewer_id': 653, 'book_id': 19},
        {'id': 127, 'text': 'Practical and easy to apply.', 'stars': 5, 'reviewer_id': 811, 'book_id': 20},
        {'id': 128, 'text': 'Helpful but repetitive in the middle.', 'stars': 4, 'reviewer_id': 812, 'book_id': 20},
        {'id': 129, 'text': 'Wide perspective and thought-provoking.', 'stars': 5, 'reviewer_id': 813, 'book_id': 21},
        {'id': 130, 'text': 'Great overview, sometimes too broad.', 'stars': 4, 'reviewer_id': 814, 'book_id': 21},
        {'id': 131, 'text': 'Amazing atmosphere and mystery.', 'stars': 5, 'reviewer_id': 653, 'book_id': 22},
        {'id': 132, 'text': 'A bit long, yet worth it.', 'stars': 4, 'reviewer_id': 450, 'book_id': 22},
        {'id': 133, 'text': 'Dense but rewarding read.', 'stars': 4, 'reviewer_id': 814, 'book_id': 23},
        {'id': 134, 'text': 'Changed how I think about decisions.', 'stars': 5, 'reviewer_id': 811, 'book_id': 23},
        {'id': 135, 'text': 'Wild, satirical and unforgettable.', 'stars': 5, 'reviewer_id': 812, 'book_id': 24},
        {'id': 136, 'text': 'Brilliant absurd humor.', 'stars': 5, 'reviewer_id': 753, 'book_id': 24},
        {'id': 137, 'text': 'Scary and still relevant.', 'stars': 5, 'reviewer_id': 345, 'book_id': 25},
        {'id': 138, 'text': 'A thoughtful sci-fi classic.', 'stars': 4, 'reviewer_id': 123, 'book_id': 25},
        {'id': 139, 'text': 'Touching and heartbreaking.', 'stars': 5, 'reviewer_id': 568, 'book_id': 26},
        {'id': 140, 'text': 'One of the most humane books I read.', 'stars': 5, 'reviewer_id': 813, 'book_id': 26},
        {'id': 141, 'text': 'Deep philosophical dialogues.', 'stars': 5, 'reviewer_id': 653, 'book_id': 27},
        {'id': 142, 'text': 'Long but absolutely worth the time.', 'stars': 5, 'reviewer_id': 814, 'book_id': 27},
        {'id': 143, 'text': 'Short and practical wisdom.', 'stars': 5, 'reviewer_id': 450, 'book_id': 28},
        {'id': 144, 'text': 'Great book to reread every year.', 'stars': 5, 'reviewer_id': 811, 'book_id': 28},
        {'id': 145, 'text': 'Beautiful and poetic.', 'stars': 5, 'reviewer_id': 812, 'book_id': 29},
        {'id': 146, 'text': 'Looks simple but very profound.', 'stars': 5, 'reviewer_id': 345, 'book_id': 29},
        {'id': 147, 'text': 'Compact and challenging essay.', 'stars': 4, 'reviewer_id': 123, 'book_id': 30},
        {'id': 148, 'text': 'Important read after The Stranger.', 'stars': 5, 'reviewer_id': 753, 'book_id': 30},
    ]
    db.session.add_all([Review(**row) for row in reviews_data])
    safe_commit()

    annotations_data = [
        {'id': 331, 'text': 'Time in this novel feels cyclical.', 'reviewer_id': 123, 'book_id': 12},
        {'id': 332, 'text': 'Detached tone makes every event heavier.', 'reviewer_id': 345, 'book_id': 13},
        {'id': 333, 'text': 'Correlation and causation are not the same.', 'reviewer_id': 812, 'book_id': 14},
        {'id': 334, 'text': 'Guilt is almost a separate character here.', 'reviewer_id': 814, 'book_id': 15},
        {'id': 335, 'text': 'The process itself becomes the punishment.', 'reviewer_id': 568, 'book_id': 16},
        {'id': 336, 'text': 'Solidarity is the book core for me.', 'reviewer_id': 653, 'book_id': 17},
        {'id': 337, 'text': 'A clear look at identity conflict.', 'reviewer_id': 450, 'book_id': 18},
        {'id': 338, 'text': 'Geography shapes long-term outcomes.', 'reviewer_id': 568, 'book_id': 19},
        {'id': 339, 'text': 'Small habits compound over years.', 'reviewer_id': 811, 'book_id': 20},
        {'id': 340, 'text': 'Great macro-history perspective.', 'reviewer_id': 813, 'book_id': 21},
        {'id': 341, 'text': 'The monastery is like a full character.', 'reviewer_id': 653, 'book_id': 22},
        {'id': 342, 'text': 'System 1 vs System 2 is very useful.', 'reviewer_id': 814, 'book_id': 23},
        {'id': 343, 'text': 'Layered satire with deep metaphors.', 'reviewer_id': 753, 'book_id': 24},
        {'id': 344, 'text': 'Pleasure is used as a control mechanism.', 'reviewer_id': 345, 'book_id': 25},
        {'id': 345, 'text': 'Progress can carry an emotional price.', 'reviewer_id': 813, 'book_id': 26},
        {'id': 346, 'text': 'Faith and doubt are balanced masterfully.', 'reviewer_id': 653, 'book_id': 27},
        {'id': 347, 'text': 'Focus only on what you can control.', 'reviewer_id': 450, 'book_id': 28},
        {'id': 348, 'text': 'Childlike language reveals adult truths.', 'reviewer_id': 812, 'book_id': 29},
        {'id': 349, 'text': 'Absurdity is described without despair.', 'reviewer_id': 123, 'book_id': 30},
    ]
    db.session.add_all([Annotation(**row) for row in annotations_data])
    safe_commit()

    db.session.close()
