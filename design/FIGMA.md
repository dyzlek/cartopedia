# Maquettes et prototype Figma

Fichier : https://www.figma.com/design/3Z3z652xWviZlCfksfqKru

| Page Figma | Contenu |
|---|---|
| Design system | Palette (variables `Cartopedia/Couleurs`), typographie, composant **Bouton** (4 types), composant **Carte** (6 raretés), **Carte compacte (mobile)**, spécimen de **focus visible** |
| Écrans | 10 écrans desktop (1280 px), prototype cliquable (départ : Accueil) |
| Mobile | 9 écrans à 375 px, prototype cliquable (départ : Accueil), barre d'onglets en bas |

## Écrans
Accueil · Album · Marché · Inscription (captcha Cap) · Paquet fermé · Paquet ouvert · Détail carte · Échanges · Profil · Erreur 404

## Parcours du prototype
- Accueil → Inscription → Paquet fermé → Paquet ouvert → Album / Détail
- Navigation du bandeau : Paquets, Album, Marché, Échanges, Profil (portefeuille), logo = Accueil
- Détail : Vendre → Marché, Échanger → Échanges, Retour → Album
- Marché : Acheter → Détail ; Échanges : Accepter → Album, Proposer → Profil
- Profil : Déconnexion → Accueil ; 404 : Retour à l'accueil

À faire : états hover/disabled, états d'erreur des formulaires, lien d'aide, confirmation de vente (voir `ACCESSIBILITY.md`).
