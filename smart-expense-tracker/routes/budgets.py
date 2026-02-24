"""
routes/budgets.py
Set and manage monthly + category-wise budgets.
"""

from datetime import date
from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from flask_wtf import FlaskForm
from wtforms import DecimalField, SelectField, HiddenField
from wtforms.validators import DataRequired, NumberRange, Optional

from models.budget import Budget
from models.expense import Expense

budgets_bp = Blueprint("budgets", __name__)


class BudgetForm(FlaskForm):
    category_id = SelectField("Category (or Overall)", coerce=int)
    amount      = DecimalField("Budget Amount (₹)", validators=[
        DataRequired(), NumberRange(min=1)
    ], places=2)

    def populate_categories(self):
        cats = Expense.get_all_categories()
        self.category_id.choices = [(0, "— Overall Monthly Budget —")] + [
            (c["id"], c["name"]) for c in cats
        ]


@budgets_bp.route("/budgets", methods=["GET", "POST"])
@login_required
def manage_budgets():
    month = date.today().strftime("%Y-%m")
    form  = BudgetForm()
    form.populate_categories()

    if form.validate_on_submit():
        cat_id = form.category_id.data or None  # 0 → None = overall
        Budget.set(
            user_id=current_user.id,
            month=month,
            amount=form.amount.data,
            category_id=cat_id
        )
        flash("Budget saved successfully.", "success")
        return redirect(url_for("budgets.manage_budgets"))

    budgets = Budget.get_status_for_month(current_user.id, month)
    return render_template("budgets/manage.html",
                           form=form, budgets=budgets, month=month)


@budgets_bp.route("/budgets/<int:budget_id>/delete", methods=["POST"])
@login_required
def delete_budget(budget_id):
    Budget.delete(budget_id, current_user.id)
    flash("Budget removed.", "info")
    return redirect(url_for("budgets.manage_budgets"))
