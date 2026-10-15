from flask import Blueprint, abort, current_app, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from ...extensions import db, limiter
from ...models import Card, PackLog, utcnow
from ...services import captcha
from ...services.packs import (
    EmptyCatalog,
    InsufficientCoins,
    PackNotAvailable,
    next_free_pack_at,
    open_pack,
)

bp = Blueprint("packs", __name__, url_prefix="/paquets")


@bp.get("/")
@login_required
def index():
    nxt = next_free_pack_at(current_user)
    minutes_left = int((nxt - utcnow()).total_seconds() // 60) + 1 if nxt else 0
    return render_template("pages/packs.html", next_free_at=nxt, minutes_left=minutes_left)


@bp.post("/ouvrir")
@login_required
@limiter.limit("20 per hour")
def open_():
    kind = request.form.get("kind", "free")
    if kind not in {"free", "paid"}:
        abort(400)
    if not captcha.verify(request.form.get(captcha.TOKEN_FIELD)):
        flash("Vérification échouée, réessaie.", "error")
        return redirect(url_for("packs.index")), 303
    try:
        result = open_pack(current_user.id, kind)
    except PackNotAvailable:
        flash("Ton paquet gratuit n’est pas encore prêt.", "info")
    except InsufficientCoins:
        flash(
            f"Il te faut {current_app.config['PAID_PACK_PRICE']} pièces pour ce paquet.", "error"
        )
    except EmptyCatalog:
        flash("Le catalogue est vide pour l’instant. Reviens plus tard.", "error")
    else:
        return redirect(url_for("packs.result", log_id=result.log_id))
    return redirect(url_for("packs.index"))


@bp.get("/resultat/<int:log_id>")
@login_required
def result(log_id: int):
    log = db.session.get(PackLog, log_id)
    if log is None or log.user_id != current_user.id:
        abort(404)
    ids = log.card_id_list
    cards = {
        c.id: c
        for c in db.session.execute(db.select(Card).where(Card.id.in_(set(ids)))).scalars()
    }
    return render_template(
        "pages/pack_result.html", cards=[cards[i] for i in ids if i in cards], log=log
    )
