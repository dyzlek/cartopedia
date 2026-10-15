from datetime import datetime, timezone

from flask_login import UserMixin
from sqlalchemy import CheckConstraint, Index

from ..extensions import db

RARITIES = ("C", "PC", "R", "SR", "UR", "L")
RARITY_LABELS = {
    "C": "Commune",
    "PC": "Peu commune",
    "R": "Rare",
    "SR": "Super rare",
    "UR": "Ultra rare",
    "L": "Légendaire",
}


def utcnow() -> datetime:
    """Date UTC naïve (SQLite ne stocke pas les fuseaux)."""
    return datetime.now(timezone.utc).replace(tzinfo=None)


class User(UserMixin, db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    pseudo = db.Column(db.String(24), nullable=False, unique=True)
    email = db.Column(db.String(254), nullable=False, unique=True)
    password_hash = db.Column(db.String(255), nullable=False)
    coins = db.Column(db.Integer, nullable=False, default=0)
    last_free_pack_at = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=utcnow)

    __table_args__ = (CheckConstraint("coins >= 0", name="ck_users_coins_positive"),)


class Card(db.Model):
    __tablename__ = "cards"

    id = db.Column(db.Integer, primary_key=True)
    wiki_page_id = db.Column(db.Integer, nullable=False, unique=True)
    lang = db.Column(db.String(8), nullable=False, default="fr")
    title = db.Column(db.String(255), nullable=False)
    summary = db.Column(db.Text, nullable=False, default="")
    description = db.Column(db.String(255), nullable=False, default="")
    image_url = db.Column(db.String(500), nullable=True)
    page_url = db.Column(db.String(500), nullable=False)
    rarity = db.Column(db.String(2), nullable=False)
    pageviews_30d = db.Column(db.Integer, nullable=False, default=0)
    length = db.Column(db.Integer, nullable=False, default=0)
    categories = db.Column(db.Integer, nullable=False, default=0)
    attack = db.Column(db.Integer, nullable=False, default=0)
    defense = db.Column(db.Integer, nullable=False, default=0)
    updated_at = db.Column(db.DateTime, nullable=False, default=utcnow)

    __table_args__ = (
        Index("ix_cards_rarity", "rarity"),
        Index("ix_cards_pageviews", "pageviews_30d"),
        Index("ix_cards_title", "title"),
    )

    @property
    def rarity_label(self) -> str:
        return RARITY_LABELS.get(self.rarity, self.rarity)


class Inventory(db.Model):
    """Une ligne par (joueur, carte) avec une quantité : jamais une ligne par exemplaire."""

    __tablename__ = "inventory"

    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), primary_key=True)
    card_id = db.Column(db.Integer, db.ForeignKey("cards.id"), primary_key=True)
    quantity = db.Column(db.Integer, nullable=False, default=1)
    first_obtained_at = db.Column(db.DateTime, nullable=False, default=utcnow)

    card = db.relationship("Card", lazy="joined", innerjoin=True)

    __table_args__ = (
        CheckConstraint("quantity >= 1", name="ck_inventory_quantity"),
        Index("ix_inventory_card", "card_id"),
    )


class Ledger(db.Model):
    __tablename__ = "ledger"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    delta = db.Column(db.Integer, nullable=False)
    reason = db.Column(db.String(24), nullable=False)
    ref_id = db.Column(db.Integer, nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=utcnow)

    __table_args__ = (Index("ix_ledger_user_date", "user_id", "created_at"),)


class PackLog(db.Model):
    __tablename__ = "pack_log"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    kind = db.Column(db.String(8), nullable=False)  # free | paid
    card_ids = db.Column(db.String(255), nullable=False)  # "12,40,40,7"
    opened_at = db.Column(db.DateTime, nullable=False, default=utcnow)

    __table_args__ = (Index("ix_pack_log_user", "user_id", "opened_at"),)

    @property
    def card_id_list(self) -> list[int]:
        return [int(x) for x in self.card_ids.split(",") if x]
