"""
Épisode 06 — « Le bouton rouge » : bande-son (bips, bruitages, musiques), calée image par image
sur episodes/06-le-bouton-rouge/animatique.py (30 images/s).

    python episodes/06-le-bouton-rouge/bande-son.py  →  episodes/06-le-bouton-rouge/bande-son.wav
"""

import os
import sys

ICI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(ICI, "..", "..", "tools", "audio"))
import sons as S  # noqa: E402

FPS = 30
DUREE = 1980 / FPS  # 66 s


def t(image):
    return (image - 1) / FPS


p = S.Piste(DUREE)
cue = lambda image, son, vol=1.0: p.ajouter(son, t(image), vol)  # noqa: E731


def morceau(son, debut, fin, vol=1.0, fondu=0.3):
    """Place un extrait de musique entre deux images, avec fondus."""
    n = int((t(fin) - t(debut)) * S.SR)
    x = son[:n].copy()
    f = min(int(fondu * S.SR), n // 2)
    x[:f] *= S.np.linspace(0, 1, f)
    x[-f:] *= S.np.linspace(1, 0, f)
    p.ajouter(x, t(debut), vol)


# --- Musiques : suspense (sauf pendant les silences), fête disco, puis plus rien.
suspense = S.musique_suspense(DUREE)
morceau(suspense, 1, 271, 0.9)
morceau(suspense[int(t(391) * S.SR):], 391, 1171, 0.9)
morceau(S.musique_disco(15.0), 1414, 1789, 0.9, fondu=0.02)

# --- 0:00 HOOK : la patte s'approche
cue(10, S.frottement(2.5, 0.06))
# --- 0:03 les Mains posent le boîtier, font « non » et s'en vont
cue(95, S.frottement(1.8, 0.08))
cue(150, S.plop(), 0.8)
cue(118, S.signature())
cue(130, S.question())
cue(268, S.pas(5, 0.3))
# --- 0:09 face au bouton : silence + tic-tac
cue(271, S.tictac(4.0, 60))
cue(282, S.bip(900, 0.05, 0.25))
cue(290, S.bip(900, 0.05, 0.25))
cue(298, S.bip(900, 0.05, 0.25))
# --- 0:13 fois 1
cue(400, S.frottement(2.2, 0.05))
cue(470, S.alarme())
cue(484, S.ressort())
cue(492, S.mrrp())
cue(545, S.determine())
# --- 0:20 « non » de Bip
cue(622, S.non_non())
cue(660, S.non_non())
# --- 0:24 fois 2 : Mocha pousse le boîtier vers le bord
cue(745, S.frottement(5.0, 0.12))
cue(800, S.question())
cue(860, S.surprise())
# --- 0:30 Bip le rattrape
cue(901, S.panique(0.8))
cue(912, S.roule(0.5, 0.15))
cue(925, S.ressort(500, 300, 0.1))
cue(990, S.joie())
cue(1000, S.boup_apaise())
# --- 0:35 Mocha abandonne
cue(1105, S.soupir())
cue(1130, S.frottement(1.0, 0.05))
# --- 0:39 Bip seul avec le bouton : le tic-tac accélère
cue(1171, S.tictac(7.1, 60, 170, 0.3))
cue(1260, S.question())
# --- 0:45 fois 3 : CLIC
cue(1384, S.gros_clic())
cue(1388, S.bip_glisse(900, 1500, 0.12, 0.35))
# --- 0:47 la fête
cue(1415, S.tres_joyeux())
cue(1500, S.joie(), 0.7)
# --- 0:53 l'aspirateur-robot
cue(1595, S.vrombissement(t(1789) - t(1595), 0.35))
cue(1600, S.surprise())
cue(1625, S.panique(1.3))
cue(1668, S.roule(1.7, 0.2))
# --- 0:57 Mocha appuie : tout s'arrête
cue(1789, S.gros_clic())
cue(1800, S.surprise(), 0.6)
cue(1840, S.question(), 0.6)
# --- 1:02 Mocha ouvre un œil
cue(1861, S.ronronnement(t(1980) - t(1861), 0.4))

sortie = os.path.join(ICI, "bande-son.wav")
p.ecrire(sortie)
print("Bande-son écrite :", sortie)
