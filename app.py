import logging
import os

from flask import Flask

from extensions import db, login_manager


logging.basicConfig(level=logging.DEBUG, format='%(levelname)s: %(message)s')

base_dir = os.path.abspath(os.path.dirname(__file__))
instance_dir = os.path.join(base_dir, 'instance')
app = Flask(__name__, instance_relative_config=True, instance_path=instance_dir)
app.config['SECRET_KEY'] = 'you-will-never-guess'

os.makedirs(app.instance_path, exist_ok=True)
db_path = os.path.join(app.instance_path, 'myDB.db')
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

if os.path.exists(db_path):
    logging.info('DB ' + db_path + 'is exists')
else:
    logging.info('DB ' + db_path + 'is not exists')

login_manager.login_view = 'main.login'
login_manager.init_app(app)

from models import Reader  # noqa: E402
from routes import bp  # noqa: E402

app.register_blueprint(bp)


@login_manager.user_loader
def load_user(user_id):
    return db.session.get(Reader, int(user_id))


if __name__ == "__main__":
    app.run(debug=True)
