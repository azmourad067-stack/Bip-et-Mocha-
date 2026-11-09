"""
Bip & Mocha — style « studio » : le rendu doux et brillant des films d'animation 3D.

  - BIP : robot en plastique laqué bleu-vert, tête-écran arrondie posée sur un petit corps,
    oreilles rondes, antenne, bras articulés (accents orange, articulations bleu nuit) ;
  - MOCHA : vrai pelage (poils), grands yeux brillants à iris dégradé, nez rose, oreilles douces ;
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


def mat_poils(nom, racine, pointe):
    """Poils : plus foncés à la racine, plus clairs à la pointe (donne le volume)."""
    m = bpy.data.materials.get(nom) or bpy.data.materials.new(nom)
    m.use_nodes = True
    nt = m.node_tree
    nt.nodes.clear()
    info = nt.nodes.new("ShaderNodeHairInfo")
    rampe = nt.nodes.new("ShaderNodeValToRGB")
    rampe.color_ramp.elements[0].color = lin(racine)
    rampe.color_ramp.elements[1].color = lin(pointe)
    rampe.color_ramp.elements[1].position = 0.85
    b = nt.nodes.new("ShaderNodeBsdfPrincipled")
    b.inputs["Roughness"].default_value = 0.55
    e = _entree(b, "Sheen Weight")
    if e is not None:
        e.default_value = 0.4
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    nt.links.new(info.outputs["Intercept"], rampe.inputs[0])
    nt.links.new(rampe.outputs[0], b.inputs["Base Color"])
    nt.links.new(b.outputs[0], out.inputs[0])
    m.diffuse_color = lin(pointe)
    return m


def fourrure(o, mat, longueur, nombre, enfants=12, masque=None, epaisseur=0.00038):
    """Pelage en poils (particules « Hair ») ; masque(co) → 0..1 règle densité et longueur."""
    if o.particle_systems:
        return
    if masque:
        g = o.vertex_groups.new(name="Poils")
        for v in o.data.vertices:
            g.add([v.index], max(0.0, min(1.0, masque(v.co))), "REPLACE")
    o.data.materials.append(mat)
    o.modifiers.new("Poils", "PARTICLE_SYSTEM")
    ps = o.particle_systems[-1]
    if masque:
        ps.vertex_group_density = ps.vertex_group_length = "Poils"
    s = ps.settings
    s.type = "HAIR"
    s.count = nombre
    s.use_advanced_hair = True
    s.material = len(o.data.materials)
    s.child_type = "INTERPOLATED"
    s.child_percent = 2
    s.rendered_child_count = enfants
    s.child_length = 1.0
    s.clump_factor = 0.55
    s.clump_shape = -0.3
    s.kink = "CURL"
    s.kink_amplitude = 0.0015
    s.kink_frequency = 1.5
    s.roughness_1 = 0.0025
    s.roughness_endpoint = 0.002
    s.roughness_2 = 0.001
    s.child_radius = 0.004
    s.root_radius = 1.0
    s.tip_radius = 0.0
    s.shape = -0.25  # pointes fines : effet duveteux
    s.radius_scale = epaisseur
    s.display_step, s.render_step = 2, 3
    s.length_random = 0.35
    s.use_hair_bspline = True
    s.hair_length = longueur  # en dernier : ce réglage fixe la vitesse « normale » des poils
    s.factor_random = s.normal_factor * 0.2  # un peu de désordre (en proportion de la longueur)


def _lisser_doux(t):
    t = max(0.0, min(1.0, t))
    return t * t * (3 - 2 * t)


def habiller_mocha():
    O = bpy.data.objects
    mocha = O["Mocha"]
    k = ECHELLE_YEUX_MOCHA
    sans_contour(("Mocha",))
    pelage = regler("Mocha_Pelage", "#B98A5C", 0.6, sheen=0.5)
    fonce = regler("Mocha_Fonce", "#6E4428", 0.6, sheen=0.4)
    creme = regler("Mocha_Creme", "#F1DEC4", 0.6, sheen=0.5, sss=0.05)
    regler("Mocha_Paupiere", "#A0724B", 0.6, sheen=0.5)  # même peau que le visage
    regler("Mocha_Pupille", "#120C09", 0.25, vernis=1.0, vernis_rug=0.03)
    rose = regler("Mocha_Nez", "#D9827C", 0.35, vernis=0.4)
    oreille_int = regler("Mocha_Oreille_Interieur", "#E9A79B", 0.6, sss=0.2)
    yeux_brillants(bpy.data.materials["Mocha_Yeux"])

    # Formes un peu plus rondes, échelle « appliquée » (les poils poussent alors à la bonne taille)
    corps, tete, ventre = O["Mocha_Corps"], O["Mocha_Tete"], O["Mocha_Ventre"]
    corps.scale = (0.105, 0.095, 0.135)
    tete.scale = (0.122, 0.104, 0.1)
    for o in (corps, tete, ventre, O["Mocha_Queue_Bout"]):
        _appliquer_echelle(o)
        if not any(m.type == "SUBSURF" for m in o.modifiers):
            s = o.modifiers.new("Lissage", "SUBSURF")
            s.levels = s.render_levels = 1

    # Grands yeux. Tout l'œil vit dans l'espace de l'œil (sphère unité, aplatie par l'échelle de l'œil) :
    # pupille sur un pivot qui tourne (elle glisse sur la surface), reflet fixe,
    # paupières = demi-coques un peu plus grandes que l'œil qui pivotent pour se fermer.
    mocha["echelle_yeux"] = k
    mocha["yeux"] = "coques"
    for cote, s in (("G", -1), ("D", 1)):
        oe = O[f"Mocha_Oeil_{cote}"]
        oe.location, oe.scale = (s * 0.054, -0.09, 0.333), (0.024 * k, 0.017, 0.02 * k)
        oe.rotation_euler = (0, 0, 0)
        regard = O[f"Mocha_Regard_{cote}"]
        regard.parent = oe
        regard.matrix_parent_inverse.identity()
        regard.location, regard.rotation_euler = (0, 0, 0), (0, 0, 0)
        pu = O[f"Mocha_Pupille_{cote}"]
        pu.parent = regard
        pu.matrix_parent_inverse.identity()
        pu.location, pu.scale = (0, -0.995, 0), (0.18, 0.03, 0.52)
        re = O[f"Mocha_Reflet_{cote}"]
        re.parent = oe
        re.matrix_parent_inverse.identity()
        re.location, re.scale = (0.36, -0.95, 0.42), (0.17, 0.03, 0.17)
        for nom, haut in ((f"Mocha_Paupiere_{cote}", True), (f"Mocha_Paupiere_Bas_{cote}", False)):
            bpy.data.objects.remove(O[nom], do_unlink=True)
            demi_coque(nom, oe, haut, bpy.data.materials["Mocha_Paupiere"], corps)
        so = O[f"Mocha_Sourcil_{cote}"]
        so.location = (s * 0.058, -0.092, 0.381)
        so.scale = (0.019, 0.005, 0.005)
        # Oreilles douces (cône lisse + intérieur rose) à la place des pyramides
        ancienne = O[f"Mocha_Oreille_{cote}"]
        loc = (s * 0.075, 0.0, 0.425)
        bpy.data.objects.remove(ancienne, do_unlink=True)
        o = primitive(f"Mocha_Oreille_{cote}", "cone", loc, pelage, mocha, modele=corps,
                      rot=(math.radians(-8), math.radians(s * 16), 0), ech=(1, 0.55, 1),
                      vertices=32, radius1=0.05, radius2=0.005, depth=0.1)
        s_ = o.modifiers.new("Lissage", "SUBSURF")
        s_.levels = s_.render_levels = 1
        i = primitive(f"Mocha_Oreille_Int_{cote}", "cone", (0, -0.012, -0.008), oreille_int, o, modele=corps,
                      ech=(0.68, 0.4, 0.78), vertices=32, radius1=0.05, radius2=0.005, depth=0.1)
        i.modifiers.new("Lissage", "SUBSURF").render_levels = 1

    museau = O["Mocha_Museau"]
    museau.location, museau.scale = (0, -0.09, 0.288), (0.048, 0.032, 0.03)
    primitive("Mocha_Nez", "uv_sphere", (0, -0.121, 0.306), rose, mocha, modele=corps, ech=(0.011, 0.007, 0.0075),
              segments=24, ring_count=12, radius=1.0)
    gf = O["Mocha_Goutte_Front"]
    gf.location, gf.scale = (0, -0.103, 0.376), (0.0075, 0.004, 0.011)

    # Queue : la courbe devient un maillage (pour porter des poils)
    q = O.get("Mocha_Queue")
    if q and q.type == "CURVE":
        q.data.bevel_depth = 0.016
        q.data.bevel_resolution = 3
        dg = bpy.context.evaluated_depsgraph_get()
        me = bpy.data.meshes.new_from_object(q.evaluated_get(dg))
        nq = bpy.data.objects.new("Mocha_Queue_Poils", me)
        _ranger(nq, corps)
        nq.parent, nq.matrix_world = mocha, q.matrix_world.copy()
        _lisse(nq)
        q.hide_render = q.hide_viewport = True
        q.name = "Mocha_Queue_Courbe"
        nq.name = "Mocha_Queue"
        fourrure(nq, mat_poils("Mocha_Poils_Queue", "#7E5434", "#C99B6A"), 0.014, 900, enfants=10)

    # Pelage : visage dégagé (comme une peau douce), poils longs sur le crâne, les joues et le corps
    def masque_tete(co):
        n = co.normalized()
        face = _lisser_doux((-n.y - 0.45) / 0.28) * _lisser_doux((0.72 - n.z) / 0.3)
        return 1.0 - 0.95 * face

    def masque_corps(co):
        n = co.normalized()
        return 1.0 - 0.7 * _lisser_doux((-n.y - 0.55) / 0.3)

    fourrure(tete, mat_poils("Mocha_Poils", "#8A5E3B", "#D9AE80"), 0.012, 3200, enfants=20, masque=masque_tete)
    fourrure(corps, mat_poils("Mocha_Poils_Corps", "#8A5E3B", "#D2A576"), 0.014, 3200, enfants=18,
             masque=masque_corps)
    fourrure(ventre, mat_poils("Mocha_Poils_Creme", "#CDB08C", "#F6E8D2"), 0.008, 1200, enfants=12)
    return mocha


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


def yeux_brillants(m):
    """Iris ambré dégradé (clair au centre, cerne foncé au bord) sous un vernis très brillant."""
    regler(m, None, 0.3, vernis=1.0, vernis_rug=0.02)
    nt = m.node_tree
    b = nt.nodes["Principled BSDF"]
    if b.inputs["Base Color"].is_linked:
        return
    coord = nt.nodes.new("ShaderNodeTexCoord")
    sep = nt.nodes.new("ShaderNodeSeparateXYZ")
    nt.links.new(coord.outputs["Object"], sep.inputs[0])
    carre = []
    for axe in ("X", "Z"):
        p = nt.nodes.new("ShaderNodeMath")
        p.operation = "POWER"
        p.inputs[1].default_value = 2
        nt.links.new(sep.outputs[axe], p.inputs[0])
        carre.append(p)
    somme = nt.nodes.new("ShaderNodeMath")
    nt.links.new(carre[0].outputs[0], somme.inputs[0])
    nt.links.new(carre[1].outputs[0], somme.inputs[1])
    racine = nt.nodes.new("ShaderNodeMath")
    racine.operation = "SQRT"
    nt.links.new(somme.outputs[0], racine.inputs[0])
    rampe = nt.nodes.new("ShaderNodeValToRGB")
    els = rampe.color_ramp.elements
    els[0].position, els[0].color = 0.0, lin("#FFD27A")
    els[1].position, els[1].color = 0.95, lin("#5A3412")
    milieu = els.new(0.6)
    milieu.color = lin("#E39A2E")
    nt.links.new(racine.outputs[0], rampe.inputs[0])
    nt.links.new(rampe.outputs[0], b.inputs["Base Color"])


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
        "Mousse": dict(rugosite=0.55, sheen=0.6, sss=0.35),
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
