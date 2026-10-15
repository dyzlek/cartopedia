# DESIGN – Cartopedia (thème brutaliste)

Direction : **néo-brutalisme web**. Brut, franc, lisible. Aucune décoration inutile : l'interface montre sa structure.

## Principes
1. **Bordures épaisses** noires (3 px partout, 4 px sur les cartes et les modales).
2. **Ombres dures décalées**, jamais de flou, en **noir à 30 %** : plus claires que les bordures (noir pur) pour que le contour reste dominant. `box-shadow: 6px 6px 0 rgba(0,0,0,.3)`.
3. **Aucun arrondi** (`border-radius: 0`). Aucun dégradé, aucune transparence.
4. **Couleurs plates et saturées** sur fond crème, texte noir pur.
5. **Typographie lourde** : titres en grotesque extra-gras, données en monospace.
6. **Grille visible** : blocs rectangulaires collés, séparés par des traits noirs.
7. **Interaction mécanique** : au survol le bloc se décale, à l'appui il « s'enfonce » (l'ombre disparaît). Pas d'animation douce, des sauts de 100 ms en `steps()`.
8. **Accessibilité d'abord** (WCAG 2.2 AA, voir [`ACCESSIBILITY.md`](ACCESSIBILITY.md)) : contraste texte ≥ 4,5:1, texte ≥ 14 px, **focus visible = anneau noir 4 px + liseré blanc 2 px** (jamais jaune seul : 1,12:1), cibles ≥ 32 px desktop et 44 px mobile, `prefers-reduced-motion` respecté.
9. **Règles de couleur** : jamais de texte noir sur bleu `#2B3BFF` (3,17:1), jamais de texte blanc sur rouge `#FF3B30` (3,55:1).

## Palette
| Rôle | Nom | Hex |
|---|---|---|
| Fond | Papier | `#F4F0E6` |
| Texte / traits | Encre | `#000000` |
| Action principale | Jaune signal | `#FFE500` |
| Danger / vente | Rouge brut | `#FF3B30` |
| Information / lien | Bleu électrique | `#2B3BFF` |
| Succès | Vert acide | `#3DDC84` |
| Accent | Rose choc | `#FF6AD5` |

### Raretés des cartes
| Rareté | Code | Couleur de fond | Marque distinctive |
|---|---|---|---|
| Commune | C | `#F4F0E6` | bordure simple |
| Peu commune | PC | `#3DDC84` | coin coupé |
| Rare | R | `#2B3BFF` (texte blanc) | double bordure |
| Super rare | SR | `#FF6AD5` | motif de points |
| Ultra rare | UR | `#FF3B30` (texte noir) | rayures diagonales |
| Légendaire | L | `#FFE500` | cadre noir épais + étoile |

> La rareté ne repose jamais sur la couleur seule : le code (C, PC, R, SR, UR, L) est toujours écrit sur la carte.

## Mouvement
Les animations sont réalisées en **HTML/CSS** (pas dans Figma) :
- Boutons : survol `translate(-2px,-2px)` + ombre 6 px, appui `translate(4px,4px)` sans ombre, 100 ms.
- Ouverture d'un paquet : les cartes sont **révélées une par une, de la moins rare à la plus rare**, au rythme du joueur (boutons « Révéler la carte suivante » et « Tout révéler »). Chaque carte apparaît avec `animation: reveal 240ms steps(4)` (saut « mécanique » plutôt que fondu). Une annonce `role=status` indique la carte révélée. Sans JavaScript, toutes les cartes sont visibles.
- `prefers-reduced-motion: reduce` : aucune animation, les cartes sont affichées directement.
- Compte à rebours : texte mis à jour à la minute, jamais annoncé en continu aux lecteurs d'écran.

## Symboles (pas d'émojis)
Aucun émoji (rendu variable, couleurs imposées par le système). Seuls des **symboles typographiques**, qui prennent la couleur du texte : `▲` erreur, `✓` succès, `●` information, `◆` pièces, `←` retour, `⇄` échange, `☐` case. Chaque symbole accompagne toujours un texte.

## Typographie
| Usage | Police | Graisse | Remarque |
|---|---|---|---|
| Titres | **Archivo Black** (ou Space Grotesk 700) | 900 | MAJUSCULES, interlignage 0.95 |
| Texte | **Space Grotesk** | 400 / 600 | corps 16–18 px |
| Données, prix, stats | **JetBrains Mono** | 500 / 700 | chiffres tabulaires |

Échelle : 12 / 14 / 16 / 20 / 28 / 40 / 64 px. Polices servies depuis nos propres fichiers (`static/fonts`) : pas de requête externe.

## Espacement et grille
- Unité de base : **8 px**. Espacements : 8, 16, 24, 32, 48, 64.
- Conteneur : 1280 px max, 12 colonnes, gouttière 0 (les blocs se touchent, séparés par la bordure).
- Points de rupture : 640, 1024, 1280 px. Mobile d'abord.

## Composants
| Composant | Description |
|---|---|
| **Bouton — états** | Repos, **survol** (ombre 6 px + texte souligné), **appui** (ombre 0), **désactivé** (fond gris, pointillés, texte `#595447`), **focus** (anneau). |
| **Bouton** | Rectangle plein, bordure 3 px, ombre 4 px. Dans un tableau : 14 px de marge verticale dans la ligne, le bouton ne touche jamais les bords. Hover : décalage (−2, −2). Active : ombre 0, décalage (+4, +4). |
| **Carte** | Ratio 5:7, bordure 4 px, bandeau de rareté en haut, image en niveaux de gris par défaut puis couleur au survol, stats en monospace en pied. |
| **Champ de formulaire** | Bordure 3 px, fond blanc, étiquette au-dessus en majuscules. **États : repos, focus (anneau noir + blanc), erreur (bordure 5 px + bloc rouge « ▲ ERREUR : … » en texte noir), désactivé (pointillés, fond gris).** |
| **Tag / badge** | Rectangle, bordure 2 px, texte monospace en majuscules. |
| **Tableau** | Lignes séparées par 3 px, en-tête noir sur texte crème. |
| **Modale** | Bordure 4 px, ombre 12 px, fond de page noir à 100 % de contraste (pas de flou). |
| **Mobile** | 375 px (320 px minimum). Barre haute (logo + portefeuille), **barre d'onglets fixe en bas** (Paquets, Album, Marché, Échanges, 44 px), cartes compactes en 2 colonnes (164 px), boutons pleine largeur. |
| **Captcha** | Widget Cap habillé aux couleurs du site (bordure noire, case carrée). |
| **Compte à rebours (enchère)** | Bloc monospace 40 px, fond jaune ; rouge sous 5 min. |
| **Message d'état (toast)** | Bandeau plein largeur en haut, symbole (✓ ▲ ●) + texte + bouton FERMER, 3 types : succès (vert), erreur (rouge, texte noir), info (jaune). Reste affiché tant qu'il n'est pas fermé (≥ 5 s). |

## Pages principales (maquettes Figma)
1. Accueil (visiteur) – accroche, aperçu de cartes, inscription.
2. Inscription / Connexion + captcha.
3. Ouverture de paquet.
4. Album (collection) – filtres par rareté et tag, recherche.
5. Détail d'une carte – stats, source Wikipédia, historique des prix.
6. Marché – liste des ventes, filtres, tri.
7. Échanges – proposer / répondre à une offre.
8. Profil et portefeuille.
9. États vides, erreurs 404/429, chargement.

## Tokens (extrait Tailwind)
```js
// tailwind.config.js
theme: {
  borderRadius: { none: '0' },
  extend: {
    colors: { paper: '#F4F0E6', ink: '#000', signal: '#FFE500', brut: '#FF3B30',
              volt: '#2B3BFF', acid: '#3DDC84', shock: '#FF6AD5' },
    // `hard` et non `brut` : `shadow-brut` entrerait en collision avec la couleur `brut`.
    boxShadow: { hard: '6px 6px 0 rgba(0,0,0,.3)', 'hard-sm': '4px 4px 0 rgba(0,0,0,.3)', 'hard-lg': '12px 12px 0 rgba(0,0,0,.3)' },
    borderWidth: { 3: '3px' },
    fontFamily: { display: ['"Archivo Black"'], sans: ['"Space Grotesk"'], mono: ['"JetBrains Mono"'] },
  },
}
```
