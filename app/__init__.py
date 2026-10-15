import os

from flask import Flask, render_template, request, url_for
from sqlalchemy import event
from sqlalchemy.engine import Engine

from .config import Config
from .extensions import csrf, db, limiter, login_manager
from .models import RARITIES, RARITY_LABELS, User


@event.listens_for(Engine, "connect")
def _sqlite_pragmas(dbapi_conn, _record):
    """SQLite : intégrité des clés étrangères et écritures concurrentes."""
    if dbapi_conn.__class__.__module__.startswith("sqlite3"):
        cur = dbapi_conn.cursor()
        cur.execute("PRAGMA foreign_keys=ON")
        cur.execute("PRAGMA journal_mode=WAL")
        cur.execute("PRAGMA synchronous=NORMAL")
        cur.close()


def create_app(config_object=Config) -> Flask:
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_object(config_object)
    if app.config["SESSION_COOKIE_SECURE"] and app.config["SECRET_KEY"] == "dev-only-change-me":
        raise RuntimeError("SECRET_KEY par défaut interdit en production (COOKIE_SECURE=true).")

    db.init_app(app)
    csrf.init_app(app)
    limiter.init_app(app)
    login_manager.init_app(app)

    @login_manager.user_loader
    def load_user(user_id: str):
        return db.session.get(User, int(user_id))

    from .blueprints.album import bp as album_bp
    from .blueprints.auth import bp as auth_bp
    from .blueprints.main import bp as main_bp
    from .blueprints.packs import bp as packs_bp

    for bp in (main_bp, auth_bp, packs_bp, album_bp):
        app.register_blueprint(bp)

    register_template_helpers(app)
    register_security_headers(app)
    register_error_handlers(app)

    with app.app_context():
        db.create_all()
    return app


def register_template_helpers(app: Flask) -> None:
    @app.template_filter("thousands")
    def thousands(value) -> str:
        return f"{int(value):,}".replace(",", " ")

    @app.template_global("asset")
    def asset(filename: str) -> str:
        """URL d'un fichier statique avec ?v=<date de modification> : cache longue durée sans
        risque de servir une ancienne version après une mise à jour."""
        path = os.path.join(app.static_folder, filename)
        try:
            version = int(os.path.getmtime(path))
        except OSError:
            version = 0
        return url_for("static", filename=filename, v=version)

    # Globals : disponibles aussi dans les macros importées (sans « with context »)
    app.jinja_env.globals.update(RARITIES=RARITIES, RARITY_LABELS=RARITY_LABELS)

    @app.context_processor
    def inject_globals():
        from .services import captcha

        return {
            "captcha_enabled": captcha.is_enabled(),
            "cap_endpoint": app.config["CAP_ENDPOINT"],
            "cap_site_key": app.config["CAP_SITE_KEY"],
            "cap_widget_url": app.config["CAP_WIDGET_URL"],
            "free_interval_hours": int(app.config["FREE_PACK_INTERVAL"].total_seconds() // 3600),
            "paid_pack_price": app.config["PAID_PACK_PRICE"],
            "pack_size": app.config["PACK_SIZE"],
        }


def register_security_headers(app: Flask) -> None:
    @app.after_request
    def headers(resp):
        cap = app.config["CAP_ENDPOINT"]
        csp = [
            "default-src 'self'",
            "img-src 'self' https://*.wikimedia.org data:",
            "script-src 'self' https://cdn.jsdelivr.net 'wasm-unsafe-eval'",
            "style-src 'self' 'unsafe-inline'",
            "font-src 'self' data:",
            f"connect-src 'self' https://cdn.jsdelivr.net {cap}".strip(),
            "worker-src 'self' blob:",
            "frame-ancestors 'none'",
            "base-uri 'self'",
            "form-action 'self'",
        ]
        resp.headers.setdefault("Content-Security-Policy", "; ".join(csp))
        resp.headers.setdefault("X-Content-Type-Options", "nosniff")
        resp.headers.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
        resp.headers.setdefault("X-Frame-Options", "DENY")
        if request.endpoint == "static":
            # « immutable » seulement si l'URL est versionnée (?v=…) ; sinon revalidation
            if request.args.get("v") or request.path.startswith("/static/fonts/"):
                resp.headers["Cache-Control"] = "public, max-age=31536000, immutable"
            else:
                resp.headers["Cache-Control"] = "no-cache"
        elif request.method == "GET" and "Cache-Control" not in resp.headers:
            resp.headers["Cache-Control"] = "no-cache"
        return resp


def register_error_handlers(app: Flask) -> None:
    @app.errorhandler(404)
    def not_found(_e):
        return render_template("errors/404.html"), 404

    @app.errorhandler(429)
    def too_many(_e):
        return render_template("errors/429.html"), 429

    @app.errorhandler(500)
    def server_error(_e):
        db.session.rollback()
        return render_template("errors/500.html"), 500
