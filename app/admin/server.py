"""Application factory and local HTTP server runner for JARVIS Admin Dashboard."""

import os
import secrets
from datetime import timedelta
from flask import Flask, redirect, url_for
from app.config import ADMIN_HOST, ADMIN_PORT, ADMIN_SECRET_KEY
from app.admin.routes import admin_bp


def create_app(secret_key=None, test_config=None):
    """Create and configure the Flask Admin Dashboard application."""
    app = Flask(
        __name__,
        template_folder=os.path.join(os.path.dirname(__file__), "templates"),
        static_folder=os.path.join(os.path.dirname(__file__), "static"),
    )

    # Use configured secret key or generate a cryptographically strong random token
    app.secret_key = secret_key or ADMIN_SECRET_KEY or secrets.token_hex(32)

    # Secure local session cookie policies
    app.config["PERMANENT_SESSION_LIFETIME"] = timedelta(hours=8)
    app.config["SESSION_COOKIE_HTTPONLY"] = True
    app.config["SESSION_COOKIE_SAMESITE"] = "Lax"

    if test_config:
        app.config.update(test_config)

    # Context processor to expose csrf_token() in all templates
    from app.admin.csrf import generate_csrf_token

    @app.context_processor
    def inject_csrf_token():
        return dict(csrf_token=generate_csrf_token)

    # Register Admin Blueprint
    app.register_blueprint(admin_bp, url_prefix="/admin")

    @app.route("/")
    def root():
        return redirect(url_for("admin.index"))

    return app


def run_admin_server(host=None, port=None):
    """Run the Admin Dashboard server bound locally."""
    host = host or ADMIN_HOST or "127.0.0.1"
    port = port or ADMIN_PORT or 5005
    app = create_app()
    print(f"JARVIS Admin Dashboard running locally on http://{host}:{port}/admin")
    app.run(host=host, port=port, debug=False, use_reloader=False)


if __name__ == "__main__":
    run_admin_server()
