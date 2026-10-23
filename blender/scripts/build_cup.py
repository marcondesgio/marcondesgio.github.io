"""Mug "WORLD'S BEST DEV" (ref docs/71hYZJeC4EL.jpg) -> blender/cup.blend, public/models/cup.glb."""
import math
import os
import sys

import bpy

sys.path.append(os.path.dirname(__file__))
from common import *  # noqa: E402,F403

H = 0.095          # height
R = 0.041          # outer radius
WALL = 0.0045
COFFEE_LEVEL = 0.082


def label_textures():
    # Texture wraps the full circumference (U 0..1). Text sits centered at U=0.5,
    # which faces -Y (the camera side) once the UVs are laid out below.
    out = {}
    for lang, lines in (("en", ["WORLD'S", "BEST", "DEV"]), ("pt", ["MELHOR", "DEV DO", "MUNDO"])):
        p = os.path.join(TEX_DIR, f"cup_label_{lang}.png")
        # canvas aspect = circumference / printable height
        text_image(p, lines, size=(2048, 564), font="arialbd.ttf", fg="#141414", bg="#FBFAF7",
                   scale=0.6, line_height=0.98, offset=(0, -0.2))
        out[lang] = p
    return out


def build():
    reset_scene()
    tex = label_textures()

    # Body: lathe profile (outer wall, rim, inner wall, inner floor) via screw modifier
    prof = [
        (0.0, 0.0), (R - 0.004, 0.0), (R - 0.0005, 0.002), (R, 0.006),
        (R, H - 0.003), (R - 0.0012, H), (R - WALL + 0.0012, H), (R - WALL, H - 0.003),
        (R - WALL, 0.012), (R - WALL - 0.004, 0.008), (0.0, 0.008),
    ]
    me = bpy.data.meshes.new("cup_profile")
    me.from_pydata([(x, 0, z) for x, z in prof], [(i, i + 1) for i in range(len(prof) - 1)], [])
    body = bpy.data.objects.new("cup_body", me)
    bpy.context.scene.collection.objects.link(body)
    scr = body.modifiers.new("lathe", "SCREW")
    scr.axis = "Z"
    scr.steps = 64
    scr.render_steps = 64
    scr.use_merge_vertices = True
    scr.use_normal_calculate = True
    apply_all(body)
    smooth(body, 50)

    # Cylindrical UVs: U by angle (0.5 at -Y), V by height. Only outer wall gets the label band.
    import bmesh
    bm = bmesh.new()
    bm.from_mesh(body.data)
    uv = bm.loops.layers.uv.new("UVMap")
    band_lo, band_hi = 0.012, H - 0.012
    for f in bm.faces:
        cx = sum((l.vert.co.x for l in f.loops)) / len(f.loops)
        cy = sum((l.vert.co.y for l in f.loops)) / len(f.loops)
        fa = math.atan2(cy, cx)
        for l in f.loops:
            co = l.vert.co
            a = math.atan2(co.y, co.x)
            # keep the seam continuous inside a face
            if abs(a - fa) > math.pi:
                a += 2 * math.pi if a < fa else -2 * math.pi
            u = ((a + math.pi / 2) / (2 * math.pi)) + 0.5
            r = math.hypot(co.x, co.y)
            outer = r > R - 0.001
            v = (co.z - band_lo) / (band_hi - band_lo) if outer else -1.0
            l[uv].uv = (u, v)
    bm.to_mesh(body.data)
    bm.free()

    # Ceramic with label: image only where V in [0,1] (texture extension = CLIP -> white elsewhere)
    mat = bpy.data.materials.new("cup_ceramic")
    mat.use_nodes = True
    nt = mat.node_tree
    bsdf = nt.nodes["Principled BSDF"]
    bsdf.inputs["Roughness"].default_value = 0.22
    bsdf.inputs["Coat Weight"].default_value = 0.3
    img = nt.nodes.new("ShaderNodeTexImage")
    img.name = "label"
    img.image = bpy.data.images.load(tex["en"])
    img.extension = "EXTEND"
    nt.links.new(img.outputs["Color"], bsdf.inputs["Base Color"])
    assign(body, mat)
    # the image's border colour is the ceramic white, so EXTEND keeps rim/inside white

    # Handle: thick "C" tube on +X... rotated so text faces -Y and handle sits at +X
    hp = [(R - 0.004, 0, H * 0.80), (R + 0.012, 0, H * 0.84), (R + 0.03, 0, H * 0.72), (R + 0.032, 0, H * 0.5),
          (R + 0.028, 0, H * 0.3), (R + 0.012, 0, H * 0.2), (R - 0.004, 0, H * 0.22)]
    handle = tube("cup_handle", hp, 0.0062, bevel_res=4, resolution=10)
    handle.scale.y = 0.9
    white = material("cup_white", "#FBFAF7", rough=0.22)
    assign(handle, white)

    # Coffee surface (separate so loader scene / spill can drive it)
    bpy.ops.mesh.primitive_circle_add(vertices=64, radius=R - WALL - 0.0002, fill_type="NGON",
                                      location=(0, 0, COFFEE_LEVEL))
    coffee = bpy.context.object
    coffee.name = "cup_coffee"
    assign(coffee, material("coffee", "#22130C", rough=0.12))

    cup = join([body, handle], "cup")
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    coffee.parent = cup

    # Steam placeholder empty (runtime shader in three.js)
    steam = bpy.data.objects.new("cup_steam_anchor", None)
    steam.location = (0, 0, H + 0.01)
    steam.parent = cup
    bpy.context.scene.collection.objects.link(steam)
    return cup, coffee, steam


if __name__ == "__main__":
    cup, coffee, steam = build()
    save_blend("cup.blend")
    export_glb(os.path.join(MODELS_DIR, "cup.glb"), [cup, coffee, steam])

    sc = bpy.context.scene
    studio(sc, target=(0, 0, 0.05), dist=0.4)
    sc.render.film_transparent = False
    render_views(sc, "cup", target=(0, 0, 0.045), dist=0.32, height=0.06, lens=70,
                 views=("front", "three_quarter"), res=(900, 800),
                 extra=[("top", -90, 0.32)])
