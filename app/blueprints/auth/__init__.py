import re
from urllib.parse import urlparse

from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required, login_user, logout_user
from sqlalchemy import func, or_
from sqlalchemy.exc import IntegrityError
from werkzeug.security import check_password_hash, generate_password_hash

from ...extensions import db, limiter
from ...models import Ledger, User
from ...services import captcha
from flask import current_app

bp = Blueprint("auth", __name__)

PSEUDO_RE = re.compile(r"^[A-Za-z0-9_-]{3,24}$")
EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]{2,}$")
MIN_PASSWORD = 10
# Hash factice pour que la durée de réponse ne révèle pas si un compte existe
_DUMMY_HASH = generate_password_hash("not-a-real-password")


def _safe_next(target: str | None) -> str | None:
    """N'accepte que des chemins relatifs du site (évite la redirection ouverte)."""
    if not target:
        return None
    parts = urlparse(target)
    if parts.scheme or parts.netloc or not target.startswith("/") or target.startswith("//"):
        return None
    return target


@bp.route("/inscription", methods=["GET", "POST"])
@limiter.limit("5 per hour", methods=["POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for("packs.index"))
    errors: dict[str, str] = {}
    form = {"pseudo": "", "email": ""}
    if request.method == "POST":
        pseudo = request.form.get("pseudo", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        form = {"pseudo": pseudo, "email": email}

        if not PSEUDO_RE.match(pseudo):
            errors["pseudo"] = "3 à 24 caractères : lettres, chiffres, tiret ou tiret bas (pas d’espace)."
        if not EMAIL_RE.match(email) or len(email) > 254:
            errors["email"] = "Adresse incomplète : il faut un domaine (par exemple exemple.fr)."
        if len(password) < MIN_PASSWORD:
            errors["password"] = (
                f"{MIN_PASSWORD} caractères minimum (il en manque {MIN_PASSWORD - len(password)})."
            )
        if not request.form.get("adult"):
            errors["adult"] = "Tu dois confirmer avoir au moins 18 ans."
        if not request.form.get("terms"):
            errors["terms"] = "Tu dois accepter les conditions d’utilisation."
        if not errors:
            exists = db.session.execute(
                db.select(User.id).where(
                    or_(func.lower(User.pseudo) == pseudo.lower(), User.email == email)
                )
            ).first()
            if exists:
                errors["pseudo"] = "Ce nom d’utilisateur ou cette adresse est déjà utilisé."
        if not errors and not captcha.verify(request.form.get(captcha.TOKEN_FIELD)):
            errors["captcha"] = "Vérification échouée, réessaie."

        if not errors:
            user = User(
                pseudo=pseudo,
                email=email,
                password_hash=generate_password_hash(password),
                coins=current_app.config["START_COINS"],
            )
            db.session.add(user)
            try:
                db.session.flush()
                db.session.add(Ledger(user_id=user.id, delta=user.coins, reason="bonus"))
                db.session.commit()
            except IntegrityError:
                db.session.rollback()
                errors["pseudo"] = "Ce nom d’utilisateur ou cette adresse est déjà utilisé."
            else:
                login_user(user)
                flash("Compte créé. Ton premier paquet gratuit t’attend.", "success")
                return redirect(url_for("packs.index"))
    status = 422 if errors else 200
    return render_template("pages/register.html", errors=errors, form=form), status


@bp.route("/connexion", methods=["GET", "POST"])
@limiter.limit("10 per minute", methods=["POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("packs.index"))
    errors: dict[str, str] = {}
    identifier = ""
    if request.method == "POST":
        identifier = request.form.get("identifier", "").strip()
        password = request.form.get("password", "")
        user = db.session.execute(
            db.select(User).where(
                or_(func.lower(User.pseudo) == identifier.lower(), User.email == identifier.lower())
            )
        ).scalar_one_or_none()
        ok = check_password_hash(user.password_hash if user else _DUMMY_HASH, password)
        if not (user and ok):
            errors["form"] = "Identifiant ou mot de passe incorrect."
        elif not captcha.verify(request.form.get(captcha.TOKEN_FIELD)):
            errors["captcha"] = "Vérification échouée, réessaie."
        else:
            login_user(user, remember=bool(request.form.get("remember")))
            return redirect(_safe_next(request.args.get("next")) or url_for("packs.index"))
    status = 422 if errors else 200
    return render_template("pages/login.html", errors=errors, identifier=identifier), status


@bp.post("/deconnexion")
@login_required
def logout():
    logout_user()
    flash("Tu es déconnecté.", "info")
    return redirect(url_for("main.home"))
