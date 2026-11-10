"""
Bip & Mocha — prépare la sortie VIDÉO d'un épisode : MP4 vertical 1080 × 1920 avec la bande-son.

À lancer APRÈS le script d'animation de l'épisode (episodes/XX-…/animatique.py) :
- Dans Blender : Scripting → Ouvrir ce fichier → ▶, puis menu Render → Render Animation (Ctrl+F12).
- Sous Windows, en un clic : tools/rendre-episode.bat 06   (voir docs/10-rendu-sur-pc.md)

Ce que fait le script :
1. retrouve l'épisode ouvert (collection « Episode_XX ») et son dossier episodes/XX-… ;
2. fabrique la bande-son (bande-son.py → bande-son.wav) si elle n'existe pas encore ;
3. place le son dans le montage (Video Sequencer) de la scène ;
4. règle la sortie : MP4 (H.264 + AAC) → episodes/XX-…/rendu/episode-XX.mp4
"""

import glob
import os
import runpy
import sys

import bpy

DOSSIER_PROJET = r""  # à remplir seulement si le projet n'est pas trouvé automatiquement
TEMOIN = os.path.join("assets", "design", "bip-ecran-atlas.json")


def racine():
    cands = [DOSSIER_PROJET] if DOSSIER_PROJET else []
    cands += [os.path.dirname(os.path.abspath(bpy.path.abspath(t.filepath))) for t in bpy.data.texts if t.filepath]
    if "__file__" in globals():
        cands.append(os.path.dirname(os.path.abspath(__file__)))
    if bpy.data.filepath:
        cands.append(os.path.dirname(bpy.data.filepath))
    cands.append(os.getcwd())
    for c in cands:
        d = c
        for _ in range(6):
            if os.path.isfile(os.path.join(d, TEMOIN)):
                return d
            d = os.path.dirname(d)
    raise RuntimeError("Dossier du projet introuvable : renseigner DOSSIER_PROJET en haut du script.")


def episode_ouvert(r):
    noms = [c.name for c in bpy.data.collections if c.name.startswith("Episode_")]
    if not noms:
        raise RuntimeError("Aucun épisode dans la scène : lancer d'abord episodes/XX-…/animatique.py.")
    numero = noms[0].split("_")[1]
    dossiers = glob.glob(os.path.join(r, "episodes", f"{numero}-*"))
    if not dossiers:
        raise RuntimeError(f"Dossier episodes/{numero}-… introuvable.")
    return numero, dossiers[0]


def bande_son(dossier):
    wav = os.path.join(dossier, "bande-son.wav")
    if not os.path.isfile(wav):
        print("Fabrication de la bande-son (une minute environ)…")
        argv = sys.argv
        try:
            runpy.run_path(os.path.join(dossier, "bande-son.py"), run_name="__main__")
        finally:
            sys.argv = argv
    return wav


def ajouter_son(sc, wav):
    sc.sequence_editor_create()
    se = sc.sequence_editor
    pistes = se.strips if hasattr(se, "strips") else se.sequences  # Blender 5 : strips ; Blender 4 : sequences
    for s in list(pistes):
        if s.name == "Bande_Son":
            pistes.remove(s)
    son = pistes.new_sound("Bande_Son", wav, channel=1, frame_start=1)
    son.volume = 1.0
    return son


def sortie_mp4(sc, chemin):
    reglages = sc.render.image_settings
    if hasattr(reglages, "media_type"):  # Blender 5
        reglages.media_type = "VIDEO"
    reglages.file_format = "FFMPEG"
    f = sc.render.ffmpeg
    f.format = "MPEG4"
    f.codec = "H264"
    f.constant_rate_factor = "HIGH"
    f.ffmpeg_preset = "GOOD"
    f.gopsize = 30
    f.audio_codec = "AAC"
    f.audio_bitrate = 192
    f.audio_channels = "STEREO"
    f.audio_mixrate = 44100
    sc.render.filepath = chemin
    sc.render.use_file_extension = False
    sc.render.use_overwrite = True
    sc.render.use_placeholder = False


R = racine()
sc = bpy.context.scene
numero, dossier = episode_ouvert(R)
ajouter_son(sc, bande_son(dossier))
os.makedirs(os.path.join(dossier, "rendu"), exist_ok=True)
sortie = os.path.join(dossier, "rendu", f"episode-{numero}.mp4")
sortie_mp4(sc, sortie)
sc.render.resolution_percentage = 100
print(f"Épisode {numero} prêt pour la vidéo → {sortie}")
print("Blender : menu Render → Render Animation (Ctrl+F12).")
