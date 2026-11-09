"""
Épisode 01 — « Le café » : animatique 3D (≈ 75 s, 30 im/s, 9:16).

Construit la scène complète (personnages + cuisine), anime l'épisode plan par plan
d'après episodes/01-le-cafe/script.md, et pose les changements de caméra.

Dans Blender : onglet Scripting → Ouvrir ce fichier → ▶ (la scène est prête à être
retouchée à la main : chaque plan est un repère « marqueur » dans la timeline).

En ligne de commande (rendu des images PNG) :
    blender -b --python episodes/01-le-cafe/animatique.py -- --rendu DOSSIER [--debut 1 --fin 2250]
Options : --pourcentage 100 (taille de l'image, 100 = 1080 × 1920), --echantillons 4,
          --ombres 4 (rayons d'ombre), --sans-debruitage (désactive OpenImageDenoise).
Réglage par défaut ≈ 9 s par image sur 4 processeurs sans carte graphique (bien plus rapide avec une carte graphique).
"""

import math
import os
import random
import runpy
import sys
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
# Construction de la scène
# ---------------------------------------------------------------------------
if bpy.app.background:
    bpy.ops.wm.read_factory_settings(use_empty=True)
elif "Cube" in bpy.data.objects:
    bpy.data.objects.remove(bpy.data.objects["Cube"], do_unlink=True)
runpy.run_path(os.path.join(OUTILS, "preparer-scene.py"), init_globals={"DEMO": False})
K = runpy.run_path(os.path.join(OUTILS, "decor-cuisine.py"))["construire_cuisine"]()

sc = bpy.context.scene
FPS = 30
sc.render.fps = FPS
sc.frame_start, sc.frame_end = 1, 2250  # 75 s
D = bpy.data.objects

bip, corps_bip, mocha = D["Bip"], D["Bip_Corps"], D["Mocha"]
tasse, horloge = K["tasse"], K["horloge"]

# Les anciennes caméras de preparer-scene sont remplacées par celles de l'épisode
for nom in ("CAM_LARGE", "CAM_BIP", "CAM_MOCHA", "Viseur_Large"):
    if nom in D:
        D.remove(D[nom], do_unlink=True)
for nom in ("Ref_Bip", "Ref_Mocha"):
    if nom in D:
        D[nom].hide_viewport = True

coll_ep = bpy.data.collections.new("Episode_01")
sc.collection.children.link(coll_ep)


def lin(h):
    h = h.lstrip("#")
    c = [int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    return tuple(x / 12.92 if x <= 0.04045 else ((x + 0.055) / 1.055) ** 2.4 for x in c) + (1.0,)


def mat(nom, hexa, rug=0.4):
    m = bpy.data.materials.new(nom)
    m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = lin(hexa)
    b.inputs["Roughness"].default_value = rug
    m.diffuse_color = lin(hexa)
    return m


def sphere(nom, r, loc, m, parent=None, ech=(1, 1, 1), seg=24):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=seg, ring_count=seg // 2, radius=r, location=loc)
    o = bpy.context.active_object
    o.name = nom
    o.scale = ech
    o.data.materials.append(m)
    for p in o.data.polygons:
        p.use_smooth = True
    for c in list(o.users_collection):
        c.objects.unlink(o)
    coll_ep.objects.link(o)
    if parent:
        o.parent = parent
    return o


# ---------------------------------------------------------------------------
# Outils d'animation
# ---------------------------------------------------------------------------
def courbes(obj):
    a = obj.animation_data.action
    try:
        from bpy_extras import anim_utils
        return anim_utils.action_get_channelbag_for_slot(a, obj.animation_data.action_slot).fcurves
    except (ImportError, AttributeError):
        return a.fcurves


def cle(obj, chemin, f, val, index=-1):
    """Pose une image clé : cle(bip, 'location', 120, (x, y, z))."""
    if chemin.startswith('["'):
        obj[chemin[2:-2]] = val
        obj.keyframe_insert(chemin, frame=f)
        return
    prop = getattr(obj, chemin)
    if index >= 0:
        prop[index] = val
    else:
        for i, v in enumerate(val):
            prop[i] = v
    obj.keyframe_insert(chemin, index=index, frame=f)


def saut(obj, chemin, f, avant, apres):
    """Changement instantané (coupe) : valeur « avant » jusqu'à f-1, « apres » à partir de f."""
    cle(obj, chemin, f - 1, avant)
    cle(obj, chemin, f, apres)


def pos(obj, f, x=None, y=None, z=None):
    v = list(obj.location)
    for i, val in enumerate((x, y, z)):
        if val is not None:
            v[i] = val
    cle(obj, "location", f, tuple(v))


def rotz(obj, f, degres):
    r = list(obj.rotation_euler)
    r[2] = math.radians(degres)
    cle(obj, "rotation_euler", f, tuple(r))


EXPR = {n: i for i, n in enumerate((
    "neutre", "joie", "tres-joyeux", "triste", "pleure", "colere", "surprise", "question", "exclamation",
    "idee", "amour", "panique", "veille", "batterie-faible", "erreur", "chargement", "clin-oeil", "determine"))}


def expr(f, nom, clignement=True):
    """Change l'écran de Bip, avec un micro-clignotement (2 images en veille) avant."""
    if clignement and f > 3:
        cle(bip, '["expression"]', f - 2, EXPR["veille"])
    cle(bip, '["expression"]', f, EXPR[nom])


def constantes(obj, chemin):
    if obj.animation_data and obj.animation_data.action:
        for fc in courbes(obj):
            if fc.data_path == chemin:
                for k in fc.keyframe_points:
                    k.interpolation = "CONSTANT"


def tremblement(obj, f1, f2, amp=0.006, pas=2):
    base = tuple(obj.location)
    rnd = random.Random(f1)
    for f in range(f1, f2, pas):
        cle(obj, "location", f, (base[0] + rnd.uniform(-amp, amp), base[1], base[2] + rnd.uniform(0, amp)))
    cle(obj, "location", f2, base)


def saute(obj, f, hauteur=0.05, duree=14):
    """Petit saut avec anticipation et écrasement (squash & stretch)."""
    x, y, z = obj.location
    cle(obj, "scale", f, (1, 1, 1))
    cle(obj, "scale", f + 3, (1.08, 1.08, 0.88))
    cle(obj, "location", f + 3, (x, y, z))
    cle(obj, "scale", f + 6, (0.94, 0.94, 1.1))
    cle(obj, "location", f + 3 + duree // 2, (x, y, z + hauteur))
    cle(obj, "location", f + 3 + duree, (x, y, z))
    cle(obj, "scale", f + 3 + duree, (1.1, 1.1, 0.86))
    cle(obj, "scale", f + 6 + duree, (1, 1, 1))


# Yeux de Mocha : outil commun (pupilles, paupières, sourcils — voir YEUX_MOCHA)
yeux_mocha = runpy.run_path(os.path.join(OUTILS, "outils_animation.py"))["yeux_mocha"]


# ---------------------------------------------------------------------------
# Accessoires animés : mousse, vapeur, café
# ---------------------------------------------------------------------------
m_mousse = mat("Mousse", "#FFF6E6", 0.6)
m_mousse.node_tree.nodes["Principled BSDF"].inputs["Emission Color"].default_value = lin("#FFF6E6")
m_mousse.node_tree.nodes["Principled BSDF"].inputs["Emission Strength"].default_value = 0.35
m_contour = bpy.data.materials["Contour"]


def contour(o, ep):
    o.data.materials.append(m_contour)
    md = o.modifiers.new("Contour", "SOLIDIFY")
    md.thickness, md.offset, md.use_flip_normals, md.use_rim = ep, 1.0, True, False
    md.material_offset = len(o.data.materials) - 1

m_cafe = mat("Cafe", "#5A3520", 0.15)
m_vapeur = mat("Vapeur", "#FFFFFF", 0.9)

rnd = random.Random(1)
mousse = []
for i in range(110):
    x, y = rnd.uniform(-0.78, 0.66), rnd.uniform(-0.32, 0.42)
    r = rnd.uniform(0.07, 0.17)
    s = sphere(f"Mousse_{i:03d}", 1.0, (x, y, rnd.uniform(0.0, 0.12)), m_mousse, seg=16)
    contour(s, 0.04)
    s["taille"] = r
    mousse.append(s)
# Les bulles trop proches des personnages (à leurs places de la scène finale) sont rétrécies
for s in mousse:
    for cx, cy in ((0.2, 0.1), (-0.2, -0.06), (0.0, -0.02), (-0.42, -0.05)):
        if math.hypot(s.location.x - cx, s.location.y - cy) < 0.15:
            s["taille"] = min(s["taille"], 0.05)
mousse_tasse = sphere("Mousse_Tasse", 1.0, (0, 0, 0.19), m_mousse, parent=tasse, ech=(0.095, 0.095, 0.05))

bpy.ops.mesh.primitive_cylinder_add(vertices=40, radius=1, depth=0.004, location=(-0.42, 0.0, 0.002))
flaque = bpy.context.active_object
flaque.name = "Flaque_Cafe"
flaque.data.materials.append(m_cafe)
for c in list(flaque.users_collection):
    c.objects.unlink(flaque)
coll_ep.objects.link(flaque)

bpy.ops.mesh.primitive_cylinder_add(vertices=16, radius=0.007, depth=1, location=(-0.42, 0.02, 0.19))
jet = bpy.context.active_object
jet.name = "Jet_Cafe"
jet.data.materials.append(m_cafe)
for c in list(jet.users_collection):
    c.objects.unlink(jet)
coll_ep.objects.link(jet)
# Le jet « pousse » vers le bas : origine en haut
jet.data.transform(__import__("mathutils").Matrix.Translation((0, 0, -0.5)))

vapeur = [sphere(f"Vapeur_{i}", 1.0, (0, 0, 0), m_vapeur, seg=12) for i in range(8)]


def bouffee(f, centre, direction=(0, 0, 1), taille=0.05, duree=24):
    rnd2 = random.Random(f)
    for i, v in enumerate(vapeur):
        d = f + i * 2
        p0 = (centre[0] + rnd2.uniform(-0.02, 0.02), centre[1] + rnd2.uniform(-0.02, 0.02), centre[2])
        p1 = tuple(p0[k] + direction[k] * rnd2.uniform(0.08, 0.18) + (rnd2.uniform(-0.05, 0.05) if k < 2 else 0) for k in range(3))
        cle(v, "scale", d - 1, (0, 0, 0))
        cle(v, "location", d, p0)
        cle(v, "scale", d, (taille * 0.3,) * 3)
        cle(v, "scale", d + duree // 2, (taille,) * 3)
        cle(v, "location", d + duree, p1)
        cle(v, "scale", d + duree, (0, 0, 0))


for v in vapeur:
    cle(v, "scale", 1, (0, 0, 0))


def degager_premier_plan(f1, f2, sujets, marge=0.16):
    """Astuce de tournage : pendant un gros plan, cache les bulles placées entre la caméra
    (devant, en y négatif) et les personnages filmés, pour qu'elles ne masquent pas leur visage."""
    for s in mousse:
        if any(s.location.y < cy - 0.02 and abs(s.location.x - cx) < marge + s["taille"] for cx, cy in sujets):
            s.hide_render = False
            if not s.get("degagee"):  # visible par défaut, une seule fois
                s.keyframe_insert("hide_render", frame=1)
                s["degagee"] = True
            s.keyframe_insert("hide_render", frame=f2)
            s.hide_render = True
            s.keyframe_insert("hide_render", frame=f1)


def mousse_etat(f, facteur):
    for s in mousse:
        cle(s, "scale", f, (s["taille"] * facteur,) * 3)


def mousse_monte(f1, f2):
    """La mousse envahit la cuisine, en partant de la machine à café."""
    for s in mousse:
        dist = math.hypot(s.location.x + 0.42, s.location.y - 0.05)
        d = int(f1 + (f2 - f1) * min(dist / 1.1, 1) * 0.75)
        cle(s, "scale", d, (0, 0, 0))
        cle(s, "scale", d + 18, (s["taille"] * 1.15,) * 3)
        cle(s, "scale", d + 26, (s["taille"],) * 3)


# ---------------------------------------------------------------------------
# Caméras
# ---------------------------------------------------------------------------
def camera(nom, loc, focale, cible=None, suivre=None):
    c = bpy.data.objects.new(nom, bpy.data.cameras.new(nom))
    c.data.lens = focale
    c.location = loc
    coll_ep.objects.link(c)
    if suivre:
        cl = c.constraints.new("COPY_LOCATION")
        cl.target = suivre
        cl.use_z = False
        cl.use_offset = True
    if cible:
        t = c.constraints.new("TRACK_TO")
        t.target = cible
        t.track_axis = "TRACK_NEGATIVE_Z"
        t.up_axis = "UP_Y"
    return c


viseur = bpy.data.objects.new("Viseur_Large", None)
viseur.location = (-0.075, 0.1, 0.3)
coll_ep.objects.link(viseur)
CAM = {
    "LARGE": camera("CAM_LARGE", (-0.075, -2.1, 0.45), 45, viseur),
    "BIP": camera("CAM_BIP", (0.05, -0.75, 0.16), 50, corps_bip, suivre=bip),
    "MOCHA": camera("CAM_MOCHA", (-0.08, -0.85, 0.3), 55, D["Mocha_Tete"], suivre=mocha),
    "HORLOGE": camera("CAM_HORLOGE", (0.42, -0.3, 0.84), 50, horloge),
}

PLANS = [  # (image de début, caméra) — d'après le script minuté
    (1, "LARGE"), (61, "HORLOGE"), (121, "BIP"), (211, "MOCHA"), (301, "BIP"), (421, "LARGE"),
    (721, "MOCHA"), (781, "LARGE"), (1141, "BIP"), (1501, "LARGE"), (1651, "BIP"), (1771, "MOCHA"),
    (1981, "BIP"), (2161, "LARGE"),
]
sc.timeline_markers.clear()
for f, nom in PLANS:
    m = sc.timeline_markers.new(f"{nom}_{(f - 1) // FPS:02d}s", frame=f)
    m.camera = CAM[nom]
sc.camera = CAM["LARGE"]

# ---------------------------------------------------------------------------
# ANIMATION — plan par plan
# ---------------------------------------------------------------------------
# Positions de repère
BIP_DEPART = (0.12, -0.08, 0)
MOCHA_DEPART = (0.32, 0.18, 0)
MOCHA_MILIEU = (0.2, 0.1, 0)
TASSE_MACHINE = (-0.42, -0.05, 0)
TASSE_FIN = (0.0, -0.02, 0)

# 0:00 HOOK — la cuisine est envahie de mousse (même image que 0:50)
cle(bip, "location", 1, (-0.2, -0.06, 0))
rotz(bip, 1, 10)
expr(1, "erreur", clignement=False)
cle(mocha, "location", 1, MOCHA_MILIEU)
rotz(mocha, 1, -5)
yeux_mocha(1, "mi-clos")
mousse_etat(1, 1.0)
cle(tasse, "location", 1, TASSE_MACHINE)
cle(mousse_tasse, "scale", 1, (0.095, 0.095, 0.05))
bouffee(8, (-0.2, -0.06, 0.33), taille=0.035)
cle(flaque, "scale", 1, (0, 0, 1))
cle(jet, "scale", 1, (1, 1, 0))

# 0:02 RETOUR EN ARRIÈRE — l'horloge tourne à l'envers, tout redevient propre
aig_m, aig_h = K["Horloge_Aiguille_M"], K["Horloge_Aiguille_H"]
cle(aig_m, "rotation_euler", 1, (0, 0, 0))
cle(aig_h, "rotation_euler", 1, (0, math.radians(240), 0))
cle(aig_m, "rotation_euler", 61, (0, 0, 0))
cle(aig_m, "rotation_euler", 116, (0, math.radians(-720), 0))
cle(aig_h, "rotation_euler", 61, (0, math.radians(240), 0))
cle(aig_h, "rotation_euler", 116, (0, math.radians(180), 0))
cle(aig_m, "rotation_euler", 2250, (0, math.radians(-720 + 360 * 1.2), 0))
mousse_etat(61, 1.0)
mousse_etat(62, 0.0)
saut(bip, "location", 62, (-0.2, -0.06, 0), BIP_DEPART)
rotz(bip, 61, 10)
rotz(bip, 62, 0)
saut(mocha, "location", 62, MOCHA_MILIEU, MOCHA_DEPART)
rotz(mocha, 61, -5)
rotz(mocha, 62, -45)
saut(tasse, "location", 62, TASSE_MACHINE, (-0.12, 0.02, 0))
cle(mousse_tasse, "scale", 61, (0.095, 0.095, 0.05))
cle(mousse_tasse, "scale", 62, (0, 0, 0))
expr(62, "veille", clignement=False)

# 0:04 BIP S'ALLUME — bip-bip-boup
expr(140, "joie")
saute(bip, 140, 0.05)

# 0:07 MOCHA BÂILLE et fixe la tasse vide
yeux_mocha(215, "mi-clos")
yeux_mocha(222, "fermes")
cle(mocha, "scale", 222, (1, 1, 1))
cle(mocha, "scale", 235, (0.97, 0.97, 1.06))
cle(mocha, "scale", 255, (1, 1, 1))
yeux_mocha(255, "fermes")
yeux_mocha(262, "mi-clos")

# 0:10 BIP COMPREND « CAFÉ »
expr(305, "question")
expr(345, "idee")
saute(bip, 345, 0.03, 10)
expr(385, "determine")

# 0:14 TENTATIVE 1 — Bip appuie partout ; jet de vapeur au visage
pos(bip, 421, *BIP_DEPART)
rotz(bip, 421, 0)
pos(bip, 470, -0.2, 0.02, 0)
rotz(bip, 470, -80)
for i, f in enumerate(range(480, 560, 20)):  # quatre appuis sur la machine
    pos(bip, f, -0.2, 0.02, 0)
    pos(bip, f + 6, -0.235, 0.02, 0.01)
    pos(bip, f + 12, -0.2, 0.02, 0)
    b = K[f"bouton_{i % 3}"]
    cle(b, "scale", f + 5, (1, 1, 1))
    cle(b, "scale", f + 7, (1, 1, 0.4))
    cle(b, "scale", f + 12, (1, 1, 1))
bouffee(560, (-0.3, 0.0, 0.2), direction=(1, -0.3, 0.3), taille=0.06, duree=30)
expr(562, "surprise", clignement=False)
pos(bip, 560, -0.2, 0.02, 0)
pos(bip, 575, 0.0, -0.05, 0)
rotz(bip, 560, -80)
rotz(bip, 575, 200)
rotz(bip, 600, 360)
expr(600, "erreur")
tremblement(bip, 600, 640, 0.004)
expr(675, "neutre")
rotz(bip, 700, 360)
yeux_mocha(560, "mi-clos")

# 0:24 MOCHA REGARDE L'OBJECTIF
rotz(mocha, 720, -45)
rotz(mocha, 724, -8)
rotz(mocha, 778, -8)
rotz(mocha, 782, -45)

# 0:26 TENTATIVE 2 — le café coule à côté ; Bip essuie… avec Mocha
pos(bip, 781, 0.0, -0.05, 0)
rotz(bip, 781, 360)
pos(bip, 800, -0.24, 0.0, 0)
rotz(bip, 800, 280)
expr(800, "determine")
cle(K["bouton_1"], "scale", 806, (1, 1, 1))
cle(K["bouton_1"], "scale", 808, (1, 1, 0.4))
cle(K["bouton_1"], "scale", 814, (1, 1, 1))
cle(jet, "scale", 810, (1, 1, 0))
cle(jet, "scale", 820, (1, 1, 0.19))
cle(jet, "scale", 900, (1, 1, 0.19))
cle(jet, "scale", 910, (1, 1, 0))
cle(flaque, "scale", 815, (0, 0, 1))
cle(flaque, "scale", 930, (0.16, 0.13, 1))
expr(830, "joie")
pos(bip, 900, -0.24, 0.0, 0)
pos(bip, 915, -0.15, -0.08, 0)
rotz(bip, 915, 360)
expr(918, "surprise")
expr(945, "idee")
pos(bip, 960, -0.15, -0.08, 0)
pos(bip, 1000, 0.2, 0.08, 0)  # va chercher Mocha
rotz(bip, 1000, 420)
expr(1000, "determine")
pos(mocha, 1010, *MOCHA_DEPART)
rotz(mocha, 1010, -45)
yeux_mocha(1012, "mi-clos")
yeux_mocha(1016, "ouverts")
pos(bip, 1010, 0.2, 0.08, 0)
pos(mocha, 1050, -0.2, 0.08, 0)  # Mocha glisse dans la flaque, poussé par Bip
pos(bip, 1050, -0.06, 0.04, 0)
rotz(mocha, 1050, -100)
pos(mocha, 1080, -0.34, -0.07, 0)
pos(bip, 1080, -0.2, -0.02, 0)
cle(flaque, "scale", 1045, (0.16, 0.13, 1))
cle(flaque, "scale", 1085, (0.03, 0.02, 1))
expr(1085, "tres-joyeux")
yeux_mocha(1095, "mi-clos")
rotz(mocha, 1098, -100)
rotz(mocha, 1104, 20)  # Mocha se retourne, indigné (miaou)
cle(mocha, "scale", 1100, (1, 1, 1))
cle(mocha, "scale", 1104, (1.05, 1.05, 0.95))
cle(mocha, "scale", 1110, (1, 1, 1))
expr(1108, "neutre")

# 0:38 TENTATIVE 3 — Bip met la tasse sous la machine, lait à fond… la mousse monte
pos(mocha, 1141, -0.34, -0.07, 0)  # Mocha s'éloigne, vexé
rotz(mocha, 1141, 20)
rotz(mocha, 1150, 95)
pos(mocha, 1200, *MOCHA_MILIEU)
rotz(mocha, 1200, 95)
rotz(mocha, 1215, -5)
pos(bip, 1141, -0.2, -0.02, 0)
pos(bip, 1150, 0.0, -0.06, 0)
rotz(bip, 1150, 450)
expr(1145, "determine")
pos(tasse, 1150, -0.12, 0.02, 0)
pos(bip, 1200, -0.25, -0.06, 0)
pos(tasse, 1200, *TASSE_MACHINE)
rotz(bip, 1200, 450)
cle(K["bouton_2"], "scale", 1212, (1, 1, 1))
cle(K["bouton_2"], "scale", 1214, (1, 1, 0.4))
cle(K["bouton_2"], "scale", 1220, (1, 1, 1))
cle(mousse_tasse, "scale", 1225, (0, 0, 0))
cle(mousse_tasse, "scale", 1270, (0.095, 0.095, 0.05))
cle(mousse_tasse, "scale", 1290, (0.11, 0.11, 0.12))
cle(mousse_tasse, "scale", 1310, (0.095, 0.095, 0.05))
expr(1240, "tres-joyeux")
expr(1300, "surprise")
expr(1330, "panique")
mousse_monte(1300, 1490)
pos(bip, 1300, -0.25, -0.06, 0)
pos(bip, 1340, -0.2, -0.06, 0)
rotz(bip, 1340, 370)
tremblement(bip, 1340, 1495, 0.008)

# 0:50 LA CATASTROPHE — exactement l'image du début
pos(bip, 1501, -0.2, -0.06, 0)
expr(1501, "erreur", clignement=False)
bouffee(1505, (-0.2, -0.06, 0.33), taille=0.035)
pos(tasse, 1501, *TASSE_MACHINE)

# 0:55 BIP PRÉSENTE LA TASSE À MOCHA
pos(tasse, 1660, *TASSE_MACHINE)
pos(bip, 1660, -0.2, -0.06, 0)
pos(tasse, 1720, *TASSE_FIN)
pos(bip, 1720, -0.17, -0.08, 0)
rotz(bip, 1720, 340)
expr(1700, "triste")

# 0:59 MOCHA VIDE LA TASSE… ET S'INSTALLE DEDANS
cle(tasse, "rotation_euler", 1790, (0, 0, 0))
cle(tasse, "rotation_euler", 1815, (0, math.radians(-75), 0))
cle(mousse_tasse, "scale", 1812, (0.095, 0.095, 0.05))
cle(mousse_tasse, "scale", 1820, (0, 0, 0))
cle(tasse, "rotation_euler", 1850, (0, math.radians(-75), 0))
cle(tasse, "rotation_euler", 1870, (0, 0, 0))
rotz(mocha, 1785, -5)
rotz(mocha, 1800, -60)
rotz(mocha, 1870, -60)
pos(mocha, 1880, *MOCHA_MILIEU)
cle(mocha, "scale", 1880, (1, 1, 1))
cle(mocha, "scale", 1886, (1.05, 1.05, 0.85))
pos(mocha, 1898, 0.1, 0.03, 0.24)
cle(mocha, "scale", 1898, (0.85, 0.85, 1.05))
pos(mocha, 1912, 0.0, -0.02, 0.05)
cle(mocha, "scale", 1912, (0.78, 0.78, 0.55))
cle(mocha, "scale", 1920, (0.72, 0.72, 0.62))
rotz(mocha, 1912, -10)
yeux_mocha(1930, "fermes")

# 1:06 BIP COMPREND, S'INSTALLE À CÔTÉ ET SE MET EN VEILLE
expr(1990, "question")
expr(2040, "amour")
pos(bip, 2050, -0.17, -0.08, 0)
pos(bip, 2090, -0.19, -0.04, 0)
rotz(bip, 2090, 380)
expr(2120, "veille")
cle(bip, "scale", 2118, (1, 1, 1))
cle(bip, "scale", 2135, (1.04, 1.04, 0.95))

# 1:12 LE SOLEIL SE LÈVE — boucle vers l'image d'ouverture
soleil = D["Soleil"]
soleil.data.energy = 1.6
cle(soleil.data, "color", 2160, (1, 1, 1))
cle(soleil.data, "color", 2250, (1.0, 0.78, 0.55))
soleil.data.energy = 1.6
soleil.data.keyframe_insert("energy", frame=2160)
soleil.data.energy = 2.4
soleil.data.keyframe_insert("energy", frame=2250)

# Regard de Mocha : ses réactions aux catastrophes de Bip
yeux_mocha(1, "agace", regard=(-0.7, 0))          # hook : il fixe Bip, au milieu de la mousse
yeux_mocha(60, "agace", regard=(-0.7, 0))
yeux_mocha(62, "mi-clos")
yeux_mocha(566, "content", regard=(-0.8, 0))      # Bip prend la vapeur au visage : petit plaisir
yeux_mocha(640, "content", regard=(-0.8, 0))
yeux_mocha(650, "mi-clos")
yeux_mocha(722, "agace")                          # regard caméra
yeux_mocha(776, "agace")
yeux_mocha(782, "mi-clos")
yeux_mocha(1040, "agace", regard=(-0.8, -0.2))    # essuyé comme un torchon
yeux_mocha(1088, "agace", regard=(-0.8, -0.2))
yeux_mocha(1310, "ouverts", regard=(-0.6, -0.5))  # la mousse monte
yeux_mocha(1400, "mefiant", regard=(-0.8, 0))
yeux_mocha(1495, "mefiant", regard=(-0.8, 0))
yeux_mocha(1501, "agace", regard=(-0.7, 0))       # la catastrophe (même image que le début)
yeux_mocha(1700, "agace", regard=(-0.7, 0))
yeux_mocha(1730, "attendri", regard=(-0.4, -0.8))  # la tasse… parfaite pour faire la sieste
yeux_mocha(1790, "content", regard=(-0.4, -0.8))
yeux_mocha(1900, "content")

constantes(bip, '["expression"]')

# Lumière plus douce dans la cuisine (évite la surexposition)
sc.world.node_tree.nodes["Background"].inputs["Strength"].default_value = 0.45
D["Lumiere_Douce"].data.energy = 22
D["Contre_Jour"].data.energy = 10
for o in ("Tasse_Corps", "Machine_Corps"):
    contour(D[o], 0.006)

# Appels dans l'ordre chronologique : chaque plan rétablit la visibilité à sa fin,
# le plan suivant (qui commence à la même image) doit donc passer après.
# Plans larges : on garde la marée de mousse, mais l'écran « erreur » de Bip (catastrophe, aussi
# montrée en ouverture) et la tasse où dort Mocha (image finale) restent lisibles.
degager_premier_plan(1, 61, [(-0.2, -0.06)], marge=0.03)
degager_premier_plan(1501, 1651, [(-0.2, -0.06)], marge=0.03)
# Gros plans de la fin : la mousse au premier plan ne doit pas cacher Bip ni Mocha
degager_premier_plan(1651, 1771, [(-0.2, -0.06), (-0.17, -0.08), TASSE_FIN[:2]])
degager_premier_plan(1771, 1981, [MOCHA_MILIEU[:2], TASSE_FIN[:2]])
degager_premier_plan(1981, 2161, [(-0.17, -0.08), (-0.19, -0.04), TASSE_FIN[:2]])
degager_premier_plan(2161, 2251, [(-0.19, -0.04), TASSE_FIN[:2]], marge=0.06)  # image finale


# Rendu : EEVEE propre et rapide = 4 passes + 4 rayons d'ombre + débruiteur OpenImageDenoise
def regler_rendu(echantillons=4, rayons_ombre=4, debruitage=True):
    sc.eevee.taa_render_samples = echantillons
    if hasattr(sc.eevee, "shadow_ray_count"):  # Blender 4.2 et plus
        sc.eevee.shadow_ray_count = rayons_ombre  # supprime le grain des ombres douces
    sc.render.image_settings.file_format = "PNG"
    if D.get("Bip_Torse"):  # personnages au style studio : image AgX, reflets, profondeur de champ
        runpy.run_path(os.path.join(OUTILS, "style-studio.py"))["reglages_image"](sc)
    if not debruitage:
        sc.render.use_compositing = False
        return
    vl = sc.view_layers[0]
    vl.use_pass_normal = vl.use_pass_diffuse_color = True  # guident le débruiteur
    if hasattr(sc, "compositing_node_group"):  # Blender 5.x
        arbre = bpy.data.node_groups.get("Debruitage") or bpy.data.node_groups.new("Debruitage", "CompositorNodeTree")
        arbre.nodes.clear()
        if not arbre.interface.items_tree:
            arbre.interface.new_socket("Image", in_out="OUTPUT", socket_type="NodeSocketColor")
        sortie = arbre.nodes.new("NodeGroupOutput")
        sc.compositing_node_group = arbre
    else:  # Blender 4.x
        sc.use_nodes = True
        arbre = sc.node_tree
        arbre.nodes.clear()
        sortie = arbre.nodes.new("CompositorNodeComposite")
    calques = arbre.nodes.new("CompositorNodeRLayers")
    debruiteur = arbre.nodes.new("CompositorNodeDenoise")
    sorties = calques.outputs
    arbre.links.new(sorties["Image"], debruiteur.inputs["Image"])
    arbre.links.new(sorties["Normal"], debruiteur.inputs["Normal"])
    albedo = sorties.get("Diffuse Color") or sorties.get("DiffCol")
    if albedo:
        arbre.links.new(albedo, debruiteur.inputs["Albedo"])
    arbre.links.new(debruiteur.outputs[0], sortie.inputs[0])
    sc.render.use_compositing = True


regler_rendu()

# ---------------------------------------------------------------------------
# Rendu en ligne de commande
# ---------------------------------------------------------------------------
if "--" in sys.argv:
    args = sys.argv[sys.argv.index("--") + 1:]

    def arg(nom, defaut):
        return type(defaut)(args[args.index(nom) + 1]) if nom in args else defaut

    regler_rendu(arg("--echantillons", 4), arg("--ombres", 4), "--sans-debruitage" not in args)
    dossier = arg("--rendu", "")
    if dossier:
        sc.render.resolution_percentage = arg("--pourcentage", 100)
        sc.frame_start, sc.frame_end = arg("--debut", 1), arg("--fin", 2250)
        sc.render.filepath = os.path.join(dossier, "")
        sc.render.use_overwrite = False  # reprise possible : les images déjà rendues sont gardées
        sc.render.use_placeholder = True
        bpy.ops.render.render(animation=True)
    if "--images" in args:  # rendus de contrôle : --images 1,140,560
        dossier = arg("--controle", ".")
        sc.render.resolution_percentage = arg("--pourcentage", 100)
        for f in [int(x) for x in arg("--images", "1").split(",")]:
            sc.frame_set(f)
            sc.render.filepath = os.path.join(dossier, f"controle_{f:04d}.png")
            bpy.ops.render.render(write_still=True)
    if "--enregistrer" in args:
        bpy.ops.wm.save_as_mainfile(filepath=arg("--enregistrer", "episode01.blend"))

print("Épisode 01 : scène animée prête.")
