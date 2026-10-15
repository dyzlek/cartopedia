# ARCHITECTURE – Cartopedia

Jeu de **collection de cartes issues d'articles Wikipédia** : ouvrir des paquets, collectionner, **vendre** (marché) et **échanger**. Pas de combat.

## Stack
| Couche | Choix | Pourquoi |
|---|---|---|
| Backend | Flask (application factory + blueprints) | cours + simplicité |
| Base de données | SQLite en dev (mode WAL), PostgreSQL en prod | SQLAlchemy permet les deux |
| ORM / migrations | Flask-SQLAlchemy, Flask-Migrate | |
| Auth | Flask-Login, mots de passe hachés (argon2 ou scrypt de Werkzeug) | |
| CSS | **Tailwind CLI standalone** (aucun Node requis) | thème brutaliste, voir `DESIGN.md` |
| Captcha | **[Cap](https://github.com/tiagozip/cap)** auto-hébergé (Docker) | preuve de travail, sans pistage |
| Anti-abus | Flask-Limiter | limitation par IP et par compte |
| Cache | mémoire locale (TTL) puis Redis/Valkey si besoin | |
| Prod | Gunicorn derrière un reverse proxy | |

## Arborescence
```
cartopedia/
├── README.md
├── DESIGN.md                 # charte brutaliste
├── ARCHITECTURE.md           # ce fichier
├── LICENSE
├── .gitignore
├── .env.example              # SECRET_KEY, DATABASE_URL, CAP_*…
├── requirements.txt
├── tailwind.config.js
├── wsgi.py                   # point d'entrée Gunicorn
│
├── app/
│   ├── __init__.py           # create_app()
│   ├── config.py
│   ├── extensions.py         # db, login_manager, limiter, cache
│   ├── models/               # user, card, inventory, listing, trade, ledger
│   ├── blueprints/
│   │   ├── auth/             # inscription, connexion
│   │   ├── packs/            # ouverture de paquets
│   │   ├── album/            # collection, filtres
│   │   ├── market/           # ventes
│   │   ├── trades/           # échanges
│   │   ├── profile/          # profil, portefeuille
│   │   └── api/              # JSON (pagination, recherche)
│   ├── services/             # logique métier (sans Flask)
│   │   ├── pack_opener.py
│   │   ├── market.py
│   │   ├── trading.py
│   │   ├── captcha.py        # vérification Cap côté serveur
│   │   └── cache.py
│   ├── templates/
│   │   ├── layouts/
│   │   ├── components/       # carte, bouton, badge, modale…
│   │   └── pages/
│   └── static/
│       ├── css/              # input.css → output.css (Tailwind)
│       ├── js/
│       ├── fonts/
│       └── img/
│
├── jobs/                     # scripts hors requêtes web
│   ├── seed_cards.py         # remplit la table des cartes depuis Wikipédia
│   └── refresh_stats.py      # recalcule rareté (vues) périodiquement
├── infra/
│   └── cap/                  # docker-compose du serveur Cap
├── migrations/
├── tests/
├── design/                   # tokens, liens Figma, exports
└── docs/
```

## Règle d'or : zéro appel externe pendant une requête
Wikipédia n'est **jamais** interrogée quand un joueur clique. Un job (`jobs/seed_cards.py`) construit à l'avance un **catalogue** de cartes dans la base : titre, résumé, image, vues sur 30 jours, taille, qualité, rareté calculée. Ouvrir un paquet = quelques lectures en base, rien d'autre.

| Statistique de carte | Source (gratuite) | Calculé |
|---|---|---|
| Rareté | API Wikimedia Pageviews (30 j) | hors ligne, par quantiles |
| Attaque (affichée) | taille de l'article | hors ligne |
| Défense (affichée) | nb de références / sections / label qualité | hors ligne |

Le texte reprend Wikipédia (CC BY-SA) : mention de la source et lien vers l'article sur chaque carte.

## Modèle de données
```
users(id, pseudo UNIQUE, email UNIQUE, password_hash, coins, created_at,
      last_free_pack_at, is_adult_confirmed)

cards(id, wiki_page_id UNIQUE, title, summary, image_url, lang,
      rarity ENUM, pageviews_30d, length, quality, tags, updated_at)

inventory(user_id, card_id, quantity, pinned, PRIMARY KEY(user_id, card_id))

listings(id, seller_id, card_id, price, status ENUM[open,sold,cancelled],
         created_at, sold_to, sold_at)          -- vente à prix fixe

trades(id, proposer_id, receiver_id, status ENUM[pending,accepted,declined,cancelled],
       created_at, resolved_at)
trade_items(trade_id, side ENUM[give,want], card_id, quantity)

ledger(id, user_id, delta, reason ENUM[pack,sale,purchase,daily,bonus], ref_id, created_at)
pack_log(id, user_id, opened_at, card_ids)       -- audit + anti-abus
```

### Index (obligatoires)
- `cards(rarity)`, `cards(title)` (recherche), `cards(pageviews_30d)`.
- `inventory(user_id)` (clé primaire composite) et `inventory(card_id)`.
- `listings(status, card_id, price)` : liste des ventes triée par prix.
- `listings(seller_id, status)`.
- `trades(receiver_id, status)`, `trades(proposer_id, status)`.
- `ledger(user_id, created_at)`.

## Optimisation et protection de la base
| Problème | Réponse |
|---|---|
| Requêtes N+1 | `joinedload` / `selectinload` systématiques, test qui compte les requêtes par page |
| Pages lourdes | **pagination par curseur** (`WHERE id < ? ORDER BY id DESC LIMIT 24`), jamais `OFFSET` énorme |
| Catalogue lu en boucle | cache mémoire (TTL 10 min) des listes de cartes par rareté, invalidé par le job |
| Inventaire = lignes en masse | une ligne par (joueur, carte) avec `quantity`, pas une ligne par exemplaire |
| Écritures concurrentes (vente, échange) | **transaction unique** + `UPDATE … WHERE status='open'` (verrou optimiste) : une vente ne peut pas être achetée deux fois |
| Double ouverture de paquet | contrainte de délai en base (`last_free_pack_at`) + verrou de ligne |
| Données statiques | en-têtes `Cache-Control` longs + noms de fichiers hachés, `ETag` sur les images de cartes |
| Réponses JSON | `LIMIT` borné (max 48), champs minimaux, compression gzip/brotli |
| SQLite en dev | `PRAGMA journal_mode=WAL; synchronous=NORMAL; foreign_keys=ON` |

## Anti-spam et sécurité
| Surface | Protection |
|---|---|
| Inscription, connexion, ouverture de paquet, création de vente, proposition d'échange | **Captcha Cap** (jeton vérifié côté serveur) |
| Toutes les routes d'écriture | **Flask-Limiter** : p. ex. 5 inscriptions/h/IP, 10 connexions/min/IP, 30 actions/min/compte |
| Formulaires | CSRF (Flask-WTF), validation côté serveur |
| Prix de vente | bornes min/max par rareté (évite l'abus et le blanchiment de pièces) |
| Mots de passe | hachage fort, longueur min. 10 |
| Contenu | échappement Jinja par défaut ; contenu Wikipédia traité comme non fiable |
| Secrets | `.env` hors dépôt, `.env.example` versionné |

### Intégration de Cap
1. Lancer le serveur **Cap Standalone** (`tiago2/cap`, port 3000, tableau de bord pour créer la clé de site et son secret).
2. Côté page : le composant `<cap-widget data-cap-api-endpoint="https://<cap>/<site-key>/">` fournit un jeton dans l'événement `solve`.
3. Côté Flask : `POST https://<cap>/<site-key>/siteverify` avec `{"secret": "...", "response": "<jeton>"}` ; on accepte uniquement si `success: true`. Fait dans `services/captcha.py`.
4. Le secret n'est jamais envoyé au navigateur.

## Économie (gratuite, sans argent réel)
- Pièces virtuelles : paquet gratuit toutes les 8 h, pièces gagnées en vendant.
- Prix du paquet payant fixe ; les ventes entre joueurs prennent une petite taxe (puits de pièces anti-inflation).
- Aucun paiement réel, aucune enchère dans la V1.

## Feuille de route
| Version | Contenu |
|---|---|
| **V0** | Dossiers, `DESIGN.md`, `ARCHITECTURE.md`, maquettes Figma (fait) |
| **V1** | Comptes + captcha, job de catalogue, ouverture de paquets, album |
| **V2** | Marché (vente à prix fixe), portefeuille |
| **V3** | Échanges entre joueurs |
| **V4** | Enchères, guildes, succès (optionnel) |
