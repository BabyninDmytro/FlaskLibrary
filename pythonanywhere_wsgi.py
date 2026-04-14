"""WSGI entrypoint template for PythonAnywhere.

Usage on PythonAnywhere:
- Place this file in your project root.
- Update PROJECT_HOME to your real path, e.g. /home/<username>/FlaskLibrary.
- In the PythonAnywhere Web tab WSGI file, you can either copy this content
  or import `application` from this module.
"""

import os
import sys


PROJECT_HOME = os.getenv("PROJECT_HOME", "/home/<your_username>/FlaskLibrary")

if PROJECT_HOME not in sys.path:
    sys.path.insert(0, PROJECT_HOME)

# Optional runtime configuration for this project:
os.environ.setdefault("FLASK_INSTANCE_PATH", f"{PROJECT_HOME}/instance")
os.environ.setdefault("FLASK_DB_PATH", f"{PROJECT_HOME}/instance/myDB.db")
os.environ.setdefault("FLASK_DEBUG", "false")

from app import create_app


application = create_app()
