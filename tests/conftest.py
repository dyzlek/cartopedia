import pytest

from app import create_app
from app.config import TestConfig
from app.extensions import db
from app.models import RARITIES, Card
from app.services.cache import cache


@pytest.fixture()
def app():
    cache.clear()
    app = create_app(TestConfig)
    with app.app_context():
        db.create_all()
        # 8 cartes par rareté : le tirage a toujours de quoi piocher
        n = 0
        for r in RARITIES:
            for i in range(8):
                n += 1
                db.session.add(
                    Card(
                        wiki_page_id=1000 + n, title=f"Article {r}{i}", summary="Résumé " * 20,
                        description=f"description {r}{i}", page_url=f"https://fr.wikipedia.org/?curid={n}",
                        rarity=r, pageviews_30d=n * 100, length=n * 900, categories=n, attack=n * 10, defense=n * 5,
                    )
                )
        db.session.commit()
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture()
def client(app):
    return app.test_client()


@pytest.fixture()
def register(client):
    def _register(pseudo="alice", email="alice@exemple.fr", password="motdepasse-solide", **extra):
        data = {"pseudo": pseudo, "email": email, "password": password, "adult": "1", "terms": "1", **extra}
        return client.post("/inscription", data=data)

    return _register
