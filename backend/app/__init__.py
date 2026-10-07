import os
from flask import Flask
from dotenv import load_dotenv
from .extensions import db
from flask_cors import CORS
from werkzeug.exceptions import HTTPException


load_dotenv()

def create_app(test_config=None):
    app = Flask(__name__)

    # ── SECRET KEY ────────────────────────────────────────────────
    # Must be set via the SECRET_KEY environment variable.
    # A missing key at startup is a configuration error — fail fast.
    secret_key = os.environ.get("SECRET_KEY") or (test_config or {}).get("SECRET_KEY")
    if not secret_key:
        raise RuntimeError(
            "SECRET_KEY environment variable is not set. "
            "Add it to backend/.env before running."
        )
    app.config["SECRET_KEY"] = secret_key

    # ── CORS ──────────────────────────────────────────────────────
    # CORS_ORIGINS: comma-separated list of allowed frontend origins.
    # ALLOWED_ORIGINS remains supported for existing deployments.
    raw_origins = (
        (test_config or {}).get("CORS_ORIGINS")
        or os.environ.get("CORS_ORIGINS")
        or os.environ.get("ALLOWED_ORIGINS")
        or "http://localhost:5173"
    )
    if isinstance(raw_origins, str):
        allowed_origins = [o.strip() for o in raw_origins.split(",") if o.strip()]
    else:
        allowed_origins = [o.strip() for o in raw_origins if o.strip()]
    if not allowed_origins or "*" in allowed_origins:
        raise RuntimeError(
            "CORS_ORIGINS must contain explicit origins when credentialed CORS is enabled."
        )
    app.config["CORS_ORIGINS"] = allowed_origins
    CORS(app,
         supports_credentials=True,
         origins=allowed_origins,
         )

    # ── DATABASE ──────────────────────────────────────────────────
    app.config["SQLALCHEMY_DATABASE_URI"] = (
        os.environ.get("DATABASE_URL") or "sqlite:///plutii.db"
    )
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    # ── SESSION COOKIES ───────────────────────────────────────────
    # HttpOnly: browser JS cannot read the session cookie (always on).
    app.config["SESSION_COOKIE_HTTPONLY"] = True

    # Secure: only send the cookie over HTTPS.
    # Set COOKIE_SECURE=true in your production .env.
    # Leave unset (or set to anything else) for local HTTP dev.
    session_cookie_secure = (
        os.environ.get("COOKIE_SECURE", "false").lower() == "true"
    )
    app.config["SESSION_COOKIE_SECURE"] = session_cookie_secure

    # Localhost ports are cross-origin but same-site; production Vercel and
    # Render hosts are cross-site and require SameSite=None over HTTPS.
    app.config["SESSION_COOKIE_SAMESITE"] = (
        "None" if session_cookie_secure else "Lax"
    )
    if test_config:
        app.config.update(test_config)
    app.config["CORS_ORIGINS"] = allowed_origins

    # ── INIT DB ───────────────────────────────────────────────────
    db.init_app(app)

    # Import models before create_all so SQLAlchemy registers every table.
    from . import models  # noqa: F401

    # Add the small documented provenance columns before create_all attempts
    # to build their indexes on legacy tables.
    with app.app_context():
        from .schema_compat import ensure_provenance_columns
        ensure_provenance_columns()
        # Create missing tables; this does not drop existing database tables.
        db.create_all()

    # Authentication/session infrastructure is shared across future roles.
    from .auth.routes import auth_bp
    app.register_blueprint(auth_bp)

    from .harbour.routes import harbour_bp
    from .market.routes import market_bp
    from .species.routes import species_bp
    from .buyers.routes import buyers_bp
    from .resources.routes import resources_bp
    from .auction.routes import auction_bp
    from .announcements.routes import announcements_bp, alerts_bp
    from .decision.routes import decision_bp
    from .ai.routes import ai_bp
    from .health.routes import health_bp
    for blueprint in (
        harbour_bp,
        market_bp,
        species_bp,
        buyers_bp,
        resources_bp,
        auction_bp,
        announcements_bp,
        alerts_bp,
        decision_bp,
        ai_bp,
        health_bp,
    ):
        app.register_blueprint(blueprint)

    from app.api.errors import APIError, error_payload

    @app.errorhandler(APIError)
    def handle_api_error(error):
        return {"error": {"code": error.code, "message": error.message}}, error.status_code

    @app.errorhandler(HTTPException)
    def handle_http_error(error):
        code = "not_found" if error.code == 404 else "http_error"
        return error_payload(error.description, code), error.code

    @app.errorhandler(Exception)
    def handle_unexpected_error(_error):
        app.logger.exception("Unhandled API error")
        return error_payload("An unexpected server error occurred.", "internal_error"), 500

    return app
