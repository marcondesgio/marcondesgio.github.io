"""Night desk scene (refs: docs/6de4513….jpg, c6e3942….jpg, fe957b5….jpg)
-> blender/desk_scene.blend (then bake_desk.py bakes it and exports public/models/desk_scene.glb).

Layout: back wall at +Y, Gio sits at the desk facing +Y with her back to the camera.
Left -> right from the camera: Gio, Tutu, mug. Run build_cup/build_tutu/build_gio first;
the preview renders link their .blend files in.
"""
import math
import os
import random
import sys

import bpy
from mathutils import Euler, Matrix, Vector

sys.path.append(os.path.dirname(__file__))
from common import *  # noqa: E402,F403
import gio_anim  # noqa: E402
import decor  # noqa: E402
import build_tutu  # noqa: E402

random.seed(7)
DESK_TOP = 0.75
DESK_W, DESK_D = 1.7, 0.72
WALL_Y = 0.78

CODE = [
    ("class TutuWatcher extends StatefulWidget {", "#C9A0F0"),
    ("  const TutuWatcher({super.key});", "#A39DB8"),
    ("", "#A39DB8"),
    ("  @override", "#F4B860"),
    ("  State<TutuWatcher> createState() => _State();", "#9FD3F0"),
    ("}", "#A39DB8"),
    ("", "#A39DB8"),
    ("class _State extends State<TutuWatcher> {", "#C9A0F0"),
    ("  bool coffeeIsSafe = true; // famous last words", "#7FA77A"),
    ("", "#A39DB8"),
    ("  void onPawDetected(Paw paw) {", "#9FD3F0"),
    ("    if (paw.isNear(mug)) {", "#F6EFE6"),
    ("      setState(() => coffeeIsSafe = false);", "#F2A7A0"),
    ("      mug.shatter(shards: projects.length);", "#F4B860"),
    ("    }", "#F6EFE6"),
    ("  }", "#F6EFE6"),
    ("", "#A39DB8"),
    ("  @override", "#F4B860"),
    ("  Widget build(BuildContext context) {", "#9FD3F0"),
    ("    return Portfolio(shards: projects);", "#F6EFE6"),
    ("  }", "#F6EFE6"),
    ("}", "#A39DB8"),
]

POSTITS = [
    ("flutter\nrun", "#F7E07A"),
    ("TODO:\nmais café", "#F2A7A0"),
    ("<3 dart", "#9FD3F0"),
    ("bug #42\n(é a Tutu)", "#B9E3A6"),
    ("git push\n--force?\nNÃO", "#F7E07A"),
    ("pub get", "#F2A7A0"),
]


# ---------------------------------------------------------------- textures

def textures():
    code = os.path.join(TEX_DIR, "monitor_code.png")
    text_image(code, [l for l, _ in CODE], size=(1600, 1000), font="consola.ttf", bg="#1B1A2B",
               colors=[c for _, c in CODE], scale=0.072, line_height=1.45, align="LEFT", offset=(0.06, -0.02))
    notes = []
    for i, (txt, paper) in enumerate(POSTITS):
        p = os.path.join(TEX_DIR, f"postit_{i}.png")
        lines = txt.split("\n")
        text_image(p, lines, size=(256, 256), font="segoepr.ttf", fg="#2B2440", bg=paper, scale=0.36,
                   line_height=1.15)
        notes.append((p, paper))
    return code, notes


def sky_texture():
    """Night sky for the window: gradient + stars + a soft moon, rendered once to PNG."""
    p = os.path.join(TEX_DIR, "window_sky.png")
    sc = bpy.data.scenes.new("sky_tmp")
    bpy.ops.mesh.primitive_plane_add(size=2)
    plane = bpy.context.object
    for c in plane.users_collection:
        c.objects.unlink(plane)
    sc.collection.objects.link(plane)
    mat = bpy.data.materials.new("sky_tmp")
    mat.use_nodes = True
    nt = mat.node_tree
    nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    em = nt.nodes.new("ShaderNodeEmission")
    tc = nt.nodes.new("ShaderNodeTexCoord")
    sep = nt.nodes.new("ShaderNodeSeparateXYZ")
    ramp = nt.nodes.new("ShaderNodeValToRGB")
    ramp.color_ramp.elements[0].color = hex_rgba("#161528")
    ramp.color_ramp.elements[1].color = hex_rgba("#3A3466")
    vor = nt.nodes.new("ShaderNodeTexVoronoi")
    vor.inputs["Scale"].default_value = 60
    vor.feature = "DISTANCE_TO_EDGE" if False else "F1"
    stars = nt.nodes.new("ShaderNodeMath")
    stars.operation = "LESS_THAN"
    stars.inputs[1].default_value = 0.035
    moon_d = nt.nodes.new("ShaderNodeVectorMath")
    moon_d.operation = "DISTANCE"
    moon_d.inputs[1].default_value = (0.72, 0.78, 0)
    moon = nt.nodes.new("ShaderNodeMapRange")
    moon.inputs["From Min"].default_value = 0.11
    moon.inputs["From Max"].default_value = 0.13
    moon.inputs["To Min"].default_value = 1
    moon.inputs["To Max"].default_value = 0
    mix1 = nt.nodes.new("ShaderNodeMix")
    mix1.data_type = "RGBA"
    mix1.inputs["B"].default_value = hex_rgba("#E8E6F7")
    mix2 = nt.nodes.new("ShaderNodeMix")
    mix2.data_type = "RGBA"
    mix2.inputs["B"].default_value = hex_rgba("#F6EFE6")
    L = nt.links.new
    L(tc.outputs["UV"], sep.inputs[0])
    L(sep.outputs["Y"], ramp.inputs[0])
    L(tc.outputs["UV"], vor.inputs["Vector"])
    L(vor.outputs["Distance"], stars.inputs[0])
    L(ramp.outputs["Color"], mix1.inputs["A"])
    L(stars.outputs[0], mix1.inputs["Factor"])
    L(tc.outputs["UV"], moon_d.inputs[0])
    L(moon_d.outputs["Value"], moon.inputs["Value"])
    L(mix1.outputs["Result"], mix2.inputs["A"])
    L(moon.outputs["Result"], mix2.inputs["Factor"])
    L(mix2.outputs["Result"], em.inputs["Color"])
    L(em.outputs[0], out.inputs[0])
    plane.data.materials.append(mat)
    cam_d = bpy.data.cameras.new("sc")
    cam_d.type = "ORTHO"
    cam_d.ortho_scale = 2
    cam = bpy.data.objects.new("sc", cam_d)
    cam.location = (0, 0, 3)
    sc.collection.objects.link(cam)
    sc.camera = cam
    sc.render.engine = "BLENDER_EEVEE"
    sc.render.resolution_x = sc.render.resolution_y = 512
    sc.view_settings.view_transform = "Standard"
    sc.render.filepath = p
    bpy.ops.render.render(write_still=True, scene=sc.name)
    bpy.data.scenes.remove(sc)
    return p


# ---------------------------------------------------------------- props

def floor(col):
    # warm honey planks with real grain (procedural, baked into the lightmap)
    woods = [decor.wood_material(f"wood_{i}", light, dark) for i, (light, dark) in enumerate(
        (("#C98E5E", "#9C6A43"), ("#B97F52", "#8E5E3B"), ("#D19A6A", "#A5734B"), ("#BE8558", "#93633F")))]
    planks = []
    w = 0.16
    x = -2.4
    while x < 2.4:
        # staggered plank lengths so the joints don't line up
        y = -2.6 + random.uniform(0, 1.2)
        start = -2.6
        for y_end in (y, y + random.uniform(1.4, 2.2), 1.2):
            length = y_end - start
            if length > 0.05:
                p = rounded_box("plank", (w - 0.006, length - 0.006, 0.02), bevel=0.004, segments=2,
                                loc=(x + w / 2, start + length / 2, -0.01))
                assign(p, random.choice(woods))
                planks.append(p)
            start = y_end
        x += w
    f = join(planks, "floor")
    return link(f, col)


def wall(col, sky):
    wall_mat = decor.wallpaper_material("wall", "#7B6BB0", "#8C7CC2")
    trim = material("trim", "#F6EFE6", rough=0.6)
    parts = [assign(rounded_box("wall_back", (4.8, 0.08, 2.8), bevel=0.005, loc=(0, WALL_Y + 0.04, 1.4)), wall_mat),
             assign(rounded_box("baseboard", (4.8, 0.02, 0.09), bevel=0.006, loc=(0, WALL_Y - 0.005, 0.045)), trim)]
    w = join(parts, "wall")
    link(w, col)
    # window up and to the right of the monitor
    wx, wz, ww, wh = 0.55, 1.62, 0.8, 0.85
    frame_parts = []
    for loc, size in (((wx, 0, wz + wh / 2), (ww + 0.08, 0.06, 0.06)), ((wx, 0, wz - wh / 2), (ww + 0.12, 0.1, 0.06)),
                      ((wx - ww / 2, 0, wz), (0.06, 0.06, wh)), ((wx + ww / 2, 0, wz), (0.06, 0.06, wh)),
                      ((wx, 0, wz), (0.035, 0.04, wh)), ((wx, 0, wz + 0.1), (ww, 0.04, 0.035))):
        frame_parts.append(rounded_box("wf", size, bevel=0.012, loc=(loc[0], WALL_Y - 0.01, loc[2])))
    frame = assign(join(frame_parts, "window_frame"), trim)
    link(frame, col)
    bpy.ops.mesh.primitive_plane_add(size=1, location=(wx, WALL_Y + 0.005, wz), rotation=(math.radians(90), 0, 0))
    glass = bpy.context.object
    glass.name = "window_sky"
    glass.scale = (ww, wh, 1)
    assign(glass, material("window_sky", "#000000", emit="image", image=sky, emit_strength=1.0))
    link(glass, col)
    pot, plant = decor.sill_plant(col, wx + 0.22, WALL_Y - 0.06, wz - wh / 2 + 0.03)
    drapes = decor.curtains(col, WALL_Y, wx, wz, ww, wh)
    return [w, frame, glass, pot, plant] + drapes


def desk(col):
    white = material("desk_white", "#F3F1F4", rough=0.45)
    top = rounded_box("desk_top", (DESK_W, DESK_D, 0.045), bevel=0.018, loc=(0, DESK_D / 2, DESK_TOP - 0.0225))
    parts = [top]
    for sx in (1, -1):
        for y in (0.06, DESK_D - 0.06):
            parts.append(rounded_box("leg", (0.05, 0.05, DESK_TOP - 0.04), bevel=0.012,
                                     loc=(sx * (DESK_W / 2 - 0.06), y, (DESK_TOP - 0.04) / 2)))
    # drawer block on the right, chunky toy handle
    parts.append(rounded_box("drawer", (0.4, DESK_D - 0.1, 0.16), bevel=0.014, loc=(0.58, DESK_D / 2, DESK_TOP - 0.12)))
    d = assign(join(parts, "desk"), white)
    handle = rounded_box("drawer_handle", (0.12, 0.02, 0.02), bevel=0.008, loc=(0.58, 0.04, DESK_TOP - 0.12),
                         mat=material("handle", "#F7A8C8", rough=0.4))
    for o in (d, handle):
        link(o, col)
    return [d, handle]


def monitor(col, code_tex, notes):
    body_mat = material("monitor_body", "#E9E6EE", rough=0.5)
    cx, cy, cz = -0.22, 0.5, 1.08
    W, H = 0.66, 0.42
    shell = rounded_box("monitor_shell", (W, 0.06, H), bevel=0.03, loc=(cx, cy, cz))
    back = rounded_box("monitor_back", (W * 0.6, 0.08, H * 0.55), bevel=0.03, loc=(cx, cy + 0.05, cz))
    neck = rounded_box("monitor_neck", (0.07, 0.05, 0.22), bevel=0.02, loc=(cx, cy + 0.06, DESK_TOP + 0.12))
    base = rounded_box("monitor_base", (0.28, 0.2, 0.025), bevel=0.012, loc=(cx, cy + 0.04, DESK_TOP + 0.0125))
    m = assign(join([shell, back, neck, base], "monitor"), body_mat)
    link(m, col)
    bpy.ops.mesh.primitive_plane_add(size=1, location=(cx, cy - 0.0305, cz + 0.01), rotation=(math.radians(90), 0, 0))
    screen = bpy.context.object
    screen.name = "monitor_screen"
    screen.scale = (W - 0.07, H - 0.08, 1)
    bpy.ops.object.transform_apply(scale=True)
    assign(screen, material("monitor_screen", "#000000", emit="image", image=code_tex, emit_strength=1.4, rough=0.25))
    link(screen, col)
    # post-its stuck on the bezel and on the wall, slightly crooked
    spots = [((cx - W / 2 + 0.02, cy - 0.034, cz + H / 2 - 0.03), 12), ((cx + W / 2 - 0.01, cy - 0.034, cz + 0.08), -9),
             ((cx + W / 2 + 0.03, cy - 0.034, cz - 0.1), 6), ((cx - W / 2 - 0.12, WALL_Y - 0.002, 1.3), -5),
             ((cx - W / 2 - 0.25, WALL_Y - 0.002, 1.18), 8), ((cx - W / 2 - 0.1, WALL_Y - 0.002, 1.0), -12)]
    stickies = []
    for i, ((x, y, z), ang) in enumerate(spots):
        tex, paper = notes[i % len(notes)]
        bpy.ops.mesh.primitive_plane_add(size=0.085, location=(x, y, z),
                                         rotation=(math.radians(90), math.radians(ang), 0))
        p = bpy.context.object
        p.name = f"postit_{i + 1:02d}"
        sol = p.modifiers.new("s", "SOLIDIFY")
        sol.thickness = 0.002
        apply_all(p)
        assign(p, material(f"postit_{i}", paper, rough=0.8, image=tex))
        stickies.append(link(p, col))
    return [m, screen] + stickies


def keyboard(col):
    shell = rounded_box("kb_shell", (0.44, 0.15, 0.028), bevel=0.012, loc=(-0.22, 0.2, DESK_TOP + 0.014),
                        rot=(math.radians(-3), 0, 0), mat=material("kb_shell", "#ECE9F0", rough=0.5))
    keys = []
    for r, (n, off) in enumerate(((13, 0.0), (12, 0.008), (11, 0.014), (10, 0.02))):
        for c in range(n):
            x = -0.22 - 0.195 + off + c * 0.0305
            keys.append(rounded_box("key", (0.026, 0.026, 0.016), bevel=0.006, segments=2,
                                    loc=(x, 0.245 - r * 0.0305, DESK_TOP + 0.032 + r * 0.0015)))
    keys.append(rounded_box("space", (0.17, 0.026, 0.016), bevel=0.006, segments=2,
                            loc=(-0.22, 0.245 - 4 * 0.0305, DESK_TOP + 0.038)))
    k = assign(join(keys, "keyboard_keys"), material("kb_keys", "#FBFAFC", rough=0.45))
    accent = rounded_box("key_enter", (0.04, 0.026, 0.017), bevel=0.006, segments=2,
                         loc=(-0.22 + 0.2, 0.245 - 1.5 * 0.0305, DESK_TOP + 0.034),
                         mat=material("kb_accent", "#F4B860", rough=0.4))
    for o in (shell, k, accent):
        link(o, col)
    return [shell, k, accent]


def mouse(col):
    pad = rounded_box("mouse_pad", (0.24, 0.2, 0.005), bevel=0.0025, segments=2, loc=(0.12, 0.22, DESK_TOP + 0.0025),
                      mat=material("mouse_pad", "#7D6FA8", rough=0.85))
    m = sphere("mouse", 1, loc=(0.12, 0.21, DESK_TOP + 0.018), scale=(0.032, 0.052, 0.022),
               mat=material("mouse", "#F3F1F4", rough=0.4))
    wheel = rounded_box("mouse_wheel", (0.006, 0.014, 0.008), bevel=0.003, loc=(0.12, 0.185, DESK_TOP + 0.038),
                        mat=material("kb_accent", "#F4B860"))
    cable = tube("mouse_cable", [(0.12, 0.26, DESK_TOP + 0.01), (0.1, 0.4, DESK_TOP + 0.006),
                                 (0.0, 0.55, DESK_TOP + 0.006), (-0.12, 0.6, DESK_TOP + 0.006)], 0.004,
                 mat=material("cable", "#ECE9F0", rough=0.6))
    for o in (pad, m, wheel, cable):
        link(o, col)
    return [pad, m, wheel, cable]


def lamp(col):
    shade_mat = material("lamp_shade", "#F7A8C8", rough=0.45)
    metal = material("lamp_arm", "#F6EFE6", rough=0.4)
    bx, by = 0.8, 0.6  # set back to the right so the shade clears Tutu (0.42, 0.44)
    base = cylinder("lamp_base", 0.075, 0.03, loc=(bx, by, DESK_TOP + 0.015), bevel=0.012, mat=shade_mat)
    j1 = Vector((bx, by, DESK_TOP + 0.03))
    j2 = Vector((bx - 0.05, by - 0.04, DESK_TOP + 0.36))
    j3 = Vector((bx - 0.17, by - 0.25, DESK_TOP + 0.44))
    arm1 = tube("lamp_arm1", [j1, (j1 + j2) / 2, j2], 0.012, mat=metal)
    arm2 = tube("lamp_arm2", [j2, (j2 + j3) / 2, j3], 0.012, mat=metal)
    knuckle = sphere("lamp_knuckle", 0.022, loc=j2, mat=shade_mat)
    # bell shade pointing down toward the mug/keyboard area
    prof = [(0.0, 0.0), (0.03, 0.0), (0.045, -0.03), (0.08, -0.1), (0.095, -0.13), (0.09, -0.135)]
    me = bpy.data.meshes.new("shade")
    me.from_pydata([(x, 0, z) for x, z in prof], [(i, i + 1) for i in range(len(prof) - 1)], [])
    shade = bpy.data.objects.new("lamp_shade", me)
    bpy.context.scene.collection.objects.link(shade)
    s = shade.modifiers.new("lathe", "SCREW")
    s.axis = "Z"
    s.steps = 48
    s.render_steps = 48
    sol = shade.modifiers.new("solid", "SOLIDIFY")
    sol.thickness = 0.006
    apply_all(shade)
    smooth(shade, 50)
    shade.location = j3 + Vector((0, 0, 0.02))
    shade.rotation_euler = (math.radians(-25), math.radians(20), 0)
    assign(shade, shade_mat)
    bulb = sphere("lamp_bulb", 0.03, loc=(0, 0, 0))
    assign(bulb, material("lamp_bulb", "#FFF3D6", emit="#FFD89A", emit_strength=9))
    bulb.parent = shade
    bulb.location = (0, 0, -0.07)
    objs = [base, arm1, arm2, knuckle, shade, bulb]
    for o in objs:
        link(o, col)
    return objs, shade


def chair(col):
    dark = material("chair_dark", "#2A2944", rough=0.6)
    seat_mat = decor.fabric_material("chair_seat", "#9C86E0", 160)
    cx, cy = -0.22, -0.30
    seat_z = 0.56
    seat = rounded_box("chair_seat", (0.5, 0.48, 0.09), bevel=0.04, loc=(cx, cy, seat_z), mat=seat_mat)
    back = rounded_box("chair_back", (0.44, 0.08, 0.3), bevel=0.04, loc=(cx, cy - 0.27, seat_z + 0.26),
                       rot=(math.radians(-8), 0, 0), mat=seat_mat)
    spine = rounded_box("chair_spine", (0.06, 0.04, 0.3), bevel=0.015, loc=(cx, cy - 0.25, seat_z + 0.08),
                        rot=(math.radians(-15), 0, 0), mat=dark)
    pole = cylinder("chair_pole", 0.03, seat_z - 0.1, loc=(cx, cy, (seat_z - 0.1) / 2 + 0.06), mat=dark)
    legs = [pole, seat, back, spine]
    for i in range(5):
        a = math.radians(90 + i * 72)
        tip = Vector((cx + math.cos(a) * 0.3, cy + math.sin(a) * 0.3, 0.07))
        legs.append(tube("chair_leg", [(cx, cy, 0.09), ((cx + tip.x) / 2, (cy + tip.y) / 2, 0.085), tip], 0.022))
        legs.append(sphere("caster", 0.03, loc=(tip.x, tip.y, 0.03)))
    for o in legs[4:]:
        assign(o, dark)
    for sx in (1, -1):
        arm = rounded_box("chair_arm", (0.05, 0.28, 0.035), bevel=0.015, loc=(cx + sx * 0.27, cy + 0.02, seat_z + 0.2),
                          mat=dark)
        post = rounded_box("chair_arm_post", (0.035, 0.035, 0.18), bevel=0.012,
                           loc=(cx + sx * 0.27, cy - 0.04, seat_z + 0.1), mat=dark)
        legs += [arm, post]
    c = join(legs, "chair")
    return link(c, col), seat_z + 0.045


# ---------------------------------------------------------------- lighting

def night_lights(scene, shade):
    world = bpy.data.worlds.new("night")
    world.use_nodes = True
    world.node_tree.nodes["Background"].inputs[0].default_value = hex_rgba("#3A3060")
    world.node_tree.nodes["Background"].inputs[1].default_value = 1.6
    scene.world = world
    lights = bpy.data.collections.new("lights")
    scene.collection.children.link(lights)

    def add(name, kind, loc, color, energy, size=0.1, aim=None, spot=None):
        ld = bpy.data.lights.new(name, kind)
        ld.color = hex_rgba(color)[:3]
        ld.energy = energy
        if kind == "AREA":
            ld.size = size
        elif kind in ("POINT", "SPOT"):
            ld.shadow_soft_size = size
        if spot:
            ld.spot_size = math.radians(spot)
            ld.spot_blend = 0.6
        o = bpy.data.objects.new(name, ld)
        o.location = loc
        if aim is not None:
            o.rotation_euler = (Vector(aim) - Vector(loc)).to_track_quat("-Z", "Y").to_euler()
        lights.objects.link(o)
        return o

    bpy.context.view_layer.update()
    lamp_pos = shade.matrix_world @ Vector((0, 0, -0.08))
    # feedback round 2: a softer lamp, a real glow from the monitor and a gentle room ambient
    add("lamp_key", "SPOT", lamp_pos, "#FFD2A1", 64, size=0.06, aim=(0.3, 0.3, DESK_TOP), spot=125)
    add("lamp_glow", "POINT", lamp_pos + Vector((0, -0.05, -0.02)), "#FFC9A0", 4.5, size=0.08)
    add("monitor_glow", "AREA", (-0.22, 0.43, 1.08), "#A9D8F5", 45, size=0.62, aim=(-0.22, -1.0, 0.95))
    add("ambient_fill", "AREA", (0.0, -0.4, 2.6), "#CDBDF5", 140, size=3.2, aim=(0.0, -0.1, 0.0))
    add("moon_fill", "AREA", (0.55, WALL_Y - 0.15, 1.7), "#7C86C8", 10, size=0.8, aim=(0.0, -0.8, 0.6))
    add("room_bounce", "AREA", (-1.2, -1.8, 2.4), "#5A4F96", 70, size=3.0, aim=(0, 0.3, 0.6))
    # moonlight from a window behind the viewer, pooling on the floor where the mug breaks (scenes 3–6
    # happen down there; the desk would block light coming from the back wall)
    add("moon_floor", "SPOT", (1.1, -1.9, 2.1), "#9AA2E0", 110, size=0.5, aim=(0.5, -0.4, 0.0), spot=50)
    scene.eevee.use_shadows = True
    scene.eevee.use_raytracing = True
    scene.view_settings.view_transform = "Khronos PBR Neutral"
    scene.view_settings.exposure = 0.0


# ---------------------------------------------------------------- characters for the preview

def link_from(blend, names, col):
    path = os.path.join(BLENDER_DIR, blend)
    with bpy.data.libraries.load(path, link=False) as (src, dst):
        dst.objects = [n for n in src.objects if n in names or not names]
    objs = [o for o in dst.objects if o]
    for o in objs:
        col.objects.link(o)
    return objs


def place(objs, root_name, loc, rot_z=0.0):
    root = next(o for o in objs if o.name == root_name)
    root.location = loc
    root.rotation_euler = (0, 0, math.radians(rot_z))
    return root


def build():
    reset_scene()
    sky = sky_texture()
    code_tex, notes = textures()
    env = collection("environment")
    objs = [floor(env)] + wall(env, sky) + desk(env) + keyboard(env) + mouse(env)
    objs += monitor(env, code_tex, notes)
    lamp_objs, shade = lamp(env)
    chair_obj, seat_top = chair(env)
    objs += lamp_objs + [chair_obj]
    # cozy office (feedback round 2): bookshelf, framed art, fairy lights, big plant
    objs += decor.bookshelf(env, WALL_Y) + decor.frames(env, WALL_Y) + decor.string_lights(env, WALL_Y)
    objs += decor.floor_plant(env)

    # markers the web app reads for positioning characters and the camera path
    markers = {
        "spot_cup": (0.47, 0.3, DESK_TOP),
        "spot_tutu_desk": (0.42, 0.44, DESK_TOP),  # right behind the mug, so her swipe reaches it
        "spot_gio_seat": tuple(gio_anim.RIG_LOC),  # gio_rig origin (rotated 180°, facing the desk)
        "spot_cup_floor": (0.62, -0.45, 0.0),
    }
    for name, loc in markers.items():
        e = bpy.data.objects.new(name, None)
        e.location = loc
        e.empty_display_size = 0.05
        env.objects.link(e)
        objs.append(e)
    return env, objs, shade, seat_top


if __name__ == "__main__":
    env, objs, shade, seat_top = build()
    # the web GLB is exported by bake_desk.py, after baking light + AO into this scene

    sc = bpy.context.scene
    night_lights(sc, shade)
    chars = collection("characters_preview")
    cup = link_from("cup.blend", [], chars)
    place(cup, "cup", (0.47, 0.3, DESK_TOP), rot_z=20)
    shards = link_from("cup_fracture.blend", [], chars)
    tutu = link_from("tutu.blend", [], chars)
    tutu_root = place(tutu, "tutu", (0.42, 0.44, DESK_TOP), rot_z=20)
    tutu_rig = next(o for o in tutu if o.name == "tutu_rig")
    gio = link_from("gio.blend", [], chars)
    rig = place(gio, "gio_rig", tuple(gio_anim.RIG_LOC), rot_z=math.degrees(gio_anim.RIG_YAW))
    broom = next(o for o in gio if o.name == "gio_broom")
    anchor = next(o for o in gio if o.name == "gio_cat_anchor")
    chair_obj = next(o for o in objs if o.name == "chair")

    fill_d = bpy.data.lights.new("preview_fill", "AREA")
    fill_d.size = 1.0
    fill_d.color = hex_rgba("#C9C2F0")[:3]
    fill = bpy.data.objects.new("preview_fill", fill_d)  # preview only, not in any GLB
    sc.collection.objects.link(fill)

    def setup(gio_action, frame, tutu_mode, broken, chair_turned=False):
        """tutu_mode: 'desk' (sitting by the mug) or 'anchor' (wherever Gio's cat anchor is)."""
        gio_anim.pose_at(rig, gio_action, frame, broom, anchor)
        for o in cup:
            o.hide_render = broken
        for o in shards:
            o.hide_render = not broken
        sc.frame_set(200 if broken else 1)  # shards rest at the end of cup_fall_break
        if tutu_mode == "desk":
            tutu_root.matrix_world = Matrix.LocRotScale(Vector((0.42, 0.44, DESK_TOP)),
                                                        Euler((0, 0, math.radians(20))), (build_tutu.SCALE,) * 3)
        else:
            bpy.context.view_layer.update()
            loc, rot, _ = anchor.matrix_world.decompose()
            tutu_root.matrix_world = Matrix.LocRotScale(loc, rot, (build_tutu.SCALE,) * 3)
        build_tutu.pose(tutu_rig, "sit_bored", 0.15)
        chair_obj.rotation_euler.z = math.pi if chair_turned else 0.0
        bpy.context.view_layer.update()

    setup("gio_typing_loop", 1, "desk", False)
    save_blend("desk_scene.blend")

    cam_d = bpy.data.cameras.new("cam")
    cam_d.lens = 32
    cam = bpy.data.objects.new("preview_cam", cam_d)
    sc.collection.objects.link(cam)
    sc.camera = cam
    sc.render.resolution_x, sc.render.resolution_y = 1600, 900
    shots = [
        ("scene1_desk", ("gio_typing_loop", 1, "desk", False), (1.15, -1.55, 1.45), (0.0, 0.35, 0.92)),
        ("scene1_mouse", ("gio_mouse_loop", 13, "desk", False), (0.6, -1.0, 1.3), (-0.05, 0.2, 0.85)),
        ("scene_wide", ("gio_typing_loop", 1, "desk", False), (0.2, -2.6, 1.6), (0.0, 0.3, 0.9)),
        ("scene_cup_closeup", ("gio_typing_loop", 1, "desk", False), (0.75, -0.2, 0.98), (0.4, 0.33, 0.8)),
        ("scene5_broom", ("gio_broom_enter", 60, "anchor", True), (0.35, -1.55, 0.2), (0.8, -0.45, 0.25)),
        ("scene5_crouch", ("gio_crouch_pick_cat", 36, "anchor", True), (0.25, -1.5, 0.5), (0.8, -0.45, 0.3)),
        ("scene6_lift", ("gio_crouch_pick_cat", 64, "anchor", True), (0.2, -1.7, 0.9), (0.85, -0.45, 0.65)),
        ("scene6_lap", ("gio_sit_with_cat", 64, "anchor", True, True), (-0.22, -1.55, 1.1), (-0.22, -0.22, 0.95)),
    ]
    # `-- --shots a,b` renders only those previews (each one takes a few minutes)
    if "--shots" in sys.argv:
        keep = sys.argv[sys.argv.index("--shots") + 1].split(",")
        shots = [s for s in shots if s[0] in keep]
    for name, args, loc, target in shots:
        setup(*args)
        cam.location = loc
        cam.rotation_euler = (Vector(target) - Vector(loc)).to_track_quat("-Z", "Y").to_euler()
        # soft key from the camera side for the floor and lap shots, which the desk lamp does not reach
        fill_d.energy = 0 if name.startswith("scene1") or name.startswith("scene_") else 60
        fill.location = Vector(loc) + Vector((0.3, 0, 0.5))
        fill.rotation_euler = (Vector(target) - fill.location).to_track_quat("-Z", "Y").to_euler()
        sc.render.filepath = os.path.join(PREVIEW_DIR, f"{name}.png")
        bpy.ops.render.render(write_still=True)
