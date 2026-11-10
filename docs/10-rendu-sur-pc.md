# 10 — Rendre un épisode en vidéo sur votre PC

Les épisodes sont entièrement décrits par des scripts (`episodes/XX-…/animatique.py`) : votre PC
reconstruit la scène, l'anime et la calcule. **Avec une carte graphique, c'est 5 à 10 fois plus rapide**
que dans le cloud (≈ 2 à 4 h par épisode avec le style « studio » — pelage, reflets, flou —
contre une trentaine d'heures sur le serveur).

Résultat : `episodes/XX-…/rendu/episode-XX.mp4` — vertical 1080 × 1920, 30 images/s, **avec la bande-son**,
prêt à être importé dans CapCut ou TikTok.

## Ce qu'il faut
- **Blender 4.2 ou plus récent** (gratuit : blender.org). Les versions 4.x et 5.x sont gérées.
- Le dossier du projet sur le PC. Sur GitHub : bouton vert **Code → Download ZIP**, puis
  « Extraire tout » (par exemple dans `C:\BipEtMocha`).
  Tant que la pull request n'est pas fusionnée, choisir d'abord la branche `claude/gifted-allen-xytuhu`
  dans le menu des branches (en haut à gauche).
- Rien d'autre : la bande-son est fabriquée par Blender lui-même, et Blender écrit le MP4.

## Méthode A — en un clic (recommandée)
1. Dans le dossier du projet, ouvrir `tools` et **double-cliquer sur `rendre-episode.bat`**.
2. Taper le numéro de l'épisode (`01` ou `06`), puis Entrée.
3. Laisser tourner (PC branché, mise en veille désactivée). La fenêtre affiche l'avancement image par image.
4. À la fin : `episodes\06-le-bouton-rouge\rendu\episode-06.mp4`.

Si le message « Blender introuvable » s'affiche : clic droit sur `rendre-episode.bat` → **Modifier**,
et écrire le chemin de Blender à la ligne `set "BLENDER="`, par exemple :
`set "BLENDER=C:\Program Files\Blender Foundation\Blender 4.5\blender.exe"`
(installation Steam : `C:\Program Files (x86)\Steam\steamapps\common\Blender\blender.exe`).

## Méthode B — dans Blender (pour voir et retoucher)
1. Ouvrir Blender → onglet **Scripting** → **Ouvrir** `episodes/06-le-bouton-rouge/animatique.py` → **▶**.
   La scène complète apparaît : personnages, décor, caméras (un marqueur par plan dans la timeline).
2. Toujours dans Scripting : **Ouvrir** `tools/blender/rendre-video.py` → **▶**.
3. Menu **Render → Render Animation** (Ctrl+F12).

Avant l'étape 3, vous pouvez tout retoucher à la main : poses, timing, cadrages… C'est là que se fait
**votre contribution créative** (importante pour la monétisation, voir [docs/07](07-pipeline-ia.md)).
Pensez à enregistrer le fichier `.blend` : relancer `animatique.py` reconstruit la scène de zéro.

## Bon à savoir
- **Aperçu rapide** : dans *Propriétés → Sortie*, mettre la résolution à 50 % pour un test 4 fois plus
  rapide ; remettre 100 % pour la version finale.
- **Le rendu MP4 ne reprend pas** s'il est interrompu (il repart du début). Pour un rendu très long en
  plusieurs fois, rendre plutôt en images PNG (voir l'en-tête de `animatique.py`) puis les assembler avec
  `tools/assembler-video.sh`.
- **Message « Dossier du projet introuvable »** : ouvrir le script concerné et remplir
  `DOSSIER_PROJET = r"C:\BipEtMocha"` en haut du fichier.
- **Qualité** : 4 passes EEVEE + débruiteur (OpenImageDenoise). Si vous voyez encore du grain,
  augmenter *Render → Sampling → Render* à 8 ou 16.
