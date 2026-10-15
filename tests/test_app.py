from datetime import timedelta
from unittest.mock import patch

import pytest
import requests
from sqlalchemy import event

from app import create_app
from app.config import TestConfig
from app.extensions import db
from app.models import Card, Inventory, Ledger, User, utcnow
from app.services import captcha
from app.services.packs import (
    EmptyCatalog,
    InsufficientCoins,
    PackNotAvailable,
    open_pack,
)
from jobs.seed_cards import assign_rarities, quotas, scale_stats


# --- Inscription / connexion -------------------------------------------------------------

def test_register_success_gives_start_coins(client, register, app):
    r = register()
    assert r.status_code == 302
    with app.app_context():
        u = db.session.execute(db.select(User)).scalar_one()
        assert u.coins == app.config["START_COINS"]
        assert u.password_hash != "motdepasse-solide"
        assert db.session.execute(db.select(Ledger)).scalar_one().delta == u.coins


@pytest.mark.parametrize(
    "kwargs, field",
    [
        ({"pseudo": "a b"}, "pseudo"),
        ({"email": "pasunmail"}, "email"),
        ({"password": "court"}, "password"),
    ],
)
def test_register_validation_errors(register, kwargs, field):
    r = register(**kwargs)
    assert r.status_code == 422
    assert "ERREUR" in r.get_data(as_text=True)
    assert f'id="{field}-msg"' in r.get_data(as_text=True)


def test_register_requires_adult_and_terms(client):
    r = client.post("/inscription", data={"pseudo": "bob", "email": "bob@exemple.fr", "password": "motdepasse-solide"})
    assert r.status_code == 422
    html = r.get_data(as_text=True)
    assert "18 ans" in html and "conditions" in html


def test_register_duplicate_pseudo_case_insensitive(client, register):
    assert register().status_code == 302
    client.post("/deconnexion")
    r = register(pseudo="ALICE", email="autre@exemple.fr")
    assert r.status_code == 422


def test_login_wrong_password_is_generic(client, register):
    register()
    client.post("/deconnexion")
    r = client.post("/connexion", data={"identifier": "alice", "password": "mauvais-mot-de-passe"})
    assert r.status_code == 422
    assert "Identifiant ou mot de passe incorrect" in r.get_data(as_text=True)
    r2 = client.post("/connexion", data={"identifier": "inconnu", "password": "mauvais-mot-de-passe"})
    assert "Identifiant ou mot de passe incorrect" in r2.get_data(as_text=True)


def test_login_ignores_open_redirect(client, register):
    register()
    client.post("/deconnexion")
    r = client.post(
        "/connexion?next=https://evil.example/", data={"identifier": "alice@exemple.fr", "password": "motdepasse-solide"}
    )
    assert r.status_code == 302
    assert "evil.example" not in r.headers["Location"]


def test_pages_require_login(client):
    for path in ("/paquets/", "/album", "/profil"):
        assert client.get(path).status_code == 302


# --- Paquets -------------------------------------------------------------------------------

def _user(app):
    return db.session.execute(db.select(User)).scalar_one()


def test_free_pack_then_cooldown(client, register, app):
    register()
    r = client.post("/paquets/ouvrir", data={"kind": "free"})
    assert r.status_code == 302 and "/paquets/resultat/" in r.headers["Location"]
    page = client.get(r.headers["Location"])
    assert page.status_code == 200
    with app.app_context():
        total = db.session.execute(db.select(db.func.sum(Inventory.quantity))).scalar()
        assert total == app.config["PACK_SIZE"]
        with pytest.raises(PackNotAvailable):
            open_pack(_user(app).id, "free")
        # le délai écoulé, un nouveau paquet est possible
        u = _user(app)
        u.last_free_pack_at = utcnow() - timedelta(hours=9)
        db.session.commit()
        assert len(open_pack(u.id, "free").cards) == app.config["PACK_SIZE"]


def test_paid_pack_spends_coins_and_logs(client, register, app):
    register()
    with app.app_context():
        u = _user(app)
        before = u.coins
        open_pack(u.id, "paid")
        db.session.refresh(u)
        assert u.coins == before - app.config["PAID_PACK_PRICE"]
        assert db.session.execute(db.select(Ledger).where(Ledger.reason == "pack")).scalar_one().delta < 0


def test_paid_pack_insufficient_coins_changes_nothing(client, register, app):
    register()
    with app.app_context():
        u = _user(app)
        u.coins = 10
        db.session.commit()
        with pytest.raises(InsufficientCoins):
            open_pack(u.id, "paid")
        db.session.refresh(u)
        assert u.coins == 10
        assert db.session.execute(db.select(db.func.count(Inventory.card_id))).scalar() == 0


def test_empty_catalog_does_not_consume_free_pack(client, register, app):
    from app.services.cache import cache

    register()
    with app.app_context():
        db.session.execute(db.delete(Card))
        db.session.commit()
        cache.clear()
        u = _user(app)
        with pytest.raises(EmptyCatalog):
            open_pack(u.id, "free")
        db.session.refresh(u)
        assert u.last_free_pack_at is None  # le paquet n'est pas « brûlé »


def test_duplicates_increment_quantity_not_rows(client, register, app):
    register()
    with app.app_context():
        u = _user(app)
        # catalogue réduit à une seule carte : tous les tirages sont des doublons
        keep = db.session.execute(db.select(Card).limit(1)).scalar_one().id
        db.session.execute(db.delete(Card).where(Card.id != keep))
        db.session.commit()
        from app.services.cache import cache

        cache.clear()
        open_pack(u.id, "paid")
        rows = db.session.execute(db.select(Inventory)).scalars().all()
        assert len(rows) == 1 and rows[0].quantity == app.config["PACK_SIZE"]


# --- Album : performance et visibilité -----------------------------------------------------

def _count_queries(app, fn):
    n = {"q": 0}

    def counter(*_a, **_k):
        n["q"] += 1

    event.listen(db.engine, "before_cursor_execute", counter)
    try:
        fn()
    finally:
        event.remove(db.engine, "before_cursor_execute", counter)
    return n["q"]


def test_album_query_count_is_constant(client, register, app):
    register()
    with app.app_context():
        u = _user(app)
        for c in db.session.execute(db.select(Card).limit(40)).scalars():
            db.session.add(Inventory(user_id=u.id, card_id=c.id, quantity=2))
        db.session.commit()
    q = _count_queries(app, lambda: client.get("/album"))
    assert q <= 6, f"{q} requêtes SQL pour la page album (N+1 ?)"


def test_album_filter_and_cursor(client, register, app):
    register()
    with app.app_context():
        u = _user(app)
        for c in db.session.execute(db.select(Card)).scalars():
            db.session.add(Inventory(user_id=u.id, card_id=c.id, quantity=1))
        db.session.commit()
    page1 = client.get("/album").get_data(as_text=True)
    assert "Page suivante" in page1  # 48 cartes > 24 par page
    only_l = client.get("/album?rarete=L").get_data(as_text=True)
    assert "Article L0" in only_l and "Article C0" not in only_l


def test_card_detail_only_for_owned(client, register, app):
    register()
    with app.app_context():
        u = _user(app)
        owned, other = db.session.execute(db.select(Card).limit(2)).scalars().all()
        db.session.add(Inventory(user_id=u.id, card_id=owned.id, quantity=1))
        db.session.commit()
        owned_id, other_id = owned.id, other.id
    assert client.get(f"/carte/{owned_id}").status_code == 200
    assert client.get(f"/carte/{other_id}").status_code == 404


def test_pack_result_belongs_to_user(client, register, app):
    register()
    r = client.post("/paquets/ouvrir", data={"kind": "free"})
    url = r.headers["Location"]
    client.post("/deconnexion")
    register(pseudo="bob", email="bob@exemple.fr")
    assert client.get(url).status_code == 404


# --- Captcha Cap -----------------------------------------------------------------------------

class CapConfig(TestConfig):
    CAP_ENDPOINT = "http://cap.test"
    CAP_SITE_KEY = "site"
    CAP_SECRET = "secret"


@pytest.fixture()
def cap_app():
    app = create_app(CapConfig)
    with app.app_context():
        yield app


def _resp(ok=True, body=None):
    class R:
        def __init__(self):
            self.ok = ok

        def json(self):
            return body if body is not None else {"success": True}

    return R()


def test_captcha_disabled_in_dev(app):
    with app.app_context():
        assert captcha.is_enabled() is False
        assert captcha.verify(None) is True


def test_captcha_verify_success_and_failure(cap_app):
    with patch("app.services.captcha.requests.post", return_value=_resp(True, {"success": True})) as post:
        assert captcha.verify("tok") is True
        url = post.call_args.args[0]
        assert url == "http://cap.test/site/siteverify"
        assert post.call_args.kwargs["json"] == {"secret": "secret", "response": "tok"}
    with patch("app.services.captcha.requests.post", return_value=_resp(True, {"success": False})):
        assert captcha.verify("tok") is False
    assert captcha.verify("") is False


def test_captcha_fails_closed_on_network_error(cap_app):
    with patch("app.services.captcha.requests.post", side_effect=requests.ConnectionError):
        assert captcha.verify("tok") is False


def test_register_blocked_by_captcha(cap_app):
    client = cap_app.test_client()
    data = {"pseudo": "carl", "email": "carl@exemple.fr", "password": "motdepasse-solide", "adult": "1", "terms": "1"}
    with patch("app.services.captcha.requests.post", return_value=_resp(True, {"success": False})):
        r = client.post("/inscription", data={**data, "cap-token": "bad"})
    assert r.status_code == 422 and "Vérification échouée" in r.get_data(as_text=True)
    with patch("app.services.captcha.requests.post", return_value=_resp(True, {"success": True})):
        r = client.post("/inscription", data={**data, "cap-token": "good"})
    assert r.status_code == 302


# --- Limites de débit et en-têtes ------------------------------------------------------------

def test_register_is_rate_limited():
    class Limited(TestConfig):
        RATELIMIT_ENABLED = True

    app = create_app(Limited)
    client = app.test_client()
    codes = [client.post("/inscription", data={"pseudo": "x"}).status_code for _ in range(7)]
    assert codes[:5] == [422] * 5
    assert 429 in codes[5:]


def test_security_headers(client):
    r = client.get("/")
    assert "frame-ancestors 'none'" in r.headers["Content-Security-Policy"]
    assert r.headers["X-Content-Type-Options"] == "nosniff"


def test_404_page(client):
    r = client.get("/nimporte-quoi")
    assert r.status_code == 404 and "Page introuvable" in r.get_data(as_text=True)


# --- Job de catalogue ------------------------------------------------------------------------

def test_quotas_sum_and_cover_all_rarities():
    q = quotas(48)
    assert sum(q.values()) == 48
    assert all(q[r] >= 1 for r in ("C", "PC", "R", "SR", "UR", "L"))
    assert q["C"] > q["PC"] > q["R"] >= q["SR"] >= q["UR"] >= q["L"]
    assert sum(quotas(1000).values()) == 1000 and quotas(1000)["L"] == 5


def test_assign_rarities_orders_by_pageviews(app):
    with app.app_context():
        counts = assign_rarities()
        assert set(counts) == {"C", "PC", "R", "SR", "UR", "L"}
        most = db.session.execute(db.select(Card).order_by(Card.pageviews_30d.desc()).limit(1)).scalar_one()
        least = db.session.execute(db.select(Card).order_by(Card.pageviews_30d).limit(1)).scalar_one()
        assert most.rarity == "L" and least.rarity == "C"


def test_scale_stats_bounds():
    assert scale_stats(0, 0) == (0, 0)
    assert scale_stats(10**7, 10**4) == (9990, 9990)


def test_static_assets_are_versioned_and_cacheable(client):
    html = client.get("/").get_data(as_text=True)
    import re

    m = re.search(r'href="(/static/css/output\.css\?v=\d+)"', html)
    assert m, "le CSS doit porter un paramètre de version"
    r = client.get(m.group(1))
    assert "immutable" in r.headers["Cache-Control"]
    assert "immutable" not in client.get("/static/css/output.css").headers["Cache-Control"]
