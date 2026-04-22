from __future__ import annotations

from typing import Any


def is_librarian(user: Any) -> bool:
    if not getattr(user, 'is_authenticated', False):
        return False
    try:
        return getattr(user, 'role', None) == 'librarian'
    except Exception:
        return False


def can_view_hidden_books(user: Any) -> bool:
    return is_librarian(user)


def can_create_review(user: Any) -> bool:
    return bool(getattr(user, 'is_authenticated', False))


def can_create_annotation(user: Any) -> bool:
    return is_librarian(user)


def can_create_book(user: Any) -> bool:
    return is_librarian(user)


def can_edit_book_content(user: Any) -> bool:
    return is_librarian(user)


def can_update_book(user: Any) -> bool:
    return is_librarian(user)


def can_delete_review(user: Any, review: Any = None) -> bool:
    if not getattr(user, 'is_authenticated', False):
        return False
    if is_librarian(user):
        return True
    if review is None:
        return False
    try:
        return getattr(review, 'reviewer_id', None) == getattr(user, 'id', None)
    except Exception:
        return False


def can_delete_annotation(user: Any) -> bool:
    return is_librarian(user)


def can_update_review(user: Any) -> bool:
    return is_librarian(user)


def can_update_annotation(user: Any) -> bool:
    return is_librarian(user)
