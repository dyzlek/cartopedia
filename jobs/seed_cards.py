"""Construit / met à jour le catalogue de cartes depuis Wikipédia.

    python -m jobs.seed_cards --count 300 --lang fr

Hors ligne par rapport au site : le site ne contacte jamais Wikipédia. Le job peut être relancé
(mise à jour des cartes existantes, ajout des nouvelles) et recalcule les raretés par quantiles.
"""
import argparse
import random
import sys

from app import create_app
from app.extensions import db
from app.models import Card, utcnow
from app.services.wikipedia import WikipediaClient

# Part du catalogue par rareté, des plus rares aux plus communes (le reste est « commune »).
# Chaque rareté a au moins une carte dès que le catalogue en compte assez.
RARITY_SHARES = [("L", 0.005), ("UR", 0.025), ("SR", 0.05), ("R", 0.12), ("PC", 0.25)]


def quotas(n: int) -> dict[str, int]:
    out, left = {}, n
    for code, share in RARITY_SHARES:
        q = min(left, max(1, round(n * share))) if n >= len(RARITY_SHARES) + 1 else 0
        out[code] = q
        left -= q
    out["C"] = left
    return out


def assign_rarities() -> dict[str, int]:
    """Raretés par quantiles de fréquentation : les articles les plus lus sont les plus rares."""
    cards = db.session.execute(
        db.select(Card).order_by(Card.pageviews_30d.desc(), Card.id)
    ).scalars().all()
    q = quotas(len(cards))
    counts: dict[str, int] = {}
    i = 0
    for code in [c for c, _ in RARITY_SHARES] + ["C"]:
        for card in cards[i : i + q[code]]:
            card.rarity = code
        counts[code] = q[code]
        i += q[code]
    db.session.commit()
    return counts


def scale_stats(length: int, categories: int) -> tuple[int, int]:
    attack = min(9990, (length // 30) // 10 * 10)
    defense = min(9990, categories * 180 // 10 * 10)
    return attack, defense


def collect(client: WikipediaClient, count: int, top_share: float, rng: random.Random) -> dict[int, dict]:
    """Retourne {wiki_page_id: résumé} : une part d'articles très lus, le reste tiré au hasard."""
    found: dict[int, dict] = {}

    def keep(s: dict | None) -> None:
        if not s or s.get("type") != "standard":
            return
        extract = (s.get("extract") or "").strip()
        if len(extract) < 80 or not s.get("pageid"):
            return
        found.setdefault(s["pageid"], s)

    top_n = int(count * top_share)
    titles = client.top_titles(limit=top_n * 3)
    rng.shuffle(titles)
    for t in titles:
        if len(found) >= top_n:
            break
        keep(client.summary(t))
        print(f"\r  populaires : {len(found)}/{top_n}", end="", flush=True)
    print()
    rounds = 0
    while len(found) < count and rounds < 40:
        rounds += 1
        for t in client.random_titles(50):
            if len(found) >= count:
                break
            keep(client.summary(t))
            print(f"\r  au hasard  : {len(found)}/{count}", end="", flush=True)
    print()
    return found


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--count", type=int, default=300, help="nombre de cartes visées")
    ap.add_argument("--lang", default="fr")
    ap.add_argument("--top-share", type=float, default=0.35, help="part d'articles très lus")
    ap.add_argument("--seed", type=int, default=None)
    args = ap.parse_args(argv)

    app = create_app()
    client = WikipediaClient(lang=args.lang)
    rng = random.Random(args.seed)
    with app.app_context():
        print(f"Collecte de {args.count} articles ({args.lang}.wikipedia)…")
        found = collect(client, args.count, args.top_share, rng)
        titles = [s["title"] for s in found.values()]
        print("Statistiques de pages…")
        info = client.page_info(titles)
        existing = {
            c.wiki_page_id: c
            for c in db.session.execute(db.select(Card).where(Card.wiki_page_id.in_(found))).scalars()
        }
        created = updated = 0
        for i, (pid, s) in enumerate(found.items(), 1):
            views = client.pageviews_30d(s["title"])
            meta = info.get(s["title"], {"length": 0, "categories": 0})
            attack, defense = scale_stats(meta["length"], meta["categories"])
            data = dict(
                lang=args.lang,
                title=s["title"],
                summary=s["extract"].strip(),
                description=(s.get("description") or "")[:255],
                image_url=(s.get("thumbnail") or {}).get("source"),
                page_url=s.get("content_urls", {}).get("desktop", {}).get("page")
                or f"https://{args.lang}.wikipedia.org/?curid={pid}",
                pageviews_30d=views,
                length=meta["length"],
                categories=meta["categories"],
                attack=attack,
                defense=defense,
                updated_at=utcnow(),
            )
            card = existing.get(pid)
            if card:
                for k, v in data.items():
                    setattr(card, k, v)
                updated += 1
            else:
                db.session.add(Card(wiki_page_id=pid, rarity="C", **data))
                created += 1
            if i % 25 == 0:
                db.session.commit()
                print(f"\r  stats : {i}/{len(found)}", end="", flush=True)
        db.session.commit()
        print()
        counts = assign_rarities()
        print(f"Terminé : {created} créées, {updated} mises à jour.")
        print("Raretés :", ", ".join(f"{k}={v}" for k, v in sorted(counts.items())))
    return 0


if __name__ == "__main__":
    sys.exit(main())
