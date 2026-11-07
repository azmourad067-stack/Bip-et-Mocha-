"""
Bip & Mocha — décor « cuisine » (le plan de travail est le plateau de jeu).

À utiliser après tools/blender/preparer-scene.py :
    import runpy
    cuisine = runpy.run_path("tools/blender/decor-cuisine.py")["construire_cuisine"]()

Repères (en mètres) : le dessus du plan de travail est à z = 0, son bord avant à y = -0.35,
le mur du fond à y = 0.45. Règle de l'univers : AUCUN texte lisible dans le décor.
"""

import math

import bpy


def _lin(h):
    h = h.lstrip("#")
    c = [int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    return tuple(x / 12.92 if x <= 0.04045 else ((x + 0.055) / 1.055) ** 2.4 for x in c) + (1.0,)


def _mat(nom, hexa, rugosite=0.5, emission=0.0):
    m = bpy.data.materials.get(nom) or bpy.data.materials.new(nom)
    m.use_nodes = True
    b = m.node_tree.nodes.get("Principled BSDF")
    b.inputs["Base Color"].default_value = _lin(hexa)
    b.inputs["Roughness"].default_value = rugosite
    if emission:
        b.inputs["Emission Color"].default_value = _lin(hexa)
        b.inputs["Emission Strength"].default_value = emission
    m.diffuse_color = _lin(hexa)
    return m


def _ranger(o, coll):
    for c in list(o.users_collection):
        c.objects.unlink(o)
    coll.objects.link(o)


def _boite(nom, dims, loc, mat, coll, arrondi=0.0, parent=None):
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc)
    o = bpy.context.active_object
    o.name = nom
    o.scale = dims
    o.data.materials.append(mat)
    if arrondi:
        b = o.modifiers.new("Arrondi", "BEVEL")
        b.width = arrondi
        b.segments = 4
        b.affect = "EDGES"
    _ranger(o, coll)
    if parent:
        o.parent = parent
    return o


def _cylindre(nom, r, h, loc, mat, coll, rot=(0, 0, 0), parent=None, sommets=32):
    bpy.ops.mesh.primitive_cylinder_add(vertices=sommets, radius=r, depth=h, location=loc, rotation=rot)
    o = bpy.context.active_object
    o.name = nom
    o.data.materials.append(mat)
    for p in o.data.polygons:
        p.use_smooth = True
    _ranger(o, coll)
    if parent:
        o.parent = parent
    return o


def construire_cuisine():
    coll = bpy.data.collections.get("Cuisine") or bpy.data.collections.new("Cuisine")
    if coll.name not in bpy.context.scene.collection.children:
        bpy.context.scene.collection.children.link(coll)
    for o in list(coll.objects):
        bpy.data.objects.remove(o, do_unlink=True)

    # Le sol générique de preparer-scene.py est remplacé par le plan de travail
    sol = bpy.data.objects.get("Sol")
    if sol:
        sol.hide_render = sol.hide_viewport = True

    bois = _mat("Cuisine_Plan", "#C8955E", 0.6)
    facade = _mat("Cuisine_Facade", "#9CC5B9", 0.5)
    mur = _mat("Cuisine_Mur", "#F2D7B6", 0.9)
    carreau = _mat("Cuisine_Carreau", "#BFE0D8", 0.3)
    joint = _mat("Cuisine_Joint", "#F7EFE4", 0.9)
    metal = _mat("Cuisine_Machine", "#E2574C", 0.35)
    noir = _mat("Cuisine_Noir", "#2A2F3A", 0.4)
    chrome = _mat("Cuisine_Chrome", "#C9CED6", 0.2)
    tasse = _mat("Cuisine_Tasse", "#F4C542", 0.3)
    horloge = _mat("Cuisine_Horloge", "#FBF7F1", 0.5)

    o = {}
    # Plan de travail + façade des placards (visible en bas des plans larges)
    o["plan"] = _boite("Plan_De_Travail", (2.6, 0.85, 0.05), (0, 0.05, -0.025), bois, coll, 0.01)
    o["facade"] = _boite("Facade_Placards", (2.6, 0.05, 0.9), (0, -0.33, -0.5), facade, coll)
    for i, x in enumerate((-0.9, -0.3, 0.3, 0.9)):
        _boite(f"Poignee_{i}", (0.12, 0.02, 0.015), (x, -0.36, -0.12), chrome, coll, 0.005)
        _boite(f"Jointure_{i}", (0.008, 0.01, 0.85), (x + 0.3, -0.355, -0.5), joint, coll)

    # Mur du fond avec crédence carrelée
    o["mur"] = _boite("Mur", (2.6, 0.05, 2.0), (0, 0.48, 1.0), mur, coll)
    _boite("Credence_Joints", (2.6, 0.01, 0.42), (0, 0.45, 0.21), joint, coll)
    for ix in range(-12, 13):
        for iz in range(4):
            _boite(f"Carreau_{ix}_{iz}", (0.095, 0.012, 0.095), (ix * 0.1, 0.444, 0.055 + iz * 0.1), carreau, coll, 0.006)

    # Machine à café (à gauche) : corps, bec, grille, 3 boutons sans texte
    machine = bpy.data.objects.new("Machine_Cafe", None)
    machine.location = (-0.42, 0.18, 0)
    coll.objects.link(machine)
    o["machine"] = machine
    _boite("Machine_Corps", (0.22, 0.24, 0.34), (0, 0, 0.17), metal, coll, 0.03, machine)
    _boite("Machine_Socle", (0.22, 0.3, 0.03), (0, -0.03, 0.015), noir, coll, 0.01, machine)
    _boite("Machine_Grille", (0.14, 0.12, 0.012), (0, -0.12, 0.035), chrome, coll, 0.004, machine)
    _boite("Machine_Tete", (0.16, 0.1, 0.06), (0, -0.14, 0.24), noir, coll, 0.015, machine)
    o["bec"] = _cylindre("Machine_Bec", 0.012, 0.04, (0, -0.16, 0.195), chrome, coll, parent=machine)
    for i, (x, c) in enumerate(((-0.05, "#7ED957"), (0.0, "#4FD1FF"), (0.05, "#FF4D4D"))):
        o[f"bouton_{i}"] = _cylindre(f"Machine_Bouton_{i}", 0.014, 0.015, (x, -0.125, 0.3),
                                     _mat(f"Bouton_{i}", c, 0.3, 0.6), coll, rot=(math.radians(90), 0, 0), parent=machine)

    # Tasse XXL (Mocha doit pouvoir s'y asseoir !)
    t = bpy.data.objects.new("Tasse", None)
    t.location = (-0.12, 0.02, 0)
    coll.objects.link(t)
    o["tasse"] = t
    bpy.ops.mesh.primitive_cylinder_add(vertices=48, radius=0.1, depth=0.19, location=(0, 0, 0.095))
    corps = bpy.context.active_object
    corps.name = "Tasse_Corps"
    corps.data.materials.append(tasse)
    sol_mod = corps.modifiers.new("Epaisseur", "SOLIDIFY")
    sol_mod.thickness = 0.012
    # On retire le couvercle du cylindre pour en faire une tasse
    import bmesh
    bm = bmesh.new()
    bm.from_mesh(corps.data)
    haut = [f for f in bm.faces if f.normal.z > 0.9]
    bmesh.ops.delete(bm, geom=haut, context="FACES_ONLY")
    bm.to_mesh(corps.data)
    bm.free()
    for p in corps.data.polygons:
        p.use_smooth = True
    _ranger(corps, coll)
    corps.parent = t
    bpy.ops.mesh.primitive_torus_add(major_radius=0.05, minor_radius=0.014, location=(0.115, 0, 0.1),
                                     rotation=(math.radians(90), 0, 0))
    anse = bpy.context.active_object
    anse.name = "Tasse_Anse"
    anse.data.materials.append(tasse)
    _ranger(anse, coll)
    anse.parent = t

    # Horloge murale (pour le « retour en arrière »)
    h = bpy.data.objects.new("Horloge", None)
    h.location = (0.42, 0.44, 0.86)
    coll.objects.link(h)
    o["horloge"] = h
    _cylindre("Horloge_Cadre", 0.12, 0.03, (0, 0, 0), noir, coll, rot=(math.radians(90), 0, 0), parent=h, sommets=48)
    _cylindre("Horloge_Cadran", 0.105, 0.032, (0, -0.002, 0), horloge, coll, rot=(math.radians(90), 0, 0), parent=h, sommets=48)
    for i in range(12):
        a = i * math.pi / 6
        _boite(f"Horloge_Repere_{i}", (0.008, 0.005, 0.02 if i % 3 else 0.03),
               (0.088 * math.sin(a), -0.02, 0.088 * math.cos(a)), noir, coll).rotation_euler = (0, a, 0)
        bpy.data.objects[f"Horloge_Repere_{i}"].parent = h
    for nom, longueur, ep in (("Horloge_Aiguille_H", 0.055, 0.01), ("Horloge_Aiguille_M", 0.08, 0.007)):
        pivot = bpy.data.objects.new(nom, None)
        pivot.parent = h
        pivot.location = (0, -0.022, 0)
        coll.objects.link(pivot)
        _boite(nom + "_Forme", (ep, 0.004, longueur), (0, 0, longueur / 2 - 0.01), noir, coll, parent=pivot)
        o[nom] = pivot
    bpy.data.objects["Horloge_Aiguille_H"].rotation_euler = (0, math.radians(240), 0)
    _cylindre("Horloge_Axe", 0.01, 0.01, (0, -0.026, 0), _mat("Cuisine_Accent", "#F28C38", 0.4), coll,
              rot=(math.radians(90), 0, 0), parent=h)

    # Étagère avec bocaux (sans étiquettes : règle « aucun texte »)
    _boite("Etagere", (0.62, 0.16, 0.025), (-0.3, 0.38, 0.62), bois, coll, 0.006)
    for i, (x, hx, c) in enumerate(((-0.52, 0.16, "#E9A23B"), (-0.38, 0.12, "#7FB3D5"), (-0.24, 0.19, "#E07A5F"),
                                    (-0.1, 0.1, "#81B29A"))):
        _cylindre(f"Bocal_{i}", 0.045, hx, (x, 0.38, 0.6325 + hx / 2), _mat(f"Bocal_{i}", c, 0.25), coll)
        _cylindre(f"Bocal_Couvercle_{i}", 0.048, 0.02, (x, 0.38, 0.6325 + hx + 0.01), chrome, coll)

    # Petite plante (le « témoin muet » de l'univers)
    _cylindre("Plante_Pot", 0.05, 0.08, (0.62, 0.3, 0.04), _mat("Plante_Pot", "#C9734E", 0.6), coll)
    feuille = _mat("Plante_Feuille", "#5FA36A", 0.6)
    for i in range(6):
        a = i * math.pi / 3
        bpy.ops.mesh.primitive_uv_sphere_add(radius=1, location=(0.62 + 0.035 * math.cos(a), 0.3 + 0.035 * math.sin(a), 0.13))
        f = bpy.context.active_object
        f.name = f"Plante_Feuille_{i}"
        f.scale = (0.025, 0.025, 0.06)
        f.rotation_euler = (0.5 * math.sin(a), -0.5 * math.cos(a), 0)
        f.data.materials.append(feuille)
        for p in f.data.polygons:
            p.use_smooth = True
        _ranger(f, coll)

    return o


if __name__ == "__main__":
    construire_cuisine()
