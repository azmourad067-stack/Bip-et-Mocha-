# 4. Production

## Options de fabrication

| Option | Coût | Vitesse | Unicité | Risque monétisation | Commentaire |
|---|---|---|---|---|---|
| **A. Animation 3D** (Blender) | Faible en argent, élevé en temps | Lente au début, rapide ensuite (assets réutilisables) | ⭐⭐⭐ | Faible | **Recommandée** : personnages réutilisables à l'infini |
| B. Animation 2D (Toon Boom, Krita, Moho, After Effects) | Faible | Moyenne | ⭐⭐⭐ | Faible | Bon choix si on dessine bien |
| C. Animation assistée par IA | Faible | Très rapide | ⭐ | **Élevé** (contenu « synthétique », cohérence des personnages) | En appoint seulement, avec étiquette |
| D. Prises de vue réelles : vrai chat + robot jouet/marionnette | Moyen | Variable (le chat décide !) | ⭐⭐ | Faible | Très attachant mais dépend de l'animal, bien-être animal à respecter |
| E. Stop-motion (pâte à modeler / peluches) | Moyen | Très lente | ⭐⭐⭐ | Faible | Superbe, mais difficile à tenir à un rythme quotidien |

**Recommandation** : 3D (option A) avec des personnages simples et stylisés
(formes rondes, peu de détails) → modélisés une seule fois, puis chaque épisode
réutilise décors, animations et bruitages. Un rythme de 3–4 épisodes/semaine devient tenable.

## Pipeline d'un épisode
1. **Idée** (banque d'idées dans [05-episodes.md](05-episodes.md)) — 15 min
2. **Storyboard** : 8–12 cases, croquis rapides — 30 min
3. **Animatique** : storyboard minuté avec sons provisoires → valider le timing et la durée ≥ 60 s — 30 min
4. **Animation** — 3–8 h selon complexité
5. **Sound design** : bips, bruitages, musique — 1 h
6. **Montage et export** 9:16 — 30 min
7. **Checklist conformité** ([02-monetisation.md](02-monetisation.md#d-checklist-avant-chaque-publication)) — 5 min
8. **Publication** + réponse aux commentaires dans la 1re heure

## Outils (gratuits en priorité)
- **3D** : Blender
- **2D** : Krita, OpenToonz
- **Montage** : DaVinci Resolve, CapCut
- **Son** : Audacity, Reaper ; bruitages : Freesound (vérifier la licence de chaque son), enregistrements maison
- **Musique** : composition originale (GarageBand, LMMS) ou banque libre de droits avec licence commerciale
- **Organisation** : ce dépôt (scripts, storyboards, licences, calendrier)

## Bibliothèque d'assets à constituer (avant le lancement)
- Modèles/rigs de Bip et Mocha + 10 expressions chacun
- 3 décors : cuisine, salon/canapé, balcon
- 20 animations réutilisables (marcher, sauter, tomber, s'asseoir, sursauter…)
- Banque de sons : 30 bips de Bip classés par émotion, 15 sons de Mocha, 50 bruitages
- 1 jingle signature + 3 boucles musicales

## Organisation proposée du dépôt
```
docs/          → documents de conception (ce dossier)
episodes/      → un dossier par épisode : script.md, storyboard, notes
assets/        → sources des personnages, décors, sons (ou lien vers stockage externe)
licences/      → preuves de licences musique / sons
```
Les fichiers lourds (vidéos, projets Blender) sont à stocker hors Git
(Google Drive, Dropbox) ou via Git LFS.
