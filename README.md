# Cartopedia

Jeu gratuit de **collection de cartes tirées d'articles Wikipédia** : ouvre des paquets, complète ton album. Pas de combat. Thème **brutaliste**, accessible (WCAG 2.2 AA visé).

> Statut : **V1** (comptes + captcha, catalogue, paquets, album). Marché (V2) et échanges (V3) à venir. Voir la [feuille de route](ARCHITECTURE.md#feuille-de-route).

## Démarrer en local

```bash
python -m venv .venv
.venv\Scripts\activate            # Linux/macOS : source .venv/bin/activate
pip install -r requirements.txt
npm install && npm run css        # compile Tailwind (app/static/css/output.css)

cp .env.example .env              # puis éditer SECRET_KEY, WIKI_USER_AGENT
python -m jobs.seed_cards --count 300   # construit le catalogue depuis Wikipédia (quelques minutes)
flask --app app run --debug       # http://127.0.0.1:5000
```

- `npm run css:watch` recompile le CSS à chaque modification des gabarits.
- Le job de catalogue est **poli** avec Wikimedia (User-Agent, débit modéré, `Retry-After`). Ne le lance pas en boucle.
- Tests : `pytest -q`.

## Captcha Cap

Sans `CAP_ENDPOINT`, `CAP_SITE_KEY` et `CAP_SECRET`, le captcha est **désactivé** (mode développement, un encart le signale sur les formulaires). **Ne jamais déployer ainsi.**

```bash
cd infra/cap
CAP_ADMIN_KEY=<32+ caractères> docker compose up -d   # tableau de bord : http://localhost:3000
```

Créer une clé de site dans le tableau de bord, puis reporter les trois valeurs dans `.env`. Le jeton est vérifié côté serveur (`app/services/captcha.py`, route `/<clé>/siteverify`) ; en cas d'erreur réseau, la requête est refusée.

## Documents
- [`ARCHITECTURE.md`](ARCHITECTURE.md) : arborescence, base de données, optimisation, anti-spam
- [`DESIGN.md`](DESIGN.md) : charte brutaliste
- [`ACCESSIBILITY.md`](ACCESSIBILITY.md) : audit WCAG 2.2
- [`design/FIGMA.md`](design/FIGMA.md) : maquettes et prototype Figma (17 écrans desktop + 15 mobiles)

## Ce que fait la V1
| Fonction | Où |
|---|---|
| Inscription / connexion, mots de passe hachés, redirection sûre | `app/blueprints/auth` |
| Captcha Cap sur inscription, connexion, ouverture de paquet | `app/services/captcha.py` |
| Limites : 5 inscriptions/h, 10 connexions/min, 20 paquets/h par IP | `Flask-Limiter` |
| Paquet gratuit toutes les 8 h (atomique), paquet à 80 ◆ | `app/services/packs.py` |
| Album paginé par curseur, filtre par rareté, détail d'une carte | `app/blueprints/album` |
| Catalogue précalculé : aucun appel Wikipédia pendant une requête | `jobs/seed_cards.py` |

## Licence et sources
- Code : MIT.
- Contenu des cartes : extraits de [Wikipédia](https://fr.wikipedia.org), licence **CC BY-SA 4.0**. Chaque carte renvoie à son article d'origine.
- Projet indépendant, inspiré du concept des jeux de cartes à collectionner.
