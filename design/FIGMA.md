# Maquettes et prototype Figma

Fichier : https://www.figma.com/design/3Z3z652xWviZlCfksfqKru

| Page Figma | Contenu |
|---|---|
| Design system | Palette (variables `Cartopedia/Couleurs`), typographie, **Bouton** (4 types × 5 états), **Carte** (6 raretés), **Carte compacte (mobile)**, **Champ** (repos, focus, erreur, désactivé), **Message d'état** (succès, erreur, info), spécimens de focus |
| Écrans | 17 écrans desktop (1280 px), prototype cliquable |
| Mobile | 15 écrans à 375 px, prototype cliquable, barre d'onglets en bas |

## Écrans
Accueil · Connexion · Inscription · Inscription — erreurs · Paquet fermé · Paquet ouvert · Album · Album vide · Détail carte · Mettre en vente · Marché · Marché — vente confirmée · Échanges · Profil · Aide et contact · Erreur 404 · Erreur 429 (desktop). Le mobile reprend tout sauf 404 et 429.

## Parcours du prototype
- Accueil → Connexion → Album ; Accueil → Inscription → (erreurs) → Paquet fermé → Paquet ouvert → Album / Détail
- Détail : Vendre → Mettre en vente → Marché (vente confirmée) ; Échanger → Échanges
- Bandeau : Paquets, Album, Marché, Échanges, **Aide** (même place partout), solde → Profil, logo → Accueil
- Page active soulignée (desktop) ou onglet inversé (mobile)
- Marché mobile : chaque vente affiche sa carte compacte, rareté, prix et bouton Acheter

À faire : 429 mobile, survol des cartes dessiné, états hors ligne. Voir `ACCESSIBILITY.md`.
