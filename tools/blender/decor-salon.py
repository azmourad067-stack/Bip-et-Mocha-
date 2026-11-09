"""
Bip & Mocha — décor « salon » (style studio) : épisodes 02, 03, 05 et fin du 04.

À utiliser après tools/blender/preparer-scene.py :
    import runpy
    salon = runpy.run_path("tools/blender/decor-salon.py")["construire_salon"]()

Repères (en mètres) : le sol est à z = 0 (les personnages jouent par terre, sur le tapis),
le mur du fond est à y = 1.45, la fenêtre est au-dessus du canapé, l'avant du canapé est à y ≈ 0.58.
Règle de l'univers : AUCUN texte lisible dans le décor.

Objets utiles aux épisodes (clés du dictionnaire renvoyé) :
    "canape", "assise_g", "assise_d"  (le canapé et ses deux coussins d'assise, pour les faire rebondir)
    "lampe", "lampe_lumiere"          (lampe de bureau sur la table d'appoint ; lumière éteinte au départ)
    "prise"                           (prise murale, à gauche du canapé : le chargeur de Bip, épisode 04)
    "fenetre_soleil"                  (le soleil qui entre par la fenêtre : tache de lumière au sol, épisode 05)
    "ciel"                            (le ciel derrière la fenêtre, pour y faire passer un nuage)
"""

import math
import os
import runpy

import bmesh
import bpy

ICI = os.path.dirname(os.path.abspath(__file__)) if "__file__" in globals() else ""
ST = runpy.run_path(os.path.join(ICI, "style-studio.py")) if ICI else None

MUR_Y = 1.45  # face avant du mur du fond
FEN_X, FEN_Z = (-0.35, 0.45), (0.95, 1.85)  # ouverture de la fenêtre


def _coll():
    coll = bpy.data.collections.get("Salon") or bpy.data.collections.new("Salon")
    if coll.name not in bpy.context.scene.collection.children:
        bpy.context.scene.collection.children.link(coll)
    return coll


def _lier(o, coll, parent=None):
    for c in list(o.users_collection):
        c.objects.unlink(o)
    coll.objects.link(o)
    if parent:
        o.parent = parent
    return o


def _boite(nom, dims, loc, mat, coll, arrondi=0.01, parent=None, rot=(0, 0, 0), lissage=2):
    """Boîte aux arêtes arrondies (dimensions réelles dans le maillage)."""
    if arrondi:
        me = ST["maillage_boite"](dims, arrondi)
    else:
        me = bpy.data.meshes.new(nom)
        bm = bmesh.new()
        bmesh.ops.create_cube(bm, size=1.0)
        for v in bm.verts:
            v.co.x, v.co.y, v.co.z = v.co.x * dims[0], v.co.y * dims[1], v.co.z * dims[2]
        bm.to_mesh(me)
        bm.free()
    o = bpy.data.objects.new(nom, me)
    o.location, o.rotation_euler = loc, tuple(math.radians(a) for a in rot)
    me.materials.append(mat)
    _lier(o, coll, parent)
    if arrondi:
        for p in me.polygons:
            p.use_smooth = True
        if lissage:
            s = o.modifiers.new("Lissage", "SUBSURF")
            s.levels = s.render_levels = lissage
    return o


def _prim(nom, quoi, loc, mat, coll, parent=None, rot=(0, 0, 0), ech=(1, 1, 1), lisse=True, **params):
    getattr(bpy.ops.mesh, f"primitive_{quoi}_add")(location=(0, 0, 0), **params)
    o = bpy.context.active_object
    o.name = nom
    o.location, o.rotation_euler, o.scale = loc, tuple(math.radians(a) for a in rot), ech
    o.data.materials.append(mat)
    if lisse:
        for p in o.data.polygons:
            p.use_smooth = True
    return _lier(o, coll, parent)


def _vide(nom, loc, coll, parent=None):
    o = bpy.data.objects.new(nom, None)
    o.location = loc
    return _lier(o, coll, parent)


# ---------------------------------------------------------------------------
# Matières
# ---------------------------------------------------------------------------
def _relief_bruit(m, echelle=60.0, force=0.05):
    nt = m.node_tree
    b = nt.nodes["Principled BSDF"]
    if b.inputs["Normal"].is_linked:
        return m
    bruit = nt.nodes.new("ShaderNodeTexNoise")
    bruit.inputs["Scale"].default_value = echelle
    relief = nt.nodes.new("ShaderNodeBump")
    relief.inputs["Strength"].default_value = force
    nt.links.new(bruit.outputs["Fac"], relief.inputs["Height"])
    nt.links.new(relief.outputs[0], b.inputs["Normal"])
    return m


def parquet(m):
    """Lames de parquet (veinage + joints fins + teinte qui varie d'une lame à l'autre)."""
    lin = ST["lin"]
    ST["regler"](m, None, 0.38, vernis=0.45, vernis_rug=0.12)
    nt = m.node_tree
    b = nt.nodes["Principled BSDF"]
    if b.inputs["Base Color"].is_linked:
        return m
    coord = nt.nodes.new("ShaderNodeTexCoord")
    lames = nt.nodes.new("ShaderNodeTexBrick")
    lames.offset = 0.37
    lames.inputs["Color1"].default_value = lin("#C08A55")
    lames.inputs["Color2"].default_value = lin("#A8723F")
    lames.inputs["Mortar"].default_value = lin("#5A3A20")
    lames.inputs["Scale"].default_value = 1.0
    lames.inputs["Mortar Size"].default_value = 0.0025
    lames.inputs["Brick Width"].default_value = 1.1
    lames.inputs["Row Height"].default_value = 0.13
    nt.links.new(coord.outputs["Object"], lames.inputs["Vector"])
    etire = nt.nodes.new("ShaderNodeMapping")
    etire.inputs["Scale"].default_value = (0.6, 7.0, 1.0)
    nt.links.new(coord.outputs["Object"], etire.inputs[0])
    vague = nt.nodes.new("ShaderNodeTexWave")
    vague.wave_type = "RINGS"
    vague.inputs["Scale"].default_value = 2.5
    vague.inputs["Distortion"].default_value = 7.0
    vague.inputs["Detail"].default_value = 3.0
    nt.links.new(etire.outputs[0], vague.inputs["Vector"])
    veines = nt.nodes.new("ShaderNodeMix")
    veines.data_type = "RGBA"
    veines.blend_type = "MULTIPLY"
    veines.inputs["Factor"].default_value = 0.35
    nt.links.new(lames.outputs["Color"], veines.inputs["A"])
    nt.links.new(vague.outputs["Color"], veines.inputs["B"])
    nt.links.new(veines.outputs["Result"], b.inputs["Base Color"])
    relief = nt.nodes.new("ShaderNodeBump")
    relief.invert = True
    relief.inputs["Strength"].default_value = 0.35
    relief.inputs["Distance"].default_value = 0.002
    nt.links.new(lames.outputs["Fac"], relief.inputs["Height"])
    nt.links.new(relief.outputs[0], b.inputs["Normal"])
    return m


def tapis(m):
    """Tapis rond tissé : anneaux crème / terracotta / ocre, fibres en relief."""
    lin = ST["lin"]
    ST["regler"](m, "#EADCC6", 0.95, sheen=0.8)
    nt = m.node_tree
    b = nt.nodes["Principled BSDF"]
    if b.inputs["Base Color"].is_linked:
        return m
    coord = nt.nodes.new("ShaderNodeTexCoord")
    sep = nt.nodes.new("ShaderNodeVectorMath")
    sep.operation = "LENGTH"
    nt.links.new(coord.outputs["Object"], sep.inputs[0])
    rampe = nt.nodes.new("ShaderNodeValToRGB")
    rampe.color_ramp.interpolation = "CONSTANT"
    el = rampe.color_ramp.elements
    el[0].color = lin("#EADCC6")
    el[1].position, el[1].color = 0.62, lin("#C8694A")
    for pos, c in ((0.70, "#EADCC6"), (0.82, "#E2A84B"), (0.88, "#EADCC6"), (0.95, "#C8694A")):
        e = el.new(pos)
        e.color = lin(c)
    nt.links.new(sep.outputs["Value"], rampe.inputs[0])
    nt.links.new(rampe.outputs[0], b.inputs["Base Color"])
    _relief_bruit(m, 300.0, 0.25)
    return m


def tissu(m, couleur, sheen=0.7):
    ST["regler"](m, couleur, 0.85, sheen=sheen)
    return _relief_bruit(m, 220.0, 0.12)


def ciel(m):
    """Ciel d'après-midi (dégradé bleu → crème vers l'horizon), lumineux par lui-même."""
    lin = ST["lin"]
    nt = m.node_tree
    nt.nodes.clear()
    coord = nt.nodes.new("ShaderNodeTexCoord")
    sep = nt.nodes.new("ShaderNodeSeparateXYZ")
    nt.links.new(coord.outputs["Generated"], sep.inputs[0])
    rampe = nt.nodes.new("ShaderNodeValToRGB")
    rampe.color_ramp.elements[0].color = lin("#FFE9CC")
    rampe.color_ramp.elements[1].color = lin("#6FB2E8")
    rampe.color_ramp.elements[0].position = 0.25
    nt.links.new(sep.outputs["Y"], rampe.inputs[0])
    em = nt.nodes.new("ShaderNodeEmission")
    em.inputs["Strength"].default_value = 1.6
    nt.links.new(rampe.outputs[0], em.inputs["Color"])
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    nt.links.new(em.outputs[0], out.inputs[0])
    return m


# ---------------------------------------------------------------------------
# Éléments du salon
# ---------------------------------------------------------------------------
def _rideau(nom, x, coll, mat):
    """Rideau : plan plissé (vagues) + épaisseur."""
    me = bpy.data.meshes.new(nom)
    bm = bmesh.new()
    bmesh.ops.create_grid(bm, x_segments=28, y_segments=3, size=0.5)
    for v in bm.verts:
        u = v.co.x + 0.5  # 0..1 sur la largeur
        h = v.co.y + 0.5  # 0..1 sur la hauteur
        v.co.x = (u - 0.5) * 0.3 * (1 - 0.15 * (1 - h))
        v.co.z = (h - 0.5) * 1.3
        v.co.y = 0.018 * math.sin(u * math.pi * 7) * (0.6 + 0.4 * (1 - h))
    bm.to_mesh(me)
    bm.free()
    o = bpy.data.objects.new(nom, me)
    o.location = (x, MUR_Y - 0.09, 1.3)
    me.materials.append(mat)
    for p in me.polygons:
        p.use_smooth = True
    ep = o.modifiers.new("Epaisseur", "SOLIDIFY")
    ep.thickness = 0.01
    s = o.modifiers.new("Lissage", "SUBSURF")
    s.levels = s.render_levels = 1
    return _lier(o, coll)


def _plante(coll, loc):
    pot = ST["regler"]("Salon_Pot", "#C9734E", 0.55)
    terre = ST["regler"]("Salon_Terre", "#4A3426", 0.9)
    feuille = ST["regler"]("Salon_Feuille", "#3F8F55", 0.42, vernis=0.35, sss=0.12)
    r = _vide("Plante_Salon", loc, coll)
    _prim("Plante_Salon_Pot", "cylinder", (0, 0, 0.16), pot, coll, r, vertices=48, radius=0.15, depth=0.32)
    ST["biseau"](bpy.data.objects["Plante_Salon_Pot"], 0.01)
    _prim("Plante_Salon_Terre", "cylinder", (0, 0, 0.31), terre, coll, r, vertices=48, radius=0.14, depth=0.02)
    # Grandes feuilles ovales sur de fines tiges, disposées en gerbe
    tige = ST["regler"]("Salon_Tige", "#3E7A45", 0.5)
    for i in range(11):
        a = i * 2.4  # angle d'or : répartition naturelle
        incl = 18 + (i % 4) * 9
        h = 0.45 + (i % 5) * 0.09
        dx, dy = math.cos(a), math.sin(a)
        bout = (dx * math.sin(math.radians(incl)) * h, dy * math.sin(math.radians(incl)) * h,
                0.3 + math.cos(math.radians(incl)) * h)
        mi = tuple(c / 2 for c in bout)
        t = _prim(f"Plante_Salon_Tige_{i}", "cylinder", (mi[0], mi[1], 0.3 + (bout[2] - 0.3) / 2), tige, coll, r,
                  vertices=8, radius=0.006, depth=h)
        t.rotation_euler = (-math.radians(incl) * dy, math.radians(incl) * dx, 0)
        f = _prim(f"Plante_Salon_Feuille_{i}", "uv_sphere", bout, feuille, coll, r, segments=24, ring_count=12,
                  radius=1.0, ech=(0.09, 0.012, 0.13))
        f.rotation_euler = (math.radians(70) * -dy * 0.6, math.radians(incl + 25) * dx * 0.8, a + math.pi / 2)
    return r


def _tableau(coll, loc, couleurs):
    cadre = ST["regler"]("Salon_Cadre", "#3B2B20", 0.45, vernis=0.4)
    toile = ST["regler"]("Salon_Toile", "#F4EDE2", 0.9)
    r = _vide("Tableau", loc, coll)
    _boite("Tableau_Cadre", (0.42, 0.03, 0.52), (0, 0, 0), cadre, coll, 0.006, r, lissage=1)
    _boite("Tableau_Toile", (0.36, 0.01, 0.46), (0, -0.012, 0), toile, coll, 0, r)
    # Formes abstraites (soleil, collines) : aucun texte
    for i, (forme, c, loc_f, ech) in enumerate(couleurs):
        m = ST["regler"](f"Salon_Tableau_{i}", c, 0.7)
        if forme == "rond":
            _prim(f"Tableau_Forme_{i}", "cylinder", loc_f, m, coll, r, rot=(90, 0, 0), vertices=48,
                  radius=ech, depth=0.004)
        else:
            _prim(f"Tableau_Forme_{i}", "uv_sphere", loc_f, m, coll, r, segments=48, ring_count=12, radius=1.0,
                  ech=(ech[0], 0.002, ech[1]))
    # La toile coupe tout ce qui dépasse (les collines) : un masque « booléen » serait lourd,
    # les formes sont donc dessinées à l'intérieur.
    return r


def _canape(coll, centre):
    velours = tissu(bpy.data.materials.get("Salon_Velours") or bpy.data.materials.new("Salon_Velours"), "#3F6197")
    bois_pied = ST["regler"]("Salon_Pied", "#7A5232", 0.4, vernis=0.4)
    coussin_a = tissu(bpy.data.materials.get("Salon_Coussin_A") or bpy.data.materials.new("Salon_Coussin_A"),
                      "#E3A93E", 0.6)
    coussin_b = tissu(bpy.data.materials.get("Salon_Coussin_B") or bpy.data.materials.new("Salon_Coussin_B"),
                      "#E7826A", 0.6)
    cx, cy = centre
    r = _vide("Canape", (cx, cy, 0), coll)
    _boite("Canape_Base", (1.9, 0.8, 0.22), (0, 0, 0.19), velours, coll, 0.05, r)
    _boite("Canape_Dossier", (1.9, 0.24, 0.52), (0, 0.29, 0.53), velours, coll, 0.07, r)
    for cote, s in (("G", -1), ("D", 1)):
        _boite(f"Canape_Accoudoir_{cote}", (0.2, 0.8, 0.5), (s * 0.85, 0, 0.33), velours, coll, 0.08, r)
    assises = []
    for cote, s in (("G", -1), ("D", 1)):
        a = _boite(f"Canape_Assise_{cote}", (0.74, 0.6, 0.14), (s * 0.375, -0.07, 0.36), velours, coll, 0.06, r)
        assises.append(a)
        _boite(f"Canape_Dos_{cote}", (0.72, 0.17, 0.36), (s * 0.375, 0.13, 0.6), velours, coll, 0.07, r, rot=(-12, 0, 0))
    _boite("Canape_Coussin_A", (0.32, 0.12, 0.3), (-0.55, 0.0, 0.57), coussin_a, coll, 0.06, r, rot=(-15, 0, 18))
    _boite("Canape_Coussin_B", (0.3, 0.11, 0.28), (0.6, 0.0, 0.56), coussin_b, coll, 0.06, r, rot=(-14, 0, -14))
    for i, (x, y) in enumerate(((-0.88, -0.33), (0.88, -0.33), (-0.88, 0.33), (0.88, 0.33))):
        _prim(f"Canape_Pied_{i}", "cone", (x, y, 0.04), bois_pied, coll, r, vertices=16, radius1=0.018,
              radius2=0.026, depth=0.08)
    return r, assises


def _table_lampe(coll, loc):
    bois_clair = ST["bois"](bpy.data.materials.get("Salon_Table") or bpy.data.materials.new("Salon_Table"),
                            "#D9AE7A", "#B3814E")
    metal = ST["regler"]("Salon_Lampe_Metal", "#2F3B45", 0.35, metal=0.6, vernis=0.5)
    abat = ST["regler"]("Salon_Lampe_Abat", "#4DB3A8", 0.3, vernis=0.8)
    ampoule = ST["regler"]("Salon_Ampoule", "#FFF4DD", 0.3, emission="#FFE2A8", force=0.0)
    t = _vide("Table_Appoint", loc, coll)
    _prim("Table_Plateau", "cylinder", (0, 0, 0.5), bois_clair, coll, t, vertices=64, radius=0.22, depth=0.03)
    ST["biseau"](bpy.data.objects["Table_Plateau"], 0.006)
    _prim("Table_Pied", "cylinder", (0, 0, 0.25), bois_clair, coll, t, vertices=24, radius=0.025, depth=0.5)
    _prim("Table_Socle", "cylinder", (0, 0, 0.01), bois_clair, coll, t, vertices=48, radius=0.13, depth=0.02)
    ST["biseau"](bpy.data.objects["Table_Socle"], 0.005)
    # Lampe de bureau articulée (épisode 05 : Bip la tire, le fil est trop court)
    lampe = _vide("Lampe", (0.05, 0.02, 0.515), coll, t)
    _prim("Lampe_Pied", "cylinder", (0, 0, 0.01), metal, coll, lampe, vertices=48, radius=0.06, depth=0.02)
    bras1 = _prim("Lampe_Bras_1", "cylinder", (0.0, 0.0, 0.12), metal, coll, lampe, vertices=12, radius=0.008,
                  depth=0.24, rot=(0, -18, 0))
    bras1.location = (-0.037, 0, 0.12)
    _prim("Lampe_Coude", "uv_sphere", (-0.074, 0, 0.235), metal, coll, lampe, segments=16, ring_count=8,
          radius=0.014)
    bras2 = _prim("Lampe_Bras_2", "cylinder", (0, 0, 0), metal, coll, lampe, vertices=12, radius=0.008, depth=0.2,
                  rot=(0, 62, 0))
    bras2.location = (0.014, 0, 0.282)
    tete = _vide("Lampe_Tete", (0.1, 0, 0.33), coll, lampe)
    tete.rotation_euler = (0, math.radians(-125), 0)
    abat_o = _prim("Lampe_Abat", "cone", (0, 0, 0.0), abat, coll, tete, vertices=48, radius1=0.07, radius2=0.03,
                   depth=0.09)
    sol = abat_o.modifiers.new("Epaisseur", "SOLIDIFY")
    sol.thickness = 0.004
    # Le cône est ouvert du côté large (l'ampoule se voit)
    bm = bmesh.new()
    bm.from_mesh(abat_o.data)
    bas = [f for f in bm.faces if f.normal.z < -0.9]
    bmesh.ops.delete(bm, geom=bas, context="FACES_ONLY")
    bm.to_mesh(abat_o.data)
    bm.free()
    _prim("Lampe_Ampoule", "uv_sphere", (0, 0, -0.02), ampoule, coll, tete, segments=24, ring_count=12, radius=0.022)
    d = bpy.data.lights.new("Lampe_Lumiere", "SPOT")
    d.energy, d.color = 0.0, ST["lin"]("#FFD9A0")[:3]
    d.spot_size, d.spot_blend, d.shadow_soft_size = math.radians(80), 0.6, 0.03
    lum = bpy.data.objects.new("Lampe_Lumiere", d)
    _lier(lum, coll, tete)
    lum.location = (0, 0, -0.03)
    lum.rotation_euler = (math.radians(180), 0, 0)
    return t, lampe, d


def construire_salon():
    coll = _coll()
    for o in list(coll.objects):
        bpy.data.objects.remove(o, do_unlink=True)
    sol_generique = bpy.data.objects.get("Sol")
    if sol_generique:
        sol_generique.hide_render = sol_generique.hide_viewport = True
    regler, lin = ST["regler"], ST["lin"]
    o = {}

    # Sol en parquet, tapis rond
    m_parquet = parquet(bpy.data.materials.get("Salon_Parquet") or bpy.data.materials.new("Salon_Parquet"))
    o["sol"] = _boite("Salon_Sol", (7.0, 5.0, 0.04), (0, 0.5, -0.02), m_parquet, coll, 0)
    m_tapis = tapis(bpy.data.materials.get("Salon_Tapis") or bpy.data.materials.new("Salon_Tapis"))
    o["tapis"] = _prim("Tapis", "cylinder", (0.05, -0.05, 0.004), m_tapis, coll, vertices=96, radius=1.0,
                       depth=0.008, ech=(1.0, 0.8, 1.0))
    ST["biseau"](o["tapis"], 0.003)

    # Mur du fond percé d'une fenêtre (4 pans autour de l'ouverture), plinthe, prise
    m_mur = regler("Salon_Mur", "#EBD3BD", 0.85)
    ST["platre"](m_mur)
    ep, yc = 0.1, MUR_Y + 0.05
    (x0, x1), (z0, z1) = FEN_X, FEN_Z
    for nom, (ax, bx), (az, bz) in (("G", (-3.5, x0), (0, 2.8)), ("D", (x1, 3.5), (0, 2.8)),
                                    ("Bas", (x0, x1), (0, z0)), ("Haut", (x0, x1), (z1, 2.8))):
        _boite(f"Salon_Mur_{nom}", (bx - ax, ep, bz - az), ((ax + bx) / 2, yc, (az + bz) / 2), m_mur, coll, 0)
    blanc = regler("Salon_Boiserie", "#F6F0E6", 0.35, vernis=0.4)
    _boite("Salon_Plinthe", (7.0, 0.02, 0.09), (0, MUR_Y - 0.01, 0.045), blanc, coll, 0.004, lissage=1)
    prise = _vide("Prise", (-0.62, MUR_Y - 0.012, 0.22), coll)
    _boite("Prise_Plaque", (0.075, 0.012, 0.075), (0, 0, 0), blanc, coll, 0.008, prise, lissage=1)
    trou = regler("Salon_Prise_Trou", "#2A2F3A", 0.5)
    for i, x in enumerate((-0.012, 0.012)):
        _prim(f"Prise_Trou_{i}", "cylinder", (x, -0.006, 0), trou, coll, prise, rot=(90, 0, 0), vertices=16,
              radius=0.0045, depth=0.004)
    o["prise"] = prise

    # Fenêtre : cadre, croisillon, appui ; ciel lumineux derrière ; rideaux moutarde sur une tringle
    for nom, dims, loc in (
        ("G", (0.05, 0.08, z1 - z0 + 0.05), (x0 - 0.0, MUR_Y + 0.02, (z0 + z1) / 2)),
        ("D", (0.05, 0.08, z1 - z0 + 0.05), (x1, MUR_Y + 0.02, (z0 + z1) / 2)),
        ("Haut", (x1 - x0 + 0.05, 0.08, 0.05), ((x0 + x1) / 2, MUR_Y + 0.02, z1)),
        ("Bas", (x1 - x0 + 0.05, 0.08, 0.05), ((x0 + x1) / 2, MUR_Y + 0.02, z0)),
        ("Croisillon_V", (0.03, 0.04, z1 - z0), ((x0 + x1) / 2, MUR_Y + 0.05, (z0 + z1) / 2)),
        ("Croisillon_H", (x1 - x0, 0.04, 0.03), ((x0 + x1) / 2, MUR_Y + 0.05, z0 + (z1 - z0) * 0.62)),
    ):
        _boite(f"Fenetre_{nom}", dims, loc, blanc, coll, 0.006, lissage=1)
    _boite("Fenetre_Appui", (x1 - x0 + 0.2, 0.12, 0.03), ((x0 + x1) / 2, MUR_Y - 0.03, z0 - 0.03), blanc, coll, 0.008,
           lissage=1)
    m_ciel = ciel(bpy.data.materials.get("Salon_Ciel") or bpy.data.materials.new("Salon_Ciel"))
    o["ciel"] = _prim("Ciel", "plane", ((x0 + x1) / 2, MUR_Y + 1.2, 1.4), m_ciel, coll, rot=(90, 0, 0),
                      ech=(2.5, 1.8, 1), lisse=False, size=1.0)
    o["ciel"].visible_shadow = False  # le soleil passe à travers
    # Silhouette d'un arbre lointain et des collines (sans détail : c'est flou de toute façon)
    # (éclairés par le soleil du dehors : ils brillent un peu par eux-mêmes)
    lointain = regler("Salon_Lointain", "#A9CC9A", 0.9, emission="#A9CC9A", force=0.9)
    _prim("Colline", "uv_sphere", (0.2, MUR_Y + 1.1, 0.55), lointain, coll, segments=48, ring_count=16, radius=1.0,
          ech=(1.6, 0.05, 0.42))
    _prim("Arbre_Lointain", "uv_sphere", (-0.15, MUR_Y + 1.05, 1.15), regler("Salon_Arbre", "#8DBB7E", 0.9, emission="#8DBB7E", force=0.8), coll,
          segments=32, ring_count=16, radius=1.0, ech=(0.32, 0.05, 0.36))
    for nom in ("Colline", "Arbre_Lointain"):
        bpy.data.objects[nom].visible_shadow = False
    rideau = tissu(bpy.data.materials.get("Salon_Rideau") or bpy.data.materials.new("Salon_Rideau"), "#E0A93B", 0.5)
    for cote, x in (("G", x0 - 0.17), ("D", x1 + 0.17)):
        _rideau(f"Rideau_{cote}", x, coll, rideau)
    _prim("Tringle", "cylinder", ((x0 + x1) / 2, MUR_Y - 0.09, 1.97), regler("Salon_Tringle", "#2F3B45", 0.3, metal=0.8),
          coll, rot=(0, 90, 0), vertices=16, radius=0.009, depth=x1 - x0 + 0.75)

    # Canapé (devant : y ≈ 0.58), table d'appoint + lampe à gauche, plante à droite, tableau
    o["canape"], (o["assise_g"], o["assise_d"]) = _canape(coll, (0.45, 0.98))
    o["table"], o["lampe"], o["lampe_lumiere"] = _table_lampe(coll, (-0.85, 1.05, 0))
    o["plante"] = _plante(coll, (1.72, 1.12, 0))
    o["tableau"] = _tableau(coll, (1.1, MUR_Y - 0.02, 1.32), (
        ("rond", "#E9A23B", (0.07, -0.02, 0.1), 0.065),
        ("ovale", "#8FBFB2", (-0.05, -0.02, -0.17), (0.2, 0.09)),
        ("ovale", "#4F6E9C", (0.08, -0.021, -0.2), (0.14, 0.06)),
    ))

    # Lumière d'après-midi : soleil qui entre par la fenêtre (tache chaude au sol), ciel bleuté en appoint
    coll_plateau = bpy.data.collections.get("Plateau") or coll
    d = bpy.data.lights.new("Soleil_Fenetre", "SUN")
    d.energy, d.color, d.angle = 3.0, lin("#FFD8A8")[:3], math.radians(1.5)
    soleil = bpy.data.objects.new("Soleil_Fenetre", d)
    soleil.rotation_euler = (math.radians(-55), 0, math.radians(15))
    coll_plateau.objects.link(soleil)
    o["fenetre_soleil"] = soleil
    if "Rebond" not in bpy.data.objects:
        dr = bpy.data.lights.new("Rebond", "AREA")
        dr.energy, dr.color, dr.size = 25, lin("#CFE3FF")[:3], 1.5
        ro = bpy.data.objects.new("Rebond", dr)
        ro.location, ro.rotation_euler = (1.4, -1.3, 0.6), tuple(math.radians(a) for a in (75, 0, 50))
        coll_plateau.objects.link(ro)
    if "Fenetre" not in bpy.data.objects:  # lumière douce venue de la fenêtre (grande source)
        df = bpy.data.lights.new("Fenetre", "AREA")
        df.energy, df.color, df.size = 90, lin("#FFE7C7")[:3], 1.2
        fo = bpy.data.objects.new("Fenetre", df)
        fo.location, fo.rotation_euler = (0.05, 1.3, 1.6), tuple(math.radians(a) for a in (-55, 0, 0))
        coll_plateau.objects.link(fo)
    return o


if __name__ == "__main__":
    construire_salon()
