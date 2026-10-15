"""Ouverture de paquets : tout se passe en base, aucun appel externe."""
import random
from dataclasses import dataclass
from datetime import datetime

from flask import current_app
from sqlalchemy import update

from ..extensions import db
from ..models import Card, Inventory, Ledger, PackLog, User, utcnow
from .cache import cache

# Poids de tirage par rareté (somme = 100)
RARITY_WEIGHTS = {"C": 60.0, "PC": 25.0, "R": 10.0, "SR": 4.0, "UR": 0.9, "L": 0.1}


class PackError(Exception):
    pass


class PackNotAvailable(PackError):
    def __init__(self, next_at: datetime):
        super().__init__("Paquet gratuit pas encore disponible")
        self.next_at = next_at


class InsufficientCoins(PackError):
    pass


class EmptyCatalog(PackError):
    pass


@dataclass
class PackResult:
    log_id: int
    cards: list[Card]
    new_card_ids: set[int]


def catalog_ids_by_rarity() -> dict[str, list[int]]:
    """Identifiants des cartes par rareté, mis en cache (une requête toutes les N minutes)."""

    def load():
        rows = db.session.execute(db.select(Card.rarity, Card.id)).all()
        out: dict[str, list[int]] = {}
        for rarity, cid in rows:
            out.setdefault(rarity, []).append(cid)
        return out

    ttl = current_app.config["CATALOG_CACHE_SECONDS"]
    return cache.get_or_set("catalog_ids_by_rarity", ttl, load)


def draw_card_ids(count: int, rng: random.Random | None = None) -> list[int]:
    rng = rng or random.SystemRandom()
    pool = catalog_ids_by_rarity()
    available = {r: w for r, w in RARITY_WEIGHTS.items() if pool.get(r)}
    if not available:
        raise EmptyCatalog("Le catalogue est vide : lance `python -m jobs.seed_cards`.")
    rarities, weights = zip(*available.items())
    picked = rng.choices(rarities, weights=weights, k=count)
    return [rng.choice(pool[r]) for r in picked]


def next_free_pack_at(user: User) -> datetime | None:
    """None si un paquet gratuit est disponible maintenant."""
    if user.last_free_pack_at is None:
        return None
    nxt = user.last_free_pack_at + current_app.config["FREE_PACK_INTERVAL"]
    return nxt if nxt > utcnow() else None


def open_pack(user_id: int, kind: str, rng: random.Random | None = None) -> PackResult:
    """Ouvre un paquet de façon atomique.

    Les conditions (délai, solde) sont vérifiées par un UPDATE conditionnel : deux requêtes
    simultanées ne peuvent pas ouvrir deux paquets gratuits ni dépenser deux fois les mêmes pièces.
    """
    cfg = current_app.config
    now = utcnow()
    session = db.session

    if kind == "free":
        threshold = now - cfg["FREE_PACK_INTERVAL"]
        res = session.execute(
            update(User)
            .where(
                User.id == user_id,
                (User.last_free_pack_at.is_(None)) | (User.last_free_pack_at <= threshold),
            )
            .values(last_free_pack_at=now)
        )
        if res.rowcount == 0:
            session.rollback()
            user = session.get(User, user_id)
            raise PackNotAvailable(user.last_free_pack_at + cfg["FREE_PACK_INTERVAL"])
    elif kind == "paid":
        price = cfg["PAID_PACK_PRICE"]
        res = session.execute(
            update(User)
            .where(User.id == user_id, User.coins >= price)
            .values(coins=User.coins - price)
        )
        if res.rowcount == 0:
            session.rollback()
            raise InsufficientCoins()
        session.add(Ledger(user_id=user_id, delta=-price, reason="pack", created_at=now))
    else:
        raise PackError("Type de paquet inconnu")

    try:
        ids = draw_card_ids(cfg["PACK_SIZE"], rng)
    except EmptyCatalog:
        session.rollback()
        raise

    unique_ids = set(ids)
    cards_by_id = {
        c.id: c for c in session.execute(db.select(Card).where(Card.id.in_(unique_ids))).scalars()
    }
    owned = {
        inv.card_id: inv
        for inv in session.execute(
            db.select(Inventory).where(Inventory.user_id == user_id, Inventory.card_id.in_(unique_ids))
        ).scalars()
    }
    new_ids: set[int] = set()
    for cid in ids:
        inv = owned.get(cid)
        if inv:
            inv.quantity += 1
        else:
            inv = Inventory(user_id=user_id, card_id=cid, quantity=1, first_obtained_at=now)
            session.add(inv)
            owned[cid] = inv
            new_ids.add(cid)

    log = PackLog(user_id=user_id, kind=kind, card_ids=",".join(map(str, ids)), opened_at=now)
    session.add(log)
    session.commit()
    return PackResult(log_id=log.id, cards=[cards_by_id[i] for i in ids], new_card_ids=new_ids)
