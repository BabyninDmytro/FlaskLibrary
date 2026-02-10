# Dev Notes

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
