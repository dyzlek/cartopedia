# Cartopedia

Jeu gratuit de **collection de cartes tirées d'articles Wikipédia** : ouvre des paquets, complète ton album, **vends** et **échange** tes cartes. Pas de combat. Thème **brutaliste**.

> Statut : **V0 – conception.** Les dossiers et la documentation sont en place, le site n'est pas encore développé.

## Documents
- [`DESIGN.md`](DESIGN.md) : charte brutaliste (couleurs, typographie, composants, pages)
- [`ARCHITECTURE.md`](ARCHITECTURE.md) : arborescence, base de données, optimisation, anti-spam, captcha

## Stack
Flask · SQLAlchemy · Tailwind CSS · [Cap](https://github.com/tiagozip/cap) (captcha auto-hébergé) · SQLite / PostgreSQL

## Licence et sources
- Code : MIT.
- Contenu des cartes : extraits de [Wikipédia](https://fr.wikipedia.org), sous licence **CC BY-SA 4.0**. Chaque carte renvoie à son article d'origine.
- Projet indépendant, inspiré du concept des jeux de cartes à collectionner.
