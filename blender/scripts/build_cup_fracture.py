"""Mug fracture + baked fall -> blender/cup_fracture.blend, public/models/cup_fracture.glb.

The mug from build_cup is cut into Voronoi cells: 5 main shards (shard_01…05, one per project in
src/data/projects.ts) plus small decorative fragments. The fall is deterministic and baked to keyframes:
  1. slap: the mug slides from the desk spot to the front edge and tips (keyframed);
  2. fall: ballistic tumble to the floor (keyframed, analytic);
  3. break: from the impact frame the shards are dynamic rigid bodies, scattered by a short force-field
     burst, simulated once and baked to keyframes.
Everything is in desk-scene world space (same as desk_scene.glb), in one glTF animation `cup_fall_break`.
"""
import math
import os
import random
import sys

import bmesh
import bpy
from mathutils import Euler, Matrix, Quaternion, Vector

sys.path.append(os.path.dirname(__file__))
from common import *  # noqa: E402,F403
import build_cup  # noqa: E402

random.seed(11)
FPS = 60
START = Vector((0.47, 0.3, 0.75))  # spot_cup in desk_scene
ROT_Z = math.radians(20)           # same yaw as the intact mug in the desk scene
DESK_EDGE_Y = -0.035
SLIDE_END = 14
SIM_END = 200
ANIM = "cup_fall_break"
H, R = build_cup.H, build_cup.R


def cyl(angle_deg, z, r=R - 0.0025):
    """Point on the mug wall. Angle 0 = +X (handle side), -90 = -Y (label side)."""
    a = math.radians(angle_deg)
    return Vector((math.cos(a) * r, math.sin(a) * r, z))


# Seeds sit inside the wall (r = mid-wall). Tuned so the five main shards are 17–27 cm³ each.
# shard_01 keeps "WORLD'S BEST", shard_02 keeps "DEV", shard_03 has the handle, shard_05 is the foot.
MAIN_SEEDS = [cyl(-95, 0.058), cyl(-85, 0.015), cyl(30, 0.05), cyl(130, 0.06), Vector((-0.015, 0.02, 0.0))]
# Small decorative chips: pairs of close seeds at the rim and the foot make small cells.
CHIP_SEEDS = [cyl(-28, 0.096), cyl(-23, 0.095), cyl(-178, 0.096), cyl(-173, 0.095), cyl(75, 0.002), cyl(80, 0.003)]


# ---------------------------------------------------------------- fracture

def voronoi_cell(i, seeds, name):
    bpy.ops.mesh.primitive_cube_add(size=0.4)
    cell = bpy.context.object
    cell.name = name
    bm = bmesh.new()
    bm.from_mesh(cell.data)
    bmesh.ops.translate(bm, verts=bm.verts[:], vec=(0, 0, H / 2))  # seeds are in mesh space
    p = seeds[i]
    for j, q in enumerate(seeds):
        if j == i:
            continue
        mid = (p + q) / 2
        n = (q - p).normalized()
        geom = bm.verts[:] + bm.edges[:] + bm.faces[:]
        # n points from seed i toward seed j; clear_outer drops the half on the normal side (toward j)
        bmesh.ops.bisect_plane(bm, geom=geom, plane_co=mid, plane_no=n, clear_outer=True)
        # cap the cut right away, otherwise later cuts through the hole lose their vertices
        bmesh.ops.holes_fill(bm, edges=[e for e in bm.edges if e.is_boundary], sides=0)
    # rebuild as a clean closed convex hull for the exact boolean
    pts = [v.co.copy() for v in bm.verts]
    bm.clear()
    for co in pts:
        bm.verts.new(co)
    bmesh.ops.convex_hull(bm, input=bm.verts[:])
    bmesh.ops.delete(bm, geom=[v for v in bm.verts if not v.link_faces], context="VERTS")
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    bm.to_mesh(cell.data)
    bm.free()
    return cell


def mesh_volume(obj):
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    v = abs(bm.calc_volume())
    bm.free()
    return v


def fracture(cup):
    bm = bmesh.new()
    bm.from_mesh(cup.data)
    bmesh.ops.remove_doubles(bm, verts=bm.verts[:], dist=1e-6)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    bm.to_mesh(cup.data)
    bm.free()
    seeds = MAIN_SEEDS + CHIP_SEEDS
    white = bpy.data.materials["cup_white"]
    pieces = []
    for i in range(len(seeds)):
        main = i < len(MAIN_SEEDS)
        name = f"shard_{i + 1:02d}" if main else f"fragment_{i - len(MAIN_SEEDS) + 1:02d}"
        cell = voronoi_cell(i, seeds, f"cell_{i}")
        cell.data.materials.append(white)
        piece = cup.copy()
        piece.data = cup.data.copy()
        piece.name = name
        bpy.context.scene.collection.objects.link(piece)
        mod = piece.modifiers.new("cut", "BOOLEAN")
        mod.operation = "INTERSECT"
        mod.solver = "EXACT"
        mod.use_self = True
        mod.use_hole_tolerant = True
        mod.material_mode = "TRANSFER"
        mod.object = cell
        apply_all(piece)
        bpy.data.objects.remove(cell)
        if len(piece.data.vertices) < 4:
            bpy.data.objects.remove(piece)
            continue
        active(piece)
        bpy.ops.object.origin_set(type="ORIGIN_GEOMETRY", center="BOUNDS")
        smooth(piece, 40)
        pieces.append(piece)
    bpy.data.objects.remove(cup)
    for p in pieces:
        print(f"{p.name}: {mesh_volume(p) * 1e6:.1f} cm3, {len(p.data.polygons)} faces")
    return pieces


# ---------------------------------------------------------------- choreography

def ease_out(t):
    return 1 - (1 - t) ** 3


def cup_matrix(frame):
    """Mug root transform for the keyframed part (slap slide + ballistic fall)."""
    if frame <= SLIDE_END:
        t = ease_out((frame - 1) / (SLIDE_END - 1))
        pos = START.lerp(Vector((START.x + 0.03, DESK_EDGE_Y, START.z)), t)
        tip = math.radians(28) * max(0.0, (t - 0.55) / 0.45) ** 2
        rot = Euler((-tip, 0, ROT_Z + math.radians(15) * t)).to_matrix().to_4x4()
        return Matrix.Translation(pos) @ rot
    # ballistic: keep the slide velocity, gravity down, tumble forward
    t = (frame - SLIDE_END) / FPS
    vy = -0.55
    pos = Vector((START.x + 0.03, DESK_EDGE_Y + vy * t, START.z - 0.5 * 9.81 * t * t))
    tip = math.radians(28) + math.radians(330) * t
    rot = Euler((-tip, math.radians(40) * t, ROT_Z + math.radians(15))).to_matrix().to_4x4()
    return Matrix.Translation(pos) @ rot


def lowest_z(pieces, m):
    return min((m @ p.matrix_world @ v.co).z for p in pieces for v in p.data.vertices)


def find_impact(pieces):
    rest = {p.name: p.matrix_world.copy() for p in pieces}
    f = SLIDE_END
    while True:
        f += 1
        z = min((cup_matrix(f) @ rest[p.name] @ v.co).z for p in pieces for v in p.data.vertices)
        if z <= 0.0:
            return f, rest


# ---------------------------------------------------------------- rigid body sim

def setup_world(scene, impact):
    bpy.ops.rigidbody.world_add()
    rbw = scene.rigidbody_world
    rbw.substeps_per_frame = 10
    rbw.solver_iterations = 30
    rbw.point_cache.frame_start = 1
    rbw.point_cache.frame_end = SIM_END
    rbw.effector_weights.all = 1.0
    bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 0, -0.05))
    floor = bpy.context.object
    floor.name = "sim_floor"
    floor.scale = (4, 4, 0.1)
    bpy.ops.object.transform_apply(scale=True)
    active(floor)
    bpy.ops.rigidbody.object_add(type="PASSIVE")
    floor.rigid_body.friction = 0.7
    floor.rigid_body.restitution = 0.25
    floor.rigid_body.collision_margin = 0.001
    return floor


def burst(scene, at, impact):
    """Short outward push right after impact; strength keyed so the scatter is identical every bake."""
    bpy.ops.object.effector_add(type="FORCE", location=at)
    f = bpy.context.object
    f.name = "sim_burst"
    fld = f.field
    fld.shape = "POINT"
    fld.use_max_distance = True
    fld.distance_max = 0.35
    fld.falloff_type = "SPHERE"
    for frame, s in ((impact - 1, 0.0), (impact, 0.9), (impact + 3, 0.9), (impact + 4, 0.0)):
        fld.strength = s
        fld.keyframe_insert("strength", frame=frame)
    return f


def simulate(scene, pieces, impact, rest):
    scene.render.fps = FPS
    scene.frame_start, scene.frame_end = 1, SIM_END
    floor = setup_world(scene, impact)
    # keyframed (kinematic) until impact, then dynamic
    for p in pieces:
        active(p)
        bpy.ops.rigidbody.object_add(type="ACTIVE")
        rb = p.rigid_body
        rb.collision_shape = "MESH"
        rb.mesh_source = "BASE"
        rb.collision_margin = 0.0006
        rb.mass = 0.04 if p.name.startswith("shard") else 0.01
        rb.friction = 0.6
        rb.restitution = 0.3
        rb.linear_damping = 0.15
        rb.angular_damping = 0.35
        p.rotation_mode = "QUATERNION"
        for f in range(1, impact + 1):
            p.matrix_world = cup_matrix(f) @ rest[p.name]
            p.keyframe_insert("location", frame=f)
            p.keyframe_insert("rotation_quaternion", frame=f)
        rb.kinematic = True
        rb.keyframe_insert("kinematic", frame=impact - 1)
        rb.kinematic = False
        rb.keyframe_insert("kinematic", frame=impact)
    at = cup_matrix(impact).translation.copy()
    at.z = -0.03
    field = burst(scene, at, impact)

    # step the sim once, in order, and record every world matrix
    record = {p.name: {} for p in pieces}
    for f in range(1, SIM_END + 1):
        scene.frame_set(f)
        for p in pieces:
            record[p.name][f] = p.matrix_world.copy()

    # replace the simulation by plain keyframes
    for p in pieces:
        p.animation_data_clear()
        active(p)
        bpy.ops.rigidbody.object_remove()
    bpy.data.objects.remove(field)
    bpy.data.objects.remove(floor)
    bpy.ops.rigidbody.world_remove()
    return record


def bake(pieces, record):
    for p in pieces:
        p.rotation_mode = "QUATERNION"
        prev = None
        for f in range(1, SIM_END + 1):
            p.matrix_world = record[p.name][f]
            q = p.rotation_quaternion.copy()
            if prev is not None and prev.dot(q) < 0:
                q.negate()  # keep quaternions continuous so three.js slerps the short way
                p.rotation_quaternion = q
            prev = q
            p.keyframe_insert("location", frame=f)
            p.keyframe_insert("rotation_quaternion", frame=f)
        push_track(p)


def push_track(obj):
    ad = obj.animation_data
    act = ad.action
    act.name = f"{ANIM}_{obj.name}"
    ad.action = None
    tr = ad.nla_tracks.new()
    tr.name = ANIM  # same track name on every object -> one merged glTF animation
    # keep the action on its own frames (drops start at impact, not at frame 1)
    tr.strips.new(ANIM, int(act.frame_range[0]), act)


# ---------------------------------------------------------------- coffee

def coffee_fx(impact, rest_coffee, coffee):
    """Coffee surface rides along until impact, then splashes into stylised round drops and a puddle."""
    coffee.rotation_mode = "QUATERNION"
    for f in range(1, impact + 1):
        coffee.matrix_world = cup_matrix(f) @ rest_coffee
        coffee.scale = (1, 1, 1)
        coffee.keyframe_insert("location", frame=f)
        coffee.keyframe_insert("rotation_quaternion", frame=f)
        coffee.keyframe_insert("scale", frame=f)
    coffee.scale = (0, 0, 0)
    coffee.keyframe_insert("scale", frame=impact + 1)
    push_track(coffee)

    hit = cup_matrix(impact).translation.copy()
    hit.z = 0.0
    coffee_mat = material("coffee_spill", "#4A2C1E", rough=0.12)
    objs = []

    bpy.ops.mesh.primitive_cylinder_add(radius=1, depth=0.002, vertices=40, location=(hit.x, hit.y, 0.001))
    puddle = bpy.context.object
    puddle.name = "coffee_puddle"
    # wobbly organic outline
    for v in puddle.data.vertices:
        a = math.atan2(v.co.y, v.co.x)
        k = 1 + 0.12 * math.sin(a * 3 + 1) + 0.07 * math.sin(a * 7)
        v.co.x *= k
        v.co.y *= k * 0.8
    smooth(puddle, 40)
    assign(puddle, coffee_mat)
    for f, s in ((impact, 0.0), (impact + 6, 0.06), (impact + 30, 0.11)):
        puddle.scale = (s, s, 1)
        puddle.keyframe_insert("scale", frame=f)
    push_track(puddle)
    objs.append(puddle)

    g = 9.81
    for i in range(14):
        a = random.uniform(0, math.tau)
        speed = random.uniform(0.5, 1.1)
        vz = random.uniform(0.9, 1.6)
        r = random.uniform(0.006, 0.011)
        d = sphere(f"coffee_drop_{i + 1:02d}", r, seg=16, rings=8, mat=coffee_mat)
        d.scale = (0, 0, 0)
        d.keyframe_insert("scale", frame=impact - 1)
        t_land = 2 * vz / g
        frames = max(2, int(t_land * FPS))
        for k in range(frames + 1):
            t = k / FPS
            d.location = (hit.x + math.cos(a) * speed * t, hit.y + math.sin(a) * speed * t * 0.8,
                          0.02 + vz * t - 0.5 * g * t * t)
            stretch = 1 + 0.6 * min(1.0, abs(vz - g * t) / 2)  # teardrop stretch along the motion
            d.scale = (1 / math.sqrt(stretch), 1 / math.sqrt(stretch), stretch)
            d.keyframe_insert("location", frame=impact + k)
            d.keyframe_insert("scale", frame=impact + k)
        # splat into a tiny flat dot and stay there
        d.location.z = 0.0015
        d.scale = (1.8, 1.8, 0.15)
        d.keyframe_insert("location", frame=impact + frames + 2)
        d.keyframe_insert("scale", frame=impact + frames + 2)
        push_track(d)
        objs.append(d)
    return objs


# ---------------------------------------------------------------- main

def build():
    cup, coffee, steam = build_cup.build()
    bpy.data.objects.remove(steam)
    bpy.context.view_layer.update()
    coffee.parent = None
    coffee.matrix_world = cup.matrix_world @ coffee.matrix_parent_inverse @ Matrix.Translation(coffee.location)
    pieces = fracture(cup)
    impact, rest = find_impact(pieces)
    print(f"impact frame: {impact} ({impact / FPS:.2f}s)")
    scene = bpy.context.scene
    record = simulate(scene, pieces, impact, rest)
    bake(pieces, record)
    fx = coffee_fx(impact, Matrix.Translation(coffee.location), coffee)
    root = bpy.data.objects.new("cup_fracture", None)
    scene.collection.objects.link(root)
    for o in pieces + fx + [coffee]:
        o.parent = root
    root["impact_frame"] = impact
    root["fps"] = FPS
    for p in pieces:
        print(f"{p.name} rests at {tuple(round(c, 3) for c in record[p.name][SIM_END].translation)}")
    return root, pieces, fx, coffee, impact


if __name__ == "__main__":
    root, pieces, fx, coffee, impact = build()
    sc = bpy.context.scene
    sc.frame_set(1)
    save_blend("cup_fracture.blend")
    export_glb(os.path.join(MODELS_DIR, "cup_fracture.glb"), [root] + pieces + fx + [coffee], animations=True)

    # previews on a plain wood-toned floor
    bpy.ops.mesh.primitive_plane_add(size=4, location=(0.4, -0.3, 0))
    assign(bpy.context.object, material("preview_floor", "#7A4E33", rough=0.6))
    studio(sc, bg="#2A2944", target=(0.5, -0.3, 0.1), dist=2.0)
    cam_d = bpy.data.cameras.new("cam")
    cam_d.lens = 45
    cam = bpy.data.objects.new("cam", cam_d)
    sc.collection.objects.link(cam)
    sc.camera = cam
    sc.render.resolution_x, sc.render.resolution_y = 1400, 900
    sc.frame_set(SIM_END)
    rest_c = sum((p.matrix_world.translation for p in pieces), Vector()) / len(pieces)
    shots = [("cup_fall_mid", impact - 6, (1.2, -1.2, 0.8), (0.5, -0.1, 0.35)),
             ("cup_impact", impact + 3, (0.9, -0.9, 0.45), (0.5, -0.35, 0.03)),
             ("cup_shards_rest", SIM_END, (rest_c.x + 0.5, rest_c.y - 0.55, 0.45), (rest_c.x, rest_c.y, 0.0)),
             ("cup_shards_top", SIM_END, (rest_c.x, rest_c.y - 0.05, 0.9), (rest_c.x, rest_c.y, 0.0))]
    for name, frame, loc, target in shots:
        sc.frame_set(frame)
        cam.location = loc
        cam.rotation_euler = (Vector(target) - Vector(loc)).to_track_quat("-Z", "Y").to_euler()
        sc.render.filepath = os.path.join(PREVIEW_DIR, f"{name}.png")
        bpy.ops.render.render(write_still=True)
