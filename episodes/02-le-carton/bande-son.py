"""
Épisode 02 — « Le carton » : bande-son (bips, bruitages, musique), calée image par image
sur episodes/02-le-carton/animatique.py (30 images/s).

    python episodes/02-le-carton/bande-son.py  →  episodes/02-le-carton/bande-son.wav

La musique est à 120 bpm : un temps = 15 images, donc les « pop » du papier bulle
(toutes les 15 images à partir de 1816) tombent pile sur les temps.
"""

import os
import sys

ICI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(ICI, "..", "..", "tools", "audio"))
import sons as S  # noqa: E402

np = S.np
FPS = 30
DUREE = 2130 / FPS  # 71 s


def t(image):
    return (image - 1) / FPS


p = S.Piste(DUREE)
cue = lambda image, son, vol=1.0: p.ajouter(son, t(image), vol)  # noqa: E731


# --- Bruitages propres à l'épisode (synthétisés, comme toute la bibliothèque)
def boum(force=1.0):
    """Gros carton qui tombe : choc grave + carton qui vibre."""
    n = int(0.6 * S.SR)
    choc = S.glissando(110, 38, 0.6) * np.exp(-np.linspace(0, 6, n))
    carton = S.passe_bas(S.bruit(0.6), 0.12) * np.exp(-np.linspace(0, 9, n))
    carton /= np.max(np.abs(carton)) + 1e-9
    return force * 0.8 * (choc + 0.5 * carton)


def scotch(duree=0.45):
    """Ruban adhésif arraché : « SCRITCH » (craquements serrés qui accélèrent)."""
    x = S.silence(duree)
    temps, k = 0.0, 0
    while temps < duree - 0.01:
        c = S.passe_haut(S.bruit(0.006)) * S.enveloppe(int(0.006 * S.SR), 0.0005, 0.004)
        i = int(temps * S.SR)
        x[i:i + len(c)] += c[:len(x) - i] * (0.6 + 0.4 * np.sin(k))
        temps += 0.012 * (1 - 0.6 * temps / duree)
        k += 1
    return 0.6 * x / (np.max(np.abs(x)) + 1e-9) * S.enveloppe(len(x), 0.005, 0.08)


def tension(duree):
    """Le ruban qui résiste : grincement grave qui monte doucement."""
    x = S.glissando(160, 260, duree, "scie") * (1 + 0.3 * np.sin(2 * np.pi * 13 * S._t(duree)))
    return 0.07 * S.passe_bas(x, 0.2) * S.enveloppe(len(x), 0.3, 0.05)


def boing():
    d = 0.6
    f = 180 * (1 + 0.35 * np.sin(2 * np.pi * 14 * S._t(d)) * np.exp(-S._t(d) * 4))
    x = np.sin(2 * np.pi * np.cumsum(f) / S.SR) * np.exp(-S._t(d) * 5)
    return 0.55 * x


def bulle_pop(vol=0.7):
    """POP du papier bulle : claquement sec + petit « plip »."""
    clac = S.passe_haut(S.bruit(0.004)) * 0.9
    plip = S.glissando(2200, 700, 0.035) * np.exp(-np.linspace(0, 6, int(0.035 * S.SR)))
    return vol * S.suite(clac, 0.5 * plip)


def feulement():
    """Mocha souffle (court) : souffle aigu filtré."""
    x = S.passe_haut(S.bruit(0.55)) * S.enveloppe(int(0.55 * S.SR), 0.02, 0.3)
    return 0.3 * x / (np.max(np.abs(x)) + 1e-9)


def papier(duree=0.8):
    """Papier / carton qui crisse."""
    x = S.passe_haut(S.passe_bas(S.bruit(duree), 0.5)) * (0.5 + 0.5 * np.abs(np.sin(2 * np.pi * 9 * S._t(duree))))
    return 0.18 * x / (np.max(np.abs(x)) + 1e-9) * S.enveloppe(len(x), 0.02, 0.1)


def effort():
    return S.suite(S.bip(330, 0.06, 0.4), S.silence(0.03), S.bip(300, 0.08, 0.4))


def vexe():
    return S.suite(S.bip_glisse(700, 380, 0.18, 0.5), S.silence(0.05), S.non_non())


def etire(duree=0.8):
    """Bras (ou chat) qui s'étire : glissando montant élastique."""
    x = S.glissando(220, 700, duree) * (1 + 0.15 * np.sin(2 * np.pi * 10 * S._t(duree)))
    return 0.18 * x * S.enveloppe(len(x), 0.05, 0.1)


# --- Musique : boucle curieuse en pizzicatos, 120 bpm. Silence pendant la chute (hook) et
#     le regard caméra ; elle s'emballe pendant le duel ; fin musicale.
def intensite(s):
    if t(901) <= s < t(1261):
        return min(1.0, (s - t(901)) / (t(1200) - t(901)))
    if t(1801) <= s < t(1981):
        return 0.5
    return 0.0


musique = S.musique(DUREE, bpm=120, intensite=intensite, graine=11)
env = np.ones(len(musique))


def couper(a, b, fondu=0.15):
    i, j, f = int(t(a) * S.SR), int(t(b) * S.SR), int(fondu * S.SR)
    env[i:j] = 0
    env[max(0, i - f):i] *= np.linspace(1, 0, min(f, i))
    env[j:j + f] *= np.linspace(0, 1, len(env[j:j + f]))


couper(1, 61, 0.01)
couper(1261, 1278, 0.05)
couper(1981, 2071, 0.2)  # Mocha s'endort… POP
env[-int(1.2 * S.SR):] *= np.linspace(1, 0, int(1.2 * S.SR))
p.ajouter(musique * env * 0.85, 0)

# --- 0:00 HOOK : le carton tombe, BOUM, deux têtes
cue(1, S.glissando(900, 500, 0.55) * 0.08 * S.enveloppe(int(0.55 * S.SR), 0.3, 0.05))  # sifflement de chute
cue(18, boum())
cue(52, S.suite(S.bip(1500, 0.07, 0.5), S.silence(0.04), S.bip(1700, 0.06, 0.5)))
cue(64, S.mrrp())
# --- 0:04 Bip fait le tour du carton
cue(124, S.signature())
cue(150, S.roule(2.5, 0.1))
cue(200, S.question())
# --- 0:08 Mocha contemple le carton
cue(262, S.ronronnement(2.6, 0.13))
# --- 0:12 Bip tire sur le ruban
cue(371, S.roule(0.8, 0.1))
cue(398, S.determine())
cue(410, tension(6.2))
for f in range(430, 590, 32):
    cue(f, effort())
cue(540, vexe(), 0.6)
# --- 0:20 SCRITCH, Bip percute le canapé, BOING
cue(596, scotch())
cue(597, S.roule(0.35, 0.2))
cue(606, boing())
cue(607, S.erreur())
cue(609, papier(0.3))
cue(625, S.bip_glisse(900, 500, 0.9, 0.3, vibrato=0.25))
# --- 0:24 Mocha saute dans le carton
cue(745, S.ressort(400, 900, 0.08))
cue(764, S.plop(), 0.8)
cue(768, papier(0.4))
# --- 0:27 Bip découvre Mocha dedans
cue(842, S.surprise())
cue(860, vexe())
# --- 0:30 duel (×3) : Mocha s'étire… et glisse
for k, f0 in enumerate((925, 1035, 1145)):
    cue(f0 + 2, S.determine() if k < 2 else S.panique(0.6), 0.8)
    cue(f0 + 14, effort())
    cue(f0 + 16, etire(0.8 + 0.1 * k))
    cue(f0 + 44, S.glissade(0.4))
    cue(f0 + 50, S.plop(), 0.7)
    cue(f0 + 52, boum(0.25 + 0.15 * k))
cue(1240, S.triste())
# --- 0:42 REGARD (silence ½ s)
# --- 0:44 Bip a une idée, tire le rabat : le carton bascule, tout sort
cue(1336, S.idee())
cue(1340, S.ressort(400, 800, 0.1))
cue(1395, S.determine())
cue(1412, papier(0.6))
cue(1422, S.panique(0.6))
cue(1426, S.glissade(0.5))
cue(1432, boum(0.7))
cue(1434, S.frottement(0.6, 0.15))
cue(1442, S.surprise())
cue(1462, S.question())
cue(1478, S.pas(3, 0.2, 0.12))
cue(1495, S.mrrp(), 0.8)
# --- 0:50 le carton moyen → le petit → le papier bulle
cue(1532, papier(0.4))
cue(1540, S.surprise(), 0.8)
cue(1540, S.ressort(400, 900, 0.08))
cue(1558, S.plop(), 0.8)
cue(1566, S.question())
cue(1600, papier(0.4))
cue(1606, papier(0.8))
cue(1620, S.plop(), 0.5)
cue(1624, S.question())
# --- 0:56 déçu… POP !
cue(1690, S.triste())
cue(1731, bulle_pop())
cue(1732, S.surprise())
cue(1752, S.tres_joyeux())
cue(1780, bulle_pop())
# --- 1:00 pop-pop-pop en rythme
for k, f in enumerate(range(1816, 1980, 15)):
    cue(f, bulle_pop(0.65 + 0.1 * (k % 2)))
    if k % 4 == 3:
        cue(f + 3, S.bip(1600 + 100 * (k % 3), 0.05, 0.3))
# --- 1:06 Mocha s'endort… POP : sursaut, queue gonflée, il se cogne au carton
cue(1985, S.ronronnement(0.35, 0.1))
cue(1996, bulle_pop(0.8))
cue(1999, feulement())
cue(2003, boum(0.2))
# --- 1:09 Bip saute dans le petit carton, clin d'œil
cue(2077, S.ressort(400, 900, 0.08))
cue(2090, S.plop(), 0.8)
cue(2100, S.suite(S.bip(1200, 0.05, 0.4), S.silence(0.03), S.bip_glisse(1200, 1800, 0.12, 0.4)))

sortie = os.path.join(ICI, "bande-son.wav")
p.ecrire(sortie)
print("Bande-son écrite :", sortie)
