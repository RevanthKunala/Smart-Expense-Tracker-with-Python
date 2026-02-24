"""
models/budget.py
Budget goal management — monthly overall + per-category budgets.
"""

from db import get_cursor


class Budget:

    @staticmethod
    def set(user_id, month, amount, category_id=None):
        """Upsert a budget. month is 'YYYY-MM'. category_id=None → overall budget."""
        cur = get_cursor()
        cur.execute(
            """INSERT INTO budgets (user_id, category_id, month, amount)
               VALUES (%s, %s, %s, %s)
               ON DUPLICATE KEY UPDATE amount = VALUES(amount)""",
            (user_id, category_id, month, amount)
        )
        cur._connection.commit()
        cur.close()

    @staticmethod
    def get_for_month(user_id, month):
        """Return all budgets for a given month as list of dicts."""
        cur = get_cursor()
        cur.execute(
            """SELECT b.id, b.category_id, b.month, b.amount,
                      c.name AS category_name
               FROM budgets b
               LEFT JOIN categories c ON c.id = b.category_id
               WHERE b.user_id = %s AND b.month = %s""",
            (user_id, month)
        )
        rows = cur.fetchall()
        cur.close()
        return rows

    @staticmethod
    def get_overall(user_id, month):
        """Return the overall monthly budget (category_id IS NULL), or None."""
        cur = get_cursor()
        cur.execute(
            """SELECT amount FROM budgets
               WHERE user_id = %s AND month = %s AND category_id IS NULL""",
            (user_id, month)
        )
        row = cur.fetchone()
        cur.close()
        return float(row["amount"]) if row else None

    @staticmethod
    def delete(budget_id, user_id):
        cur = get_cursor()
        cur.execute(
            "DELETE FROM budgets WHERE id = %s AND user_id = %s",
            (budget_id, user_id)
        )
        cur._connection.commit()
        cur.close()

    @staticmethod
    def get_status_for_month(user_id, month):
        """
        Returns a list of budget status dicts for dashboard display.
        Each dict: { label, budget, spent, pct, over_80, overspent }
        """
        cur = get_cursor()
        # Overall budget
        cur.execute(
            """SELECT b.id, b.category_id, b.amount AS budget_amt,
                      COALESCE((
                          SELECT SUM(e.amount)
                          FROM expenses e
                          WHERE e.user_id = %s
                            AND DATE_FORMAT(e.date, '%%Y-%%m') = %s
                            AND (%s IS NULL OR e.category_id = b.category_id)
                      ), 0) AS spent
               FROM budgets b
               WHERE b.user_id = %s AND b.month = %s
               ORDER BY b.category_id IS NOT NULL, b.category_id""",
            (user_id, month, None, user_id, month)
        )
        rows = cur.fetchall()
        cur.close()

        # Simpler — do two queries
        cur = get_cursor()
        cur.execute(
            """SELECT b.id, b.category_id, b.amount AS budget_amt,
                      c.name AS category_name
               FROM budgets b
               LEFT JOIN categories c ON c.id = b.category_id
               WHERE b.user_id = %s AND b.month = %s""",
            (user_id, month)
        )
        budgets = cur.fetchall()
        cur.close()

        result = []
        for b in budgets:
            cur = get_cursor()
            if b["category_id"] is None:
                cur.execute(
                    """SELECT COALESCE(SUM(amount), 0) AS spent FROM expenses
                       WHERE user_id = %s AND DATE_FORMAT(date, '%%Y-%%m') = %s""",
                    (user_id, month)
                )
            else:
                cur.execute(
                    """SELECT COALESCE(SUM(amount), 0) AS spent FROM expenses
                       WHERE user_id = %s AND category_id = %s
                         AND DATE_FORMAT(date, '%%Y-%%m') = %s""",
                    (user_id, b["category_id"], month)
                )
            spent_row = cur.fetchone()
            cur.close()

            spent  = float(spent_row["spent"])
            budget = float(b["budget_amt"])
            pct    = round((spent / budget * 100), 1) if budget > 0 else 0

            result.append({
                "id":           b["id"],
                "category_id":  b["category_id"],
                "label":        b["category_name"] if b["category_name"] else "Overall",
                "budget":       budget,
                "spent":        spent,
                "pct":          pct,
                "over_80":      pct >= 80 and pct < 100,
                "overspent":    pct >= 100,
            })

        return result
