# Dev Notes

## Session summary
- Added reader authentication, registration, and logout flow with role selection and templates.
- Stored the SQLite database under the Flask `instance/` directory and aligned the seeder with this path.
- Updated the Flask-Login user loader to use `db.session.get` to avoid SQLAlchemy 2.0 legacy warnings.
- Added per-book detail pages and linked book titles in yearly and home listings to those pages.
- 2026-02-09: Restyled templates (login, register, home, book list, and book detail) with centered layouts, card-based sections, and unified form/message styling.
- 2026-02-10: Refactored project structure by separating models into `models.py`, forms into `forms.py`, shared extensions into `extensions.py`, and routing into `routes.py`.
- 2026-02-10: Fixed circular import issues between `app.py` and `models.py` by moving `db`/`login_manager` instances to `extensions.py` and initializing them in `app.py`.
- 2026-02-10: Switched routes to a Blueprint (`main`) and registered it from `app.py`; updated template `url_for(...)` calls to `main.*` endpoints.
- 2026-02-10: Updated `add_data.py` imports to use models from `models.py` under the refactored layout.
