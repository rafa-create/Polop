import math
import os
import json
import struct
import zlib
import binascii
from array import array
import unreal

# =============================================================================
# LA BOUCLE / POLOP — PREVIZ COMPLETE V11
# RAVIN ETROIT + FLANC PRESERVE + CAMERAS HUMAINES CORRIGEES
# Unreal Engine 5.8 — 1 uu = 1 cm
#
# V08 est validée techniquement. V11 NE CHANGE PAS la topologie :
# - A monte depuis la convergence jusqu'à la jonction haute ;
# - B descend depuis la jonction haute ;
# - pont court A <-> B ;
# - flanc long B -> A ;
# - chemin qui continue à monter ;
# - grotte = poche latérale à accès unique.
#
# V11 améliore uniquement la forme :
# - courbes Hermite continues à la place des cassures polygonales ;
# - flanc transformé en vrai détour arrondi ;
# - banquettes de sentier sculptées autour des courbes ;
# - pont blockout avec tablier, garde-corps et pile ;
# - grotte blockout locale ;
# - proxies humains ;
# - 9 caméras créées de façon robuste.
#
# Après exécution :
#   Saved/POLOP/V11/polop_v11_heightmap_1009.png
#   Saved/POLOP/V11/route_model_v11.json
#
# IMPORT DU LANDSCAPE V11 :
#   Supprimer uniquement le Landscape V08.
#   Shift+2 -> Landscape -> Import from File
#   Location UI : X=100800 Y=0 Z=0
#   Scale       : X=200 Y=200 Z=100
#   Flip Y      : OFF
#
# Le script ne supprime que les Actors dont le label commence par PZ_.
# =============================================================================

PREFIX = "PZ_"
ROOT = "POLOP_PREVIZ"

HM_SIZE = 1009
WORLD_X_MIN_M, WORLD_X_MAX_M = 0.0, 2016.0
WORLD_Y_MIN_M, WORLD_Y_MAX_M = -1008.0, 1008.0
GRID_STEP_M = 2.0

GUIDE_Z_OFFSET_CM = 45.0
GUIDE_WIDTH_CM = 135.0
GUIDE_THICKNESS_CM = 14.0
CURVE_STEP_M = 5.0

GROUP_SPEED_KMH = 2.20
INVERSE_SPEED_KMH = 2.82
INVERSE_PAUSE_MIN = 7.0

actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
asset_tools = unreal.AssetToolsHelpers.get_asset_tools()

CUBE = unreal.load_asset("/Engine/BasicShapes/Cube.Cube")
SPHERE = unreal.load_asset("/Engine/BasicShapes/Sphere.Sphere")
CYLINDER = unreal.load_asset("/Engine/BasicShapes/Cylinder.Cylinder")

if not CUBE or not SPHERE or not CYLINDER:
    raise RuntimeError("BasicShapes Unreal introuvables.")


def V(x, y, z):
    return unreal.Vector(float(x), float(y), float(z))


def clamp(v, lo, hi):
    return max(lo, min(hi, v))


def smoothstep(t):
    t = clamp(t, 0.0, 1.0)
    return t * t * (3.0 - 2.0 * t)


def gaussian(x, y, cx, cy, sx, sy, amp):
    dx, dy = (x - cx) / sx, (y - cy) / sy
    return amp * math.exp(-(dx * dx + dy * dy))


A_CTRL = [
    (0.0, 0.0, 0.0),
    (300.0, -50.0, 20.0),
    (650.0, -80.0, 45.0),
    (900.0, 0.0, 70.0),
    (1250.0, -120.0, 100.0),
    (1550.0, -90.0, 135.0),
    (1760.0, 0.0, 158.0),
]

B_CTRL = [
    (1760.0, 0.0, 158.0),
    (1600.0, 350.0, 140.0),
    (1300.0, 600.0, 115.0),
    (1050.0, 450.0, 90.0),
    (900.0, 25.0, 70.0),
]

UP_CTRL = [
    (1760.0, 0.0, 158.0),
    (1880.0, -50.0, 172.0),
    (2010.0, -90.0, 188.0),
]

CAVE_CTRL = [
    (1760.0, 0.0, 158.0),
    (1780.0, 65.0, 158.5),
    (1830.0, 90.0, 160.5),
]

FLANK_CTRL = [
    (900.0, 25.0, 70.0),
    (875.0, 52.0, 68.0),
    (842.0, 74.0, 65.0),
    (807.0, 82.0, 62.0),
    (785.0, 68.0, 60.0),
    (780.0, 43.0, 59.0),
    (794.0, 24.0, 60.5),
    (825.0, 11.0, 63.5),
    (860.0, 4.0, 66.5),
    (900.0, 0.0, 70.0),
]

A_BRIDGE = (900.0, 0.0, 70.0)
B_BRIDGE = (900.0, 25.0, 70.0)


def psub(a, b):
    return (a[0]-b[0], a[1]-b[1], a[2]-b[2])


def pscale(a, s):
    return (a[0]*s, a[1]*s, a[2]*s)


def tangent(points, i):
    if i == 0:
        return pscale(psub(points[1], points[0]), 0.50)
    if i == len(points)-1:
        return pscale(psub(points[-1], points[-2]), 0.50)
    return pscale(psub(points[i+1], points[i-1]), 0.50)


def hermite(p0, p1, m0, m1, t):
    t2, t3 = t*t, t*t*t
    h00 = 2*t3 - 3*t2 + 1
    h10 = t3 - 2*t2 + t
    h01 = -2*t3 + 3*t2
    h11 = t3 - t2
    return (
        h00*p0[0] + h10*m0[0] + h01*p1[0] + h11*m1[0],
        h00*p0[1] + h10*m0[1] + h01*p1[1] + h11*m1[1],
        h00*p0[2] + h10*m0[2] + h01*p1[2] + h11*m1[2],
    )


def smooth_route(points, step_m=CURVE_STEP_M):
    out = []
    tangents = [tangent(points, i) for i in range(len(points))]

    for i in range(len(points)-1):
        p0, p1 = points[i], points[i+1]
        m0, m1 = tangents[i], tangents[i+1]
        horizontal = math.hypot(p1[0]-p0[0], p1[1]-p0[1])
        count = max(2, int(math.ceil(horizontal / step_m)))
        first = 0 if i == 0 else 1

        for j in range(first, count+1):
            out.append(hermite(p0, p1, m0, m1, j/float(count)))

    return out


ROUTES = {
    "A": smooth_route(A_CTRL),
    "B": smooth_route(B_CTRL),
    "HAUT": smooth_route(UP_CTRL),
    "GROTTE": smooth_route(CAVE_CTRL),
    "FLANC": smooth_route(FLANK_CTRL),
}


def route_length(route):
    total = 0.0
    for a, b in zip(route, route[1:]):
        total += math.sqrt(
            (b[0]-a[0])**2 +
            (b[1]-a[1])**2 +
            (b[2]-a[2])**2
        )
    return total


def max_grade(route):
    value = 0.0
    for a, b in zip(route, route[1:]):
        horizontal = math.hypot(b[0]-a[0], b[1]-a[1])
        if horizontal > 1e-6:
            value = max(value, abs(b[2]-a[2]) / horizontal * 100.0)
    return value


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
    return clamp(h, 0.0, 225.0)


COUNT = HM_SIZE * HM_SIZE
base = array("f", [0.0]) * COUNT
weights = array("f", [0.0]) * COUNT
targets = array("f", [0.0]) * COUNT

unreal.log("POLOP V11 : calcul du relief de base...")

for iy in range(HM_SIZE):
    y = WORLD_Y_MIN_M + iy * GRID_STEP_M
    row = iy * HM_SIZE

    for ix in range(HM_SIZE):
        x = WORLD_X_MIN_M + ix * GRID_STEP_M
        base[row + ix] = base_height_m(x, y)


def accumulate_route(route, half_width_m, shoulder_m):
    outer = half_width_m + shoulder_m
    radius_px = int(math.ceil(outer / GRID_STEP_M))

    for sx, sy, sz in route:
        cx = int(round((sx - WORLD_X_MIN_M) / GRID_STEP_M))
        cy = int(round((sy - WORLD_Y_MIN_M) / GRID_STEP_M))

        x0 = max(0, cx-radius_px)
        x1 = min(HM_SIZE-1, cx+radius_px)
        y0 = max(0, cy-radius_px)
        y1 = min(HM_SIZE-1, cy+radius_px)

        for iy in range(y0, y1+1):
            wy = WORLD_Y_MIN_M + iy*GRID_STEP_M
            dy = wy - sy

            for ix in range(x0, x1+1):
                wx = WORLD_X_MIN_M + ix*GRID_STEP_M
                d = math.hypot(wx-sx, dy)

                if d >= outer:
                    continue

                if d <= half_width_m:
                    w = 1.0
                else:
                    w = smoothstep((outer-d)/shoulder_m)

                idx = iy*HM_SIZE + ix
                weights[idx] += w
                targets[idx] += w*sz


def accumulate_disc(cx_m, cy_m, z_m, radius_m, shoulder_m):
    outer = radius_m + shoulder_m
    radius_px = int(math.ceil(outer / GRID_STEP_M))
    cx = int(round((cx_m-WORLD_X_MIN_M)/GRID_STEP_M))
    cy = int(round((cy_m-WORLD_Y_MIN_M)/GRID_STEP_M))

    for iy in range(max(0,cy-radius_px), min(HM_SIZE-1,cy+radius_px)+1):
        wy = WORLD_Y_MIN_M + iy*GRID_STEP_M

        for ix in range(max(0,cx-radius_px), min(HM_SIZE-1,cx+radius_px)+1):
            wx = WORLD_X_MIN_M + ix*GRID_STEP_M
            d = math.hypot(wx-cx_m, wy-cy_m)

            if d >= outer:
                continue

            w = 1.0 if d <= radius_m else smoothstep((outer-d)/shoulder_m)
            idx = iy*HM_SIZE + ix
            weights[idx] += 2.0*w
            targets[idx] += 2.0*w*z_m


unreal.log("POLOP V11 : sculpture des sentiers courbes...")

accumulate_route(ROUTES["A"], 2.5, 22.0)
accumulate_route(ROUTES["B"], 2.2, 20.0)
accumulate_route(ROUTES["HAUT"], 2.4, 18.0)
accumulate_route(ROUTES["GROTTE"], 2.0, 15.0)
accumulate_route(ROUTES["FLANC"], 1.8, 14.0)

accumulate_disc(1760.0, 0.0, 158.0, 8.0, 10.0)
accumulate_disc(1810.0, 78.0, 160.0, 10.0, 12.0)

height_grid = array("f", [0.0]) * COUNT

for i in range(COUNT):
    if weights[i] > 1e-8:
        target = targets[i] / weights[i]
        w = min(1.0, weights[i])
        height_grid[i] = base[i]*(1.0-w) + target*w
    else:
        height_grid[i] = base[i]


# =============================================================================
# V11 — POST-PROCESS CIBLE
# =============================================================================
RAVINE_DEPTH_M = 9.0
RAVINE_SIGMA_X_M = 28.0

for iy in range(HM_SIZE):
    y = WORLD_Y_MIN_M + iy * GRID_STEP_M
    if y < 0.0 or y > 25.0:
        continue

    u = y / 25.0
    across = math.sin(math.pi * u) ** 4
    if across <= 1e-9:
        continue

    for ix in range(HM_SIZE):
        x = WORLD_X_MIN_M + ix * GRID_STEP_M
        along = math.exp(-((x - 900.0) / RAVINE_SIGMA_X_M) ** 2)
        cut = RAVINE_DEPTH_M * across * along
        if cut > 0.0001:
            idx = iy * HM_SIZE + ix
            height_grid[idx] = max(0.0, height_grid[idx] - cut)

# Terrasse locale sous toute la petite grotte.
CAVE_TERRACE_X = 1839.0
CAVE_TERRACE_Y = 94.5
CAVE_TERRACE_Z = 160.5
CAVE_RADIUS_M = 16.0
CAVE_SHOULDER_M = 12.0

outer = CAVE_RADIUS_M + CAVE_SHOULDER_M
radius_px = int(math.ceil(outer / GRID_STEP_M))
cx = int(round((CAVE_TERRACE_X - WORLD_X_MIN_M) / GRID_STEP_M))
cy = int(round((CAVE_TERRACE_Y - WORLD_Y_MIN_M) / GRID_STEP_M))

for iy in range(max(0, cy-radius_px), min(HM_SIZE-1, cy+radius_px)+1):
    wy = WORLD_Y_MIN_M + iy * GRID_STEP_M
    for ix in range(max(0, cx-radius_px), min(HM_SIZE-1, cx+radius_px)+1):
        wx = WORLD_X_MIN_M + ix * GRID_STEP_M
        d = math.hypot(wx-CAVE_TERRACE_X, wy-CAVE_TERRACE_Y)
        if d >= outer:
            continue
        w = 1.0 if d <= CAVE_RADIUS_M else smoothstep((outer-d)/CAVE_SHOULDER_M)
        idx = iy * HM_SIZE + ix
        height_grid[idx] = height_grid[idx] * (1.0-w) + CAVE_TERRACE_Z * w


def height_to_u16(h):
    return max(0, min(65535, int(round(32768.0 + (h/256.0)*32768.0))))


def png_chunk(kind, payload):
    return (
        struct.pack(">I", len(payload))
        + kind + payload
        + struct.pack(">I", binascii.crc32(kind+payload) & 0xffffffff)
    )


def write_heightmap(path):
    raw = bytearray()

    for iy in range(HM_SIZE):
        raw.append(0)
        row = iy*HM_SIZE
        for ix in range(HM_SIZE):
            raw.extend(struct.pack(">H", height_to_u16(height_grid[row+ix])))

    ihdr = struct.pack(">IIBBBBB", HM_SIZE, HM_SIZE, 16, 0, 0, 0, 0)
    png = bytearray(b"\x89PNG\r\n\x1a\n")
    png.extend(png_chunk(b"IHDR", ihdr))
    png.extend(png_chunk(b"IDAT", zlib.compress(bytes(raw), 9)))
    png.extend(png_chunk(b"IEND", b""))

    with open(path, "wb") as f:
        f.write(png)


def height_at(x_m, y_m):
    fx = clamp((x_m-WORLD_X_MIN_M)/GRID_STEP_M, 0.0, HM_SIZE-1.0)
    fy = clamp((y_m-WORLD_Y_MIN_M)/GRID_STEP_M, 0.0, HM_SIZE-1.0)
    x0, y0 = int(math.floor(fx)), int(math.floor(fy))
    x1, y1 = min(HM_SIZE-1,x0+1), min(HM_SIZE-1,y0+1)
    tx, ty = fx-x0, fy-y0
    z00 = height_grid[y0*HM_SIZE+x0]
    z10 = height_grid[y0*HM_SIZE+x1]
    z01 = height_grid[y1*HM_SIZE+x0]
    z11 = height_grid[y1*HM_SIZE+x1]
    return (z00*(1-tx)+z10*tx)*(1-ty) + (z01*(1-tx)+z11*tx)*ty


saved = unreal.Paths.convert_relative_path_to_full(unreal.Paths.project_saved_dir())
out_dir = os.path.join(saved, "POLOP", "V11")
os.makedirs(out_dir, exist_ok=True)

heightmap_path = os.path.join(out_dir, "polop_v11_heightmap_1009.png")
route_path = os.path.join(out_dir, "route_model_v11.json")
instructions_path = os.path.join(out_dir, "IMPORT_V11.txt")

unreal.log("POLOP V11 : écriture du PNG...")
write_heightmap(heightmap_path)

route_model = {
    "version": "V11",
    "curve_step_m": CURVE_STEP_M,
    "routes": {},
}

for name, route in ROUTES.items():
    route_model["routes"][name] = {
        "controls": {
            "A": A_CTRL, "B": B_CTRL, "HAUT": UP_CTRL,
            "GROTTE": CAVE_CTRL, "FLANC": FLANK_CTRL,
        }[name],
        "samples": route,
        "length_m": route_length(route),
        "max_grade_percent": max_grade(route),
    }

a_low = smooth_route(A_CTRL[:4])
inverse_distance = (
    route_length(ROUTES["GROTTE"])
    + route_length(ROUTES["B"])
    + math.dist(A_BRIDGE, B_BRIDGE)
    + route_length(a_low)
)

route_model["timing"] = {
    "A_length_m": route_length(ROUTES["A"]),
    "A_minutes_at_2_2_kmh": route_length(ROUTES["A"]) / 1000.0 / GROUP_SPEED_KMH * 60.0,
    "inverse_length_m": inverse_distance,
    "inverse_walk_minutes_at_2_82_kmh": inverse_distance / 1000.0 / INVERSE_SPEED_KMH * 60.0,
    "inverse_total_with_7min_pause": inverse_distance / 1000.0 / INVERSE_SPEED_KMH * 60.0 + INVERSE_PAUSE_MIN,
    "flank_length_m": route_length(ROUTES["FLANC"]),
    "bridge_length_m": math.dist(A_BRIDGE, B_BRIDGE),
}

inverse_exact_speed_kmh = (
    route_model["timing"]["inverse_length_m"] / 1000.0
    / ((60.0 - INVERSE_PAUSE_MIN) / 60.0)
)
route_model["timing"]["inverse_speed_kmh_for_exact_60min_with_7min_pause"] = inverse_exact_speed_kmh
route_model["timing"]["inverse_total_at_calibrated_speed_min"] = 60.0

with open(route_path, "w", encoding="utf-8") as f:
    json.dump(route_model, f, indent=2, ensure_ascii=False)

with open(instructions_path, "w", encoding="utf-8") as f:
    f.write(
        "POLOP V11\n\n"
        "Supprimer uniquement le Landscape V08 puis importer :\n%s\n\n"
        "Location UI X=100800 Y=0 Z=0\n"
        "Rotation 0/0/0\n"
        "Scale X=200 Y=200 Z=100\n"
        "Flip Y Axis OFF\n"
        "Resolution 1009x1009\n\n"
        "Puis exécuter previz_polop_validation_v11.py.\n" % heightmap_path
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
    expr.set_editor_property("constant", unreal.LinearColor(rgb[0],rgb[1],rgb[2],1.0))
    unreal.MaterialEditingLibrary.connect_material_property(
        expr, "", unreal.MaterialProperty.MP_BASE_COLOR
    )
    unreal.MaterialEditingLibrary.recompile_material(mat)
    unreal.EditorAssetLibrary.save_loaded_asset(mat)
    return mat


MAT_A = ensure_material("M_V11_A", (0.05,0.35,1.0))
MAT_B = ensure_material("M_V11_B", (1.0,0.18,0.04))
MAT_UP = ensure_material("M_V11_UP", (0.5,0.18,0.95))
MAT_CAVE = ensure_material("M_V11_CAVE_ACCESS", (0.85,0.85,0.85))
MAT_FLANK = ensure_material("M_V11_FLANK", (0.05,0.78,0.15))
MAT_BRIDGE = ensure_material("M_V11_BRIDGE", (0.95,0.68,0.03))
MAT_CAVE_DARK = ensure_material("M_V11_CAVE_DARK", (0.04,0.04,0.05))
MAT_MARKER = ensure_material("M_V11_MARKER", (1.0,1.0,0.03))
MAT_THOMAS = ensure_material("M_V11_THOMAS", (0.08,0.35,1.0))
MAT_INVERSE = ensure_material("M_V11_INVERSE", (1.0,0.12,0.05))
MAT_EVA = ensure_material("M_V11_EVA", (0.75,0.15,0.85))
MAT_LEA = ensure_material("M_V11_LEA", (0.03,0.82,0.68))


def label(actor, name, folder):
    actor.set_actor_label(PREFIX + name, True)
    try:
        actor.set_folder_path(unreal.Name(ROOT + "/" + folder))
    except Exception:
        pass


def apply_material(actor, mat):
    try:
        comp = actor.get_component_by_class(unreal.StaticMeshComponent)
        if comp:
            comp.set_material(0, mat)
    except Exception:
        pass


def spawn_box(name, pos, size_cm, mat, folder, rot=None):
    actor = actors.spawn_actor_from_object(
        CUBE, pos, rot or unreal.Rotator(0,0,0), False
    )
    label(actor, name, folder)
    actor.set_actor_scale3d(V(size_cm[0]/100.0,size_cm[1]/100.0,size_cm[2]/100.0))
    apply_material(actor, mat)
    return actor


def spawn_sphere(name, pos, radius_cm, mat, folder="Reperes"):
    actor = actors.spawn_actor_from_object(SPHERE, pos, unreal.Rotator(0,0,0), False)
    label(actor, name, folder)
    actor.set_actor_scale3d(V(radius_cm/50.0,radius_cm/50.0,radius_cm/50.0))
    apply_material(actor, mat)
    return actor


def spawn_person(name, x_m, y_m, height_cm, mat):
    z_cm = height_at(x_m,y_m)*100.0
    actor = actors.spawn_actor_from_object(
        CYLINDER,
        V(x_m*100.0,y_m*100.0,z_cm+height_cm/2.0),
        unreal.Rotator(0,0,0), False
    )
    label(actor, name, "Personnages_proxy")
    actor.set_actor_scale3d(V(0.34,0.34,height_cm/100.0))
    apply_material(actor, mat)
    return actor


def world_point(p):
    x,y,_ = p
    return V(x*100.0,y*100.0,height_at(x,y)*100.0+GUIDE_Z_OFFSET_CM)


def d3(a,b):
    return math.sqrt((b.x-a.x)**2+(b.y-a.y)**2+(b.z-a.z)**2)


def mid(a,b):
    return V((a.x+b.x)/2,(a.y+b.y)/2,(a.z+b.z)/2)


def guide_curve(name, route, mat, folder, width_cm=GUIDE_WIDTH_CM):
    pts = route[::3]
    if pts[-1] != route[-1]:
        pts.append(route[-1])
    pts = [world_point(p) for p in pts]

    for i,(a,b) in enumerate(zip(pts,pts[1:]), start=1):
        spawn_box(
            "GUIDE_%s_%03d"%(name,i),
            mid(a,b),
            (d3(a,b)*1.02,width_cm,GUIDE_THICKNESS_CM),
            mat,
            folder,
            unreal.MathLibrary.find_look_at_rotation(a,b)
        )


guide_curve("A", ROUTES["A"], MAT_A, "Guides/A")
guide_curve("B", ROUTES["B"], MAT_B, "Guides/B")
guide_curve("HAUT", ROUTES["HAUT"], MAT_UP, "Guides/Chemin_haut")
guide_curve("GROTTE", ROUTES["GROTTE"], MAT_CAVE, "Guides/Acces_grotte", 120.0)
guide_curve("FLANC", ROUTES["FLANC"], MAT_FLANK, "Guides/Flanc", 120.0)


def bridge_blockout():
    ax,ay,az = A_BRIDGE
    bx,by,bz = B_BRIDGE
    a = V(ax*100,ay*100,(height_at(ax,ay)+0.45)*100)
    b = V(bx*100,by*100,(height_at(bx,by)+0.45)*100)
    rotation = unreal.MathLibrary.find_look_at_rotation(a,b)
    length = d3(a,b)
    center = mid(a,b)

    deck_width_cm = 220.0
    spawn_box("PONT_TABLIER", center, (length,deck_width_cm,28.0), MAT_BRIDGE, "Props/Pont", rotation)

    dx,dy = b.x-a.x,b.y-a.y
    horiz = max(1.0, math.hypot(dx,dy))
    nx,ny = -dy/horiz, dx/horiz
    rail_offset = deck_width_cm/2.0 - 12.0

    for side,sign in (("G",1.0),("D",-1.0)):
        rail_center = V(
            center.x + nx*rail_offset*sign,
            center.y + ny*rail_offset*sign,
            center.z + 70.0
        )
        spawn_box(
            "PONT_GARDE_%s"%side,
            rail_center,
            (length,12.0,110.0),
            MAT_BRIDGE,
            "Props/Pont",
            rotation
        )

    ravine_z = height_at(900.0,12.5)
    deck_z = center.z/100.0
    pillar_h = max(0.0, deck_z-ravine_z)

    if pillar_h > 1.0:
        spawn_box(
            "PONT_PILE_CENTRALE",
            V(90000,1250,(ravine_z+pillar_h/2.0)*100.0),
            (70.0,70.0,pillar_h*100.0),
            MAT_BRIDGE,
            "Props/Pont"
        )


bridge_blockout()


def cave_blockout():
    p_prev = ROUTES["GROTTE"][-2]
    p_end = ROUTES["GROTTE"][-1]
    dx, dy = p_end[0]-p_prev[0], p_end[1]-p_prev[1]
    length = max(1e-6, math.hypot(dx, dy))
    ux, uy = dx/length, dy/length
    nx, ny = -uy, ux

    z = height_at(CAVE_TERRACE_X, CAVE_TERRACE_Y)
    tunnel_length_m = 8.0
    half_width_m = 2.8
    wall_t_m = 1.0
    wall_h_m = 4.2

    cx = p_end[0] + ux*tunnel_length_m/2.0
    cy = p_end[1] + uy*tunnel_length_m/2.0
    yaw = math.degrees(math.atan2(dy, dx))
    rot = unreal.Rotator(0, yaw, 0)

    spawn_box(
        "GROTTE_SOL",
        V(cx*100, cy*100, (z+0.08)*100),
        (tunnel_length_m*100, half_width_m*2*100, 16.0),
        MAT_CAVE_DARK,
        "Props/Grotte",
        rot
    )

    for side, sign in (("G", 1.0), ("D", -1.0)):
        wx = cx + nx*(half_width_m+wall_t_m/2.0)*sign
        wy = cy + ny*(half_width_m+wall_t_m/2.0)*sign
        spawn_box(
            "GROTTE_PAROI_%s" % side,
            V(wx*100, wy*100, (z+wall_h_m/2.0)*100),
            (tunnel_length_m*100, wall_t_m*100, wall_h_m*100),
            MAT_CAVE_DARK,
            "Props/Grotte",
            rot
        )

    spawn_box(
        "GROTTE_TOIT",
        V(cx*100, cy*100, (z+wall_h_m+0.4)*100),
        (tunnel_length_m*100, (half_width_m*2+wall_t_m*2)*100, 80.0),
        MAT_CAVE_DARK,
        "Props/Grotte",
        rot
    )


cave_blockout()


spawn_sphere(
    "REPERE_CONVERGENCE_17H00",
    V(0,0,height_at(0,0)*100+150),
    75,
    MAT_MARKER
)
spawn_sphere(
    "REPERE_JONCTION_HAUTE",
    V(176000,0,height_at(1760,0)*100+150),
    75,
    MAT_MARKER
)

spawn_person("THOMAS_NORMAL_PROXY", 650.0,-80.0,180.0,MAT_THOMAS)
spawn_person("EVA_PROXY", 654.0,-76.0,170.0,MAT_EVA)
spawn_person("LEA_PROXY_FLANC", 810.0,82.0,135.0,MAT_LEA)
spawn_person("THOMAS_INVERSE_PROXY", 1300.0,600.0,180.0,MAT_INVERSE)


def make_camera(name,pos,target,focal):
    try:
        cam = actors.spawn_actor_from_class(
            unreal.CineCameraActor,pos,unreal.Rotator(0,0,0),False
        )
        if not cam:
            raise RuntimeError("spawn_actor_from_class=None")
        label(cam,"CAM_REVIEW_"+name,"Cameras/Review_V11")
        cam.set_actor_rotation(unreal.MathLibrary.find_look_at_rotation(pos,target),False)
        cam.get_cine_camera_component().set_current_focal_length(float(focal))
        unreal.log("POLOP V11 CAM OK : "+name)
        return cam
    except Exception as exc:
        unreal.log_error("POLOP V11 CAM FAIL %s : %s"%(name,exc))
        return None


def target(x,y,extra=0):
    return V(x*100,y*100,height_at(x,y)*100+extra)


def nearest_route_sample(route_name, x, y):
    route = ROUTES[route_name]
    return min(route, key=lambda p: (p[0]-x)**2 + (p[1]-y)**2)


def route_camera_point(route_name, x, y, eye_cm=175.0):
    p = nearest_route_sample(route_name, x, y)
    return V(
        p[0]*100.0,
        p[1]*100.0,
        height_at(p[0], p[1])*100.0 + eye_cm
    )


a_eye = route_camera_point("A", 650.0, -80.0, 175.0)
a_look_p = nearest_route_sample("A", 710.0, -65.0)
a_look = V(a_look_p[0]*100, a_look_p[1]*100, height_at(a_look_p[0], a_look_p[1])*100 + 165)

b_eye = route_camera_point("B", 1300.0, 600.0, 175.0)
b_look_p = nearest_route_sample("B", 1230.0, 555.0)
b_look = V(b_look_p[0]*100, b_look_p[1]*100, height_at(b_look_p[0], b_look_p[1])*100 + 165)

cave_eye_p = nearest_route_sample("GROTTE", 1800.0, 76.0)
cave_eye = V(
    cave_eye_p[0]*100,
    cave_eye_p[1]*100,
    height_at(cave_eye_p[0], cave_eye_p[1])*100 + 175
)
cave_look = V(183400, 9200, height_at(1834.0, 92.0)*100 + 160)

conv_eye_p = nearest_route_sample("A", 8.0, 0.0)
conv_look_p = nearest_route_sample("A", 45.0, -6.0)

camera_specs = [
    ("01_TOP_MAP", V(100800, 0, 520000), V(100800, 0, 9000), 50),
    ("02_FLANC_CLOSE", V(75500, -8500, height_at(755,-85)*100+7000), target(825,45,650), 45),
    ("03_BRIDGE_A", V(81000, -10500, height_at(810,-105)*100+6500), target(900,12.5,450), 45),
    ("04_BRIDGE_B", V(99000, 15000, height_at(990,150)*100+6500), target(900,12.5,450), 45),
    ("05_HIGH_JUNCTION", V(169000, -8500, height_at(1760,0)*100+6500), target(1760,0,900), 42),
    ("06_CAVE_HUMAN", cave_eye, cave_look, 35),
    ("07_HUMAN_A", a_eye, a_look, 35),
    ("08_HUMAN_B", b_eye, b_look, 35),
    (
        "09_CONVERGENCE",
        V(conv_eye_p[0]*100, conv_eye_p[1]*100, height_at(conv_eye_p[0],conv_eye_p[1])*100+175),
        V(conv_look_p[0]*100, conv_look_p[1]*100, height_at(conv_look_p[0],conv_look_p[1])*100+165),
        35
    ),
]

created = []
for spec in camera_specs:
    cam = make_camera(*spec)
    if cam:
        created.append(cam)

if created:
    actors.set_selected_level_actors([created[0]])

timing = route_model["timing"]

unreal.log("============================================================")
unreal.log("POLOP PREVIZ V11 PREPAREE")
unreal.log("Heightmap : "+heightmap_path)
unreal.log("Route model : "+route_path)
unreal.log("A : %.1fm / %.1fmin"%(timing["A_length_m"],timing["A_minutes_at_2_2_kmh"]))
unreal.log("FLANC : %.1fm"%timing["flank_length_m"])
unreal.log("THOMAS INVERSE : %.1fm / total %.1fmin"%(
    timing["inverse_length_m"], timing["inverse_total_with_7min_pause"]
))
unreal.log("CAMERAS : %d / %d créées"%(len(created),len(camera_specs)))
unreal.log("IMPORT : Location UI 100800/0/0 | Scale 200/200/100 | Flip Y OFF")
unreal.log("============================================================")
