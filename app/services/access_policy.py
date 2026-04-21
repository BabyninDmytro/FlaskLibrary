def is_librarian(user):
    if not getattr(user, 'is_authenticated', False):
        return False
    try:
        return getattr(user, 'role', None) == 'librarian'
    except Exception:
        return False


def can_view_hidden_books(user):
    return is_librarian(user)


def can_create_review(user):
    return bool(getattr(user, 'is_authenticated', False))


def can_create_annotation(user):
    return is_librarian(user)


def can_create_book(user):
    return is_librarian(user)


def can_edit_book_content(user):
    return is_librarian(user)


def can_update_book(user):
    return is_librarian(user)


def can_delete_review(user, review=None):
    if not getattr(user, 'is_authenticated', False):
        return False
    if is_librarian(user):
        return True
    if review is None:
        return False
    return getattr(review, 'reviewer_id', None) == getattr(user, 'id', None)


def can_delete_annotation(user):
    return is_librarian(user)


def can_update_review(user):
    return is_librarian(user)


def can_update_annotation(user):
    return is_librarian(user)
