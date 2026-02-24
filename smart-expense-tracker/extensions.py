"""
extensions.py
Shared extension instances.
SQLite connection is managed via a helper in db.py.
"""

from flask_bcrypt import Bcrypt
from flask_login import LoginManager
from flask_wtf.csrf import CSRFProtect

bcrypt        = Bcrypt()
login_manager = LoginManager()
csrf          = CSRFProtect()

login_manager.login_view             = "auth.login"
login_manager.login_message          = "Please log in to access this page."
login_manager.login_message_category = "warning"
