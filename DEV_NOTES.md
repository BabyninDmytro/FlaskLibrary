# Dev Notes


## 2026-02-27
- Додатково уніфіковано `app/services/book_service.py` під SQLAlchemy 2-style термінологію та вирази: `build_books_query()`/`paginate_books()` працюють через `stmt` (Select statement), а `get_book_or_404()` використовує явний `where(Book.id == ...)` замість query-подібного `filter_by`, щоб прибрати неоднозначність зі «старим» синтаксисом.
- Перевірено й виправлено `is_librarian` у web-шаблонах: додано context processor `inject_role_flags()` та уніфікований helper `_is_librarian()` в `app/web_routes.py`, тому librarian-контент коректно з’являється на сторінках (`home`, `book`, `book_read`, `_review`). Також відновлено web moderation endpoint-и `POST /reviews/<id>/delete` і `POST /annotations/<id>/delete`, які використовуються кнопками в шаблонах.
- Виправлено web-доступи та рольову поведінку в `app/web_routes.py`: додано `@login_required` для `profile/reviews/book/book_read`, відновлено передачу `is_librarian` у шаблони, обмежено створення анотацій лише для `librarian` (для reader — редірект на `/home`), додано маршрут `POST /book/<id>/toggle-hidden` для бібліотекаря.
- Переведено сервісний шар на SQLAlchemy 2.0-style запити: замість `Model.query` використано `select(...)` + явне виконання через `db.session.execute(...)` (`app/services/book_service.py`, `app/services/review_service.py`, `app/services/annotation_service.py`, `app/services/reader_service.py`).
- У `book_service` пошук і пагінація тепер працюють із `Select`-виразом та `db.paginate(...)`, що чітко розділяє побудову запиту і його виконання.
- Оновлено тести для сучасного підходу до читання з БД: замість `Model.query...` використовується `select(...)` + `db.session.scalar(...)`/агрегації через `func.count(...)` (`tests/test_auth_search.py`, `tests/test_models_relationships.py`, `tests/test_route_access.py`).

## 2026-02-26
- Спрощено `book_details()` в `app/api_routes.py`: прибрано дублюючі list-comprehension трансформації для `reviews`/`annotations`, тепер використовується прямий результат `serialize_review()` і `serialize_annotation()` без повторного ручного мапінгу тих самих полів.
- Уточнено документацію для `books_collection()` (`app/api_routes.py`): `per_page` — це кількість книг на сторінку; якщо параметр не передано в запиті, використовується значення за замовчуванням `10`, а допустимий діапазон — `1..50`. Також описано `search`, `page` і структуру JSON-відповіді з блоком `pagination`.
- Актуалізовано `REST_API_ASSESSMENT.md`: зафіксовано поточний стан міграції на REST (що вже реалізовано: `/api/v1/*`, mutating endpoint-и, error envelope, OpenAPI) та окремо виділено незакриті пункти й оновлену оцінку зрілості.
- Перероблено маршрути під зрозуміле розділення SSR/REST для книги: `GET/POST /book/<id>` знову є canonical HTML-сторінкою з усім функціоналом `book()` (review/annotation форми і обробка).
- Реалізовано REST-представлення книги на `GET /api/v1/books/<id>` та alias `GET /books/<id>` (JSON із полями книги, `reviews`, `annotations`).
- Залишено backward-compat endpoint `GET /api/v1/books/<id>/data`, який редіректить на `GET /api/v1/books/<id>`.
- Оновлено тести маршруту книги та API: перевірки HTML-сторінки, JSON payload, 404 та редіректу legacy data endpoint.
- Роути розділено по відповідальностях у різні модулі: `app/web_routes.py` (SSR/HTML) і `app/api_routes.py` (REST/JSON).
- У `app/__init__.py` замінено реєстрацію одного blueprint на реєстрацію двох: `main` (web) та `api` (REST).
- `app/routes.py` залишено як сумісний модуль-обгортку без бізнес-логіки, щоб зафіксувати нову структуру та уникнути подальшого змішування SSR/API в одному файлі.
- Для уникнення конфлікту API alias із web-сторінками прибрано JSON alias `GET /books/<id>`; canonical JSON endpoint книги — `GET /api/v1/books/<id>`.
- Повернуто web-маршрут сторінок за роком у `app/web_routes.py`: підтримуються `GET /books/<year>` і `GET /books/year/<year>` (HTML `display_books.html`).
- Розширено `app/api_routes.py` новими REST endpoint-ами для основних сторінок/ресурсів: `GET /api/v1/books` (collection + search + pagination), `GET /api/v1/books/year/<year>`, `GET /api/v1/readers/<id>`, `GET /api/v1/reviews/<id>`.
- Для нових API-роутів додано покриття тестами в `tests/test_route_access.py`: collection/year/listing, reader profile, review details, а також 404 кейси для reader/review.
- Видалено зайві year-сторінки: прибрано web-маршрути `GET /books/<year>` і `GET /books/year/<year>` та видалено шаблони `templates/input_year.html` і `templates/display_books.html`.
- Прибрано REST endpoint `GET /api/v1/books/year/<year>` з `app/api_routes.py`; залишено базові ресурси `/api/v1/books`, `/api/v1/books/<id>`, `/api/v1/readers/<id>`, `/api/v1/reviews/<id>`.
- Додано write-операції REST API для модерації власного контенту: `PATCH/DELETE /api/v1/reviews/<id>` та `PATCH/DELETE /api/v1/annotations/<id>`.
- Для нових mutating endpoint-ів реалізовано JSON-помилки з кодами `400/401/403/404/422` і покрито тестами сценарії auth/ownership/validation/success.
- Реалізовано канонічні mutating endpoint-и REST: `PATCH/DELETE /api/v1/reviews/<id>` і `PATCH/DELETE /api/v1/annotations/<id>` із JSON-відповідями та кодами `200/204/400/401/403/404/422`.
- Винесено спільну бізнес-логіку в сервісний шар: `app/services/book_service.py`, `app/services/review_service.py`, `app/services/annotation_service.py`.
- `app/web_routes.py` і `app/api_routes.py` переведено на виклики сервісів замість прямого дублювання запитів до БД у маршрутах.
- Додано `POST /api/v1/books/<id>/reviews` і `POST /api/v1/books/<id>/annotations` з валідацією та статусами `201/401/422`.
- Уніфіковано JSON error envelope для API через обробник `HTTPException` у `app/api_routes.py` (включно з 404 для read endpoint-ів).
- Додано мінімальну OpenAPI-специфікацію у файлі `openapi.yaml` для основних існуючих endpoint-ів `/api/v1/*`.
- Додано `app/services/reader_service.py` для уніфікації роботи з Reader (отримання по `id`/`email` і серіалізація).
- Прибрано локальний імпорт `Review` всередині `reviews()` у `app/web_routes.py`: тепер web/api роутери використовують сервіси замість імпортів у тілі функцій.

## 2026-02-25
- У `REST_API_ASSESSMENT.md` додано роз'яснення до пункту про REST gap "HTML templates vs JSON": пояснено, чому SSR-відповіді коректні для браузера, але не формують стабільний API-контракт для mobile/integrations.
- Додано приклад різниці між HTML endpoint (`GET /book/12`) та API endpoint (`GET /api/v1/books/12`) для зняття неоднозначності в рев'ю.
- Уточнено гібридний підхід у `REST_API_ASSESSMENT.md`: `GET /book/<id>` та `GET /book/<id>/read` залишаються HTML-first, тоді як каталог/профілі/операції review+annotation можуть додаватися через `/api/v1/*` для mobile/integrations.
- Реалізовано REST endpoint `GET /api/v1/books/<id>` у `app/routes.py`: повертає JSON з полями книги, списком `reviews` і `annotations`; HTML сторінка `/book/<id>` залишилась без змін.
- Додано тести для API-деталей книги: перевірка JSON payload для існуючої книги та `404` для неіснуючої (`tests/test_route_access.py`).
- Основний роут сторінки книги перенесено з `/book/<id>` на `/api/v1/books/<id>` (тепер саме він рендерить `book.html` і обробляє POST для review/annotation).
- Додано legacy-redirect `GET/POST /book/<id> -> /api/v1/books/<id>` (301), щоб старі посилання не ламались під час переходу.
- Тести `tests/test_route_access.py` оновлено під новий canonical route книги (`/api/v1/books/<id>`) та перевірку редіректу зі старого шляху.
- Повернуто JSON-представлення книги окремим endpoint-ом `GET /api/v1/books/<id>/data`: повертає поля книги, `reviews` та `annotations` для mobile/integrations.
- Розведено ролі маршрутів: `/api/v1/books/<id>` — HTML сторінка книги (SSR), `/api/v1/books/<id>/data` — JSON-дані книги; додано тести на payload і 404 для JSON endpoint.

## 2026-02-20
- Відкотили публічний доступ до сторінок `/book/<id>`, `/book/<id>/read`, `/profile/<id>`, `/reviews/<id>`: повернули `@login_required`, щоб незалогінені користувачі не могли відкривати ці маршрути.
- Додали явний fallback-редірект у цих обробниках: `if not current_user.is_authenticated: return redirect(url_for('main.login'))` (додатковий захист поверх Flask-Login декоратора).
- Оновили route-access тести під очікувану політику доступу: для гостей перевіряється редірект на `/login`, а сценарії читання сторінки книги виконуються після логіну.
- Розкрито публічний доступ до сторінок перегляду контенту: знято `@login_required` з `GET`-маршрутів `/book/<id>`, `/book/<id>/read`, `/profile/<id>`, `/reviews/<id>`, щоб гості отримували коректні `404` для неіснуючих ресурсів і могли читати публічні сторінки без авторизації.
- Авторизація для змін даних збережена: у `/book/<id>` POST-сценарії додавання review/annotation і далі вимагають логін через наявні перевірки в обробнику.
- Секцію `Annotations` на read-сторінках винесено в спільний partial `templates/book_reads/_annotations_section.html` і підключено через `{% include %}` у всіх `book_*_read.html` та `book_default_read.html`; це прибирає дублювання й спрощує подальші зміни UI/логіки анотацій.
- Перевірено й прибрано неявне використання `current_user.role` на інших сторінках: шаблони `book.html`, `_review.html` та всі `templates/book_reads/*` переведено на явний прапорець `is_librarian`, який передається з роутів.
- Оновлено роутинг для явного контексту ролі: `book`, `book_read`, `reviews`, `books/<year>` тепер передають `is_librarian` у `render_template`, щоб шаблони не залежали від глобального `current_user`.
- Уточнено джерело ролі для `home.html`: тепер роут `/home` явно передає прапорець `is_librarian` у шаблон (замість перевірки `current_user.role` прямо в template), щоб уникнути неявної залежності від глобального контексту.
- Заголовки anti-cache після logout звужено до автентифікованих запитів: `no-store` тепер виставляється тільки коли `current_user.is_authenticated`, щоб не відключати кешування для публічних сторінок (наприклад, `/login`).
- Додано тест `test_public_login_page_is_not_marked_no_store` для перевірки, що сторінка входу не маркується `no-store`.
- Виправлено кешування після logout: у `app.after_request` додано заголовки `Cache-Control: no-store, no-cache, must-revalidate, max-age=0`, `Pragma: no-cache`, `Expires: 0`, щоб кнопка Back не відкривала закешовані захищені сторінки після розлогіну.
- Додано тест `test_protected_pages_send_no_store_cache_headers`, який перевіряє no-store заголовки для сторінки книги `/book/<id>`.
- Візуальне доопрацювання `book.html`: прибрано верхню кнопку `Hide/Unhide book`; залишена кнопка біля `Read now` у блоці книги та приведена до того самого розміру, що й `Read now`.
- Follow-up UX: кнопку `Hide/Unhide book` на сторінці книги перенесено з верхнього header-блоку в картку книги (поруч із кнопкою `Read now`).
- Обмежено створення анотацій: форму `Add your annotation` бачить і може submit-ити тільки `librarian`; для звичайного `reader` форма прихована, а POST-спроба створення анотації редіректить на `/home` без запису в БД.
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

## 2026-02-27
- Оновлено `README.md`: додано актуальний опис можливостей FlaskLibrary, структуру проєкту, інструкції запуску, запуску тестів та посилання на API-документацію.
