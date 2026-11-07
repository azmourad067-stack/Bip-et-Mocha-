# 9. Apprendre Blender — semaine 1 (2 h par jour)

Objectif de la semaine : **savoir naviguer, modéliser simple, poser des matériaux,
animer et exporter une vidéo verticale**, et finir avec un premier clip de 5 s de Bip.

> Version conseillée : la dernière **LTS** sur blender.org (le script du projet a été testé
> avec **Blender 5.2 LTS**). Les tutoriels un peu plus anciens restent valables à 90 % :
> si un menu a bougé, chercher la fonction avec **F3** (recherche).

## Le raccourci : le script de préparation
Le dépôt contient [`tools/blender/preparer-scene.py`](../tools/blender/preparer-scene.py).
Lancé dans Blender, il crée en quelques secondes :
- une scène réglée pour TikTok (1080 × 1920, 30 im/s, EEVEE) ;
- **Bip** aux bonnes dimensions, avec contour cartoon et **un écran déjà branché sur les 18 expressions** ;
- un **Mocha** simplifié pour l'échelle ;
- sol, lumières, 3 caméras (`CAM_LARGE`, `CAM_BIP`, `CAM_MOCHA`) et les planches de référence ;
- une animation de démonstration de 5 s.

| Plan large | Plan serré Bip (expression « idée ») |
|---|---|
| ![](../assets/design/apercu-blockout-large.png) | ![](../assets/design/apercu-blockout-bip.png) |

**Lancer le script** : Blender → Fichier → Nouveau → Général → supprimer le cube (X) →
onglet **Scripting** → **Ouvrir** → `tools/blender/preparer-scene.py` → bouton **▶**.

**Changer l'expression de Bip** : sélectionner l'objet `Bip` → panneau **Propriétés de l'objet** →
**Propriétés personnalisées** → `expression` (0 à 17). Survoler le champ et appuyer sur **I** pour
poser une image clé. Correspondance des numéros :

| N° | Expression | N° | Expression | N° | Expression |
|---|---|---|---|---|---|
| 0 | neutre | 6 | surprise | 12 | veille |
| 1 | joie | 7 | question | 13 | batterie faible |
| 2 | très joyeux | 8 | exclamation | 14 | erreur |
| 3 | triste | 9 | idée | 15 | chargement |
| 4 | pleure | 10 | amour | 16 | clin d'œil |
| 5 | colère | 11 | panique | 17 | déterminé |

⚠️ Ce sont des **blockouts** (formes provisoires) : parfaits pour apprendre, faire des
animatiques et tester le timing. Les vrais modèles (semaine 2) les remplaceront — on garde
le même nom d'objet `Bip` et le même matériau d'écran.

---

## Programme jour par jour

### Jour 1 — L'interface (2 h)
- Installer Blender, **Édition → Préférences → Interface** : langue au choix
  (les tutoriels sont souvent en anglais : garder l'anglais aide à les suivre).
- Suivre la première partie d'un tutoriel débutant complet : le classique **« Donut »
  de Blender Guru** (YouTube), ou la série gratuite **« Blender Fundamentals »** de
  Blender Studio (studio.blender.org).
- Retenir : tourner (clic molette), zoomer (molette), déplacer (Maj + molette),
  vues de face/côté/dessus (pavé numérique 1 / 3 / 7).

### Jour 2 — Modéliser (2 h)
- Continuer le tutoriel : mode Édition (**Tab**), extruder (**E**), modificateurs
  **Subdivision Surface** et **Mirror**.
- Exercice : refaire **à la main** un corps d'œuf comme celui de Bip (sans regarder le script).

### Jour 3 — Matériaux, lumière, caméra (2 h)
- Matériaux (Principled BSDF), couleurs de la [palette](../assets/design/palette.png),
  lumières, caméra.
- Lancer **le script de préparation** et explorer la scène créée : ouvrir l'onglet
  **Shading** sur `Bip_Ecran` pour voir comment l'atlas d'expressions est branché.

### Jour 4 — Animer (2 h)
- Images clés (**I**), timeline, **Graph Editor** (courbes d'animation).
- Les 12 principes de l'animation : regarder une vidéo de résumé (anticipation,
  exagération, *squash & stretch*, timing). **C'est ce qui rend un gag drôle.**
- Exercice : Bip saute de joie (anticipation → saut → écrasement à l'atterrissage).

### Jour 5 — Jouer avec Bip (2 h)
- Supprimer l'animation de démo, et animer **la séquence « idée »** de l'épisode 01 :
  Bip regarde la tasse → `question` → `idee` → `determine` → il démarre en roulant.
- Ajouter le **micro-clignotement** : passer 2 images sur `veille` entre deux expressions.
- Animer l'antenne (rotation légère, en retard sur le mouvement du corps : c'est le
  principe du *follow-through*).

### Jour 6 — Rendu et export vidéo (2 h)
- **Rendu → Rendu de l'animation** (Ctrl + F12). Conseil : sortir en **séquence PNG**
  (`Sortie` → format PNG) puis assembler dans DaVinci Resolve / CapCut : si Blender plante,
  rien n'est perdu.
- Ajouter quelques bips (enregistrés ou générés) au montage, exporter en **MP4 1080 × 1920**.
- Vérifier sur le téléphone : lisible ? expressions visibles ? zone basse (légende) dégagée ?

### Jour 7 — Design (2 h)
- Utiliser les prompts de [08-fiches-personnages.md](08-fiches-personnages.md#-prompts-pour-les-images-de-référence-ia)
  pour générer 20–40 variantes de Bip et Mocha.
- Choisir les meilleures, les annoter, les ranger dans `assets/design/references-ia/`.
- Bilan de la semaine + préparer la semaine 2 (vrais modèles).

## Livrable de fin de semaine
✅ Un clip de **5 secondes** : Bip a une idée et part en roulant, avec ses bips,
au format TikTok. (À ne pas publier : c'est un test… mais il peut servir de teaser plus tard.)

## Aide-mémoire des raccourcis
| Action | Raccourci |
|---|---|
| Déplacer / Tourner / Échelle | **G** / **R** / **S** (puis X, Y ou Z pour bloquer un axe) |
| Mode Objet ↔ Édition | **Tab** |
| Extruder | **E** |
| Poser une image clé | **I** |
| Rechercher une commande | **F3** |
| Vue caméra | Pavé num. **0** |
| Isoler l'objet sélectionné | Pavé num. **/** |
| Annuler | **Ctrl + Z** |
| Rendu image / animation | **F12** / **Ctrl + F12** |

## Pièges classiques de débutant
- **Appliquer l'échelle** (Ctrl + A → Échelle) avant de riguer ou d'ajouter des modificateurs.
- **Enregistrer souvent** et en versions (`bip_v01.blend`, `bip_v02.blend`…) ;
  activer l'enregistrement automatique dans les Préférences.
- Rendu trop lent → vérifier qu'on est bien en **EEVEE** et baisser les *samples*.
- Ne pas viser la perfection en semaine 1 : l'objectif est d'être **à l'aise**, pas d'être bon.
