"""Tutu (Trufa), snowshoe cat (refs: docs/1249d238….jpg, character sheet, eu_e_tutu)
-> blender/tutu.blend, public/models/tutu.glb. The cat faces -Y; 1 unit = 1 m."""
import math
import os
import sys

import bpy
from mathutils import Matrix, Quaternion, Vector, noise

sys.path.append(os.path.dirname(__file__))
from common import *  # noqa: E402,F403

LOW = 0.02  # how much shorter the legs are than a "real" cat
SCALE = 0.78  # whole-cat scale so she reads right next to the 9.5 cm mug
HEAD_C = Vector((0, -0.15, 0.262))
HEAD_R = Vector((0.11, 0.094, 0.092))
EYE_X, EYE_Z = 0.047, 0.272
MUZZLE_C = Vector((0, -0.24, 0.232))
# long thick tail, S-curve with a little hook at the tip (z already lowered by LOW)
TAIL_PTS = [(0, 0.17, 0.12), (0, 0.24, 0.13), (0.01, 0.29, 0.22), (0.03, 0.3, 0.31), (0.035, 0.27, 0.39),
            (0.005, 0.235, 0.43), (-0.03, 0.225, 0.425)]


def ellipsoid(name, c, r, rot=(0, 0, 0)):
    return sphere(name, 1.0, loc=c, scale=r, rot=rot, seg=32, rings=16)


def capsule(name, a, b, r):
    return tube(name, [a, ((a[0] + b[0]) / 2, (a[1] + b[1]) / 2, (a[2] + b[2]) / 2), b], r, bevel_res=6)


def surface_y(x, z):
    """Front surface of the head ellipsoid at (x, z)."""
    k = 1 - (x / HEAD_R.x) ** 2 - ((z - HEAD_C.z) / HEAD_R.z) ** 2
    return HEAD_C.y - HEAD_R.y * math.sqrt(max(k, 0))


def body_mesh():
    z = -LOW
    parts = [
        ellipsoid("torso", (0, 0.035, 0.145 + z), (0.1, 0.16, 0.09)),
        ellipsoid("belly", (0, 0.03, 0.115 + z), (0.108, 0.13, 0.08)),
        ellipsoid("chest", (0, -0.085, 0.165 + z), (0.09, 0.085, 0.09)),
        ellipsoid("haunch_l", (0.06, 0.12, 0.13 + z), (0.052, 0.075, 0.07)),
        ellipsoid("haunch_r", (-0.06, 0.12, 0.13 + z), (0.052, 0.075, 0.07)),
        ellipsoid("head", HEAD_C, HEAD_R),
        ellipsoid("cheek_l", (0.06, -0.19, 0.228), (0.05, 0.044, 0.04)),
        ellipsoid("cheek_r", (-0.06, -0.19, 0.228), (0.05, 0.044, 0.04)),
        ellipsoid("muzzle", MUZZLE_C, (0.034, 0.022, 0.024)),
        ellipsoid("chin", (0, -0.222, 0.207), (0.028, 0.02, 0.016)),
    ]
    for sx in (1, -1):
        for y, top in ((-0.095, 0.14 + z), (0.13, 0.1 + z)):
            x = 0.052 * sx
            parts.append(capsule(f"leg_{sx}_{y}", (x, y, top), (x, y - 0.004, 0.03), 0.032))
            parts.append(ellipsoid(f"paw_{sx}_{y}", (x, y - 0.012, 0.02), (0.034, 0.04, 0.02)))
    parts.append(tube("tail", TAIL_PTS, 0.022, radii=[1.25, 1.1, 1.0, 0.95, 0.9, 0.85, 0.75], bevel_res=6))

    body = join(parts, "tutu_body")
    rm = body.modifiers.new("remesh", "REMESH")
    rm.mode = "VOXEL"
    rm.voxel_size = 0.0035
    apply_all(body)
    sm = body.modifiers.new("smooth", "CORRECTIVE_SMOOTH")
    sm.iterations = 14
    sm.use_only_smooth = True
    apply_all(body)
    decimate(body, 0.4)  # painting per corner in Python is slow on the full voxel mesh
    return body


def fur_color(co, n):
    x, y, z = co
    j = noise.noise(co * 14) * 0.009  # wobbly patch borders
    p = Vector((x, y, z))
    # tail -> chocolate points, blending from saddle at the base
    if y > 0.2 and z > 0.12:
        return "fur_points" if (y > 0.235 or z > 0.18) else "fur_saddle"
    if y < -0.075 and z > 0.17:  # head
        front = n.y < -0.25
        if (p - MUZZLE_C).length < 0.048 + j and z > 0.2:
            return "fur_muzzle"
        # white inverted-V blaze, leaning to the viewer's left (-X) as it goes down
        if front and 0.245 < z < 0.36:
            centre = -(0.36 - z) * 0.16
            half_w = 0.006 + (0.36 - z) * 0.2
            if abs(x - centre) < half_w + j * 0.5:
                return "fur_white"
        # chocolate mask around the eyes, merging into the muzzle
        for sx in (1, -1):
            eye_c = Vector((EYE_X * sx, surface_y(EYE_X, EYE_Z), EYE_Z - 0.004))
            if front and (p - eye_c).length < 0.042 + j:
                return "fur_points"
        if front and z < 0.25:
            return "fur_white"  # cheeks and chin
        if z > 0.24 + j or n.y > 0.1:
            return "fur_head"
        return "fur_white"
    saddle = ((x / 0.118) ** 2 + ((y - 0.06) / 0.15) ** 2) < 1.0 and z > 0.13 + j * 2
    hip = y > 0.07 and abs(x) > 0.05 and z > 0.08 + j and n.y > -0.3
    if saddle or hip:
        # small white spot on the flank, like the character sheet
        if ((x - 0.085) / 0.03) ** 2 + ((y - 0.03) / 0.04) ** 2 + ((z - 0.14) / 0.03) ** 2 < 1:
            return "fur_white"
        return "fur_saddle"
    return "fur_white"


def ear(name, sx):
    bpy.ops.mesh.primitive_cone_add(vertices=24, radius1=0.05, radius2=0.005, depth=0.085)
    e = bpy.context.object
    e.scale = (1, 0.42, 1)
    bpy.ops.object.transform_apply(scale=True)
    m = e.modifiers.new("sub", "SUBSURF")
    m.levels = 1
    apply_all(e)
    smooth(e)
    assign(e, material("tutu_ear_points", "fur_points", rough=0.75))
    bpy.ops.mesh.primitive_cone_add(vertices=24, radius1=0.034, radius2=0.002, depth=0.06, location=(0, -0.013, -0.008))
    inner = bpy.context.object
    inner.scale = (1, 0.25, 1)
    bpy.ops.object.transform_apply(scale=True)
    smooth(inner)
    assign(inner, material("tutu_ear_inner", "ear_inner", rough=0.7))
    e = join([e, inner], name)
    e.location = (0.07 * sx, -0.155, 0.345)
    e.rotation_euler = (math.radians(-10), math.radians(24 * sx), math.radians(-14 * sx))
    return e


def eye(sx):
    side = "L" if sx > 0 else "R"
    yaw = math.radians(28 * sx)
    fwd = Vector((math.sin(yaw), -math.cos(yaw), 0))
    c = Vector((EYE_X * sx, surface_y(EYE_X, EYE_Z) + 0.001, EYE_Z))
    # almond: wide ellipse, slight upward tilt toward the outer corner
    iris = ellipsoid(f"tutu_eye_{side}", c, (0.03, 0.01, 0.022), rot=(0, math.radians(-12 * sx), yaw))
    assign(iris, material("tutu_iris", "eyes", rough=0.12))
    pupil = ellipsoid(f"tutu_pupil_{side}", c + fwd * 0.0075, (0.0075, 0.004, 0.0175), rot=(0, 0, yaw))
    assign(pupil, material("tutu_pupil", "#0E0B0C", rough=0.1))
    hl = sphere(f"tutu_eye_highlight_{side}", 0.0045, loc=c + fwd * 0.009 + Vector((0.009 * sx, 0, 0.009)))
    assign(hl, material("tutu_highlight", "#FFFFFF", emit="#FFFFFF", emit_strength=1.5))
    return [iris, pupil, hl]


def whiskers(sx):
    objs = []
    for i, (dz, droop) in enumerate(((0.008, 0.012), (0.0, -0.002), (-0.008, -0.018))):
        root = (0.034 * sx, -0.245, 0.232 + dz)
        pts = [root, (0.08 * sx, -0.238, 0.234 + dz + droop * 0.4), (0.13 * sx, -0.222, 0.232 + dz + droop)]
        objs.append(tube(f"w{sx}{i}", pts, 0.0007, bevel_res=1, resolution=6))
    w = join(objs, f"tutu_whiskers_{'L' if sx > 0 else 'R'}")
    assign(w, material("tutu_whisker", "#F3EEE8", rough=0.5))
    return w


def nose():
    bpy.ops.mesh.primitive_cone_add(vertices=3, radius1=0.012, depth=0.006, location=(0, -0.26, 0.243),
                                    rotation=(math.radians(-80), 0, math.radians(180)))
    n = bpy.context.object
    n.name = "tutu_nose"
    m = n.modifiers.new("bevel", "BEVEL")
    m.width = 0.003
    m.segments = 3
    apply_all(n)
    smooth(n)
    return assign(n, material("tutu_nose_mat", "#1A0F0D", rough=0.35))


def build():
    reset_scene()
    body = body_mesh()
    paint_vertex_colors(body, fur_color)
    decimate(body, 0.3)
    assign(body, vcol_material("tutu_fur", rough=0.75))
    parts = [ear("tutu_ear_L", 1), ear("tutu_ear_R", -1), nose(), whiskers(1), whiskers(-1)] + eye(1) + eye(-1)
    parts.append(sweat_drop())
    rig = build_rig(body, parts)
    find_sit(rig, body)
    make_actions(rig)
    root = bpy.data.objects.new("tutu", None)
    bpy.context.scene.collection.objects.link(root)
    parent_keep(rig, root)
    root.scale = (SCALE,) * 3
    return root, rig, [root, rig, body] + parts


# ---------------------------------------------------------------- rig

def skeleton():
    """bone -> (head, tail, parent, deform). Rest pose = the standing model; the cat faces -Y, her left is +X."""
    b = {
        "pelvis": ((0, 0.14, 0.13), (0, 0.03, 0.14), None, True),
        "chest": ((0, 0.03, 0.14), (0, -0.085, 0.16), "pelvis", True),
        "neck": ((0, -0.085, 0.16), (0, -0.12, 0.21), "chest", True),
        # head bone points along the gaze (toward the nose) so aiming it = looking somewhere
        "head": ((0, -0.12, 0.24), (0, -0.26, 0.245), "neck", True),
    }
    for s, n in ((1, "L"), (-1, "R")):
        x, xb = 0.052 * s, 0.06 * s
        b[f"ear.{n}"] = ((0.066 * s, -0.155, 0.33), (0.082 * s, -0.162, 0.41), "head", False)
        b[f"front_upper.{n}"] = ((x, -0.09, 0.14), (x, -0.095, 0.075), "chest", True)
        b[f"front_lower.{n}"] = ((x, -0.095, 0.075), (x, -0.099, 0.03), f"front_upper.{n}", True)
        b[f"front_paw.{n}"] = ((x, -0.099, 0.03), (x, -0.14, 0.018), f"front_lower.{n}", True)
        b[f"thigh.{n}"] = ((xb, 0.12, 0.13), (xb, 0.13, 0.07), "pelvis", True)
        b[f"shin.{n}"] = ((xb, 0.13, 0.07), (xb, 0.126, 0.03), f"thigh.{n}", True)
        b[f"hind_paw.{n}"] = ((xb, 0.126, 0.03), (xb, 0.085, 0.018), f"shin.{n}", True)
    pts = [TAIL_PTS[i] for i in (0, 1, 2, 3, 4, 6)]
    for i in range(5):
        b[f"tail_{i + 1}"] = (pts[i], pts[i + 1], "pelvis" if i == 0 else f"tail_{i}", True)
    return b


def build_rig(body, parts):
    data = bpy.data.armatures.new("tutu_rig")
    rig = bpy.data.objects.new("tutu_rig", data)
    bpy.context.scene.collection.objects.link(rig)
    active(rig)
    bpy.ops.object.mode_set(mode="EDIT")
    sk = skeleton()
    for name, (h, t, _, deform) in sk.items():
        eb = data.edit_bones.new(name)
        eb.head, eb.tail = h, t
        eb.use_deform = deform
    for name, (_, _, parent, _) in sk.items():
        if parent:
            data.edit_bones[name].parent = data.edit_bones[parent]
    bpy.ops.object.mode_set(mode="OBJECT")

    # automatic (bone heat) weights on the single fur mesh
    bpy.ops.object.select_all(action="DESELECT")
    body.select_set(True)
    rig.select_set(True)
    bpy.context.view_layer.objects.active = rig
    bpy.ops.object.parent_set(type="ARMATURE_AUTO")
    assert len(body.vertex_groups) > 10, "bone heat weighting failed"

    # rigid accessories ride on bones
    for o in parts:
        bone = f"ear.{o.name[-1]}" if o.name.startswith("tutu_ear_") else "head"
        bpy.context.view_layer.update()
        mw = o.matrix_world.copy()
        o.parent = rig
        o.parent_type = "BONE"
        o.parent_bone = bone
        bpy.context.view_layer.update()
        o.matrix_world = mw
    return rig


# ---------------------------------------------------------------- poses
# Directions are in armature space. Bones are aimed parent-first (same idea as build_gio.aim_pose).

def aim(rig, directions):
    bpy.context.view_layer.update()
    order = []

    def walk(b):
        order.append(b.name)
        for c in b.children:
            walk(c)

    for b in rig.data.bones:
        if b.parent is None:
            walk(b)
    for name in order:
        if name not in directions:
            continue
        pb = rig.pose.bones[name]
        head = pb.head.copy()
        q = (pb.tail - pb.head).rotation_difference(Vector(directions[name]).normalized())
        pb.matrix = Matrix.Translation(head) @ q.to_matrix().to_4x4() @ Matrix.Translation(-head) @ pb.matrix
        bpy.context.view_layer.update()


def reset_pose(rig):
    for pb in rig.pose.bones:
        pb.rotation_mode = "QUATERNION"
        pb.rotation_quaternion = (1, 0, 0, 0)
        pb.location = (0, 0, 0)
        pb.scale = (1, 1, 1)
    bpy.context.view_layer.update()


def tilt_dir(base, deg):
    """Rotate a rest direction around X so the front end goes up by `deg`."""
    return tuple(Matrix.Rotation(math.radians(-deg), 3, "X") @ Vector(base))


def sit_dirs(tilt):
    d = {
        "pelvis": tilt_dir((0, -0.11, 0.01), tilt),
        "chest": tilt_dir((0, -0.115, 0.02), tilt + 12),
        "neck": (0, -0.35, 1),
        "head": (0, -1, 0.04),
        # tail lies on the floor and wraps around the front paws
        "tail_1": (0.3, 0.9, -0.8), "tail_2": (1, 0.1, -0.2), "tail_3": (0.7, -0.8, 0),
        "tail_4": (0.1, -1, 0.05), "tail_5": (-0.4, -1, 0.1),
    }
    for n in ("L", "R"):
        d[f"front_upper.{n}"] = (0, -0.12, -1)
        d[f"front_lower.{n}"] = (0, -0.05, -1)
        d[f"front_paw.{n}"] = (0, -1, -0.25)
        d[f"thigh.{n}"] = (0, -1, -0.3)
        d[f"shin.{n}"] = (0, 0.75, -0.65)
        d[f"hind_paw.{n}"] = (0, -1, -0.1)
    return d


SIT_TILT = 38  # degrees the body rocks back onto the haunches


def pose_with_drop(rig, dirs, drop, stretch=1.0):
    reset_pose(rig)
    aim(rig, dirs)
    # toon legs are short: lengthen the front legs so the paws still reach the floor when sitting up
    for n in ("L", "R"):
        rig.pose.bones[f"front_upper.{n}"].scale = (1, stretch, 1)
    bpy.context.view_layer.update()
    pb = rig.pose.bones["pelvis"]
    pb.matrix = Matrix.Translation((0, 0, -drop)) @ pb.matrix
    bpy.context.view_layer.update()


def _lowest(body, idx):
    dg = bpy.context.evaluated_depsgraph_get()
    ev = body.evaluated_get(dg)
    me = ev.to_mesh()
    z = min(me.vertices[i].co.z for i in idx)
    ev.to_mesh_clear()
    return z


def find_sit(rig, body):
    """Drop the body so the butt rests on the floor, then stretch the front legs until the paws touch too."""
    rest = [v.co.copy() for v in body.data.vertices]
    rear = [i for i, c in enumerate(rest) if 0.06 < c.y < 0.2 and c.z < 0.16]
    front = [i for i, c in enumerate(rest) if c.y < -0.07 and c.z < 0.05]
    dirs = sit_dirs(SIT_TILT)
    pose_with_drop(rig, dirs, 0.0)
    drop = _lowest(body, rear)
    stretch = 1.0
    while stretch < 2.0:
        pose_with_drop(rig, dirs, drop, stretch)
        if _lowest(body, front) <= 0.002:
            break
        stretch += 0.04
    print(f"tutu sit: tilt={SIT_TILT} drop={drop:.3f} stretch={stretch:.2f}")
    rig["sit_tilt"], rig["sit_drop"], rig["sit_stretch"] = float(SIT_TILT), float(drop), float(stretch)
    reset_pose(rig)


# Tutu sits right behind the mug, turned to face it (desk spot (0.42, 0.44), yaw 20°): in her own model space
# the mug is straight ahead, ~0.19 away, and Gio is to her right (-X) and above.
TO_CUP = Vector((0.0, -1.0, 0.0))
LOOK_GIO = {"neck": (-0.25, -0.3, 1), "head": (-0.8, -0.42, 0.3)}
LOOK_CUP = {"neck": (0, -0.45, 1), "head": (0, -0.85, -0.55)}
# the swat, frame by frame: aim → raise → wind up → lunge + hit → push through → watch it go over the edge
SLAP = {
    "slap_ready": {**LOOK_CUP, "front_upper.L": (0.15, -0.3, 0.95), "front_lower.L": (0.1, -0.6, 0.8),
                   "front_paw.L": (0.1, -0.95, 0.3)},
    "slap_wind": {**LOOK_CUP, "front_upper.L": (0.2, 0.15, 1), "front_lower.L": (0.15, -0.25, 0.95),
                  "front_paw.L": (0.1, -0.8, 0.6)},
    "slap_hit": {**LOOK_CUP, "front_upper.L": (0.05, -0.85, -0.3), "front_lower.L": (0.02, -0.95, -0.28),
                 "front_paw.L": (0, -1, -0.25)},
    "slap_through": {"neck": (0, -0.6, 0.8), "head": (0, -0.8, -0.6), "front_upper.L": (0, -0.95, -0.45),
                     "front_lower.L": (-0.05, -0.9, -0.5), "front_paw.L": (-0.1, -0.8, -0.6)},
    "look_edge": {"neck": (0, -0.6, 0.8), "head": (0, -0.75, -0.7)},
}
# body motion that sells the swat (pelvis offset in model space, chest pitch)
SLAP_BODY = {"slap_ready": ((0, -0.01, 0), 6), "slap_wind": ((0, 0.025, 0.005), 14),
             "slap_hit": ((0, -0.055, 0), -14), "slap_through": ((0, -0.07, -0.005), -20), "look_edge": ((0, -0.02, 0), -6)}
SLAP_REACH = {"slap_hit": 1.3, "slap_through": 1.35}  # the swatting leg stretches to reach the mug


def _legs(d, front=None, hind=None):
    for n in ("L", "R"):
        if front:
            d[f"front_upper.{n}"], d[f"front_lower.{n}"], d[f"front_paw.{n}"] = front
        if hind:
            d[f"thigh.{n}"], d[f"shin.{n}"], d[f"hind_paw.{n}"] = hind
    return d


def pose_spec(rig, name, t):
    """Bone directions + extras for a named pose. Returns dict(dirs, drop, stretch, lift, ears, ears_out, sweat)."""
    tilt = rig["sit_tilt"]
    d = sit_dirs(tilt)
    sway = math.sin(t * math.tau)
    d["tail_4"] = (0.1 + 0.3 * sway, -1, 0.05 + 0.25 * max(sway, 0))
    d["tail_5"] = (-0.4 + 0.5 * sway, -1, 0.1 + 0.35 * max(sway, 0))
    spec = dict(dirs=d, drop=rig["sit_drop"], stretch=rig["sit_stretch"], lift=Vector(), ears=0.0, ears_out=0.0,
                sweat=0.0, reach=None)
    flick = 0.25 * max(math.sin(t * math.tau * 2), 0)

    if name in ("look_gio", "look_cup"):
        d.update(LOOK_GIO if name == "look_gio" else LOOK_CUP)
    elif name in SLAP:
        d.update(SLAP[name])
        lift, pitch = SLAP_BODY[name]
        spec["lift"] = Vector(lift)
        d["chest"] = tilt_dir((0, -0.115, 0.02), tilt + 12 + pitch)
        spec["reach"] = SLAP_REACH.get(name, 1.1)
        spec["ears_out"] = 0.2 if name in ("slap_ready", "slap_wind") else 0.0
        d["tail_5"] = (0.6 if name == "slap_wind" else -0.4, -1, 0.3)
    elif name == "sit_bored":
        spec["ears"] = flick
    elif name == "lean_cup":
        # scene 0: leaning over the mug so her eyes reflect in the coffee
        u = TO_CUP
        # peeking over the rim: stays seated, only chest, neck and head reach toward the mug
        d["chest"] = (u.x * 0.6, u.y * 0.6, 0.6)
        d["neck"] = (u.x * 0.9, u.y * 0.9, -0.25)
        d["head"] = (u.x * 0.4, u.y * 0.4, -1.0)
        spec["stretch"] = rig["sit_stretch"] * 0.8
        spec["ears"] = -0.15
    elif name == "crouch":
        spec["drop"] += 0.02
        d["chest"] = tilt_dir((0, -0.115, 0.02), tilt - 30)
        d.update(neck=(0, -1, 0.3), head=(0, -1, -0.15))
        _legs(d, front=((0, -0.35, -1), (0, -0.25, -1), (0, -1, -0.2)),
              hind=((0, -1, -0.15), (0, 0.85, -0.45), (0, -1, -0.05)))
        d.update(tail_1=(0, 1, -0.2), tail_2=(0, 1, 0.1), tail_3=(0, 1, 0.3), tail_4=(0, 1, 0.3), tail_5=(0, 1, 0.2))
    elif name == "leap":
        # stretched out in the air: front paws reaching forward-down, hind legs trailing
        spec["drop"] = 0.0
        d["pelvis"] = tilt_dir((0, -0.11, 0.01), -12)
        d["chest"] = tilt_dir((0, -0.115, 0.02), -22)
        d.update(neck=(0, -1, 0.15), head=(0, -1, -0.35))
        spec["stretch"] = 1.15
        _legs(d, front=((0, -0.75, -0.65), (0, -0.85, -0.55), (0, -1, -0.3)),
              hind=((0, 0.75, -0.6), (0, 0.95, -0.25), (0, 1, 0.1)))
        d.update(tail_1=(0, 1, 0.25), tail_2=(0, 1, 0.3), tail_3=(0, 1, 0.25), tail_4=(0, 1, 0.2), tail_5=(0, 1, 0.3))
    elif name == "land":
        spec["drop"] += 0.01
        d["chest"] = tilt_dir((0, -0.115, 0.02), tilt - 40)
        d.update(neck=(0, -1, 0.1), head=(0, -1, 0.05))
        spec["stretch"] = 1.25
        _legs(d, front=((0, -0.15, -1), (0, -0.05, -1), (0, -1, -0.25)))
    elif name == "innocent":
        # "não fui eu": head turned away, ears out to the side, a sweat drop, the tail tip twitching
        d.update(neck=(-0.25, -0.35, 1), head=(-0.8, -0.35, 0.4))
        d["tail_5"] = (-0.6 + 0.6 * math.sin(t * math.tau * 2), -0.8, 0.3)
        spec["ears_out"] = 0.55 + 0.1 * math.sin(t * math.tau)
        spec["sweat"] = 1.0
    elif name == "picked_up":
        # lifted under the arms: body upright, hind legs and tail hanging, front paws relaxed
        d["pelvis"] = tilt_dir((0, -0.11, 0.01), 72)
        d["chest"] = tilt_dir((0, -0.115, 0.02), 80)
        d.update(neck=(0, -0.3, 1), head=(0, -1, 0.05))
        spec["stretch"] = 1.0
        swing = 0.12 * math.sin(t * math.tau)
        _legs(d, front=((0, -0.75, -0.6), (0, -0.55, -0.8), (0, -0.9, -0.4)),
              hind=((0, -0.15 + swing, -1), (0, 0.15, -1), (0, -0.5, -0.9)))
        d.update(tail_1=(0, 0.4, -1), tail_2=(0.1, 0.2, -1), tail_3=(0.15, 0, -1),
                 tail_4=(0.1 + swing, -0.1, -1), tail_5=(swing, -0.3, -1))
        spec["drop"] = rig["sit_drop"] * 0.6
        spec["sweat"] = max(0.0, 1.0 - t * 3)
    elif name == "lap":
        # on Gio's lap, held against her chest like the eu_e_tutu photo; slow breathing, purring
        breath = 0.04 * math.sin(t * math.tau)
        d["pelvis"] = tilt_dir((0, -0.11, 0.01), 55)
        d["chest"] = tilt_dir((0, -0.115, 0.02), 68 + 6 * breath)
        d.update(neck=(0, -0.25, 1), head=(0.12, -1, 0.12 + breath))
        spec["stretch"] = 1.0
        _legs(d, front=((0, -0.75, -0.55), (0, -0.7, -0.6), (0, -1, -0.15)))
        spec["ears"] = flick * 0.5
    return spec


def pose(rig, name, t=0.0):
    """Named poses: sit, sit_bored, look_gio, look_cup, slap_raise, slap_hit, lean_cup, crouch, leap,
    land, innocent, picked_up, lap. `t` (0..1) drives the ambient loops (tail, ears, breathing)."""
    spec = pose_spec(rig, name, t)
    pose_with_drop(rig, spec["dirs"], spec["drop"], spec["stretch"])
    if spec["lift"].length:
        pb = rig.pose.bones["pelvis"]
        pb.matrix = Matrix.Translation(spec["lift"]) @ pb.matrix
    if spec["reach"]:
        # the swatting leg is off the floor: its own length, stretched out on the hit to reach the mug
        rig.pose.bones["front_upper.L"].scale = (1, spec["reach"], 1)
    for n, sgn in (("L", 1), ("R", -1)):
        pb = rig.pose.bones[f"ear.{n}"]
        # `ears` tilts both ears the same way (flick); `ears_out` splays them sideways (guilty)
        pb.rotation_quaternion = Quaternion((0, 1, 0), spec["ears"] + sgn * spec["ears_out"])
    sweat = bpy.data.objects.get("tutu_sweat")
    if sweat:
        k = spec["sweat"]
        sweat.scale = (k, k, k)
    bpy.context.view_layer.update()


def sweat_drop():
    """Little blue sweat drop by her forehead (character sheet, "não fui eu")."""
    drop = sphere("tutu_sweat", 0.012, loc=(0.105, -0.17, 0.335), scale=(1, 0.8, 1.35))
    assign(drop, material("tutu_sweat_mat", "eyes", rough=0.1))
    return drop


# ---------------------------------------------------------------- actions

def key_all(rig, frame):
    for pb in rig.pose.bones:
        pb.keyframe_insert("rotation_quaternion", frame=frame)
        pb.keyframe_insert("location", frame=frame)
        pb.keyframe_insert("scale", frame=frame)
    sweat = bpy.data.objects.get("tutu_sweat")
    if sweat:
        sweat.keyframe_insert("scale", frame=frame)


def make_action(rig, name, keys):
    """keys: list of (frame, pose_name, t). Each action (rig + sweat drop) sits on its own muted NLA
    track with the same name, which the glTF exporter merges into one named animation."""
    owners = [rig] + [o for o in (bpy.data.objects.get("tutu_sweat"),) if o]
    acts = {}
    for o in owners:
        ad = o.animation_data or o.animation_data_create()
        acts[o] = bpy.data.actions.new(name if o is rig else f"{name}_{o.name}")
        ad.action = acts[o]
    for frame, pname, t in keys:
        pose(rig, pname, t)
        key_all(rig, frame)
    for o, act in acts.items():
        ad = o.animation_data
        ad.action = None
        track = ad.nla_tracks.new()
        track.name = name
        strip = track.strips.new(name, int(keys[0][0]), act)
        strip.name = name
        track.mute = True
        act.use_fake_user = True


def make_actions(rig):
    make_action(rig, "tutu_sit_bored_loop", [(f, "sit_bored", (f - 1) / 48) for f in range(1, 50, 6)])
    make_action(rig, "tutu_look_gio", [(1, "sit", 0), (14, "look_gio", 0), (24, "look_gio", 0)])
    make_action(rig, "tutu_look_cup", [(1, "look_gio", 0), (14, "look_cup", 0), (24, "look_cup", 0)])
    # contact with the mug at frame 13 of 24 (t = 0.52): the app starts pushing the mug at that moment
    make_action(rig, "tutu_slap", [(1, "look_cup", 0), (6, "slap_ready", 0), (10, "slap_wind", 0), (13, "slap_hit", 0),
                                   (16, "slap_through", 0), (24, "look_edge", 0)])
    # scene 0 → 1: from sitting to leaning over the mug (the app plays it backwards as she sits up)
    make_action(rig, "tutu_lean_cup", [(1, "sit", 0), (14, "lean_cup", 0), (24, "lean_cup", 0)])
    # scene 5: crouch, leap off the desk, land, sit. The app moves her along the arc (frames 12–26).
    make_action(rig, "tutu_jump_down", [(1, "look_edge", 0), (8, "crouch", 0), (12, "leap", 0), (20, "leap", 0),
                                         (26, "land", 0), (36, "sit", 0)])
    make_action(rig, "tutu_sit_floor_innocent", [(f, "innocent", (f - 1) / 48) for f in range(1, 50, 4)])
    make_action(rig, "tutu_picked_up", [(1, "innocent", 0)] + [(f, "picked_up", (f - 8) / 32) for f in range(8, 41, 4)])
    make_action(rig, "tutu_lap_loop", [(f, "lap", (f - 1) / 48) for f in range(1, 50, 4)])
    reset_pose(rig)
    sweat = bpy.data.objects.get("tutu_sweat")
    if sweat:
        sweat.scale = (0, 0, 0)


if __name__ == "__main__":
    root, rig, objs = build()
    save_blend("tutu.blend")
    export_glb(os.path.join(MODELS_DIR, "tutu.glb"), objs, animations=True)

    if "--no-previews" in sys.argv:
        sys.exit(0)
    sc = bpy.context.scene
    studio(sc, target=(0, 0, 0.16), dist=1.0)
    render_views(sc, "tutu", target=(0, 0, 0.16), dist=0.85, height=0.1, lens=60,
                 views=("front", "three_quarter", "side", "back"), res=(900, 900))
    render_views(sc, "tutu", target=(0, -0.12, 0.205), dist=0.45, height=0.02, lens=70, views=(), res=(900, 900),
                 extra=[("face", -90, 0.02)])
    for name in ("sit", "look_gio", "look_cup", "slap_wind", "slap_hit", "slap_through", "lean_cup", "crouch", "leap", "land", "innocent",
                 "picked_up", "lap"):
        pose(rig, name, 0.15)
        render_views(sc, f"tutu_pose_{name}", target=(0, -0.04, 0.17), dist=0.9, height=0.1, lens=60, views=(),
                     res=(900, 900), extra=[("3q", -55, 0.1), ("side", -5, 0.06)])
