import logging
import os

from flask import Flask
from flask_login import LoginManager
from flask_sqlalchemy import SQLAlchemy


logging.basicConfig(level=logging.DEBUG, format='%(levelname)s: %(message)s')

base_dir = os.path.abspath(os.path.dirname(__file__))
instance_dir = os.path.join(base_dir, 'instance')
app = Flask(__name__, instance_relative_config=True, instance_path=instance_dir)
app.config['SECRET_KEY'] = 'you-will-never-guess'

os.makedirs(app.instance_path, exist_ok=True)
db_path = os.path.join(app.instance_path, 'myDB.db')
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

if os.path.exists(db_path):
    logging.info('DB ' + db_path + 'is exists')
else:
    logging.info('DB ' + db_path + 'is not exists')

login_manager = LoginManager()
login_manager.login_view = 'login'
login_manager.init_app(app)

from models import Reader  # noqa: E402


@login_manager.user_loader
def load_user(user_id):
    return db.session.get(Reader, int(user_id))


import routes  # noqa: E402,F401


if __name__ == "__main__":
    app.run(debug=True)
