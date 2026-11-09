"""
Épisode 02 — « Le carton » : animatique 3D (71 s, 30 im/s, 9:16).

Bip veut ce qu'il y a dans le colis, Mocha veut le carton. Dedans… un autre carton.
Construit la scène (personnages + salon + cartons + papier bulle), anime l'épisode d'après
episodes/02-le-carton/script.md et pose les changements de caméra.

Dans Blender : onglet Scripting → Ouvrir ce fichier → ▶
En ligne de commande :
    blender -b --python episodes/02-le-carton/animatique.py -- --rendu DOSSIER [--debut 1 --fin 2130]
    (autres options : voir ligne_de_commande() dans tools/blender/outils_animation.py)
"""

import math
import os
import runpy
import types
import warnings

import bpy
import bmesh  # après bpy (module bpy hors de Blender)

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
# Scène de base : personnages + salon
# ---------------------------------------------------------------------------
if bpy.app.background:
    bpy.ops.wm.read_factory_settings(use_empty=True)
elif "Cube" in bpy.data.objects:
    bpy.data.objects.remove(bpy.data.objects["Cube"], do_unlink=True)
runpy.run_path(os.path.join(OUTILS, "preparer-scene.py"), init_globals={"DEMO": False})
SALON = runpy.run_path(os.path.join(OUTILS, "decor-salon.py"))["construire_salon"]()
A = types.SimpleNamespace(**runpy.run_path(os.path.join(OUTILS, "outils_animation.py")))
ST = runpy.run_path(os.path.join(OUTILS, "style-studio.py"))

sc = bpy.context.scene
FIN = 2130  # 71 s
sc.render.fps = A.FPS
sc.frame_start, sc.frame_end = 1, FIN
D = bpy.data.objects
for nom in ("CAM_LARGE", "CAM_BIP", "CAM_MOCHA", "Viseur_Large"):
    if nom in D:
        D.remove(D[nom], do_unlink=True)
for nom in ("Ref_Bip", "Ref_Mocha"):
    if nom in D:
        D[nom].hide_viewport = D[nom].hide_render = True
coll_ep = bpy.data.collections.new("Episode_02")
sc.collection.children.link(coll_ep)
A.initialiser(coll_ep)

bip, corps_bip, mocha = D["Bip"], D["Bip_Corps"], D["Mocha"]
cle, pos, rot, rotz, ech, expr, saut = A.cle, A.pos, A.rot, A.rotz, A.ech, A.expr, A.saut

# ---------------------------------------------------------------------------
# Bras de Bip : épaules + bras ÉLASTIQUES (le pivot s'allonge, la main garde sa forme)
# ---------------------------------------------------------------------------
EX, EY, EZ = bip.get("epaule", (0.095, 0, 0.17))
epaule = {
    "D": A.pivot("Bip_Epaule_D", [D["Bip_Bras_D"], D["Bip_Main_D"]], (EX, EY, EZ), bip),
    "G": A.pivot("Bip_Epaule_G", [D["Bip_Bras_G"], D["Bip_Main_G"]], (-EX, EY, EZ), bip),
}
ECH_MAIN = tuple(D["Bip_Main_D"].scale)


def bras(f, cote, x=0, y=0, etire=1.0):
    """x < 0 = vers l'avant (-90 = à l'horizontale, -180 = en l'air) ; etire = longueur du bras (1 = normal)."""
    cotes = ("D", "G") if cote == "DG" else (cote,)
    for c in cotes:
        rot(epaule[c], f, x=x, y=y if c == "D" else -y)
        cle(epaule[c], "scale", f, (1, 1, etire))
        cle(D[f"Bip_Main_{c}"], "scale", f, (ECH_MAIN[0], ECH_MAIN[1], ECH_MAIN[2] / etire))
        for nom in (f"Bip_Epaulette_{c}", f"Bip_Bracelet_{c}"):
            if nom in D:
                cle(D[nom], "scale", f, (1, 1, 1 / etire))


# ---------------------------------------------------------------------------
# Accessoires : 3 cartons emboîtables (sans inscription : ruban + flèche ↑), scotch, papier bulle
# ---------------------------------------------------------------------------
m_carton = ST["regler"]("Carton", "#C99A62", 0.78)
ST["platre"](m_carton)  # léger grain de fibre
m_scotch = ST["regler"]("Scotch", "#D9B57A", 0.22, vernis=0.7, vernis_rug=0.05)
m_feutre = ST["regler"]("Feutre", "#3A2E26", 0.6)
m_bulle = ST["regler"]("Papier_Bulle", "#E8F3F6", 0.08, vernis=1.0, vernis_rug=0.02)
_tr = m_bulle.node_tree.nodes["Principled BSDF"].inputs.get("Transmission Weight")
if _tr is not None:
    _tr.default_value = 0.75
OUVERT = 235  # angle d'un rabat ouvert (il retombe le long de la paroi)


def _parois(nom, L, P, H, parent):
    """Boîte sans couvercle (5 faces) avec épaisseur."""
    me = bpy.data.meshes.new(nom)
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    for v in bm.verts:
        v.co.x, v.co.y, v.co.z = v.co.x * L, v.co.y * P, v.co.z * H + H / 2
    bmesh.ops.delete(bm, geom=[f for f in bm.faces if f.normal.z > 0.9], context="FACES_ONLY")
    bm.to_mesh(me)
    bm.free()
    o = bpy.data.objects.new(nom, me)
    A.ranger(o)
    o.parent = parent
    me.materials.append(m_carton)
    ep = o.modifiers.new("Epaisseur", "SOLIDIFY")
    ep.thickness, ep.offset = 0.005, -1
    ST["biseau"](o, 0.0015)
    return o


def carton(nom, L, P, H, fleche=True):
    """Carton : origine au centre du fond. Renvoie {racine, rabats=[(pivot, axe, angle ouvert)]}."""
    r = A.vide(nom)
    _parois(nom + "_Parois", L, P, H, r)
    rabats = []
    e = 0.004
    for cote, (px, py), axe, signe in (("Avant", (0, -P / 2), "x", 1), ("Arriere", (0, P / 2), "x", -1)):
        p = A.vide(f"{nom}_Rabat_{cote}", (px, py, H + 0.003), r)
        A.boite(f"{nom}_Rabat_{cote}_Forme", (L - 0.004, P / 2 - 0.004, e), (0, signe * P / 4, e / 2), m_carton, p)
        rabats.append((p, axe, signe * OUVERT))
    l = P / 2 * 0.9
    for cote, px, signe in (("Droit", L / 2, 1), ("Gauche", -L / 2, -1)):
        p = A.vide(f"{nom}_Rabat_{cote}", (px, 0, H - 0.001), r)
        A.boite(f"{nom}_Rabat_{cote}_Forme", (l, P - 0.008, e), (-signe * l / 2, 0, -e / 2), m_carton, p)
        rabats.append((p, "y", signe * OUVERT))
    if fleche:  # flèche « ↑ » dessinée au feutre sur la face avant (pas de texte)
        f = A.vide(f"{nom}_Fleche", (L * 0.28, -P / 2 - 0.0012, H * 0.5), r)
        h = H * 0.32
        A.boite(f"{nom}_Fleche_Tige", (h * 0.07, 0.001, h), (0, 0, 0), m_feutre, f)
        for i, s in enumerate((-1, 1)):
            b = A.boite(f"{nom}_Fleche_Pointe_{i}", (h * 0.07, 0.001, h * 0.4), (s * h * 0.11, 0, h * 0.37), m_feutre, f)
            b.rotation_euler = (0, math.radians(-s * 40), 0)
    for p, axe, ang in rabats:
        rot(p, 1, x=0, y=0)
    return {"racine": r, "rabats": rabats, "dims": (L, P, H)}


def ouvrir(c, f, duree=7, ressort=True):
    """Les rabats s'ouvrent d'un coup (avec un petit rebond)."""
    for i, (p, axe, ang) in enumerate(c["rabats"]):
        d = f + (0 if i < 2 else 2)
        rot(p, d, **{axe: 0})
        rot(p, d + duree, **{axe: ang * (1.06 if ressort else 1)})
        rot(p, d + duree + 5, **{axe: ang})


C0 = (-0.1, 0.12)  # place du grand carton
L, P, H = 0.46, 0.38, 0.30
bascule = A.vide("Carton_Bascule", (C0[0], C0[1] - P / 2, 1.7))  # arête avant du fond : il bascule autour
GRAND = carton("Carton_Grand", L, P, H)
GRAND["racine"].parent = bascule
GRAND["racine"].location = (0, P / 2, 0)
MOYEN = carton("Carton_Moyen", 0.26, 0.22, 0.2)
PETIT = carton("Carton_Petit", 0.16, 0.13, 0.1, fleche=False)
# Scotch du grand carton : descend sur la face droite, traverse le dessus, redescend à gauche
hs = 0.18
scotch_d = A.vide("Scotch_D", (L / 2 + 0.0015, 0, H), GRAND["racine"])
A.boite("Scotch_D_Forme", (0.002, 0.055, hs), (0, 0, -hs / 2), m_scotch, scotch_d)
scotch_h = A.vide("Scotch_Haut", (-L / 2, 0, H + 0.0075), GRAND["racine"])
A.boite("Scotch_Haut_Forme", (L, 0.055, 0.0015), (L / 2, 0, 0), m_scotch, scotch_h)
scotch_g = A.vide("Scotch_G", (-L / 2 - 0.0015, 0, H), GRAND["racine"])
A.boite("Scotch_G_Forme", (0.002, 0.055, hs), (0, 0, -hs / 2), m_scotch, scotch_g)
# Partie arrachée : un ruban qui va du point de décollage jusqu'à la main de Bip (contrainte « Stretch To »)
contact = A.vide("Scotch_Contact", (C0[0] + L / 2 + 0.002, C0[1], H - hs))
me = bpy.data.meshes.new("Scotch_Tire")
bm = bmesh.new()
bmesh.ops.create_cube(bm, size=1.0)
for v in bm.verts:
    v.co.x, v.co.y, v.co.z = v.co.x * 0.055, v.co.y + 0.5, v.co.z * 0.0015
bm.to_mesh(me)
bm.free()
tire = bpy.data.objects.new("Scotch_Tire", me)
A.ranger(tire)
me.materials.append(m_scotch)
c1 = tire.constraints.new("COPY_LOCATION")
c1.target = contact
c2 = tire.constraints.new("STRETCH_TO")
c2.target, c2.rest_length, c2.volume = D["Bip_Main_D"], 1.0, "NO_VOLUME"
boule_scotch = A.sphere("Scotch_Boule", 0.016, (0, 0, 0), m_scotch, D["Bip_Main_D"], ech=(1, 1, 1))
boule_scotch.parent = D["Bip_Main_D"]
boule_scotch.location = (0, 0, -0.005)
boule_scotch.scale = (1 / ECH_MAIN[0], 1 / ECH_MAIN[1], 1 / ECH_MAIN[2])

# Papier bulle : feuille + 5 × 4 bulles (elles éclatent une à une)
bulle_r = A.vide("Papier_Bulle")
A.boite("Papier_Bulle_Feuille", (0.2, 0.15, 0.0015), (0, 0, 0.001), m_bulle, bulle_r)
BULLES = []
for j in range(4):
    for i in range(5):
        b = A.sphere(f"Bulle_{j}_{i}", 0.0125, ((i - 2) * 0.036, (j - 1.5) * 0.034, 0.002), m_bulle, bulle_r,
                     ech=(1, 1, 0.8), seg=16)
        BULLES.append(b)
ORDRE_BULLES = [BULLES[k] for k in (2, 7, 12, 1, 8, 13, 6, 3, 11, 16, 9, 17, 0, 14, 5, 18, 4, 15, 10, 19)]
_bulles = iter(ORDRE_BULLES)


def pop(f):
    """Une bulle éclate (elle s'aplatit et disparaît)."""
    b = next(_bulles)
    cle(b, "scale", f - 1, (1, 1, 0.8))
    cle(b, "scale", f + 1, (1.25, 1.25, 0.05))
    cle(b, "scale", f + 2, (0, 0, 0))


# ---------------------------------------------------------------------------
# Lumière d'après-midi
# ---------------------------------------------------------------------------
sc.world.node_tree.nodes["Background"].inputs["Strength"].default_value = 0.45
D["Lumiere_Douce"].data.energy = 22
D["Contre_Jour"].data.energy = 10
D["Soleil"].data.energy = 1.4

# ---------------------------------------------------------------------------
# Caméras et plans
# ---------------------------------------------------------------------------
CAM = {
    "PLONGEE": A.camera("CAM_PLONGEE", (C0[0], C0[1] - 0.5, 2.3), 45, A.vide("Viseur_Plongee", (C0[0], C0[1], 0.1))),
    "LARGE": A.camera("CAM_LARGE", (0.04, -2.05, 0.62), 42, A.vide("Viseur_Large", (0.04, 0.3, 0.3))),
    "AVANT": A.camera("CAM_LARGE_AVANT", (0.15, -2.55, 0.55), 40, A.vide("Viseur_Avant", (0.13, -0.45, 0.18))),
    "BIP": A.camera("CAM_BIP", (0.05, -0.75, 0.16), 50, corps_bip, suivre=bip),
    "MOCHA": A.camera("CAM_MOCHA", (-0.08, -0.85, 0.3), 55, D["Mocha_Tete"], suivre=mocha),
    "REGARD": A.camera("CAM_REGARD", (C0[0], C0[1] - 0.85, 0.42), 55, D["Mocha_Tete"]),
}
A.plans([
    (1, "PLONGEE"), (121, "BIP"), (241, "MOCHA"), (361, "LARGE"), (721, "MOCHA"), (811, "BIP"), (901, "LARGE"),
    (1261, "REGARD"), (1321, "BIP"), (1381, "AVANT"), (1681, "BIP"), (1801, "AVANT"), (1981, "MOCHA"),
    (2071, "AVANT"),
], CAM)

# ---------------------------------------------------------------------------
# ANIMATION — plan par plan (repères : script.md)
# ---------------------------------------------------------------------------
GX, GY = C0
# Valeurs de départ
bras(1, "DG")
expr(1, "neutre", clignement=False)
A.yeux_mocha(1, "mi-clos")
for o in (contact, scotch_d, scotch_h, scotch_g, mocha, bip, bascule, GRAND["racine"], MOYEN["racine"],
          PETIT["racine"], bulle_r, D["Mocha_Queue"], D["Canape"]):
    cle(o, "scale", 1, tuple(o.scale))
cle(contact, "location", 1, tuple(contact.location))
rot(bascule, 1, 0, 0, 0)
A.visible(tire, 1, False)
A.visible(boule_scotch, 1, False)
for c, loc in ((MOYEN, (GX, GY, 0.006)), (PETIT, (0.06, -0.7, 0.006)), ):
    cle(c["racine"], "location", 1, loc)
    rot(c["racine"], 1, 0, 0, 0)
cle(bulle_r, "location", 1, (0.47, -0.78, 0.01))
rot(bulle_r, 1, 0, 0, 0)
for o in [MOYEN["racine"], PETIT["racine"], bulle_r]:
    for enfant in o.children_recursive:
        if enfant.type == "MESH":
            A.visible(enfant, 1, False)


def montrer(racine, f):
    for enfant in racine.children_recursive:
        if enfant.type == "MESH":
            A.visible(enfant, f, True)


# 0:00 HOOK (plongée) — un énorme carton tombe au milieu du salon, BOUM. Deux têtes surgissent de chaque côté.
for f, z in ((1, 1.7), (10, 1.23), (15, 0.56), (18, 0.0)):
    cle(bascule, "location", f, (GX, GY - P / 2, z))
for fc in A.courbes(bascule):  # chute libre : pas de ralenti avant l'impact
    for k in fc.keyframe_points:
        k.interpolation = "LINEAR"
g = GRAND["racine"]
cle(g, "scale", 18, (1, 1, 1))
cle(g, "scale", 19, (1.1, 1.1, 0.82))
cle(g, "scale", 23, (0.96, 0.96, 1.06))
cle(g, "scale", 28, (1, 1, 1))
pos(bip, 1, GX + 0.8, GY, 0)
rotz(bip, 1, -90)
pos(bip, 40, GX + 0.8, GY, 0)
pos(bip, 50, GX + 0.36, GY, 0)
expr(50, "exclamation", clignement=False)
pos(mocha, 1, GX - 0.85, GY, 0)
rotz(mocha, 1, 90)
pos(mocha, 46, GX - 0.85, GY, 0)
pos(mocha, 58, GX - 0.38, GY, 0)
A.yeux_mocha(56, "mi-clos", regard=(0.8, 0))
A.yeux_mocha(62, "ouverts", regard=(0.8, 0))
A.yeux_mocha(110, "ouverts", regard=(0.8, 0))
A.yeux_mocha(118, "mi-clos")

# 0:04 BIP — bip-bip-boup, Bip fait le tour du carton (il regarde dans le sens de la marche)
expr(124, "joie")
A.saute(bip, 126, 0.03, 10)
for f, a in ((150, 0), (175, -25), (200, -50), (225, -70)):
    pos(bip, f, GX + 0.36 * math.cos(math.radians(a)), GY + 0.36 * math.sin(math.radians(a)), 0)
    rotz(bip, f, a)
rotz(bip, 150, -90)
rotz(bip, 160, 0)
rotz(bip, 240, -40)
expr(200, "question")
# … pendant ce temps, Mocha va s'asseoir devant
pos(mocha, 140, GX - 0.38, GY, 0)
rotz(mocha, 140, 90)
pos(mocha, 215, -0.3, -0.3, 0)
rotz(mocha, 180, 160)
rotz(mocha, 225, 20)

# 0:08 MOCHA — assis devant le carton, il le contemple (ronron court)
A.yeux_mocha(241, "mi-clos", regard=(0.5, 0.3))
A.yeux_mocha(265, "attendri", regard=(0.6, 0.4))
rot(mocha, 265, y=0)
rot(mocha, 285, y=-6)  # tête penchée
rot(mocha, 330, y=-6)
rot(mocha, 345, y=0)
A.yeux_mocha(345, "attendri", regard=(0.6, 0.4))
A.yeux_mocha(355, "mi-clos", regard=(0.6, 0.2))

# 0:12 LARGE — Bip tire sur le ruban adhésif… ses petits bras s'étirent… s'étirent…
pos(bip, 370, GX + 0.123, GY - 0.338, 0)
pos(bip, 395, 0.21, GY, 0)
rotz(bip, 370, -40)
rotz(bip, 395, -90)
expr(398, "determine")
bras(395, "DG")
bras(405, "DG", x=-95, etire=1.2)
for f, x in ((450, 0.27), (500, 0.32), (550, 0.37), (595, 0.42)):
    pos(bip, f, x, GY, 0)
    bras(f, "DG", x=-95, etire=(x - 0.13) / 0.066)
for i, f in enumerate(range(410, 596, 6)):
    rot(bip, f, x=-10 if i % 2 else -15)  # il tire de toutes ses forces
A.visible(tire, 405, True)
cle(contact, "location", 595, tuple(contact.location))
expr(540, "colere")
A.yeux_mocha(400, "mi-clos", regard=(0.9, 0.2))
A.yeux_mocha(560, "content", regard=(0.9, 0.2))

# 0:20 Le ruban lâche (SCRITCH), Bip part en arrière en roulant et percute le canapé (BOING)
haut_d = (GX + L / 2 + 0.002, GY, H)
cle(contact, "location", 598, haut_d)
cle(contact, "location", 606, (GX - L / 2, GY, H + 0.008))
cle(scotch_d, "scale", 595, (1, 1, 1))
cle(scotch_d, "scale", 598, (1, 1, 0.001))
cle(scotch_h, "scale", 598, (1, 1, 1))
cle(scotch_h, "scale", 606, (0.001, 1, 1))
A.visible(tire, 607, False)
A.visible(scotch_g, 607, False)
A.visible(boule_scotch, 607, True)
A.visible(boule_scotch, 700, False)
ouvrir(GRAND, 608, 8)
bras(600, "DG", x=-95, etire=1.0)
bras(604, "DG")
pos(bip, 596, 0.42, GY, 0)
pos(bip, 606, 0.5, 0.49, 0)
rot(bip, 596, x=-15, z=-90)
rot(bip, 606, x=0, z=270)  # un tour sur lui-même
ech(bip, 606, 1)
ech(bip, 607, 1.15, 1.15, 0.8)
ech(bip, 611, 0.92, 0.92, 1.1)
ech(bip, 616, 1)
expr(607, "erreur", clignement=False)
canape = D["Canape"]
cle(canape, "scale", 606, (1, 1, 1))
cle(canape, "scale", 609, (1, 0.97, 0.99))
cle(canape, "scale", 613, (1, 1.01, 1))
cle(canape, "scale", 617, (1, 1, 1))
pos(bip, 612, 0.47, 0.4, 0.035)
pos(bip, 620, 0.45, 0.33, 0)
for i, f in enumerate(range(622, 690, 8)):  # étourdi
    rot(bip, f, y=8 if i % 2 else -8)
rot(bip, 690, y=0)
A.yeux_mocha(600, "ouverts", regard=(0.9, 0.5))
A.yeux_mocha(640, "content", regard=(0.6, 0.6))  # le carton est ouvert…
A.yeux_mocha(700, "content", regard=(0.4, 0.4))
expr(690, "neutre")

# 0:24 MOCHA — il en profite et saute dans le carton ouvert (hop)
pos(mocha, 721, -0.3, -0.3, 0)
rotz(mocha, 721, 20)
rotz(mocha, 732, 45)
cle(mocha, "scale", 736, (1, 1, 1))
cle(mocha, "scale", 742, (1.08, 1.08, 0.88))
pos(mocha, 742, -0.3, -0.3, 0)
cle(mocha, "scale", 747, (0.94, 0.94, 1.12))
pos(mocha, 754, -0.2, -0.06, 0.46)
pos(mocha, 764, GX, GY, 0.02)
rotz(mocha, 764, 0)
cle(mocha, "scale", 764, (1, 1, 1))
cle(mocha, "scale", 766, (1.08, 1.08, 0.9))
cle(mocha, "scale", 772, (1, 1, 1))
A.yeux_mocha(742, "ouverts", regard=(0.4, 0.3))
A.yeux_mocha(770, "content")
A.yeux_mocha(805, "content")

# 0:27 BIP — Bip revient… et découvre Mocha dedans. Vexé.
pos(bip, 815, 0.45, 0.33, 0)
rotz(bip, 815, 270)
pos(bip, 840, 0.26, 0.0, 0)
rotz(bip, 840, 290)
expr(842, "surprise")
expr(860, "colere")
A.saute(bip, 868, 0.025, 8)

# 0:30 LARGE — DUEL : Bip essaie de sortir Mocha, qui devient « liquide » et glisse entre ses bras (3 fois)
pos(bip, 905, 0.26, 0.0, 0)
pos(bip, 920, 0.25, GY, 0)
rotz(bip, 905, 290)
rotz(bip, 920, 270)
pos(mocha, 925, GX, GY, 0.02)
A.yeux_mocha(925, "mi-clos")
for k, f0 in enumerate((925, 1035, 1145)):
    montee = (0.12, 0.17, 0.24)[k]
    expr(f0, "determine" if k < 2 else "panique", clignement=k == 0)
    bras(f0, "DG")
    bras(f0 + 10, "DG", x=-133, etire=5.2)  # les mains sur les joues de Mocha
    pos(bip, f0 + 14, 0.25, GY, 0)
    rot(bip, f0 + 14, x=0)
    pos(mocha, f0 + 14, GX, GY, 0.02)
    cle(mocha, "scale", f0 + 14, (1, 1, 1))
    bras(f0 + 40, "DG", x=(-130, -135, -140)[k], etire=(7.7, 8.8, 10.4)[k])
    pos(bip, f0 + 40, 0.29, GY, 0)
    rot(bip, f0 + 40, x=-15)
    pos(mocha, f0 + 40, GX, GY, 0.02 + montee)
    cle(mocha, "scale", f0 + 40, (0.8 - 0.05 * k, 0.8 - 0.05 * k, 1.3 + 0.15 * k))
    A.yeux_mocha(f0 + 36, "content")
    # … et il glisse !
    bras(f0 + 44, "DG", x=-120, etire=1.0)
    bras(f0 + 50, "DG")
    pos(mocha, f0 + 47, GX, GY, 0.02)
    cle(mocha, "scale", f0 + 48, (1.22, 1.22, 0.76))
    cle(mocha, "scale", f0 + 56, (1, 1, 1))
    A.yeux_mocha(f0 + 50, "mi-clos")
    pos(bip, f0 + 52, 0.36, GY, 0)
    rot(bip, f0 + 52, x=-35 if k < 2 else -88)
    if k < 2:
        pos(bip, f0 + 75, 0.25, GY, 0)
        rot(bip, f0 + 75, x=0)
pos(bip, 1235, 0.36, GY, 0)
rot(bip, 1235, x=-88)
pos(bip, 1255, 0.27, GY, 0)
rot(bip, 1255, x=0)
expr(1240, "triste")

# 0:42 REGARD — Mocha, confortablement installé, regarde l'objectif (silence ½ s)
A.yeux_mocha(1261, "content", regard=(0, 0))
A.yeux_mocha(1288, "content", regard=(0, 0))
A.yeux_mocha(1292, "fermes")
A.yeux_mocha(1297, "content", regard=(0, 0))

# 0:44 BIP — Bip a une idée…
rotz(bip, 1321, 270)
rotz(bip, 1330, 340)
expr(1336, "idee")
A.saute(bip, 1338, 0.03, 10)

# 0:46 … il tire le rabat avant : le carton bascule, tout sort, dont… un carton moyen
pos(bip, 1381, 0.27, GY, 0)
rotz(bip, 1381, 340)
pos(bip, 1395, 0.22, -0.32, 0)
pos(bip, 1405, -0.05, -0.5, 0)
rotz(bip, 1405, 180)
expr(1395, "determine")
bras(1405, "DG")
bras(1412, "DG", x=-104, etire=4.7)
pos(bip, 1420, -0.05, -0.58, 0)
bras(1420, "DG", x=-100, etire=5.6)
expr(1422, "panique", clignement=False)
bras(1424, "DG", x=-90, etire=1.0)
bras(1428, "DG")
pos(bip, 1424, -0.02, -0.6, 0)
pos(bip, 1432, 0.38, -0.5, 0)
rotz(bip, 1424, 180)
rotz(bip, 1432, 120)
avant = GRAND["rabats"][0][0]
rot(avant, 1418, x=OUVERT)
rot(avant, 1432, x=92)
for f, a in ((1412, 0), (1420, 8), (1424, 20), (1428, 55), (1432, 90), (1435, 84), (1438, 90)):
    rot(bascule, f, x=a)
cle(g, "scale", 1432, (1, 1, 1))
cle(g, "scale", 1433, (1.04, 1.04, 0.95))
cle(g, "scale", 1438, (1, 1, 1))
# Mocha est « versé » dehors comme un liquide… puis se reforme, imperturbable
BORD_Y = GY - P / 2  # arête avant du fond du grand carton
pos(mocha, 1420, GX, GY, 0.02)
rot(mocha, 1420, x=0)
pos(mocha, 1424, GX, BORD_Y + 0.172, 0.084)
rot(mocha, 1424, x=20)
pos(mocha, 1428, GX, BORD_Y + 0.093, 0.167)
rot(mocha, 1428, x=55)
pos(mocha, 1432, GX, BORD_Y - 0.02, 0.19)
rot(mocha, 1432, x=90)
cle(mocha, "scale", 1428, (1, 1, 1))
cle(mocha, "scale", 1432, (0.9, 0.9, 1.2))
pos(mocha, 1437, -0.25, -0.58, 0)
rot(mocha, 1437, x=0)
cle(mocha, "scale", 1437, (1.35, 1.35, 0.45))
cle(mocha, "scale", 1446, (0.95, 0.95, 1.08))
cle(mocha, "scale", 1452, (1, 1, 1))
A.yeux_mocha(1420, "mi-clos")
A.yeux_mocha(1450, "mi-clos")
# Le carton moyen glisse dehors
montrer(MOYEN["racine"], 1432)
m = MOYEN["racine"]
cle(m, "location", 1431, (GX, GY, 0.006))
cle(m, "location", 1432, (GX, -0.42, 0))
rotz(m, 1432, 0)
cle(m, "location", 1446, (0.06, -0.7, 0))
rotz(m, 1446, 25)
expr(1442, "surprise")
expr(1462, "question")
rotz(bip, 1450, 120)
rotz(bip, 1465, 100)
# Mocha retourne dans le grand carton (couché, il fait une « grotte ») et s'y installe en boule
pos(mocha, 1455, -0.25, -0.58, 0)
rotz(mocha, 1455, 0)
rotz(mocha, 1462, 170)
pos(mocha, 1475, -0.12, -0.45, 0)
pos(mocha, 1490, GX, -0.22, 0.006)
rotz(mocha, 1490, 200)
rotz(mocha, 1500, 360)
cle(mocha, "scale", 1490, (1, 1, 1))
cle(mocha, "scale", 1498, (1.06, 1.06, 0.78))
A.yeux_mocha(1500, "content")

# 0:50 LARGE — Bip ouvre le carton moyen : un petit carton. Il ouvre le petit : du papier bulle.
pos(bip, 1505, 0.38, -0.5, 0)
pos(bip, 1520, 0.3, -0.6, 0)
rotz(bip, 1520, 293)
bras(1520, "DG")
bras(1530, "DG", x=-80, etire=1.6)
bras(1538, "DG")
ouvrir(MOYEN, 1532, 6)
montrer(PETIT["racine"], 1538)
p_ = PETIT["racine"]
cle(p_, "location", 1537, (0.06, -0.7, 0.05))
cle(p_, "location", 1548, (0.28, -0.76, 0.32))
cle(p_, "location", 1558, (0.47, -0.78, 0))
cle(p_, "scale", 1558, (1, 1, 1))
cle(p_, "scale", 1560, (1.1, 1.1, 0.85))
cle(p_, "scale", 1565, (1, 1, 1))
expr(1540, "surprise", clignement=False)
expr(1566, "question")
pos(bip, 1570, 0.3, -0.6, 0)
pos(bip, 1585, 0.3, -0.64, 0)
rotz(bip, 1570, 293)
rotz(bip, 1585, 410)  # se tourne vers le petit carton
bras(1590, "DG")
bras(1598, "DG", x=-70, etire=1.4)
bras(1606, "DG")
ouvrir(PETIT, 1600, 5)
montrer(bulle_r, 1604)
cle(bulle_r, "location", 1603, (0.47, -0.78, 0.06))
cle(bulle_r, "location", 1612, (0.4, -0.84, 0.25))
cle(bulle_r, "location", 1620, (0.3, -0.86, 0.004))
rot(bulle_r, 1603, 0, 0, 0)
rot(bulle_r, 1612, x=30, z=20)
rot(bulle_r, 1620, 0, 0, 10)
rotz(bip, 1630, 360)
expr(1624, "question")
A.yeux_mocha(1540, "content", regard=(0.8, -0.3))
A.yeux_mocha(1600, "content", regard=(0.9, -0.4))

# 0:56 BIP — déçu… il touche le papier bulle. POP.
expr(1690, "triste")
bras(1720, "D")
bras(1728, "D", x=-60, etire=2.4)
pop(1731)
expr(1732, "surprise", clignement=False)
bras(1736, "D")
expr(1752, "tres-joyeux")
A.saute(bip, 1754, 0.03, 10)
bras(1772, "G")
bras(1777, "G", x=-60, etire=2.4)
pop(1780)
bras(1785, "G")

# 1:00 LARGE — chacun son bonheur : Mocha dans le grand carton, Bip éclate des bulles en rythme (120 bpm)
for k, f in enumerate(range(1816, 1980, 15)):
    c = "D" if k % 2 == 0 else "G"
    bras(f - 5, c)
    bras(f - 1, c, x=-60, etire=2.4)
    pop(f)
    bras(f + 5, c)
    if k % 4 == 3:
        A.saute(bip, f + 3, 0.025, 8)
A.yeux_mocha(1830, "fermes")

# 1:06 MOCHA — Mocha ferme les yeux… un POP le fait sursauter (queue gonflée)
pop(1996)
q = D["Mocha_Queue"]
cle(q, "scale", 1997, (1, 1, 1))
cle(q, "scale", 2000, (1.35, 1.35, 1.35))
cle(q, "scale", 2045, (1.3, 1.3, 1.3))
cle(q, "scale", 2060, (1, 1, 1))
pos(mocha, 1997, GX, -0.22, 0.006)
pos(mocha, 2002, GX, -0.22, 0.05)
pos(mocha, 2009, GX, -0.22, 0.006)
cle(bascule, "location", 1999, (GX, BORD_Y, 0))
cle(bascule, "location", 2003, (GX, BORD_Y, 0.025))  # il se cogne au plafond du carton !
cle(bascule, "location", 2008, (GX, BORD_Y, 0))
A.yeux_mocha(1997, "fermes")
A.yeux_mocha(1999, "ouverts")
A.yeux_mocha(2010, "agace", regard=(0.9, -0.2))
A.yeux_mocha(2060, "agace", regard=(0.9, -0.2))
A.yeux_mocha(2068, "mi-clos")

# 1:09 LARGE — plan final : Mocha dans le grand carton, Bip dans le petit
rotz(bip, 2071, 360)
pos(bip, 2071, 0.3, -0.64, 0)
cle(bip, "scale", 2071, (1, 1, 1))
cle(bip, "scale", 2074, (1.08, 1.08, 0.88))
cle(bip, "scale", 2077, (0.95, 0.95, 1.08))
pos(bip, 2083, 0.39, -0.71, 0.16)
pos(bip, 2090, 0.47, -0.78, 0.0)
cle(bip, "scale", 2090, (1.1, 1.1, 0.86))
cle(bip, "scale", 2096, (1, 1, 1))
expr(2100, "clin-oeil")
A.yeux_mocha(2085, "content")
A.yeux_mocha(2105, "fermes")

A.finir_expressions()
print("Épisode 02 : scène animée prête.")
A.ligne_de_commande()
