# Accessibilité – Cartopedia (WCAG 2.2, niveau AA visé)

> **Périmètre honnête.** Cet audit porte sur la **maquette Figma** (10 écrans desktop, 9 écrans mobile) et sur les choix de conception. Le site n'est pas encore codé : **aucune conformité WCAG 2.2 ne peut être déclarée** tant que le code n'a pas été testé (clavier, lecteur d'écran, zoom, outils automatiques). Ce document dit ce qui est **acquis côté design**, ce qui a été **corrigé**, et ce qui reste **à vérifier à l'implémentation**.

## Résultat de l'audit de la maquette

| Verdict | Nombre | Détail |
|---|---|---|
| Conforme côté design | 20 critères | contrastes, cibles, reflow, couleur non seule porteuse, authentification, aide cohérente, erreurs maquettées… |
| Corrigé pendant l'audit | 10 problèmes | voir ci-dessous |
| À vérifier à l'implémentation | 13 critères | nécessitent du code (structure, ARIA, clavier, annonces des messages…) |

## Problèmes trouvés et corrigés

| # | Critère | Problème | Correction |
|---|---|---|---|
| 1 | 1.4.3 Contraste (minimum) | Texte blanc sur rouge `#FF3B30` : **3,55:1** (< 4,5:1) sur la rareté UR et le bouton Danger | Texte **noir** : **5,92:1** |
| 2 | 2.4.7 / 2.4.11 Focus visible | Le focus prévu (contour jaune) donnait **1,12:1** sur le fond papier et était invisible sur le jaune | Anneau **noir 4 px + liseré blanc 2 px** : 18,45:1 sur papier, 16,46:1 sur jaune, 3,17:1 sur bleu (≥ 3:1) |
| 3 | 1.4.4 Redimensionnement / lisibilité | Textes de **11 à 13 px** (bandeaux de carte, descriptions, mention Cap) | Minimum **14 px** partout |
| 4 | 2.5.8 Taille de cible (minimum) | Liens de navigation d'environ 20 px de haut | Cibles de **32 px** (desktop) et **44 px** (mobile) |
| 5 | 1.4.3 Contraste | Texte indicatif (placeholder) `#6B6659` : 5,72:1, trop proche de la limite | `#595447` : **7,54:1** (mobile ; à reprendre sur desktop) |
| 6 | 1.4.10 Reflow | Aucune version petit écran | **15 écrans mobiles** à 375 px, cartes en 2 colonnes, onglets en bas |
| 7 | 3.2.6 Aide cohérente | Aucun moyen d'aide | Lien **AIDE** au même endroit (bandeau haut, avant le solde) sur **tous** les écrans desktop et mobile + page Aide et contact |
| 8 | 3.3.1 / 3.3.3 Erreurs | Aucun état d'erreur | Composant **Champ** (repos, focus, **erreur**, désactivé) : message textuel avec symbole ▲ et « ERREUR : », bordure épaissie ; écran « Inscription — erreurs » avec résumé et captcha échoué |
| 9 | 4.1.3 Messages d'état | Aucun retour après une action | Composant **Message d'état** (succès, erreur, info) avec symbole (✓ ▲ ●), texte et bouton Fermer ; écrans « Vente confirmée » et « 429 » |
| 10 | 1.4.1 / 2.4.8 Page courante | La page active n'était pas indiquée sur desktop | Lien actif **souligné** (pas seulement coloré) ; onglet inversé en noir sur mobile ; à coder avec `aria-current="page"` |

## Contrastes mesurés (palette)

| Paire | Ratio | Usage | Seuil | OK |
|---|---|---|---|---|
| Noir / papier `#F4F0E6` | 18,45:1 | texte courant | 4,5:1 | oui |
| Noir / blanc | 21,00:1 | champs, tableaux | 4,5:1 | oui |
| Noir / jaune `#FFE500` | 16,46:1 | boutons, navigation | 4,5:1 | oui |
| Blanc / bleu `#2B3BFF` | 6,62:1 | rareté R, bouton Info | 4,5:1 | oui |
| Noir / bleu `#2B3BFF` | 3,17:1 | **interdit pour le texte** | 4,5:1 | non (non utilisé) |
| Noir / rouge `#FF3B30` | 5,92:1 | rareté UR, bouton Danger | 4,5:1 | oui |
| Noir / vert `#3DDC84` | 11,77:1 | rareté PC | 4,5:1 | oui |
| Noir / rose `#FF6AD5` | 8,27:1 | rareté SR | 4,5:1 | oui |
| Blanc / noir | 21,00:1 | pied de page, bandeaux | 4,5:1 | oui |
| Jaune / blanc | 1,28:1 | **jamais** seul comme indice | 3:1 | non (toujours bordé de noir) |

Règle : **pas de texte noir sur `#2B3BFF`, pas de blanc sur `#FF3B30`**.

## Critères WCAG 2.2 – état par critère

### Perceptible
| Critère | Niveau | État | Note |
|---|---|---|---|
| 1.1.1 Contenu non textuel | A | À vérifier | `alt` = titre de l'article sur chaque image de carte ; icônes décoratives `alt=""` |
| 1.3.1 Information et relations | A | À vérifier | vrais `<table>`, `<th scope>`, `<label for>`, titres h1/h2 hiérarchisés |
| 1.3.4 Orientation | AA | Conforme | portrait et paysage prévus |
| 1.3.5 But des champs | AA | À vérifier | `autocomplete="username email new-password"` |
| 1.4.1 Utilisation de la couleur | A | **Conforme** | la rareté est écrite (C, PC, R, SR, UR, L), pas seulement colorée |
| 1.4.3 Contraste (minimum) | AA | **Conforme** | voir tableau (après correction 1) |
| 1.4.4 Redimensionner le texte | AA | À vérifier | unités `rem`, test à 200 % |
| 1.4.10 Reflow | AA | **Conforme (design)** | 320 px sans défilement horizontal à confirmer en code |
| 1.4.11 Contraste du non-textuel | AA | **Conforme** | bordures noires 3 px, anneau de focus ≥ 3:1 |
| 1.4.12 Espacement du texte | AA | À vérifier | pas de hauteur fixe sur les cartes (`min-height`) |
| 1.4.13 Contenu au survol | AA | Conforme | aucune info uniquement au survol (les images couleur au survol sont décoratives) |

### Utilisable
| Critère | Niveau | État | Note |
|---|---|---|---|
| 2.1.1 Clavier | A | À vérifier | tout au clavier, aucun piège ; cartes = vrais `<a>` / `<button>` |
| 2.1.2 Pas de piège clavier | A | À vérifier | widget Cap et modales |
| 2.2.1 Réglage du délai | A | Conforme | le compte à rebours du paquet est informatif, aucune session ne s'interrompt |
| 2.2.2 Pause, arrêt, masquage | A | À vérifier | pas de mise à jour continue lue par les lecteurs d'écran (pas de `aria-live` à la seconde) |
| 2.3.1 Pas plus de trois flashs | A | Conforme | aucune animation de flash |
| 2.4.1 Contourner des blocs | A | À vérifier | lien d'évitement « Aller au contenu » |
| 2.4.2 Titre de page | A | À vérifier | un `<title>` unique par page |
| 2.4.3 Parcours du focus | A | À vérifier | ordre du DOM = ordre visuel |
| 2.4.7 Focus visible | AA | **Conforme (design)** | anneau défini dans le design system |
| **2.4.11 Focus non masqué (minimum)** | AA | **À vérifier** | la barre d'onglets mobile est fixe : prévoir `scroll-padding-bottom` ≥ sa hauteur |
| **2.5.7 Mouvements de pointage** | AA | Conforme | aucun glisser-déposer obligatoire |
| **2.5.8 Taille de cible (minimum)** | AA | **Conforme** | ≥ 32 px desktop, ≥ 44 px mobile (24 px exigés) |

### Compréhensible
| Critère | Niveau | État | Note |
|---|---|---|---|
| 3.1.1 Langue de la page | A | À vérifier | `<html lang="fr">`, `lang` sur les extraits dans une autre langue |
| 3.2.2 Saisie | A | À vérifier | pas de changement de contexte à la saisie |
| **3.2.6 Aide cohérente** | A | **Conforme (design)** | lien AIDE au même endroit sur toutes les pages (desktop et mobile) |
| 3.3.1 / 3.3.3 Erreurs | A / AA | **Conforme (design)** | erreur décrite en texte, avec suggestion de correction ; à relier en code par `aria-describedby` et `aria-invalid` |
| 3.3.2 Étiquettes | A | **Conforme** | libellé visible au-dessus de chaque champ |
| **3.3.7 Saisie redondante** | A | À vérifier | ne jamais redemander une information déjà fournie (vente, échange) |
| **3.3.8 Authentification accessible (minimum)** | AA | **Conforme (design)** | Cap = preuve de travail en arrière-plan : aucun test cognitif (pas de puzzle, pas de transcription) ; autoriser le collage et les gestionnaires de mots de passe |

### Robuste
| Critère | Niveau | État | Note |
|---|---|---|---|
| 4.1.2 Nom, rôle, valeur | A | À vérifier | composants natifs d'abord, ARIA seulement si nécessaire |
| 4.1.3 Messages d'état | AA | À vérifier | confirmations (« Carte vendue ») dans une zone `role="status"` |

## Ce qui manque encore dans la maquette
1. Version mobile de l'écran 429 et des erreurs réseau (500, hors ligne).
2. États survol/appui des **cartes** (le survol est décrit dans `DESIGN.md`, seul le focus est dessiné).
3. Modale de confirmation (si elle est ajoutée) : piège de focus et touche Échap à spécifier.

## Règles d'implémentation
- HTML sémantique d'abord : `<header>`, `<nav aria-label>`, `<main>`, `<footer>`, un seul `<h1>`.
- Erreurs : message relié au champ par `aria-describedby`, `aria-invalid="true"`, résumé en haut du formulaire avec `role="alert"` ; le message ne repose jamais sur la seule couleur.
- Page courante : `aria-current="page"` sur le lien actif du bandeau et de la barre d'onglets.
- Focus : `:focus-visible { outline: 4px solid #000; outline-offset: 2px; box-shadow: 0 0 0 2px #fff; }` (blanc sur fond noir).
- Chaque carte : un seul lien englobant avec un nom accessible complet, par exemple « Albert Einstein, ultra rare, attaque 7 470, défense 8 000 ».
- Compte à rebours : texte statique mis à jour toutes les minutes, jamais `aria-live` à la seconde.
- `prefers-reduced-motion` respecté ; aucune animation essentielle.
- Cap : widget accessible au clavier, repli signalé si le JavaScript est désactivé.

## Comment vérifier une fois codé
| Outil | Rôle |
|---|---|
| axe DevTools / Lighthouse | contrôle automatique (≈ 30 % des problèmes) |
| Navigation **clavier seul** | parcours complet inscription → paquet → vente |
| NVDA (Windows) + Firefox | lecture des cartes, tableaux, messages d'état |
| Zoom 200 % et 400 %, largeur 320 px | 1.4.4, 1.4.10 |
| Espacement du texte (bookmarklet) | 1.4.12 |

Un audit automatique ne suffit pas : la conformité WCAG 2.2 AA se déclare après tests manuels sur le site codé.
