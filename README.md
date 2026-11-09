# Bip & Mocha

Chaîne TikTok de divertissement **sans dialogue**, pensée pour une audience mondiale
et conçue dès le départ pour être éligible à la monétisation TikTok.

> Deux personnages, zéro mot, des histoires que tout le monde comprend
> à Tokyo, São Paulo, Lagos ou Paris.

## Le pitch en 3 lignes

- **Bip** : un petit robot curieux et maladroit qui ne s'exprime qu'en *bips*, en sons et avec son écran-visage.
- **Mocha** : un chat couleur café, flegmatique, malin, qui comprend tout et en profite.
- Chaque épisode (60–90 s) = un problème du quotidien, une catastrophe en chaîne, une chute qui fait rire.

## Documents du projet

| # | Document | Contenu |
|---|----------|---------|
| 1 | [Concept & univers](docs/01-concept.md) | Personnages, ton, règles de l'univers |
| 2 | [Monétisation TikTok](docs/02-monetisation.md) | Règles de la monétisation, sources de revenus, checklist de conformité |
| 3 | [Format vidéo](docs/03-format-video.md) | Structure d'un épisode, règles « sans langue », specs techniques |
| 4 | [Production](docs/04-production.md) | Options de fabrication, pipeline, outils, assets |
| 5 | [Épisodes](docs/05-episodes.md) | 12 pitchs + 1 script détaillé |
| 6 | [Plan de lancement](docs/06-plan-lancement.md) | Plan 90 jours, objectifs, KPIs, décisions prises |
| 7 | [Pipeline IA](docs/07-pipeline-ia.md) | Où et comment utiliser l'IA sans perdre la monétisation |
| 8 | [Fiches personnages](docs/08-fiches-personnages.md) | Proportions, palette, 18 expressions de Bip, guide Blender, prompts IA |
| 9 | [Apprendre Blender — semaine 1](docs/09-apprentissage-blender.md) | Programme jour par jour + script de préparation de scène |
| 10 | [Rendre un épisode sur votre PC](docs/10-rendu-sur-pc.md) | Vidéo MP4 avec le son en un clic (carte graphique = 5 à 10× plus rapide) |

**Scripts des épisodes** : [`episodes/`](episodes/) (épisodes 01 à 06 écrits).

**Outils** :
- `tools/generer-design.js` — visuels de référence (planches, écrans de Bip)
- `tools/blender/preparer-scene.py` — scène Blender prête à animer (Bip, Mocha, caméras)
- `tools/blender/decor-cuisine.py` — décor de la cuisine
- `tools/blender/style-studio.py` — look « film d'animation » (plastique laqué, pelage, grands yeux, lumière, flou)
- `tools/blender/outils_animation.py` — outils communs aux scripts d'épisode (images clés, expressions, caméras, rendu propre)
- `tools/audio/sons.py` — bibliothèque de sons synthétisés (bips, bruitages, musique) → `assets/sons/`
- `tools/assembler-video.sh` — images + bande-son → MP4 TikTok
- `tools/rendre-episode.bat` + `tools/blender/rendre-video.py` — rendu d'un épisode en MP4 avec le son, en un clic sous Windows

## Statut

Phase 0 — préparation. Choix validés : **3D (Blender) · solo · ~2 h/jour · IA importante**.
Prochaine étape : semaine 1 du [plan de préparation](docs/06-plan-lancement.md#phase-0--préparation-6-semaines-2-hjour)
(design de Bip et Mocha) avec les [fiches personnages](docs/08-fiches-personnages.md).
