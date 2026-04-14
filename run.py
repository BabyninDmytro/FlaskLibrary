import os

from app import create_app


app = create_app()


def _is_debug_enabled():
    return os.getenv('FLASK_DEBUG', 'true').strip().lower() in {'1', 'true', 'yes', 'on'}


if __name__ == "__main__":
    app.run(debug=_is_debug_enabled())
