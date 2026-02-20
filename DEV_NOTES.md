# Dev Notes


## 2026-02-20
- Для моделі `Book` додано прапорець `is_hidden` (default `False`) для підтримки приховування книг бібліотекарем.
- Додано рольову перевірку `librarian` у роутингу: звичайні читачі не бачать приховані книги у `/home` та `/books/<year>`, а також не можуть відкривати `/book/<id>` і `/book/<id>/read` для прихованих книг.
- Реалізовано moderation-маршрути для `Librarian`: `POST /book/<id>/toggle-hidden`, `POST /reviews/<id>/delete`, `POST /annotations/<id>/delete`.
- Оновлено UI: на `home.html` і `book.html` для бібліотекаря додано кнопки Hide/Unhide; на шаблонах читання (`templates/book_reads/*`) додано кнопки видалення анотацій; у review-блоці додано кнопку видалення коментаря.
- Додано тестові сценарії для прав бібліотекаря: приховування/показ книг, видалення review/annotation, а також перевірки, що звичайний Reader не може виконувати moderation-дії.


## 2026-02-13
- Для маршруту `/book/<book_id>/read` додано вибір окремого шаблону за `book_id`: якщо є `templates/book_reads/book_<id>_read.html`, рендериться саме він; для не-seed книг використовується `book_default_read.html`.
- Додано окремі read-шаблони для seed-книг (`book_12_read.html` ... `book_30_read.html`) зі спрощеним "plain document" стилем (serif, мінімум декоративних елементів).
- Усі read-шаблони приведено до однакової структури секцій: `Title` → `Description` → `Annotations` → `Book text`.
- У секцію `Book text` тимчасово додано текст із `Lorem ipsum`.
- `templates/book_read.html` видалено; спільний read-шаблон більше не використовується.
- Тести read-маршруту розширено перевірками порядку секцій, наявності `Lorem ipsum`, а також доступності сторінки `/book/12/read`.
- На read-сторінках додано друге посилання `Back to book page` одразу після секції `Annotations` (окрім існуючого посилання внизу після `Book text`).
- Read-шаблони спрощено під формат plain-document (як у референсі): порядок блоків `Back link` → `Назва` → `Опис` → `Обкладинка` → `Анотації` → `Текст книги` → `Back link`, без секції `Description` англійською.
- На read-сторінках прибрано підписи `Опис:` і `Текст книги`; додано секцію `Contents` перед текстом із гіперпосиланням `Розділ 1`, яке веде до якоря початку тексту (`#chapter-1`).

- Перенесено вивід списку анотацій зі сторінки `book.html` на нову сторінку читання `/book/<book_id>/read`.
- На сторінці книги біля метаданих додано кнопку `Read now`, що веде на нову сторінку читання.
- На `book.html` прибрано стрічку відображення анотацій, але форму додавання анотації залишено без змін.
- Додано новий шаблон `book_read.html` для відображення анотацій книги та оновлено тести маршруту/шаблону під новий UX.
- На сторінку `book.html` додано окремий блок `Annotations` перед відгуками: тепер користувачі бачать короткі анотації до книги окремо від review.
- Додано `AnnotationForm` та обробку анотацій у роуті `/book/<book_id>` з окремим submit-потоком (через префікси форм), щоб форма анотацій не конфліктувала з формою відгуків.
- Оновлено логіку рендера сторінки книги: анотації та відгуки передаються в шаблон окремими списками з сортуванням за новизною.
- Розширено тести: покрито валідацію форми анотацій і POST-сценарії створення/блокування анотацій для автентифікованих/гостьових користувачів.

- Додано підтримку окремої обкладинки для кожної книги: у модель `Book` додано поле `cover_image` з дефолтним шляхом `book_covers/default.svg`.
- Оновлено шаблон сторінки книги: обкладинка тепер рендериться зі статичних файлів через `url_for('static', filename=book.cover_image)`.
- Додано набір локальних SVG-обкладинок у `app/static/book_covers/` (для кожної seed-книги + `default.svg`).
- Оновлено сид-дані в `add_data.py`: для кожної книги збережено власний шлях до обкладинки.
- Додано тест `test_book_has_default_cover_image`, який перевіряє дефолтне значення обкладинки для нової книги.
- Зафіксовано візуальну перевірку сторінки книги зі статичною обкладинкою (`/book/12`, Playwright screenshot).

## 2026-02-12
- Added review submission support on `book.html`: users can now enter custom review text in a new textarea form shown below the existing reviews.
- Updated `/book/<book_id>` to accept `POST`, save the submitted review to the database for authenticated users, and redirect back to the same page so the new review is visible immediately.
- Added/updated tests for review form validation and for authenticated/guest review submission behavior on the book page.
- Extended the review form to collect `Stars` (1-5) from the user and store that value in the `Review.stars` column instead of using a fixed default.
- Replaced numeric stars input with a clickable star-rating control (★) while keeping stored values in range 1-5.

## 2026-02-10
- Reworked `/home` book filtering from multiple dedicated fields to one free-form search field (`q`) placed between the welcome header and the book list.
- Implemented tokenized smart search: the query is split into words, and each word is matched across title, author name, author surname, month, and year.
- Added pagination for `/home` search results with 10 books per page.
- Added pagination navigation controls (Prev/Next + page numbers) and preserved `q` in pagination links.
- Fixed layout shift while changing pages by reserving vertical scrollbar space with `html { overflow-y: scroll; }`.

## 2026-02-09
- Added reader authentication, registration, and logout flow with role selection and templates.
- Stored the SQLite database under the Flask `instance/` directory and aligned the seeder with this path.
- Updated the Flask-Login user loader to use `db.session.get` to avoid SQLAlchemy 2.0 legacy warnings.
- Added per-book detail pages and linked book titles in yearly and home listings to those pages.
- Restyled templates (login, register, home, book list, and book detail) with centered layouts, card-based sections, and unified form/message styling.


## Testing quick start
- Create and activate a virtual environment:
  - `python -m venv .venv`
  - `source .venv/bin/activate`
- Install dependencies:
  - `python -m pip install -r requirements-dev.txt`
- Run tests:
  - `pytest -q`

Notes:
- `pytest.ini` already points test discovery to `tests/`.
- `tests/conftest.py` creates an isolated sqlite test database and cleans tables before each test.
