# Notes de production — Épisode 06

## Animatique 3D v1 (version de travail, non publiable)
| Élément | Fichier | Comment le refaire |
|---|---|---|
| Scène + animation (1 980 images, 66 s) | `animatique.py` | Blender → Scripting → Ouvrir → ▶ (ou en ligne de commande, voir l'en-tête) |
| Outils d'animation communs | `tools/blender/outils_animation.py` | utilisé par `animatique.py` |
| Bande-son | `bande-son.py` → `bande-son.wav` | `python episodes/06-le-bouton-rouge/bande-son.py` |
| Montage | `tools/assembler-video.sh` | `tools/assembler-video.sh DOSSIER_IMAGES bande-son.wav sortie.mp4` |

**Rendu** : 1080 × 1920, ≈ 9,5 s par image sur 4 processeurs sans carte graphique (≈ 5 h 15) ;
avec une carte graphique récente, compter environ 1 à 2 s par image.

### Choix de mise en scène (écarts par rapport au script)
- **Accroche** : plan dédié `CAM_ACCROCHE` (patte + bouton + Mocha), puis retour 3 s en arrière
  quand les Mains apportent le boîtier.
- **Fois 1** filmée en plan « duo » (`CAM_DUO`, bouton au premier plan) plutôt qu'en plan Mocha :
  on voit à la fois la patte, le bouton et le bond de Bip.
- **L'aspirateur-robot** arrive par la droite du plan de travail (la cuisine n'a pas de porte visible).
- **Mocha ne se couche pas** : il s'endort assis, à portée de patte du bouton (indispensable pour la chute).
- Fête : boule à facettes + 3 lumières colorées qui alternent à chaque temps (120 bpm).

### Nouveaux assets (réutilisables)
- Boîtier à bouton rouge (`Boitier`, origine sur l'arête avant : il bascule au bord du plan de travail).
- Les Mains : pose « porte » (`Main_Porte`) et pose « doigt levé » (`Main_Doigt`).
- Aspirateur-robot (`Aspirateur`), boule disco (`Boule_Disco`), lumières `Disco_0..2`.
- Articulations : épaules de Bip (`Bip_Epaule_G/D`), patte avant de Mocha (`Mocha_Epaule_D`).
- Sons : gros clic, tic-tac qui accélère, pas, soupir, alarme, « non-non », aspirateur,
  musiques « suspense » et « disco » (`tools/audio/sons.py`).

### À améliorer pour la version finale
- Personnages définitifs (mêmes noms d'objets → l'animation se réapplique).
- Mains plus détaillées (doigts articulés) ; Mocha qui marche au lieu de glisser.

## IA (traçabilité)
- **Animatique v1 entièrement produite par Claude (IA)** par programmation (formes simples,
  images clés écrites en code, sons et musiques synthétisés, sans échantillon ni musique sous droits).
- Version publiée : apporter votre contribution créative et **activer l'étiquette IA** sur TikTok.

## Publication
- Date : …
- Durée finale : … s (≥ 60 s ?)
- Monétisation : acceptée / refusée (motif : …)

## Résultats à J+7
- Vues : … · Visionnage complet : … % · Durée moyenne : … s
- Partages : … · Commentaires : … · Abonnés gagnés : …
- Part des vues hors France : … %
- Ce qu'on retient : …
