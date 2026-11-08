"""
Épisode 06 — « Le bouton rouge » : animatique 3D (66 s, 30 im/s, 9:16).

Il y a un bouton rouge. On n'y touche pas. La 3e fois, c'est Bip qui craque.
Construit la scène (personnages + cuisine + accessoires), anime l'épisode d'après
episodes/06-le-bouton-rouge/script.md et pose les changements de caméra.

Dans Blender : onglet Scripting → Ouvrir ce fichier → ▶
En ligne de commande :
    blender -b --python episodes/06-le-bouton-rouge/animatique.py -- --rendu DOSSIER [--debut 1 --fin 1980]
    (autres options : voir ligne_de_commande() dans tools/blender/outils_animation.py)
"""

import math
import os
import runpy
import types
import warnings

import bpy

warnings.filterwarnings("ignore", category=DeprecationWarning)

# ---------------------------------------------------------------------------
# Localisation du projet (même logique que tools/blender/preparer-scene.py)
# ---------------------------------------------------------------------------
DOSSIER_PROJET = r""
TEMOIN = os.path.join("assets", "design", "bip-ecran-atlas.json")


def racine():
    cands = [DOSSIER_PROJET] if DOSSIER_PROJET else []
    cands += [os.path.dirname(os.path.abspath(bpy.path.abspath(t.filepath))) for t in bpy.data.texts if t.filepath]
    if "__file__" in globals():
        cands.append(os.path.dirname(os.path.abspath(__file__)))
    cands.append(os.getcwd())
    for c in cands:
        d = c
        for _ in range(6):
            if os.path.isfile(os.path.join(d, TEMOIN)):
                return d
            d = os.path.dirname(d)
    raise RuntimeError("Dossier du projet introuvable : renseigner DOSSIER_PROJET en haut du script.")


RACINE = racine()
OUTILS = os.path.join(RACINE, "tools", "blender")

# ---------------------------------------------------------------------------
# Scène de base : personnages + cuisine
# ---------------------------------------------------------------------------
if bpy.app.background:
    bpy.ops.wm.read_factory_settings(use_empty=True)
elif "Cube" in bpy.data.objects:
    bpy.data.objects.remove(bpy.data.objects["Cube"], do_unlink=True)
runpy.run_path(os.path.join(OUTILS, "preparer-scene.py"), init_globals={"DEMO": False})
K = runpy.run_path(os.path.join(OUTILS, "decor-cuisine.py"))["construire_cuisine"]()
A = types.SimpleNamespace(**runpy.run_path(os.path.join(OUTILS, "outils_animation.py")))

sc = bpy.context.scene
FIN = 1980  # 66 s
sc.render.fps = A.FPS
sc.frame_start, sc.frame_end = 1, FIN
D = bpy.data.objects
for nom in ("CAM_LARGE", "CAM_BIP", "CAM_MOCHA", "Viseur_Large"):
    if nom in D:
        D.remove(D[nom], do_unlink=True)
for nom in ("Ref_Bip", "Ref_Mocha"):
    if nom in D:
        D[nom].hide_viewport = D[nom].hide_render = True
coll_ep = bpy.data.collections.new("Episode_06")
sc.collection.children.link(coll_ep)
A.initialiser(coll_ep)

bip, corps_bip, mocha = D["Bip"], D["Bip_Corps"], D["Mocha"]
K["tasse"].location = (-0.72, 0.2, 0)  # la tasse XXL de l'épisode 01 est rangée à côté de la machine
cle, pos, rot, rotz, ech, expr, saut = A.cle, A.pos, A.rot, A.rotz, A.ech, A.expr, A.saut

# Articulations : épaules de Bip, épaule avant droite de Mocha (pour tendre la patte)
epaule = {
    "D": A.pivot("Bip_Epaule_D", [D["Bip_Bras_D"], D["Bip_Main_D"]], (0.095, 0, 0.17), bip),
    "G": A.pivot("Bip_Epaule_G", [D["Bip_Bras_G"], D["Bip_Main_G"]], (-0.095, 0, 0.17), bip),
}
m_pelage = D["Mocha_Corps"].data.materials[0]
jambe = A.sphere("Mocha_Jambe_D", 1.0, (0, 0, 0), m_pelage, ech=(0.022, 0.022, 0.085))
jambe.parent = mocha
jambe.location = (0.045, -0.065, 0.11)
epaule_mocha = A.pivot("Mocha_Epaule_D", [jambe, D["Mocha_Patte_D"]], (0.045, -0.06, 0.2), mocha)


def bras(f, cote, x=0, y=0):
    """Bras de Bip : x < 0 = vers l'avant, y = sur le côté (signe selon le côté)."""
    rot(epaule[cote], f, x=x, y=y)


def patte(f, angle):
    """Patte avant de Mocha : 0 = posée, -55 = tendue vers l'avant."""
    rot(epaule_mocha, f, x=angle)


# ---------------------------------------------------------------------------
# Accessoires
# ---------------------------------------------------------------------------
m_boitier = A.mat("Boitier", "#3A3F4B", 0.5)
m_rouge = A.mat("Bouton_Rouge", "#E8302A", 0.25, emission=0.3)
m_peau = A.mat("Mains_Peau", "#E0AC86", 0.6)
m_manche = A.mat("Mains_Manche", "#5B7DB1", 0.8)
m_chrome = A.mat("Disco_Chrome", "#E8ECF2", 0.08)
m_chrome.node_tree.nodes["Principled BSDF"].inputs["Metallic"].default_value = 1.0
m_aspi = A.mat("Aspirateur", "#2E3440", 0.4)
m_aspi_led = A.mat("Aspirateur_Led", "#4FD1FF", 0.3, emission=4.0)
m_aspi_bord = A.mat("Aspirateur_Bord", "#9AA3B0", 0.3)

# Boîtier : son origine est l'arête AVANT du bas (il bascule autour d'elle au bord du plan de travail)
boitier = A.vide("Boitier")
corps_boitier = A.boite("Boitier_Corps", (0.13, 0.1, 0.045), (0, 0.05, 0.0225), m_boitier, boitier, 0.008)
A.contour(corps_boitier, 0.004)
socle_bouton = A.cylindre("Bouton_Socle", 0.042, 0.008, (0, 0.05, 0.049), m_boitier, boitier)
bouton = A.vide("Bouton", (0, 0.05, 0.05), boitier)  # pivot en bas : on l'écrase pour « appuyer »
dome = A.cylindre("Bouton_Dome", 0.034, 0.022, (0, 0, 0.011), m_rouge, bouton)
A.contour(dome, 0.003)
BOITIER_0 = (0.045, -0.17, 0)  # bouton au centre en (0.045, -0.12)


def appui(f):
    cle(bouton, "scale", f, (1, 1, 1))
    cle(bouton, "scale", f + 2, (1, 1, 0.35))
    cle(bouton, "scale", f + 8, (1, 1, 1))


def lueur(f, force):
    entree = m_rouge.node_tree.nodes["Principled BSDF"].inputs["Emission Strength"]
    entree.default_value = force
    entree.keyframe_insert("default_value", frame=f)


# Les Mains (l'humain, jamais vu en entier) — deux poses : « porte » et « doigt levé »
def main_porte():
    r = A.vide("Main_Porte")
    paume = A.sphere("Main_Porte_Paume", 1.0, (0, 0.01, 0.0), m_peau, r, (0.055, 0.065, 0.022))
    for i, x in enumerate((-0.036, -0.012, 0.012, 0.036)):
        A.cylindre(f"Main_Porte_Doigt_{i}", 0.009, 0.06, (x, -0.06, -0.025), m_peau, r, rot=(math.radians(20), 0, 0), sommets=12)
    manche = A.cylindre("Main_Porte_Manche", 0.045, 1.4, (0, 0.33, 0.62), m_manche, r, rot=(math.radians(-25), 0, 0))
    for o in (paume, manche):
        A.contour(o, 0.004)
    return r


def main_doigt():
    r = A.vide("Main_Doigt")  # origine au poignet
    poing = A.sphere("Main_Doigt_Poing", 1.0, (0, 0, 0.045), m_peau, r, (0.042, 0.032, 0.045))
    A.cylindre("Main_Doigt_Index", 0.009, 0.07, (0.012, -0.01, 0.11), m_peau, r, sommets=12)
    A.sphere("Main_Doigt_Bout", 0.009, (0.012, -0.01, 0.145), m_peau, r, seg=12)
    A.sphere("Main_Doigt_Pouce", 1.0, (-0.035, -0.015, 0.06), m_peau, r, (0.012, 0.012, 0.022), seg=12)
    manche = A.cylindre("Main_Doigt_Manche", 0.045, 1.4, (0, 0, -0.7), m_manche, r)
    for o in (poing, manche):
        A.contour(o, 0.004)
    return r


porte, doigt = main_porte(), main_doigt()

# Boule à facettes + lumières colorées pour la fête
boule = A.sphere("Boule_Disco", 0.055, (0, 0, 0), m_chrome, seg=12)
for p in boule.data.polygons:
    p.use_smooth = False  # facettes !
A.cylindre("Boule_Disco_Fil", 0.002, 1.0, (0, 0, 0.55), m_boitier, boule, sommets=6)
LUMIERES_DISCO = []
for i, (couleur, loc) in enumerate((("#FF3EA5", (-0.5, -0.7, 0.8)), ("#3EE0FF", (0.5, -0.7, 0.8)),
                                     ("#FFD23E", (0.0, -0.4, 1.0)))):
    ld = bpy.data.lights.new(f"Disco_{i}", "POINT")
    ld.color = A.lin(couleur)[:3]
    ld.shadow_soft_size = 0.05
    lo = bpy.data.objects.new(f"Disco_{i}", ld)
    lo.location = loc
    coll_ep.objects.link(lo)
    LUMIERES_DISCO.append(ld)

# Aspirateur-robot (vu dans l'épisode 03)
aspi = A.vide("Aspirateur")
corps_aspi = A.cylindre("Aspirateur_Corps", 0.11, 0.05, (0, 0, 0.03), m_aspi, aspi, sommets=48)
A.contour(corps_aspi, 0.004)
A.cylindre("Aspirateur_Bord", 0.112, 0.012, (0, 0, 0.012), m_aspi_bord, aspi, sommets=48)
A.cylindre("Aspirateur_Capteur", 0.03, 0.02, (0, 0.02, 0.06), m_aspi_bord, aspi)
A.sphere("Aspirateur_Led", 0.012, (-0.06, -0.06, 0.055), m_aspi_led, aspi, seg=12)

# ---------------------------------------------------------------------------
# Lumière de la cuisine (mêmes réglages que l'épisode 01) + états « normal » / « fête »
# ---------------------------------------------------------------------------
fond = sc.world.node_tree.nodes["Background"].inputs["Strength"]
douce, contre, soleil = D["Lumiere_Douce"].data, D["Contre_Jour"].data, D["Soleil"].data


def eclairage(f, fete):
    fond.default_value = 0.15 if fete else 0.45
    fond.keyframe_insert("default_value", frame=f)
    for lampe, normal, ambiance in ((douce, 22, 5), (contre, 10, 3), (soleil, 1.6, 0.3)):
        A.cle(lampe, "energy", f, ambiance if fete else normal)


def disco(f1, f2, temps=15):
    """Une lumière colorée par temps (120 bpm = 15 images)."""
    for ld in LUMIERES_DISCO:
        A.cle(ld, "energy", f1 - 1, 0.0)
    k = 0
    for f in range(f1, f2, temps):
        for i, ld in enumerate(LUMIERES_DISCO):
            A.cle(ld, "energy", f, 90.0 if i == k % 3 else 8.0)
            A.cle(ld, "energy", f + temps - 2, 30.0 if i == k % 3 else 8.0)
        k += 1
    for ld in LUMIERES_DISCO:
        A.cle(ld, "energy", f2, 0.0)


# ---------------------------------------------------------------------------
# Caméras et plans
# ---------------------------------------------------------------------------
viseur = A.vide("Viseur_Large", (-0.075, 0.1, 0.3))
cible_duo = A.vide("Viseur_Duo", (-0.09, 0.0, 0.16))
CAM = {
    "LARGE": A.camera("CAM_LARGE", (-0.075, -2.1, 0.45), 45, viseur),
    "DUO": A.camera("CAM_DUO", (-0.05, -0.95, 0.13), 28, cible_duo),
    "BOUTON": A.camera("CAM_BOUTON", (0.06, -0.48, 0.14), 50, dome),
    "ACCROCHE": A.camera("CAM_ACCROCHE", (0.07, -0.62, 0.17), 35, A.vide("Viseur_Accroche", (0.03, -0.04, 0.16))),
    "BIP": A.camera("CAM_BIP", (0.05, -0.75, 0.16), 50, corps_bip, suivre=bip),
    "MOCHA": A.camera("CAM_MOCHA", (-0.08, -0.85, 0.3), 55, D["Mocha_Tete"], suivre=mocha),
}
A.plans([
    (1, "ACCROCHE"), (91, "LARGE"), (271, "DUO"), (391, "DUO"), (601, "BIP"), (721, "LARGE"),
    (901, "BIP"), (1051, "MOCHA"), (1171, "BIP"), (1351, "BOUTON"), (1411, "LARGE"), (1861, "MOCHA"),
], CAM)

# ---------------------------------------------------------------------------
# ANIMATION — plan par plan (repères : script.md)
# ---------------------------------------------------------------------------
BIP_0 = (-0.22, -0.1, 0)
MOCHA_0 = (0.0, 0.1, 0)        # derrière le boîtier : sa patte tombe pile sur le bouton
DODO = (0.27, -0.075, 0)      # là où Mocha va dormir, à portée de patte du bouton
BIP_SEUL = (-0.12, -0.12, 0)  # Bip à côté du boîtier, le bras droit au-dessus du bouton

# Valeurs de départ
eclairage(1, False)
for ld in LUMIERES_DISCO:
    A.cle(ld, "energy", 1, 0.0)
lueur(1, 0.3)
cle(bouton, "scale", 1, (1, 1, 1))
for c in ("D", "G"):
    bras(1, c)
patte(1, 0)
A.yeux_mocha(1, "mi-clos")
cle(boule, "location", 1, (0.0, -0.05, 1.6))
cle(aspi, "location", 1, (1.2, -0.3, 0))
cle(porte, "location", 1, (0.045, -0.12, 1.8))
cle(doigt, "location", 1, (0.12, -0.45, -0.7))
rot(doigt, 1, 0, 0, 0)

# 0:00 HOOK — gros plan sur le bouton rouge ; une patte de chat s'approche lentement…
cle(boitier, "location", 1, BOITIER_0)
cle(mocha, "location", 1, MOCHA_0)
rot(mocha, 1, 0, 0, 0)
cle(bip, "location", 1, BIP_0)
rotz(bip, 1, 30)
expr(1, "veille", clignement=False)
rot(mocha, 30, x=-6)
patte(15, 0)
patte(88, -52)
lueur(60, 1.2)

# 0:03 LES MAINS posent le boîtier et font « non » du doigt (retour en arrière de quelques secondes)
saut(boitier, "location", 91, BOITIER_0, (0.045, -0.17, 1.2))
patte(90, -52)
patte(91, 0)
rot(mocha, 90, x=-6)
rot(mocha, 91, x=0)
lueur(90, 1.2)
lueur(91, 0.3)
cle(porte, "location", 91, (0.045, -0.12, 1.2 + 0.085))
cle(boitier, "location", 150, BOITIER_0)
cle(porte, "location", 150, (0.045, -0.12, 0.085))
cle(porte, "location", 160, (0.045, -0.12, 0.085))
cle(porte, "location", 185, (0.045, -0.05, 1.8))
expr(100, "neutre")
expr(118, "question")
A.saute(bip, 118, 0.03, 10)
cle(doigt, "location", 180, (0.12, -0.45, -0.7))
cle(doigt, "location", 198, (0.12, -0.45, 0.3))
for i, f in enumerate(range(200, 250, 8)):
    rot(doigt, f, y=18 if i % 2 == 0 else -18)
rot(doigt, 250, y=0)
cle(doigt, "location", 250, (0.12, -0.45, 0.3))
cle(doigt, "location", 268, (0.12, -0.45, -0.7))
rotz(bip, 200, 15)
rotz(mocha, 200, 10)

# 0:09 Bip et Mocha fixent le bouton. Silence, tic-tac.
rotz(bip, 271, 35)
rotz(mocha, 271, 0)
expr(280, "chargement")
A.yeux_mocha(300, "mi-clos")
A.yeux_mocha(330, "ouverts")
A.yeux_mocha(345, "mi-clos")
lueur(271, 0.3)
lueur(330, 1.5)
lueur(380, 0.3)

# 0:13 FOIS 1 — Mocha tend la patte… Bip bondit et la repousse
patte(395, 0)
rot(mocha, 395, x=0)
rot(mocha, 440, x=-6)
patte(470, -52)
expr(470, "exclamation", clignement=False)
pos(bip, 470, *BIP_0)
pos(bip, 476, -0.2, -0.1, 0)
pos(bip, 486, -0.1, -0.12, 0.06)
pos(bip, 494, -0.08, -0.13, 0)
rotz(bip, 476, 35)
rotz(bip, 486, 60)
bras(470, "D")
bras(484, "D", x=-60, y=-60)
bras(492, "D", x=-80, y=-70)
patte(486, -52)
patte(492, -15)
patte(505, 0)
rot(mocha, 486, x=-6)
rot(mocha, 494, x=6)
rot(mocha, 520, x=0)
A.yeux_mocha(486, "mi-clos")
A.yeux_mocha(490, "ouverts")
A.yeux_mocha(530, "mi-clos")
bras(530, "D", x=-80, y=-70)
bras(545, "D")
expr(545, "determine")
pos(bip, 560, -0.08, -0.13, 0)
pos(bip, 590, *BIP_0)
rotz(bip, 590, 20)

# 0:20 Bip fait « non » avec son bras, comme les Mains
rotz(bip, 601, 10)
bras(605, "D")
bras(618, "D", x=-20, y=-150)
for i, f in enumerate(range(624, 690, 8)):
    bras(f, "D", x=-20, y=-130 if i % 2 == 0 else -170)
bras(690, "D", x=-20, y=-150)
bras(705, "D")

# 0:24 FOIS 2 — Mocha pousse lentement le boîtier vers le bord (comme un verre)
pos(mocha, 721, *MOCHA_0)
cle(boitier, "location", 735, BOITIER_0)
patte(735, -50)
rot(mocha, 735, x=-6)
pos(mocha, 745, *MOCHA_0)
for f, y in ((790, -0.24), (840, -0.31), (880, -0.355), (896, -0.37)):
    cle(boitier, "location", f, (BOITIER_0[0], y, 0))
    pos(mocha, f, 0.0, y + 0.27, 0)
rot(boitier, 880, x=0)
rot(boitier, 898, x=-22)
rotz(bip, 721, 30)
expr(800, "question")
expr(860, "surprise")

# 0:30 Bip le rattrape au dernier moment, soulagé
patte(905, -50)
patte(915, 0)
rot(mocha, 915, x=0)
expr(901, "panique", clignement=False)
pos(bip, 901, *BIP_0)
rotz(bip, 901, 30)
pos(bip, 925, -0.06, -0.27, 0)
rotz(bip, 925, 75)
for c in ("D", "G"):
    bras(915, c)
bras(925, "D", x=-80)
bras(925, "G", x=-80)
rot(boitier, 918, x=-22)
rot(boitier, 932, x=0)
cle(boitier, "location", 928, (BOITIER_0[0], -0.37, 0))
cle(boitier, "location", 990, (BOITIER_0[0], -0.25, 0))
pos(bip, 990, -0.06, -0.15, 0)
cle(boitier, "location", 1035, BOITIER_0)
pos(bip, 1035, -0.08, -0.06, 0)
pos(bip, 1048, -0.4, -0.04, 0)  # Bip recule : le plan « regard » est pour Mocha
expr(990, "joie")
bras(1000, "D", x=-80)
bras(1000, "G", x=-80)
bras(1015, "D")
bras(1015, "G")
rotz(bip, 1040, 20)

# 0:35 REGARD — Mocha regarde l'objectif. Il abandonne et va se coucher.
pos(mocha, 1051, 0.0, -0.1, 0)
rotz(mocha, 1051, -15)
rotz(mocha, 1060, 0)
A.yeux_mocha(1080, "mi-clos")
A.yeux_mocha(1105, "fermes")
cle(mocha, "scale", 1105, (1, 1, 1))
cle(mocha, "scale", 1115, (1.03, 1.03, 0.95))
cle(mocha, "scale", 1125, (1, 1, 1))
A.yeux_mocha(1125, "mi-clos")
pos(mocha, 1128, 0.0, -0.1, 0)
rotz(mocha, 1128, 0)
rotz(mocha, 1140, -90)
pos(mocha, 1162, *DODO)
A.yeux_mocha(1162, "fermes")

# 0:39 Bip est seul avec le bouton. Il le fixe. Le bouton semble briller.
pos(bip, 1171, *BIP_SEUL)
rotz(bip, 1171, 0)
expr(1180, "chargement")
for i, f in enumerate(range(1180, 1345, 20)):
    lueur(f, 0.4)
    lueur(f + 10, 0.8 + 0.35 * i)
expr(1260, "question")
rotz(bip, 1290, 0)
rotz(bip, 1320, 25)
rotz(bip, 1345, 0)

# 0:45 FOIS 3 — un tout petit doigt de Bip… CLIC
bras(1355, "D")
bras(1378, "D", y=-12)
bras(1384, "D", y=-24)  # la main tombe pile sur le dôme du bouton
ech(bip, 1378, 1, 1, 1)
ech(bip, 1384, 1, 1, 0.85)
appui(1384)
lueur(1384, 4.0)
expr(1386, "clin-oeil", clignement=False)
bras(1395, "D", y=-24)
bras(1405, "D")
ech(bip, 1395, 1, 1, 0.85)
ech(bip, 1405, 1, 1, 1)

# 0:47 LUMIÈRES DISCO, musique de fête ! Bip danse.
eclairage(1410, False)
eclairage(1414, True)
disco(1414, 1790)
cle(boule, "location", 1412, (0.0, -0.05, 1.6))
cle(boule, "location", 1430, (0.0, -0.05, 0.72))
rot(boule, 1412, z=0)
rot(boule, 1790, z=720)
expr(1415, "tres-joyeux")
pos(bip, 1411, *BIP_SEUL)
pos(bip, 1430, -0.2, -0.1, 0)
for i, f in enumerate(range(1430, 1590, 15)):
    rotz(bip, f, 25 if i % 2 == 0 else -25)
    bras(f, "D", y=-150 if i % 2 == 0 else -40)
    bras(f, "G", y=40 if i % 2 == 0 else 150)
    if i % 2 == 0:
        A.saute(bip, f, 0.035, 10)
A.yeux_mocha(1440, "fermes")

# 0:53 L'aspirateur-robot fonce vers Bip
cle(aspi, "location", 1595, (1.2, -0.3, 0))
cle(aspi, "location", 1650, (0.15, -0.3, 0))
rotz(aspi, 1595, 0)
rotz(aspi, 1650, 200)
expr(1600, "surprise", clignement=False)
rotz(bip, 1600, 0)
bras(1600, "D")
bras(1600, "G")
expr(1625, "panique", clignement=False)
A.tremblement(bip, 1625, 1665, 0.006)

# 0:57 Bip s'enfuit. Mocha, sans ouvrir les yeux, tend la patte… CLIC : tout s'arrête.
pos(bip, 1668, -0.2, -0.1, 0)
rotz(bip, 1668, 0)
rotz(bip, 1676, -90)
pos(bip, 1720, -0.95, -0.15, 0)
cle(aspi, "location", 1700, (-0.1, -0.3, 0))
cle(aspi, "location", 1790, (-0.42, -0.3, 0))
rotz(aspi, 1790, 380)
patte(1750, 0)
patte(1785, -55)
appui(1789)
lueur(1789, 4.0)
lueur(1795, 0.3)
eclairage(1789, True)
eclairage(1791, False)
cle(boule, "location", 1792, (0.0, -0.05, 0.72))
cle(boule, "location", 1830, (0.0, -0.05, 1.6))
patte(1800, -55)
patte(1825, 0)
pos(bip, 1792, -0.95, -0.15, 0)
rotz(bip, 1792, -90)
pos(bip, 1800, -0.6, -0.15, 0)
rotz(bip, 1800, -20)
expr(1800, "surprise")
expr(1840, "question")

# 1:02 REGARD — Mocha ouvre un œil vers l'objectif
pos(mocha, 1861, *DODO)
rotz(mocha, 1860, -90)
rotz(mocha, 1861, -35)
A.yeux_mocha(1861, "fermes")
A.yeux_mocha(1900, "fermes", cote="D")
A.yeux_mocha(1906, "mi-clos", cote="D")
A.yeux_mocha(1950, "mi-clos", cote="D")
A.yeux_mocha(1956, "fermes", cote="D")

A.finir_expressions()

# La « jambe » de Mocha n'apparaît que quand la patte est tendue (au repos, elle se verrait devant le ventre)
fc = next(c for c in A.courbes(epaule_mocha) if c.data_path == "rotation_euler" and c.array_index == 0)
etat = None
for f in range(1, FIN + 1):
    tendue = abs(fc.evaluate(f)) > math.radians(4)
    if tendue != etat:
        A.visible(jambe, f, tendue)
        etat = tendue

print("Épisode 06 : scène animée prête.")
A.ligne_de_commande()
