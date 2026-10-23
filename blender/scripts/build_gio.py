"""Giovanna, designer-toy style (refs: docs/54c5550….jpg, 8025aaf….jpg, character sheet, eu_e_tutu)
-> blender/gio.blend, public/models/gio.glb.

Faces -Y, feet at the origin, 1 unit = 1 m. Body parts are rigid "action figure" segments, each
weighted 100% to one bone, so the rig deforms cleanly in glTF without weight painting.
"""
import math
import os
import sys

import bmesh
import bpy
from mathutils import Matrix, Vector, noise

sys.path.append(os.path.dirname(__file__))
from common import *  # noqa: E402,F403

HEAD_C = Vector((0, 0, 1.2))
HEAD_R = Vector((0.17, 0.155, 0.16))
ARM_ANGLE = math.radians(38)


def side_name(s):
    return "L" if s > 0 else "R"  # her left is +X (she faces -Y)


# ---------------------------------------------------------------- skeleton

def skeleton():
    """bone -> (head, tail, parent)."""
    b = {
        # root carries walking/turning; hips sit at the rest pelvis
        "root": ((0, 0, 0), (0, -0.15, 0), None),
        "hips": ((0, 0, 0.6), (0, 0, 0.72), "root"),
        "spine": ((0, 0, 0.72), (0, 0, 0.95), "hips"),
        "neck": ((0, 0, 0.95), (0, 0, 1.05), "spine"),
        "head": ((0, 0, 1.05), (0, 0, 1.38), "neck"),
    }
    for s in (1, -1):
        n = side_name(s)
        d = Vector((math.sin(ARM_ANGLE) * s, 0, -math.cos(ARM_ANGLE)))
        sh = Vector((0.165 * s, 0, 0.925))
        el = sh + d * 0.21
        wr = el + d * 0.19
        b[f"upper_arm.{n}"] = (tuple(sh), tuple(el), "spine")
        b[f"forearm.{n}"] = (tuple(el), tuple(wr), f"upper_arm.{n}")
        b[f"hand.{n}"] = (tuple(wr), tuple(wr + d * 0.065), f"forearm.{n}")
        for f, (y, ln) in FINGERS.items():
            if f == "thumb":
                continue
            base = hand_to_world(s, Vector((0, y, -0.068)))
            tip = hand_to_world(s, Vector((0, y, -0.068 - ln)))
            b[f"{f}.{n}"] = (tuple(base), tuple(tip), f"hand.{n}")
        tb = hand_to_world(s, Vector((0.004 * s, -0.03, -0.028)))
        tt = hand_to_world(s, Vector((0.012 * s, -0.058, -0.06)))
        b[f"thumb.{n}"] = (tuple(tb), tuple(tt), f"hand.{n}")
        b[f"thigh.{n}"] = ((0.08 * s, 0, 0.6), (0.085 * s, 0, 0.34), "hips")
        b[f"shin.{n}"] = ((0.085 * s, 0, 0.34), (0.085 * s, 0, 0.085), f"thigh.{n}")
        b[f"foot.{n}"] = ((0.085 * s, 0, 0.085), (0.085 * s, -0.13, 0.03), f"shin.{n}")
    return b


FINGERS = {"index": (-0.021, 0.04), "middle": (-0.006, 0.044), "ring": (0.009, 0.041), "pinky": (0.023, 0.033),
           "thumb": (0, 0)}


def hand_matrix(s):
    """Local hand frame: fingers point -Z, thumb toward -Y. Placed at the wrist."""
    sh = Vector((0.165 * s, 0, 0.925))
    d = Vector((math.sin(ARM_ANGLE) * s, 0, -math.cos(ARM_ANGLE)))
    wr = sh + d * 0.4
    return Matrix.Translation(wr) @ Matrix.Rotation(-ARM_ANGLE * s, 4, "Y")


def hand_to_world(s, v):
    return hand_matrix(s) @ v


# ---------------------------------------------------------------- parts

def tag(obj, bone):
    vg = obj.vertex_groups.new(name=bone)
    vg.add([v.index for v in obj.data.vertices], 1.0, "REPLACE")
    return obj


def blob(name, objs, voxel, iters=8):
    o = join(objs, name)
    rm = o.modifiers.new("remesh", "REMESH")
    rm.mode = "VOXEL"
    rm.voxel_size = voxel
    apply_all(o)
    if iters:
        sm = o.modifiers.new("smooth", "CORRECTIVE_SMOOTH")
        sm.iterations = iters
        sm.use_only_smooth = True
        apply_all(o)
    smooth(o)
    return o


def capsule(name, a, b, r, radii=None):
    a, b = Vector(a), Vector(b)
    return tube(name, [a, (a + b) / 2, b], r, bevel_res=6, radii=radii)


def head_surface(head, x, z, inset=0.0):
    bpy.context.view_layer.update()
    mw = head.matrix_world
    inv = mw.inverted()
    ok, loc, nrm, _ = head.ray_cast(inv @ Vector((x, -1, z)), (inv.to_3x3() @ Vector((0, 1, 0))).normalized())
    assert ok, (x, z)
    nrm = (mw.to_3x3() @ nrm).normalized()
    return mw @ loc - nrm * inset, nrm


def build_head(M):
    head = blob("head_skin", [
        sphere("h", 1, loc=HEAD_C, scale=HEAD_R),
        sphere("jaw", 1, loc=(0, -0.012, 1.13), scale=(0.145, 0.138, 0.1)),
        sphere("ear_l", 1, loc=(0.165, 0.0, 1.17), scale=(0.022, 0.035, 0.045)),
        sphere("ear_r", 1, loc=(-0.165, 0.0, 1.17), scale=(0.022, 0.035, 0.045)),
    ], 0.006, 6)
    decimate(head, 0.35)
    assign(head, M["skin"])
    parts = [head]

    for s in (1, -1):
        n = side_name(s)
        p, nrm = head_surface(head, 0.062 * s, 1.165)
        eye = sphere(f"eye_{n}", 1, loc=p, scale=(0.024, 0.009, 0.031))
        parts.append(assign(eye, M["eye"]))
        hl = sphere(f"eye_hl_{n}", 0.0075, loc=p + Vector((0.008 * s, -0.007, 0.012)))
        parts.append(assign(hl, M["white"]))
        # brows: gentle arcs
        pts = []
        for t in (0.0, 0.5, 1.0):
            x = (0.038 + 0.05 * t) * s
            z = 1.222 + 0.008 * math.sin(math.pi * t) - 0.004 * t
            q, _ = head_surface(head, x, z, -0.002)
            pts.append(q)
        parts.append(assign(tube(f"brow_{n}", pts, 0.0035, bevel_res=2), M["brow"]))
        # blush
        q, nrm = head_surface(head, 0.102 * s, 1.11, -0.0005)
        parts.append(assign(sphere(f"blush_{n}", 1, loc=q, scale=(0.022, 0.004, 0.014)), M["blush"]))

    # nose bump, smile
    q, nrm = head_surface(head, 0, 1.13, 0.006)
    nose = sphere("nose", 0.014, loc=q, scale=(1, 0.9, 0.8))
    parts.append(assign(nose, M["skin"]))
    pts = [head_surface(head, x, 1.077 + 0.006 * (abs(x) / 0.022) ** 2, -0.001)[0] for x in (-0.022, 0, 0.022)]
    parts.append(assign(tube("mouth", pts, 0.0028, bevel_res=2), M["mouth"]))

    # piercings: ring on her LEFT nostril (+X) and a septum ring
    nose_front = q + Vector((0, -0.012, -0.004))
    bpy.ops.mesh.primitive_torus_add(major_radius=0.0065, minor_radius=0.0013, major_segments=24, minor_segments=8,
                                     location=nose_front + Vector((0, 0.004, -0.009)), rotation=(math.radians(90), 0, 0))
    septum = bpy.context.object
    septum.name = "piercing_septum"
    bpy.ops.mesh.primitive_torus_add(major_radius=0.0058, minor_radius=0.0012, major_segments=24, minor_segments=8,
                                     location=q + Vector((0.012, -0.004, -0.008)),
                                     rotation=(math.radians(90), 0, math.radians(70)))
    nostril = bpy.context.object
    nostril.name = "piercing_nostril_L"
    for o in (septum, nostril):
        smooth(o)
        parts.append(assign(o, M["metal"]))

    body_head = join(parts, "gio_head")
    return tag(body_head, "head"), head


def build_hair(M):
    """Chunky sculpted hair: scalp cap + a wavy grooved curtain to the shoulders, fused by a voxel remesh."""
    cx, cy = 0.0, 0.012
    cap = sphere("hair_cap", 1, loc=(cx, cy, 1.215), scale=(0.186, 0.176, 0.182), seg=48, rings=24)
    bm = bmesh.new()
    bm.from_mesh(cap.data)
    mw = cap.matrix_world

    def kill_face(f):
        c = mw @ f.calc_center_median()
        # face opening with a soft, side-parted hairline (higher on her right, -X)
        hairline = 1.305 + 0.025 * max(0.0, -c.x) / 0.15 - 0.03 * (abs(c.x) / 0.15) ** 2
        return (c.y < -0.03 and c.z < hairline and abs(c.x) < 0.152) or c.z < 1.08

    bmesh.ops.delete(bm, geom=[f for f in bm.faces if kill_face(f)], context="FACES")
    bm.to_mesh(cap.data)
    bm.free()
    sol = cap.modifiers.new("solid", "SOLIDIFY")
    sol.thickness = 0.022
    apply_all(cap)

    # curtain: grid wrapped around the back and sides, grooves = locks, scalloped wavy hem
    rows, cols = 26, 72
    a0, a1 = math.radians(-128), math.radians(128)  # 0 = straight back (+Y)
    verts, faces = [], []
    for r in range(rows):
        t = r / (rows - 1)
        for c in range(cols):
            a = a0 + (a1 - a0) * c / (cols - 1)
            hem = 0.935 + 0.022 * math.sin(a * 9.0) + 0.01 * math.sin(a * 23.0)
            z = 1.35 + (hem - 1.35) * t
            # follow the scalp above the ears, then flare out toward the shoulders
            base = 0.184 * math.sqrt(max(0.0, 1 - ((z - 1.215) / 0.19) ** 2)) if z > 1.215 else 0.184
            low = max(0.0, (1.215 - z) / (1.215 - hem))
            groove = 0.006 * (math.sin(a * 22.0 + t * 2.5) ** 2) * min(1.0, t * 3)
            wave = 0.012 * math.sin(t * math.pi * 2.6 + a * 1.5) * low
            rad = base - 0.012 + 0.045 * low ** 1.4 + wave - groove + 0.012 * low * (abs(a) / a1)
            verts.append((cx + math.sin(a) * rad, cy + math.cos(a) * rad * 0.97, z))
    for r in range(rows - 1):
        for c in range(cols - 1):
            i = r * cols + c
            faces.append((i, i + 1, i + cols + 1, i + cols))
    me = bpy.data.meshes.new("curtain")
    me.from_pydata(verts, [], faces)
    curtain = bpy.data.objects.new("curtain", me)
    bpy.context.scene.collection.objects.link(curtain)
    sol = curtain.modifiers.new("solid", "SOLIDIFY")
    sol.thickness = 0.03
    sol.offset = 1.0
    apply_all(curtain)

    # side-parted swoop over the forehead, hugging the scalp, plus face-framing locks
    def on_scalp(x, z, lift=0.012):
        k = max(1 - (x / 0.19) ** 2 - ((z - 1.215) / 0.185) ** 2, 0.0)
        return (x, cy - 0.178 * math.sqrt(k) - lift, z)

    swoops = [
        tube("swoop_r", [on_scalp(0.045, 1.37), on_scalp(-0.03, 1.345), on_scalp(-0.1, 1.3), on_scalp(-0.15, 1.235),
                         (-0.18, -0.07, 1.14), (-0.195, -0.05, 1.02)], 0.03, radii=[0.7, 1.0, 1.0, 1.0, 0.9, 0.7]),
        tube("swoop_l", [on_scalp(0.06, 1.37), on_scalp(0.11, 1.32), on_scalp(0.15, 1.25),
                         (0.18, -0.07, 1.15), (0.195, -0.05, 1.02)], 0.026, radii=[0.7, 1.0, 1.0, 0.9, 0.7]),
    ]
    hair = blob("gio_hair", [cap, curtain] + swoops, 0.006, 10)
    decimate(hair, 0.3)

    def hair_col(co, n):
        # soft sun-kissed patches on the upper, outward-facing locks
        k = noise.noise(Vector((co.x * 9, co.y * 9, co.z * 2.5)))
        return "hair_light" if k > 0.22 and n.z > -0.2 else "hair"

    paint_vertex_colors(hair, hair_col)
    assign(hair, M["hair"])
    return tag(hair, "head")


def build_glasses(M, head):
    parts = []
    eye_y = head_surface(head, 0.062, 1.165)[0].y
    for s in (1, -1):
        bpy.ops.mesh.primitive_torus_add(major_radius=0.04, minor_radius=0.0045, major_segments=40, minor_segments=8,
                                         location=(0.064 * s, eye_y - 0.03, 1.165), rotation=(math.radians(90), 0, 0))
        rim = bpy.context.object
        rim.scale = (1.12, 0.85, 1)
        smooth(rim)
        parts.append(rim)
        parts.append(tube(f"temple_{s}", [(0.108 * s, eye_y - 0.028, 1.175), (0.165 * s, eye_y + 0.02, 1.18),
                                          (0.17 * s, 0.03, 1.17)], 0.0035, bevel_res=2))
    parts.append(tube("bridge", [(-0.02, eye_y - 0.032, 1.17), (0, eye_y - 0.036, 1.178), (0.02, eye_y - 0.032, 1.17)],
                      0.004, bevel_res=2))
    g = join(parts, "gio_glasses")
    assign(g, M["frame"])
    return tag(g, "head")


def build_torso(M):
    shirt = blob("shirt", [
        sphere("chest", 1, loc=(0, 0, 0.8), scale=(0.155, 0.108, 0.2)),
        sphere("shoulders", 1, loc=(0, 0, 0.9), scale=(0.175, 0.1, 0.07)),
        sphere("hem", 1, loc=(0, 0, 0.655), scale=(0.165, 0.118, 0.06)),
    ], 0.008, 6)
    assign(shirt, M["shirt"])
    tag(shirt, "spine")
    neck = cylinder("neck", 0.042, 0.16, loc=(0, 0.005, 1.0), mat=M["skin"])
    tag(neck, "neck")
    pelvis = sphere("pelvis", 1, loc=(0, 0, 0.615), scale=(0.15, 0.1, 0.085))
    assign(pelvis, M["jeans"])
    pockets = []
    for s in (1, -1):
        pk = rounded_box(f"pocket_{s}", (0.07, 0.008, 0.07), bevel=0.012, loc=(0.06 * s, 0.1, 0.57),
                         rot=(math.radians(-10), 0, 0))
        pockets.append(assign(pk, M["jeans_dark"]))
    pelvis = join([pelvis] + pockets, "pelvis")
    return [shirt, neck, tag(pelvis, "hips")]


def build_arm(M, s):
    n = side_name(s)
    d = Vector((math.sin(ARM_ANGLE) * s, 0, -math.cos(ARM_ANGLE)))
    sh = Vector((0.165 * s, 0, 0.925))
    el = sh + d * 0.21
    wr = el + d * 0.19
    sleeve = capsule(f"sleeve_{n}", sh - d * 0.01, sh + d * 0.11, 0.056, radii=[1.0, 1.0, 1.05])
    shoulder = sphere(f"shoulder_{n}", 0.058, loc=sh)
    upper = join([assign(sleeve, M["shirt"]), assign(shoulder, M["shirt"]),
                  assign(capsule(f"uarm_{n}", sh, el, 0.045), M["skin"])], f"upper_arm_{n}")
    fore = join([assign(capsule(f"farm_{n}", el, wr, 0.042, radii=[1.0, 0.95, 0.85]), M["skin"]),
                 assign(sphere(f"elbow_{n}", 0.044, loc=el), M["skin"])], f"forearm_{n}")

    hm = hand_matrix(s)
    palm = sphere(f"palm_{n}", 1, loc=(0, 0, -0.036), scale=(0.024, 0.04, 0.042))
    palm_parts = [palm]
    fingers = []
    for f, (y, ln) in FINGERS.items():
        if f == "thumb":
            fo = capsule(f"{f}_{n}", (0.004 * s, -0.03, -0.028), (0.012 * s, -0.058, -0.06), 0.0105)
        else:
            fo = capsule(f"{f}_{n}", (0, y, -0.062), (0, y, -0.068 - ln), 0.0108)
        fo.data.transform(hm)
        fingers.append(tag(assign(fo, M["skin"]), f"{f}.{n}"))
    for o in palm_parts:
        o.data.transform(hm)
        assign(o, M["skin"])
    hand = tag(join(palm_parts, f"hand_{n}"), f"hand.{n}")
    return [tag(upper, f"upper_arm.{n}"), tag(fore, f"forearm.{n}"), hand] + fingers


def build_leg(M, s):
    n = side_name(s)
    x = 0.085 * s
    thigh = assign(capsule(f"thigh_{n}", (0.08 * s, 0, 0.62), (x, 0, 0.33), 0.068, radii=[1.05, 1.0, 0.96]), M["jeans"])
    knee = assign(sphere(f"knee_{n}", 0.064, loc=(x, 0, 0.34)), M["jeans"])
    shin = assign(capsule(f"shin_{n}", (x, 0, 0.34), (x, 0, 0.1), 0.062, radii=[1.0, 1.0, 1.06]), M["jeans"])
    bpy.ops.mesh.primitive_torus_add(major_radius=0.06, minor_radius=0.012, location=(x, 0, 0.1))
    cuff = assign(bpy.context.object, M["jeans_dark"])
    smooth(cuff)

    # old-school skate shoe: white sole + toe cap, black upper, curved side stripe (no logo)
    sole = rounded_box(f"sole_{n}", (0.112, 0.265, 0.03), bevel=0.013, loc=(x, -0.04, 0.018), mat=M["sole"])
    upper = blob(f"upper_{n}", [
        sphere("u1", 1, loc=(x, -0.025, 0.06), scale=(0.059, 0.128, 0.056)),
        sphere("u2", 1, loc=(x, 0.03, 0.09), scale=(0.058, 0.075, 0.055)),
    ], 0.005, 4)
    assign(upper, M["shoe"])
    toe = sphere(f"toe_{n}", 1, loc=(x, -0.118, 0.034), scale=(0.054, 0.042, 0.025))
    assign(toe, M["sole"])
    stripes = []
    for side in (1, -1):
        sx = x + 0.058 * side
        stripes.append(tube(f"stripe_{n}{side}", [(sx, 0.07, 0.045), (sx + 0.003 * side, 0.0, 0.085),
                                                  (sx + 0.002 * side, -0.07, 0.05)], 0.006, bevel_res=2))
    for st in stripes:
        assign(st, M["sole"])
    collar = assign(cylinder(f"collar_{n}", 0.05, 0.02, loc=(x, 0.03, 0.125)), M["sole"])
    foot = join([sole, upper, toe, collar] + stripes, f"shoe_{n}")
    return [tag(join([thigh], f"thigh_{n}"), f"thigh.{n}"),
            tag(join([knee, shin, cuff], f"shin_{n}"), f"shin.{n}"),
            tag(foot, f"foot.{n}")]


def materials():
    return {
        "skin": material("gio_skin", "skin", rough=0.55),
        "shirt": material("gio_shirt", "shirt", rough=0.85),
        "jeans": material("gio_jeans", "jeans", rough=0.8),
        "jeans_dark": material("gio_jeans_dark", "#435E86", rough=0.8),
        "shoe": material("gio_shoe", "shoe", rough=0.45),
        "sole": material("gio_sole", "sole", rough=0.5),
        "hair": vcol_material("gio_hair", rough=0.55),
        "eye": material("gio_eye", "#2A1C15", rough=0.15),
        "white": material("gio_eye_hl", "#FFFFFF", rough=0.2, emit="#FFFFFF", emit_strength=0.8),
        "brow": material("gio_brow", "#6A4A33", rough=0.6),
        "blush": material("gio_blush", "#F2B0A2", rough=0.7),
        "mouth": material("gio_mouth", "#A9564A", rough=0.5),
        "metal": material("gio_piercing", "piercing", rough=0.25, metal=1.0),
        "frame": material("gio_glasses", "#2A2328", rough=0.3),
    }


def build_armature():
    arm_data = bpy.data.armatures.new("gio_rig")
    rig = bpy.data.objects.new("gio_rig", arm_data)
    bpy.context.scene.collection.objects.link(rig)
    active(rig)
    bpy.ops.object.mode_set(mode="EDIT")
    sk = skeleton()
    for name, (h, t, _) in sk.items():
        eb = arm_data.edit_bones.new(name)
        eb.head, eb.tail = h, t
    for name, (_, _, parent) in sk.items():
        if parent:
            eb = arm_data.edit_bones[name]
            eb.parent = arm_data.edit_bones[parent]
            eb.use_connect = False
    bpy.ops.object.mode_set(mode="OBJECT")
    return rig


def bind(rig, obj):
    m = obj.modifiers.new("rig", "ARMATURE")
    m.object = rig
    obj.parent = rig
    return obj


def build():
    reset_scene()
    M = materials()
    head, head_skin = build_head(M)
    hair = build_hair(M)
    glasses = build_glasses(M, head_skin)
    body_parts = [head] + build_torso(M)
    for s in (1, -1):
        body_parts += build_arm(M, s) + build_leg(M, s)
    body = join(body_parts, "gio_body")
    rig = build_armature()
    for o in (body, hair, glasses):
        bind(rig, o)
    return rig, body, hair, glasses



if __name__ == "__main__":
    import gio_anim

    rig, body, hair, glasses = build()
    extras = gio_anim.add_animations(rig)
    gio_anim.reset(rig)
    save_blend("gio.blend")
    export_glb(os.path.join(MODELS_DIR, "gio.glb"), [rig, body, hair, glasses] + extras, animations=True)
    sc = bpy.context.scene
    studio(sc, target=(0, 0, 0.75), dist=4.5)
    render_views(sc, "gio", target=(0, 0, 0.72), dist=3.6, height=0.25, lens=55,
                 views=("front", "three_quarter", "side", "back"), res=(800, 1100))
    render_views(sc, "gio", target=(0, -0.05, 1.18), dist=1.0, height=0.02, lens=60, views=(), res=(900, 900),
                 extra=[("face", -90, 0.02), ("face_profile", -20, 0.02)])
