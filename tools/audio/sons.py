"""
Bip & Mocha — bibliothèque de sons 100 % synthétisés (aucun échantillon externe,
donc aucun problème de droits). Nécessite numpy.

    import sons
    piste = sons.Piste(75.0)                   # une piste de 75 s
    piste.ajouter(sons.signature(), 4.6)       # le « bip-bip-boup » à 4,6 s
    piste.ecrire("bande-son.wav")

Lancer ce fichier directement génère un échantillon de chaque son dans
assets/sons/ (pour les écouter ou les réutiliser au montage) :
    python tools/audio/sons.py
"""

import os
import wave

import numpy as np

SR = 44100
_rng = np.random.default_rng(7)


# ---------------------------------------------------------------------------
# Briques de base
# ---------------------------------------------------------------------------
def _t(duree):
    return np.arange(int(duree * SR)) / SR


def enveloppe(n, attaque=0.005, relache=0.03):
    e = np.ones(n)
    a, r = min(int(attaque * SR), n), min(int(relache * SR), n)
    if a:
        e[:a] = np.linspace(0, 1, a)
    if r:
        e[-r:] *= np.linspace(1, 0, r)
    return e


def glissando(f0, f1, duree, forme="sinus", courbe="exp"):
    n = int(duree * SR)
    if courbe == "exp" and f0 > 0 and f1 > 0:
        f = f0 * (f1 / f0) ** np.linspace(0, 1, n)
    else:
        f = np.linspace(f0, f1, n)
    phase = 2 * np.pi * np.cumsum(f) / SR
    if forme == "sinus":
        return np.sin(phase)
    if forme == "carre":
        return np.tanh(4 * np.sin(phase)) * 0.6
    if forme == "triangle":
        return 2 / np.pi * np.arcsin(np.sin(phase))
    if forme == "scie":
        return 2 * ((phase / (2 * np.pi)) % 1) - 1
    raise ValueError(forme)


def silence(duree):
    return np.zeros(int(duree * SR))


def suite(*morceaux):
    return np.concatenate(morceaux)


def bruit(duree):
    return _rng.uniform(-1, 1, int(duree * SR))


def passe_bas(x, force=0.05):
    """Filtre passe-bas d'ordre 1 (force petite = plus sourd)."""
    y = np.empty_like(x)
    acc = 0.0
    for i, v in enumerate(x):
        acc += force * (v - acc)
        y[i] = acc
    return y


def passe_haut(x):
    return np.diff(x, prepend=0.0)


# ---------------------------------------------------------------------------
# La voix de Bip
# ---------------------------------------------------------------------------
def bip(freq=1200, duree=0.07, vol=0.5):
    """Un bip de robot : sinus + un peu de carré pour le timbre « électronique »."""
    x = 0.75 * glissando(freq, freq, duree) + 0.25 * glissando(freq, freq, duree, "carre")
    return vol * x * enveloppe(len(x), 0.003, 0.02)


def bip_glisse(f0, f1, duree, vol=0.5, vibrato=0.0):
    x = 0.8 * glissando(f0, f1, duree) + 0.2 * glissando(f0, f1, duree, "carre")
    if vibrato:
        x *= 1 + vibrato * np.sin(2 * np.pi * 7 * _t(duree))
    return vol * x * enveloppe(len(x), 0.005, 0.04)


def signature():
    """Le « bip-bip-boup » de Bip : la marque sonore de la chaîne."""
    return suite(bip(1320, 0.07), silence(0.045), bip(1320, 0.07), silence(0.06), bip_glisse(880, 520, 0.2, 0.55))


def joie():
    return suite(bip_glisse(700, 1400, 0.16), silence(0.02), bip(1650, 0.07))


def tres_joyeux():
    return suite(*[suite(bip(f, 0.06), silence(0.015)) for f in (1047, 1319, 1568, 2093)])


def triste():
    return bip_glisse(700, 330, 0.55, 0.45, vibrato=0.25)


def question():
    return suite(bip(700, 0.06), silence(0.03), bip_glisse(650, 1150, 0.22))


def idee():
    return suite(*[suite(bip(f, 0.055), silence(0.01)) for f in (880, 1109, 1319, 1760)])


def determine():
    return suite(bip(900, 0.05), silence(0.03), bip(1200, 0.09, 0.55))


def amour():
    return 0.8 * bip_glisse(900, 1250, 0.25, 0.45, vibrato=0.15)


def surprise():
    return suite(bip(1800, 0.04), silence(0.02), bip(2100, 0.06))


def panique(duree=0.9, base=1000):
    morceaux, t = [], 0.0
    while t < duree:
        f = base * _rng.uniform(0.9, 2.0)
        d = _rng.uniform(0.03, 0.06)
        morceaux += [bip(f, d, 0.4), silence(0.015)]
        t += d + 0.015
    return suite(*morceaux)


def erreur():
    buzz = glissando(180, 180, 0.22, "carre") * enveloppe(int(0.22 * SR))
    return 0.4 * suite(buzz, silence(0.06), buzz)


def boup_apaise():
    return bip_glisse(620, 310, 0.3, 0.35)


def gresillement(duree=0.6):
    n = int(duree * SR)
    porte = (np.repeat(_rng.random(n // 400 + 1) > 0.45, 400)[:n]).astype(float)
    return 0.3 * passe_haut(bruit(duree)) * porte * enveloppe(n, 0.01, 0.1)


def roule(duree=1.0, vol=0.12):
    """Le petit moteur de la roue de Bip."""
    t = _t(duree)
    x = glissando(110, 130, duree, "scie") * (1 + 0.3 * np.sin(2 * np.pi * 18 * t))
    return vol * passe_bas(x, 0.08) * enveloppe(len(t), 0.08, 0.15)


# ---------------------------------------------------------------------------
# Mocha (synthèse additive à « formants » : donne un timbre de voyelle)
# ---------------------------------------------------------------------------
def _voix_chat(f0_points, formant_points, duree, vol=0.35, souffle=0.05):
    n = int(duree * SR)
    xs = np.linspace(0, 1, n)
    f0 = np.interp(xs, np.linspace(0, 1, len(f0_points)), f0_points)
    fo = np.interp(xs, np.linspace(0, 1, len(formant_points)), formant_points)
    phase = 2 * np.pi * np.cumsum(f0) / SR
    x = np.zeros(n)
    for k in range(1, 18):
        poids = np.exp(-(((k * f0) - fo) / 450.0) ** 2) + 0.15 / k
        x += poids * np.sin(k * phase)
    x += souffle * passe_bas(bruit(duree), 0.3)
    x /= np.max(np.abs(x)) + 1e-9
    return vol * x * enveloppe(n, 0.04, 0.12)


def miaou_indigne():
    return _voix_chat([420, 520, 700, 650, 380], [500, 900, 1500, 1200, 600], 0.62, 0.4)


def mrrp():
    """Petit « mrrp ? » de surprise."""
    return _voix_chat([380, 450, 640], [400, 700, 1300], 0.22, 0.3)


def baillement():
    return _voix_chat([330, 300, 240, 200], [700, 1100, 800, 450], 0.9, 0.22, souffle=0.4)


def ronronnement(duree=4.0, vol=0.16):
    t = _t(duree)
    grain = passe_bas(bruit(duree), 0.02)
    battement = 0.5 + 0.5 * np.sign(np.sin(2 * np.pi * 26 * t))
    respiration = 0.55 + 0.45 * np.sin(2 * np.pi * t / 2.4) ** 2
    x = grain * battement * respiration
    x /= np.max(np.abs(x)) + 1e-9
    return vol * x * enveloppe(len(t), 0.4, 0.6)


# ---------------------------------------------------------------------------
# Bruitages
# ---------------------------------------------------------------------------
def clic():
    return 0.35 * suite(passe_haut(bruit(0.004)), 0.6 * bip(2400, 0.012, 1.0))


def vapeur(duree=0.9, vol=0.35):
    n = int(duree * SR)
    x = passe_haut(bruit(duree)) * enveloppe(n, 0.02, duree * 0.5)
    return vol * x / (np.max(np.abs(x)) + 1e-9)


def glouglou(duree=3.0, vol=0.3):
    piste = silence(duree)
    t = 0.0
    while t < duree - 0.1:
        b = glissando(_rng.uniform(250, 380), _rng.uniform(500, 750), 0.045) * enveloppe(int(0.045 * SR), 0.002, 0.02)
        i = int(t * SR)
        piste[i:i + len(b)] += b
        t += _rng.uniform(0.05, 0.13)
    return vol * piste


def bulles_montantes(duree=5.0, vol=0.25):
    """La mousse qui monte : bulles de plus en plus nombreuses et aiguës."""
    piste = silence(duree)
    t = 0.0
    while t < duree - 0.1:
        avance = t / duree
        f = 300 + 700 * avance
        b = glissando(f * _rng.uniform(0.8, 1.2), f * 1.8, 0.04) * enveloppe(int(0.04 * SR), 0.002, 0.02)
        i = int(t * SR)
        piste[i:i + len(b)] += b * (0.4 + 0.6 * avance)
        t += _rng.uniform(0.02, 0.12) * (1.2 - avance)
    return vol * piste


def bloop():
    x = glissando(420, 55, 0.55) * np.exp(-np.linspace(0, 5, int(0.55 * SR)))
    return 0.7 * suite(0.4 * passe_haut(bruit(0.01)), x)


def retour_arriere(duree=1.8):
    """Le « rewind » cartoon : glissements rapides vers le grave + souffle."""
    t = _t(duree)
    f = 1800 * (1 - 0.85 * (t / duree)) * (1 + 0.35 * np.sin(2 * np.pi * 9 * t))
    x = np.sin(2 * np.pi * np.cumsum(f) / SR) * 0.35 + 0.08 * passe_haut(bruit(duree))
    return 0.45 * x * enveloppe(len(t), 0.05, 0.2)


def frottement(duree=1.5, vol=0.12):
    t = _t(duree)
    x = passe_bas(bruit(duree), 0.15) * (0.6 + 0.4 * np.abs(np.sin(2 * np.pi * 3 * t)))
    return vol * x / (np.max(np.abs(x)) + 1e-9) * enveloppe(len(t), 0.05, 0.2)


def glissade(duree=1.2):
    """Sifflet à coulisse vers le grave (Mocha qui glisse)."""
    x = glissando(1100, 320, duree, courbe="lin") * (1 + 0.08 * np.sin(2 * np.pi * 6 * _t(duree)))
    return 0.25 * x * enveloppe(len(x), 0.03, 0.15)


def ressort(f0=300, f1=650, duree=0.12):
    return 0.3 * glissando(f0, f1, duree) * enveloppe(int(duree * SR), 0.005, 0.05)


def plouf():
    return 0.4 * suite(passe_bas(bruit(0.25), 0.2) * enveloppe(int(0.25 * SR), 0.005, 0.2), glouglou(0.4, 0.5))


def plop():
    return 0.45 * glissando(500, 160, 0.12) * enveloppe(int(0.12 * SR), 0.002, 0.08)


# ---------------------------------------------------------------------------
# Musique originale « Boucle du matin » (Do majeur, 96 bpm)
# ---------------------------------------------------------------------------
NOTES = {"C": 0, "D": 2, "E": 4, "F": 5, "G": 7, "A": 9, "B": 11}


def hz(note, octave):
    return 440.0 * 2 ** ((NOTES[note] + 12 * (octave + 1) - 69) / 12)


def pincee(freq, duree, vol=0.2):
    t = _t(duree)
    x = np.sin(2 * np.pi * freq * t) + 0.3 * np.sin(4 * np.pi * freq * t)
    return vol * x * np.exp(-t * 6) * enveloppe(len(t), 0.003, 0.02)


def musique(duree, bpm=96, intensite=None, graine=3):
    """intensite(t) -> 0..1 : ajoute des couches (arpèges rapides) quand ça s'emballe."""
    rng = np.random.default_rng(graine)
    piste = silence(duree + 1)
    temps = 60 / bpm
    accords = [("C", "E", "G"), ("A", "C", "E"), ("F", "A", "C"), ("G", "B", "D")]
    basses = ["C", "A", "F", "G"]
    gamme = [hz(n, o) for o, ns in ((5, "CDEGA"), (6, "CDE")) for n in ns]
    motif = [rng.integers(len(gamme)) if rng.random() < 0.55 else -1 for _ in range(16)]

    def poser(x, t):
        i = int(t * SR)
        if i < len(piste):
            piste[i:i + len(x)] += x[:len(piste) - i]

    mesure, t = 0, 0.0
    while t < duree:
        acc = accords[mesure % 4]
        # nappe douce
        for n in acc:
            x = glissando(hz(n, 4), hz(n, 4), 4 * temps, "triangle") * enveloppe(int(4 * temps * SR), 0.3, 0.4)
            poser(0.035 * x, t)
        # basse
        for b in (0, 2):
            poser(pincee(hz(basses[mesure % 4], 2), temps * 1.5, 0.28), t + b * temps)
        # mélodie (motif sur 2 mesures)
        for c in range(8):
            idx = motif[(mesure % 2) * 8 + c]
            if idx >= 0:
                poser(pincee(gamme[idx], temps, 0.11), t + c * temps / 2)
        # « shaker » léger
        for c in range(8):
            poser(0.025 * passe_haut(bruit(0.03)) * enveloppe(int(0.03 * SR), 0.001, 0.02), t + c * temps / 2)
        # arpèges rapides quand l'intensité monte
        for c in range(16):
            tc = t + c * temps / 4
            k = intensite(tc) if intensite else 0
            if k > 0.05:
                n = acc[c % 3]
                poser(pincee(hz(n, 6 if c % 4 else 5), temps / 2, 0.09 * k), tc)
        mesure += 1
        t += 4 * temps
    return piste[: int(duree * SR)]


# ---------------------------------------------------------------------------
# Piste de mixage
# ---------------------------------------------------------------------------
class Piste:
    def __init__(self, duree):
        self.x = silence(duree)

    def ajouter(self, son, t, vol=1.0):
        i = int(t * SR)
        if i >= len(self.x):
            return
        fin = min(len(self.x), i + len(son))
        self.x[i:fin] += vol * son[: fin - i]

    def ecrire(self, chemin, crete=0.89):
        x = self.x / (np.max(np.abs(self.x)) + 1e-9) * crete
        stereo = np.repeat((x * 32767).astype(np.int16)[:, None], 2, axis=1)
        with wave.open(chemin, "wb") as w:
            w.setnchannels(2)
            w.setsampwidth(2)
            w.setframerate(SR)
            w.writeframes(stereo.tobytes())


if __name__ == "__main__":
    dossier = os.path.join(os.path.dirname(__file__), "..", "..", "assets", "sons")
    os.makedirs(dossier, exist_ok=True)
    catalogue = {
        "bip-signature": signature(), "bip-joie": joie(), "bip-tres-joyeux": tres_joyeux(), "bip-triste": triste(),
        "bip-question": question(), "bip-idee": idee(), "bip-determine": determine(), "bip-amour": amour(),
        "bip-surprise": surprise(), "bip-panique": panique(), "bip-erreur": erreur(), "bip-veille": boup_apaise(),
        "bip-gresillement": gresillement(), "bip-roule": roule(1.5, 0.4),
        "mocha-miaou-indigne": miaou_indigne(), "mocha-mrrp": mrrp(), "mocha-baillement": baillement(),
        "mocha-ronronnement": ronronnement(4.0, 0.5),
        "bruit-clic": clic(), "bruit-vapeur": vapeur(), "bruit-glouglou": glouglou(2.0), "bruit-bulles": bulles_montantes(3.0),
        "bruit-bloop": bloop(), "bruit-retour-arriere": retour_arriere(), "bruit-frottement": frottement(),
        "bruit-glissade": glissade(), "bruit-ressort": ressort(), "bruit-plouf": plouf(), "bruit-plop": plop(),
        "musique-boucle-du-matin": musique(10.0),
    }
    for nom, son in catalogue.items():
        p = Piste(len(son) / SR + 0.05)
        p.ajouter(son, 0)
        p.ecrire(os.path.join(dossier, nom + ".wav"))
    print(f"{len(catalogue)} sons écrits dans {os.path.normpath(dossier)}")
