import logging
import os

from flask import Flask

from app.extensions import db, login_manager


logging.basicConfig(level=logging.DEBUG, format='%(levelname)s: %(message)s')


def create_app(test_config=None):
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
    instance_dir = os.path.join(base_dir, 'instance')
    template_dir = os.path.join(base_dir, 'templates')
    app = Flask(
        __name__,
        instance_relative_config=True,
        instance_path=instance_dir,
        template_folder=template_dir,
    )

    app.config.from_mapping(
        SECRET_KEY='you-will-never-guess',
        SQLALCHEMY_DATABASE_URI=f"sqlite:///{os.path.join(app.instance_path, 'myDB.db')}",
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
    )

    if test_config:
        app.config.update(test_config)

    os.makedirs(app.instance_path, exist_ok=True)
    db_path = os.path.join(app.instance_path, 'myDB.db')

    db.init_app(app)

    if os.path.exists(db_path):
        logging.info('DB ' + db_path + 'is exists')
    else:
        logging.info('DB ' + db_path + 'is not exists')

    login_manager.login_view = 'main.login'
    login_manager.init_app(app)

    from app.models import Reader  # noqa: E402
    from app.routes import bp  # noqa: E402

    app.register_blueprint(bp)

    @login_manager.user_loader
    def _load_user(user_id):
        return load_user(user_id)

    return app


def load_user(user_id):
    from app.models import Reader

    return db.session.get(Reader, int(user_id))


app = create_app()
