"""
Bip & Mocha — style « studio » : le rendu doux et brillant des films d'animation 3D.

  - BIP : robot en plastique laqué bleu-vert, tête-écran arrondie posée sur un petit corps,
    oreilles rondes, antenne, bras articulés (accents orange, articulations bleu nuit) ;
  - MOCHA : chaton roux tigré à vrais poils (front en « M », museau et poitrail blancs), grands yeux verts,
    nez rose, grandes oreilles à touffes, moustaches ;
  - CUISINE : bois veiné, carrelage émaillé, façades à panneaux, métal chromé, plante, lumière de fenêtre ;
  - IMAGE : rendu AgX (couleurs « cinéma »), reflets et lumière indirecte en lancer de rayons,
    profondeur de champ (arrière-plan flou, effet « miniature »).

Les noms des objets animés (Bip, Bip_Corps, Bip_Bras_D, Mocha_Tete, Mocha_Paupiere_G…) ne changent pas :
les scripts d'épisode existants continuent de fonctionner.

Utilisé automatiquement par preparer-scene.py (personnages + image) et decor-cuisine.py (cuisine).
"""

import math

import bmesh
import bpy
from mathutils import Vector, geometry, noise

ECHELLE_YEUX_MOCHA = 1.55 # grands yeux (lus par outils_animation.yeux_mocha)
EPAULE_BIP = (0.075, 0.0, 0.095)  # articulation des bras (lue par les épisodes)


# ---------------------------------------------------------------------------
# Outils
# ---------------------------------------------------------------------------
def lin(h):
    h = h.lstrip("#")
    c = [int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    return tuple(x / 12.92 if x <= 0.04045 else ((x + 0.055) / 1.055) ** 2.4 for x in c) + (1.0,)


def _entree(bsdf, *noms):
    for n in noms:
        if n in bsdf.inputs:
            return bsdf.inputs[n]
    return None


def regler(m, couleur=None, rugosite=None, vernis=0.0, vernis_rug=0.08, metal=None, sheen=0.0,
           sss=0.0, emission=None, force=0.0):
    """Règle le Principled BSDF d'un matériau (créé si besoin)."""
    if isinstance(m, str):
        m = bpy.data.materials.get(m) or bpy.data.materials.new(m)
    m.use_nodes = True
    b = m.node_tree.nodes.get("Principled BSDF")
    if b is None:
        m.node_tree.nodes.clear()
        b = m.node_tree.nodes.new("ShaderNodeBsdfPrincipled")
        out = m.node_tree.nodes.new("ShaderNodeOutputMaterial")
        m.node_tree.links.new(b.outputs[0], out.inputs[0])
    if couleur is not None:
        c = lin(couleur) if isinstance(couleur, str) else couleur
        b.inputs["Base Color"].default_value = c
        m.diffuse_color = c
    if rugosite is not None:
        b.inputs["Roughness"].default_value = rugosite
    if metal is not None:
        b.inputs["Metallic"].default_value = metal
    for noms, v in ((("Coat Weight", "Clearcoat"), vernis), (("Coat Roughness", "Clearcoat Roughness"), vernis_rug),
                    (("Sheen Weight", "Sheen"), sheen), (("Subsurface Weight",), sss)):
        e = _entree(b, *noms)
        if e is not None:
            e.default_value = v
    if emission is not None:
        b.inputs["Emission Color"].default_value = lin(emission) if isinstance(emission, str) else emission
        b.inputs["Emission Strength"].default_value = force
    return m


def _ranger(o, modele):
    """Met l'objet o dans la (les) collection(s) de l'objet modèle."""
    for c in list(o.users_collection):
        c.objects.unlink(o)
    for c in (modele.users_collection or [bpy.context.scene.collection]):
        c.objects.link(o)


def _lisse(o):
    for p in o.data.polygons:
        p.use_smooth = True


def maillage_boite(dims, arrondi):
    """Boîte aux coins très arrondis (biseau + subdivision), dimensions réelles dans le maillage."""
    me = bpy.data.meshes.new("boite")
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    for v in bm.verts:
        v.co.x *= dims[0]
        v.co.y *= dims[1]
        v.co.z *= dims[2]
    bmesh.ops.bevel(bm, geom=list(bm.edges), offset=arrondi, segments=3, profile=0.5, affect="EDGES")
    bm.to_mesh(me)
    bm.free()
    return me


def boite(nom, dims, loc, mat, parent, arrondi=0.01, modele=None, obj=None):
    me = maillage_boite(dims, arrondi)
    if obj is None:
        obj = bpy.data.objects.get(nom) or bpy.data.objects.new(nom, me)
        _ranger(obj, modele or parent)
    obj.data = me
    obj.modifiers.clear()
    obj.parent = parent
    obj.location, obj.rotation_euler, obj.scale = loc, (0, 0, 0), (1, 1, 1)
    me.materials.append(mat)
    _lisse(obj)
    s = obj.modifiers.new("Lissage", "SUBSURF")
    s.levels = s.render_levels = 2
    return obj


def primitive(nom, quoi, loc, mat, parent, modele=None, rot=(0, 0, 0), ech=(1, 1, 1), lisser=True, **params):
    getattr(bpy.ops.mesh, f"primitive_{quoi}_add")(location=(0, 0, 0), **params)
    o = bpy.context.active_object
    ancien = bpy.data.objects.get(nom)
    if ancien and ancien != o:
        bpy.data.objects.remove(ancien, do_unlink=True)
    o.name = nom
    _ranger(o, modele or parent)
    o.parent = parent
    o.location, o.rotation_euler, o.scale = loc, rot, ech
    o.data.materials.append(mat)
    if lisser:
        _lisse(o)
    return o


def sans_contour(prefixes):
    for o in bpy.data.objects:
        if o.name.startswith(prefixes):
            for m in [m for m in o.modifiers if m.name == "Contour"]:
                o.modifiers.remove(m)


def remplacer_maillage(o, me):
    """Donne un nouveau maillage à un objet existant (ses animations sont conservées)."""
    o.data = me
    o.modifiers.clear()


# ---------------------------------------------------------------------------
# BIP
# ---------------------------------------------------------------------------
def habiller_bip():
    O = bpy.data.objects
    bip = O["Bip"]
    sans_contour(("Bip",))
    coque = regler("Bip_Corps", "#3FA19D", 0.32, vernis=0.7)
    marine = regler("Bip_Cadre", "#1E2836", 0.3, vernis=0.6)
    orange = regler("Bip_Accent", "#F28C38", 0.35, vernis=0.5)
    lumiere = regler("Bip_Voyant", "#BFEFFF", 0.2, emission="#BFEFFF", force=2.5)

    # Tête-écran (c'est Bip_Corps : la caméra « BIP » la vise)
    tete = boite("Bip_Corps", (0.2, 0.14, 0.15), (0, 0, 0.19), coque, bip, 0.035, obj=O["Bip_Corps"])
    boite("Bip_Ecran_Cadre", (0.172, 0.012, 0.13), (0, -0.068, 0.19), marine, bip, 0.012, obj=O["Bip_Ecran_Cadre"])
    ecran = O["Bip_Ecran"]
    ecran.location, ecran.scale = (0, -0.0748, 0.19), (0.15, 0.1125, 1)
    vitre_ecran(ecran.data.materials[0])
    for cote, s in (("G", -1), ("D", 1)):
        primitive(f"Bip_Oreille_{cote}", "cylinder", (s * 0.101, 0, 0.19), marine, bip, rot=(0, math.radians(90), 0),
                  vertices=40, radius=0.03, depth=0.022)
        primitive(f"Bip_Oreille_Point_{cote}", "cylinder", (s * 0.112, 0, 0.19), orange, bip,
                  rot=(0, math.radians(90), 0), vertices=32, radius=0.011, depth=0.006)
        biseau(O[f"Bip_Oreille_{cote}"], 0.006)
        biseau(O[f"Bip_Oreille_Point_{cote}"], 0.002)

    # Cou, corps, voyant de poitrine, roue
    primitive("Bip_Cou", "cylinder", (0, 0, 0.112), marine, bip, vertices=32, radius=0.032, depth=0.03)
    boite("Bip_Torse", (0.13, 0.1, 0.085), (0, 0, 0.07), coque, bip, 0.022)
    boite("Bip_Plastron", (0.072, 0.012, 0.05), (0, -0.047, 0.07), marine, bip, 0.008)
    primitive("Bip_Voyant", "cylinder", (0, -0.0535, 0.074), lumiere, bip, rot=(math.radians(90), 0, 0),
              vertices=40, radius=0.0145, depth=0.004)
    primitive("Bip_Bouton_Poitrine", "uv_sphere", (0, -0.053, 0.0545), orange, bip, segments=24, ring_count=12,
              radius=0.0045)
    roue = O["Bip_Roue"]
    roue.location, roue.scale = (0, 0, 0.026), (0.9, 0.9, 0.9)
    roue.data.materials[0] = marine

    # Antenne
    antenne = O["Bip_Antenne"]
    for p, co in zip(antenne.data.splines[0].bezier_points, ((0, 0, 0.255), (0, 0, 0.275), (0, 0, 0.295))):
        p.co = co
        p.handle_left_type = p.handle_right_type = "AUTO"
    antenne.data.bevel_depth = 0.0042
    antenne.data.materials[0] = marine
    boule = O["Bip_Antenne_Boule"]
    boule.location, boule.scale = (0, 0, 0.302), (1.05, 1.05, 1.05)

    # Bras : épaule (bleu nuit) → bras (coque) → bracelet orange → main (bleu nuit)
    ex, ey, ez = EPAULE_BIP
    for cote, s in (("G", -1), ("D", 1)):
        bras = O[f"Bip_Bras_{cote}"]
        pts = ((s * ex, ey, ez), (s * (ex + 0.012), 0, 0.066), (s * (ex + 0.01), 0, 0.04))
        for p, co in zip(bras.data.splines[0].bezier_points, pts):
            p.co = co
            p.handle_left_type = p.handle_right_type = "AUTO"
        bras.data.bevel_depth = 0.0105
        bras.data.materials[0] = coque
        main = O[f"Bip_Main_{cote}"]
        main.location, main.scale = (s * (ex + 0.01), 0, 0.03), (1.4, 1.4, 1.4)
        main.data.materials[0] = marine
        ep = primitive(f"Bip_Epaulette_{cote}", "uv_sphere", (s * ex, ey, ez), marine, bip, segments=32,
                       ring_count=16, radius=0.019)
        br = primitive(f"Bip_Bracelet_{cote}", "torus", (s * (ex + 0.0115), 0, 0.058), orange, bip,
                       major_radius=0.0115, minor_radius=0.0045, major_segments=32, minor_segments=12)
        for o in (ep, br):  # suivent le bras quand un épisode le fait pivoter
            m = o.matrix_world.copy()
            o.parent = bras
            o.matrix_world = m
    bip["epaule"] = EPAULE_BIP
    return tete


def biseau(o, largeur):
    b = o.modifiers.new("Arrondi", "BEVEL")
    b.width, b.segments = largeur, 3
    b.harden_normals = False


def vitre_ecran(m):
    """Ajoute un reflet de vitre sur l'écran de Bip (l'image reste l'atlas d'expressions)."""
    nt = m.node_tree
    if "Vitre" in nt.nodes:
        return
    sortie = next(n for n in nt.nodes if n.type == "OUTPUT_MATERIAL")
    emis = next(n for n in nt.nodes if n.type == "EMISSION")
    emis.inputs["Strength"].default_value = 2.2
    vitre = nt.nodes.new("ShaderNodeBsdfPrincipled")
    vitre.name = "Vitre"
    vitre.inputs["Base Color"].default_value = (0, 0, 0, 1)
    vitre.inputs["Roughness"].default_value = 0.12
    somme = nt.nodes.new("ShaderNodeAddShader")
    nt.links.new(emis.outputs[0], somme.inputs[0])
    nt.links.new(vitre.outputs[0], somme.inputs[1])
    nt.links.new(somme.outputs[0], sortie.inputs["Surface"])


# ---------------------------------------------------------------------------
# MOCHA
# ---------------------------------------------------------------------------
def _appliquer_echelle(o):
    for v in o.data.vertices:
        v.co.x *= o.scale.x
        v.co.y *= o.scale.y
        v.co.z *= o.scale.z
    o.scale = (1, 1, 1)


def _melange(nt, fac, a, b):
    """Mélange de deux couleurs (prises sur des sorties de nœuds) ; renvoie la sortie."""
    m = nt.nodes.new("ShaderNodeMix")
    m.data_type = "RGBA"
    nt.links.new(fac, m.inputs[0])
    nt.links.new(a, next(i for i in m.inputs if i.identifier == "A_Color"))
    nt.links.new(b, next(i for i in m.inputs if i.identifier == "B_Color"))
    return next(o for o in m.outputs if o.identifier == "Result_Color")


def _rampe(nt, entree, couleurs):
    """Rampe de couleurs [(position, "#hex"), …] branchée sur une valeur ; renvoie la sortie couleur."""
    r = nt.nodes.new("ShaderNodeValToRGB")
    els = r.color_ramp.elements
    while len(els) < len(couleurs):
        els.new(0.5)
    for e, (pos, c) in zip(els, couleurs):
        e.position, e.color = pos, lin(c)
    nt.links.new(entree, r.inputs[0])
    return r.outputs[0]


def _couleur_motif(nt, base, rayure, blanc):
    """Couleur de base → rayures tigrées (u de la carte « Motif ») → blanc (v)."""
    uv = nt.nodes.new("ShaderNodeUVMap")
    uv.uv_map = "Motif"
    sep = nt.nodes.new("ShaderNodeSeparateXYZ")
    nt.links.new(uv.outputs[0], sep.inputs[0])
    c = _melange(nt, sep.outputs["X"], base, rayure)
    return _melange(nt, sep.outputs["Y"], c, blanc)


# Robe de Mocha (chat roux tigré) : racine des poils → pointe
ROBE = {"base": ("#B4561C", "#F7A956"), "rayure": ("#7E3410", "#C4621E"), "blanc": ("#F2DEC4", "#FFFFFF")}


def mat_poils(nom, racine=None, pointe=None):
    """Poils : plus foncés à la racine, plus clairs à la pointe (donne le volume).
    Sans couleurs données : la robe tigrée de Mocha, peinte par la carte « Motif » de l'objet."""
    m = bpy.data.materials.get(nom) or bpy.data.materials.new(nom)
    m.use_nodes = True
    nt = m.node_tree
    nt.nodes.clear()
    info = nt.nodes.new("ShaderNodeHairInfo")
    t = info.outputs["Intercept"]

    def degrade(r, p):
        return _rampe(nt, t, [(0.0, r), (0.85, p)])

    if racine:
        couleur = degrade(racine, pointe)
    else:
        couleur = _couleur_motif(nt, degrade(*ROBE["base"]), degrade(*ROBE["rayure"]), degrade(*ROBE["blanc"]))
        racine, pointe = ROBE["base"]
    b = nt.nodes.new("ShaderNodeBsdfPrincipled")
    b.inputs["Roughness"].default_value = 0.5
    e = _entree(b, "Sheen Weight")
    if e is not None:
        e.default_value = 0.4
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    nt.links.new(couleur, b.inputs["Base Color"])
    nt.links.new(b.outputs[0], out.inputs[0])
    m.diffuse_color = lin(pointe)
    return m


def peau_tigree(nom):
    """Peau sous les poils : mêmes rayures et même blanc que le pelage (aucun trou visible)."""
    m = regler(nom, "#D98A48", 0.75, sheen=0.0)
    nt = m.node_tree
    b = nt.nodes["Principled BSDF"]
    if not b.inputs["Base Color"].is_linked:
        rgb = []
        for c in ("#D98A48", "#9C4A1C", "#F6EADB"):  # teinte moyenne des poils : les trous ne se voient pas
            n = nt.nodes.new("ShaderNodeRGB")
            n.outputs[0].default_value = lin(c)
            rgb.append(n.outputs[0])
        nt.links.new(_couleur_motif(nt, *rgb), b.inputs["Base Color"])
    return m


def fourrure(o, mat, longueur, nombre, enfants=12, masque=None, epaisseur=0.00032, couche=0.8):
    """Pelage en poils (particules « Hair »).
    masque(co) → 0..1 (densité et longueur) ou (densité, longueur) ; longueur = longueur maximale.
    couche : poils couchés le long de la peau, vers le « pôle sud » du maillage (comme un vrai pelage
    qui descend du crâne) ; 0 = poils dressés."""
    if o.particle_systems:
        return
    if masque:
        gd = o.vertex_groups.new(name="Poils")
        gl = o.vertex_groups.new(name="Poils_Longueur")
        for v in o.data.vertices:
            r = masque(v.co)
            d, lg = r if isinstance(r, tuple) else (r, r)
            gd.add([v.index], max(0.0, min(1.0, d)), "REPLACE")
            gl.add([v.index], max(0.0, min(1.0, lg)), "REPLACE")
    o.data.materials.append(mat)
    o.modifiers.new("Poils", "PARTICLE_SYSTEM")
    ps = o.particle_systems[-1]
    if masque:
        ps.vertex_group_density, ps.vertex_group_length = "Poils", "Poils_Longueur"
    s = ps.settings
    s.type = "HAIR"
    s.count = nombre
    s.use_advanced_hair = True
    s.material = len(o.data.materials)
    s.child_type = "INTERPOLATED"
    s.child_percent = 2
    s.rendered_child_count = enfants
    s.child_length = 1.0
    s.clump_factor = 0.35
    s.clump_shape = -0.1
    s.roughness_1 = 0.0008
    s.roughness_endpoint = 0.0006
    s.roughness_2 = 0.0003
    s.child_radius = 0.004
    s.root_radius = 1.0
    s.tip_radius = 0.0
    s.shape = -0.35  # pointes fines : effet duveteux
    s.radius_scale = epaisseur
    s.display_step, s.render_step = 2, 3
    s.length_random = 0.3
    s.use_hair_bspline = True
    s.hair_length = longueur  # en dernier : ce réglage fixe la vitesse « normale » des poils
    s.factor_random = s.normal_factor * 0.12  # un peu de désordre (en proportion de la longueur)
    if couche and o.data.uv_layers:
        o.data.uv_layers.active = o.data.uv_layers[0]  # la carte de la sphère donne le sens « vers le bas »
        s.tangent_factor = s.normal_factor * couche
        s.tangent_phase = SENS_POILS

    return ps


SENS_POILS = 0.75  # orientation des poils couchés sur la carte UV (fraction de tour) : vers le bas


def _lisser_doux(t):
    t = max(0.0, min(1.0, t))
    return t * t * (3 - 2 * t)


def _bande(t, largeur=0.36):
    """Rayures : 1 au milieu d'une bande sombre, 0 entre deux ; t compté en périodes."""
    seuil = math.cos(math.pi * largeur)
    return _lisser_doux((math.cos(2 * math.pi * t) - seuil) / 0.35 + 0.5)


def _bruit(co, frequence, ampleur):
    return noise.noise(co * frequence) * ampleur


def _densifier(o, niveaux=2):
    """Maillage plus fin (subdivision appliquée) : rayures nettes et poils bien répartis."""
    s = o.modifiers.new("Densifier", "SUBSURF")
    s.levels = niveaux
    dg = bpy.context.evaluated_depsgraph_get()
    me = bpy.data.meshes.new_from_object(o.evaluated_get(dg))
    o.modifiers.remove(s)
    o.data = me
    _lisse(o)


def _motif(o, fonction):
    """Carte « Motif » (u = rayure sombre, v = blanc, de 0 à 1), lue par la peau et les poils."""
    me = o.data
    if not me.uv_layers:
        me.uv_layers.new(name="UVMap")
    uv = me.uv_layers.get("Motif") or me.uv_layers.new(name="Motif")
    val = [fonction(v.co) for v in me.vertices]
    for l in me.loops:
        uv.data[l.index].uv = val[l.vertex_index]


def _prep(o, echelle=None, niveaux=2):
    """Pièce de Mocha prête pour les poils : échelle appliquée (en mètres), maillage fin."""
    if echelle:
        o.scale = echelle
    for m in list(o.modifiers):
        o.modifiers.remove(m)
    _densifier(o, niveaux)
    _appliquer_echelle(o)
    return o


def moustache(nom, points, rayon, mat, parent, modele):
    """Vibrisse : courbe fine qui s'effile jusqu'à la pointe."""
    cu = bpy.data.curves.new(nom, "CURVE")
    cu.dimensions = "3D"
    cu.bevel_depth = rayon
    cu.bevel_resolution = 1
    cu.resolution_u = 8
    sp = cu.splines.new("BEZIER")
    sp.bezier_points.add(len(points) - 1)
    for i, (bp, p) in enumerate(zip(sp.bezier_points, points)):
        bp.co = p
        bp.handle_left_type = bp.handle_right_type = "AUTO"
        bp.radius = 1.0 - 0.85 * i / (len(points) - 1)
    cu.materials.append(mat)
    o = bpy.data.objects.new(nom, cu)
    _ranger(o, modele)
    o.parent = parent
    return o


def habiller_mocha():
    """Mocha « chaton de cinéma » : pelage roux tigré (rayures en M sur le front, joues rayées),
    museau, menton et poitrail blancs, grands yeux verts, nez rose, grandes oreilles à touffes, moustaches."""
    O = bpy.data.objects
    mocha = O["Mocha"]
    k = ECHELLE_YEUX_MOCHA
    sans_contour(("Mocha",))
    pelage = peau_tigree("Mocha_Pelage")
    regler("Mocha_Fonce", ROBE["rayure"][1], 0.6, sheen=0.4)
    creme = regler("Mocha_Creme", ROBE["blanc"][1], 0.6, sheen=0.5, sss=0.05)
    paupiere = regler("Mocha_Paupiere", "#D27A34", 0.55, sheen=0.5)
    regler("Mocha_Pupille", "#050403", 0.5)  # mate : le vernis de l'œil suffit
    rose = regler("Mocha_Nez", "#E8837E", 0.38, vernis=0.35, sss=0.15)
    oreille_int = regler("Mocha_Oreille_Interieur", "#F0A69C", 0.6, sss=0.3)
    vibrisse = regler("Mocha_Moustache", "#FFFDF8", 0.3, sheen=0.2)
    poils = mat_poils("Mocha_Poils")
    poils_corps = mat_poils("Mocha_Poils_Corps")
    poils_queue = mat_poils("Mocha_Poils_Queue")
    poils_blancs = mat_poils("Mocha_Poils_Creme", *ROBE["blanc"])
    poils_paupiere = mat_poils("Mocha_Poils_Paupiere", *ROBE["base"])
    trait_paupiere(paupiere)

    corps, tete, ventre = O["Mocha_Corps"], O["Mocha_Tete"], O["Mocha_Ventre"]
    _prep(corps, (0.105, 0.095, 0.135))
    _prep(tete, (0.122, 0.104, 0.1), 3)
    _prep(ventre)
    museau = O["Mocha_Museau"]
    museau.location = (0, -0.088, 0.287)
    _prep(museau, (0.05, 0.033, 0.03))

    # Tête : joues plus larges (la bouille d'un chaton), crâne un peu plus plat
    for v in tete.data.vertices:
        nx, nz = v.co.x / 0.122, v.co.z / 0.1
        w = _lisser_doux((0.3 - nz) / 0.6) * _lisser_doux((abs(nx) - 0.25) / 0.55)
        v.co.x *= 1 + 0.09 * w
        if nz > 0:
            v.co.z *= 1 - 0.05 * nz * nz
    # Museau : deux coussinets de moustaches et un petit creux sous le nez
    for v in museau.data.vertices:
        nx = v.co.x / 0.05
        if v.co.y < 0:
            v.co.y *= 1 + 0.18 * math.exp(-((abs(nx) - 0.45) / 0.3) ** 2) - 0.08 * math.exp(-(nx / 0.15) ** 2)

    # Grands yeux. Tout l'œil vit dans l'espace de l'œil (sphère unité, aplatie par l'échelle de l'œil) :
    # pupille sur un pivot qui tourne (elle glisse sur la surface, l'iris la suit), reflet fixe,
    # paupières = demi-coques un peu plus grandes que l'œil qui pivotent pour se fermer.
    mocha["echelle_yeux"] = k
    mocha["yeux"] = "coques"
    mocha["pupille_ronde"] = True
    for cote, s in (("G", -1), ("D", 1)):
        oe = O[f"Mocha_Oeil_{cote}"]
        oe.location, oe.scale = (s * 0.054, -0.09, 0.333), (0.024 * k, 0.017, 0.02 * k)
        oe.rotation_euler = (0, 0, 0)
        regard = O[f"Mocha_Regard_{cote}"]
        regard.parent = oe
        regard.matrix_parent_inverse.identity()
        regard.location, regard.rotation_euler = (0, 0, 0), (0, 0, 0)
        oe.data.materials[0] = yeux_verts(f"Mocha_Yeux_{cote}", regard)
        pu = O[f"Mocha_Pupille_{cote}"]
        pu.parent = regard
        pu.matrix_parent_inverse.identity()
        pu.location, pu.scale = (0, -0.995, 0), (0.29, 0.03, 0.41)
        re = O[f"Mocha_Reflet_{cote}"]
        re.parent = oe
        re.matrix_parent_inverse.identity()
        re.location, re.scale = (0.34, -0.95, 0.4), (0.15, 0.03, 0.15)
        for nom, haut in ((f"Mocha_Paupiere_{cote}", True), (f"Mocha_Paupiere_Bas_{cote}", False)):
            bpy.data.objects.remove(O[nom], do_unlink=True)
            pa = demi_coque(nom, oe, haut, paupiere, corps)
            # Paupière en fourrure (poils courts : ils se fondent dans ceux du front quand l'œil s'ouvre)
            fourrure(pa, poils_paupiere, 0.0055, 1200 if haut else 500, enfants=16, epaisseur=0.0003,
                     masque=lambda co: (_lisser_doux((abs(co.z) - 0.12) / 0.25), 1.0))
            pa.modifiers.move(len(pa.modifiers) - 1, 0)  # poils sur la coque, avant l'épaisseur
        # Sourcil : une petite touffe plus foncée posée dans le pelage (elle bouge avec les expressions)
        so = O[f"Mocha_Sourcil_{cote}"]
        so.hide_render = True  # chaton : l'expression passe par les paupières (l'objet reste pour l'animation)
        # Grandes oreilles (cône lisse, intérieur rose, touffes blanches)
        ancienne = O[f"Mocha_Oreille_{cote}"]
        bpy.data.objects.remove(ancienne, do_unlink=True)
        o = primitive(f"Mocha_Oreille_{cote}", "cone", (s * 0.08, 0.004, 0.43), pelage, mocha, modele=corps,
                      rot=(math.radians(-10), math.radians(s * 20), 0), ech=(1, 0.5, 1),
                      vertices=40, radius1=0.06, radius2=0.004, depth=0.125)
        _densifier(o, 2)
        _appliquer_echelle(o)
        i = primitive(f"Mocha_Oreille_Int_{cote}", "cone", (0, -0.013, -0.01), oreille_int, o, modele=corps,
                      ech=(0.7, 0.42, 0.8), vertices=40, radius1=0.06, radius2=0.004, depth=0.125)
        _densifier(i, 2)
        _appliquer_echelle(i)
        fourrure(o, poils, 0.006, 500, enfants=10, masque=lambda co: (_lisser_doux((co.y + 0.004) / 0.012), 1.0))
        fourrure(i, poils_blancs, 0.03, 140, enfants=12,
                 masque=lambda co: (_lisser_doux(-co.y / 0.012) * _lisser_doux((0.01 - co.z) / 0.05),
                                    0.5 + 0.5 * _lisser_doux((-0.01 - co.z) / 0.04)), epaisseur=0.00022)

    primitive("Mocha_Nez", "uv_sphere", (0, -0.122, 0.305), rose, mocha, modele=corps, ech=(0.0125, 0.007, 0.0085),
              segments=24, ring_count=12, radius=1.0)
    nez = O["Mocha_Nez"]
    for v in nez.data.vertices:  # nez en triangle arrondi, pointe en bas
        v.co.x *= 1 - 0.35 * _lisser_doux(-v.co.z)
    gf = O["Mocha_Goutte_Front"]  # remplacée par le « M » rayé du front
    gf.hide_render = gf.hide_viewport = True

    # Queue : la courbe devient un maillage (pour porter des poils)
    q = O.get("Mocha_Queue")
    axe = []
    if q and q.type == "CURVE":
        sp = q.data.splines[0]
        for a, b in zip(sp.bezier_points[:-1], sp.bezier_points[1:]):
            axe += geometry.interpolate_bezier(a.co, a.handle_right, b.handle_left, b.co, 16)
        q.data.bevel_depth = 0.017
        q.data.bevel_resolution = 4
        q.data.resolution_u = 16
        dg = bpy.context.evaluated_depsgraph_get()
        me = bpy.data.meshes.new_from_object(q.evaluated_get(dg))
        nq = bpy.data.objects.new("Mocha_Queue_Poils", me)
        _ranger(nq, corps)
        nq.parent, nq.matrix_world = mocha, q.matrix_world.copy()
        _lisse(nq)
        q.hide_render = q.hide_viewport = True
        q.name = "Mocha_Queue_Courbe"
        nq.name = "Mocha_Queue"
        cumul = [0.0]
        for a, b in zip(axe[:-1], axe[1:]):
            cumul.append(cumul[-1] + (b - a).length)

        def anneaux(co):
            i = min(range(len(axe)), key=lambda j: (axe[j] - co).length_squared)
            return (_bande(cumul[i] / 0.045 + 0.3, 0.42), 0.0)

        _motif(nq, anneaux)
        fourrure(nq, poils_queue, 0.016, 1300, enfants=12)
    bout = O["Mocha_Queue_Bout"]
    bout.data.materials[0] = pelage
    _prep(bout, None, 1)
    _motif(bout, lambda co: (0.85, 0.0))
    fourrure(bout, poils_queue, 0.014, 160, enfants=12)

    # --- Motifs de la robe (coordonnées en mètres, centrées sur chaque pièce) ---
    def robe_tete(co):
        n = Vector((co.x / 0.122, co.y / 0.104, co.z / 0.1))
        b = _bruit(co, 40, 0.06)
        # « M » du front et rayures du crâne : bandes qui remontent vers l'arrière de la tête
        front = _lisser_doux((n.z - 0.32) / 0.2)
        x = co.x * (1 - 0.35 * _lisser_doux((-n.y - 0.2) / 0.5) * (n.z - 0.3)) + b * 0.03
        r = front * _bande(x / 0.034, 0.34) * (1 - _lisser_doux((abs(n.x) - 0.62) / 0.15))
        # joues : deux traits qui partent du coin de l'œil vers l'arrière
        joue = _lisser_doux((abs(n.x) - 0.6) / 0.15) * _lisser_doux((0.3 - n.z) / 0.15) * _lisser_doux((n.y + 0.8) / 0.3)
        r = max(r, joue * _bande((co.z + 0.006 + b * 0.02 + 0.05 * n.y) / 0.028, 0.3))
        # nuque
        nuque = _lisser_doux((n.y - 0.2) / 0.3) * _lisser_doux((0.4 - n.z) / 0.3)
        r = max(r, nuque * _bande((co.z + b * 0.03) / 0.03, 0.36))
        # blanc : menton, dessous des joues, tour du museau
        blanc = _lisser_doux((-n.y - 0.55) / 0.2) * _lisser_doux((-n.z - 0.3) / 0.2) * _lisser_doux((0.5 - abs(n.x)) / 0.2)
        blanc = max(blanc, 0.7 * _lisser_doux((-n.z - 0.75) / 0.15))
        return (r * (1 - blanc), blanc)

    def robe_corps(co):
        n = Vector((co.x / 0.105, co.y / 0.095, co.z / 0.135))
        b = _bruit(co, 30, 0.08)
        dos = _lisser_doux((n.y + 0.2) / 0.4)
        r = dos * _bande((co.z + 0.25 * abs(co.x) - 0.3 * co.y + b * 0.04) / 0.042, 0.4)
        blanc = 0.6 * _lisser_doux((-n.y - 0.6) / 0.25) * _lisser_doux((0.45 - abs(n.x)) / 0.25)
        return (r * (1 - blanc), blanc)

    _motif(tete, robe_tete)
    _motif(corps, robe_corps)
    _motif(ventre, lambda co: (0.0, 0.55 * _lisser_doux((0.07 - co.z) / 0.12)))  # poitrail clair, pas blanc
    _motif(museau, lambda co: (0.0, 1.0))

    # --- Pelage ---
    yeux = [Vector((s * 0.054, -0.08, 0.013)) for s in (-1, 1)]

    def masque_tete(co):
        n = Vector((co.x / 0.122, co.y / 0.104, co.z / 0.1))
        d = 1.0
        if co.y < 0:
            for e in yeux:  # rien sur les yeux : les poils s'arrêtent au bord des paupières
                r = math.hypot((co.x - e.x) / 0.028, (co.z - e.z) / 0.024)  # bord visible de l'œil (il est enfoncé)
                d = min(d, _lisser_doux((r - 1.0) / 0.12))
        if (co.x / 0.05) ** 2 + ((co.y + 0.078) / 0.03) ** 2 + ((co.z + 0.033) / 0.028) ** 2 < 1:
            d = 0.0  # caché sous le museau
        face = _lisser_doux((-n.y - 0.3) / 0.35) * _lisser_doux((0.75 - n.z) / 0.3)
        joue = _lisser_doux((abs(n.x) - 0.45) / 0.3) * _lisser_doux((0.35 - n.z) / 0.4)
        return d, 0.6 - 0.2 * face + 0.4 * joue

    def masque_corps(co):
        n = Vector((co.x / 0.105, co.y / 0.095, co.z / 0.135))
        return 1.0, 0.85 - 0.25 * _lisser_doux((-n.y - 0.5) / 0.3) + 0.15 * _lisser_doux((n.z - 0.6) / 0.3)

    def masque_museau(co):
        nez = math.hypot(co.x / 0.016, (co.z - 0.016) / 0.012)
        return (_lisser_doux((nez - 1.0) / 0.4) if co.y < 0 else 1.0), 1.0

    fourrure(tete, poils, 0.018, 7500, enfants=20, masque=masque_tete)
    fourrure(corps, poils_corps, 0.016, 4200, enfants=18, masque=masque_corps)
    fourrure(ventre, poils_corps, 0.012, 1300, enfants=14)
    fourrure(museau, poils_blancs, 0.0045, 1100, enfants=10, masque=masque_museau, epaisseur=0.00024)
    for cote in ("G", "D"):
        pa = _prep(O[f"Mocha_Patte_{cote}"], None, 1)
        pa.data.materials[0] = creme
        fourrure(pa, poils_blancs, 0.006, 260, enfants=12)

    # --- Moustaches : 4 de chaque côté du museau, 2 au-dessus de chaque œil ---
    for cote, s in (("G", -1), ("D", 1)):
        for j, (dz, long_, ecart) in enumerate(((0.008, 0.15, 0.03), (0.0, 0.165, 0.008),
                                                 (-0.008, 0.155, -0.014), (-0.015, 0.13, -0.035))):
            x0, y0, z0 = s * 0.03, -0.112, 0.291 + dz
            moustache(f"Mocha_Moustache_{cote}{j}",
                      [(x0, y0, z0), (x0 + s * long_ * 0.5, y0 + 0.012, z0 + ecart * 0.45 + 0.006),
                       (x0 + s * long_, y0 + 0.04, z0 + ecart - 0.008)], 0.00055, vibrisse, mocha, corps)
        for j, (dx, dz) in enumerate(((0.0, 0.0), (0.012, -0.004))):
            x0, y0, z0 = s * (0.045 + dx), -0.09, 0.372 + dz
            moustache(f"Mocha_Sourcil_Poil_{cote}{j}",
                      [(x0, y0, z0), (x0 + s * 0.03, y0 - 0.006, z0 + 0.03), (x0 + s * 0.06, y0 + 0.01, z0 + 0.05)],
                      0.0004, vibrisse, mocha, corps)
    return mocha


def trait_paupiere(m):
    """Paupière : pelage roux, bordée d'un trait sombre (le « liner » naturel des chats)."""
    nt = m.node_tree
    b = nt.nodes["Principled BSDF"]
    if b.inputs["Base Color"].is_linked:
        return
    coord = nt.nodes.new("ShaderNodeTexCoord")
    sep = nt.nodes.new("ShaderNodeSeparateXYZ")
    nt.links.new(coord.outputs["Object"], sep.inputs[0])
    absz = nt.nodes.new("ShaderNodeMath")
    absz.operation = "ABSOLUTE"
    nt.links.new(sep.outputs["Z"], absz.inputs[0])
    nt.links.new(_rampe(nt, absz.outputs[0], [(0.0, "#3A1C0C"), (0.16, "#4A2410"), (0.3, "#C96A26")]),
                 b.inputs["Base Color"])


def demi_coque(nom, oeil, haut, mat, modele):
    """Paupière : demi-sphère (haut ou bas) un peu plus grande que l'œil, enfant de l'œil."""
    bpy.ops.mesh.primitive_uv_sphere_add(segments=40, ring_count=20, radius=1.12)
    o = bpy.context.active_object
    o.name = nom
    bm = bmesh.new()
    bm.from_mesh(o.data)
    bmesh.ops.delete(bm, geom=[v for v in bm.verts if (v.co.z < -1e-4 if haut else v.co.z > 1e-4)], context="VERTS")
    bm.to_mesh(o.data)
    bm.free()
    _lisse(o)
    o.data.materials.append(mat)
    ep = o.modifiers.new("Epaisseur", "SOLIDIFY")
    ep.thickness, ep.offset = 0.08, 1.0  # épaisseur vers l'extérieur : rien ne traverse
    _ranger(o, modele)
    o.parent = oeil
    o.matrix_parent_inverse.identity()
    o.location, o.rotation_euler, o.scale = (0, 0, 0), (math.radians(90 if not haut else 0), 0, 0), (1, 1, 1)
    return o


def yeux_verts(nom, regard):
    """Œil de chaton : iris vert (doré autour de la pupille, cerclé de sombre), un peu de blanc au bord,
    sous un vernis très brillant. Le motif suit le pivot du regard : l'iris tourne avec la pupille."""
    m = bpy.data.materials.get(nom) or bpy.data.materials.new(nom)
    regler(m, None, 0.3, vernis=1.0, vernis_rug=0.015)
    nt = m.node_tree
    b = nt.nodes["Principled BSDF"]
    if b.inputs["Base Color"].is_linked:
        return m
    coord = nt.nodes.new("ShaderNodeTexCoord")
    coord.object = regard
    sep = nt.nodes.new("ShaderNodeSeparateXYZ")
    nt.links.new(coord.outputs["Object"], sep.inputs[0])
    xz = nt.nodes.new("ShaderNodeCombineXYZ")
    nt.links.new(sep.outputs["X"], xz.inputs[0])
    nt.links.new(sep.outputs["Z"], xz.inputs[2])
    rayon = nt.nodes.new("ShaderNodeVectorMath")
    rayon.operation = "LENGTH"
    nt.links.new(xz.outputs[0], rayon.inputs[0])
    # fibres de l'iris : un léger bruit radial
    fibres = nt.nodes.new("ShaderNodeTexNoise")
    fibres.inputs["Scale"].default_value = 18.0
    nt.links.new(coord.outputs["Object"], fibres.inputs["Vector"])
    r = nt.nodes.new("ShaderNodeMath")
    r.operation = "MULTIPLY_ADD"
    nt.links.new(fibres.outputs["Fac"], r.inputs[0])
    r.inputs[1].default_value = 0.08
    nt.links.new(rayon.outputs["Value"], r.inputs[2])
    couleur = _rampe(nt, r.outputs[0], [(0.0, "#F2D35A"), (0.36, "#D8C64C"), (0.5, "#9CC24E"), (0.66, "#6FA640"),
                                        (0.78, "#3F7A2C"), (0.84, "#1C2E12"), (0.885, "#E9E1D2"), (1.0, "#C9BBA6")])
    nt.links.new(couleur, b.inputs["Base Color"])
    m.diffuse_color = lin("#7FB246")
    return m


# ---------------------------------------------------------------------------
# CUISINE
# ---------------------------------------------------------------------------
def bois(m, clair="#D7A46E", fonce="#A8703F"):
    regler(m, None, 0.42, vernis=0.35, vernis_rug=0.15)
    nt = m.node_tree
    b = nt.nodes["Principled BSDF"]
    if b.inputs["Base Color"].is_linked:
        return m
    coord = nt.nodes.new("ShaderNodeTexCoord")
    etire = nt.nodes.new("ShaderNodeMapping")
    etire.inputs["Scale"].default_value = (1.0, 9.0, 1.0)
    nt.links.new(coord.outputs["Object"], etire.inputs[0])
    vague = nt.nodes.new("ShaderNodeTexWave")
    vague.wave_type = "RINGS"
    vague.inputs["Scale"].default_value = 3.0
    vague.inputs["Distortion"].default_value = 6.0
    vague.inputs["Detail"].default_value = 3.0
    nt.links.new(etire.outputs[0], vague.inputs["Vector"])
    rampe = nt.nodes.new("ShaderNodeValToRGB")
    rampe.color_ramp.elements[0].color = lin(fonce)
    rampe.color_ramp.elements[1].color = lin(clair)
    rampe.color_ramp.elements[0].position = 0.2
    nt.links.new(vague.outputs["Fac"], rampe.inputs[0])
    nt.links.new(rampe.outputs[0], b.inputs["Base Color"])
    relief = nt.nodes.new("ShaderNodeBump")
    relief.inputs["Strength"].default_value = 0.08
    relief.inputs["Distance"].default_value = 0.0005
    nt.links.new(vague.outputs["Fac"], relief.inputs["Height"])
    nt.links.new(relief.outputs[0], b.inputs["Normal"])
    return m


def nuances(m, ecart=0.06):
    """Chaque objet du matériau reçoit une teinte très légèrement différente (carrelage fait main)."""
    nt = m.node_tree
    b = nt.nodes["Principled BSDF"]
    if b.inputs["Base Color"].is_linked:
        return
    base = tuple(b.inputs["Base Color"].default_value)
    info = nt.nodes.new("ShaderNodeObjectInfo")
    rampe = nt.nodes.new("ShaderNodeValToRGB")
    rampe.color_ramp.elements[0].color = tuple(max(0, c * (1 - ecart)) for c in base[:3]) + (1,)
    rampe.color_ramp.elements[1].color = tuple(min(1, c * (1 + ecart)) for c in base[:3]) + (1,)
    nt.links.new(info.outputs["Random"], rampe.inputs[0])
    nt.links.new(rampe.outputs[0], b.inputs["Base Color"])


def platre(m):
    nt = m.node_tree
    b = nt.nodes["Principled BSDF"]
    if b.inputs["Normal"].is_linked:
        return
    bruit = nt.nodes.new("ShaderNodeTexNoise")
    bruit.inputs["Scale"].default_value = 60.0
    relief = nt.nodes.new("ShaderNodeBump")
    relief.inputs["Strength"].default_value = 0.05
    nt.links.new(bruit.outputs["Fac"], relief.inputs["Height"])
    nt.links.new(relief.outputs[0], b.inputs["Normal"])


def habiller_cuisine():
    O = bpy.data.objects
    M = bpy.data.materials
    if "Cuisine" not in bpy.data.collections:
        return
    coll = bpy.data.collections["Cuisine"]
    bois(M["Cuisine_Plan"])
    regler(M["Cuisine_Facade"], "#8FBFB2", 0.38, vernis=0.25)
    regler(M["Cuisine_Mur"], "#F3D9B8", 0.85)
    platre(M["Cuisine_Mur"])
    regler(M["Cuisine_Carreau"], "#B9DED5", 0.12, vernis=0.6, vernis_rug=0.04)
    nuances(M["Cuisine_Carreau"])
    regler(M["Cuisine_Joint"], "#F2E9DC", 0.9)
    regler(M["Cuisine_Machine"], "#E0483E", 0.28, vernis=0.9, vernis_rug=0.05)
    regler(M["Cuisine_Noir"], "#24282F", 0.35, vernis=0.4)
    regler(M["Cuisine_Chrome"], "#D9DEE5", 0.12, metal=1.0)
    regler(M["Cuisine_Tasse"], "#F4C542", 0.25, vernis=0.8, vernis_rug=0.04)
    regler(M["Cuisine_Horloge"], "#FBF7F1", 0.4, vernis=0.5)
    for i in range(4):
        if f"Bocal_{i}" in M:
            regler(M[f"Bocal_{i}"], None, 0.18, vernis=0.8, vernis_rug=0.03)
    if "Plante_Feuille" in M:
        regler(M["Plante_Feuille"], "#4E9A5C", 0.45, vernis=0.3, sss=0.15)
        regler(M["Plante_Pot"], "#C9734E", 0.55)

    # Façades : un panneau en relief par porte (plus de profondeur, plus « vrai »)
    facade = O.get("Facade_Placards")
    if facade and "Porte_0" not in O:
        panneau = regler("Cuisine_Panneau", "#9CCBBE", 0.38, vernis=0.25)
        for i, x in enumerate((-0.9, -0.3, 0.3, 0.9)):
            p = boite(f"Porte_{i}", (0.5, 0.012, 0.66), (x, -0.36, -0.5), panneau, None, 0.012, modele=facade)
            p.parent = None
    # Arêtes adoucies partout (les reflets dessinent les formes)
    for o in coll.objects:
        if o.type == "MESH" and not any(m.type == "BEVEL" for m in o.modifiers) and not o.name.startswith("Porte"):
            if o.name.startswith(("Mur", "Credence", "Facade", "Jointure", "Horloge_Repere")):
                continue
            biseau(o, 0.004)
    lumiere_fenetre()


def lumiere_fenetre():
    """Grande lumière chaude de fenêtre (gauche) + douce lumière de rebond froide (droite)."""
    coll = bpy.data.collections.get("Plateau") or bpy.context.scene.collection
    for nom, energie, couleur, loc, rot, taille in (
        ("Fenetre", 120, "#FFE2B8", (-1.4, -0.6, 1.3), (55, 0, -60), 1.4),
        ("Rebond", 18, "#CFE3FF", (1.3, -1.2, 0.5), (75, 0, 50), 1.5),
    ):
        if nom in bpy.data.objects:
            continue
        d = bpy.data.lights.new(nom, "AREA")
        d.energy, d.color, d.size = energie, lin(couleur)[:3], taille
        o = bpy.data.objects.new(nom, d)
        o.location, o.rotation_euler = loc, tuple(math.radians(a) for a in rot)
        coll.objects.link(o)


# ---------------------------------------------------------------------------
# IMAGE (à appeler une fois les caméras créées)
# ---------------------------------------------------------------------------
def reglages_image(scene=None):
    sc = scene or bpy.context.scene
    try:
        sc.view_settings.view_transform = "AgX"
        sc.view_settings.look = "AgX - Punchy"
    except TypeError:
        try:
            sc.view_settings.look = "Punchy"
        except TypeError:
            pass
    sc.view_settings.exposure = -0.2
    ee = sc.eevee
    if hasattr(ee, "use_raytracing"):  # Blender 4.2 et plus
        ee.use_raytracing = True
        ee.ray_tracing_method = "SCREEN"
        ee.use_fast_gi = True
        ee.fast_gi_method = "GLOBAL_ILLUMINATION"
        ee.ray_tracing_options.resolution_scale = "2"
        ee.ray_tracing_options.use_denoise = True
    if hasattr(sc.render, "hair_type"):
        sc.render.hair_type = "STRAND"
        sc.render.hair_subdiv = 1
    # Lumières de la scène : clé chaude, contre-jour légèrement froid (couleurs, pas les intensités)
    for nom, couleur in (("Soleil", "#FFE9C9"), ("Lumiere_Douce", "#FFF1E0"), ("Contre_Jour", "#DDEBFF")):
        o = bpy.data.objects.get(nom)
        if o:
            o.data.color = lin(couleur)[:3]
    finitions_accessoires()
    profondeur_de_champ(sc)


def finitions_accessoires():
    """Accessoires créés par les épisodes : sans contour, matières « studio »."""
    for o in bpy.data.objects:
        for m in [m for m in o.modifiers if m.name == "Contour"]:
            o.modifiers.remove(m)
    M = bpy.data.materials
    reglages = {
        "Mousse": dict(couleur="#FFFFFF", rugosite=0.6, sheen=0.3, sss=0.1),
        "Cafe": dict(rugosite=0.08, vernis=1.0, vernis_rug=0.02),
        "Vapeur": dict(rugosite=0.9, sss=0.4),
        "Boitier": dict(rugosite=0.4, vernis=0.5),
        "Bouton_Rouge": dict(rugosite=0.2, vernis=1.0, vernis_rug=0.03),
        "Mains_Peau": dict(rugosite=0.5, sss=0.25),
        "Mains_Manche": dict(rugosite=0.8, sheen=0.6),
        "Aspirateur": dict(rugosite=0.3, vernis=0.7),
    }
    for nom, r in reglages.items():
        if nom in M:
            regler(M[nom], **r)
    if "Mousse" in M:
        bulles(M["Mousse"])
    jambe = bpy.data.objects.get("Mocha_Jambe_D")  # patte tendue (épisode 06) : elle aussi a des poils
    if jambe and not jambe.particle_systems and "Mocha_Poils_Corps" in M:
        _appliquer_echelle(jambe)
        fourrure(jambe, M["Mocha_Poils_Corps"], 0.012, 500, enfants=14)


def bulles(m):
    """Petites bulles en relief sur la mousse."""
    nt = m.node_tree
    b = nt.nodes["Principled BSDF"]
    if b.inputs["Normal"].is_linked:
        return
    v = nt.nodes.new("ShaderNodeTexVoronoi")
    v.inputs["Scale"].default_value = 90.0
    relief = nt.nodes.new("ShaderNodeBump")
    relief.inputs["Strength"].default_value = 0.25
    relief.inputs["Distance"].default_value = 0.002
    nt.links.new(v.outputs["Distance"], relief.inputs["Height"])
    nt.links.new(relief.outputs[0], b.inputs["Normal"])


def profondeur_de_champ(sc=None, ouverture=4.0):
    """Arrière-plan légèrement flou : la mise au point suit la cible de chaque caméra."""
    for o in (sc or bpy.context.scene).objects:
        if o.type != "CAMERA":
            continue
        cible = next((c.target for c in o.constraints if c.type == "TRACK_TO" and c.target), None)
        if cible is None:
            continue
        o.data.dof.use_dof = True
        o.data.dof.focus_object = cible
        o.data.dof.aperture_fstop = ouverture * o.data.lens / 50
