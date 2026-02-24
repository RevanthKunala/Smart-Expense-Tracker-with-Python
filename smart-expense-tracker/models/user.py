"""
models/user.py
User model — MySQL 8, Flask-Login UserMixin, dict cursors.
Includes role-based access (user / admin).
"""

from flask_login import UserMixin
from db import get_cursor


class User(UserMixin):

    def __init__(self, row):
        self.id       = row["id"]
        self.username = row["username"]
        self.email    = row["email"]
        self.password = row["password"]
        self.role     = row.get("role", "user")

    def is_admin(self):
        return self.role == "admin"

    # ── Lookup ────────────────────────────────────────────────

    @staticmethod
    def get_by_id(user_id):
        cur = get_cursor()
        cur.execute("SELECT * FROM users WHERE id = %s", (user_id,))
        row = cur.fetchone()
        cur.close()
        return User(row) if row else None

    @staticmethod
    def get_by_email(email):
        cur = get_cursor()
        cur.execute("SELECT * FROM users WHERE email = %s", (email,))
        row = cur.fetchone()
        cur.close()
        return User(row) if row else None

    @staticmethod
    def get_by_username(username):
        cur = get_cursor()
        cur.execute("SELECT * FROM users WHERE username = %s", (username,))
        row = cur.fetchone()
        cur.close()
        return User(row) if row else None

    @staticmethod
    def username_exists(username):
        cur = get_cursor()
        cur.execute("SELECT 1 FROM users WHERE username = %s", (username,))
        exists = cur.fetchone() is not None
        cur.close()
        return exists

    @staticmethod
    def email_exists(email):
        cur = get_cursor()
        cur.execute("SELECT 1 FROM users WHERE email = %s", (email,))
        exists = cur.fetchone() is not None
        cur.close()
        return exists

    @staticmethod
    def get_total_count():
        cur = get_cursor()
        cur.execute("SELECT COUNT(*) AS cnt FROM users")
        row = cur.fetchone()
        cur.close()
        return row["cnt"] if row else 0

    # ── Create ────────────────────────────────────────────────

    @staticmethod
    def create(username, email, hashed_password):
        """
        Insert a new user. First user ever is auto-promoted to admin.
        """
        role = "admin" if User.get_total_count() == 0 else "user"
        cur  = get_cursor()
        cur.execute(
            """INSERT INTO users (username, email, password, role)
               VALUES (%s, %s, %s, %s)""",
            (username, email, hashed_password, role)
        )
        cur._connection.commit()
        last_id = cur.lastrowid
        cur.close()
        return last_id

    # ── Admin helpers ─────────────────────────────────────────

    @staticmethod
    def get_all():
        cur = get_cursor()
        cur.execute(
            "SELECT id, username, email, role, created_at FROM users ORDER BY created_at DESC"
        )
        rows = cur.fetchall()
        cur.close()
        return rows

    @staticmethod
    def promote(user_id):
        cur = get_cursor()
        cur.execute(
            "UPDATE users SET role = 'admin' WHERE id = %s", (user_id,)
        )
        cur._connection.commit()
        cur.close()

    @staticmethod
    def demote(user_id):
        cur = get_cursor()
        cur.execute(
            "UPDATE users SET role = 'user' WHERE id = %s", (user_id,)
        )
        cur._connection.commit()
        cur.close()
