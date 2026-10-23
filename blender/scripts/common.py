"""Shared helpers for the portfolio Blender build scripts.

Run any build script headless:
  blender -b --factory-startup -P blender/scripts/build_<name>.py
"""
import math
import os

import bmesh
import bpy
from mathutils import Vector

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
BLENDER_DIR = os.path.join(ROOT, "blender")
TEX_DIR = os.path.join(BLENDER_DIR, "textures")
PREVIEW_DIR = os.path.join(BLENDER_DIR, "previews")
MODELS_DIR = os.path.join(ROOT, "public", "models")
FONTS = "C:/Windows/Fonts"

# Design system + character sheet palette
PALETTE = {
    "night": "#1C1B2E",
    "surface": "#2A2944",
    "lamp": "#F4B860",
    "coffee": "#6B4A3A",
    "cream": "#F6EFE6",
    "eyes": "#9FD3F0",
    "blush": "#F2A7A0",
    # Tutu
    "fur_white": "#FBF8F3",
    "fur_saddle": "#B88A62",
    "fur_head": "#8A6248",
    "fur_points": "#3A241B",
    "fur_muzzle": "#2E1C16",
    "ear_inner": "#E9B7AE",
    # Gio
    "skin": "#F1CDB4",
    "hair": "#8C6A4F",
    "hair_light": "#A9835F",
    "shirt": "#1E1E22",
    "jeans": "#4F6E9A",
    "shoe": "#1B1B1F",
    "sole": "#F6EFE6",
    "piercing": "#B9BCC8",
}


def srgb_to_linear(c):
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


def hex_rgba(h, alpha=1.0):
    h = PALETTE.get(h, h).lstrip("#")
    return tuple(srgb_to_linear(int(h[i:i + 2], 16) / 255) for i in (0, 2, 4)) + (alpha,)


def reset_scene():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    scene = bpy.context.scene
    scene.unit_settings.system = "METRIC"
    scene.unit_settings.scale_length = 1.0
    return scene


def material(name, color, rough=0.6, metal=0.0, emit=None, emit_strength=0.0, image=None, alpha=None):
    """Principled material. `image` (path) drives base color, or emission when emit == 'image'."""
    mat = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    mat.use_nodes = True
    nt = mat.node_tree
    bsdf = nt.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = hex_rgba(color) if isinstance(color, str) else color
    bsdf.inputs["Roughness"].default_value = rough
    bsdf.inputs["Metallic"].default_value = metal
    if image:
        tex = nt.nodes.new("ShaderNodeTexImage")
        tex.image = bpy.data.images.load(image, check_existing=True)
        target = "Emission Color" if emit == "image" else "Base Color"
        nt.links.new(tex.outputs["Color"], bsdf.inputs[target])
        if emit == "image":
            bsdf.inputs["Base Color"].default_value = (0, 0, 0, 1)
    if emit and emit != "image":
        bsdf.inputs["Emission Color"].default_value = hex_rgba(emit)
    if emit_strength:
        bsdf.inputs["Emission Strength"].default_value = emit_strength
    if alpha is not None:
        bsdf.inputs["Alpha"].default_value = alpha
        mat.surface_render_method = "BLENDED"
    return mat


def vcol_material(name, rough=0.6):
    """Material whose base color comes from the 'Col' color attribute (exported to glTF as COLOR_0)."""
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    nt = mat.node_tree
    bsdf = nt.nodes.get("Principled BSDF")
    attr = nt.nodes.new("ShaderNodeVertexColor")
    attr.layer_name = "Col"
    nt.links.new(attr.outputs["Color"], bsdf.inputs["Base Color"])
    bsdf.inputs["Roughness"].default_value = rough
    return mat


def assign(obj, mat):
    obj.data.materials.clear()
    obj.data.materials.append(mat)
    return obj


def collection(name):
    col = bpy.data.collections.get(name) or bpy.data.collections.new(name)
    if col.name not in bpy.context.scene.collection.children:
        bpy.context.scene.collection.children.link(col)
    return col


def link(obj, col):
    for c in list(obj.users_collection):
        c.objects.unlink(obj)
    col.objects.link(obj)
    return obj


def active(obj):
    bpy.ops.object.select_all(action="DESELECT")
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    return obj


def apply_all(obj):
    active(obj)
    bpy.ops.object.convert(target="MESH")
    return obj


def smooth(obj, angle=None):
    active(obj)
    if angle is None:
        bpy.ops.object.shade_smooth()
    else:
        bpy.ops.object.shade_auto_smooth(angle=math.radians(angle))
    return obj


def rounded_box(name, size, bevel=0.01, segments=4, loc=(0, 0, 0), rot=(0, 0, 0), mat=None):
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc, rotation=rot)
    o = bpy.context.object
    o.name = name
    o.scale = size
    bpy.ops.object.transform_apply(scale=True)
    m = o.modifiers.new("bevel", "BEVEL")
    m.width = bevel
    m.segments = segments
    m.limit_method = "NONE"
    apply_all(o)
    smooth(o, 40)
    if mat:
        assign(o, mat)
    return o


def cylinder(name, r, depth, loc=(0, 0, 0), rot=(0, 0, 0), verts=32, bevel=0.0, mat=None, segments=3):
    bpy.ops.mesh.primitive_cylinder_add(radius=r, depth=depth, vertices=verts, location=loc, rotation=rot)
    o = bpy.context.object
    o.name = name
    if bevel:
        m = o.modifiers.new("bevel", "BEVEL")
        m.width = bevel
        m.segments = segments
        m.limit_method = "ANGLE"
        apply_all(o)
    smooth(o, 40)
    if mat:
        assign(o, mat)
    return o


def sphere(name, r, loc=(0, 0, 0), scale=(1, 1, 1), rot=(0, 0, 0), seg=32, rings=16, mat=None):
    bpy.ops.mesh.primitive_uv_sphere_add(radius=r, segments=seg, ring_count=rings, location=loc, rotation=rot)
    o = bpy.context.object
    o.name = name
    o.scale = scale
    bpy.ops.object.transform_apply(scale=True)
    smooth(o)
    if mat:
        assign(o, mat)
    return o


def tube(name, points, radius, mat=None, bevel_res=6, resolution=8, radii=None, cap=True):
    """Curve tube through `points` (list of xyz), optional per-point radius multipliers."""
    cu = bpy.data.curves.new(name, "CURVE")
    cu.dimensions = "3D"
    cu.bevel_depth = radius
    cu.bevel_resolution = bevel_res
    cu.resolution_u = resolution
    cu.use_fill_caps = cap
    sp = cu.splines.new("NURBS")
    sp.points.add(len(points) - 1)
    for i, p in enumerate(points):
        sp.points[i].co = (*p, 1)
        if radii:
            sp.points[i].radius = radii[i]
    sp.use_endpoint_u = True
    sp.order_u = min(4, len(points))
    o = bpy.data.objects.new(name, cu)
    bpy.context.scene.collection.objects.link(o)
    apply_all(o)
    smooth(o)
    if mat:
        assign(o, mat)
    return o


def metaball_mesh(name, elements, resolution=0.02, threshold=0.6, voxel=None, smooth_iters=0):
    """elements: list of dicts {co, radius, type('BALL'|'ELLIPSOID'|'CAPSULE'), size(xyz), rot(quat or euler), stiffness}."""
    mb = bpy.data.metaballs.new(name)
    mb.resolution = resolution
    mb.render_resolution = resolution
    mb.threshold = threshold
    for e in elements:
        el = mb.elements.new(type=e.get("type", "BALL"))
        el.co = e["co"]
        el.radius = e["radius"]
        el.stiffness = e.get("stiffness", 2.0)
        if "size" in e:
            el.size_x, el.size_y, el.size_z = e["size"]
        if "rot" in e:
            from mathutils import Euler
            el.rotation = Euler(e["rot"]).to_quaternion()
        if e.get("negative"):
            el.use_negative = True
    o = bpy.data.objects.new(name, mb)
    bpy.context.scene.collection.objects.link(o)
    bpy.context.view_layer.update()
    apply_all(o)
    o = bpy.context.object
    o.name = name
    if voxel:
        m = o.modifiers.new("remesh", "REMESH")
        m.mode = "VOXEL"
        m.voxel_size = voxel
        apply_all(o)
    if smooth_iters:
        m = o.modifiers.new("smooth", "CORRECTIVE_SMOOTH")
        m.iterations = smooth_iters
        m.use_only_smooth = True
        m.smooth_type = "LENGTH_WEIGHTED"
        apply_all(o)
    smooth(o)
    return o


def decimate(obj, ratio):
    m = obj.modifiers.new("decimate", "DECIMATE")
    m.ratio = ratio
    apply_all(obj)
    smooth(obj)
    return obj


def paint_vertex_colors(obj, fn):
    """fn(co: Vector, normal: Vector) -> hex or rgba. Writes a 'Col' corner color attribute."""
    me = obj.data
    attr = me.color_attributes.get("Col") or me.color_attributes.new("Col", "BYTE_COLOR", "CORNER")
    mw = obj.matrix_world
    for poly in me.polygons:
        for li in poly.loop_indices:
            v = me.vertices[me.loops[li].vertex_index]
            c = fn(mw @ v.co, (mw.to_3x3() @ v.normal).normalized())
            attr.data[li].color = hex_rgba(c) if isinstance(c, str) else c
    me.color_attributes.active_color = attr
    return obj


def parent_keep(child, parent):
    bpy.context.view_layer.update()
    child.parent = parent
    child.matrix_parent_inverse = parent.matrix_world.inverted()
    return child


def join(objs, name):
    active(objs[0])
    for o in objs[1:]:
        o.select_set(True)
    bpy.ops.object.join()
    o = bpy.context.object
    o.name = name
    return o


def text_image(path, lines, size=(1024, 512), font="arialbd.ttf", fg="#111111", bg="#FFFFFF",
               line_height=1.0, scale=1.0, align="CENTER", bg_alpha=1.0, offset=(0, 0), colors=None):
    """Render text lines to a PNG using a throwaway scene with an orthographic camera."""
    prev = bpy.context.window.scene if bpy.context.window else bpy.context.scene
    sc = bpy.data.scenes.new("text_tmp")
    if bpy.context.window:
        bpy.context.window.scene = sc
    w, h = size
    aspect = w / h
    fnt = bpy.data.fonts.load(os.path.join(FONTS, font), check_existing=True)
    n = len(lines)
    for i, line in enumerate(lines):
        cu = bpy.data.curves.new(f"t{i}", "FONT")
        cu.body = line
        cu.font = fnt
        cu.align_x = align
        cu.align_y = "CENTER"
        cu.size = scale
        o = bpy.data.objects.new(f"t{i}", cu)
        y = ((n - 1) / 2 - i) * line_height * scale + offset[1]
        x = offset[0] if align == "CENTER" else -aspect + 0.05 + offset[0]
        o.location = (x, y, 0)
        sc.collection.objects.link(o)
        col = colors[i] if colors else fg
        mat = bpy.data.materials.new(f"tm{i}")
        mat.use_nodes = True
        nt = mat.node_tree
        nt.nodes.clear()
        out = nt.nodes.new("ShaderNodeOutputMaterial")
        em = nt.nodes.new("ShaderNodeEmission")
        em.inputs["Color"].default_value = hex_rgba(col)
        nt.links.new(em.outputs[0], out.inputs[0])
        cu.materials.append(mat)
    cam_data = bpy.data.cameras.new("tc")
    cam_data.type = "ORTHO"
    cam_data.ortho_scale = 2 * aspect if aspect >= 1 else 2
    cam = bpy.data.objects.new("tc", cam_data)
    cam.location = (0, 0, 5)
    sc.collection.objects.link(cam)
    sc.camera = cam
    world = bpy.data.worlds.new("tw")
    world.use_nodes = True
    world.node_tree.nodes["Background"].inputs[0].default_value = hex_rgba(bg)
    sc.world = world
    sc.render.engine = "BLENDER_EEVEE"
    sc.render.resolution_x, sc.render.resolution_y = w, h
    sc.render.film_transparent = bg_alpha < 1
    sc.view_settings.view_transform = "Standard"
    sc.render.image_settings.file_format = "PNG"
    sc.render.image_settings.color_mode = "RGBA" if bg_alpha < 1 else "RGB"
    sc.render.filepath = path
    bpy.ops.render.render(write_still=True, scene=sc.name)
    if bpy.context.window:
        bpy.context.window.scene = prev
    bpy.data.scenes.remove(sc)
    return path


def export_glb(path, objects=None, animations=False):
    bpy.ops.object.select_all(action="DESELECT")
    if objects:
        for o in objects:
            o.select_set(True)
    bpy.ops.export_scene.gltf(
        filepath=path,
        export_format="GLB",
        use_selection=bool(objects),
        export_apply=True,
        export_yup=True,
        export_draco_mesh_compression_enable=True,
        export_draco_mesh_compression_level=6,
        export_animations=animations,
        # one glTF animation per NLA track, named after the track (e.g. tutu_slap)
        export_animation_mode="NLA_TRACKS",
        # keep constant channels: a clip must fully define props like the broom (scale 1 vs hidden at rest)
        export_optimize_animation_size=False,
        export_optimize_animation_keep_anim_object=True,
        export_cameras=False,
        export_lights=False,
        export_image_format="WEBP",
    )


def save_blend(name):
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(BLENDER_DIR, name))


# ---------- preview rendering ----------

def studio(scene, bg="#EFE7DD", key=450, fill=140, target=(0, 0, 0.5), dist=3.0):
    world = bpy.data.worlds.new("studio")
    world.use_nodes = True
    world.node_tree.nodes["Background"].inputs[0].default_value = hex_rgba(bg)
    world.node_tree.nodes["Background"].inputs[1].default_value = 0.45
    scene.world = world
    t = Vector(target)
    for name, off, energy, size in (("key", (-1.2, -1.6, 1.6), key, 2.0), ("fill", (1.6, -1.0, 0.6), fill, 3.0),
                                    ("rim", (0.5, 2.0, 1.8), key * 0.8, 1.5)):
        ld = bpy.data.lights.new(name, "AREA")
        ld.energy = energy * (dist / 3) ** 2
        ld.size = size * dist / 3
        lo = bpy.data.objects.new(name, ld)
        lo.location = t + Vector(off) * dist / 2
        lo.rotation_euler = (t - lo.location).to_track_quat("-Z", "Y").to_euler()
        scene.collection.objects.link(lo)
    scene.render.engine = "BLENDER_EEVEE"
    scene.eevee.use_shadows = True
    # matches three.js NeutralToneMapping, keeps palette hues true
    scene.view_settings.view_transform = "Khronos PBR Neutral"
    scene.view_settings.exposure = -0.6


def render_views(scene, prefix, target, dist, height=0.0, lens=60, views=("front", "side", "back"), res=(900, 1100),
                 extra=None):
    cam_data = bpy.data.cameras.new("preview_cam")
    cam_data.lens = lens
    cam = bpy.data.objects.new("preview_cam", cam_data)
    scene.collection.objects.link(cam)
    scene.camera = cam
    scene.render.resolution_x, scene.render.resolution_y = res
    angles = {"front": -90, "three_quarter": -55, "side": 0, "back": 90}
    t = Vector(target)
    outs = []
    shots = [(v, angles[v], height) for v in views] + (extra or [])
    for view, ang, h in shots:
        a = math.radians(ang)
        cam.location = t + Vector((math.cos(a) * dist, math.sin(a) * dist, h))
        cam.rotation_euler = (t - cam.location).to_track_quat("-Z", "Y").to_euler()
        p = os.path.join(PREVIEW_DIR, f"{prefix}_{view}.png")
        scene.render.filepath = p
        bpy.ops.render.render(write_still=True)
        outs.append(p)
    bpy.data.objects.remove(cam)
    return outs
