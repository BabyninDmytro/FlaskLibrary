"""WSGI entrypoint template for PythonAnywhere.

Usage on PythonAnywhere:
- Place this file in your project root.
- Update PROJECT_HOME to your real path, e.g. /home/<username>/FlaskLibrary.
- In the PythonAnywhere Web tab WSGI file, you can either copy this content
  or import `application` from this module.
"""

import os
import sys
from pathlib import Path

from dotenv import load_dotenv


PROJECT_HOME = Path(os.getenv("PROJECT_HOME", "/home/<your_username>/FlaskLibrary")).resolve()

if str(PROJECT_HOME) not in sys.path:
    sys.path.insert(0, str(PROJECT_HOME))

# Load .env from project root for PythonAnywhere runtime.
# `override=False` keeps Web tab Environment variables higher priority.
load_dotenv(PROJECT_HOME / ".env", override=False)

# Optional defaults if values are missing in .env / Web environment variables.
os.environ.setdefault("FLASK_INSTANCE_PATH", f"{PROJECT_HOME}/instance")
os.environ.setdefault("FLASK_DB_PATH", f"{PROJECT_HOME}/instance/myDB.db")
os.environ.setdefault("FLASK_DEBUG", "false")

# PythonAnywhere-only overrides (uncomment if you need values different from .env):
# os.environ["FLASK_INSTANCE_PATH"] = "/home/DmytroBabynin/FlaskLibrary/instance"
# os.environ["FLASK_DB_PATH"] = "/home/DmytroBabynin/FlaskLibrary/instance/myDB.db"
# os.environ["SECRET_KEY"] = "твій_секрет"
# os.environ["FLASK_DEBUG"] = "false"
# os.environ["LOG_LEVEL"] = "INFO"

from app import create_app


application = create_app()
