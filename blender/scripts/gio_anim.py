"""Giovanna's animations (spec §5): gio_typing_loop, gio_mouse_loop, gio_broom_enter, gio_crouch_pick_cat,
gio_sit_with_cat, gio_idle_lap_loop.

Every action is a function frame -> pose spec, so the same code bakes the keyframes, poses previews and
can be re-run at any time. Poses are built from a "body frame" (root bone offset + yaw) with
two-bone IK for arms and legs, aimed bones for spine/head/hands/fingers.

All actions assume the rig object sits where the desk scene puts it: RIG_LOC with RIG_YAW (on the chair,
facing the desk). Positions in the desk scene ("world") are converted with world_to_rig().

Extra animated nodes, merged into the same glTF animations:
  gio_broom       the broom (hidden with scale 0 when not in use)
  gio_cat_anchor  where Tutu's root should be; the app parents Tutu to it while Gio holds her
"""
import math

import bmesh
import bpy
from mathutils import Matrix, Vector

from common import assign, cylinder, join, material, rounded_box, sphere

RIG_LOC = Vector((-0.22, -0.22, 0.065))  # on the chair seat, in desk-scene coordinates
RIG_YAW = math.radians(180)              # rest pose faces -Y; the desk is at +Y
FPS = 24
STAND_Z = -RIG_LOC.z                     # root z that puts the feet on the floor
HAND_LEN = 0.065
FINGERS = ("index", "middle", "ring", "pinky")


def world_to_rig(p):
    return Matrix.Rotation(-RIG_YAW, 3, "Z") @ (Vector(p) - RIG_LOC)


# ---------------------------------------------------------------- pose core

def reset(rig):
    for pb in rig.pose.bones:
        pb.rotation_mode = "QUATERNION"
        pb.rotation_quaternion = (1, 0, 0, 0)
        pb.location = (0, 0, 0)
        pb.scale = (1, 1, 1)
    bpy.context.view_layer.update()


def _rotate_bone(pb, rot3):
    head = pb.head.copy()
    pb.matrix = Matrix.Translation(head) @ rot3.to_4x4() @ Matrix.Translation(-head) @ pb.matrix
    bpy.context.view_layer.update()


def aim(rig, name, direction):
    pb = rig.pose.bones[name]
    q = (pb.tail - pb.head).rotation_difference(Vector(direction).normalized())
    _rotate_bone(pb, q.to_matrix())


def roll_to(rig, name, ref_rest, want):
    """Twist a bone around its own axis so a rest-space reference vector lines up with `want`."""
    pb = rig.pose.bones[name]
    axis = (pb.tail - pb.head).normalized()
    cur = (pb.matrix.to_3x3() @ pb.bone.matrix_local.to_3x3().inverted()) @ Vector(ref_rest)
    cur = (cur - axis * cur.dot(axis)).normalized()
    w = Vector(want)
    w = (w - axis * w.dot(axis)).normalized()
    ang = math.atan2(axis.dot(cur.cross(w)), cur.dot(w))
    _rotate_bone(pb, Matrix.Rotation(ang, 3, axis))


def ik(rig, upper, lower, target, pole):
    """Two-bone IK: place the tail of `lower` on `target`, bending toward `pole` (a direction)."""
    pu, pl = rig.pose.bones[upper], rig.pose.bones[lower]
    a, b = pu.bone.length, pl.bone.length
    s = pu.head.copy()
    t = Vector(target)
    d = min((t - s).length, (a + b) * 0.999)
    fwd = (t - s).normalized()
    cos_a = max(-1.0, min(1.0, (a * a + d * d - b * b) / (2 * a * d)))
    pv = Vector(pole)
    side = (pv - fwd * pv.dot(fwd)).normalized()
    elbow = s + fwd * a * cos_a + side * a * math.sqrt(1 - cos_a * cos_a)
    aim(rig, upper, elbow - s)
    aim(rig, lower, t - rig.pose.bones[lower].head)


class Body:
    """Body frame: root offset + yaw, both in rig (armature) space."""

    def __init__(self, root, yaw_deg):
        self.root = Vector(root)
        self.rot = Matrix.Rotation(math.radians(yaw_deg), 3, "Z")

    def p(self, v):
        return self.root + self.rot @ Vector(v)

    def d(self, v):
        return self.rot @ Vector(v)


def palm_rest(n):
    """Palm normal of the rest hand (A-pose palms face the thighs)."""
    s = 1 if n == "L" else -1
    a = math.radians(38)
    return (-math.cos(a) * s, 0, -math.sin(a))


def apply(rig, spec):
    """spec keys (all in body frame): root, yaw, spine, neck, head, arms{L,R}, legs{L,R}."""
    reset(rig)
    body = Body(spec.get("root", (0, 0, 0)), spec.get("yaw", 0))
    pb = rig.pose.bones["root"]
    pb.matrix = Matrix.Translation(body.root) @ body.rot.to_4x4() @ pb.bone.matrix_local
    bpy.context.view_layer.update()
    for bone in ("spine", "neck", "head"):
        if bone in spec:
            aim(rig, bone, body.d(spec[bone]))
    for n, arm in spec.get("arms", {}).items():
        ik(rig, f"upper_arm.{n}", f"forearm.{n}", body.p(arm["wrist"]), body.d(arm["pole"]))
        aim(rig, f"hand.{n}", body.d(arm["hand"]))
        roll_to(rig, f"hand.{n}", palm_rest(n), body.d(arm["palm"]))
        fingers = arm.get("fingers", {})
        for f in FINGERS:
            if f in fingers:
                aim(rig, f"{f}.{n}", body.d(fingers[f]))
        if "thumb" in arm:
            aim(rig, f"thumb.{n}", body.d(arm["thumb"]))
    for n, leg in spec.get("legs", {}).items():
        ik(rig, f"thigh.{n}", f"shin.{n}", body.p(leg["ankle"]), body.d(leg.get("pole", (0, -1, 0))))
        aim(rig, f"foot.{n}", body.d(leg.get("foot", (0, -1, -0.45))))
    return body


# ---------------------------------------------------------------- reusable pieces

def lerp(a, b, t):
    return tuple(x + (y - x) * t for x, y in zip(a, b))


def smooth(t):
    t = max(0.0, min(1.0, t))
    return t * t * (3 - 2 * t)


def seated_legs():
    # chibi on a tall office chair: thighs forward, shins hanging, feet off the floor
    return {n: {"ankle": (0.09 * s, -0.27, 0.34), "pole": (0, -1, 0.2), "foot": (0, -1, -0.3)}
            for n, s in (("L", 1), ("R", -1))}


def standing_legs():
    return {n: {"ankle": (0.09 * s, 0.0, 0.085), "pole": (0, -1, 0)} for n, s in (("L", 1), ("R", -1))}


def walk_legs(phase, stride=0.25, lift=0.07):
    """phase in cycles (1 = two steps). Feet in body frame; body moves -Y."""
    legs = {}
    for n, s, off in (("L", 1, 0.0), ("R", -1, 0.5)):
        c = (phase + off) % 1.0
        if c < 0.5:      # stance: foot slides back as the body moves forward
            k = c / 0.5
            y, z, tilt = -stride / 2 + stride * k, 0.085, -0.45
        else:            # swing: lift and bring forward
            k = (c - 0.5) / 0.5
            y = stride / 2 - stride * smooth(k)
            z = 0.085 + lift * math.sin(math.pi * k)
            tilt = -0.45 + 0.35 * math.sin(math.pi * k)
        legs[n] = {"ankle": (0.09 * s, y, z), "pole": (0, -1, 0), "foot": (0, -1, tilt)}
    return legs


def walk_bob(phase):
    return -0.012 * abs(math.sin(phase * math.tau))


def hug_arms(cat):
    """Arms wrapped around Tutu, whose root (paws) is at `cat` (body frame), like the eu_e_tutu photo."""
    cx, cy, cz = cat[0], cat[1], cat[2] + 0.12  # around her belly, not her paws
    return {
        "L": {"wrist": (cx + 0.07, cy - 0.04, cz - 0.04), "pole": (0.6, 0.2, -1), "hand": (-0.7, -0.6, -0.1),
              "palm": (-1, 0.2, 0), "fingers": {f: (-1, 0, -0.4) for f in FINGERS}, "thumb": (-0.5, -1, 0.3)},
        "R": {"wrist": (cx - 0.06, cy - 0.06, cz + 0.07), "pole": (-0.7, 0.3, -1), "hand": (0.8, -0.5, 0.1),
              "palm": (1, 0.2, 0), "fingers": {f: (1, 0, -0.4) for f in FINGERS}, "thumb": (0.5, -1, 0.3)},
    }


# ---------------------------------------------------------------- desk targets (desk-scene coords)

KEYBOARD = Vector((-0.22, 0.2, 0.775))
MOUSE = Vector((0.12, 0.21, 0.765))
CAT_FLOOR = Vector((0.6, -0.5, 0.0))     # Tutu sitting among the shards ("não fui eu")
BROOM_STOP = Vector((0.95, -0.5, 0.0))   # where Gio stops to sweep, facing -X (toward the shards)
BROOM_START = Vector((2.0, -0.5, 0.0))   # off screen to the right
CAT_HOLD = (0.0, -0.2, 0.68)  # Tutu root while hugged standing (body frame)
CAT_LAP = (0.0, -0.19, 0.67)   # Tutu root on her lap when seated


def typing_arm(n, t, press_phase=0.0):
    s = 1 if n == "L" else -1
    w = world_to_rig(KEYBOARD) + Vector((0.075 * s, 0.075, 0.03))
    w.z += 0.004 * math.sin((t + press_phase) * math.tau * 2)
    fingers = {}
    for i, f in enumerate(FINGERS):
        down = math.sin((t * 4 + i * 0.27 + press_phase) * math.tau) > 0.3
        fingers[f] = (0, -0.45, -1) if down else (0, -0.85, -0.55)
    return {"wrist": tuple(w), "pole": (0.7 * s, 0.4, -1), "hand": (-0.05 * s, -1, -0.28), "palm": (0, 0, -1),
            "fingers": fingers, "thumb": (-0.5 * s, -0.8, -0.5)}


def seated(extra=None, lean=0.18):
    spec = {"root": (0, 0, 0), "yaw": 0, "spine": (0, -lean, 1), "neck": (0, -0.1, 1), "head": (0, -0.12, 1),
            "legs": seated_legs()}
    spec.update(extra or {})
    return spec


def mouse_arm(t):
    w = world_to_rig(MOUSE) + Vector((0.0, 0.07, 0.03))
    w += Vector((0.012 * math.cos(t * math.tau), 0.009 * math.sin(t * math.tau), 0))
    click = 0.45 < (t % 0.5) / 0.5 < 0.6
    fingers = {f: (0, -0.8, -0.6) for f in FINGERS}
    fingers["index"] = (0, -0.6, -0.8) if click else (0, -0.9, -0.45)
    return {"wrist": tuple(w), "pole": (-0.8, 0.3, -1), "hand": (0, -1, -0.3), "palm": (0, 0, -1),
            "fingers": fingers, "thumb": (0.6, -0.7, -0.4)}


# ---------------------------------------------------------------- actions (frame -> spec, broom, anchor)

def act_typing(f):
    t = (f - 1) / 24
    return seated({"arms": {"L": typing_arm("L", t), "R": typing_arm("R", t, 0.5)},
                   "head": (0.03 * math.sin(t * math.tau), -0.12, 1)}), None, None


def act_mouse(f):
    t = (f - 1) / 48
    return seated({"arms": {"L": typing_arm("L", t * 0.25), "R": mouse_arm(t)},
                   "head": (-0.04, -0.12, 1)}), None, None


def broom_frame(body, t, sweep):
    """Broom bottom on the floor in front of her, handle up to her hands. Returns (bottom, up) in rig space."""
    # bristles sweep in front and a little to her left, clear of Tutu
    bottom = body.p((0.2 + 0.1 * math.sin(sweep * math.tau), -0.36 - 0.03 * math.cos(sweep * math.tau), 0.0))
    top = body.p((0.02, -0.06, 0.95))
    return bottom, (top - bottom).normalized()


def broom_arms(bottom, up, body):
    def along(dist):
        return bottom + up * dist

    inv = body.rot.inverted()
    loc = lambda p: tuple(inv @ (p - body.root))  # noqa: E731
    r = along(0.5) - up * HAND_LEN * 0.5
    lw = along(0.82) - up * HAND_LEN * 0.5
    grip = {f: (0.3, -0.2, -1) for f in FINGERS}
    return {
        "R": {"wrist": loc(r), "pole": (-0.8, 0.2, -0.6), "hand": (0.6, -0.6, -0.5),
              "palm": (0.8, 0, 0), "fingers": grip, "thumb": (0.6, -0.8, 0)},
        "L": {"wrist": loc(lw), "pole": (0.8, 0.4, -0.6), "hand": (-0.4, -0.7, -0.4), "palm": (-0.6, 0.2, -0.6),
              "fingers": {f: (-0.6, -0.2, -1) for f in FINGERS}, "thumb": (-0.6, -0.8, 0)},
    }


def act_broom_enter(f):
    walk_frames = 48
    a, b = world_to_rig(BROOM_START), world_to_rig(BROOM_STOP)
    t = min(1.0, (f - 1) / walk_frames)
    phase = (f - 1) / 24 if f <= walk_frames else 2.0
    root = a.lerp(b, t)
    root.z = STAND_Z + (walk_bob(phase) if f <= walk_frames else 0.0)
    body = Body(root, 90)  # facing -X in the desk scene
    sweep = (f - 1) / 24 * 0.5 if f <= walk_frames else 1.0 + (f - walk_frames) / 24
    bottom, up = broom_frame(body, t, sweep)
    legs = walk_legs(phase) if f <= walk_frames else standing_legs()
    spec = {"root": tuple(root), "yaw": 90, "spine": (0.05, -0.12, 1), "neck": (0, -0.15, 1), "head": (0, -0.35, 1),
            "legs": legs, "arms": broom_arms(bottom, up, body)}
    return spec, (bottom, up, 1.0), (world_to_rig(CAT_FLOOR), 270)  # Tutu faces her


def act_crouch_pick(f):
    root = world_to_rig(BROOM_STOP)
    body0 = Body((root.x, root.y, STAND_Z), 90)
    cat_b = (0.0, -0.36, 0.0)  # Tutu in front of her feet (body frame)
    # 1-10 let the broom fall, 10-30 crouch + reach, 30-40 grab, 40-64 stand up hugging her
    down = smooth((f - 10) / 20) * (1 - smooth((f - 40) / 24))
    z = STAND_Z - 0.3 * down
    body = Body((root.x, root.y, z), 90)
    lift = smooth((f - 40) / 24)
    cat = lerp((cat_b[0], cat_b[1], 0.0), CAT_HOLD, lift)
    cat_rig = body0.p(cat) if lift == 0 else body.p(cat)
    reach_l = {"wrist": (0.1, cat_b[1] + 0.02, 0.2 + 0.4 * (1 - down)), "pole": (0.6, 0.2, -1), "hand": (-0.4, -0.5, -1),
               "palm": (-1, 0, 0), "fingers": {fn: (-0.5, -0.3, -1) for fn in FINGERS}, "thumb": (-0.5, -0.8, -0.4)}
    reach_r = {"wrist": (-0.1, cat_b[1] + 0.02, 0.2 + 0.4 * (1 - down)), "pole": (-0.6, 0.2, -1),
               "hand": (0.4, -0.5, -1), "palm": (1, 0, 0), "fingers": {fn: (0.5, -0.3, -1) for fn in FINGERS},
               "thumb": (0.5, -0.8, -0.4)}
    if lift > 0:
        hug = hug_arms(cat)
        arms = {n: {k: (lerp(reach[k], hug[n][k], lift) if k in ("wrist", "pole", "hand", "palm", "thumb")
                        else hug[n][k]) for k in hug[n]}
                for n, reach in (("L", reach_l), ("R", reach_r))}
    else:
        arms = {"L": reach_l, "R": reach_r}
    # local body: feet stay planted at the standing spot, knees forward
    legs = {n: {"ankle": (0.11 * s, 0.03, 0.085 - (z - STAND_Z)), "pole": (0.15 * s, -1, 0.2),
                "foot": (0, -1, -0.45)} for n, s in (("L", 1), ("R", -1))}
    spec = {"root": tuple(body.root), "yaw": 90, "spine": (0, -0.15 - 0.85 * down, 1), "neck": (0, -0.3 - 0.4 * down, 1),
            "head": (0, -0.4 - 0.3 * down, 1), "legs": legs, "arms": arms}
    # broom tips over to the floor during the first 10 frames, then lies there
    bottom, up = broom_frame(body0, 0, 1.0)
    side = body0.d((0.25, -0.15, 0)).normalized()
    fall = smooth((f - 1) / 10)
    up_now = (up.lerp(side, fall)).normalized()
    up_now.z = max(up_now.z, 0.02)
    broom = (bottom, up_now.normalized(), 1.0)
    return spec, broom, (cat_rig, 270 - 180 * lift)


def act_sit_with_cat(f):
    a = world_to_rig(BROOM_STOP)
    stand_spot = Vector((0.0, 0.16, STAND_Z))  # just in front of the chair, facing away from the desk
    walk_frames, sit_frames = 40, 24
    t = smooth((f - 1) / walk_frames)
    phase = (f - 1) / 24
    sit = smooth((f - walk_frames) / sit_frames)
    yaw = 90 + 90 * t
    root = a.lerp(stand_spot, t)
    root.z = STAND_Z + (walk_bob(phase) if f <= walk_frames else 0.0)
    root = root.lerp(Vector((0.0, 0.0, 0.0)), sit)
    cat = lerp(CAT_HOLD, CAT_LAP, sit)
    body = Body(root, yaw)
    if f <= walk_frames:
        legs = walk_legs(phase, stride=0.3)
    else:
        legs = {n: {k: (lerp(standing_legs()[n][k] if k in standing_legs()[n] else seated_legs()[n][k],
                             seated_legs()[n][k], sit) if k != "pole" else seated_legs()[n][k])
                    for k in seated_legs()[n]} for n in ("L", "R")}
    spec = {"root": tuple(root), "yaw": yaw, "spine": (0, -0.12 + 0.12 * sit, 1), "neck": (0, -0.12, 1),
            "head": (0.12 * sit, -0.2, 1), "legs": legs, "arms": hug_arms(cat)}
    return spec, None, (body.p(cat), yaw)


def act_idle_lap(f):
    t = (f - 1) / 48
    breath = 0.008 * math.sin(t * math.tau)
    cat = (CAT_LAP[0], CAT_LAP[1], CAT_LAP[2] + breath)
    body = Body((0, 0, 0), 180)
    arms = hug_arms(cat)
    arms["R"]["fingers"] = {fn: (1, 0, -0.4 + 0.4 * max(0.0, math.sin(t * math.tau * 2))) for fn in FINGERS}  # petting
    spec = {"root": (0, 0, 0), "yaw": 180, "spine": (0, 0.02 * math.sin(t * math.tau), 1), "neck": (0, -0.12, 1),
            "head": (0.12 + 0.05 * math.sin(t * math.tau), -0.2, 1), "legs": seated_legs(), "arms": arms}
    return spec, None, (body.p(cat), 180)


ACTIONS = {
    # name: (generator, last frame, key step)
    "gio_typing_loop": (act_typing, 25, 2),
    "gio_mouse_loop": (act_mouse, 49, 3),
    "gio_broom_enter": (act_broom_enter, 73, 2),
    "gio_crouch_pick_cat": (act_crouch_pick, 64, 2),
    "gio_sit_with_cat": (act_sit_with_cat, 64, 2),
    "gio_idle_lap_loop": (act_idle_lap, 49, 4),
}


# ---------------------------------------------------------------- broom + anchor

def build_broom():
    handle_mat = material("broom_handle", "#F4B860", rough=0.45)
    bristle_mat = material("broom_bristles", "#C9A48E", rough=0.8)
    band_mat = material("broom_band", "#F2A7A0", rough=0.5)
    # origin at the bristle tips, handle along +Z
    handle = cylinder("bh", 0.013, 1.0, loc=(0, 0, 0.6), mat=handle_mat)
    knob = sphere("bk", 0.018, loc=(0, 0, 1.1), mat=handle_mat)
    band = rounded_box("bb", (0.2, 0.06, 0.035), bevel=0.012, loc=(0, 0, 0.125), mat=band_mat)
    bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 0, 0.055))
    bristles = bpy.context.object
    bristles.scale = (0.24, 0.07, 0.11)
    bpy.ops.object.transform_apply(scale=True)
    bm = bmesh.new()
    bm.from_mesh(bristles.data)
    for v in bm.verts:  # flare the bottom like a straw fan
        if v.co.z < 0.03:
            v.co.x *= 1.25
            v.co.y *= 1.3
    bm.to_mesh(bristles.data)
    bm.free()
    m = bristles.modifiers.new("bevel", "BEVEL")
    m.width = 0.012
    m.segments = 3
    assign(bristles, bristle_mat)
    from common import apply_all, smooth as shade_smooth
    apply_all(bristles)
    shade_smooth(bristles, 40)
    broom = join([handle, knob, band, bristles], "gio_broom")
    # join keeps the handle's origin; move it to the bristle tips so the broom matrix is bottom + up
    broom.data.transform(Matrix.Translation(broom.location))
    broom.location = (0, 0, 0)
    return broom


def hide(obj):
    obj.location = (0, 0, 0)
    obj.rotation_quaternion = (1, 0, 0, 0)
    obj.scale = (0, 0, 0)


def broom_matrix(bottom, up):
    z = Vector(up).normalized()
    x = Vector((0, 0, 1)).cross(z)
    if x.length < 1e-4:
        x = Vector((1, 0, 0))
    x.normalize()
    y = z.cross(x)
    m = Matrix((x, y, z)).transposed().to_4x4()
    m.translation = bottom
    return m


def pose_at(rig, name, frame, broom=None, anchor=None):
    """Pose the rig (and broom/anchor, when given) for `name` at `frame`."""
    gen = ACTIONS[name][0]
    spec, b, cat = gen(frame)
    apply(rig, spec)
    if broom is not None:
        if b is None:
            hide(broom)
        else:
            broom.matrix_basis = broom_matrix(b[0], b[1])
    if anchor is not None:
        pos, yaw = cat if cat is not None else (Body((0, 0, 0), 180).p(CAT_LAP), 180)
        anchor.matrix_basis = Matrix.Translation(pos) @ Matrix.Rotation(math.radians(yaw), 4, "Z")
    bpy.context.view_layer.update()


def push(obj, name, act):
    ad = obj.animation_data
    ad.action = None
    tr = ad.nla_tracks.new()
    tr.name = name  # same track name on rig, broom and anchor -> one glTF animation
    tr.strips.new(name, int(act.frame_range[0]), act)
    tr.mute = True
    act.use_fake_user = True


def add_animations(rig):
    scene = bpy.context.scene
    scene.render.fps = FPS
    broom = build_broom()
    broom.parent = rig
    anchor = bpy.data.objects.new("gio_cat_anchor", None)
    anchor.empty_display_size = 0.05
    scene.collection.objects.link(anchor)
    anchor.parent = rig
    for o in (broom, anchor):
        o.rotation_mode = "QUATERNION"
        o.animation_data_create()
    rig.animation_data_create()
    for name, (gen, last, step) in ACTIONS.items():
        acts = {o: bpy.data.actions.new(f"{name}" if o is rig else f"{name}_{o.name}") for o in (rig, broom, anchor)}
        for o, a in acts.items():
            o.animation_data.action = a
        frames = list(range(1, last + 1, step))
        if frames[-1] != last:
            frames.append(last)
        for f in frames:
            pose_at(rig, name, f, broom, anchor)
            for pb in rig.pose.bones:
                pb.keyframe_insert("rotation_quaternion", frame=f)
                pb.keyframe_insert("location", frame=f)
            for o in (broom, anchor):
                o.keyframe_insert("location", frame=f)
                o.keyframe_insert("rotation_quaternion", frame=f)
                o.keyframe_insert("scale", frame=f)
        for o, a in acts.items():
            push(o, name, a)
        print(f"{name}: {len(frames)} keys")
    reset(rig)
    hide(broom)
    pose_at(rig, "gio_idle_lap_loop", 1, None, anchor)
    reset(rig)
    return [broom, anchor]
