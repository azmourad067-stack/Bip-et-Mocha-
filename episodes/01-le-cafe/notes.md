# Notes de production — Épisode 01 « Le café »

## Animatique 3D v1 (version de travail, non publiable)
Une **animatique** = l'épisode entier, animé et sonorisé, avec des personnages et un décor
provisoires. Elle sert à **valider le timing, les gags et la durée (≥ 60 s)** avant de
produire la version finale.

| Élément | Fichier | Comment le refaire |
|---|---|---|
| Scène + animation (2 250 images, 75 s) | `animatique.py` | Blender → Scripting → Ouvrir → ▶ (ou en ligne de commande, voir l'en-tête du fichier) |
| Décor cuisine | `tools/blender/decor-cuisine.py` | appelé par `animatique.py` |
| Bande-son (bips, bruitages, musique) | `bande-son.py` → `bande-son.wav` | `python episodes/01-le-cafe/bande-son.py` (numpy requis) |
| Montage vidéo | `tools/assembler-video.sh` | `tools/assembler-video.sh DOSSIER_IMAGES bande-son.wav sortie.mp4` |

**▶ Aperçu de la v1** : [`animatique-v1-apercu.mp4`](animatique-v1-apercu.mp4) (540 × 960, version allégée
pour le dépôt ; la version 1080 × 1920 se régénère avec le montage ci-dessus).

**Rendu** : 1080 × 1920 natif, EEVEE 4 échantillons + 4 rayons d'ombre + débruiteur
OpenImageDenoise (≈ 9,5 s par image sur 4 processeurs sans carte graphique, ≈ 6 h pour l'épisode ;
beaucoup plus rapide sur un PC avec carte graphique).
La v1 (540 × 960, 2 échantillons) était trop granuleuse : les ombres douces des lampes « Area »
ont besoin de plusieurs rayons, sinon chaque surface est mouchetée.

### Ce qui est validé par l'animatique
- Durée : **75 s** → éligible Creator Rewards (≥ 60 s).
- Structure : hook (catastrophe) → retour en arrière → 3 tentatives → catastrophe → chute tendre → boucle.
- Tous les plans du script minuté sont en place (14 plans, 4 caméras).

### À améliorer pour la version finale
- **Personnages définitifs** (semaine 2) : remplacer les blockouts en gardant les noms d'objets
  `Bip`, `Bip_Ecran`, `Mocha`, `Mocha_Tete`, `Mocha_Paupiere_G/D` → l'animation existante se réapplique.
- **Animation plus fine** : bras de Bip qui appuient vraiment sur les boutons, pattes de Mocha
  (aujourd'hui il « glisse »), antenne qui suit les mouvements.
- **Mousse** : plus de volume et de « remplissage » dans la scène de catastrophe.
  (v2 : les bulles placées devant la caméra sont cachées pendant les gros plans et devant
  l'écran de Bip / la tasse dans les plans larges — `degager_premier_plan()`.)
- **Sons** : les sons synthétisés sont des maquettes ; remplacer au moins le miaou et le
  ronronnement par de vrais enregistrements (ou une banque sous licence commerciale).

## IA (traçabilité)
- **Animatique v1 entièrement produite par Claude (IA)** par programmation : modèles en formes
  géométriques, animation par images clés écrites en code, sons et musique synthétisés
  (aucun échantillon externe, aucune musique sous droits).
- Pour la **version publiée** : apporter votre contribution créative (design final des
  personnages, retouches d'animation, timing, montage, sons) et **activer l'étiquette IA**
  sur TikTok. Voir [07-pipeline-ia.md](../../docs/07-pipeline-ia.md).

## Publication
- Date : …
- Durée finale : … s (≥ 60 s ?)
- Monétisation : acceptée / refusée (motif : …)

## Résultats à J+7
- Vues : … · Visionnage complet : … % · Durée moyenne : … s
- Partages : … · Commentaires : … · Abonnés gagnés : …
- Part des vues hors France : … %
- Ce qu'on retient : …
