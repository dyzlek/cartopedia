from flask import Blueprint, redirect, render_template, url_for
from flask_login import current_user, login_required

from ...extensions import db
from ...models import Inventory, Ledger
from ...services.packs import catalog_ids_by_rarity

bp = Blueprint("main", __name__)


@bp.get("/")
def home():
    if current_user.is_authenticated:
        return redirect(url_for("packs.index"))
    total = sum(len(v) for v in catalog_ids_by_rarity().values())
    return render_template("pages/home.html", catalog_size=total)


@bp.get("/aide")
def help_page():
    return render_template("pages/help.html")


@bp.get("/profil")
@login_required
def profile():
    stats = db.session.execute(
        db.select(db.func.count(Inventory.card_id), db.func.coalesce(db.func.sum(Inventory.quantity), 0)).where(
            Inventory.user_id == current_user.id
        )
    ).one()
    movements = db.session.execute(
        db.select(Ledger).where(Ledger.user_id == current_user.id).order_by(Ledger.id.desc()).limit(10)
    ).scalars().all()
    catalog_size = sum(len(v) for v in catalog_ids_by_rarity().values())
    return render_template(
        "pages/profile.html", unique=stats[0], total=stats[1], catalog_size=catalog_size, movements=movements
    )
