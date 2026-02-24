"""
routes/auth.py
Registration, login, logout. CSRF-protected via Flask-WTF.
"""

import re
from flask import Blueprint, render_template, redirect, url_for, flash, request, session
from flask_login import login_user, logout_user, login_required, current_user
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField
from wtforms.validators import DataRequired, Length, Email, EqualTo, ValidationError

from models.user import User
from extensions import bcrypt

auth_bp = Blueprint("auth", __name__)


class RegisterForm(FlaskForm):
    # Use StringField instead of EmailField for broader compatibility
    username = StringField("Username", validators=[
        DataRequired(), Length(min=3, max=50)
    ])
    email    = StringField("Email", validators=[
        DataRequired(), Email(message="Enter a valid email address.")
    ])
    password = PasswordField("Password", validators=[
        DataRequired(), Length(min=8, message="Password must be at least 8 characters.")
    ])
    confirm  = PasswordField("Confirm Password", validators=[
        DataRequired(), EqualTo("password", message="Passwords must match.")
    ])

    def validate_username(self, field):
        if not re.match(r'^[A-Za-z0-9_]+$', field.data):
            raise ValidationError("Letters, numbers and underscores only.")
        if User.username_exists(field.data):
            raise ValidationError("Username already taken.")

    def validate_email(self, field):
        if User.email_exists(field.data.strip().lower()):
            raise ValidationError("Email already registered.")


class LoginForm(FlaskForm):
    email    = StringField("Email", validators=[
        DataRequired(), Email(message="Enter a valid email address.")
    ])
    password = PasswordField("Password", validators=[DataRequired()])


@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for("main.dashboard"))
    form = RegisterForm()
    if form.validate_on_submit():
        hashed = bcrypt.generate_password_hash(form.password.data).decode("utf-8")
        User.create(
            form.username.data.strip(),
            form.email.data.strip().lower(),
            hashed
        )
        flash("Account created! Please log in.", "success")
        return redirect(url_for("auth.login"))
    return render_template("auth/register.html", form=form)


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("main.dashboard"))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.get_by_email(form.email.data.strip().lower())
        if user and bcrypt.check_password_hash(user.password, form.password.data):
            login_user(user)
            session.permanent = True
            next_page = request.args.get("next")
            flash("Welcome back, {}!".format(user.username), "success")
            return redirect(next_page or url_for("main.dashboard"))
        flash("Invalid email or password.", "danger")
    return render_template("auth/login.html", form=form)


@auth_bp.route("/logout")
@login_required
def logout():
    logout_user()
    flash("You have been logged out.", "info")
    return redirect(url_for("auth.login"))
