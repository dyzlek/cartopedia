from flask import Blueprint, abort, current_app, render_template, request
from flask_login import current_user, login_required

from ...extensions import db
from ...models import RARITIES, Card, Inventory
from ...services.packs import catalog_ids_by_rarity

bp = Blueprint("album", __name__)


@bp.get("/album")
@login_required
def index():
    size = current_app.config["ALBUM_PAGE_SIZE"]
    rarity = request.args.get("rarete", "")
    if rarity not in RARITIES:
        rarity = ""
    cursor = request.args.get("curseur", type=int, default=0)

    # Pagination par curseur (WHERE card_id > ?) : coût constant quelle que soit la page.
    q = (
        db.select(Inventory)
        .join(Card, Card.id == Inventory.card_id)
        .where(Inventory.user_id == current_user.id, Inventory.card_id > max(cursor, 0))
        .order_by(Inventory.card_id)
        .limit(size + 1)
    )
    if rarity:
        q = q.where(Card.rarity == rarity)
    rows = db.session.execute(q).scalars().unique().all()
    has_more = len(rows) > size
    rows = rows[:size]
    next_cursor = rows[-1].card_id if has_more and rows else None

    unique, total = db.session.execute(
        db.select(db.func.count(Inventory.card_id), db.func.coalesce(db.func.sum(Inventory.quantity), 0)).where(
            Inventory.user_id == current_user.id
        )
    ).one()
    catalog_size = sum(len(v) for v in catalog_ids_by_rarity().values())
    return render_template(
        "pages/album.html",
        rows=rows,
        rarity=rarity,
        next_cursor=next_cursor,
        unique=unique,
        total=total,
        catalog_size=catalog_size,
    )


@bp.get("/carte/<int:card_id>")
@login_required
def detail(card_id: int):
    inv = db.session.get(Inventory, (current_user.id, card_id))
    if inv is None:
        abort(404)  # on ne révèle que les cartes possédées
    return render_template("pages/card_detail.html", card=inv.card, quantity=inv.quantity)
