"""
models/recurring.py
Recurring expense management (subscriptions, EMI, rent, etc).
Auto-insert logic checks if current-month expense already exists before inserting.
"""

from datetime import date
from db import get_cursor


class Recurring:

    @staticmethod
    def get_all(user_id):
        cur = get_cursor()
        cur.execute(
            """SELECT r.id, r.category_id, r.amount, r.description,
                      r.day_of_month, r.active, r.created_at,
                      c.name AS category_name
               FROM recurring_expenses r
               JOIN categories c ON c.id = r.category_id
               WHERE r.user_id = %s
               ORDER BY r.active DESC, r.description""",
            (user_id,)
        )
        rows = cur.fetchall()
        cur.close()
        return rows

    @staticmethod
    def create(user_id, category_id, amount, description, day_of_month=1):
        cur = get_cursor()
        cur.execute(
            """INSERT INTO recurring_expenses
               (user_id, category_id, amount, description, day_of_month, active)
               VALUES (%s, %s, %s, %s, %s, 1)""",
            (user_id, category_id, amount, description, day_of_month)
        )
        cur._connection.commit()
        last_id = cur.lastrowid
        cur.close()
        return last_id

    @staticmethod
    def toggle_active(rec_id, user_id):
        cur = get_cursor()
        cur.execute(
            """UPDATE recurring_expenses
               SET active = NOT active
               WHERE id = %s AND user_id = %s""",
            (rec_id, user_id)
        )
        cur._connection.commit()
        cur.close()

    @staticmethod
    def delete(rec_id, user_id):
        cur = get_cursor()
        cur.execute(
            "DELETE FROM recurring_expenses WHERE id = %s AND user_id = %s",
            (rec_id, user_id)
        )
        cur._connection.commit()
        cur.close()

    @staticmethod
    def auto_insert_for_month(user_id, year, month):
        """
        For each active recurring expense, insert into expenses for the given
        year/month if not already present (idempotent).
        Returns count of newly inserted expenses.
        """
        cur = get_cursor()
        cur.execute(
            """SELECT * FROM recurring_expenses
               WHERE user_id = %s AND active = 1""",
            (user_id,)
        )
        recurrings = cur.fetchall()
        cur.close()

        inserted = 0
        for rec in recurrings:
            # Clamp day_of_month to valid range for the month
            import calendar
            max_day = calendar.monthrange(year, month)[1]
            day     = min(rec["day_of_month"], max_day)
            exp_date = date(year, month, day)

            # Check if already inserted this month
            cur = get_cursor()
            cur.execute(
                """SELECT COUNT(*) AS cnt FROM expenses
                   WHERE user_id = %s AND category_id = %s
                     AND amount = %s AND description = %s
                     AND DATE_FORMAT(date, '%%Y-%%m') = %s""",
                (user_id, rec["category_id"], rec["amount"],
                 rec["description"], f"{year:04d}-{month:02d}")
            )
            exists = cur.fetchone()["cnt"] > 0
            cur.close()

            if not exists:
                cur = get_cursor()
                cur.execute(
                    """INSERT INTO expenses
                       (user_id, category_id, amount, description, date)
                       VALUES (%s, %s, %s, %s, %s)""",
                    (user_id, rec["category_id"], rec["amount"],
                     rec["description"], exp_date)
                )
                cur._connection.commit()
                cur.close()
                inserted += 1

        return inserted
