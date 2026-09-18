import math
import os
import struct
import zlib
import binascii
import unreal

PREFIX = "PZ_"
ROOT = "POLOP_PREVIZ"
HM_SIZE = 1009
WORLD_X_MIN_M, WORLD_X_MAX_M = 0.0, 2016.0
WORLD_Y_MIN_M, WORLD_Y_MAX_M = -1008.0, 1008.0
GUIDE_Z_OFFSET_CM = 45.0
GUIDE_WIDTH_CM = 150.0
GUIDE_THICKNESS_CM = 16.0

actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
asset_tools = unreal.AssetToolsHelpers.get_asset_tools()

CUBE = unreal.load_asset("/Engine/BasicShapes/Cube.Cube")
SPHERE = unreal.load_asset("/Engine/BasicShapes/Sphere.Sphere")

PATH_A = [
    (0.0, 0.0, 0.0), (300.0, -50.0, 20.0), (650.0, -80.0, 45.0),
    (900.0, 0.0, 70.0), (1250.0, -120.0, 100.0),
    (1550.0, -90.0, 135.0), (1760.0, 0.0, 158.0),
]
PATH_B = [
    (1760.0, 0.0, 158.0), (1600.0, 350.0, 140.0),
    (1300.0, 600.0, 115.0), (1050.0, 450.0, 90.0),
    (900.0, 25.0, 70.0),
]
PATH_UP = [
    (1760.0, 0.0, 158.0), (1880.0, -50.0, 172.0),
    (2010.0, -90.0, 188.0),
]
PATH_CAVE = [
    (1760.0, 0.0, 158.0), (1780.0, 65.0, 158.5),
    (1830.0, 90.0, 160.5),
]
PATH_FLANK = [
    (900.0, 25.0, 70.0), (860.0, 65.0, 66.0),
    (810.0, 85.0, 62.0), (780.0, 50.0, 59.0),
    (820.0, 12.0, 63.0), (900.0, 0.0, 70.0),
]
A_BRIDGE = (900.0, 0.0, 70.0)
B_BRIDGE = (900.0, 25.0, 70.0)

def V(x, y, z):
    return unreal.Vector(float(x), float(y), float(z))

def clamp(v, lo, hi):
    return max(lo, min(hi, v))

def smoothstep(t):
    t = clamp(t, 0.0, 1.0)
    return t*t*(3.0-2.0*t)

def gaussian(x, y, cx, cy, sx, sy, amp):
    dx, dy = (x-cx)/sx, (y-cy)/sy
    return amp * math.exp(-(dx*dx + dy*dy))

def nearest_segment(px, py, a, b):
    ax, ay, az = a
    bx, by, bz = b
    vx, vy = bx-ax, by-ay
    vv = vx*vx + vy*vy
    t = 0.0 if vv <= 1e-9 else clamp(((px-ax)*vx + (py-ay)*vy)/vv, 0.0, 1.0)
    nx, ny = ax+vx*t, ay+vy*t
    nz = az+(bz-az)*t
    return math.hypot(px-nx, py-ny), nz

def nearest_path(px, py, path):
    best_d, best_z = 1e30, 0.0
    for i in range(len(path)-1):
        d, z = nearest_segment(px, py, path[i], path[i+1])
        if d < best_d:
            best_d, best_z = d, z
    return best_d, best_z

def blend_to_path(h, x, y, path, half_width, shoulder):
    d, target = nearest_path(x, y, path)
    outer = half_width + shoulder
    if d >= outer:
        return h
    w = 1.0 if d <= half_width else smoothstep((outer-d)/shoulder)
    return h*(1.0-w) + target*w

def base_height_m(x, y):
    h = 4.0 + 0.047*x
    h += gaussian(x, y, 1180, 170, 330, 175, 42)
    h += gaussian(x, y, 1470, 155, 300, 175, 55)
    h += gaussian(x, y, 1690, 100, 220, 150, 44)
    h += gaussian(x, y, 1250, -260, 430, 300, 18)
    h += gaussian(x, y, 1300, 520, 440, 300, 16)
    h += gaussian(x, y, 1800, 20, 250, 210, 22)
    h -= gaussian(x, y, 900, 12.5, 90, 9, 31)
    h -= gaussian(x, y, 825, 48, 135, 85, 8)
    h -= gaussian(x, y, 1820, 88, 90, 75, 6)
    h += 1.5*math.sin(x/91.0)*math.cos(y/121.0)
    h += 0.7*math.sin((x+y)/53.0)
    return h

def terrain_height_m(x, y):
    h = base_height_m(x, y)
    h = blend_to_path(h, x, y, PATH_A, 2.5, 22.0)
    h = blend_to_path(h, x, y, PATH_B, 2.2, 20.0)
    h = blend_to_path(h, x, y, PATH_UP, 2.4, 18.0)
    h = blend_to_path(h, x, y, PATH_CAVE, 2.0, 15.0)
    h = blend_to_path(h, x, y, PATH_FLANK, 1.8, 14.0)

    d = math.hypot(x-1760.0, y)
    if d < 18.0:
        w = 1.0-smoothstep(d/18.0)
        h = h*(1.0-w)+158.0*w

    d = math.hypot(x-1810.0, y-78.0)
    if d < 22.0:
        w = 1.0-smoothstep(d/22.0)
        h = h*(1.0-w)+160.0*w

    return clamp(h, 0.0, 225.0)

def height_to_u16(h):
    return max(0, min(65535, int(round(32768.0 + (h/256.0)*32768.0))))

def png_chunk(kind, payload):
    return (
        struct.pack(">I", len(payload)) + kind + payload
        + struct.pack(">I", binascii.crc32(kind+payload) & 0xffffffff)
    )

def write_heightmap(filepath):
    unreal.log("POLOP V08 : génération du heightmap 1009x1009...")
    raw = bytearray()

    for py in range(HM_SIZE):
        y = WORLD_Y_MIN_M + (py/float(HM_SIZE-1))*(WORLD_Y_MAX_M-WORLD_Y_MIN_M)
        raw.append(0)
        for px in range(HM_SIZE):
            x = WORLD_X_MIN_M + (px/float(HM_SIZE-1))*(WORLD_X_MAX_M-WORLD_X_MIN_M)
            raw.extend(struct.pack(">H", height_to_u16(terrain_height_m(x, y))))

    ihdr = struct.pack(">IIBBBBB", HM_SIZE, HM_SIZE, 16, 0, 0, 0, 0)
    data = bytearray(b"\x89PNG\r\n\x1a\n")
    data.extend(png_chunk(b"IHDR", ihdr))
    data.extend(png_chunk(b"IDAT", zlib.compress(bytes(raw), 9)))
    data.extend(png_chunk(b"IEND", b""))

    with open(filepath, "wb") as f:
        f.write(data)

saved_dir = unreal.Paths.convert_relative_path_to_full(unreal.Paths.project_saved_dir())
out_dir = os.path.join(saved_dir, "POLOP", "V08")
os.makedirs(out_dir, exist_ok=True)

heightmap_path = os.path.join(out_dir, "polop_v08_heightmap_1009.png")
instructions_path = os.path.join(out_dir, "IMPORT_V08.txt")

write_heightmap(heightmap_path)

with open(instructions_path, "w", encoding="utf-8") as f:
    f.write(
        "POLOP V08\n\n"
        "Supprimer le Landscape V07 puis importer :\n%s\n\n"
        "Location X=100800 Y=0 Z=0\n"
        "Rotation 0/0/0\n"
        "Scale X=200 Y=200 Z=100\n"
        "Flip Y Axis OFF\n"
        "Resolution 1009x1009\n" % heightmap_path
    )

old = []
for actor in actors.get_all_level_actors():
    try:
        if actor.get_actor_label().startswith(PREFIX):
            old.append(actor)
    except Exception:
        pass
if old:
    actors.destroy_actors(old)

def ensure_material(name, rgb):
    folder = "/Game/POLOP/Previz/Materials"
    unreal.EditorAssetLibrary.make_directory(folder)
    path = folder + "/" + name

    if unreal.EditorAssetLibrary.does_asset_exist(path):
        return unreal.load_asset(path)

    mat = asset_tools.create_asset(name, folder, unreal.Material, unreal.MaterialFactoryNew())
    expr = unreal.MaterialEditingLibrary.create_material_expression(
        mat, unreal.MaterialExpressionConstant3Vector, -300, 0
    )
    expr.set_editor_property(
        "constant", unreal.LinearColor(rgb[0], rgb[1], rgb[2], 1.0)
    )
    unreal.MaterialEditingLibrary.connect_material_property(
        expr, "", unreal.MaterialProperty.MP_BASE_COLOR
    )
    unreal.MaterialEditingLibrary.recompile_material(mat)
    unreal.EditorAssetLibrary.save_loaded_asset(mat)
    return mat

MAT_A = ensure_material("M_V08_GUIDE_A", (0.05, 0.35, 1.0))
MAT_B = ensure_material("M_V08_GUIDE_B", (1.0, 0.18, 0.04))
MAT_UP = ensure_material("M_V08_GUIDE_UP", (0.5, 0.18, 0.95))
MAT_CAVE = ensure_material("M_V08_GUIDE_CAVE", (0.85, 0.85, 0.85))
MAT_FLANK = ensure_material("M_V08_GUIDE_FLANK", (0.05, 0.78, 0.15))
MAT_BRIDGE = ensure_material("M_V08_GUIDE_BRIDGE", (1.0, 0.72, 0.02))
MAT_MARKER = ensure_material("M_V08_MARKER", (1.0, 1.0, 0.04))

def label_actor(actor, name, folder_name):
    actor.set_actor_label(PREFIX + name, True)
    try:
        actor.set_folder_path(unreal.Name(ROOT + "/" + folder_name))
    except Exception:
        pass

def apply_material(actor, material):
    try:
        comp = actor.get_component_by_class(unreal.StaticMeshComponent)
        if comp:
            comp.set_material(0, material)
    except Exception:
        pass

def world_point(p):
    x, y, _ = p
    return V(x*100.0, y*100.0, terrain_height_m(x, y)*100.0 + GUIDE_Z_OFFSET_CM)

def dist3(a, b):
    return math.sqrt((b.x-a.x)**2+(b.y-a.y)**2+(b.z-a.z)**2)

def mid(a, b):
    return V((a.x+b.x)/2, (a.y+b.y)/2, (a.z+b.z)/2)

def guide(name, path, material, folder, width=GUIDE_WIDTH_CM):
    pts = [world_point(p) for p in path]
    for i in range(len(pts)-1):
        a, b = pts[i], pts[i+1]
        actor = actors.spawn_actor_from_object(
            CUBE, mid(a, b), unreal.MathLibrary.find_look_at_rotation(a, b), False
        )
        label_actor(actor, "GUIDE_%s_%02d" % (name, i+1), folder)
        actor.set_actor_scale3d(
            V(dist3(a, b)*1.01/100.0, width/100.0, GUIDE_THICKNESS_CM/100.0)
        )
        apply_material(actor, material)

guide("A", PATH_A, MAT_A, "Guides/A")
guide("B", PATH_B, MAT_B, "Guides/B")
guide("HAUT", PATH_UP, MAT_UP, "Guides/Chemin_haut")
guide("GROTTE", PATH_CAVE, MAT_CAVE, "Guides/Acces_grotte", 130.0)
guide("FLANC", PATH_FLANK, MAT_FLANK, "Guides/Flanc", 130.0)
guide("PONT", [A_BRIDGE, B_BRIDGE], MAT_BRIDGE, "Guides/Pont", 105.0)

def marker(name, x, y):
    z = terrain_height_m(x, y)*100.0 + 150.0
    actor = actors.spawn_actor_from_object(SPHERE, V(x*100.0, y*100.0, z), unreal.Rotator(), False)
    label_actor(actor, name, "Reperes")
    actor.set_actor_scale3d(V(1.5, 1.5, 1.5))
    apply_material(actor, MAT_MARKER)

marker("REPERE_CONVERGENCE_17H00", 0.0, 0.0)
marker("REPERE_JONCTION_HAUTE", 1760.0, 0.0)

def target(x, y, extra=0.0):
    return V(x*100.0, y*100.0, terrain_height_m(x, y)*100.0 + extra)

def camera(name, pos, look, focal):
    cam = actors.spawn_actor_from_class(unreal.CineCameraActor, pos, unreal.Rotator(), False)
    label_actor(cam, "CAM_REVIEW_" + name, "Cameras/Review_V08")
    cam.set_actor_rotation(unreal.MathLibrary.find_look_at_rotation(pos, look), False)
    cam.get_cine_camera_component().set_current_focal_length(float(focal))
    return cam

cam_01 = camera(
    "01_TOP_MAP",
    V(100800.0, 0.0, 520000.0),
    V(100800.0, 0.0, 9000.0),
    50.0
)
camera(
    "02_SIDE_PROFILE",
    V(100800.0, -145000.0, 33000.0),
    target(1100.0, 0.0, 2500.0),
    50.0
)
camera(
    "03_BRIDGE_A",
    V(76000.0, -19000.0, terrain_height_m(760.0, -190.0)*100.0 + 12000.0),
    target(855.0, 35.0, 900.0),
    42.0
)
camera(
    "04_BRIDGE_B",
    V(102000.0, 23000.0, terrain_height_m(1020.0, 230.0)*100.0 + 12000.0),
    target(855.0, 35.0, 900.0),
    42.0
)
camera(
    "05_HIGH_JUNCTION",
    V(157000.0, -27000.0, terrain_height_m(1570.0, -270.0)*100.0 + 13000.0),
    target(1770.0, 25.0, 1200.0),
    45.0
)
camera(
    "06_CAVE_ACCESS",
    V(170000.0, -9000.0, terrain_height_m(1700.0, -90.0)*100.0 + 4500.0),
    target(1810.0, 78.0, 800.0),
    45.0
)
camera(
    "07_HUMAN_A",
    V(62000.0, -8000.0, terrain_height_m(620.0, -80.0)*100.0 + 175.0),
    target(720.0, -50.0, 165.0),
    35.0
)
camera(
    "08_HUMAN_B",
    V(131000.0, 59500.0, terrain_height_m(1310.0, 595.0)*100.0 + 175.0),
    target(1190.0, 520.0, 165.0),
    35.0
)

actors.set_selected_level_actors([cam_01])

unreal.log("============================================================")
unreal.log("POLOP PREVIZ V08 PREPAREE")
unreal.log("Heightmap : " + heightmap_path)
unreal.log("IMPORT : X=100800 Y=0 Z=0 | Scale 200/200/100 | Flip Y OFF")
unreal.log("============================================================")
