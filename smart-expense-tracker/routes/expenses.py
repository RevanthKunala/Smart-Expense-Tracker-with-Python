"""
routes/expenses.py
Full CRUD for expenses + analytics JSON API + CSV/PDF export.
Advanced filtering: search, amount range, sort.
"""

import io
import csv
import json
from datetime import date

from flask import (Blueprint, render_template, redirect, url_for,
                   flash, request, current_app, abort, Response)
from flask_login import login_required, current_user
from flask_wtf import FlaskForm
from wtforms import StringField, DecimalField, SelectField, DateField
from wtforms.validators import DataRequired, NumberRange, Length

from models.expense import Expense
from models.budget import Budget
from models.recurring import Recurring

expenses_bp = Blueprint("expenses", __name__)


# ── Form ──────────────────────────────────────────────────────

class ExpenseForm(FlaskForm):
    amount      = DecimalField("Amount (₹)", validators=[
        DataRequired(), NumberRange(min=0.01, max=999999.99)
    ], places=2)
    category_id = SelectField("Category", coerce=int, validators=[DataRequired()])
    description = StringField("Description", validators=[DataRequired(), Length(max=255)])
    date        = DateField("Date", validators=[DataRequired()])

    def populate_categories(self):
        cats = Expense.get_all_categories()
        self.category_id.choices = [(c["id"], c["name"]) for c in cats]


# ── Helpers ───────────────────────────────────────────────────

def _owned_or_404(expense_id):
    row = Expense.get_by_id(expense_id, current_user.id)
    if not row:
        abort(404)
    return row


def _date_val(row_date):
    if isinstance(row_date, date):
        return row_date
    return date.fromisoformat(str(row_date))


# ── List ──────────────────────────────────────────────────────

@expenses_bp.route("/expenses")
@login_required
def list_expenses():
    date_from   = request.args.get("date_from")   or None
    date_to     = request.args.get("date_to")     or None
    category_id = request.args.get("category_id") or None
    search      = request.args.get("search")      or None
    amount_min  = request.args.get("amount_min")  or None
    amount_max  = request.args.get("amount_max")  or None
    sort        = request.args.get("sort", "date_desc")

    # Convert to correct types
    amount_min = float(amount_min) if amount_min else None
    amount_max = float(amount_max) if amount_max else None
    cat_id_int = int(category_id) if category_id else None

    expenses   = Expense.get_all(current_user.id, date_from, date_to, cat_id_int,
                                  search, amount_min, amount_max, sort)
    categories = Expense.get_all_categories()

    return render_template(
        "expenses/list.html",
        expenses=expenses,
        categories=categories,
        filters={
            "date_from":   date_from,
            "date_to":     date_to,
            "category_id": cat_id_int,
            "search":      search,
            "amount_min":  amount_min,
            "amount_max":  amount_max,
            "sort":        sort,
        },
    )


# ── Add ───────────────────────────────────────────────────────

@expenses_bp.route("/expenses/add", methods=["GET", "POST"])
@login_required
def add_expense():
    form = ExpenseForm()
    form.populate_categories()
    if form.validate_on_submit():
        Expense.create(
            user_id=current_user.id,
            category_id=form.category_id.data,
            amount=form.amount.data,
            description=form.description.data.strip(),
            date=form.date.data,
        )
        flash("Expense added successfully.", "success")
        return redirect(url_for("expenses.list_expenses"))
    if request.method == "GET":
        form.date.data = date.today()
    return render_template("expenses/form.html", form=form, action="Add")


# ── Edit ──────────────────────────────────────────────────────

@expenses_bp.route("/expenses/<int:expense_id>/edit", methods=["GET", "POST"])
@login_required
def edit_expense(expense_id):
    row  = _owned_or_404(expense_id)
    form = ExpenseForm()
    form.populate_categories()
    if form.validate_on_submit():
        Expense.update(
            expense_id=expense_id,
            user_id=current_user.id,
            category_id=form.category_id.data,
            amount=form.amount.data,
            description=form.description.data.strip(),
            date=form.date.data,
        )
        flash("Expense updated successfully.", "success")
        return redirect(url_for("expenses.list_expenses"))
    if request.method == "GET":
        form.amount.data      = row["amount"]
        form.category_id.data = row["category_id"]
        form.description.data = row["description"]
        form.date.data        = _date_val(row["date"])
    return render_template("expenses/form.html", form=form,
                           action="Edit", expense_id=expense_id)


# ── Delete ────────────────────────────────────────────────────

@expenses_bp.route("/expenses/<int:expense_id>/delete", methods=["POST"])
@login_required
def delete_expense(expense_id):
    _owned_or_404(expense_id)
    Expense.delete(expense_id, current_user.id)
    flash("Expense deleted.", "info")
    return redirect(url_for("expenses.list_expenses"))


# ── Export CSV ────────────────────────────────────────────────

@expenses_bp.route("/expenses/export/csv")
@login_required
def export_csv():
    expenses = Expense.export_all(current_user.id)
    output   = io.StringIO()
    writer   = csv.writer(output)
    writer.writerow(["Date", "Category", "Description", "Amount (₹)"])
    for exp in expenses:
        writer.writerow([
            str(exp["date"]),
            exp["category_name"],
            exp["description"],
            f"{float(exp['amount']):.2f}",
        ])
    output.seek(0)
    filename = f"expenses_{date.today().strftime('%Y%m%d')}.csv"
    return Response(
        output.getvalue(),
        mimetype="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )


# ── Export PDF ────────────────────────────────────────────────

@expenses_bp.route("/expenses/export/pdf")
@login_required
def export_pdf():
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.lib import colors
        from reportlab.lib.units import cm
        from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    except ImportError:
        flash("PDF export requires reportlab. Run: pip install reportlab", "danger")
        return redirect(url_for("expenses.list_expenses"))

    expenses = Expense.export_all(current_user.id)
    buffer   = io.BytesIO()
    doc      = SimpleDocTemplate(buffer, pagesize=A4,
                                 rightMargin=2*cm, leftMargin=2*cm,
                                 topMargin=2*cm, bottomMargin=2*cm)
    styles   = getSampleStyleSheet()
    story    = []

    # Title
    title_style = ParagraphStyle("title", parent=styles["Heading1"],
                                 fontSize=16, spaceAfter=8)
    story.append(Paragraph(f"Expense Report — {current_user.username}", title_style))
    story.append(Paragraph(f"Generated: {date.today().strftime('%d %b %Y')}", styles["Normal"]))
    story.append(Spacer(1, 0.5*cm))

    # Table
    header = ["Date", "Category", "Description", "Amount (₹)"]
    rows   = [header]
    total  = 0.0
    for exp in expenses:
        amt = float(exp["amount"])
        total += amt
        rows.append([
            str(exp["date"]),
            exp["category_name"],
            exp["description"][:50],
            f"₹{amt:,.2f}",
        ])
    rows.append(["", "", "TOTAL", f"₹{total:,.2f}"])

    t = Table(rows, colWidths=[3*cm, 3.5*cm, 8*cm, 3*cm])
    t.setStyle(TableStyle([
        ("BACKGROUND",  (0, 0), (-1,  0),  colors.HexColor("#6366f1")),
        ("TEXTCOLOR",   (0, 0), (-1,  0),  colors.white),
        ("FONTNAME",    (0, 0), (-1,  0),  "Helvetica-Bold"),
        ("FONTSIZE",    (0, 0), (-1,  0),  10),
        ("ALIGN",       (3, 0), (3, -1),   "RIGHT"),
        ("ROWBACKGROUNDS", (0, 1), (-1, -2), [colors.white, colors.HexColor("#f8fafc")]),
        ("BACKGROUND",  (0, -1), (-1, -1), colors.HexColor("#ede9fe")),
        ("FONTNAME",    (0, -1), (-1, -1), "Helvetica-Bold"),
        ("GRID",        (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
        ("TOPPADDING",  (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
    ]))
    story.append(t)
    doc.build(story)
    buffer.seek(0)
    filename = f"expenses_{date.today().strftime('%Y%m%d')}.pdf"
    return Response(
        buffer.getvalue(),
        mimetype="application/pdf",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )


# ── Analytics API ─────────────────────────────────────────────

@expenses_bp.route("/api/analytics")
@login_required
def analytics_api():
    try:
        from datetime import datetime
        now   = datetime.now()
        month = now.strftime("%Y-%m")

        # Auto-insert recurring expenses for this month
        Recurring.auto_insert_for_month(current_user.id, now.year, now.month)

        monthly_rows = Expense.get_monthly_total(current_user.id)
        cat_rows     = Expense.get_category_distribution(current_user.id)
        month_total  = Expense.get_current_month_total(current_user.id)
        last_total   = Expense.get_last_month_total(current_user.id)
        top_cat      = Expense.get_top_category(current_user.id)
        top3         = Expense.get_top3_categories(current_user.id)
        avg_daily    = Expense.get_avg_daily_spend(current_user.id)
        predicted    = Expense.get_predicted_next_month(current_user.id)
        recent       = Expense.get_recent(current_user.id, limit=5)
        budget_status = Budget.get_status_for_month(current_user.id, month)

        # Growth percentage vs last month
        if last_total > 0:
            growth_pct = round((month_total - last_total) / last_total * 100, 1)
        else:
            growth_pct = 0.0

        payload = {
            "monthly": {
                "labels": [r["month"] for r in monthly_rows],
                "data":   [float(r["total"]) for r in monthly_rows],
            },
            "category": {
                "labels": [r["category"] for r in cat_rows],
                "data":   [float(r["total"]) for r in cat_rows],
            },
            "month_total": float(month_total),
            "top_category": {
                "name":  top_cat["category"] if top_cat else "N/A",
                "total": float(top_cat["total"]) if top_cat else 0.0,
            },
            "smart": {
                "top3_categories": [
                    {"name": r["category"], "total": float(r["total"])} for r in top3
                ],
                "avg_daily_spend":   round(avg_daily, 2),
                "last_month_total":  float(last_total),
                "growth_pct":        growth_pct,
                "predicted_next":    round(predicted, 2),
            },
            "budgets": budget_status,
            "recent": [
                {
                    "id":          r["id"],
                    "amount":      float(r["amount"]),
                    "description": r["description"],
                    "date":        str(r["date"]),
                    "category":    r["category_name"],
                }
                for r in recent
            ],
        }

        return current_app.response_class(
            json.dumps(payload),
            mimetype="application/json"
        )

    except Exception as e:
        current_app.logger.error(f"Analytics error: {e}", exc_info=True)
        return current_app.response_class(
            json.dumps({"error": "Failed to load analytics"}),
            status=500, mimetype="application/json"
        )
