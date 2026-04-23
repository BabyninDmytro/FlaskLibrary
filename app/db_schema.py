from __future__ import annotations

from sqlalchemy import inspect

from app.extensions import db


def ensure_database_schema() -> tuple[str, ...]:
    inspector = inspect(db.engine)
    missing_tables = [table for table in db.metadata.sorted_tables if not inspector.has_table(table.name)]
    if not missing_tables:
        return ()

    db.metadata.create_all(bind=db.engine, tables=missing_tables)
    return tuple(table.name for table in missing_tables)
