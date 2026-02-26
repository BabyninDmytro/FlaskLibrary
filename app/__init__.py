import logging
import os
from pathlib import Path

from flask import Flask
from flask_login import current_user
from sqlalchemy.exc import OperationalError

from app.extensions import db, login_manager


logging.basicConfig(level=logging.DEBUG, format='%(levelname)s: %(message)s')


def _default_paths():
    base_dir = Path(__file__).resolve().parent.parent
    instance_dir = Path(os.getenv('FLASK_INSTANCE_PATH', base_dir / 'instance')).resolve()
    template_dir = (base_dir / 'templates').resolve()
    db_path = Path(os.getenv('FLASK_DB_PATH', instance_dir / 'myDB.db')).resolve()
    return base_dir, instance_dir, template_dir, db_path


def create_app(test_config=None):
    _, instance_dir, template_dir, db_path = _default_paths()

    app = Flask(
        __name__,
        instance_relative_config=True,
        instance_path=str(instance_dir),
        template_folder=str(template_dir),
    )

    app.config.from_mapping(
        SECRET_KEY='you-will-never-guess',
        SQLALCHEMY_DATABASE_URI=f"sqlite:///{db_path}",
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
    )

    if test_config:
        app.config.update(test_config)

    os.makedirs(app.instance_path, exist_ok=True)

    db.init_app(app)

    logging.info('DB path: %s', db_path)

    login_manager.login_view = 'main.login'
    login_manager.init_app(app)

    from app import models  # noqa: E402,F401
    from app.web_routes import bp as web_bp  # noqa: E402
    from app.api_routes import bp as api_bp  # noqa: E402

    app.register_blueprint(web_bp)
    app.register_blueprint(api_bp)

    @app.after_request
    def add_no_store_headers(response):
        if current_user.is_authenticated:
            response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
            response.headers['Pragma'] = 'no-cache'
            response.headers['Expires'] = '0'
        return response


    @login_manager.user_loader
    def _load_user(user_id):
        return load_user(user_id)

    return app


def load_user(user_id):
    from app.models import Reader

    try:
        return db.session.get(Reader, int(user_id), populate_existing=True)
    except OperationalError:
        db.session.rollback()
        return None


app = create_app()
