#!/bin/bash
# Assemble les images PNG d'un rendu Blender et une bande-son en vidéo TikTok (MP4, 9:16).
#
#   tools/assembler-video.sh DOSSIER_IMAGES BANDE_SON.wav SORTIE.mp4 [LARGEUR]
#
# - DOSSIER_IMAGES : images numérotées 0001.png, 0002.png… (30 im/s)
# - LARGEUR : 1080 par défaut (la hauteur suit en 9:16). Les images plus petites sont agrandies.
# Un léger débruitage (hqdn3d) lisse le grain des rendus EEVEE à peu d'échantillons.
set -euo pipefail
images="$1"; son="$2"; sortie="$3"; largeur="${4:-1080}"
hauteur=$(( largeur * 16 / 9 ))
ffmpeg -y -loglevel error -stats \
  -framerate 30 -i "$images/%04d.png" -i "$son" \
  -vf "hqdn3d=3:3:4:4,scale=${largeur}:${hauteur}:flags=lanczos,format=yuv420p" \
  -c:v libx264 -preset slow -crf 20 -profile:v high -movflags +faststart \
  -c:a aac -b:a 192k -shortest "$sortie"
echo "Vidéo écrite : $sortie"
