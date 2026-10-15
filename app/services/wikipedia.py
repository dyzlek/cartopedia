"""Client minimal des API Wikimedia (REST + Action) — utilisé uniquement par les jobs.

Règle : aucune requête web ne passe par ici. Respect de la politique d'usage de Wikimedia :
User-Agent explicite, débit modéré, nouvelle tentative avec attente sur 429/5xx.
"""
import os
import time
from datetime import date, timedelta
from urllib.parse import quote

import requests

DEFAULT_UA = "Cartopedia/0.1 (jeu de cartes educatif; contact: voir WIKI_USER_AGENT)"


class WikipediaClient:
    def __init__(self, lang: str = "fr", delay: float = 0.25):
        self.lang = lang
        self.delay = delay
        self.session = requests.Session()
        self.session.headers["User-Agent"] = os.environ.get("WIKI_USER_AGENT", DEFAULT_UA)
        self.session.headers["Accept"] = "application/json"

    @property
    def project(self) -> str:
        return f"{self.lang}.wikipedia"

    def _get(self, url: str, params: dict | None = None, tries: int = 4):
        for attempt in range(tries):
            time.sleep(self.delay)
            try:
                r = self.session.get(url, params=params, timeout=20)
            except requests.RequestException:
                time.sleep(1.5 * (attempt + 1))
                continue
            if r.status_code == 404:
                return None
            if r.status_code in (429, 500, 502, 503, 504):
                # Respecte Retry-After si présent, sinon attente exponentielle (plafonnée)
                wait = r.headers.get("Retry-After", "")
                time.sleep(min(int(wait) if wait.isdigit() else 5 * 2 ** attempt, 60))
                continue
            r.raise_for_status()
            return r.json()
        return None

    @staticmethod
    def _slug(title: str) -> str:
        return quote(title.replace(" ", "_"), safe="")

    def top_titles(self, limit: int = 200, days_ago: int = 3) -> list[str]:
        """Articles les plus lus d'une journée récente (hors pages spéciales)."""
        d = date.today() - timedelta(days=days_ago)
        url = (
            "https://wikimedia.org/api/rest_v1/metrics/pageviews/top/"
            f"{self.project}/all-access/{d.year}/{d.month:02d}/{d.day:02d}"
        )
        data = self._get(url)
        if not data:
            return []
        out = []
        for item in data["items"][0]["articles"]:
            title = item["article"].replace("_", " ")
            if ":" in title or title.startswith(("Wikipédia", "Accueil")):
                continue
            out.append(title)
            if len(out) >= limit:
                break
        return out

    def summary(self, title: str) -> dict | None:
        return self._get(
            f"https://{self.lang}.wikipedia.org/api/rest_v1/page/summary/{self._slug(title)}"
        )

    def random_titles(self, count: int = 50) -> list[str]:
        """Titres d'articles tirés au hasard (une requête, jusqu'à 50 titres)."""
        data = self._get(
            f"https://{self.lang}.wikipedia.org/w/api.php",
            {"action": "query", "list": "random", "rnnamespace": 0, "rnlimit": min(count, 50),
             "format": "json", "formatversion": 2},
        )
        if not data:
            return []
        return [r["title"] for r in data.get("query", {}).get("random", [])]

    def pageviews_30d(self, title: str) -> int:
        end = date.today() - timedelta(days=2)
        start = end - timedelta(days=29)
        url = (
            "https://wikimedia.org/api/rest_v1/metrics/pageviews/per-article/"
            f"{self.project}/all-access/user/{self._slug(title)}/daily/"
            f"{start:%Y%m%d}/{end:%Y%m%d}"
        )
        data = self._get(url)
        if not data:
            return 0
        return sum(i["views"] for i in data.get("items", []))

    def page_info(self, titles: list[str]) -> dict[str, dict]:
        """Longueur de l'article et nombre de catégories visibles (50 titres par requête)."""
        out: dict[str, dict] = {}
        for i in range(0, len(titles), 40):
            batch = titles[i : i + 40]
            params = {
                "action": "query", "format": "json", "formatversion": 2,
                "prop": "info|categories", "clshow": "!hidden", "cllimit": "max",
                "titles": "|".join(batch), "redirects": 1,
            }
            while True:
                data = self._get(f"https://{self.lang}.wikipedia.org/w/api.php", params)
                if not data:
                    break
                for p in data.get("query", {}).get("pages", []):
                    if p.get("missing"):
                        continue
                    e = out.setdefault(p["title"], {"length": 0, "categories": 0})
                    e["length"] = p.get("length", e["length"])
                    e["categories"] += len(p.get("categories", []))
                if "continue" not in data:
                    break
                params = {**params, **data["continue"]}
        return out
