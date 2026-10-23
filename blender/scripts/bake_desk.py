"""Bake the night lighting + AO of the static desk scene (spec §6, §11) -> public/models/desk_scene.glb.

Run after build_desk.py (it reads blender/desk_scene.blend). Static objects are joined into a few groups,
each gets a lightmap UV and one texture = albedo × blurred diffuse lighting × AO + emission
(no view-dependent gloss). The web app renders these meshes unlit.
Kept live: monitor_screen (animated code later), chair (it turns in scene 6, baked on its own), spot_*.
"""
import os
import sys
import time

import bpy
import numpy as np

sys.path.append(os.path.dirname(__file__))
from common import *  # noqa: E402,F403

GROUPS = {
    # name: (object name prefixes, texture size)
    "floor": (("floor",), 2048),
    "room": (("wall", "window_frame", "window_sky", "curtain", "rod", "poster", "frame_", "string"), 2048),
    "props": (("shelf", "books", "yarn", "floorplant", "pot", "plant_leaves"), 2048),
    "desk": (("desk", "drawer_handle", "kb_", "key_", "keyboard", "lamp_", "monitor", "mouse", "postit_"), 2048),
    "chair": (("chair",), 1024),
}
KEEP_LIVE = {"monitor_screen"}
SAMPLES = 96  # lighting pass; its noise is blurred away in texture space
AO_STRENGTH = 0.45  # how much of the AO pass is multiplied in
GAIN = 2.1  # feedback round 2: the room must read as a cosy, lit space, never near-black
BLUR = {"floor": 3.0, "room": 2.0, "props": 2.0, "desk": 2.5, "chair": 2.0}  # gaussian sigma in texels
# bake only these groups (e.g. `blender -b -P bake_desk.py -- floor`); the others reuse their last lightmap
ONLY = set(sys.argv[sys.argv.index("--") + 1:]) if "--" in sys.argv else set()


def members(prefixes):
    env = bpy.data.collections["environment"]
    return [o for o in env.objects if o.type == "MESH" and o.name not in KEEP_LIVE and o.name.startswith(prefixes)]


def prepare_scene():
    bpy.ops.wm.open_mainfile(filepath=os.path.join(BLENDER_DIR, "desk_scene.blend"))
    for name in ("characters_preview",):
        col = bpy.data.collections.get(name)
        if col:
            for o in list(col.all_objects):
                bpy.data.objects.remove(o)
            bpy.data.collections.remove(col)
    for name in ("preview_fill", "preview_cam"):
        if name in bpy.data.objects:
            bpy.data.objects.remove(bpy.data.objects[name])
    # same night rig as build_desk.night_lights (rebuilt so light tweaks there need no full rebuild)
    import build_desk
    for o in list(bpy.data.collections["lights"].objects):
        bpy.data.objects.remove(o)
    bpy.data.collections.remove(bpy.data.collections["lights"])
    build_desk.night_lights(bpy.context.scene, bpy.data.objects["lamp_shade"])
    bulb = bpy.data.materials.get("lamp_bulb")
    if bulb:  # keep the bulb in step with the (25 % softer) lamp without a full rebuild
        bulb.node_tree.nodes["Principled BSDF"].inputs["Emission Strength"].default_value = 9
    sc = bpy.context.scene
    sc.render.engine = "CYCLES"
    sc.cycles.device = "CPU"
    sc.cycles.samples = SAMPLES
    sc.cycles.use_denoising = False
    sc.render.bake.margin = 8
    return sc


def join_group(name, prefixes):
    objs = members(prefixes)
    for o in objs:  # make materials single-user so bake image nodes never leak across groups
        for slot in o.material_slots:
            if slot.material and slot.material.users > 1:
                slot.material = slot.material.copy()
    o = join(objs, f"baked_{name}") if len(objs) > 1 else objs[0]
    o.name = f"baked_{name}"
    return o


def lightmap_uv(obj):
    me = obj.data
    uv = me.uv_layers.new(name="Lightmap")
    me.uv_layers.active = uv  # bake target
    for layer in me.uv_layers:
        layer.active_render = layer.name != "Lightmap"  # keep sampling textures with the original UVs
    active(obj)
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.select_all(action="SELECT")
    bpy.ops.uv.smart_project(angle_limit=1.15, island_margin=0.004, area_weight=1.0, scale_to_bounds=False)
    bpy.ops.uv.pack_islands(margin=0.004, rotate=True)
    bpy.ops.object.mode_set(mode="OBJECT")


def bake_into(obj, image, bake_type, samples, **passes):
    for slot in obj.material_slots:
        nt = slot.material.node_tree
        node = nt.nodes.get("bake_target") or nt.nodes.new("ShaderNodeTexImage")
        node.name = "bake_target"
        node.image = image
        nt.nodes.active = node
    active(obj)
    sc = bpy.context.scene
    sc.cycles.samples = samples
    for k, v in passes.items():
        setattr(sc.render.bake, k, v)
    if bake_type == "AO":
        sc.world.light_settings.distance = 0.12
    t = time.time()
    bpy.ops.object.bake(type=bake_type)
    print(f"  {obj.name} {bake_type}: {time.time() - t:.0f}s")


def new_target(name, size):
    img = bpy.data.images.new(name, size, size, alpha=True, float_buffer=True)
    img.pixels.foreach_set(np.zeros(size * size * 4, dtype=np.float32))  # alpha 0 = never baked
    return img


def read(img, size):
    px = np.empty(size * size * 4, dtype=np.float32)
    img.pixels.foreach_get(px)
    return px.reshape(size, size, 4)


def masked_blur(rgb, mask, sigma):
    """Gaussian blur that only averages baked texels (no black bleeding in from outside the UV islands)."""
    r = int(sigma * 3)
    x = np.arange(-r, r + 1)
    k = np.exp(-(x * x) / (2 * sigma * sigma))
    k /= k.sum()
    num = rgb * mask[..., None]
    den = mask.astype(np.float32)
    for axis in (0, 1):
        pad = [(r, r) if a == axis else (0, 0) for a in range(num.ndim)]
        n = np.pad(num, pad, mode="edge")
        d = np.pad(den, pad[:2], mode="edge")
        num = sum(w * np.take(n, range(i, i + rgb.shape[axis]), axis=axis) for i, w in enumerate(k))
        den = sum(w * np.take(d, range(i, i + rgb.shape[axis]), axis=axis) for i, w in enumerate(k))
    return num / np.maximum(den, 1e-6)[..., None]


def bake_group(name, prefixes, size):
    """Bakes four passes and combines them:
    albedo (sharp, noise-free: keeps post-it text crisp) × lighting (noisy at night, so blurred in texture
    space) × AO + emission (screen glow, sky, bulb)."""
    obj = join_group(name, prefixes)
    lightmap_uv(obj)
    png = os.path.join(TEX_DIR, f"lightmap_{name}.png")
    if ONLY and name not in ONLY and os.path.exists(png):
        return finish(obj, name, png)  # same deterministic UVs, reuse the last bake
    irr, alb, emit, ao = (new_target(f"{p}_{name}", size) for p in ("irr", "alb", "emit", "ao"))
    off = dict(use_pass_direct=False, use_pass_indirect=False, use_pass_color=False)
    bake_into(obj, irr, "DIFFUSE", SAMPLES, use_pass_direct=True, use_pass_indirect=True, use_pass_color=False)
    bake_into(obj, alb, "DIFFUSE", 4, **{**off, "use_pass_color": True})
    bake_into(obj, emit, "EMIT", 1)
    bake_into(obj, ao, "AO", 48)

    i, a, e, o = (read(img, size) for img in (irr, alb, emit, ao))
    mask = i[..., 3] > 0.5
    lit = masked_blur(i[..., :3], mask, BLUR[name])
    occ = (1 - AO_STRENGTH) + AO_STRENGTH * o[..., :1]
    out_px = np.ones((size, size, 4), dtype=np.float32)
    out_px[..., :3] = a[..., :3] * lit * occ * GAIN + e[..., :3]
    out = bpy.data.images.new(f"lightmap_{name}", size, size, float_buffer=False)
    out.pixels.foreach_set(out_px.ravel())
    out.filepath_raw = png
    out.file_format = "PNG"
    out.save()
    for img in (irr, alb, emit, ao):
        bpy.data.images.remove(img)
    return finish(obj, name, png)


def finish(obj, name, png):
    """One plain material on the lightmap UV only (the web app shows it unlit)."""
    me = obj.data
    for layer in list(me.uv_layers):
        if layer.name != "Lightmap":
            me.uv_layers.remove(layer)
    mat = material(f"baked_{name}", "#FFFFFF", rough=1.0, image=png)
    me.materials.clear()
    me.materials.append(mat)
    return obj


if __name__ == "__main__":
    t0 = time.time()
    sc = prepare_scene()
    baked = []
    for name, (prefixes, size) in GROUPS.items():
        print(f"baking {name} ({size}px)")
        baked.append(bake_group(name, prefixes, size))
    # the chair keeps its name: the app turns it in scene 6
    chair = bpy.data.objects["baked_chair"]
    chair.name = "chair"
    env = bpy.data.collections["environment"]
    export = baked + [bpy.data.objects["monitor_screen"]] + [o for o in env.objects if o.name.startswith("spot_")]
    save_blend("desk_baked.blend")
    export_glb(os.path.join(MODELS_DIR, "desk_scene.glb"), export)
    print(f"done in {(time.time() - t0) / 60:.1f} min")
