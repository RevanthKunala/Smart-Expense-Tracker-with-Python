"""
app.py — Application factory (updated with new blueprints).
"""

import os
from flask import Flask, render_template
from extensions import bcrypt, login_manager, csrf
from config.settings import config_map
from db import get_db, close_db
from models.user import User


def create_app():
    app = Flask(__name__)

    # ── Config ────────────────────────────────────────────────
    env = os.environ.get("FLASK_ENV", "development")
    app.config.from_object(config_map.get(env, config_map["development"]))

    # ── Extensions ────────────────────────────────────────────
    bcrypt.init_app(app)
    login_manager.init_app(app)
    csrf.init_app(app)

    login_manager.login_view     = "auth.login"
    login_manager.login_message  = "Please log in to access this page."
    login_manager.login_message_category = "warning"

    @login_manager.user_loader
    def load_user(user_id):
        return User.get_by_id(int(user_id))

    # ── Database teardown ─────────────────────────────────────
    app.teardown_appcontext(close_db)

    # ── Blueprints ────────────────────────────────────────────
    from routes.auth      import auth_bp
    from routes.main      import main_bp
    from routes.expenses  import expenses_bp
    from routes.budgets   import budgets_bp
    from routes.recurring import recurring_bp
    from routes.admin     import admin_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(main_bp)
    app.register_blueprint(expenses_bp)
    app.register_blueprint(budgets_bp)
    app.register_blueprint(recurring_bp)
    app.register_blueprint(admin_bp)

    # ── Jinja2 filters ────────────────────────────────────────
    @app.template_filter("inr")
    def inr_filter(value):
        try:
            return "₹{:,.2f}".format(float(value))
        except (TypeError, ValueError):
            return "₹0.00"

    # ── Error handlers ────────────────────────────────────────
    @app.errorhandler(404)
    def not_found(e):
        return render_template("errors/404.html"), 404

    @app.errorhandler(403)
    def forbidden(e):
        return render_template("errors/403.html"), 403

    @app.errorhandler(500)
    def server_error(e):
        return render_template("errors/500.html"), 500

    return app


app = create_app()

if __name__ == "__main__":
    app.run()
