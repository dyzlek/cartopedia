"""Vérification du jeton Cap (https://github.com/tiagozip/cap) côté serveur.

Le secret n'est jamais envoyé au navigateur. En cas d'erreur réseau, on refuse (fail closed).
"""
import logging

import requests
from flask import current_app

log = logging.getLogger(__name__)
TOKEN_FIELD = "cap-token"


def is_enabled() -> bool:
    cfg = current_app.config
    return bool(cfg.get("CAP_ENDPOINT") and cfg.get("CAP_SITE_KEY") and cfg.get("CAP_SECRET"))


def verify(token: str | None) -> bool:
    if not is_enabled():
        # Mode développement : voir README. Jamais en production.
        return True
    if not token:
        return False
    cfg = current_app.config
    url = f"{cfg['CAP_ENDPOINT']}/{cfg['CAP_SITE_KEY']}/siteverify"
    try:
        r = requests.post(
            url, json={"secret": cfg["CAP_SECRET"], "response": token}, timeout=5
        )
        return r.ok and bool(r.json().get("success"))
    except (requests.RequestException, ValueError):
        log.warning("Vérification Cap impossible (%s)", url)
        return False
