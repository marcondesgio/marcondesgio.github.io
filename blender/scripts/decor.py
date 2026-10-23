"""Cozy office decor + procedural surface textures for the desk scene (feedback round 2).

Textures are procedural shader nodes; bake_desk.py bakes them (albedo pass) into the lightmaps, so the
web app gets wood grain, fabric weave and wallpaper for free.
"""
import math
import os
import random

import bmesh
import bpy
from mathutils import Matrix, Vector

from common import TEX_DIR, assign, cylinder, hex_rgba, join, rounded_box, smooth, sphere, text_image, tube

# soft, cute palette for props (matches the site's pink / lilac / aqua accents)
PASTELS = ["#F7A8C8", "#C3A8FF", "#8FE0D6", "#FFE3A3", "#A8E6B8", "#FFB3A7", "#F6EFE6", "#9EC5FF"]


# ---------------------------------------------------------------- procedural materials

def _principled(name, rough):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    nt = mat.node_tree
    bsdf = nt.nodes["Principled BSDF"]
    bsdf.inputs["Roughness"].default_value = rough
    return mat, nt, bsdf


def _coords(nt, scale):
    tc = nt.nodes.new("ShaderNodeTexCoord")
    mp = nt.nodes.new("ShaderNodeMapping")
    mp.inputs["Scale"].default_value = scale
    nt.links.new(tc.outputs["Object"], mp.inputs["Vector"])
    return mp.outputs["Vector"]


def wood_material(name, light, dark, scale=(1.0, 0.12, 1.0), rough=0.5):
    """Grain running along Y (plank length): distorted wave bands mixed between two browns, plus bump."""
    mat, nt, bsdf = _principled(name, rough)
    co = _coords(nt, scale)
    wave = nt.nodes.new("ShaderNodeTexWave")
    wave.wave_type = "BANDS"
    wave.bands_direction = "X"
    wave.inputs["Scale"].default_value = 18
    wave.inputs["Distortion"].default_value = 9
    wave.inputs["Detail"].default_value = 3
    noise = nt.nodes.new("ShaderNodeTexNoise")
    noise.inputs["Scale"].default_value = 40
    mix_f = nt.nodes.new("ShaderNodeMath")
    mix_f.operation = "MULTIPLY_ADD"
    mix_f.inputs[1].default_value = 0.75
    ramp = nt.nodes.new("ShaderNodeValToRGB")
    ramp.color_ramp.elements[0].color = hex_rgba(dark)
    ramp.color_ramp.elements[1].color = hex_rgba(light)
    ramp.color_ramp.elements[0].position = 0.25
    bump = nt.nodes.new("ShaderNodeBump")
    bump.inputs["Strength"].default_value = 0.12
    L = nt.links.new
    L(co, wave.inputs["Vector"])
    L(co, noise.inputs["Vector"])
    L(wave.outputs["Fac"], mix_f.inputs[0])
    L(noise.outputs["Fac"], mix_f.inputs[2])
    L(mix_f.outputs[0], ramp.inputs["Fac"])
    L(ramp.outputs["Color"], bsdf.inputs["Base Color"])
    L(wave.outputs["Fac"], bump.inputs["Height"])
    L(bump.outputs["Normal"], bsdf.inputs["Normal"])
    return mat


def fabric_material(name, color, scale=180.0, rough=0.9):
    """Woven cloth: two perpendicular fine wave textures multiplied, tinting the colour and the bump."""
    mat, nt, bsdf = _principled(name, rough)
    bsdf.inputs["Sheen Weight"].default_value = 0.4
    co = _coords(nt, (scale, scale, scale))
    waves = []
    for d in ("X", "Z"):
        w = nt.nodes.new("ShaderNodeTexWave")
        w.wave_type = "BANDS"
        w.bands_direction = d
        w.inputs["Scale"].default_value = 1.0
        nt.links.new(co, w.inputs["Vector"])
        waves.append(w)
    mul = nt.nodes.new("ShaderNodeMath")
    mul.operation = "MULTIPLY"
    nt.links.new(waves[0].outputs["Fac"], mul.inputs[0])
    nt.links.new(waves[1].outputs["Fac"], mul.inputs[1])
    mix = nt.nodes.new("ShaderNodeMix")
    mix.data_type = "RGBA"
    mix.inputs["A"].default_value = tuple(c * 0.78 for c in hex_rgba(color)[:3]) + (1,)
    mix.inputs["B"].default_value = hex_rgba(color)
    nt.links.new(mul.outputs[0], mix.inputs["Factor"])
    nt.links.new(mix.outputs["Result"], bsdf.inputs["Base Color"])
    bump = nt.nodes.new("ShaderNodeBump")
    bump.inputs["Strength"].default_value = 0.25
    nt.links.new(mul.outputs[0], bump.inputs["Height"])
    nt.links.new(bump.outputs["Normal"], bsdf.inputs["Normal"])
    return mat


def wallpaper_material(name, base, dot, scale=14.0):
    """Painted wall with a soft polka-dot wallpaper."""
    mat, nt, bsdf = _principled(name, 0.85)
    co = _coords(nt, (scale, scale, scale))
    vor = nt.nodes.new("ShaderNodeTexVoronoi")
    vor.inputs["Randomness"].default_value = 0.0
    cut = nt.nodes.new("ShaderNodeMath")
    cut.operation = "LESS_THAN"
    cut.inputs[1].default_value = 0.16
    mix = nt.nodes.new("ShaderNodeMix")
    mix.data_type = "RGBA"
    mix.inputs["A"].default_value = hex_rgba(base)
    mix.inputs["B"].default_value = hex_rgba(dot)
    nt.links.new(co, vor.inputs["Vector"])
    nt.links.new(vor.outputs["Distance"], cut.inputs[0])
    nt.links.new(cut.outputs[0], mix.inputs["Factor"])
    nt.links.new(mix.outputs["Result"], bsdf.inputs["Base Color"])
    return mat


def flat(name, color, rough=0.6, emit=None, strength=0.0):
    mat, nt, bsdf = _principled(name, rough)
    bsdf.inputs["Base Color"].default_value = hex_rgba(color)
    if emit:
        bsdf.inputs["Emission Color"].default_value = hex_rgba(emit)
        bsdf.inputs["Emission Strength"].default_value = strength
    return mat


# ---------------------------------------------------------------- props

def bookshelf(col, wall_y, x=-1.08):
    """Tall bookshelf left of the desk: pastel books, a ball of yarn, a mini plant and a tiny photo."""
    wood = wood_material("shelf_wood", "#D9A877", "#B57F52", scale=(8.0, 8.0, 1.0))
    w, d, h = 0.72, 0.3, 1.8
    y = wall_y - d / 2 - 0.01
    parts = [
        rounded_box("shelf_side", (0.03, d, h), bevel=0.008, loc=(x - w / 2, y, h / 2)),
        rounded_box("shelf_side", (0.03, d, h), bevel=0.008, loc=(x + w / 2, y, h / 2)),
        rounded_box("shelf_back", (w, 0.015, h), bevel=0.004, loc=(x, wall_y - 0.02, h / 2)),
    ]
    levels = [0.04, 0.46, 0.88, 1.3, 1.78]
    for z in levels:
        parts.append(rounded_box("shelf_board", (w, d, 0.03), bevel=0.008, loc=(x, y, z)))
    frame = assign(join(parts, "shelf"), wood)
    objs = [frame]
    rnd = random.Random(4)
    book_mats = [flat(f"book_{i}", c, 0.7) for i, c in enumerate(PASTELS)]
    books = []
    for li, z in enumerate(levels[:-1]):
        bx = x - w / 2 + 0.04
        limit = x + w / 2 - (0.22 if li in (1, 3) else 0.04)  # leave room for knick-knacks
        while bx < limit:
            bw = rnd.uniform(0.025, 0.05)
            bh = rnd.uniform(0.2, 0.33)
            lean = rnd.random() < 0.12
            b = rounded_box("book", (bw, d * rnd.uniform(0.7, 0.88), bh), bevel=0.004, segments=2,
                            loc=(bx + bw / 2, y + 0.01, z + 0.015 + bh / 2),
                            rot=(0, math.radians(14) if lean else 0, 0))
            assign(b, rnd.choice(book_mats))
            books.append(b)
            bx += bw + (0.03 if lean else 0.004)
    objs.append(join(books, "books"))
    # knick-knacks: yarn ball (cat house!), mini cactus pot, tiny framed photo
    yarn = sphere("yarn", 0.055, loc=(x + w / 2 - 0.12, y, levels[1] + 0.07), mat=fabric_material("yarn_mat", "#F7A8C8", 90))
    pot = cylinder("shelf_plantpot", 0.04, 0.07, loc=(x + w / 2 - 0.11, y, levels[3] + 0.05), bevel=0.008,
                   mat=flat("shelf_pot", "#8FE0D6", 0.6))
    cactus = sphere("shelf_plant", 0.035, loc=(x + w / 2 - 0.11, y, levels[3] + 0.12), scale=(1, 1, 1.6),
                    mat=flat("cactus", "#6FBF8E", 0.7))
    objs += [yarn, pot, cactus]
    for o in objs:
        _link(o, col)
    return objs


def poster(name, lines, font, bg, ink, size=(384, 480)):
    path = os.path.join(TEX_DIR, f"{name}.png")
    text_image(path, lines, size=size, font=font, fg=ink, bg=bg, scale=0.32, line_height=1.1)
    return path


def frames(col, wall_y):
    """Framed posters: cute dev / cat art in the site palette."""
    specs = [
        ("poster_hello", ["hello,", "world"], "georgiai.ttf", "#F7A8C8", "#2B2440", (-0.78, 1.78), (0.32, 0.4)),
        ("poster_braces", ["{ }"], "consolab.ttf", "#C3A8FF", "#2B2440", (-0.42, 1.6), (0.22, 0.22)),
        ("poster_miau", ["miau", ":3"], "segoepr.ttf", "#8FE0D6", "#2B2440", (1.18, 1.72), (0.3, 0.38)),
    ]
    wood = wood_material("frame_wood", "#E8C9A4", "#C9A27C", scale=(10, 10, 10))
    objs = []
    for name, lines, font, bg, ink, (fx, fz), (fw, fh) in specs:
        img = poster(name, lines, font, bg, ink, size=(384, int(384 * fh / fw)))
        border = rounded_box(f"frame_{name}", (fw + 0.04, 0.025, fh + 0.04), bevel=0.008, loc=(fx, wall_y - 0.015, fz))
        assign(border, wood)
        bpy.ops.mesh.primitive_plane_add(size=1, location=(fx, wall_y - 0.029, fz), rotation=(math.radians(90), 0, 0))
        art = bpy.context.object
        art.name = name
        art.scale = (fw, fh, 1)
        bpy.ops.object.transform_apply(scale=True)
        mat, nt, bsdf = _principled(f"{name}_mat", 0.8)
        tex = nt.nodes.new("ShaderNodeTexImage")
        tex.image = bpy.data.images.load(img)
        nt.links.new(tex.outputs["Color"], bsdf.inputs["Base Color"])
        assign(art, mat)
        objs += [border, art]
    for o in objs:
        _link(o, col)
    return objs


def curtains(col, wall_y, wx, wz, ww, wh):
    """Two gathered fabric panels and a rod around the window."""
    fabric = fabric_material("curtain_fabric", "#F7A8C8", 220)
    top = wz + wh / 2 + 0.12
    bottom = wz - wh / 2 - 0.18
    objs = [tube("curtain_rod", [(wx - ww / 2 - 0.3, wall_y - 0.08, top + 0.03), (wx, wall_y - 0.08, top + 0.03),
                                 (wx + ww / 2 + 0.3, wall_y - 0.08, top + 0.03)], 0.012,
                 mat=flat("rod", "#F6EFE6", 0.4))]
    for side in (-1, 1):
        x0 = wx + side * (ww / 2 + 0.14)
        width = 0.3
        cols, rows = 36, 16
        verts, faces = [], []
        for r in range(rows):
            t = r / (rows - 1)
            z = top - (top - bottom) * t
            gather = 1 - 0.25 * t * (1 - t) * 4 * 0.5  # slight pinch near the middle
            for c in range(cols):
                u = c / (cols - 1)
                x = x0 + (u - 0.5) * width * gather
                fold = 0.028 * math.sin(u * math.tau * 4.5) * (0.6 + 0.4 * t)
                verts.append((x, wall_y - 0.07 + fold, z))
        for r in range(rows - 1):
            for c in range(cols - 1):
                i = r * cols + c
                faces.append((i, i + 1, i + cols + 1, i + cols))
        me = bpy.data.meshes.new("curtain")
        me.from_pydata(verts, [], faces)
        o = bpy.data.objects.new(f"curtain_{'L' if side < 0 else 'R'}", me)
        bpy.context.scene.collection.objects.link(o)
        sol = o.modifiers.new("solid", "SOLIDIFY")
        sol.thickness = 0.006
        from common import apply_all
        apply_all(o)
        smooth(o)
        assign(o, fabric)
        objs.append(o)
    for o in objs:
        _link(o, col)
    return objs


def string_lights(col, wall_y, x0=-0.95, x1=0.08, z=2.02, sag=0.12, count=14):
    """Fairy lights draped across the wall above the desk (they glow in the bake and bloom on the site)."""
    pts = []
    for i in range(9):
        t = i / 8
        pts.append((x0 + (x1 - x0) * t, wall_y - 0.03, z - sag * math.sin(math.pi * t)))
    wire = tube("string_wire", pts, 0.0025, mat=flat("wire", "#3A3858", 0.5))
    bulbs = []
    warm = flat("bulb_warm", "#FFF1D6", 0.3, emit="#FFE2B0", strength=8)
    pink = flat("bulb_pink", "#FFD6E6", 0.3, emit="#FFB3D1", strength=8)
    for i in range(count):
        t = (i + 0.5) / count
        b = sphere(f"bulb_{i}", 0.012, loc=(x0 + (x1 - x0) * t, wall_y - 0.035, z - sag * math.sin(math.pi * t) - 0.015),
                   scale=(1, 1, 1.3), seg=12, rings=6)
        assign(b, warm if i % 2 else pink)
        bulbs.append(b)
    objs = [wire, join(bulbs, "string_bulbs")]
    for o in objs:
        _link(o, col)
    return objs


def leaf(name, base, direction, length, width):
    """A plump stylised leaf: a flattened ellipsoid tilted along `direction`."""
    d = Vector(direction).normalized()
    centre = Vector(base) + d * length / 2
    o = sphere(name, 1, loc=centre, scale=(width, 0.012, length / 2), seg=16, rings=10)
    # rotate the mesh itself about the leaf centre: sphere() bakes the location into the vertices, so a plain
    # rotation would swing the leaf around the world origin (that flung them across the room)
    rot = d.to_track_quat("Z", "Y").to_matrix().to_4x4()
    o.data.transform(Matrix.Translation(centre) @ rot @ Matrix.Translation(-centre))
    o.data.update()
    return o


def floor_plant(col, x=1.18, y=0.42):
    """Big leafy plant beside the desk."""
    pot = cylinder("floorplant_pot", 0.15, 0.32, loc=(x, y, 0.16), bevel=0.02, mat=flat("floor_pot", "#C3A8FF", 0.55))
    soil = cylinder("floorplant_soil", 0.135, 0.01, loc=(x, y, 0.315), mat=flat("soil", "#4A3326", 0.9))
    rnd = random.Random(9)
    stems, leaves = [], []
    for i in range(9):
        a = i / 9 * math.tau + rnd.uniform(-0.2, 0.2)
        h = rnd.uniform(0.55, 1.05)
        base = Vector((x, y, 0.32))
        tip = base + Vector((math.cos(a) * 0.22, math.sin(a) * 0.18, h))
        mid = (base + tip) / 2 + Vector((math.cos(a) * 0.04, math.sin(a) * 0.04, 0.05))
        stems.append(tube(f"floorplant_stem{i}", [base, mid, tip], 0.008))
        out = Vector((math.cos(a), math.sin(a), 0.35))
        leaves.append(leaf(f"floorplant_leaf{i}", tip, out, rnd.uniform(0.22, 0.3), rnd.uniform(0.08, 0.11)))
    green = flat("plant_green", "#5FAF7A", 0.55)
    stem_o = assign(join(stems, "floorplant_stems"), flat("plant_stem", "#4E8F62", 0.6))
    leaf_o = assign(join(leaves, "floorplant_leaves"), green)
    objs = [pot, soil, stem_o, leaf_o]
    for o in objs:
        _link(o, col)
    return objs


def sill_plant(col, x, y, z):
    """Small potted plant on the window sill (replaces the old tube leaves)."""
    pot = cylinder("pot", 0.06, 0.1, loc=(x, y, z + 0.05), bevel=0.01, mat=flat("pot_mat", "#F7A8C8", 0.6))
    rnd = random.Random(2)
    leaves = []
    for i in range(8):
        a = i / 8 * math.tau
        base = Vector((x, y, z + 0.1))
        leaves.append(leaf(f"sill_leaf{i}", base, (math.cos(a) * 0.6, math.sin(a) * 0.5, 1.0),
                           rnd.uniform(0.1, 0.15), 0.035))
    plant = assign(join(leaves, "plant_leaves"), flat("leaf_mat", "#6FBF8E", 0.6))
    for o in (pot, plant):
        _link(o, col)
    return [pot, plant]


def _link(obj, col):
    for c in list(obj.users_collection):
        c.objects.unlink(obj)
    col.objects.link(obj)
    return obj
