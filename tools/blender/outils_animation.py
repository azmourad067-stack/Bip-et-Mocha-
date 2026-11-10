"""
Bip & Mocha — outils d'animation communs à tous les épisodes.

Dans un script d'épisode (après tools/blender/preparer-scene.py) :
    A = types.SimpleNamespace(**runpy.run_path(os.path.join(OUTILS, "outils_animation.py")))
    A.initialiser(collection_episode)
    A.cle(bip, "location", 120, (0, 0, 0))
    A.expr(140, "joie")

Toutes les fonctions travaillent sur la scène courante et sur les objets créés par
preparer-scene.py (« Bip », « Bip_Ecran », « Mocha », « Mocha_Paupiere_G/D »…).
"""

import math
import os
import random
import runpy
import sys

import bpy

EXPRESSIONS = ("neutre", "joie", "tres-joyeux", "triste", "pleure", "colere", "surprise", "question", "exclamation",
               "idee", "amour", "panique", "veille", "batterie-faible", "erreur", "chargement", "clin-oeil",
               "determine")
EXPR = {n: i for i, n in enumerate(EXPRESSIONS)}
FPS = 30

_etat = {"coll": None}


def initialiser(coll):
    """Collection où ranger les objets créés par l'épisode."""
    _etat["coll"] = coll


def ranger(o):
    if _etat["coll"] is None:
        return o
    for c in list(o.users_collection):
        c.objects.unlink(o)
    _etat["coll"].objects.link(o)
    return o


# ---------------------------------------------------------------------------
# Matériaux et formes simples
# ---------------------------------------------------------------------------
def lin(h):
    h = h.lstrip("#")
    c = [int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    return tuple(x / 12.92 if x <= 0.04045 else ((x + 0.055) / 1.055) ** 2.4 for x in c) + (1.0,)


def mat(nom, hexa, rug=0.4, emission=0.0):
    m = bpy.data.materials.new(nom)
    m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = lin(hexa)
    b.inputs["Roughness"].default_value = rug
    if emission:
        b.inputs["Emission Color"].default_value = lin(hexa)
        b.inputs["Emission Strength"].default_value = emission
    m.diffuse_color = lin(hexa)
    return m


def lisse(o):
    for p in o.data.polygons:
        p.use_smooth = True
    return o


def sphere(nom, r, loc, m, parent=None, ech=(1, 1, 1), seg=24):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=seg, ring_count=seg // 2, radius=r, location=loc)
    o = bpy.context.active_object
    o.name, o.scale = nom, ech
    o.data.materials.append(m)
    lisse(ranger(o))
    if parent:
        o.parent = parent
    return o


def boite(nom, dims, loc, m, parent=None, arrondi=0.0):
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc)
    o = bpy.context.active_object
    o.name, o.scale = nom, dims
    o.data.materials.append(m)
    if arrondi:
        b = o.modifiers.new("Arrondi", "BEVEL")
        b.width, b.segments, b.affect = arrondi, 4, "EDGES"
    ranger(o)
    if parent:
        o.parent = parent
    return o


def cylindre(nom, r, h, loc, m, parent=None, rot=(0, 0, 0), sommets=32):
    bpy.ops.mesh.primitive_cylinder_add(vertices=sommets, radius=r, depth=h, location=loc, rotation=rot)
    o = bpy.context.active_object
    o.name = nom
    o.data.materials.append(m)
    lisse(ranger(o))
    if parent:
        o.parent = parent
    return o


def vide(nom, loc=(0, 0, 0), parent=None):
    o = bpy.data.objects.new(nom, None)
    o.location = loc
    (_etat["coll"] or bpy.context.scene.collection).objects.link(o)
    if parent:
        o.parent = parent
    return o


def contour(o, ep):
    """Contour cartoon (coque inversée), même matériau « Contour » que les personnages."""
    o.data.materials.append(bpy.data.materials["Contour"])
    md = o.modifiers.new("Contour", "SOLIDIFY")
    md.thickness, md.offset, md.use_flip_normals, md.use_rim = ep, 1.0, True, False
    md.material_offset = len(o.data.materials) - 1


def pivot(nom, enfants, loc, parent):
    """Crée un point de rotation (épaule…) et y rattache des objets sans les déplacer."""
    p = vide(nom, loc, parent)
    bpy.context.view_layer.update()
    for e in enfants:
        m = e.matrix_world.copy()
        e.parent = p
        e.matrix_world = m
    return p


# ---------------------------------------------------------------------------
# Images clés
# ---------------------------------------------------------------------------
def courbes(obj):
    a = obj.animation_data.action
    try:
        from bpy_extras import anim_utils
        return anim_utils.action_get_channelbag_for_slot(a, obj.animation_data.action_slot).fcurves
    except (ImportError, AttributeError):
        return a.fcurves


def cle(obj, chemin, f, val, index=-1):
    """Pose une image clé : cle(bip, 'location', 120, (x, y, z)) ou cle(lampe.data, 'energy', 10, 5.0)."""
    if chemin.startswith('["'):
        obj[chemin[2:-2]] = val
        obj.keyframe_insert(chemin, frame=f)
        return
    if isinstance(val, (int, float)) and index < 0:
        setattr(obj, chemin, val)
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
    """Changement instantané (coupe) : « avant » jusqu'à f-1, « apres » à partir de f."""
    cle(obj, chemin, f - 1, avant)
    cle(obj, chemin, f, apres)


def pos(obj, f, x=None, y=None, z=None):
    v = list(obj.location)
    for i, val in enumerate((x, y, z)):
        if val is not None:
            v[i] = val
    cle(obj, "location", f, tuple(v))


def rot(obj, f, x=None, y=None, z=None):
    """Rotation en degrés ; les axes non donnés gardent leur valeur actuelle."""
    r = list(obj.rotation_euler)
    for i, val in enumerate((x, y, z)):
        if val is not None:
            r[i] = math.radians(val)
    cle(obj, "rotation_euler", f, tuple(r))


def rotz(obj, f, degres):
    rot(obj, f, z=degres)


def ech(obj, f, sx, sy=None, sz=None):
    cle(obj, "scale", f, (sx, sx if sy is None else sy, sx if sz is None else sz))


def visible(obj, f, oui):
    obj.hide_render = not oui
    obj.keyframe_insert("hide_render", frame=f)


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


# ---------------------------------------------------------------------------
# Personnages
# ---------------------------------------------------------------------------
def expr(f, nom, clignement=True):
    """Change l'écran de Bip, avec un micro-clignotement (2 images en veille) avant."""
    bip = bpy.data.objects["Bip"]
    if clignement and f > 3:
        cle(bip, '["expression"]', f - 2, EXPR["veille"])
    cle(bip, '["expression"]', f, EXPR[nom])


def finir_expressions():
    constantes(bpy.data.objects["Bip"], '["expression"]')


# Les yeux de Mocha. Pour chaque œil (bords mesurés sur l'œil : -1 = en bas, 0 = au milieu, +1 = en haut) :
#   haut     = (bord de la paupière haute, inclinaison en °) — inclinaison + = coin intérieur bas (colère),
#              - = coin intérieur haut (tristesse). -1.1 = œil fermé.
#   bas      = bord de la paupière basse (-1 = invisible ; plus haut = regard plissé, satisfait)
#   pupille  = largeur, hauteur (fente fine = agacé, ronde et grande = surpris / attendri)
#   sourcil  = montée en m, inclinaison en ° (même convention que la paupière)
#   reflet   = le petit point de lumière (False quand l'œil est fermé)
YEUX_MOCHA = {
    "mi-clos": dict(haut=(-0.25, 0), bas=-1, pupille=(0.006, 0.015), sourcil=(0, 0)),
    "fermes": dict(haut=(-1.15, 0), bas=-0.7, pupille=(0.006, 0.015), sourcil=(-0.003, 0), reflet=False),
    "ouverts": dict(haut=(0.8, 0), bas=-1, pupille=(0.012, 0.016), sourcil=(0.012, -8)),
    "agace": dict(haut=(-0.35, 16), bas=-0.65, pupille=(0.0035, 0.014), sourcil=(-0.004, 28)),
    "triste": dict(haut=(-0.05, -14), bas=-1, pupille=(0.011, 0.015), sourcil=(0.006, -25)),
    "content": dict(haut=(-0.4, -4), bas=-0.45, pupille=(0.006, 0.015), sourcil=(0.002, -6)),
    "attendri": dict(haut=(0.5, -6), bas=-0.8, pupille=(0.015, 0.017), sourcil=(0.008, -12)),
    "mefiant": {"G": dict(haut=(-0.5, 10), bas=-0.55, pupille=(0.004, 0.014), sourcil=(-0.004, 20)),
                "D": dict(haut=(0.45, -4), bas=-1, pupille=(0.005, 0.015), sourcil=(0.01, -10))},
}
_OEIL = (0.02, 0.022)  # demi-hauteur de l'œil, marge des paupières au-delà de l'œil


def _base(o):
    """Position de repos d'un objet, mémorisée au premier appel."""
    if "base" not in o:
        o["base"] = tuple(o.location)
    return o["base"]


def yeux_mocha(f, etat, cote=None, regard=(0, 0)):
    """Expression des yeux de Mocha (voir YEUX_MOCHA) : mi-clos (défaut), fermes, ouverts, agace,
    triste, content, attendri, mefiant. cote = "G" ou "D" pour un seul œil.
    regard = (gauche/droite, bas/haut) de -1 à 1 : où regardent les pupilles (0, 0 = droit devant).
    Les tailles suivent la propriété « echelle_yeux » de Mocha (grands yeux du style studio)."""
    O = bpy.data.objects
    if "Mocha" in O and O["Mocha"].get("yeux") == "coques":
        return _yeux_coques(f, etat, cote, regard)
    k = O["Mocha"].get("echelle_yeux", 1.0) if "Mocha" in O else 1.0
    oeil_h, marge_p = _OEIL[0] * k, _OEIL[1] * k
    lx_p, ly_p = 0.026 * k, (0.0145 if k > 1 else 0.013)
    for c in ((cote,) if cote else ("G", "D")):
        e = YEUX_MOCHA[etat]
        e = e.get(c, e) if "G" in e else e
        sens = 1 if c == "G" else -1  # même inclinaison = expression symétrique sur les deux yeux
        bord, incl = e["haut"]
        p = O[f"Mocha_Paupiere_{c}"]
        x, y, z = _base(p)
        centre_oeil = O[f"Mocha_Oeil_{c}"].location.z
        haut, bas = centre_oeil + marge_p, centre_oeil + bord * oeil_h
        cle(p, "location", f, (x, y, (haut + bas) / 2))
        cle(p, "scale", f, (lx_p, ly_p, max(0.001, (haut - bas) / 2)))
        rot(p, f, y=sens * incl)
        if f"Mocha_Paupiere_Bas_{c}" not in O:
            continue  # ancien modèle (sans pupilles ni sourcils)
        b = O[f"Mocha_Paupiere_Bas_{c}"]
        x, y, z = _base(b)
        bas, haut = centre_oeil - marge_p, centre_oeil + e["bas"] * oeil_h
        cle(b, "location", f, (x, y, (haut + bas) / 2))
        cle(b, "scale", f, (lx_p, ly_p, (haut - bas) / 2) if e["bas"] > -0.95 else (0, 0, 0))
        lx, lz = e["pupille"]
        pu = O[f"Mocha_Pupille_{c}"]
        cle(pu, "scale", f, (lx * k, 0.003, lz * k))
        r = O[f"Mocha_Regard_{c}"]
        x, y, z = _base(r)
        marge = max(0.003, 0.021 - lx) * k
        cle(r, "location", f, (x + regard[0] * marge, y, z + regard[1] * 0.006 * k))
        dzs, incls = e["sourcil"]
        s = O[f"Mocha_Sourcil_{c}"]
        x, y, z = _base(s)
        cle(s, "location", f, (x, y, z + dzs * k))
        rot(s, f, y=sens * incls)
        ref = O[f"Mocha_Reflet_{c}"]
        cle(ref, "scale", f, (0.0042 * k, 0.0015, 0.0042 * k) if e.get("reflet", True) else (0, 0, 0))


def _angle_paupiere(bord):
    """Bord de paupière (-1 bas de l'œil … 1 haut) → rotation de la demi-coque (degrés)."""
    if bord < -1:
        return min(105.0, 90.0 + (-bord - 1) * 60)
    return -math.degrees(math.asin(max(-1.0, min(0.98, bord))))


def _yeux_coques(f, etat, cote, regard):
    """Yeux du style studio : paupières en demi-coques qui pivotent, pupille qui glisse sur l'œil."""
    O = bpy.data.objects
    k = O["Mocha"].get("echelle_yeux", 1.0)
    for c in ((cote,) if cote else ("G", "D")):
        e = YEUX_MOCHA[etat]
        e = e.get(c, e) if "G" in e else e
        sens = 1 if c == "G" else -1
        bord, incl = e["haut"]
        rot(O[f"Mocha_Paupiere_{c}"], f, x=_angle_paupiere(bord), y=sens * incl)
        rot(O[f"Mocha_Paupiere_Bas_{c}"], f, x=_angle_paupiere(e["bas"]) if e["bas"] > -0.95 else 95)
        lx, lz = e["pupille"]
        if O["Mocha"].get("pupille_ronde"):  # chaton : pupille ronde, en fente seulement quand il est agacé
            sx = min(0.5, 0.06 + lx / 0.024 * 0.9)
            cle(O[f"Mocha_Pupille_{c}"], "scale", f, (sx, 0.03, max(lz / 0.02 * 0.55, 1.19 * sx)))
        else:
            cle(O[f"Mocha_Pupille_{c}"], "scale", f, (lx / 0.024 * 0.72, 0.03, lz / 0.02 * 0.7))
        rot(O[f"Mocha_Regard_{c}"], f, x=-regard[1] * 25, z=regard[0] * 35)
        dzs, incls = e["sourcil"]
        s = O[f"Mocha_Sourcil_{c}"]
        x, y, z = _base(s)
        cle(s, "location", f, (x, y, z + dzs * k))
        rot(s, f, y=sens * incls)
        cle(O[f"Mocha_Reflet_{c}"], "scale", f, (0.17, 0.03, 0.17) if e.get("reflet", True) else (0, 0, 0))


# ---------------------------------------------------------------------------
# Caméras et plans
# ---------------------------------------------------------------------------
def camera(nom, loc, focale, cible=None, suivre=None):
    if nom in bpy.data.objects:
        bpy.data.objects.remove(bpy.data.objects[nom], do_unlink=True)
    c = bpy.data.objects.new(nom, bpy.data.cameras.new(nom))
    c.data.lens = focale
    c.location = loc
    (_etat["coll"] or bpy.context.scene.collection).objects.link(c)
    if suivre:
        cl = c.constraints.new("COPY_LOCATION")
        cl.target, cl.use_z, cl.use_offset = suivre, False, True
    if cible:
        t = c.constraints.new("TRACK_TO")
        t.target, t.track_axis, t.up_axis = cible, "TRACK_NEGATIVE_Z", "UP_Y"
    return c


def plans(liste, cameras):
    """liste = [(image de début, "NOM"), …] → marqueurs de la timeline liés aux caméras."""
    sc = bpy.context.scene
    sc.timeline_markers.clear()
    for f, nom in liste:
        m = sc.timeline_markers.new(f"{nom}_{(f - 1) // FPS:02d}s", frame=f)
        m.camera = cameras[nom]
    sc.camera = cameras[liste[0][1]]


# ---------------------------------------------------------------------------
# Rendu
# ---------------------------------------------------------------------------
def regler_rendu(echantillons=4, rayons_ombre=4, debruitage=True):
    """EEVEE propre et rapide : 4 passes + 4 rayons d'ombre + débruiteur OpenImageDenoise."""
    sc = bpy.context.scene
    sc.eevee.taa_render_samples = echantillons
    if hasattr(sc.eevee, "shadow_ray_count"):  # Blender 4.2 et plus
        sc.eevee.shadow_ray_count = rayons_ombre  # supprime le grain des ombres douces
    sc.render.image_settings.file_format = "PNG"
    style = os.path.join(os.path.dirname(os.path.abspath(__file__)), "style-studio.py") if "__file__" in globals() else ""
    if bpy.data.objects.get("Bip_Torse") and os.path.isfile(style):  # personnages au style studio
        runpy.run_path(style)["reglages_image"](sc)
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


def ligne_de_commande():
    """Options après « -- » :
    --rendu DOSSIER [--debut a --fin b]   rendu des images PNG (reprenable)
    --images 1,140 --controle DOSSIER     rendus de contrôle
    --pourcentage 100 --echantillons 4 --ombres 4 --sans-debruitage
    --pas 2                               une image sur 2 (aperçu deux fois plus rapide, 15 im/s)
    --apercu                              brouillon rapide : 1 poil sur 10, pas de lancer de rayons
    --enregistrer fichier.blend
    """
    if "--" not in sys.argv:
        regler_rendu()
        return
    args = sys.argv[sys.argv.index("--") + 1:]

    def arg(nom, defaut):
        return type(defaut)(args[args.index(nom) + 1]) if nom in args else defaut

    sc = bpy.context.scene
    regler_rendu(arg("--echantillons", 4), arg("--ombres", 4), "--sans-debruitage" not in args)
    sc.render.resolution_percentage = arg("--pourcentage", 100)
    if "--apercu" in args:  # pour relire le rythme d'un épisode, pas pour publier
        sc.render.use_simplify = True
        sc.render.simplify_child_particles_render = 0.1
        if hasattr(sc.eevee, "use_raytracing"):
            sc.eevee.use_raytracing = False
    dossier = arg("--rendu", "")
    if dossier:
        sc.frame_start, sc.frame_end = arg("--debut", sc.frame_start), arg("--fin", sc.frame_end)
        sc.frame_step = arg("--pas", 1)
        sc.render.filepath = os.path.join(dossier, "")
        sc.render.use_overwrite = False  # reprise possible : les images déjà rendues sont gardées
        sc.render.use_placeholder = True
        bpy.ops.render.render(animation=True)
    if "--images" in args:
        dossier = arg("--controle", ".")
        for f in [int(x) for x in arg("--images", "1").split(",")]:
            sc.frame_set(f)
            sc.render.filepath = os.path.join(dossier, f"controle_{f:04d}.png")
            bpy.ops.render.render(write_still=True)
    if "--enregistrer" in args:
        bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(arg("--enregistrer", "episode.blend")))
