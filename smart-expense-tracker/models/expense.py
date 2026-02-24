"""
models/expense.py
Expense model — MySQL 8, dict cursors, full analytics including smart metrics.
"""

from db import get_cursor


class Expense:

    # ── CRUD ─────────────────────────────────────────────────

    @staticmethod
    def create(user_id, category_id, amount, description, date):
        cur = get_cursor()
        cur.execute(
            """INSERT INTO expenses (user_id, category_id, amount, description, date)
               VALUES (%s, %s, %s, %s, %s)""",
            (user_id, category_id, amount, description, date)
        )
        cur._connection.commit()
        last_id = cur.lastrowid
        cur.close()
        return last_id

    @staticmethod
    def get_by_id(expense_id, user_id):
        cur = get_cursor()
        cur.execute(
            """SELECT e.*, c.name AS category_name
               FROM expenses e JOIN categories c ON c.id = e.category_id
               WHERE e.id = %s AND e.user_id = %s""",
            (expense_id, user_id)
        )
        row = cur.fetchone()
        cur.close()
        return row

    @staticmethod
    def get_all(user_id, date_from=None, date_to=None, category_id=None,
                search=None, amount_min=None, amount_max=None, sort="date_desc"):
        query = """
            SELECT e.id, e.amount, e.description, e.date,
                   c.name AS category_name, e.category_id, e.created_at
            FROM expenses e
            JOIN categories c ON c.id = e.category_id
            WHERE e.user_id = %s
        """
        params = [user_id]

        if date_from:
            query += " AND e.date >= %s"
            params.append(date_from)
        if date_to:
            query += " AND e.date <= %s"
            params.append(date_to)
        if category_id:
            query += " AND e.category_id = %s"
            params.append(category_id)
        if search:
            query += " AND e.description LIKE %s"
            params.append(f"%{search}%")
        if amount_min is not None:
            query += " AND e.amount >= %s"
            params.append(amount_min)
        if amount_max is not None:
            query += " AND e.amount <= %s"
            params.append(amount_max)

        sort_map = {
            "date_desc":    "e.date DESC, e.id DESC",
            "date_asc":     "e.date ASC,  e.id ASC",
            "amount_desc":  "e.amount DESC",
            "amount_asc":   "e.amount ASC",
        }
        query += " ORDER BY " + sort_map.get(sort, "e.date DESC, e.id DESC")

        cur = get_cursor()
        cur.execute(query, params)
        rows = cur.fetchall()
        cur.close()
        return rows

    @staticmethod
    def update(expense_id, user_id, category_id, amount, description, date):
        cur = get_cursor()
        cur.execute(
            """UPDATE expenses
               SET category_id=%s, amount=%s, description=%s, date=%s
               WHERE id=%s AND user_id=%s""",
            (category_id, amount, description, date, expense_id, user_id)
        )
        cur._connection.commit()
        cur.close()

    @staticmethod
    def delete(expense_id, user_id):
        cur = get_cursor()
        cur.execute(
            "DELETE FROM expenses WHERE id = %s AND user_id = %s",
            (expense_id, user_id)
        )
        cur._connection.commit()
        cur.close()

    # ── Category helpers ──────────────────────────────────────

    @staticmethod
    def get_all_categories():
        cur = get_cursor()
        cur.execute("SELECT id, name FROM categories ORDER BY name")
        rows = cur.fetchall()
        cur.close()
        return rows

    # ── Analytics ─────────────────────────────────────────────

    @staticmethod
    def get_monthly_total(user_id):
        cur = get_cursor()
        cur.execute(
            """SELECT DATE_FORMAT(date, '%%Y-%%m') AS month,
                      SUM(amount)                  AS total
               FROM expenses
               WHERE user_id = %s
                 AND date >= DATE_SUB(CURDATE(), INTERVAL 12 MONTH)
               GROUP BY month
               ORDER BY month""",
            (user_id,)
        )
        rows = cur.fetchall()
        cur.close()
        return rows

    @staticmethod
    def get_category_distribution(user_id):
        """Category totals for current month."""
        cur = get_cursor()
        cur.execute(
            """SELECT c.name AS category, SUM(e.amount) AS total
               FROM expenses e
               JOIN categories c ON c.id = e.category_id
               WHERE e.user_id = %s
                 AND DATE_FORMAT(e.date, '%%Y-%%m') = DATE_FORMAT(CURDATE(), '%%Y-%%m')
               GROUP BY c.id, c.name
               ORDER BY total DESC""",
            (user_id,)
        )
        rows = cur.fetchall()
        cur.close()
        return rows

    @staticmethod
    def get_current_month_total(user_id):
        cur = get_cursor()
        cur.execute(
            """SELECT COALESCE(SUM(amount), 0) AS total
               FROM expenses
               WHERE user_id = %s
                 AND DATE_FORMAT(date, '%%Y-%%m') = DATE_FORMAT(CURDATE(), '%%Y-%%m')""",
            (user_id,)
        )
        row = cur.fetchone()
        cur.close()
        return float(row["total"]) if row else 0.0

    @staticmethod
    def get_last_month_total(user_id):
        cur = get_cursor()
        cur.execute(
            """SELECT COALESCE(SUM(amount), 0) AS total
               FROM expenses
               WHERE user_id = %s
                 AND DATE_FORMAT(date, '%%Y-%%m') = DATE_FORMAT(
                       DATE_SUB(CURDATE(), INTERVAL 1 MONTH), '%%Y-%%m')""",
            (user_id,)
        )
        row = cur.fetchone()
        cur.close()
        return float(row["total"]) if row else 0.0

    @staticmethod
    def get_top_category(user_id):
        cur = get_cursor()
        cur.execute(
            """SELECT c.name AS category, SUM(e.amount) AS total
               FROM expenses e
               JOIN categories c ON c.id = e.category_id
               WHERE e.user_id = %s
                 AND DATE_FORMAT(e.date, '%%Y-%%m') = DATE_FORMAT(CURDATE(), '%%Y-%%m')
               GROUP BY c.id, c.name
               ORDER BY total DESC
               LIMIT 1""",
            (user_id,)
        )
        row = cur.fetchone()
        cur.close()
        return row

    @staticmethod
    def get_top3_categories(user_id):
        """Top 3 spending categories this month."""
        cur = get_cursor()
        cur.execute(
            """SELECT c.name AS category, SUM(e.amount) AS total
               FROM expenses e
               JOIN categories c ON c.id = e.category_id
               WHERE e.user_id = %s
                 AND DATE_FORMAT(e.date, '%%Y-%%m') = DATE_FORMAT(CURDATE(), '%%Y-%%m')
               GROUP BY c.id, c.name
               ORDER BY total DESC
               LIMIT 3""",
            (user_id,)
        )
        rows = cur.fetchall()
        cur.close()
        return rows

    @staticmethod
    def get_avg_daily_spend(user_id):
        """Average daily spend for current month (days elapsed so far)."""
        cur = get_cursor()
        cur.execute(
            """SELECT COALESCE(SUM(amount), 0) AS total,
                      DAY(CURDATE()) AS days_elapsed
               FROM expenses
               WHERE user_id = %s
                 AND DATE_FORMAT(date, '%%Y-%%m') = DATE_FORMAT(CURDATE(), '%%Y-%%m')""",
            (user_id,)
        )
        row = cur.fetchone()
        cur.close()
        if row and row["days_elapsed"]:
            return float(row["total"]) / row["days_elapsed"]
        return 0.0

    @staticmethod
    def get_predicted_next_month(user_id):
        """Predict next month spend using 3-month moving average."""
        cur = get_cursor()
        cur.execute(
            """SELECT SUM(amount) AS total
               FROM expenses
               WHERE user_id = %s
                 AND date >= DATE_SUB(DATE_FORMAT(CURDATE(), '%%Y-%%m-01'), INTERVAL 3 MONTH)
                 AND date <  DATE_FORMAT(CURDATE(), '%%Y-%%m-01')
               """,
            (user_id,)
        )
        row = cur.fetchone()
        cur.close()
        if row and row["total"]:
            return float(row["total"]) / 3
        return 0.0

    @staticmethod
    def get_recent(user_id, limit=5):
        cur = get_cursor()
        cur.execute(
            """SELECT e.id, e.amount, e.description, e.date,
                      c.name AS category_name
               FROM expenses e
               JOIN categories c ON c.id = e.category_id
               WHERE e.user_id = %s
               ORDER BY e.date DESC, e.id DESC
               LIMIT %s""",
            (user_id, limit)
        )
        rows = cur.fetchall()
        cur.close()
        return rows

    @staticmethod
    def get_total_by_user(user_id):
        """All-time total for a user (used in admin)."""
        cur = get_cursor()
        cur.execute(
            "SELECT COALESCE(SUM(amount), 0) AS total FROM expenses WHERE user_id = %s",
            (user_id,)
        )
        row = cur.fetchone()
        cur.close()
        return float(row["total"]) if row else 0.0

    @staticmethod
    def export_all(user_id, date_from=None, date_to=None, category_id=None):
        """All expenses for export (CSV/PDF) — same filters as get_all."""
        return Expense.get_all(user_id, date_from, date_to, category_id)
