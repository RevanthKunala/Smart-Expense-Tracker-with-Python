"""
db.py — MySQL connection helper
Uses Flask's g object to maintain one connection per request.
mysql-connector-python is used as the driver (pure Python, no system libs needed).
Cursor returns dictionaries so columns are accessed by name just like sqlite3.Row.
"""

import mysql.connector
from flask import current_app, g


def get_db():
    """Return the per-request MySQL connection, creating it if needed."""
    if "db" not in g:
        cfg = current_app.config
        g.db = mysql.connector.connect(
            host=cfg["MYSQL_HOST"],
            port=cfg["MYSQL_PORT"],
            user=cfg["MYSQL_USER"],
            password=cfg["MYSQL_PASSWORD"],
            database=cfg["MYSQL_DB"],
            charset="utf8mb4",
            use_unicode=True,
            autocommit=False,          # explicit commits for safety
        )
    return g.db


def get_cursor(dictionary=True):
    """Return a fresh cursor from the current connection.
    dictionary=True → rows behave like dicts (column access by name).
    """
    return get_db().cursor(dictionary=dictionary)


def close_db(e=None):
    """Close the MySQL connection at the end of the request."""
    db = g.pop("db", None)
    if db is not None and db.is_connected():
        db.close()


def init_app(app):
    """Register teardown context with the Flask app."""
    app.teardown_appcontext(close_db)
