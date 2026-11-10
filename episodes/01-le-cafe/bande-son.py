"""
Épisode 01 — « Le café » : bande-son (bips, bruitages, musique), calée image par image
sur episodes/01-le-cafe/animatique.py (30 images/s).

    python episodes/01-le-cafe/bande-son.py  →  episodes/01-le-cafe/bande-son.wav
"""

import os
import sys

ICI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(ICI, "..", "..", "tools", "audio"))
import sons as S  # noqa: E402

FPS = 30
DUREE = 2250 / FPS  # 75 s


def t(image):
    return (image - 1) / FPS


p = S.Piste(DUREE)
cue = lambda image, son, vol=1.0: p.ajouter(son, t(image), vol)  # noqa: E731

# --- Musique : démarre à 0:04, se tait à 0:24 (regard caméra), s'emballe à 0:38,
#     coupée net à 0:50 (catastrophe), revient à 1:12 (lever de soleil).
def intensite(s):
    return 0.0 if s < t(1141) else min(1.0, (s - t(1141)) / (t(1500) - t(1141)))


musique = S.musique(DUREE, intensite=intensite)
env = S.np.ones(len(musique))
def couper(a, b, fondu=0.15):
    i, j, f = int(t(a) * S.SR), int(t(b) * S.SR), int(fondu * S.SR)
    env[i:j] = 0
    env[max(0, i - f):i] *= S.np.linspace(1, 0, min(f, i))
    env[j:j + f] *= S.np.linspace(0, 1, len(env[j:j + f]))
couper(1, 121, 0.01)
couper(721, 781)
couper(1501, 2161, 0.01)
env[-int(1.5 * S.SR):] *= S.np.linspace(1, 0, int(1.5 * S.SR))
p.ajouter(musique * env * 1.0, 0)

# --- 0:00 HOOK
cue(1, S.gresillement(0.8))
cue(8, S.vapeur(0.5, 0.15))
cue(14, S.triste())
# --- 0:02 retour en arrière
cue(61, S.retour_arriere(1.9), 0.7)
# --- 0:04 Bip s'allume
cue(128, S.boup_apaise(), 0.4)
cue(140, S.signature())
cue(143, S.ressort())
# --- 0:07 Mocha bâille
cue(222, S.baillement())
# --- 0:10 Bip comprend
cue(305, S.question())
cue(345, S.idee())
cue(348, S.ressort(400, 800, 0.1))
cue(385, S.determine())
# --- 0:14 tentative 1
cue(421, S.roule(1.7))
for f in (485, 505, 525, 545):
    cue(f, S.clic())
    cue(f + 4, S.bip(1000 + (f - 485) * 6, 0.05, 0.35))
cue(560, S.vapeur(1.1))
cue(563, S.panique(0.7))
cue(600, S.erreur())
cue(605, S.gresillement(0.9))
cue(675, S.boup_apaise(), 0.6)
# --- 0:24 regard caméra : silence total (timing comique)
# --- 0:26 tentative 2
cue(781, S.roule(0.6))
cue(800, S.determine())
cue(808, S.clic())
cue(812, S.glouglou(3.0))
cue(830, S.joie())
cue(918, S.surprise())
cue(945, S.idee())
cue(960, S.roule(1.4))
cue(1016, S.mrrp())
cue(1012, S.glissade(2.2), 0.55)
cue(1085, S.tres_joyeux())
cue(1102, S.miaou_indigne())
# --- 0:38 tentative 3
cue(1141, S.roule(0.4))
cue(1145, S.determine())
cue(1150, S.frottement(1.7))
cue(1214, S.clic())
cue(1225, S.glouglou(2.0, 0.35))
cue(1240, S.tres_joyeux())
cue(1300, S.surprise())
cue(1300, S.bulles_montantes(6.6, 0.3))
for i, f in enumerate(range(1330, 1495, 18)):
    cue(f, S.panique(0.45, 900 + i * 90), 0.8)
# --- 0:50 la catastrophe
cue(1501, S.bloop())
cue(1505, S.gresillement(1.2))
cue(1512, S.vapeur(0.5, 0.15))
# --- 0:55 Bip présente la tasse
cue(1660, S.frottement(2.0, 0.1))
cue(1660, S.roule(2.0, 0.08))
cue(1700, S.triste())
# --- 0:59 Mocha vide la tasse et s'installe dedans
cue(1800, S.frottement(0.5, 0.1))
cue(1815, S.plouf())
cue(1886, S.ressort(250, 500, 0.15))
cue(1912, S.plop())
cue(1925, S.ronronnement(t(2250) - t(1925), 0.45))
# --- 1:06 Bip comprend
cue(1990, S.question())
cue(2040, S.amour())
cue(2050, S.roule(1.3, 0.07))
cue(2120, S.boup_apaise())

sortie = os.path.join(ICI, "bande-son.wav")
p.ecrire(sortie)
print("Bande-son écrite :", sortie)
