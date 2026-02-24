"""
routes/admin.py
Admin-only views. First registered user is auto-promoted to admin.
Access protected by @admin_required decorator.
"""

from functools import wraps
from flask import Blueprint, render_template, redirect, url_for, flash, abort
from flask_login import login_required, current_user

from models.user import User
from models.expense import Expense

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")


# ── Decorator ─────────────────────────────────────────────────

def admin_required(f):
    @wraps(f)
    @login_required
    def decorated(*args, **kwargs):
        if not current_user.is_admin():
            abort(403)
        return f(*args, **kwargs)
    return decorated


# ── Routes ────────────────────────────────────────────────────

@admin_bp.route("/")
@admin_required
def dashboard():
    users = User.get_all()
    # Annotate each user with their total spend
    for u in users:
        u["total_spent"] = Expense.get_total_by_user(u["id"])
    total_users    = len(users)
    total_expenses = sum(u["total_spent"] for u in users)
    return render_template("admin/dashboard.html",
                           users=users,
                           total_users=total_users,
                           total_expenses=total_expenses)


@admin_bp.route("/users/<int:user_id>/promote", methods=["POST"])
@admin_required
def promote_user(user_id):
    if user_id == current_user.id:
        flash("You're already an admin.", "warning")
    else:
        User.promote(user_id)
        flash("User promoted to admin.", "success")
    return redirect(url_for("admin.dashboard"))


@admin_bp.route("/users/<int:user_id>/demote", methods=["POST"])
@admin_required
def demote_user(user_id):
    if user_id == current_user.id:
        flash("You cannot demote yourself.", "danger")
    else:
        User.demote(user_id)
        flash("User demoted to regular user.", "info")
    return redirect(url_for("admin.dashboard"))
