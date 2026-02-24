"""
routes/recurring.py
Manage recurring expenses (subscriptions, EMI, rent, etc).
"""

from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from flask_wtf import FlaskForm
from wtforms import StringField, DecimalField, SelectField, IntegerField
from wtforms.validators import DataRequired, NumberRange, Length

from models.recurring import Recurring
from models.expense import Expense

recurring_bp = Blueprint("recurring", __name__)


class RecurringForm(FlaskForm):
    description  = StringField("Description", validators=[DataRequired(), Length(max=255)])
    amount       = DecimalField("Amount (₹)", validators=[
        DataRequired(), NumberRange(min=0.01)
    ], places=2)
    category_id  = SelectField("Category", coerce=int, validators=[DataRequired()])
    day_of_month = IntegerField("Day of Month (1–28)", validators=[
        DataRequired(), NumberRange(min=1, max=28)
    ])

    def populate_categories(self):
        cats = Expense.get_all_categories()
        self.category_id.choices = [(c["id"], c["name"]) for c in cats]


@recurring_bp.route("/recurring", methods=["GET", "POST"])
@login_required
def manage_recurring():
    form = RecurringForm()
    form.populate_categories()

    if form.validate_on_submit():
        Recurring.create(
            user_id=current_user.id,
            category_id=form.category_id.data,
            amount=form.amount.data,
            description=form.description.data.strip(),
            day_of_month=form.day_of_month.data,
        )
        flash("Recurring expense added.", "success")
        return redirect(url_for("recurring.manage_recurring"))

    entries = Recurring.get_all(current_user.id)
    return render_template("recurring/manage.html", form=form, entries=entries)


@recurring_bp.route("/recurring/<int:rec_id>/toggle", methods=["POST"])
@login_required
def toggle_recurring(rec_id):
    Recurring.toggle_active(rec_id, current_user.id)
    return redirect(url_for("recurring.manage_recurring"))


@recurring_bp.route("/recurring/<int:rec_id>/delete", methods=["POST"])
@login_required
def delete_recurring(rec_id):
    Recurring.delete(rec_id, current_user.id)
    flash("Recurring expense removed.", "info")
    return redirect(url_for("recurring.manage_recurring"))
