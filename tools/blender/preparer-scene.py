"""
Bip & Mocha — préparation automatique d'une scène Blender (testé avec Blender 5.2 LTS).

Ce que fait le script (dans un fichier Blender vide) :
  - règle la scène pour TikTok : 1080 x 1920 (9:16), 30 images/s, EEVEE, unités en mètres ;
  - crée un « blockout » de BIP aux bonnes dimensions (≈ 32 cm), avec contour cartoon ;
  - crée l'ÉCRAN de Bip, branché sur les 18 expressions : il suffit de changer
    la propriété « expression » de l'objet Bip (0 à 17) et de l'animer ;
  - crée un blockout de MOCHA (formes simples) pour avoir l'échelle ;
  - ajoute un sol, un éclairage doux, 3 caméras préréglées et les planches de référence ;
  - ajoute une petite animation de démonstration (5 s) — à supprimer ensuite.

Utilisation :
  1. Ouvrir Blender → Fichier → Nouveau → Général, puis supprimer le cube.
  2. Onglet « Scripting » → Ouvrir → choisir ce fichier → bouton ▶ (Exécuter).
  3. Enregistrer le .blend (hors du dépôt Git, ou avec Git LFS).
Ou en ligne de commande :  blender --python tools/blender/preparer-scene.py

Les blockouts servent à apprendre et à caler l'échelle : les vrais modèles les remplaceront.
"""

import json
import math
import os

import warnings

import bpy

warnings.filterwarnings("ignore", category=DeprecationWarning)  # use_nodes (Blender 5.x)

DEMO = globals().get("DEMO", True)  # False = pas d'animation de démonstration
# « studio » = rendu type film d'animation (plastique laqué, pelage, grands yeux) ; « simple » = blockouts
STYLE = globals().get("STYLE", "studio")

# Si le script ne trouve pas le projet tout seul, coller ici le chemin du dossier
# du projet (celui qui contient « assets », « docs », « tools »), par exemple :
#   DOSSIER_PROJET = r"C:\Users\moi\Documents\Bip-et-Mocha-"
DOSSIER_PROJET = r""

# ---------------------------------------------------------------------------
# Localisation du dépôt (pour charger les images de assets/design/)
# ---------------------------------------------------------------------------
FICHIER_TEMOIN = os.path.join("assets", "design", "bip-ecran-atlas.json")


def dossier_projet():
    candidats = []
    if DOSSIER_PROJET:
        candidats.append(DOSSIER_PROJET)
    # Chemin réel du script ouvert dans l'éditeur de texte de Blender
    for t in bpy.data.texts:
        if t.filepath:
            candidats.append(os.path.dirname(os.path.abspath(bpy.path.abspath(t.filepath))))
    # Lancement en ligne de commande (blender --python ...)
    if "__file__" in globals():
        candidats.append(os.path.dirname(os.path.abspath(__file__)))
    # Dossier du fichier .blend, s'il est enregistré
    if bpy.data.filepath:
        candidats.append(os.path.dirname(bpy.data.filepath))
    candidats.append(os.getcwd())
    # On remonte l'arborescence depuis chaque candidat jusqu'à trouver assets/design/
    for c in candidats:
        d = c
        for _ in range(6):
            if os.path.isfile(os.path.join(d, FICHIER_TEMOIN)):
                return d
            parent = os.path.dirname(d)
            if parent == d:
                break
            d = parent
    raise RuntimeError(
        "Dossier du projet introuvable. Vérifier que tout le projet est sur l'ordinateur "
        "(dossiers assets, docs, tools) et pas seulement ce script, puis ouvrir le script "
        "via Scripting > Ouvrir depuis tools/blender/. Sinon, renseigner DOSSIER_PROJET "
        "en haut du script. Chemins essayés : " + " | ".join(candidats)
    )


RACINE = dossier_projet()
DESIGN = os.path.join(RACINE, "assets", "design")

# Palette (identique à tools/generer-design.js)
def hexa(h, a=1.0):
    h = h.lstrip("#")
    srgb = [int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    lin = [c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4 for c in srgb]
    return (*lin, a)


COUL = {
    "bip_corps": hexa("#F2EDE4"), "bip_accent": hexa("#F28C38"), "bip_cadre": hexa("#2A2F3A"),
    "mocha_pelage": hexa("#C49A6C"), "mocha_fonce": hexa("#7A4E2D"), "mocha_creme": hexa("#F3E3CC"),
    "mocha_yeux": hexa("#E8A33D"), "trait": hexa("#3B2F28"), "sol": hexa("#E9DFD1"),
}

# ---------------------------------------------------------------------------
# Outils
# ---------------------------------------------------------------------------
def collection(nom):
    c = bpy.data.collections.get(nom) or bpy.data.collections.new(nom)
    if c.name not in bpy.context.scene.collection.children:
        bpy.context.scene.collection.children.link(c)
    return c


def ranger(obj, coll):
    for c in list(obj.users_collection):
        c.objects.unlink(obj)
    coll.objects.link(obj)


def materiau(nom, couleur, rugosite=0.45):
    m = bpy.data.materials.get(nom) or bpy.data.materials.new(nom)
    m.use_nodes = True
    bsdf = m.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = couleur
    bsdf.inputs["Roughness"].default_value = rugosite
    m.diffuse_color = couleur
    return m


def materiau_contour():
    m = bpy.data.materials.get("Contour")
    if m:
        return m
    m = bpy.data.materials.new("Contour")
    m.use_nodes = True
    nt = m.node_tree
    nt.nodes.clear()
    em = nt.nodes.new("ShaderNodeEmission")
    em.inputs["Color"].default_value = COUL["trait"]
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    nt.links.new(em.outputs[0], out.inputs[0])
    m.use_backface_culling = True
    m.diffuse_color = COUL["trait"]
    return m


def contour(obj, epaisseur=0.003):
    """Contour cartoon par « coque inversée » : fonctionne dans EEVEE et Cycles."""
    obj.data.materials.append(materiau_contour())
    mod = obj.modifiers.new("Contour", "SOLIDIFY")
    mod.thickness = epaisseur
    mod.offset = 1.0
    mod.use_flip_normals = True
    mod.use_rim = False
    mod.material_offset = len(obj.data.materials) - 1


def lisser(obj, niveaux=2):
    for p in obj.data.polygons:
        p.use_smooth = True
    mod = obj.modifiers.new("Lissage", "SUBSURF")
    mod.levels = niveaux
    mod.render_levels = niveaux


def sphere(nom, rayon, loc, echelle=(1, 1, 1), mat=None, coll=None, parent=None):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=32, ring_count=16, radius=rayon, location=loc)
    o = bpy.context.active_object
    o.name = nom
    o.scale = echelle
    for p in o.data.polygons:
        p.use_smooth = True
    if mat:
        o.data.materials.append(mat)
    if coll:
        ranger(o, coll)
    if parent:
        o.parent = parent
    return o


def courbe(nom, points, epaisseur, mat, coll, parent=None):
    cu = bpy.data.curves.new(nom, "CURVE")
    cu.dimensions = "3D"
    cu.bevel_depth = epaisseur
    cu.bevel_resolution = 4
    cu.use_fill_caps = True
    sp = cu.splines.new("BEZIER")
    sp.bezier_points.add(len(points) - 1)
    for bp, p in zip(sp.bezier_points, points):
        bp.co = p
        bp.handle_left_type = bp.handle_right_type = "AUTO"
    cu.materials.append(mat)
    o = bpy.data.objects.new(nom, cu)
    coll.objects.link(o)
    if parent:
        o.parent = parent
    return o


def reference(nom, fichier, largeur_m, centre_x, centre_z, y, coll):
    chemin = os.path.join(DESIGN, fichier)
    if not os.path.exists(chemin):
        return None
    img = bpy.data.images.load(chemin, check_existing=True)
    e = bpy.data.objects.new(nom, None)
    e.empty_display_type = "IMAGE"
    e.data = img
    e.empty_display_size = largeur_m
    e.location = (centre_x, y, centre_z)
    e.rotation_euler = (math.radians(90), 0, 0)
    e.color[3] = 0.5
    e.use_empty_image_alpha = True
    e.show_empty_image_perspective = False  # visible seulement en vue orthographique
    coll.objects.link(e)
    return e


# ---------------------------------------------------------------------------
# 1. Réglages de la scène
# ---------------------------------------------------------------------------
sc = bpy.context.scene
sc.name = "Bip_et_Mocha"
for nom in ("BLENDER_EEVEE", "BLENDER_EEVEE_NEXT"):
    try:
        sc.render.engine = nom
        break
    except TypeError:
        pass
sc.render.resolution_x, sc.render.resolution_y = 1080, 1920
sc.render.resolution_percentage = 100
sc.render.fps = 30
sc.frame_start, sc.frame_end = 1, 150
sc.unit_settings.system = "METRIC"
sc.unit_settings.length_unit = "CENTIMETERS"
sc.view_settings.view_transform = "Standard"  # couleurs fidèles à la palette
if sc.world is None:
    sc.world = bpy.data.worlds.new("Monde")
sc.world.use_nodes = True
fond = sc.world.node_tree.nodes.get("Background")
fond.inputs["Color"].default_value = hexa("#FBF7F1")
fond.inputs["Strength"].default_value = 1.0

# Nettoyage d'un éventuel lancement précédent
for nom in ("Bip", "Mocha", "Plateau", "References"):
    c = bpy.data.collections.get(nom)
    if c:
        for o in list(c.objects):
            bpy.data.objects.remove(o, do_unlink=True)

C_BIP, C_MOCHA, C_PLAT, C_REF = (collection(n) for n in ("Bip", "Mocha", "Plateau", "References"))

# ---------------------------------------------------------------------------
# 2. BIP (dimensions : voir docs/08-fiches-personnages.md)
# ---------------------------------------------------------------------------
m_corps = materiau("Bip_Corps", COUL["bip_corps"], 0.35)
m_accent = materiau("Bip_Accent", COUL["bip_accent"], 0.4)
m_cadre = materiau("Bip_Cadre", COUL["bip_cadre"], 0.3)

bip = bpy.data.objects.new("Bip", None)  # objet racine : c'est lui qu'on anime
bip.empty_display_type = "PLAIN_AXES"
bip.empty_display_size = 0.15
C_BIP.objects.link(bip)
bip["expression"] = 0
ui = bip.id_properties_ui("expression")
ui.update(min=0, max=17, description="0 neutre, 1 joie, 2 très joyeux, 3 triste… (voir assets/design/bip-ecran-atlas.json)")

corps = sphere("Bip_Corps", 1.0, (0, 0, 0.15), (0.105, 0.10, 0.115), m_corps, C_BIP, bip)
contour(corps, 0.025)  # épaisseur relative à l'échelle de l'objet

roue = sphere("Bip_Roue", 0.03, (0, 0, 0.03), mat=m_accent, coll=C_BIP, parent=bip)
contour(roue, 0.003)

courbe("Bip_Antenne", [(0, 0, 0.255), (0, 0.002, 0.285), (0, 0, 0.31)], 0.004, m_accent, C_BIP, bip)
boule = sphere("Bip_Antenne_Boule", 0.014, (0, 0, 0.32), mat=m_accent, coll=C_BIP, parent=bip)
contour(boule, 0.0025)

for cote, s in (("G", -1), ("D", 1)):
    courbe(f"Bip_Bras_{cote}", [(s * 0.095, 0, 0.17), (s * 0.13, 0, 0.12), (s * 0.128, 0, 0.075)], 0.007, m_cadre, C_BIP, bip)
    main = sphere(f"Bip_Main_{cote}", 0.012, (s * 0.128, 0, 0.062), mat=m_accent, coll=C_BIP, parent=bip)
    contour(main, 0.0025)

# Cadre de l'écran
bpy.ops.mesh.primitive_cube_add(size=1, location=(0, -0.075, 0.16))
cadre = bpy.context.active_object
cadre.name = "Bip_Ecran_Cadre"
cadre.scale = (0.144, 0.07, 0.108)
cadre.data.materials.append(m_cadre)
bev = cadre.modifiers.new("Arrondi", "BEVEL")
bev.width = 0.12
bev.segments = 6
bev.affect = "EDGES"
ranger(cadre, C_BIP)
cadre.parent = bip

# Écran : un plan dont la texture est l'atlas des 18 expressions
bpy.ops.mesh.primitive_plane_add(size=1, location=(0, -0.1115, 0.16), rotation=(math.radians(90), 0, 0))
ecran = bpy.context.active_object
ecran.name = "Bip_Ecran"
ecran.scale = (0.124, 0.093, 1)
ranger(ecran, C_BIP)
ecran.parent = bip

with open(os.path.join(DESIGN, "bip-ecran-atlas.json"), encoding="utf-8") as f:
    atlas = json.load(f)
COLS, LIGNES = atlas["colonnes"], atlas["lignes"]

m_ecran = bpy.data.materials.new("Bip_Ecran")
m_ecran.use_nodes = True
nt = m_ecran.node_tree
nt.nodes.clear()
N, L = nt.nodes.new, nt.links.new


def math_node(op, a=None, b=None, x=0, y=0):
    n = N("ShaderNodeMath")
    n.operation = op
    n.location = (x, y)
    if a is not None and not hasattr(a, "is_linked"):
        n.inputs[0].default_value = a
    if b is not None and not hasattr(b, "is_linked"):
        n.inputs[1].default_value = b
    return n


attr = N("ShaderNodeAttribute")  # lit la propriété « expression » de l'écran (pilotée par Bip)
attr.attribute_type = "OBJECT"
attr.attribute_name = '["expression"]'
attr.location = (-1200, 0)
arrondi = math_node("ROUND", x=-1000, y=0)
L(attr.outputs["Fac"], arrondi.inputs[0])
col = math_node("MODULO", b=COLS, x=-800, y=150)
L(arrondi.outputs[0], col.inputs[0])
off_x = math_node("DIVIDE", b=COLS, x=-600, y=150)
L(col.outputs[0], off_x.inputs[0])
lig = math_node("DIVIDE", b=COLS, x=-800, y=-150)
L(arrondi.outputs[0], lig.inputs[0])
lig_f = math_node("FLOOR", x=-650, y=-150)
L(lig.outputs[0], lig_f.inputs[0])
inv = math_node("SUBTRACT", a=LIGNES - 1, x=-500, y=-150)
L(lig_f.outputs[0], inv.inputs[1])
off_y = math_node("DIVIDE", b=LIGNES, x=-350, y=-150)
L(inv.outputs[0], off_y.inputs[0])
comb = N("ShaderNodeCombineXYZ")
comb.location = (-200, 0)
L(off_x.outputs[0], comb.inputs["X"])
L(off_y.outputs[0], comb.inputs["Y"])
coord = N("ShaderNodeTexCoord")
coord.location = (-500, 300)
mult = N("ShaderNodeVectorMath")
mult.operation = "MULTIPLY"
mult.inputs[1].default_value = (1 / COLS, 1 / LIGNES, 1)
mult.location = (-300, 300)
L(coord.outputs["UV"], mult.inputs[0])
add = N("ShaderNodeVectorMath")
add.operation = "ADD"
add.location = (-50, 150)
L(mult.outputs[0], add.inputs[0])
L(comb.outputs[0], add.inputs[1])
tex = N("ShaderNodeTexImage")
tex.image = bpy.data.images.load(os.path.join(DESIGN, "bip-ecran-atlas.png"), check_existing=True)
tex.extension = "EXTEND"
tex.location = (150, 150)
L(add.outputs[0], tex.inputs["Vector"])
emis = N("ShaderNodeEmission")
emis.inputs["Strength"].default_value = 1.5
emis.location = (450, 150)
L(tex.outputs["Color"], emis.inputs["Color"])
sortie = N("ShaderNodeOutputMaterial")
sortie.location = (650, 150)
L(emis.outputs[0], sortie.inputs["Surface"])
ecran.data.materials.append(m_ecran)

# La propriété de l'écran recopie celle de Bip (pilote simple, sans Python)
ecran["expression"] = 0
fc = ecran.driver_add('["expression"]')
fc.driver.type = "AVERAGE"
var = fc.driver.variables.new()
var.name = "expr"
var.targets[0].id = bip
var.targets[0].data_path = '["expression"]'

# ---------------------------------------------------------------------------
# 3. MOCHA (blockout d'échelle : ≈ 45 cm assis)
# ---------------------------------------------------------------------------
m_pel = materiau("Mocha_Pelage", COUL["mocha_pelage"], 0.7)
m_fon = materiau("Mocha_Fonce", COUL["mocha_fonce"], 0.7)
m_cre = materiau("Mocha_Creme", COUL["mocha_creme"], 0.7)
m_yeux = materiau("Mocha_Yeux", COUL["mocha_yeux"], 0.2)
m_paup = materiau("Mocha_Paupiere", hexa("#93693F"), 0.8)  # un ton plus foncé : la paupière avance, donc reçoit plus de lumière
m_pupille = materiau("Mocha_Pupille", hexa("#1B1410"), 0.65)  # mat : sinon le noir reflète la fenêtre et vire au gris
m_reflet = materiau("Mocha_Reflet", hexa("#FFFFFF"), 0.1)
m_reflet.node_tree.nodes["Principled BSDF"].inputs["Emission Color"].default_value = (1, 1, 1, 1)
m_reflet.node_tree.nodes["Principled BSDF"].inputs["Emission Strength"].default_value = 2.0

mocha = bpy.data.objects.new("Mocha", None)
mocha.empty_display_type = "PLAIN_AXES"
mocha.empty_display_size = 0.2
mocha.location = (0.3, 0.12, 0)
mocha.rotation_euler = (0, 0, math.radians(-15))
C_MOCHA.objects.link(mocha)

for nom, r, loc, ech, mat, ep in (
    ("Mocha_Corps", 1.0, (0, 0, 0.13), (0.10, 0.09, 0.135), m_pel, 0.025),
    ("Mocha_Ventre", 1.0, (0, -0.045, 0.12), (0.065, 0.06, 0.1), m_cre, None),
    ("Mocha_Tete", 1.0, (0, -0.01, 0.32), (0.115, 0.1, 0.095), m_pel, 0.025),
    ("Mocha_Museau", 1.0, (0, -0.085, 0.29), (0.055, 0.035, 0.035), m_cre, None),
    ("Mocha_Patte_G", 1.0, (-0.04, -0.07, 0.015), (0.03, 0.04, 0.016), m_cre, 0.08),
    ("Mocha_Patte_D", 1.0, (0.04, -0.07, 0.015), (0.03, 0.04, 0.016), m_cre, 0.08),
    ("Mocha_Oeil_G", 1.0, (-0.045, -0.09, 0.335), (0.024, 0.012, 0.02), m_yeux, 0.12),
    ("Mocha_Oeil_D", 1.0, (0.045, -0.09, 0.335), (0.024, 0.012, 0.02), m_yeux, 0.12),
):
    o = sphere(nom, r, loc, ech, mat, C_MOCHA, mocha)
    if ep:
        contour(o, ep)

for cote, s in (("G", -1), ("D", 1)):
    bpy.ops.mesh.primitive_cone_add(vertices=4, radius1=0.04, depth=0.09, location=(s * 0.07, 0, 0.415),
                                    rotation=(0, math.radians(s * 12), math.radians(45)))
    o = bpy.context.active_object
    o.name = f"Mocha_Oreille_{cote}"
    o.data.materials.append(m_pel)
    ranger(o, C_MOCHA)
    o.parent = mocha
    contour(o, 0.003)
    # Regard : pupille (fente ou ronde) + reflet, sur un pivot qui permet de regarder ailleurs
    regard = bpy.data.objects.new(f"Mocha_Regard_{cote}", None)
    regard.empty_display_size = 0.01
    C_MOCHA.objects.link(regard)
    regard.parent = mocha
    regard.location = (s * 0.045, -0.1, 0.333)
    sphere(f"Mocha_Pupille_{cote}", 1.0, (0, 0, 0), (0.006, 0.003, 0.015), m_pupille, C_MOCHA, regard)
    sphere(f"Mocha_Reflet_{cote}", 1.0, (s * 0.045 + 0.008, -0.1035, 0.325), (0.0042, 0.0015, 0.0042), m_reflet, C_MOCHA, mocha)
    # Paupière mi-close (la signature de Mocha) — elle peut aussi s'incliner (colère, tristesse)
    contour(sphere(f"Mocha_Paupiere_{cote}", 1.0, (s * 0.045, -0.092, 0.343), (0.026, 0.013, 0.013), m_paup, C_MOCHA, mocha), 0.08)
    # Paupière basse (air satisfait / mesquin) : aplatie et invisible au repos
    bas = sphere(f"Mocha_Paupiere_Bas_{cote}", 1.0, (s * 0.045, -0.092, 0.312), (0.026, 0.013, 0.003), m_paup, C_MOCHA, mocha)
    contour(bas, 0.08)
    bas.scale = (0, 0, 0)
    # Petits sourcils (touffes plus foncées) : ils portent la moitié de l'émotion
    sphere(f"Mocha_Sourcil_{cote}", 1.0, (s * 0.048, -0.089, 0.372), (0.017, 0.004, 0.0045), m_fon, C_MOCHA, mocha)

courbe("Mocha_Queue", [(0.07, 0.06, 0.03), (0.17, 0.0, 0.05), (0.16, -0.02, 0.17), (0.12, -0.03, 0.2)], 0.014, m_pel, C_MOCHA, mocha)
sphere("Mocha_Queue_Bout", 0.016, (0.12, -0.03, 0.2), mat=m_fon, coll=C_MOCHA, parent=mocha)
sphere("Mocha_Goutte_Front", 1.0, (0, -0.08, 0.385), (0.012, 0.01, 0.018), m_fon, C_MOCHA, mocha)

# ---------------------------------------------------------------------------
# 4. Plateau : sol, lumières, caméras, références
# ---------------------------------------------------------------------------
bpy.ops.mesh.primitive_plane_add(size=4, location=(0, 0, 0))
sol = bpy.context.active_object
sol.name = "Sol"
sol.data.materials.append(materiau("Sol", COUL["sol"], 0.8))
ranger(sol, C_PLAT)

def lumiere(nom, type_, energie, loc, rot, taille=None):
    d = bpy.data.lights.new(nom, type_)
    d.energy = energie
    if taille:
        d.size = taille
    o = bpy.data.objects.new(nom, d)
    o.location, o.rotation_euler = loc, tuple(math.radians(a) for a in rot)
    C_PLAT.objects.link(o)
    return o

lumiere("Soleil", "SUN", 2.5, (1, -1, 2), (50, 0, 35))
lumiere("Lumiere_Douce", "AREA", 40, (-0.6, -0.8, 0.8), (60, 0, -35), taille=1.0)
lumiere("Contre_Jour", "AREA", 20, (0.3, 0.8, 0.7), (-60, 0, 160), taille=0.6)


def camera(nom, loc, cible, focale):
    d = bpy.data.cameras.new(nom)
    d.lens = focale
    o = bpy.data.objects.new(nom, d)
    o.location = loc
    C_PLAT.objects.link(o)
    t = o.constraints.new("TRACK_TO")
    t.target = cible
    t.track_axis = "TRACK_NEGATIVE_Z"
    t.up_axis = "UP_Y"
    return o

viseur_large = bpy.data.objects.new("Viseur_Large", None)
viseur_large.location = (0.16, 0.05, 0.19)
C_PLAT.objects.link(viseur_large)
cam_large = camera("CAM_LARGE", (0.16, -1.9, 0.32), viseur_large, 50)
cam_bip = camera("CAM_BIP", (0, -0.55, 0.2), bip, 50)
cam_bip.constraints[0].target = corps
cam_mocha = camera("CAM_MOCHA", (0.22, -0.75, 0.3), bpy.data.objects["Mocha_Tete"], 60)
sc.camera = cam_large

# Planches de référence (vue de face : touche 1 du pavé numérique)
reference("Ref_Bip", "bip-proportions.png", 1.0, 0.22, 0.21, 0.4, C_REF)
reference("Ref_Mocha", "mocha-proportions.png", 1.1, 0.45 + 0.3, 0.23, 0.6, C_REF)

# ---------------------------------------------------------------------------
# 4 bis. Style « studio » (tools/blender/style-studio.py) : mêmes noms d'objets, nouveau look
# ---------------------------------------------------------------------------
if STYLE == "studio":
    import runpy
    STUDIO = runpy.run_path(os.path.join(RACINE, "tools", "blender", "style-studio.py"))
    STUDIO["habiller_bip"]()
    STUDIO["habiller_mocha"]()
    STUDIO["reglages_image"](sc)

# ---------------------------------------------------------------------------
# 5. Démo : Bip avance, réfléchit, a une idée, est ravi (5 s)
# ---------------------------------------------------------------------------
if DEMO:
    for img, x, expr in ((1, -0.25, 0), (40, 0, 0), (60, 0, 7), (90, 0, 15), (105, 0, 9), (125, 0, 2)):
        bip.location.x = x
        bip.keyframe_insert("location", index=0, frame=img)
        bip["expression"] = expr
        bip.keyframe_insert('["expression"]', frame=img)
    # L'expression change d'un coup (interpolation « constante »), pas en fondu
    action = bip.animation_data.action
    try:  # Blender 4.4 et plus (actions à « slots »)
        from bpy_extras import anim_utils
        courbes = anim_utils.action_get_channelbag_for_slot(action, bip.animation_data.action_slot).fcurves
    except (ImportError, AttributeError):
        courbes = action.fcurves
    for fcurve in courbes:
        if fcurve.data_path == '["expression"]':
            for k in fcurve.keyframe_points:
                k.interpolation = "CONSTANT"
    bip["expression"] = 0

print("Bip & Mocha : scène prête.")
