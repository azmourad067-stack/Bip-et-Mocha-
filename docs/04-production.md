# 4. Production

## Choix retenus
- **Technique** : animation **3D** (Blender), style simple et stylisé.
- **Équipe** : **seul**.
- **Temps disponible** : **~2 h par jour**, soit ~14 h par semaine.
- **IA** : usage **important**, encadré (détail dans [07-pipeline-ia.md](07-pipeline-ia.md)).

## Le principe qui rend ça tenable : « le plateau fixe »
En solo avec 2 h par jour, on ne peut pas faire du cinéma d'animation. On fait une **sitcom 3D** :
- **3 décors fixes** (cuisine, canapé, balcon), éclairage réglé une fois pour toutes.
- **4–5 angles de caméra préréglés** par décor (plan large, plan serré Bip, plan serré Mocha,
  plongée, « regard caméra » de Mocha).
- **Une bibliothèque d'animations réutilisables** (marcher, sauter, tomber, bâiller, sursauter…).
- **Un fichier modèle `.blend`** par décor : on ouvre, on place les personnages, on enchaîne
  les animations de la bibliothèque, on ajuste.
- Rendu rapide avec **EEVEE** (pas Cycles) et un style cartoon qui pardonne les imperfections.

Résultat visé : **un épisode de 60–75 s en ~4 h** une fois la bibliothèque construite.

## Rythme réaliste
| Contenu | Temps | Fréquence |
|---|---|---|
| Épisode monétisable (≥ 60 s) | ~4 h | **3 par semaine** |
| Micro-gag (10–20 s, réutilise les plans d'un épisode) | ~30 min | 2–3 par semaine |
| Écriture, analyse des stats, commentaires | ~1 h | par semaine |

→ **5 à 6 publications par semaine**, dont 3 qui rapportent.

## Semaine type (2 h/jour)
| Jour | Tâche |
|---|---|
| Lundi | Écriture : 3 scripts + storyboards de la semaine (avec aide IA) · analyse des stats |
| Mardi | Animation épisode A |
| Mercredi | Son + montage épisode A · animation épisode B (début) |
| Jeudi | Animation épisode B (fin) + son + montage |
| Vendredi | Animation épisode C |
| Samedi | Son + montage épisode C · 2–3 micro-gags |
| Dimanche | Repos, ou rattrapage / avance sur le stock |

Publication : programmer les vidéos à l'avance (planificateur de TikTok Studio)
pour ne pas dépendre du jour de production.

## Pipeline d'un épisode
1. **Idée + script** (banque d'idées dans [05-episodes.md](05-episodes.md), aide IA possible) — 20 min
2. **Storyboard** : 8–12 cases (croquis, ou images IA pour visualiser — jamais publiées) — 20 min
3. **Animatique** : storyboard minuté avec sons provisoires → valider la durée ≥ 60 s — 20 min
4. **Mise en scène 3D** : ouvrir le décor modèle, placer caméras et personnages — 30 min
5. **Animation** : bibliothèque d'animations + capture de mouvement par IA + retouches — 1 h 30
6. **Rendu** EEVEE (tourne pendant qu'on fait autre chose)
7. **Sound design** : bips, bruitages, musique — 30 min
8. **Montage et export** 9:16 — 20 min
9. **Checklist conformité** ([02-monetisation.md](02-monetisation.md#d-checklist-avant-chaque-publication)) — 5 min

## Outils
- **3D** : Blender (gratuit) — rendu EEVEE
- **Montage** : DaVinci Resolve ou CapCut
- **Son** : Audacity ou Reaper
- **IA** : voir [07-pipeline-ia.md](07-pipeline-ia.md)

## Matériel minimum
- Un PC avec une carte graphique correcte (le rendu EEVEE et les outils 3D en profitent beaucoup).
- Un smartphone : pour filmer ses propres mouvements (capture de mouvement par IA) et
  enregistrer des bruitages.

## Bibliothèque d'assets à constituer (avant le lancement)
- Modèles riggés de Bip et Mocha + 10 expressions chacun (écran de Bip = textures d'émojis)
- 3 décors : cuisine, salon/canapé, balcon (+ caméras préréglées)
- 20 animations réutilisables
- Banque de sons : 30 bips de Bip classés par émotion, 15 sons de Mocha, 50 bruitages
- 1 jingle signature + 3 boucles musicales

## Organisation du dépôt
```
docs/          → documents de conception
episodes/      → un dossier par épisode : script.md, storyboard, notes, % d'IA utilisé
assets/        → sources des personnages, décors, sons (ou lien vers stockage externe)
licences/      → preuves de licences musique / sons / outils IA
```
Les fichiers lourds (vidéos, projets Blender) sont à stocker hors Git
(Google Drive, Dropbox) ou via Git LFS.
