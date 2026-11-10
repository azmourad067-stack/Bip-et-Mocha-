# Notes de production — Épisode 02

## Animatique 3D v1 (version de travail, non publiable)
| Élément | Fichier | Comment le refaire |
|---|---|---|
| Scène + animation (2 130 images, 71 s) | `animatique.py` | Blender → Scripting → Ouvrir → ▶ (ou en ligne de commande, voir l'en-tête) |
| Décor du salon | `tools/blender/decor-salon.py` | utilisé par `animatique.py` (réutilisable : épisodes 03, 05, fin du 04) |
| Bande-son | `bande-son.py` → `bande-son.wav` | `python episodes/02-le-carton/bande-son.py` |
| Vidéo finale sur PC | `tools/rendre-episode.bat` | double-clic, puis taper `2` |
| Aperçu rapide (brouillon) | options `--apercu --pas 2 --pourcentage 20` | voir l'en-tête de `animatique.py` |

### Choix de mise en scène (écarts par rapport au script)
- **Le ruban** descend sur les côtés du carton (Bip est plus petit que le carton : il ne peut pas
  atteindre le dessus). Le gag des bras : le ruban tient bon, Bip recule, ses bras s'étirent…
  puis tout se décolle d'un coup (SCRITCH) et Bip est projeté contre le canapé.
- **Duel** : Bip attrape Mocha par les joues avec ses bras élastiques ; Mocha s'étire comme un
  liquide, de plus en plus haut, puis glisse. À la 3e fois, Bip tombe à la renverse.
- **Le renversement** : Bip tire le rabat avant, le carton bascule vers la caméra. Mocha est
  « versé » dehors comme un liquide… et retourne aussitôt s'installer dans le carton couché,
  qui devient une petite grotte face à la caméra.
- **Le POP final** fait sursauter Mocha : il se cogne au « plafond » du carton (queue gonflée).
- Les « pop » sont calés sur la musique (120 bpm = un temps toutes les 15 images).

### Nouveaux assets (réutilisables)
- Décor **salon** complet (`Canape`, `Table_Appoint`, `Lampe` + `Lampe_Lumiere`, `Prise`, `Ciel`,
  `Soleil_Fenetre`, `Tapis`, `Plante_Salon`, `Tableau`).
- 3 cartons emboîtables à rabats animables (`Carton_Grand`, `Carton_Moyen`, `Carton_Petit`),
  flèche ↑ au feutre, scotch qui s'arrache (`Scotch_*`), papier bulle à 20 bulles (`Papier_Bulle`).
- **Bras élastiques** de Bip (fonction `bras(..., etire=…)` dans `animatique.py`).
- Sons : boum, scotch arraché, boing, pop de papier bulle, feulement, papier qui crisse.

## Production
- Temps passé : écriture … · animation … · son … · montage …
- Nouveaux assets créés (réutilisables) : …
- Problèmes / à améliorer la prochaine fois : …

## IA (traçabilité)
- Outils IA utilisés : …
- Part générée par IA (estimation) : modèles 3D … · animation … · sons … · musique … · plans vidéo …
- Étiquette IA activée : oui / non

## Publication
- Date : …
- Durée finale : … s (≥ 60 s ?)
- Monétisation : acceptée / refusée (motif : …)

## Résultats à J+7
- Vues : … · Visionnage complet : … % · Durée moyenne : … s
- Partages : … · Commentaires : … · Abonnés gagnés : …
- Part des vues hors France : … %
- Ce qu'on retient : …
