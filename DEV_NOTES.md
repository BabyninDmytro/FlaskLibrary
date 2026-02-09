# Dev Notes

## Session summary
- Added reader authentication, registration, and logout flow with role selection and templates.
- Stored the SQLite database under the Flask `instance/` directory and aligned the seeder with this path.
- Updated the Flask-Login user loader to use `db.session.get` to avoid SQLAlchemy 2.0 legacy warnings.
- Added per-book detail pages and linked book titles in yearly and home listings to those pages.
- 2026-02-09: Restyled templates (login, register, home, book list, and book detail) with centered layouts, card-based sections, and unified form/message styling.
