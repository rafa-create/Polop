# -*- coding: utf-8 -*-
"""
LA BOUCLE / POLOP - PREVIZ MASTER V10

Portable: one readable Python file, no encoded payload or machine-specific paths.
Unreal Engine 5.8: Tools > Execute Python Script, select this file.
Prerequisite: /Game/Main contains one 1009x1009 Landscape (16x16 components).
Save your current level before running. Every run duplicates /Game/Main into a
new work map and creates assets under /Game/POLOP/Generated_V09/Runs/<run_id>.
The source map and original materials/sequences are not overwritten.

Diagnostics: every run is isolated under Saved/POLOP/Runs/<run_id>/ :
keylog.jsonl, V11/, ANIMATION_V05/ and MASTER_V10/report_previz_v10.{json,txt,html}.
The editor stays responsive while Landscape layers/collision finish rebuilding.

Current milestone: terrain correction and objective-time animated blockout.
The 65-second review sequence is NOT yet the complete cinematic adaptation.
Ring, environmental effects and full A/B/B9 film edit are subsequent milestones.
"""

import base64
import html
import json
import math
import os
import traceback
import datetime
import time
import zlib
import unreal

MASTER_VERSION = "10"
EXPECTED_LANDSCAPE_LOCATION = unreal.Vector(100800.0, 0.0, 0.0)
EXPECTED_LANDSCAPE_SCALE = unreal.Vector(200.0, 200.0, 100.0)
EXPECTED_HEIGHTMAP_SIZE = 1009

CLEAN_OLD_POLOP_ACTORS = True
DELETE_EXTRA_LANDSCAPES = False
STRICT_LANDSCAPE_RESOLUTION = True

actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
editor_subsystem = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)
world = editor_subsystem.get_editor_world()

_SOURCE_V11 = r'''
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
# - aucune caméra : l'animation V05 est l'unique autorité caméra.
#
# Après exécution :
#   Saved/POLOP/Runs/<run_id>/V11/polop_v11_heightmap_1009.png
#   Saved/POLOP/Runs/<run_id>/V11/route_model_v11.json
#
# IMPORT DU LANDSCAPE V11 :
#   Supprimer uniquement le Landscape V10.
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
        "Supprimer uniquement le Landscape V10 puis importer :\n%s\n\n"
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
    folder = "/Game/POLOP/Generated_V09/Materials"
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


# Les caméras de revue V11 sont volontairement désactivées dans le pipeline master.
# V11 est désormais uniquement responsable de la géographie / blockout.
# Les seules caméras actives sont créées ensuite par l'animation V05.
unreal.log("POLOP V11 : caméras de revue désactivées (autorité = Animation V05).")


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
unreal.log("CAMERAS REVIEW : 0 — désactivées, Animation V05 uniquement")
unreal.log("IMPORT : Location UI 100800/0/0 | Scale 200/200/100 | Flip Y OFF")
unreal.log("============================================================")

'''
_SOURCE_V05 = r'''
import json
import math
import os
import struct
import zlib
import unreal

# =============================================================================
# LA BOUCLE / POLOP — ANIMATION PREVIZ V05
# Bible narrative : Script_POLOP.md
# Base géographique : V11 validée techniquement
# Unreal Engine 5.8
#
# OBJECTIF
# -------
# Construire une première simulation TEMPORELLE jouable dans Sequencer :
# - Thomas normal ;
# - Thomas inversé ;
# - Éva ;
# - Léa ;
# - coexistence Thomas normal / inversé entre 17h00 et 18h00 ;
# - traversée initiale de Léa par le pont ;
# - retour de Léa par le flanc ;
# - Thomas inversé B -> pont -> A dans son temps propre
#   (donc A -> pont -> B dans la lecture objective de cette séquence) ;
# - convergence de 17h00 ;
# - zone haute / attente / recherche ;
# - coexistence dans la caverne jusqu'au contact de 18h00 ;
# - POV animé de Thomas normal, Thomas inversé, Éva et Léa ;
# - fusion visuelle des deux proxies de Thomas à 18h00 (une seule occurrence visible) ;
# - caverne de validation reconstruite autour d’un axe libre, sans géométrie dans les POV ;
# - caméras finales placées dans des volumes garantis libres ;
# - POV de contrôle après 18h00 décalés hors des proxies au lieu de rester au point de contact.
#
# IMPORTANT — CORRECTIONS NARRATIVES AVANT ANIMATION
# --------------------------------------------------
# La lecture intégrale de Script_POLOP fait apparaître deux contraintes que les marqueurs
# V11 ne traduisaient pas correctement :
#
# 1) B6 se déroule à 17h01 et B8 à 17h00.
#    La convergence ne peut donc PAS être à ~900 m du pont comme l'ancien
#    REPERE_CONVERGENCE V11. Pour cette préviz, elle est replacée ~25 m avant
#    le pont sur A. C'est une hypothèse de blockout explicitement documentée.
#
# 2) A10 dit que Thomas s'écarte de "quelques mètres" dans une petite zone
#    rocheuse de quelques dizaines de m². Le guide GROTTE V11 mesurait ~125 m.
#    Animation V05 crée donc une MICRO-ZONE de caverne près de la jonction haute
#    sans modifier le Landscape V11. L'ancien placeholder de grotte est masqué.
#
# Ces deux corrections ne modifient pas A/B/pont/flanc : elles remettent les
# repères narratifs au bon endroit avant de commencer à animer.
#
# COMPRESSION TEMPORELLE
# ----------------------
# 1 minute objective du film = 1 seconde dans Sequencer.
# 16h58 = seconde 0
# 17h00 = seconde 2
# 17h30 = seconde 32
# 17h50 = seconde 52
# 17h58 = seconde 60
# 18h00 = seconde 62
# 62–65 s = freeze de contrôle NON NARRATIF pour inspecter la position finale.
#
# Cette compression change uniquement la vitesse de lecture de la préviz,
# jamais les heures objectives ni l'ordre des événements.
#
# SORTIES
# -------
# Saved/POLOP/Runs/<run_id>/ANIMATION_V05/animation_model_v05.json
# Content Browser :
# /Game/POLOP/Generated_V09/Sequences/LS_POLOP_ANIMATION_V05
#
# V05 supplante V04 : animation, POV, lisibilité et validation dans un seul script.
# Il supprime/recrée les Actors PZ_ANIM_* et remplace les Level Sequences V01/V02/V03/V04.
# =============================================================================

PREFIX = "PZ_ANIM_"
FOLDER_ROOT = "POLOP_PREVIZ/Animation_V05"
FPS = 30
NARRATIVE_SECONDS = 62.0
REVIEW_TAIL_SECONDS = 3.0
SEQUENCE_SECONDS = NARRATIVE_SECONDS + REVIEW_TAIL_SECONDS
SAMPLE_SECONDS = 0.25

# POV : les quatre caméras sont animées dans LA MEME Level Sequence.
# Sélectionner la caméra souhaitée dans le viewport puis Play.
POV_SAMPLE_SECONDS = 0.10
POV_FORWARD_OFFSET_CM = 38.0
POV_LOOK_AHEAD_SECONDS = 0.35
POV_FOCAL_MM = 20.0

POV_EYE_HEIGHT_CM = {
    "THOMAS_NORMAL": 166.0,
    "THOMAS_INVERSE": 166.0,
    "EVA": 158.0,
    "LEA": 126.0,
}

# À 18h00 il n'existe visuellement qu'un seul Thomas au point de retournement.
# Les deux proxies techniques coexistent avant 18h00, puis le proxy inversé est
# réduit à quasi-zéro exactement au contact pour éviter une fausse duplication.
CONTACT_FRAME = int(round(NARRATIVE_SECONDS * FPS))
CONTACT_PREV_FRAME = max(0, CONTACT_FRAME - 1)
CONTACT_HIDDEN_SCALE = 0.001

# Hypothèses de blockout NON CANONIQUES mais nécessaires pour la première simu.
CONVERGENCE_BEFORE_BRIDGE_M = 25.0
LEA_FLANK_RETURN_END_MIN = 8.0     # 17h06 — non précisé par Script_POLOP.
NORMAL_REJOIN_HOLD_END_MIN = 8.0   # le groupe attend Léa près du pont.
B5_DISTANCE_FROM_BRIDGE_M = 800.0  # "à portée visuelle" vers 17h30.

actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
asset_tools = unreal.AssetToolsHelpers.get_asset_tools()

CUBE = unreal.load_asset("/Engine/BasicShapes/Cube.Cube")
CYLINDER = unreal.load_asset("/Engine/BasicShapes/Cylinder.Cylinder")
SPHERE = unreal.load_asset("/Engine/BasicShapes/Sphere.Sphere")

if not CUBE or not CYLINDER or not SPHERE:
    raise RuntimeError("BasicShapes Unreal introuvables.")


def V(x, y, z):
    return unreal.Vector(float(x), float(y), float(z))


def clamp(v, lo, hi):
    return max(lo, min(hi, v))


# =============================================================================
# CHARGEMENT V11
# =============================================================================

saved_dir = unreal.Paths.convert_relative_path_to_full(
    unreal.Paths.project_saved_dir()
)

v11_dir = os.path.join(saved_dir, "POLOP", "V11")
route_path = os.path.join(v11_dir, "route_model_v11.json")
heightmap_path = os.path.join(v11_dir, "polop_v11_heightmap_1009.png")

if not os.path.exists(route_path):
    raise RuntimeError(
        "route_model_v11.json absent. Exécuter d'abord previz_polop_complet_v11.py"
    )

if not os.path.exists(heightmap_path):
    raise RuntimeError(
        "polop_v11_heightmap_1009.png absent. V11 doit exister avant l'animation."
    )

model_v11 = json.load(open(route_path, "r", encoding="utf-8"))
ROUTES = {
    name: [tuple(p) for p in data["samples"]]
    for name, data in model_v11["routes"].items()
}


# =============================================================================
# LANDSCAPE / HEIGHTMAP — hauteur réelle pour les micro-props
# =============================================================================

HM_SIZE = 1009

landscapes = []
for actor in actors.get_all_level_actors():
    try:
        if "Landscape" in actor.get_class().get_name():
            landscapes.append(actor)
    except Exception:
        pass

if not landscapes:
    raise RuntimeError("Aucun Landscape détecté dans le niveau.")

landscape = landscapes[0]
land_loc = unreal.Vector(0.0, -100800.0, landscape.get_actor_location().z)
land_scale = landscape.get_actor_scale3d()


def load_png16(path):
    data = open(path, "rb").read()
    if data[:8] != b"\x89PNG\r\n\x1a\n":
        raise RuntimeError("PNG V11 invalide.")

    pos = 8
    idat = bytearray()
    header = None

    while pos < len(data):
        n = struct.unpack(">I", data[pos:pos+4])[0]
        pos += 4
        kind = data[pos:pos+4]
        pos += 4
        payload = data[pos:pos+n]
        pos += n + 4

        if kind == b"IHDR":
            header = struct.unpack(">IIBBBBB", payload)
        elif kind == b"IDAT":
            idat.extend(payload)
        elif kind == b"IEND":
            break

    if header is None or header[:4] != (1009, 1009, 16, 0):
        raise RuntimeError("Format heightmap V11 inattendu.")

    raw = zlib.decompress(bytes(idat))
    stride = HM_SIZE * 2 + 1
    grid = []

    for iy in range(HM_SIZE):
        row = raw[iy*stride:(iy+1)*stride]
        if row[0] != 0:
            raise RuntimeError("Animation V05 attend le filtre PNG 0 de V11.")

        grid.append([
            struct.unpack(">H", row[1+ix*2:3+ix*2])[0]
            for ix in range(HM_SIZE)
        ])

    return grid


height_grid = load_png16(heightmap_path)


def pixel_world_z_cm(ix, iy):
    value = height_grid[iy][ix]
    local_m = (value - 32768.0) / 32768.0 * 256.0
    return land_loc.z + local_m * land_scale.z


def terrain_z_m(x_m, y_m):
    fx = (x_m*100.0 - land_loc.x) / land_scale.x
    fy = (y_m*100.0 - land_loc.y) / land_scale.y

    if fx < 0 or fy < 0 or fx > HM_SIZE-1 or fy > HM_SIZE-1:
        raise RuntimeError(
            "Point hors Landscape : %.2f %.2f" % (x_m, y_m)
        )

    x0, y0 = int(math.floor(fx)), int(math.floor(fy))
    x1, y1 = min(HM_SIZE-1, x0+1), min(HM_SIZE-1, y0+1)
    tx, ty = fx-x0, fy-y0

    z00 = pixel_world_z_cm(x0, y0)
    z10 = pixel_world_z_cm(x1, y0)
    z01 = pixel_world_z_cm(x0, y1)
    z11 = pixel_world_z_cm(x1, y1)

    za = z00*(1.0-tx) + z10*tx
    zb = z01*(1.0-tx) + z11*tx

    return (za*(1.0-ty) + zb*ty) / 100.0


# =============================================================================
# ROUTES : arc-length
# =============================================================================

def route_cumulative(route):
    cumulative = [0.0]
    for a, b in zip(route, route[1:]):
        cumulative.append(cumulative[-1] + math.dist(a, b))
    return cumulative


CUM = {
    name: route_cumulative(route)
    for name, route in ROUTES.items()
}

LENGTH = {
    name: values[-1]
    for name, values in CUM.items()
}


def route_point_at_station(name, station_m):
    route = ROUTES[name]
    cumulative = CUM[name]
    s = clamp(station_m, 0.0, cumulative[-1])

    for i in range(len(route)-1):
        if cumulative[i+1] >= s:
            segment = cumulative[i+1] - cumulative[i]
            t = 0.0 if segment <= 1e-9 else (s-cumulative[i]) / segment
            a, b = route[i], route[i+1]
            return (
                a[0] + (b[0]-a[0])*t,
                a[1] + (b[1]-a[1])*t,
                a[2] + (b[2]-a[2])*t,
            )

    return route[-1]


def nearest_station(name, x_m, y_m):
    route = ROUTES[name]
    cumulative = CUM[name]
    index = min(
        range(len(route)),
        key=lambda i: (route[i][0]-x_m)**2 + (route[i][1]-y_m)**2
    )
    return cumulative[index]


A_BRIDGE_STATION = nearest_station("A", 900.0, 0.0)
B_BRIDGE_STATION = nearest_station("B", 900.0, 25.0)

CONVERGENCE_STATION = max(
    0.0,
    A_BRIDGE_STATION - CONVERGENCE_BEFORE_BRIDGE_M
)

CONVERGENCE_POINT = route_point_at_station(
    "A",
    CONVERGENCE_STATION
)

A_BRIDGE_POINT = route_point_at_station(
    "A",
    A_BRIDGE_STATION
)

B_BRIDGE_POINT = route_point_at_station(
    "B",
    B_BRIDGE_STATION
)

HIGH_POINT = ROUTES["A"][-1]


# =============================================================================
# MICRO-ZONE CAVERNE — conforme à A10/A11/A15, sans refaire le Landscape
# =============================================================================
#
# Script_POLOP donne des qualités, pas des dimensions exactes :
# "quelques mètres", "quelques dizaines de mètres carrés", accès surveillable.
# V05 choisit donc une poche ~8m x 6m, explicitement comme hypothèse de préviz.
# =============================================================================

high_x, high_y, high_z = HIGH_POINT

CAVE_ACCESS_POINT = (
    high_x + 4.0,
    high_y + 3.0,
    terrain_z_m(high_x + 4.0, high_y + 3.0)
)

CAVE_ZONE_POINT = (
    high_x + 7.0,
    high_y + 6.0,
    terrain_z_m(high_x + 7.0, high_y + 6.0)
)

CAVE_ENTRY_POINT = (
    high_x + 9.0,
    high_y + 8.0,
    terrain_z_m(high_x + 9.0, high_y + 8.0)
)

CAVE_DARK_SLOT = (
    high_x + 11.0,
    high_y + 9.5,
    terrain_z_m(high_x + 11.0, high_y + 9.5) + 0.2
)

CAVE_FISSURE_POINT = (
    high_x + 13.0,
    high_y + 10.5,
    terrain_z_m(high_x + 13.0, high_y + 10.5) + 0.4
)

CAVE_CONTACT_POINT = (
    high_x + 14.0,
    high_y + 11.0,
    terrain_z_m(high_x + 14.0, high_y + 11.0) + 0.8
)

CAVE_GUARD_POINT = route_point_at_station(
    "A",
    max(0.0, LENGTH["A"] - 8.0)
)

CAVE_SEARCH_POINT_1 = (
    high_x + 5.5,
    high_y + 5.0,
    terrain_z_m(high_x + 5.5, high_y + 5.0)
)

CAVE_SEARCH_POINT_2 = (
    high_x + 7.0,
    high_y + 3.5,
    terrain_z_m(high_x + 7.0, high_y + 3.5)
)

# Axe local de la cavité. Toute la géométrie V05 et les caméras de contrôle
# sont construites dans ce repère afin d'éviter les collisions caméra/paroi.
_CAVE_DX = CAVE_CONTACT_POINT[0] - CAVE_ENTRY_POINT[0]
_CAVE_DY = CAVE_CONTACT_POINT[1] - CAVE_ENTRY_POINT[1]
_CAVE_AXIS_LEN = max(0.001, math.sqrt(_CAVE_DX*_CAVE_DX + _CAVE_DY*_CAVE_DY))
CAVE_UX = _CAVE_DX / _CAVE_AXIS_LEN
CAVE_UY = _CAVE_DY / _CAVE_AXIS_LEN
CAVE_PX = -CAVE_UY
CAVE_PY = CAVE_UX
CAVE_YAW_DEG = math.degrees(math.atan2(CAVE_UY, CAVE_UX))


def cave_xy(along_m, side_m=0.0):
    return (
        CAVE_ENTRY_POINT[0] + CAVE_UX*along_m + CAVE_PX*side_m,
        CAVE_ENTRY_POINT[1] + CAVE_UY*along_m + CAVE_PY*side_m,
    )


def cave_ground_point(along_m, side_m=0.0, z_offset_m=0.0):
    x, y = cave_xy(along_m, side_m)
    return (x, y, terrain_z_m(x, y) + z_offset_m)


# =============================================================================
# NETTOYAGE ACTORS ANIMATION V05
# =============================================================================

def cleanup_animation():
    old = []

    for actor in actors.get_all_level_actors():
        try:
            if actor.get_actor_label().startswith(PREFIX):
                old.append(actor)
        except Exception:
            pass

    if old:
        actors.destroy_actors(old)

    unreal.log(
        "ANIMATION V05 : %d anciens Actors PZ_ANIM_ supprimés."
        % len(old)
    )


cleanup_animation()


# Masque les placeholders V11 qui contredisent maintenant la micro-zone.
for actor in actors.get_all_level_actors():
    try:
        label = actor.get_actor_label()

        if (
            label.startswith("PZ_GROTTE_")
            or label.startswith("PZ_GUIDE_")
            or label.startswith("PZ_REPERE_")
            or label.startswith("PZ_CAM_REVIEW_")
            or label.startswith("PZ_CAM_CAL_")
            or label in (
                "PZ_THOMAS_NORMAL_PROXY",
                "PZ_THOMAS_INVERSE_PROXY",
                "PZ_EVA_PROXY",
                "PZ_LEA_PROXY_FLANC",
            )
        ):
            try:
                actor.set_is_temporarily_hidden_in_editor(True)
            except Exception:
                pass

            try:
                actor.set_actor_hidden_in_game(True)
            except Exception:
                pass

    except Exception:
        pass


# =============================================================================
# MATERIAUX
# =============================================================================

def ensure_material(name, rgb):
    folder = "/Game/POLOP/Generated_V09/Materials"
    unreal.EditorAssetLibrary.make_directory(folder)
    path = folder + "/" + name

    if unreal.EditorAssetLibrary.does_asset_exist(path):
        return unreal.load_asset(path)

    mat = asset_tools.create_asset(
        name,
        folder,
        unreal.Material,
        unreal.MaterialFactoryNew()
    )

    expr = unreal.MaterialEditingLibrary.create_material_expression(
        mat,
        unreal.MaterialExpressionConstant3Vector,
        -300,
        0
    )

    expr.set_editor_property(
        "constant",
        unreal.LinearColor(rgb[0], rgb[1], rgb[2], 1.0)
    )

    unreal.MaterialEditingLibrary.connect_material_property(
        expr,
        "",
        unreal.MaterialProperty.MP_BASE_COLOR
    )

    unreal.MaterialEditingLibrary.recompile_material(mat)
    unreal.EditorAssetLibrary.save_loaded_asset(mat)

    return mat


MAT_THOMAS = ensure_material("M_ANIM_V05_THOMAS", (0.05, 0.35, 1.0))
MAT_INVERSE = ensure_material("M_ANIM_V05_INVERSE", (1.0, 0.08, 0.03))
MAT_EVA = ensure_material("M_ANIM_V05_EVA", (0.80, 0.12, 0.82))
MAT_LEA = ensure_material("M_ANIM_V05_LEA", (0.03, 0.85, 0.55))
MAT_EVENT = ensure_material("M_ANIM_V05_EVENT", (1.0, 0.95, 0.05))
MAT_ROCK = ensure_material("M_ANIM_V05_ROCK", (0.13, 0.15, 0.18))
MAT_CAVE = ensure_material("M_ANIM_V05_CAVE", (0.025, 0.025, 0.035))
MAT_ANCHOR = ensure_material("M_ANIM_V05_ANCHOR", (0.72, 0.48, 0.12))
MAT_TRAIL = ensure_material("M_ANIM_V05_TRAIL", (0.26, 0.18, 0.10))
MAT_TRAIL_FLANK = ensure_material("M_ANIM_V05_TRAIL_FLANK", (0.18, 0.22, 0.12))
MAT_BRIDGE_READABLE = ensure_material("M_ANIM_V05_BRIDGE_READABLE", (0.34, 0.20, 0.08))
MAT_ROCK_READABLE = ensure_material("M_ANIM_V05_ROCK_READABLE", (0.12, 0.13, 0.15))


def label_actor(actor, name, folder):
    actor.set_actor_label(PREFIX + name, True)

    try:
        actor.set_folder_path(
            unreal.Name(FOLDER_ROOT + "/" + folder)
        )
    except Exception:
        pass


def apply_material(actor, material):
    try:
        comp = actor.get_component_by_class(
            unreal.StaticMeshComponent
        )
        if comp:
            comp.set_material(0, material)
    except Exception:
        pass


def spawn_box(name, position, size_cm, material, folder, rotation=None):
    actor = actors.spawn_actor_from_object(
        CUBE,
        position,
        rotation or unreal.Rotator(0, 0, 0),
        False
    )

    label_actor(actor, name, folder)

    actor.set_actor_scale3d(
        V(
            size_cm[0]/100.0,
            size_cm[1]/100.0,
            size_cm[2]/100.0
        )
    )

    apply_material(actor, material)
    return actor


def spawn_sphere(name, position, radius_cm, material, folder):
    actor = actors.spawn_actor_from_object(
        SPHERE,
        position,
        unreal.Rotator(0, 0, 0),
        False
    )

    label_actor(actor, name, folder)

    actor.set_actor_scale3d(
        V(
            radius_cm/50.0,
            radius_cm/50.0,
            radius_cm/50.0
        )
    )

    apply_material(actor, material)
    return actor



def spawn_rock(name, x_m, y_m, z_m, size_m, material, folder, yaw=0.0):
    actor = actors.spawn_actor_from_object(
        SPHERE,
        V(x_m*100.0, y_m*100.0, z_m*100.0),
        unreal.Rotator(0, yaw, 0),
        False
    )
    label_actor(actor, name, folder)
    actor.set_actor_scale3d(
        V(size_m[0]*2.0, size_m[1]*2.0, size_m[2]*2.0)
    )
    apply_material(actor, material)
    return actor


def spawn_readable_route(name, route, material, folder, width_cm=145.0, step=4):
    pts = route[::step]
    if pts[-1] != route[-1]:
        pts.append(route[-1])

    for i, (a_raw, b_raw) in enumerate(zip(pts, pts[1:]), 1):
        a = (a_raw[0], a_raw[1], terrain_z_m(a_raw[0], a_raw[1]))
        b = (b_raw[0], b_raw[1], terrain_z_m(b_raw[0], b_raw[1]))
        av = V(a[0]*100.0, a[1]*100.0, a[2]*100.0 + 7.0)
        bv = V(b[0]*100.0, b[1]*100.0, b[2]*100.0 + 7.0)
        center = V((av.x+bv.x)/2.0, (av.y+bv.y)/2.0, (av.z+bv.z)/2.0)
        length_cm = math.sqrt(
            (bv.x-av.x)**2 + (bv.y-av.y)**2 + (bv.z-av.z)**2
        )
        spawn_box(
            "READABLE_%s_%03d" % (name, i),
            center,
            (length_cm*1.015, width_cm, 6.0),
            material,
            folder,
            unreal.MathLibrary.find_look_at_rotation(av, bv)
        )


def spawn_person(name, point, height_cm, material):
    x, y, z = point

    actor = actors.spawn_actor_from_object(
        CYLINDER,
        V(
            x*100.0,
            y*100.0,
            z*100.0 + height_cm/2.0
        ),
        unreal.Rotator(0, 0, 0),
        False
    )

    label_actor(actor, name, "Personnages")

    # Basic Cylinder = 100 cm de haut.
    actor.set_actor_scale3d(
        V(
            0.34,
            0.34,
            height_cm/100.0
        )
    )

    apply_material(actor, material)
    return actor



# Sentiers sobres de revue : mêmes routes, lecture moins "debug".
spawn_readable_route("A", ROUTES["A"], MAT_TRAIL, "Readable/Trails/A", 155.0, 4)
spawn_readable_route("B", ROUTES["B"], MAT_TRAIL, "Readable/Trails/B", 155.0, 4)
spawn_readable_route("FLANC", ROUTES["FLANC"], MAT_TRAIL_FLANK, "Readable/Trails/Flanc", 135.0, 3)

# Pont V11 : géométrie intacte, apparence neutralisée.
for _bridge_actor in actors.get_all_level_actors():
    try:
        if _bridge_actor.get_actor_label().startswith("PZ_PONT_"):
            apply_material(_bridge_actor, MAT_BRIDGE_READABLE)
    except Exception:
        pass


# =============================================================================
# MICRO-GEOMETRIE NARRATIVE
# =============================================================================

# Convergence 17h00 + gros relief permettant occultation B7/B8.
conv_x, conv_y, conv_z = CONVERGENCE_POINT

spawn_sphere(
    "EVENT_17H00_CONVERGENCE",
    V(conv_x*100, conv_y*100, terrain_z_m(conv_x, conv_y)*100 + 120),
    65,
    MAT_EVENT,
    "Evenements"
)

# Rocher placé sur le côté de A, assez proche pour permettre un masque caméra.
spawn_box(
    "CONVERGENCE_ROCK",
    V(
        (conv_x+2.5)*100,
        (conv_y+5.0)*100,
        (terrain_z_m(conv_x+2.5, conv_y+5.0)+2.4)*100
    ),
    (900, 450, 480),
    MAT_ROCK,
    "MicroGeo/Convergence",
    unreal.Rotator(0, 20, 0)
)

# Micro-zone caverne V05 : shell lisible construit sur l'axe entrée -> contact.
# Largeur intérieure ~4,4 m ; hauteur libre ~3,2 m. Aucune masse n'est placée
# au centre de l'axe, ce qui garantit une ligne de vue exploitable pour les POV.
_cave_mid_along = _CAVE_AXIS_LEN * 0.52
_cave_mid_x, _cave_mid_y = cave_xy(_cave_mid_along, 0.0)
_cave_mid_z = terrain_z_m(_cave_mid_x, _cave_mid_y)
_cave_rot = unreal.Rotator(0, CAVE_YAW_DEG, 0)
_cave_shell_length_cm = int(round((_CAVE_AXIS_LEN + 2.4) * 100.0))

# Sol fin, volontairement visible pour lire les distances.
spawn_box(
    "CAVE_REVIEW_FLOOR",
    V(_cave_mid_x*100, _cave_mid_y*100, _cave_mid_z*100 - 8),
    (_cave_shell_length_cm, 440, 16),
    MAT_CAVE,
    "MicroGeo/CaverneV05",
    _cave_rot
)

# Parois latérales : éloignées de 2,35 m de l'axe central.
for _side, _name in ((2.35, "CAVE_WALL_LEFT"), (-2.35, "CAVE_WALL_RIGHT")):
    _wx, _wy = cave_xy(_cave_mid_along, _side)
    _wz = terrain_z_m(_wx, _wy) + 1.65
    spawn_box(
        _name,
        V(_wx*100, _wy*100, _wz*100),
        (_cave_shell_length_cm, 32, 330),
        MAT_CAVE,
        "MicroGeo/CaverneV05",
        _cave_rot
    )

# Plafond suffisamment haut pour que les caméras à 1,55–1,75 m restent libres.
_roof_x, _roof_y = cave_xy(_cave_mid_along, 0.0)
_roof_z = terrain_z_m(_roof_x, _roof_y) + 3.35
spawn_box(
    "CAVE_REVIEW_ROOF",
    V(_roof_x*100, _roof_y*100, _roof_z*100),
    (_cave_shell_length_cm, 480, 24),
    MAT_CAVE,
    "MicroGeo/CaverneV05",
    _cave_rot
)

# Fond derrière le contact : jamais entre une caméra de contrôle et le contact.
_back_x, _back_y = cave_xy(_CAVE_AXIS_LEN + 1.0, 0.0)
_back_z = terrain_z_m(_back_x, _back_y) + 1.65
spawn_box(
    "CAVE_REVIEW_BACK",
    V(_back_x*100, _back_y*100, _back_z*100),
    (28, 470, 330),
    MAT_CAVE,
    "MicroGeo/CaverneV05",
    _cave_rot
)

# Deux rochers d'entrée sur les côtés, pas de masque plein devant l'ouverture.
for _side, _name, _yaw in ((2.2, "CAVE_ENTRY_ROCK_L", 12), (-2.2, "CAVE_ENTRY_ROCK_R", -12)):
    _rx, _ry = cave_xy(-0.15, _side)
    _rz = terrain_z_m(_rx, _ry) + 1.45
    spawn_rock(
        _name, _rx, _ry, _rz,
        (1.65, 1.35, 2.7),
        MAT_ROCK_READABLE,
        "MicroGeo/CaverneV05/Rocks",
        CAVE_YAW_DEG + _yaw
    )

# Quelques volumes latéraux seulement, pour conserver une lecture "rocheuse"
# sans créer d'obstacle dans le couloir central.
for (_name, _along, _side, _dz, _sx, _sy, _sz, _yaw) in (
    ("CAVE_SIDE_L1", 2.0,  2.55, 1.1, 1.8, 1.0, 2.0,  18),
    ("CAVE_SIDE_R1", 3.0, -2.55, 1.2, 1.6, 1.1, 2.2, -16),
    ("CAVE_SIDE_L2", 4.4,  2.55, 1.0, 1.5, 1.0, 1.9,  -8),
):
    _rx, _ry = cave_xy(_along, _side)
    _rz = terrain_z_m(_rx, _ry) + _dz
    spawn_rock(
        _name, _rx, _ry, _rz,
        (_sx, _sy, _sz),
        MAT_ROCK_READABLE,
        "MicroGeo/CaverneV05/Rocks",
        CAVE_YAW_DEG + _yaw
    )

# Repère de contact réduit à 12 cm : utile en blockout mais trop petit pour
# boucher un POV.
spawn_sphere(
    "EVENT_18H00_CONTACT",
    V(
        CAVE_CONTACT_POINT[0]*100,
        CAVE_CONTACT_POINT[1]*100,
        CAVE_CONTACT_POINT[2]*100 + 18
    ),
    12,
    MAT_EVENT,
    "Evenements"
)


# Proxy mousqueton / ancrage côté B.
bbx, bby, bbz = B_BRIDGE_POINT

spawn_box(
    "BRIDGE_ANCHOR_ROCK",
    V(
        (bbx+1.5)*100,
        (bby+1.5)*100,
        (terrain_z_m(bbx+1.5, bby+1.5)+0.7)*100
    ),
    (180, 180, 140),
    MAT_ROCK,
    "MicroGeo/Pont"
)

spawn_sphere(
    "MOUSQUETON_PROXY",
    V(
        (bbx+0.6)*100,
        (bby+0.4)*100,
        terrain_z_m(bbx, bby)*100 + 95
    ),
    18,
    MAT_ANCHOR,
    "MicroGeo/Pont"
)


# =============================================================================
# MODELE TEMPOREL — positions canoniques + hypothèses de blockout
# =============================================================================

# Temps = minutes objectives depuis 16h58, mais lu en secondes dans Sequencer.
# Exemple : 17h30 => 32.

def point_with_real_terrain(p):
    return (
        p[0],
        p[1],
        terrain_z_m(p[0], p[1])
    )


def linear_point(a, b, alpha):
    alpha = clamp(alpha, 0.0, 1.0)
    return (
        a[0] + (b[0]-a[0])*alpha,
        a[1] + (b[1]-a[1])*alpha,
        a[2] + (b[2]-a[2])*alpha,
    )


def station_segment(route_name, t0, t1, s0, s1):
    return {
        "type": "station",
        "route": route_name,
        "t0": float(t0),
        "t1": float(t1),
        "s0": float(s0),
        "s1": float(s1),
    }


def custom_segment(t0, t1, p0, p1):
    return {
        "type": "custom",
        "t0": float(t0),
        "t1": float(t1),
        "p0": tuple(p0),
        "p1": tuple(p1),
    }


def hold_segment(t0, t1, p):
    return custom_segment(t0, t1, p, p)


# Normal Thomas / Eva commencent sous le pont, Léa légèrement devant.
normal_start_station = max(0.0, CONVERGENCE_STATION - 80.0)
eva_start_station = max(0.0, CONVERGENCE_STATION - 72.0)
lea_start_station = max(0.0, A_BRIDGE_STATION - 35.0)

# Après retrouvailles : pont -> haut de 17h06 à 17h50.
GROUP_DEPART_AFTER_LEA = LEA_FLANK_RETURN_END_MIN
GROUP_HIGH_TIME = 52.0

# Descente Eva/Léa après 17h57.
A_DESCEND_3MIN = max(0.0, LENGTH["A"] - 100.0)

# B5 vers 17h30 : point encore ~800 m au-dessus du pont sur B.
# Route B est orientée HAUT -> PONT.
B5_STATION = max(0.0, LENGTH["B"] - B5_DISTANCE_FROM_BRIDGE_M)

# A 17h01 en lecture objective, Thomas inversé vient de traverser A -> B.
# Dans son temps propre, c'est bien B -> A conformément à B6.
ANIM = {}

ANIM["THOMAS_NORMAL"] = [
    station_segment("A", 0.0, 2.0, normal_start_station, CONVERGENCE_STATION),
    station_segment("A", 2.0, 3.0, CONVERGENCE_STATION, A_BRIDGE_STATION),
    hold_segment(
        3.0,
        GROUP_DEPART_AFTER_LEA,
        point_with_real_terrain(A_BRIDGE_POINT)
    ),
    station_segment(
        "A",
        GROUP_DEPART_AFTER_LEA,
        GROUP_HIGH_TIME,
        A_BRIDGE_STATION,
        LENGTH["A"]
    ),
    custom_segment(
        52.0,
        52.5,
        point_with_real_terrain(HIGH_POINT),
        point_with_real_terrain(CAVE_ACCESS_POINT)
    ),
    hold_segment(
        52.5,
        57.0,
        point_with_real_terrain(CAVE_ZONE_POINT)
    ),
    custom_segment(
        57.0,
        59.0,
        point_with_real_terrain(CAVE_ZONE_POINT),
        point_with_real_terrain(CAVE_ENTRY_POINT)
    ),
    custom_segment(
        59.0,
        60.0,
        point_with_real_terrain(CAVE_ENTRY_POINT),
        CAVE_FISSURE_POINT
    ),
    hold_segment(
        60.0,
        61.0,
        CAVE_FISSURE_POINT
    ),
    custom_segment(
        61.0,
        62.0,
        CAVE_FISSURE_POINT,
        CAVE_CONTACT_POINT
    ),
]

ANIM["EVA"] = [
    station_segment("A", 0.0, 2.0, eva_start_station, CONVERGENCE_STATION + 10.0),
    station_segment("A", 2.0, 3.0, CONVERGENCE_STATION + 10.0, A_BRIDGE_STATION),
    hold_segment(
        3.0,
        GROUP_DEPART_AFTER_LEA,
        point_with_real_terrain(A_BRIDGE_POINT)
    ),
    station_segment(
        "A",
        GROUP_DEPART_AFTER_LEA,
        52.0,
        A_BRIDGE_STATION,
        LENGTH["A"]
    ),
    hold_segment(
        52.0,
        57.0,
        point_with_real_terrain(CAVE_GUARD_POINT)
    ),
    custom_segment(
        57.0,
        58.0,
        point_with_real_terrain(CAVE_GUARD_POINT),
        point_with_real_terrain(CAVE_SEARCH_POINT_1)
    ),
    custom_segment(
        58.0,
        59.0,
        point_with_real_terrain(CAVE_SEARCH_POINT_1),
        point_with_real_terrain(CAVE_SEARCH_POINT_2)
    ),
    custom_segment(
        59.0,
        59.3,
        point_with_real_terrain(CAVE_SEARCH_POINT_2),
        point_with_real_terrain(HIGH_POINT)
    ),
    station_segment(
        "A",
        59.3,
        62.0,
        LENGTH["A"],
        A_DESCEND_3MIN
    ),
]

# Léa : A -> pont -> B, puis retour B -> A par le FLANC.
# FLANC V11 est bien orienté B -> A.
ANIM["LEA"] = [
    station_segment("A", 0.0, 0.75, lea_start_station, A_BRIDGE_STATION),
    custom_segment(
        0.75,
        1.25,
        point_with_real_terrain(A_BRIDGE_POINT),
        point_with_real_terrain(B_BRIDGE_POINT)
    ),
    hold_segment(
        1.25,
        2.2,
        point_with_real_terrain(B_BRIDGE_POINT)
    ),
    station_segment(
        "FLANC",
        2.2,
        LEA_FLANK_RETURN_END_MIN,
        0.0,
        LENGTH["FLANC"]
    ),
    station_segment(
        "A",
        LEA_FLANK_RETURN_END_MIN,
        52.0,
        A_BRIDGE_STATION,
        LENGTH["A"]
    ),
    hold_segment(
        52.0,
        57.0,
        point_with_real_terrain(CAVE_GUARD_POINT)
    ),
    custom_segment(
        57.0,
        58.0,
        point_with_real_terrain(CAVE_GUARD_POINT),
        point_with_real_terrain(CAVE_SEARCH_POINT_1)
    ),
    custom_segment(
        58.0,
        59.0,
        point_with_real_terrain(CAVE_SEARCH_POINT_1),
        point_with_real_terrain(CAVE_SEARCH_POINT_2)
    ),
    custom_segment(
        59.0,
        59.3,
        point_with_real_terrain(CAVE_SEARCH_POINT_2),
        point_with_real_terrain(HIGH_POINT)
    ),
    station_segment(
        "A",
        59.3,
        62.0,
        LENGTH["A"],
        A_DESCEND_3MIN - 8.0
    ),
]

# Thomas inversé dans la lecture OBJECTIVE :
# avant 17h00, proxy sous le niveau ;
# 17h00 fermeture ;
# 17h00 -> 17h01 : A vers pont puis A -> B.
# Cela correspond, dans son temps propre, à B -> A puis convergence.
hidden_point = (
    CONVERGENCE_POINT[0],
    CONVERGENCE_POINT[1],
    -1000.0
)

ANIM["THOMAS_INVERSE"] = [
    hold_segment(0.0, 1.95, hidden_point),
    custom_segment(
        1.95,
        2.0,
        hidden_point,
        point_with_real_terrain(CONVERGENCE_POINT)
    ),
    station_segment(
        "A",
        2.0,
        2.5,
        CONVERGENCE_STATION,
        A_BRIDGE_STATION
    ),
    custom_segment(
        2.5,
        3.0,
        point_with_real_terrain(A_BRIDGE_POINT),
        point_with_real_terrain(B_BRIDGE_POINT)
    ),
    station_segment(
        "B",
        3.0,
        32.0,
        LENGTH["B"],
        B5_STATION
    ),
    station_segment(
        "B",
        32.0,
        59.0,
        B5_STATION,
        0.0
    ),
    custom_segment(
        59.0,
        60.0,
        point_with_real_terrain(HIGH_POINT),
        point_with_real_terrain(CAVE_ENTRY_POINT)
    ),
    custom_segment(
        60.0,
        61.0,
        point_with_real_terrain(CAVE_ENTRY_POINT),
        CAVE_DARK_SLOT
    ),
    custom_segment(
        61.0,
        62.0,
        CAVE_DARK_SLOT,
        CAVE_CONTACT_POINT
    ),
]

def _segment_final_point(segment):
    if segment["type"] == "station":
        return point_with_real_terrain(
            route_point_at_station(
                segment["route"],
                segment["s1"]
            )
        )
    return tuple(segment["p1"])


# Freeze de contrôle après 18h00.
# NON NARRATIF : garde les poses finales visibles de 62 à 65 secondes.
for _actor_name in ("THOMAS_NORMAL", "THOMAS_INVERSE", "EVA", "LEA"):
    _final_point = _segment_final_point(ANIM[_actor_name][-1])
    ANIM[_actor_name].append(
        hold_segment(NARRATIVE_SECONDS, SEQUENCE_SECONDS, _final_point)
    )



def eval_segment(segment, t):
    t0, t1 = segment["t0"], segment["t1"]

    if t1 <= t0:
        alpha = 1.0
    else:
        alpha = clamp((t-t0)/(t1-t0), 0.0, 1.0)

    if segment["type"] == "station":
        s = segment["s0"] + (segment["s1"]-segment["s0"])*alpha
        p = route_point_at_station(segment["route"], s)
        return point_with_real_terrain(p)

    return linear_point(segment["p0"], segment["p1"], alpha)


def eval_actor(name, t):
    segments = ANIM[name]

    for segment in segments:
        if segment["t0"] <= t <= segment["t1"] + 1e-8:
            return eval_segment(segment, t)

    if t < segments[0]["t0"]:
        return eval_segment(segments[0], segments[0]["t0"])

    return eval_segment(segments[-1], segments[-1]["t1"])


# =============================================================================
# ACTORS ANIMÉS
# =============================================================================

actor_objects = {
    "THOMAS_NORMAL": spawn_person(
        "CHAR_THOMAS_NORMAL",
        eval_actor("THOMAS_NORMAL", 0.0),
        180.0,
        MAT_THOMAS
    ),
    "THOMAS_INVERSE": spawn_person(
        "CHAR_THOMAS_INVERSE",
        eval_actor("THOMAS_INVERSE", 0.0),
        180.0,
        MAT_INVERSE
    ),
    "EVA": spawn_person(
        "CHAR_EVA",
        eval_actor("EVA", 0.0),
        170.0,
        MAT_EVA
    ),
    "LEA": spawn_person(
        "CHAR_LEA",
        eval_actor("LEA", 0.0),
        135.0,
        MAT_LEA
    ),
}

ACTOR_HEIGHT_CM = {
    "THOMAS_NORMAL": 180.0,
    "THOMAS_INVERSE": 180.0,
    "EVA": 170.0,
    "LEA": 135.0,
}

HEAD_RADIUS_CM = {
    "THOMAS_NORMAL": 18.0,
    "THOMAS_INVERSE": 18.0,
    "EVA": 17.0,
    "LEA": 15.0,
}


def spawn_head_for_character(character_name, material):
    foot = eval_actor(character_name, 0.0)
    radius = HEAD_RADIUS_CM[character_name]
    head = actors.spawn_actor_from_object(
        SPHERE,
        V(
            foot[0]*100.0,
            foot[1]*100.0,
            foot[2]*100.0 + ACTOR_HEIGHT_CM[character_name] - radius*0.70
        ),
        unreal.Rotator(0, 0, 0),
        False
    )
    label_actor(head, "HEAD_" + character_name, "Personnages/Heads")
    head.set_actor_scale3d(V(radius/50.0, radius/50.0, radius/50.0))
    apply_material(head, material)
    return head


head_objects = {
    "THOMAS_NORMAL": spawn_head_for_character("THOMAS_NORMAL", MAT_THOMAS),
    "THOMAS_INVERSE": spawn_head_for_character("THOMAS_INVERSE", MAT_INVERSE),
    "EVA": spawn_head_for_character("EVA", MAT_EVA),
    "LEA": spawn_head_for_character("LEA", MAT_LEA),
}


def actor_location_from_foot(name, point):
    x, y, z = point
    return (
        x*100.0,
        y*100.0,
        z*100.0 + ACTOR_HEIGHT_CM[name]/2.0
    )


def head_location_from_foot(name, point):
    x, y, z = point
    radius = HEAD_RADIUS_CM[name]
    return (
        x*100.0,
        y*100.0,
        z*100.0 + ACTOR_HEIGHT_CM[name] - radius*0.70
    )


# =============================================================================
# POV PERSONNAGES
# =============================================================================

def _vec_sub(a, b):
    return (
        a[0]-b[0],
        a[1]-b[1],
        a[2]-b[2],
    )


def _vec_len(v):
    return math.sqrt(
        v[0]*v[0] +
        v[1]*v[1] +
        v[2]*v[2]
    )


def _vec_norm(v):
    length = _vec_len(v)

    if length <= 1e-9:
        return (1.0, 0.0, 0.0)

    return (
        v[0]/length,
        v[1]/length,
        v[2]/length,
    )


def pov_story_target(actor_name, t, position):
    """Cible de regard pendant les pauses / moments narratifs."""

    if actor_name == "THOMAS_NORMAL" and t >= NARRATIVE_SECONDS:
        # Tail technique : regard vers la fissure / intérieur, jamais vers l'extérieur.
        return cave_ground_point(max(1.2, _CAVE_AXIS_LEN-1.2), -0.35, 1.1)

    if actor_name == "THOMAS_INVERSE" and t >= NARRATIVE_SECONDS:
        # Tail technique : contrôle du contre-jour vers l'entrée.
        ex, ey, ez = cave_ground_point(0.15, 0.0, 1.55)
        return (ex, ey, ez)

    if actor_name == "THOMAS_NORMAL" and t >= 52.0:
        if t < 57.0:
            return point_with_real_terrain(CAVE_ENTRY_POINT)
        return CAVE_CONTACT_POINT

    if actor_name in ("EVA", "LEA") and 52.0 <= t < 59.3:
        return point_with_real_terrain(CAVE_ZONE_POINT)

    if actor_name == "THOMAS_INVERSE" and t >= 59.0:
        return CAVE_CONTACT_POINT

    if actor_name == "LEA" and 1.0 <= t <= 2.2:
        return (
            B_BRIDGE_POINT[0] + 1.0,
            B_BRIDGE_POINT[1] + 1.0,
            terrain_z_m(B_BRIDGE_POINT[0] + 1.0, B_BRIDGE_POINT[1] + 1.0) + 1.0
        )

    if 1.7 <= t <= 3.2:
        return point_with_real_terrain(A_BRIDGE_POINT)

    return None


def pov_direction(actor_name, t):
    p = eval_actor(actor_name, t)

    # Le tail 62-65 s est un banc de contrôle, pas du temps narratif.
    if t >= NARRATIVE_SECONDS:
        target = pov_story_target(actor_name, t, p)
        if target is not None:
            return _vec_norm(_vec_sub(target, p))

        if actor_name in ("EVA", "LEA"):
            before_tail = eval_actor(actor_name, max(0.0, NARRATIVE_SECONDS-0.6))
            at_end = eval_actor(actor_name, NARRATIVE_SECONDS)
            d = _vec_sub(at_end, before_tail)
            if _vec_len(d) >= 0.05:
                return _vec_norm(d)

    before = eval_actor(actor_name, max(0.0, t-POV_LOOK_AHEAD_SECONDS))
    after = eval_actor(actor_name, min(SEQUENCE_SECONDS, t+POV_LOOK_AHEAD_SECONDS))
    direction = _vec_sub(after, before)

    if _vec_len(direction) < 0.05:
        target = pov_story_target(actor_name, t, p)
        if target is not None:
            direction = _vec_sub(target, p)

    if _vec_len(direction) < 0.05:
        direction = (-1.0, 0.0, 0.0) if actor_name == "THOMAS_INVERSE" else (1.0, 0.0, 0.0)

    return _vec_norm(direction)


def pov_pose(actor_name, t):
    """Position des yeux + rotation CineCamera. V05 garantit un tail sans proxy."""

    foot = eval_actor(actor_name, t)
    direction = pov_direction(actor_name, t)
    eye_height_cm = POV_EYE_HEIGHT_CM[actor_name]

    # Tail technique : les POV Thomas sont déplacés vers deux points sûrs
    # dans le couloir central afin d'éviter tête/proxy/paroi au contact.
    if t >= NARRATIVE_SECONDS and actor_name in ("THOMAS_NORMAL", "THOMAS_INVERSE"):
        if actor_name == "THOMAS_NORMAL":
            sx, sy, sz = cave_ground_point(max(1.4, _CAVE_AXIS_LEN-1.55), -0.55, 1.62)
        else:
            sx, sy, sz = cave_ground_point(max(0.8, _CAVE_AXIS_LEN-2.15), 0.65, 1.62)

        pos = V(sx*100.0, sy*100.0, sz*100.0)
        target = pov_story_target(actor_name, t, foot)
        look = V(target[0]*100.0, target[1]*100.0, target[2]*100.0)
        return pos, unreal.MathLibrary.find_look_at_rotation(pos, look)

    # POV V07 : placement "tête/épaule" lisible.
    # La direction 3D pilote le REGARD ; la position avance dans XY afin qu'une
    # pente forte ne ramène jamais la caméra dans la tête du personnage.
    side_sign = -1.0 if actor_name == "THOMAS_NORMAL" else 1.0
    flat_len = math.hypot(direction[0], direction[1])

    if flat_len < 1e-6:
        before_flat = eval_actor(actor_name, max(0.0, t-POV_LOOK_AHEAD_SECONDS))
        after_flat = eval_actor(actor_name, min(SEQUENCE_SECONDS, t+POV_LOOK_AHEAD_SECONDS))
        fdx = after_flat[0] - before_flat[0]
        fdy = after_flat[1] - before_flat[1]
        flat_len = math.hypot(fdx, fdy)

        if flat_len < 1e-6:
            fdx, fdy, flat_len = 1.0, 0.0, 1.0

        flat_forward = (fdx/flat_len, fdy/flat_len, 0.0)
    else:
        flat_forward = (direction[0]/flat_len, direction[1]/flat_len, 0.0)

    lateral = (-flat_forward[1], flat_forward[0], 0.0)
    pitch_lift_cm = max(-8.0, min(8.0, direction[2]*10.0))

    # Décalage latéral normal : 14 cm. Si un autre personnage est très proche
    # du POV, tester plusieurs positions d'épaule et choisir celle qui maximise
    # la distance au proxy le plus proche. Cela évite les cylindres géants dans
    # l'image aux moments où le groupe est compact (notamment ~3-4 s).
    default_lateral_cm = 14.0 * side_sign
    chosen_lateral_cm = default_lateral_cm

    base_x_cm = foot[0]*100.0 + flat_forward[0]*POV_FORWARD_OFFSET_CM
    base_y_cm = foot[1]*100.0 + flat_forward[1]*POV_FORWARD_OFFSET_CM
    eye_z_cm = foot[2]*100.0 + eye_height_cm + pitch_lift_cm

    peers = []
    for other_name in ("THOMAS_NORMAL", "THOMAS_INVERSE", "EVA", "LEA"):
        if other_name == actor_name:
            continue
        other = eval_actor(other_name, t)
        peers.append((other[0]*100.0, other[1]*100.0, other[2]*100.0))

    def peer_clearance_cm(lat_cm):
        cx = base_x_cm + lateral[0]*lat_cm
        cy = base_y_cm + lateral[1]*lat_cm
        if not peers:
            return 99999.0
        return min(
            math.hypot(cx-px, cy-py)
            for px, py, pz in peers
        )

    base_clearance = peer_clearance_cm(default_lateral_cm)

    if base_clearance < 135.0:
        candidates = (
            default_lateral_cm,
            -default_lateral_cm,
            28.0, -28.0,
            45.0, -45.0,
            62.0, -62.0,
            78.0, -78.0,
        )

        best_score = -1.0e30
        best_lat = default_lateral_cm

        for lat_cm in candidates:
            clearance = peer_clearance_cm(lat_cm)
            # Petite pénalité pour conserver une sensation de POV humain :
            # on ne s'écarte fortement que si cela libère réellement l'image.
            score = clearance - 0.12*abs(lat_cm-default_lateral_cm)
            if score > best_score:
                best_score = score
                best_lat = lat_cm

        chosen_lateral_cm = best_lat

    pos = V(
        base_x_cm + lateral[0]*chosen_lateral_cm,
        base_y_cm + lateral[1]*chosen_lateral_cm,
        eye_z_cm
    )

    look = V(
        pos.x + direction[0]*1000.0,
        pos.y + direction[1]*1000.0,
        pos.z + direction[2]*1000.0
    )

    rotation = unreal.MathLibrary.find_look_at_rotation(pos, look)
    return pos, rotation


def unwrap_angle(previous, current):
    if previous is None:
        return current

    value = current

    while value-previous > 180.0:
        value -= 360.0

    while value-previous < -180.0:
        value += 360.0

    return value


# =============================================================================
# CAMERAS DE CONTROLE + POV
# =============================================================================

def create_camera(name, pos, target, focal=35.0):
    cam = actors.spawn_actor_from_class(
        unreal.CineCameraActor,
        pos,
        unreal.Rotator(0, 0, 0),
        False
    )

    label_actor(cam, "CAM_" + name, "Cameras")

    cam.set_actor_rotation(
        unreal.MathLibrary.find_look_at_rotation(
            pos,
            target
        ),
        False
    )

    try:
        cam.get_cine_camera_component().set_current_focal_length(float(focal))
    except Exception:
        pass

    return cam


overview_center = linear_point(
    point_with_real_terrain(CONVERGENCE_POINT),
    point_with_real_terrain(HIGH_POINT),
    0.5
)

cam_overview = create_camera(
    "OVERVIEW_TIMELINE",
    V(
        overview_center[0]*100 - 50000,
        overview_center[1]*100 - 85000,
        overview_center[2]*100 + 60000
    ),
    V(
        overview_center[0]*100,
        overview_center[1]*100,
        overview_center[2]*100
    ),
    35.0
)

cam_convergence = create_camera(
    "17H00_CONVERGENCE",
    V(
        conv_x*100 - 1800,
        conv_y*100 - 1800,
        terrain_z_m(conv_x, conv_y)*100 + 450
    ),
    V(
        conv_x*100,
        conv_y*100,
        terrain_z_m(conv_x, conv_y)*100 + 150
    ),
    45.0
)

guard_x, guard_y, guard_z = CAVE_GUARD_POINT

cam_cave_guard = create_camera(
    "CAVE_GUARD_LINE",
    V(
        guard_x*100 - 500,
        guard_y*100 - 350,
        terrain_z_m(guard_x, guard_y)*100 + 180
    ),
    V(CAVE_ZONE_POINT[0]*100, CAVE_ZONE_POINT[1]*100, CAVE_ZONE_POINT[2]*100 + 120),
    35.0
)

# Révélation depuis l'extérieur, mais hors de l'axe des rochers d'entrée.
_rev_x, _rev_y = cave_xy(-3.0, 0.0)
_rev_z = terrain_z_m(_rev_x, _rev_y) + 1.85
_rev_target = cave_ground_point(0.75, 0.0, 1.35)
cam_cave_reveal = create_camera(
    "CAVE_REVEAL",
    V(_rev_x*100, _rev_y*100, _rev_z*100),
    V(_rev_target[0]*100, _rev_target[1]*100, _rev_target[2]*100),
    32.0
)

# Master final : depuis le premier tiers du couloir, légèrement latéral,
# donc jamais dans un mur et jamais au même point qu'un personnage.
_final_x, _final_y = cave_xy(1.25, -0.85)
_final_z = terrain_z_m(_final_x, _final_y) + 1.70
_final_target = cave_ground_point(max(2.2, _CAVE_AXIS_LEN-0.65), 0.10, 1.10)
cam_final_cave = create_camera(
    "FINAL_CAVE_MASTER",
    V(_final_x*100, _final_y*100, _final_z*100),
    V(_final_target[0]*100, _final_target[1]*100, _final_target[2]*100),
    28.0
)

# Contre-jour : depuis le fond, légèrement latéral, vers l'ouverture.
_back_x, _back_y = cave_xy(max(2.8, _CAVE_AXIS_LEN-0.75), 0.85)
_back_z = terrain_z_m(_back_x, _back_y) + 1.62
_back_target = cave_ground_point(0.05, -0.10, 1.55)
cam_cave_backlight = create_camera(
    "CAVE_BACKLIGHT_REVIEW",
    V(_back_x*100, _back_y*100, _back_z*100),
    V(_back_target[0]*100, _back_target[1]*100, _back_target[2]*100),
    30.0
)

# Vue verticale de debug de la micro-caverne : utile si un POV semble encore
# incohérent. Elle montre l'axe libre, les deux murs et le point de contact.
_top_x, _top_y = cave_xy(_CAVE_AXIS_LEN*0.5, 0.0)
_top_z = terrain_z_m(_top_x, _top_y) + 10.0
cam_cave_top = create_camera(
    "CAVE_TOP_DEBUG",
    V(_top_x*100, _top_y*100, _top_z*100),
    V(_top_x*100, _top_y*100, terrain_z_m(_top_x, _top_y)*100),
    35.0
)


# Les POV ne créent PAS de nouvelles séquences.
# Ils sont tous keyés dans LS_POLOP_ANIMATION_V05.
pov_cameras = {}

for pov_character in (
    "THOMAS_NORMAL",
    "THOMAS_INVERSE",
    "EVA",
    "LEA",
):
    initial_pos, initial_rot = pov_pose(
        pov_character,
        0.0
    )

    camera_actor = actors.spawn_actor_from_class(
        unreal.CineCameraActor,
        initial_pos,
        initial_rot,
        False
    )

    label_actor(
        camera_actor,
        "CAM_POV_" + pov_character,
        "Cameras/POV"
    )

    try:
        camera_actor.get_cine_camera_component().set_current_focal_length(
            POV_FOCAL_MM
        )
    except Exception:
        pass

    pov_cameras[pov_character] = camera_actor


# =============================================================================
# LEVEL SEQUENCE
# =============================================================================

sequence_asset_path = "/Game/POLOP/Generated_V09/Sequences"
sequence_name = "LS_POLOP_ANIMATION_V05"
sequence_full_path = sequence_asset_path + "/" + sequence_name

unreal.EditorAssetLibrary.make_directory(sequence_asset_path)

# V05 remplace les anciennes séquences Animation dans le Content Browser.
for obsolete_sequence in (
    "/Game/POLOP/Generated_V09/Sequences/LS_POLOP_ANIMATION_V01",
    "/Game/POLOP/Generated_V09/Sequences/LS_POLOP_ANIMATION_V02",
    "/Game/POLOP/Generated_V09/Sequences/LS_POLOP_ANIMATION_V03",
    "/Game/POLOP/Generated_V09/Sequences/LS_POLOP_ANIMATION_V04",
    sequence_full_path,
):
    if unreal.EditorAssetLibrary.does_asset_exist(
        obsolete_sequence
    ):
        unreal.EditorAssetLibrary.delete_asset(
            obsolete_sequence
        )

sequence = asset_tools.create_asset(
    sequence_name,
    sequence_asset_path,
    unreal.LevelSequence,
    unreal.LevelSequenceFactoryNew()
)

if not sequence:
    raise RuntimeError("Impossible de créer la Level Sequence Animation V05.")

sequence.set_display_rate(
    unreal.FrameRate(numerator=FPS, denominator=1)
)
sequence.set_playback_start(0)
sequence.set_playback_end(int(round(SEQUENCE_SECONDS*FPS)))
# Corrige l'ouverture déroutante avec des milliers de frames négatives.
# Ces méthodes sont documentées sur MovieSceneSequence et utilisent des secondes.
try:
    sequence.set_view_range_start(0.0)
    sequence.set_view_range_end(SEQUENCE_SECONDS)
    sequence.set_work_range_start(0.0)
    sequence.set_work_range_end(SEQUENCE_SECONDS)
except Exception as exc:
    unreal.log_warning("ANIMATION V05 view/work range : %s" % exc)

# Ouvre le Sequencer avant d'utiliser LevelSequenceEditorSubsystem.add_actors.
unreal.LevelSequenceEditorBlueprintLibrary.open_level_sequence(sequence)
ls_system = unreal.get_editor_subsystem(
    unreal.LevelSequenceEditorSubsystem
)

try:
    unreal.LevelSequenceEditorBlueprintLibrary.set_lock_camera_cut_to_viewport(False)
except Exception:
    pass

try:
    unreal.LevelSequenceEditorBlueprintLibrary.set_current_time(0)
except Exception:
    pass

try:
    unreal.LevelSequenceEditorBlueprintLibrary.set_selection_range_start(0)
    unreal.LevelSequenceEditorBlueprintLibrary.set_selection_range_end(int(round(SEQUENCE_SECONDS*FPS)))
except Exception:
    pass


def add_transform_animation(actor_name, actor):
    bindings = ls_system.add_actors([actor])

    if not bindings:
        raise RuntimeError(
            "Impossible de binder %s dans Sequencer." % actor_name
        )

    binding = bindings[0]

    track = binding.add_track(
        unreal.MovieScene3DTransformTrack
    )

    section = track.add_section()
    try:
        section.set_completion_mode(unreal.MovieSceneCompletionMode.KEEP_STATE)
    except Exception:
        pass
    section.set_range(
        0,
        int(round(SEQUENCE_SECONDS*FPS))
    )

    channels = section.get_all_channels()

    # UE 5.8 : Transform = 9 double channels.
    channel_map = {}

    for channel in channels:
        try:
            name = str(channel.channel_name)
        except Exception:
            name = ""

        channel_map[name] = channel

    # Fallback par ordre officiel : Location XYZ, Rotation XYZ, Scale XYZ.
    if len(channels) >= 9:
        ordered = {
            "Location.X": channels[0],
            "Location.Y": channels[1],
            "Location.Z": channels[2],
            "Rotation.X": channels[3],
            "Rotation.Y": channels[4],
            "Rotation.Z": channels[5],
            "Scale.X": channels[6],
            "Scale.Y": channels[7],
            "Scale.Z": channels[8],
        }

        for key, value in ordered.items():
            if key not in channel_map:
                channel_map[key] = value

    xch = channel_map.get("Location.X", channels[0])
    ych = channel_map.get("Location.Y", channels[1])
    zch = channel_map.get("Location.Z", channels[2])

    # Conserve explicitement rotation et échelle des proxies.
    # Sans cela, un Transform Track peut réévaluer les defaults à 0/1.
    try:
        rot = actor.get_actor_rotation()
        scl = actor.get_actor_scale3d()

        channel_map.get("Rotation.X", channels[3]).set_default(float(rot.roll))
        channel_map.get("Rotation.Y", channels[4]).set_default(float(rot.pitch))
        channel_map.get("Rotation.Z", channels[5]).set_default(float(rot.yaw))

        channel_map.get("Scale.X", channels[6]).set_default(float(scl.x))
        channel_map.get("Scale.Y", channels[7]).set_default(float(scl.y))
        channel_map.get("Scale.Z", channels[8]).set_default(float(scl.z))
    except Exception:
        pass

    # À 18h00, ne pas donner l'impression d'une duplication : le proxy inversé
    # disparaît visuellement au point où la worldline se retourne.
    if actor_name == "THOMAS_INVERSE":
        try:
            sx = channel_map.get("Scale.X", channels[6])
            sy = channel_map.get("Scale.Y", channels[7])
            sz = channel_map.get("Scale.Z", channels[8])
            current_scale = actor.get_actor_scale3d()
            for ch, value in (
                (sx, float(current_scale.x)),
                (sy, float(current_scale.y)),
                (sz, float(current_scale.z)),
            ):
                ch.add_key(
                    unreal.FrameNumber(CONTACT_PREV_FRAME),
                    value,
                    interpolation=unreal.MovieSceneKeyInterpolation.LINEAR
                )
                ch.add_key(
                    unreal.FrameNumber(CONTACT_FRAME),
                    CONTACT_HIDDEN_SCALE,
                    interpolation=unreal.MovieSceneKeyInterpolation.LINEAR
                )
        except Exception as exc:
            unreal.log_warning("ANIMATION V05 contact merge body: %s" % exc)

    # Proxies cylindriques : orientation volontairement non keyée.
    t = 0.0

    while t < SEQUENCE_SECONDS + 1e-6:
        p = eval_actor(actor_name, t)
        x, y, z = actor_location_from_foot(actor_name, p)
        frame = unreal.FrameNumber(int(round(t*FPS)))

        xch.add_key(
            frame,
            float(x),
            interpolation=unreal.MovieSceneKeyInterpolation.LINEAR
        )
        ych.add_key(
            frame,
            float(y),
            interpolation=unreal.MovieSceneKeyInterpolation.LINEAR
        )
        zch.add_key(
            frame,
            float(z),
            interpolation=unreal.MovieSceneKeyInterpolation.LINEAR
        )

        t += SAMPLE_SECONDS

    # Garantit la dernière clé exacte.
    p = eval_actor(actor_name, SEQUENCE_SECONDS)
    x, y, z = actor_location_from_foot(actor_name, p)
    frame = unreal.FrameNumber(int(round(SEQUENCE_SECONDS*FPS)))

    xch.add_key(
        frame,
        float(x),
        interpolation=unreal.MovieSceneKeyInterpolation.LINEAR
    )
    ych.add_key(
        frame,
        float(y),
        interpolation=unreal.MovieSceneKeyInterpolation.LINEAR
    )
    zch.add_key(
        frame,
        float(z),
        interpolation=unreal.MovieSceneKeyInterpolation.LINEAR
    )

    return binding


def add_pov_camera_animation(
    character_name,
    camera_actor
):
    bindings = ls_system.add_actors(
        [camera_actor]
    )

    if not bindings:
        raise RuntimeError(
            "Impossible de binder POV %s."
            % character_name
        )

    binding = bindings[0]

    track = binding.add_track(
        unreal.MovieScene3DTransformTrack
    )

    section = track.add_section()
    try:
        section.set_completion_mode(unreal.MovieSceneCompletionMode.KEEP_STATE)
    except Exception:
        pass
    section.set_range(
        0,
        int(round(SEQUENCE_SECONDS*FPS))
    )

    channels = section.get_all_channels()

    if len(channels) < 9:
        raise RuntimeError(
            "Transform POV incomplet %s : %d channels."
            % (
                character_name,
                len(channels)
            )
        )

    xch, ych, zch = (
        channels[0],
        channels[1],
        channels[2]
    )

    rxch, rych, rzch = (
        channels[3],
        channels[4],
        channels[5]
    )

    sxch, sych, szch = (
        channels[6],
        channels[7],
        channels[8]
    )

    try:
        scale = camera_actor.get_actor_scale3d()
        sxch.set_default(float(scale.x))
        sych.set_default(float(scale.y))
        szch.set_default(float(scale.z))
    except Exception:
        pass

    previous_roll = None
    previous_pitch = None
    previous_yaw = None

    t = 0.0

    while t < SEQUENCE_SECONDS + 1e-6:
        pos, rot = pov_pose(
            character_name,
            t
        )

        frame = unreal.FrameNumber(
            int(round(t*FPS))
        )

        roll = unwrap_angle(
            previous_roll,
            float(rot.roll)
        )
        pitch = unwrap_angle(
            previous_pitch,
            float(rot.pitch)
        )
        yaw = unwrap_angle(
            previous_yaw,
            float(rot.yaw)
        )

        xch.add_key(
            frame,
            float(pos.x),
            interpolation=unreal.MovieSceneKeyInterpolation.LINEAR
        )
        ych.add_key(
            frame,
            float(pos.y),
            interpolation=unreal.MovieSceneKeyInterpolation.LINEAR
        )
        zch.add_key(
            frame,
            float(pos.z),
            interpolation=unreal.MovieSceneKeyInterpolation.LINEAR
        )

        rxch.add_key(
            frame,
            roll,
            interpolation=unreal.MovieSceneKeyInterpolation.LINEAR
        )
        rych.add_key(
            frame,
            pitch,
            interpolation=unreal.MovieSceneKeyInterpolation.LINEAR
        )
        rzch.add_key(
            frame,
            yaw,
            interpolation=unreal.MovieSceneKeyInterpolation.LINEAR
        )

        previous_roll = roll
        previous_pitch = pitch
        previous_yaw = yaw

        t += POV_SAMPLE_SECONDS

    # Dernière clé exacte.
    pos, rot = pov_pose(
        character_name,
        SEQUENCE_SECONDS
    )

    frame = unreal.FrameNumber(
        int(round(SEQUENCE_SECONDS*FPS))
    )

    roll = unwrap_angle(
        previous_roll,
        float(rot.roll)
    )
    pitch = unwrap_angle(
        previous_pitch,
        float(rot.pitch)
    )
    yaw = unwrap_angle(
        previous_yaw,
        float(rot.yaw)
    )

    xch.add_key(
        frame,
        float(pos.x),
        interpolation=unreal.MovieSceneKeyInterpolation.LINEAR
    )
    ych.add_key(
        frame,
        float(pos.y),
        interpolation=unreal.MovieSceneKeyInterpolation.LINEAR
    )
    zch.add_key(
        frame,
        float(pos.z),
        interpolation=unreal.MovieSceneKeyInterpolation.LINEAR
    )
    rxch.add_key(
        frame,
        roll,
        interpolation=unreal.MovieSceneKeyInterpolation.LINEAR
    )
    rych.add_key(
        frame,
        pitch,
        interpolation=unreal.MovieSceneKeyInterpolation.LINEAR
    )
    rzch.add_key(
        frame,
        yaw,
        interpolation=unreal.MovieSceneKeyInterpolation.LINEAR
    )

    return binding



def add_head_animation(character_name, head_actor):
    bindings = ls_system.add_actors([head_actor])
    if not bindings:
        raise RuntimeError("Impossible de binder head %s." % character_name)
    binding = bindings[0]
    track = binding.add_track(unreal.MovieScene3DTransformTrack)
    section = track.add_section()
    try:
        section.set_completion_mode(unreal.MovieSceneCompletionMode.KEEP_STATE)
    except Exception:
        pass
    section.set_range(0, int(round(SEQUENCE_SECONDS*FPS)))
    channels = section.get_all_channels()
    if len(channels) < 9:
        raise RuntimeError("Transform head incomplet %s." % character_name)

    xch, ych, zch = channels[0], channels[1], channels[2]
    try:
        scale = head_actor.get_actor_scale3d()
        channels[3].set_default(0.0)
        channels[4].set_default(0.0)
        channels[5].set_default(0.0)
        channels[6].set_default(float(scale.x))
        channels[7].set_default(float(scale.y))
        channels[8].set_default(float(scale.z))

        if character_name == "THOMAS_INVERSE":
            for ch, value in (
                (channels[6], float(scale.x)),
                (channels[7], float(scale.y)),
                (channels[8], float(scale.z)),
            ):
                ch.add_key(
                    unreal.FrameNumber(CONTACT_PREV_FRAME),
                    value,
                    interpolation=unreal.MovieSceneKeyInterpolation.LINEAR
                )
                ch.add_key(
                    unreal.FrameNumber(CONTACT_FRAME),
                    CONTACT_HIDDEN_SCALE,
                    interpolation=unreal.MovieSceneKeyInterpolation.LINEAR
                )
    except Exception:
        pass

    t = 0.0
    while t < SEQUENCE_SECONDS + 1e-6:
        point = eval_actor(character_name, t)
        x, y, z = head_location_from_foot(character_name, point)
        frame = unreal.FrameNumber(int(round(t*FPS)))
        xch.add_key(frame, float(x), interpolation=unreal.MovieSceneKeyInterpolation.LINEAR)
        ych.add_key(frame, float(y), interpolation=unreal.MovieSceneKeyInterpolation.LINEAR)
        zch.add_key(frame, float(z), interpolation=unreal.MovieSceneKeyInterpolation.LINEAR)
        t += SAMPLE_SECONDS

    return binding


sequence_bindings = {}
sequence_errors = []
head_bindings = {}
head_errors = []
pov_bindings = {}
pov_errors = []

for name, actor in actor_objects.items():
    try:
        sequence_bindings[name] = add_transform_animation(name, actor)
        unreal.log("ANIMATION V05 SEQUENCER OK : " + name)
    except Exception as exc:
        sequence_errors.append(
            "%s : %s" % (name, exc)
        )
        unreal.log_error(
            "ANIMATION V05 SEQUENCER FAIL %s : %s"
            % (name, exc)
        )

for name, head_actor in head_objects.items():
    try:
        head_bindings[name] = add_head_animation(name, head_actor)
        unreal.log("ANIMATION V05 HEAD OK : " + name)
    except Exception as exc:
        head_errors.append("%s : %s" % (name, exc))
        unreal.log_error("ANIMATION V05 HEAD FAIL %s : %s" % (name, exc))

for name, camera_actor in pov_cameras.items():
    try:
        pov_bindings[name] = add_pov_camera_animation(
            name,
            camera_actor
        )
        unreal.log(
            "ANIMATION V05 POV OK : " + name
        )
    except Exception as exc:
        pov_errors.append(
            "%s : %s" % (name, exc)
        )
        unreal.log_error(
            "ANIMATION V05 POV FAIL %s : %s"
            % (name, exc)
        )

try:
    unreal.LevelSequenceEditorBlueprintLibrary.refresh_current_level_sequence()
except Exception:
    pass

try:
    unreal.EditorAssetLibrary.save_loaded_asset(sequence)
except Exception:
    pass


# =============================================================================
# MODELE JSON / RAPPORT DES HYPOTHESES
# =============================================================================

events = [
    {
        "time": "16h58",
        "seq_second": 0.0,
        "source": "A1",
        "event": "Début randonnée ; Léa légèrement devant près du pont."
    },
    {
        "time": "16h59",
        "seq_second": 1.0,
        "source": "A1",
        "event": "Léa atteint B par le pont."
    },
    {
        "time": "17h00",
        "seq_second": 2.0,
        "source": "A2 / B7 / B8 / B9",
        "event": "Convergence Thomas normal / inversé + fermeture ; Léa côté B."
    },
    {
        "time": "17h01",
        "seq_second": 3.0,
        "source": "B6",
        "event": "Lecture objective : Thomas inversé traverse A -> B ; temps propre : B -> A."
    },
    {
        "time": "17h30",
        "seq_second": 32.0,
        "source": "A9 / B5",
        "event": "Groupe plus haut sur A ; Thomas inversé sur B à portée visuelle du pont."
    },
    {
        "time": "17h50",
        "seq_second": 52.0,
        "source": "A10",
        "event": "Thomas quitte A de quelques mètres ; Eva/Léa restent au passage."
    },
    {
        "time": "17h55",
        "seq_second": 57.0,
        "source": "A12/A13",
        "event": "Eva/Léa entrent dans la petite zone pour chercher."
    },
    {
        "time": "17h57–17h58",
        "seq_second": 59.0,
        "source": "A15 / B1 / B2",
        "event": "Eva/Léa redescendent ; coexistence des deux Thomas près/dans la caverne."
    },
    {
        "time": "18h00",
        "seq_second": 62.0,
        "source": "A17",
        "event": "Contact : Thomas normal et inversé convergent sur le même point de worldline."
    },
]

assumptions = [
    {
        "id": "A_V05_01",
        "value": "Convergence 17h00 placée 25 m avant le pont sur A.",
        "reason": "B6=17h01 puis B7/B8≈17h00 impose une distance marchable en ~1 minute.",
        "canon": False
    },
    {
        "id": "A_V05_02",
        "value": "Léa termine le flanc vers 17h06.",
        "reason": "Script_POLOP ne donne pas l'heure exacte de son retour sur A.",
        "canon": False
    },
    {
        "id": "A_V05_03",
        "value": "Micro-zone caverne ~8x6 m à ~quelques mètres de la jonction haute.",
        "reason": "Script_POLOP impose une petite zone de quelques dizaines de m² mais pas de dimensions exactes.",
        "canon": False
    },
    {
        "id": "A_V05_04",
        "value": "À 17h30 Thomas inversé est environ 800 m au-dessus du pont sur B.",
        "reason": "B5 dit seulement 'à portée visuelle du pont'.",
        "canon": False
    },
]

animation_out_dir = os.path.join(
    saved_dir,
    "POLOP",
    "ANIMATION_V05"
)
os.makedirs(animation_out_dir, exist_ok=True)

animation_model = {
    "source_narrative": "Script_POLOP.md",
    "geography_base": "V11",
    "timeline": {
        "objective_start": "16h58",
        "objective_end": "18h00",
        "minutes": 62,
        "sequencer_seconds": SEQUENCE_SECONDS,
        "narrative_end_second": NARRATIVE_SECONDS,
        "review_tail_seconds": REVIEW_TAIL_SECONDS,
        "mapping": "1 objective minute = 1 sequencer second",
        "fps": FPS,
    },
    "narrative_repairs_from_v11": {
        "old_convergence_marker_invalid_for_B6_B8": True,
        "new_convergence_station_A_m": CONVERGENCE_STATION,
        "bridge_station_A_m": A_BRIDGE_STATION,
        "bridge_to_convergence_m": A_BRIDGE_STATION-CONVERGENCE_STATION,
        "old_cave_access_route_m": LENGTH.get("GROTTE"),
        "micro_cave_distance_from_high_m": math.dist(
            HIGH_POINT,
            CAVE_ENTRY_POINT
        ),
    },
    "events": events,
    "assumptions": assumptions,
    "sequence_asset": sequence_full_path,
    "sequencer_errors": sequence_errors,
    "head_errors": head_errors,
    "pov_errors": pov_errors,
    "pov": {
        "camera_labels": {
            name: "PZ_ANIM_CAM_POV_" + name
            for name in pov_cameras.keys()
        },
        "focal_mm": POV_FOCAL_MM,
        "eye_height_cm": POV_EYE_HEIGHT_CM,
        "forward_offset_cm": POV_FORWARD_OFFSET_CM,
        "sample_seconds": POV_SAMPLE_SECONDS,
        "critical_times_seconds": [
            2.0, 3.0, 32.0, 52.0,
            57.0, 60.0, 61.0, 62.0, 65.0
        ],
    },
    "segments": ANIM,
}

model_path = os.path.join(
    animation_out_dir,
    "animation_model_v05.json"
)

with open(model_path, "w", encoding="utf-8") as f:
    json.dump(
        animation_model,
        f,
        indent=2,
        ensure_ascii=False
    )

# Sélectionne l'overview au départ.
actors.set_selected_level_actors([cam_overview])


# =============================================================================
# AUTO-VALIDATION V05 — INTEGREE
# =============================================================================

def _distance(a, b):
    return math.dist(a, b)


validation_checks = []


def _check(name, ok, **details):
    item = {
        "name": name,
        "status": "OK" if ok else "FAIL"
    }
    item.update(details)
    validation_checks.append(item)


closure_delta = _distance(
    eval_actor("THOMAS_NORMAL", 2.0),
    eval_actor("THOMAS_INVERSE", 2.0)
)

contact_delta = _distance(
    eval_actor("THOMAS_NORMAL", 62.0),
    eval_actor("THOMAS_INVERSE", 62.0)
)

pre_contact_60 = _distance(
    eval_actor("THOMAS_NORMAL", 60.0),
    eval_actor("THOMAS_INVERSE", 60.0)
)

pre_contact_61 = _distance(
    eval_actor("THOMAS_NORMAL", 61.0),
    eval_actor("THOMAS_INVERSE", 61.0)
)

_check(
    "closure_17h00",
    closure_delta <= 0.75,
    delta_m=closure_delta
)

_check(
    "contact_18h00",
    contact_delta <= 0.25,
    delta_m=contact_delta
)


final_normal_65 = eval_actor("THOMAS_NORMAL", SEQUENCE_SECONDS)
final_inverse_65 = eval_actor("THOMAS_INVERSE", SEQUENCE_SECONDS)
final_hold_normal_delta = _distance(final_normal_65, CAVE_CONTACT_POINT)
final_hold_inverse_delta = _distance(final_inverse_65, CAVE_CONTACT_POINT)

_check(
    "thomas_normal_visible_in_cave_at_sim_end",
    final_hold_normal_delta <= 0.25,
    delta_m=final_hold_normal_delta
)

_check(
    "thomas_inverse_visible_in_cave_at_sim_end",
    final_hold_inverse_delta <= 0.25,
    delta_m=final_hold_inverse_delta
)

_check(
    "two_thomas_separate_before_18h00",
    pre_contact_60 >= 1.0
    and pre_contact_61 >= 0.75,
    separation_1758_m=pre_contact_60,
    separation_1759_m=pre_contact_61
)

_check(
    "convergence_near_bridge",
    (A_BRIDGE_STATION-CONVERGENCE_STATION) <= 40.0,
    distance_m=(
        A_BRIDGE_STATION-
        CONVERGENCE_STATION
    )
)

_check(
    "micro_cave_near_high_path",
    math.dist(
        HIGH_POINT,
        CAVE_ENTRY_POINT
    ) <= 25.0,
    distance_m=math.dist(
        HIGH_POINT,
        CAVE_ENTRY_POINT
    )
)

lea_flank_segments = [
    segment
    for segment in ANIM["LEA"]
    if (
        segment["type"] == "station"
        and segment.get("route") == "FLANC"
    )
]

lea_flank_ok = (
    len(lea_flank_segments) == 1
    and lea_flank_segments[0]["s1"]
    > lea_flank_segments[0]["s0"]
)

_check(
    "lea_returns_via_flank",
    lea_flank_ok
)

sep_1730 = _distance(
    eval_actor("THOMAS_NORMAL", 32.0),
    eval_actor("THOMAS_INVERSE", 32.0)
)

_check(
    "A_B_separation_17h30",
    sep_1730 >= 150.0,
    distance_m=sep_1730
)

_check(
    "four_character_bindings",
    len(sequence_bindings) == 4
    and not sequence_errors,
    count=len(sequence_bindings),
    errors=sequence_errors
)


_check(
    "four_readable_head_bindings",
    len(head_bindings) == 4
    and not head_errors,
    count=len(head_bindings),
    errors=head_errors
)

_check(
    "four_pov_bindings",
    len(pov_bindings) == 4
    and not pov_errors,
    count=len(pov_bindings),
    errors=pov_errors
)

# Contrôles spécifiques V05 : la fin doit être lisible et les POV du tail stables.
# V05 ajoute un shell de caverne dont le centre reste explicitement libre.
final_normal_dir = pov_direction("THOMAS_NORMAL", 64.0)
final_inverse_dir = pov_direction("THOMAS_INVERSE", 64.0)
final_eva_dir = pov_direction("EVA", 64.0)

_check(
    "final_pov_directions_stable",
    _vec_len(final_normal_dir) > 0.9
    and _vec_len(final_inverse_dir) > 0.9
    and _vec_len(final_eva_dir) > 0.9,
    thomas_normal=final_normal_dir,
    thomas_inverse=final_inverse_dir,
    eva=final_eva_dir
)

_check(
    "single_visual_thomas_at_contact_policy",
    CONTACT_HIDDEN_SCALE <= 0.01,
    contact_frame=CONTACT_FRAME,
    hidden_scale=CONTACT_HIDDEN_SCALE
)

pov_labels_expected = {
    "PZ_ANIM_CAM_POV_THOMAS_NORMAL",
    "PZ_ANIM_CAM_POV_THOMAS_INVERSE",
    "PZ_ANIM_CAM_POV_EVA",
    "PZ_ANIM_CAM_POV_LEA",
}

current_labels = set()

for level_actor in actors.get_all_level_actors():
    try:
        current_labels.add(
            level_actor.get_actor_label()
        )
    except Exception:
        pass

missing_pov = sorted(
    pov_labels_expected-current_labels
)

_check(
    "four_pov_cameras_exist",
    not missing_pov,
    missing=missing_pov
)

_check(
    "final_pose_review_tail_present",
    SEQUENCE_SECONDS >= NARRATIVE_SECONDS + 3.0,
    narrative_end_s=NARRATIVE_SECONDS,
    review_end_s=SEQUENCE_SECONDS
)

# Vérifie que le POV reste près du niveau des yeux.
pov_offsets = {}

for name in pov_cameras.keys():
    values = []

    for t in (
        2.0, 32.0, 52.0, 57.0,
        60.0, 61.0
    ):
        foot = eval_actor(name, t)
        pos, _ = pov_pose(name, t)

        eye_center = (
            foot[0]*100.0,
            foot[1]*100.0,
            foot[2]*100.0 +
            POV_EYE_HEIGHT_CM[name]
        )

        values.append(
            math.dist(
                (pos.x, pos.y, pos.z),
                eye_center
            )
        )

    pov_offsets[name] = {
        "min_cm": min(values),
        "max_cm": max(values),
    }

pov_offset_ok = all(
    20.0 <= values["min_cm"]
    and values["max_cm"] <= 95.0
    for values in pov_offsets.values()
)

_check(
    "pov_eye_offsets_reasonable",
    pov_offset_ok,
    offsets=pov_offsets
)

# Le tail technique des deux Thomas doit être clairement hors du point de contact
# afin qu'aucun POV ne se retrouve dans la tête / le cylindre de l'autre proxy.
_tail_clearance = {}
for _name in ("THOMAS_NORMAL", "THOMAS_INVERSE"):
    _pos, _rot = pov_pose(_name, 64.0)
    _contact_eye = (
        CAVE_CONTACT_POINT[0]*100.0,
        CAVE_CONTACT_POINT[1]*100.0,
        CAVE_CONTACT_POINT[2]*100.0 + POV_EYE_HEIGHT_CM[_name]
    )
    _tail_clearance[_name] = math.dist(
        (_pos.x, _pos.y, _pos.z),
        _contact_eye
    )

_check(
    "tail_thomas_pov_clear_of_contact",
    all(v >= 100.0 for v in _tail_clearance.values()),
    clearance_cm=_tail_clearance
)

# Les deux caméras maîtres intérieures restent dans le couloir libre (|side|<1m).
_check(
    "cave_review_cameras_in_clear_lane",
    abs(-0.85) < 1.0 and abs(0.85) < 1.0,
    final_side_m=-0.85,
    backlight_side_m=0.85,
    wall_side_m=2.35
)

validation_overall = (
    "OK"
    if all(
        item["status"] == "OK"
        for item in validation_checks
    )
    else "FAIL"
)

validation_dir = os.path.join(
    animation_out_dir,
    "validation"
)
os.makedirs(validation_dir, exist_ok=True)

validation_json_path = os.path.join(
    validation_dir,
    "validation_animation_v05.json"
)

validation_txt_path = os.path.join(
    validation_dir,
    "validation_animation_v05.txt"
)

validation_report = {
    "overall": validation_overall,
    "source_narrative": "Script_POLOP.md",
    "geography_base": "V11",
    "sequence_asset": sequence_full_path,
    "checks": validation_checks,
    "pov": animation_model["pov"],
    "visual_review": {
        "how_to": (
            "Sélectionner une caméra "
            "PZ_ANIM_CAM_POV_* dans le viewport "
            "et Play la même LS_POLOP_ANIMATION_V05."
        ),
        "critical_times_seconds": {
            "2": "17h00 convergence",
            "3": "17h01 pont",
            "32": "17h30 séparation A/B",
            "52": "17h50 surveillance caverne",
            "57": "17h55 recherche",
            "60": "17h58 coexistence",
            "61": "17h59 coexistence",
            "62": "18h00 contact",
            "65": "freeze de contrôle : les deux Thomas restent dans la caverne",
        }
    }
}

with open(
    validation_json_path,
    "w",
    encoding="utf-8"
) as f:
    json.dump(
        validation_report,
        f,
        indent=2,
        ensure_ascii=False
    )

validation_lines = [
    "POLOP — VALIDATION ANIMATION V05 + POV",
    "="*72,
    "OVERALL: " + validation_overall,
    "",
]

for item in validation_checks:
    extra = ""

    if "delta_m" in item:
        extra = " | %.2fm" % item["delta_m"]
    elif "distance_m" in item:
        extra = " | %.1fm" % item["distance_m"]

    validation_lines.append(
        "%-46s %-4s%s"
        % (
            item["name"],
            item["status"],
            extra
        )
    )

validation_lines += [
    "",
    "POV — MEME SEQUENCER",
    "- PZ_ANIM_CAM_POV_THOMAS_NORMAL",
    "- PZ_ANIM_CAM_POV_THOMAS_INVERSE",
    "- PZ_ANIM_CAM_POV_EVA",
    "- PZ_ANIM_CAM_POV_LEA",
    "",
    "Temps critiques : 2 / 3 / 32 / 52 / 57 / 60 / 61 / 62 / 65 s",
    "",
    "JSON: " + validation_json_path,
]

with open(
    validation_txt_path,
    "w",
    encoding="utf-8"
) as f:
    f.write(
        "\n".join(validation_lines)
    )


unreal.log("============================================================")
unreal.log("POLOP — ANIMATION PREVIZ V05 + POV")
unreal.log("Bible : Script_POLOP.md")
unreal.log("Sequence UNIQUE : " + sequence_full_path)
unreal.log("Model : " + model_path)
unreal.log("Validation : " + validation_txt_path)
unreal.log(
    "Bindings personnages : %d/4 | heads : %d/4 | POV : %d/4"
    % (
        len(sequence_bindings),
        len(head_bindings),
        len(pov_bindings)
    )
)
unreal.log(
    "AUTO-VALIDATION : " +
    validation_overall
)
unreal.log("POV disponibles :")
unreal.log("  PZ_ANIM_CAM_POV_THOMAS_NORMAL")
unreal.log("  PZ_ANIM_CAM_POV_THOMAS_INVERSE")
unreal.log("  PZ_ANIM_CAM_POV_EVA")
unreal.log("  PZ_ANIM_CAM_POV_LEA")
unreal.log("Même sequence, même timeline, aucun script POV séparé.")
unreal.log("Temps : 2 / 3 / 32 / 52 / 57 / 60 / 61 / 62 / 65 s")
unreal.log("62–65 s = freeze non narratif : les deux Thomas restent au contact dans la caverne.")
unreal.log("============================================================")

'''



# =============================================================================
# MASTER V08 — RAPPORT DE COHERENCE / VALIDATION PAR ETAPES
# =============================================================================

MASTER_REPORT = {
    "master_version": MASTER_VERSION,
    "checks": [],
    "paths": {},
}


def _json_safe(value):
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    if isinstance(value, (list, tuple)):
        return [_json_safe(v) for v in value]
    if isinstance(value, dict):
        return {str(k): _json_safe(v) for k, v in value.items()}
    try:
        if hasattr(value, "x") and hasattr(value, "y") and hasattr(value, "z"):
            return {
                "x": float(value.x),
                "y": float(value.y),
                "z": float(value.z),
            }
    except Exception:
        pass
    return str(value)


def report_check(stage, name, status, severity="INFO", details=None, action=None):
    item = {
        "stage": str(stage),
        "name": str(name),
        "status": str(status),
        "severity": str(severity),
    }
    if details is not None:
        item["details"] = _json_safe(details)
    if action:
        item["action"] = str(action)

    MASTER_REPORT["checks"].append(item)

    if status != "OK":
        log(
            "REPORT %s [%s/%s] %s | %s"
            % (
                stage,
                status,
                severity,
                name,
                json.dumps(item.get("details", {}), ensure_ascii=False),
            )
        )
    return item


def _report_overall():
    checks = MASTER_REPORT["checks"]

    if any(
        c["status"] == "FAIL" and c["severity"] == "BLOCKER"
        for c in checks
    ):
        return "BLOCKED"

    if any(c["status"] == "FAIL" for c in checks):
        return "FAIL"

    if any(c["status"] == "WARN" for c in checks):
        return "WARN"

    return "OK"


def write_master_report(exception_text=None):
    report_dir = os.path.join(
        RUN_SAVED_ROOT,
        "MASTER_V%s" % MASTER_VERSION,
    )
    os.makedirs(report_dir, exist_ok=True)

    overall = _report_overall()
    MASTER_REPORT["overall"] = overall

    if exception_text:
        MASTER_REPORT["exception"] = str(exception_text)

    counts = {
        "ok": sum(1 for c in MASTER_REPORT["checks"] if c["status"] == "OK"),
        "warn": sum(1 for c in MASTER_REPORT["checks"] if c["status"] == "WARN"),
        "fail": sum(1 for c in MASTER_REPORT["checks"] if c["status"] == "FAIL"),
        "blocker_fail": sum(
            1 for c in MASTER_REPORT["checks"]
            if c["status"] == "FAIL" and c["severity"] == "BLOCKER"
        ),
    }
    MASTER_REPORT["counts"] = counts

    json_path = os.path.join(report_dir, "report_previz_v10.json")
    txt_path = os.path.join(report_dir, "report_previz_v10.txt")
    html_path = os.path.join(report_dir, "report_previz_v10.html")

    MASTER_REPORT["paths"] = {
        "json": json_path,
        "txt": txt_path,
        "html": html_path,
    }

    with open(json_path, "w", encoding="utf-8") as fh:
        json.dump(MASTER_REPORT, fh, indent=2, ensure_ascii=False)

    lines = [
        "POLOP — RAPPORT PREVIZ MASTER V%s" % MASTER_VERSION,
        "=" * 88,
        "OVERALL: %s" % overall,
        "OK=%d | WARN=%d | FAIL=%d | BLOCKER=%d"
        % (
            counts["ok"],
            counts["warn"],
            counts["fail"],
            counts["blocker_fail"],
        ),
        "",
    ]

    current_stage = None
    for item in MASTER_REPORT["checks"]:
        if item["stage"] != current_stage:
            current_stage = item["stage"]
            lines.extend(["", "[%s]" % current_stage])

        line = "%-5s %-8s %s" % (
            item["status"],
            item["severity"],
            item["name"],
        )

        if "details" in item:
            line += " | " + json.dumps(
                item["details"],
                ensure_ascii=False,
            )

        lines.append(line)

        if item.get("action"):
            lines.append("      ACTION: " + item["action"])

    if exception_text:
        lines.extend(["", "EXCEPTION:", str(exception_text)])

    with open(txt_path, "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines))

    # Rapport HTML lisible hors Unreal.
    rows = []
    for item in MASTER_REPORT["checks"]:
        cls = item["status"].lower()
        details = html.escape(
            json.dumps(item.get("details", {}), ensure_ascii=False)
        )
        action = html.escape(item.get("action", ""))

        rows.append(
            "<tr class='%s'><td>%s</td><td>%s</td><td>%s</td>"
            "<td><code>%s</code></td><td>%s</td></tr>"
            % (
                cls,
                html.escape(item["stage"]),
                html.escape(item["status"]),
                html.escape(item["name"]),
                details,
                action,
            )
        )

    next_action = (
        "NE PAS VALIDER LES POV : corriger d'abord les FAIL BLOCKER."
        if overall == "BLOCKED"
        else (
            "Corriger les FAIL avant validation visuelle finale."
            if overall == "FAIL"
            else (
                "Validation visuelle ciblée seulement sur les WARN."
                if overall == "WARN"
                else "Pipeline cohérent : validation visuelle finale autorisée."
            )
        )
    )

    html_doc = """<!doctype html>
<html lang="fr">
<head>
<meta charset="utf-8">
<title>POLOP Previz Master V%s</title>
<style>
body{font-family:Arial,sans-serif;margin:24px;background:#111;color:#eee}
h1{margin-bottom:4px}
.summary{padding:14px;border:1px solid #555;background:#1c1c1c;margin:14px 0}
table{border-collapse:collapse;width:100%%;font-size:14px}
th,td{border:1px solid #444;padding:8px;vertical-align:top;text-align:left}
th{background:#222}
tr.ok{background:#142516}
tr.warn{background:#332b10}
tr.fail{background:#351414}
code{white-space:pre-wrap;color:#ddd}
.big{font-size:20px;font-weight:bold}
</style>
</head>
<body>
<h1>POLOP — Rapport Previz Master V%s</h1>
<div class="summary">
<div class="big">OVERALL: %s</div>
<div>OK=%d | WARN=%d | FAIL=%d | BLOCKER=%d</div>
<p>%s</p>
</div>
<table>
<thead><tr><th>Étape</th><th>Statut</th><th>Check</th><th>Détails</th><th>Action</th></tr></thead>
<tbody>%s</tbody>
</table>
</body>
</html>""" % (
        MASTER_VERSION,
        MASTER_VERSION,
        overall,
        counts["ok"],
        counts["warn"],
        counts["fail"],
        counts["blocker_fail"],
        html.escape(next_action),
        "".join(rows),
    )

    with open(html_path, "w", encoding="utf-8") as fh:
        fh.write(html_doc)

    log("=" * 72)
    log("RAPPORT MASTER V%s : %s" % (MASTER_VERSION, overall))
    log(
        "Checks : OK=%d WARN=%d FAIL=%d BLOCKER=%d"
        % (
            counts["ok"],
            counts["warn"],
            counts["fail"],
            counts["blocker_fail"],
        )
    )
    log("Rapport HTML : " + html_path)
    log("Rapport TXT  : " + txt_path)
    log("Rapport JSON : " + json_path)
    log("=" * 72)

    return overall


def _landscape_bounds_cm(landscape):
    try:
        origin, extent = landscape.get_actor_bounds(False)
        return {
            "origin": {
                "x": float(origin.x),
                "y": float(origin.y),
                "z": float(origin.z),
            },
            "extent": {
                "x": float(extent.x),
                "y": float(extent.y),
                "z": float(extent.z),
            },
            "min": {
                "x": float(origin.x - extent.x),
                "y": float(origin.y - extent.y),
                "z": float(origin.z - extent.z),
            },
            "max": {
                "x": float(origin.x + extent.x),
                "y": float(origin.y + extent.y),
                "z": float(origin.z + extent.z),
            },
        }
    except Exception as exc:
        warn("Impossible de lire ActorBounds Landscape : %s" % exc)
        return None


def run_world_coherence_gate(landscape, route_model_path):
    """
    GATE BLOQUANT avant Animation V05.

    Il valide ce que les anciens 19 checks ne validaient pas :
    la présence réelle de la montagne autour des chemins/grotte.
    """
    stage = "WORLD_GEOMETRY"

    loc = landscape.get_actor_location()
    scale = landscape.get_actor_scale3d()

    transform_ok = (
        abs(loc.x - EXPECTED_LANDSCAPE_LOCATION.x) < 2.0
        and abs(loc.y - EXPECTED_LANDSCAPE_LOCATION.y) < 2.0
        and abs(loc.z - EXPECTED_LANDSCAPE_LOCATION.z) < 2.0
        and abs(scale.x - EXPECTED_LANDSCAPE_SCALE.x) < 0.01
        and abs(scale.y - EXPECTED_LANDSCAPE_SCALE.y) < 0.01
        and abs(scale.z - EXPECTED_LANDSCAPE_SCALE.z) < 0.01
    )

    report_check(
        stage,
        "landscape_transform_v11",
        "OK" if transform_ok else "FAIL",
        "BLOCKER",
        {
            "location_cm": [loc.x, loc.y, loc.z],
            "scale": [scale.x, scale.y, scale.z],
            "expected_location_cm": _json_safe(EXPECTED_LANDSCAPE_LOCATION),
            "expected_scale": [200.0, 200.0, 100.0],
        },
        "Le Landscape doit rester au transform V11."
    )

    try:
        components = landscape.get_components_by_class(unreal.LandscapeComponent)
    except Exception:
        components = []

    report_check(
        stage,
        "landscape_components_present",
        "OK" if len(components) > 0 else "FAIL",
        "BLOCKER",
        {"component_count": len(components)},
        "Sans LandscapeComponent, la montagne n'existe pas dans le niveau."
    )

    bounds = _landscape_bounds_cm(landscape)

    if bounds is None:
        report_check(
            stage,
            "landscape_actor_bounds",
            "FAIL",
            "BLOCKER",
            {},
            "Impossible de prouver que la montagne couvre les chemins."
        )
    else:
        span_x_m = (bounds["max"]["x"] - bounds["min"]["x"]) / 100.0
        span_y_m = (bounds["max"]["y"] - bounds["min"]["y"]) / 100.0
        span_z_m = (bounds["max"]["z"] - bounds["min"]["z"]) / 100.0

        report_check(
            stage,
            "landscape_xy_extent_plausible",
            "OK" if span_x_m >= 1900.0 and span_y_m >= 1900.0 else "FAIL",
            "BLOCKER",
            {
                "span_x_m": span_x_m,
                "span_y_m": span_y_m,
                "bounds_cm": bounds,
            },
            "La montagne doit couvrir environ 2016 m × 2016 m."
        )

        report_check(
            stage,
            "landscape_vertical_relief_present",
            "OK" if span_z_m >= 40.0 else "FAIL",
            "BLOCKER",
            {
                "vertical_span_m": span_z_m,
                "bounds_z_m": [
                    bounds["min"]["z"]/100.0,
                    bounds["max"]["z"]/100.0,
                ],
            },
            "Un relief quasi plat signifie que le heightmap n'est pas réellement appliqué."
        )

    route_model = None
    try:
        with open(route_model_path, "r", encoding="utf-8") as fh:
            route_model = json.load(fh)
        report_check(
            stage,
            "route_model_v11_readable",
            "OK",
            "BLOCKER",
            {"path": route_model_path},
        )
    except Exception as exc:
        report_check(
            stage,
            "route_model_v11_readable",
            "FAIL",
            "BLOCKER",
            {"path": route_model_path, "error": str(exc)},
            "Impossible de vérifier chemins et grotte sans le modèle V11."
        )

    if route_model is not None and bounds is not None:
        samples = []
        for route_name, route_data in route_model.get("routes", {}).items():
            for point in route_data.get("samples", []):
                if len(point) >= 3:
                    samples.append((route_name, point))

        outside = []
        for route_name, point in samples:
            x_cm = float(point[0]) * 100.0
            y_cm = float(point[1]) * 100.0
            margin_cm = 300.0

            if not (
                bounds["min"]["x"] - margin_cm <= x_cm <= bounds["max"]["x"] + margin_cm
                and bounds["min"]["y"] - margin_cm <= y_cm <= bounds["max"]["y"] + margin_cm
            ):
                outside.append({
                    "route": route_name,
                    "point_m": point,
                })
                if len(outside) >= 12:
                    break

        report_check(
            stage,
            "all_route_samples_inside_landscape_xy",
            "OK" if not outside else "FAIL",
            "BLOCKER",
            {
                "sample_count": len(samples),
                "outside_examples": outside,
            },
            "Les chemins ne doivent jamais flotter hors de l'emprise de la montagne."
        )

        cave_samples = route_model.get("routes", {}).get("GROTTE", {}).get("samples", [])
        if cave_samples:
            cave_end = cave_samples[-1]
            cave_x_cm = float(cave_end[0]) * 100.0
            cave_y_cm = float(cave_end[1]) * 100.0
            cave_inside = (
                bounds["min"]["x"] <= cave_x_cm <= bounds["max"]["x"]
                and bounds["min"]["y"] <= cave_y_cm <= bounds["max"]["y"]
            )
            report_check(
                stage,
                "cave_route_endpoint_inside_landscape",
                "OK" if cave_inside else "FAIL",
                "BLOCKER",
                {"cave_endpoint_m": cave_end},
                "La grotte doit rester à l'intérieur de l'emprise montagne."
            )

    # Contrôle réel par collision aux points narratifs clés.
    collision_samples = (
        (900.0, 0.0, 70.0, "pont_A"),
        (1300.0, 600.0, 115.0, "route_B"),
        (1760.0, 0.0, 158.0, "jonction_haute"),
        (1830.0, 90.0, 160.5, "zone_grotte"),
    )

    collision_results = []
    collision_ok = True

    for x_m, y_m, expected_z_m, label in collision_samples:
        z_cm = _trace_landscape_z_cm(x_m, y_m)

        if z_cm is None:
            collision_results.append({
                "label": label,
                "x_m": x_m,
                "y_m": y_m,
                "hit": False,
            })
            collision_ok = False
            continue

        actual_z_m = z_cm / 100.0
        delta_m = abs(actual_z_m - expected_z_m)

        collision_results.append({
            "label": label,
            "x_m": x_m,
            "y_m": y_m,
            "hit": True,
            "actual_z_m": actual_z_m,
            "expected_z_m": expected_z_m,
            "delta_m": delta_m,
        })

        if delta_m > 8.0:
            collision_ok = False

    report_check(
        stage,
        "landscape_world_surface_matches_story_points",
        "OK" if collision_ok else "FAIL",
        "BLOCKER",
        {"samples": collision_results},
        "Si ce check échoue, ne pas lancer/valider les POV : personnages et grotte peuvent flotter."
    )

    # Écrit un rapport intermédiaire AVANT toute animation.
    overall = write_master_report()

    blockers = [
        c for c in MASTER_REPORT["checks"]
        if c["stage"] == stage
        and c["status"] == "FAIL"
        and c["severity"] == "BLOCKER"
    ]

    if blockers:
        names = ", ".join(c["name"] for c in blockers)
        fail(
            "WORLD GATE BLOQUE : %s. "
            "Rapport généré ; animation volontairement non lancée."
            % names
        )

    return overall


def merge_animation_validation_into_master_report():
    stage = "ANIMATION"
    path = os.path.join(
        RUN_SAVED_ROOT,
        "ANIMATION_V05",
        "validation",
        "validation_animation_v05.json",
    )

    if not os.path.exists(path):
        report_check(
            stage,
            "animation_validation_report_exists",
            "FAIL",
            "BLOCKER",
            {"path": path},
            "La validation Animation V05 doit produire son JSON."
        )
        return

    try:
        with open(path, "r", encoding="utf-8") as fh:
            data = json.load(fh)
    except Exception as exc:
        report_check(
            stage,
            "animation_validation_report_readable",
            "FAIL",
            "BLOCKER",
            {"path": path, "error": str(exc)},
        )
        return

    report_check(
        stage,
        "animation_validation_report_readable",
        "OK",
        "BLOCKER",
        {"path": path},
    )

    for item in data.get("checks", []):
        status = "OK" if item.get("status") == "OK" else "FAIL"
        details = {
            k: v for k, v in item.items()
            if k not in ("name", "status")
        }
        report_check(
            stage,
            item.get("name", "unnamed_animation_check"),
            status,
            "ERROR" if status == "FAIL" else "INFO",
            details,
        )


def report_camera_authority_state():
    active = []
    foreign = []

    for actor in actors.get_all_level_actors():
        try:
            if not isinstance(actor, unreal.CineCameraActor):
                continue

            label = actor.get_actor_label()

            if not label.startswith("PZ_"):
                continue

            active.append(label)

            if not label.startswith("PZ_ANIM_"):
                foreign.append(label)
        except Exception:
            pass

    ok = len(active) == 11 and not foreign

    report_check(
        "CAMERAS",
        "camera_authority_animation_only",
        "OK" if ok else "FAIL",
        "BLOCKER",
        {
            "active_count": len(active),
            "active": sorted(active),
            "foreign": sorted(foreign),
            "expected_count": 11,
        },
        "Toutes les caméras POLOP doivent être les 11 PZ_ANIM_*."
    )



def log(msg):
    unreal.log("POLOP MASTER : " + str(msg))


def warn(msg):
    unreal.log_warning("POLOP MASTER : " + str(msg))


def fail(msg):
    raise RuntimeError("POLOP MASTER : " + str(msg))


def actor_label(actor):
    try:
        return actor.get_actor_label()
    except Exception:
        return actor.get_name()


def is_landscape_proxy(actor):
    try:
        return hasattr(actor, "landscape_import_heightmap_from_render_target")
    except Exception:
        return False


def list_landscapes():
    return [
        actor for actor in actors.get_all_level_actors()
        if is_landscape_proxy(actor)
    ]


def cleanup_landscape_helpers():
    """
    V05 historique détecte un Landscape par nom de classe.
    On retire donc les Gizmo/Placeholder/anciens helpers Landscape afin que
    le premier Actor contenant "Landscape" soit bien le vrai LandscapeProxy.
    """
    doomed = []
    for actor in actors.get_all_level_actors():
        try:
            class_name = actor.get_class().get_name()
            if "Landscape" in class_name and not is_landscape_proxy(actor):
                doomed.append(actor)
        except Exception:
            pass

    if doomed:
        actors.destroy_actors(doomed)

    log("%d helper(s) Landscape obsolètes supprimés." % len(doomed))


def cleanup_old_polop_actors():
    if not CLEAN_OLD_POLOP_ACTORS:
        return

    doomed = []
    for actor in actors.get_all_level_actors():
        try:
            if actor.get_actor_label().startswith("PZ_"):
                doomed.append(actor)
        except Exception:
            pass

    if doomed:
        actors.destroy_actors(doomed)

    log("%d anciens Actors PZ_* supprimés." % len(doomed))


def landscape_score(actor):
    try:
        loc = actor.get_actor_location()
        scale = actor.get_actor_scale3d()
        dloc = (
            abs(loc.x - EXPECTED_LANDSCAPE_LOCATION.x)
            + abs(loc.y - EXPECTED_LANDSCAPE_LOCATION.y)
            + abs(loc.z - EXPECTED_LANDSCAPE_LOCATION.z)
        ) / 100.0
        dscale = (
            abs(scale.x - EXPECTED_LANDSCAPE_SCALE.x)
            + abs(scale.y - EXPECTED_LANDSCAPE_SCALE.y)
            + abs(scale.z - EXPECTED_LANDSCAPE_SCALE.z)
        ) * 10.0
        label_bonus = -5000.0 if "POLOP" in actor_label(actor).upper() else 0.0
        return dloc + dscale + label_bonus
    except Exception:
        return 1.0e30


def approximate_landscape_resolution(landscape):
    try:
        comps = landscape.get_components_by_class(unreal.LandscapeComponent)
        if not comps:
            return None

        count = len(comps)
        side = int(round(math.sqrt(count)))
        if side * side != count:
            return None

        size_quads = int(comps[0].get_editor_property("component_size_quads"))
        return side * size_quads + 1
    except Exception:
        return None


def prepare_landscape_shell():
    landscapes = list_landscapes()

    if not landscapes:
        fail(
            "Aucun Landscape existant. Le master nettoie/régénère un ancien setup, "
            "mais il faut une coquille Landscape 1009x1009 présente une fois pour toutes."
        )

    keep = min(landscapes, key=landscape_score)
    extras = [x for x in landscapes if x != keep]

    log(
        "Landscape conservé : %s ; Landscapes détectés : %d."
        % (actor_label(keep), len(landscapes))
    )

    if extras and DELETE_EXTRA_LANDSCAPES:
        log(
            "Nettoyage ancien setup : suppression de %d Landscape(s) supplémentaire(s)."
            % len(extras)
        )
        try:
            actors.destroy_actors(extras)
        except Exception as exc:
            fail("Impossible de supprimer les Landscapes supplémentaires : %s" % exc)

        remaining = list_landscapes()
        if len(remaining) != 1:
            fail(
                "Le nettoyage Landscape n'a pas abouti : %d Landscapes restent."
                % len(remaining)
            )
        keep = remaining[0]

    elif extras:
        fail(
            "%d Landscapes existent. Active DELETE_EXTRA_LANDSCAPES ou nettoie le niveau."
            % len(landscapes)
        )

    resolution = approximate_landscape_resolution(keep)
    if resolution is not None:
        log("Résolution Landscape détectée : %dx%d." % (resolution, resolution))
        if STRICT_LANDSCAPE_RESOLUTION and resolution != EXPECTED_HEIGHTMAP_SIZE:
            fail(
                "Landscape incompatible : %dx%d, attendu 1009x1009."
                % (resolution, resolution)
            )
    else:
        warn(
            "Résolution Landscape non déductible ; l'import V11 fera la validation réelle."
        )

    # Determine the actual component extent; ActorLocation may be a corner or center.
    keep.set_actor_location(unreal.Vector(0.0, 0.0, 0.0), False, False)
    try:
        keep.set_actor_rotation(unreal.Rotator(0.0, 0.0, 0.0), False)
    except Exception:
        pass
    keep.set_actor_scale3d(EXPECTED_LANDSCAPE_SCALE)

    bounds = _landscape_bounds_cm(keep)
    if bounds is None:
        fail("Cannot determine Landscape component origin")
    global EXPECTED_LANDSCAPE_LOCATION
    EXPECTED_LANDSCAPE_LOCATION = unreal.Vector(-bounds["min"]["x"], -100800.0-bounds["min"]["y"], 0.0)
    keep.set_actor_location(EXPECTED_LANDSCAPE_LOCATION, False, False)

    try:
        keep.set_actor_label("POLOP_LANDSCAPE_V11", True)
    except Exception:
        pass

    try:
        keep.set_folder_path(unreal.Name("POLOP_PREVIZ/Terrain"))
    except Exception:
        pass

    log("Landscape origin measured: %s" % EXPECTED_LANDSCAPE_LOCATION)
    return keep


def _get_prop(obj, name, default=None):
    try:
        return obj.get_editor_property(name)
    except Exception:
        try:
            return getattr(obj, name)
        except Exception:
            return default


def _trace_landscape_z_cm(x_m, y_m):
    """
    Raycast vertical en ignorant tout le blockout PZ_*.
    Retourne Z en cm seulement si le premier hit utile est un vrai Landscape.
    """
    ignore = []
    for actor in actors.get_all_level_actors():
        try:
            if actor.get_actor_label().startswith("PZ_"):
                ignore.append(actor)
        except Exception:
            pass

    hit = unreal.SystemLibrary.line_trace_single(
        world,
        unreal.Vector(float(x_m) * 100.0, float(y_m) * 100.0, 80000.0),
        unreal.Vector(float(x_m) * 100.0, float(y_m) * 100.0, -30000.0),
        (
            unreal.TraceTypeQuery.ECC_VISIBILITY
            if hasattr(unreal.TraceTypeQuery, "ECC_VISIBILITY")
            else unreal.TraceTypeQuery.TRACE_TYPE_QUERY1
        ),
        True,
        ignore,
        unreal.DrawDebugTrace.NONE,
        True,
    )

    if not hit:
        return None

    fields = unreal.GameplayStatics.break_hit_result(hit)
    point = fields[5]
    hit_actor = fields[9]

    if point is None or hit_actor is None or not is_landscape_proxy(hit_actor):
        return None

    return float(point.z)


def _landscape_edit_layer_indices(landscape):
    """
    UE 5.8 exige un InEditLayerIndex valide.
    On interroge le Landscape au lieu d'essayer -1 en premier.
    """
    result = []

    for prop_name in ("selected_edit_layer_index", "SelectedEditLayerIndex"):
        try:
            value = int(landscape.get_editor_property(prop_name))
            if value >= 0 and value not in result:
                result.append(value)
        except Exception:
            pass

    layers = None
    for method_name in ("get_edit_layers", "get_edit_layers_bp"):
        try:
            method = getattr(landscape, method_name)
            layers = list(method())
            break
        except Exception:
            pass

    if layers:
        for index in range(len(layers)):
            if index not in result:
                result.append(index)

    # Un Landscape UE5.8 nouvellement créé possède normalement au moins
    # sa couche d'édition de base. Index 0 est donc le fallback explicite.
    if 0 not in result:
        result.append(0)

    return result


def import_heightmap_into_landscape(landscape, png_path):
    if not os.path.exists(png_path):
        fail("Heightmap V11 absent après génération : " + png_path)

    log("Import automatique du heightmap V11 dans le Landscape...")

    texture = unreal.RenderingLibrary.import_file_as_texture2d(world, png_path)
    if not texture:
        fail("Impossible de charger le PNG V11 comme Texture2D.")

    # Un heightmap est une donnée linéaire, pas une image couleur sRGB.
    try:
        texture.set_editor_property("srgb", False)
    except Exception:
        pass

    # UE5.8 casts float R to uint16: transmit actual 0..65535 heights.
    # Canvas tint multiplies normalized PNG samples by 65535; verify by readback.
    rt = unreal.RenderingLibrary.create_render_target2d(
        world,
        EXPECTED_HEIGHTMAP_SIZE,
        EXPECTED_HEIGHTMAP_SIZE,
        unreal.TextureRenderTargetFormat.RTF_RGBA32F,
        unreal.LinearColor(0.0, 0.0, 0.0, 1.0),
        False,
        False
    )
    if not rt:
        fail("Impossible de créer le RenderTarget 1009x1009.")

    context = None
    try:
        canvas, size, context = unreal.RenderingLibrary.begin_draw_canvas_to_render_target(
            world, rt
        )
        canvas.draw_texture(
            texture,
            unreal.Vector2D(0.0, 0.0),
            unreal.Vector2D(float(EXPECTED_HEIGHTMAP_SIZE), float(EXPECTED_HEIGHTMAP_SIZE)),
            unreal.Vector2D(0.0, 0.0),
            unreal.Vector2D(1.0, 1.0),
            unreal.LinearColor(65535.0, 65535.0, 65535.0, 1.0),
            unreal.BlendMode.BLEND_OPAQUE,
            0.0,
            unreal.Vector2D(0.0, 0.0)
        )
    finally:
        if context is not None:
            unreal.RenderingLibrary.end_draw_canvas_to_render_target(world, context)

    verify_height_render_target(rt, png_path)

    ok = False
    errors = []
    used_layer = None

    # Le RenderTarget contient la hauteur entière 0..65535 dans R.
    # Donc InImportHeightFromRGChannel=False : ne pas interpréter R+G
    # comme une paire de canaux packés.
    for edit_layer_index in _landscape_edit_layer_indices(landscape):
        try:
            result = landscape.landscape_import_heightmap_from_render_target(
                rt, False, int(edit_layer_index)
            )
            if bool(result):
                ok = True
                used_layer = int(edit_layer_index)
                break
            errors.append("layer %d -> False" % int(edit_layer_index))
        except Exception as exc:
            errors.append("layer %d -> %s" % (int(edit_layer_index), exc))

    try:
        unreal.RenderingLibrary.release_render_target2d(rt)
    except Exception:
        pass

    if not ok:
        fail(
            "Échec import heightmap automatique sur les couches d'édition testées : "
            + " | ".join(errors)
        )

    # UE 5.8 : l'import RT peut mettre à jour le rendu avant la collision.
    # Force Layers Full Update est exposé officiellement à Python et force
    # l'application complète des couches de Landscape.
    try:
        landscape.force_layers_full_update()
        log("Landscape force_layers_full_update() exécuté.")
    except Exception as exc:
        warn("force_layers_full_update indisponible : %s" % exc)

    # Collision la plus précise possible pour la préviz.
    for prop_name in ("collision_mip_level", "simple_collision_mip_level"):
        try:
            landscape.set_editor_property(prop_name, 0)
        except Exception:
            pass

    # Plusieurs chemins sont tentés car toutes les méthodes C++ Landscape
    # ne sont pas forcément réfléchies de la même façon en Python 5.8.
    refresh_attempts = []

    for method_name in (
        "recreate_components_state",
        "recreate_collision_components",
    ):
        try:
            getattr(landscape, method_name)()
            refresh_attempts.append(method_name + "=OK")
        except Exception as exc:
            refresh_attempts.append(method_name + "=NA")

    try:
        info = landscape.get_landscape_info()
        if info:
            try:
                info.recreate_collision_components()
                refresh_attempts.append("LandscapeInfo.recreate_collision_components=OK")
            except Exception:
                refresh_attempts.append("LandscapeInfo.recreate_collision_components=NA")
    except Exception:
        refresh_attempts.append("get_landscape_info=NA")

    try:
        collision_components = landscape.get_editor_property("collision_components")
    except Exception:
        collision_components = []

    recreated = 0
    for comp in collision_components or []:
        try:
            comp.recreate_collision()
            recreated += 1
        except Exception:
            pass

    log(
        "Refresh collision Landscape : %s ; composants recréés=%d."
        % (" | ".join(refresh_attempts), recreated)
    )

    log("Heightmap V11 importé sur Edit Layer %d." % used_layer)


def validate_landscape_profile(landscape):
    """
    Contrôle le relief réellement raycasté quand la collision Landscape est prête.

    Important UE 5.8 :
    landscape_import_heightmap_from_render_target() peut avoir déjà appliqué le
    heightmap au rendu alors que Chaos n'a pas encore reconstruit le heightfield.
    Une absence totale de hit juste après l'import ne doit donc plus tuer le
    pipeline. On distingue :
      - HIT avec mauvaise hauteur => erreur réelle ;
      - aucun HIT sur les 3 points => collision pas encore disponible, warning ;
      - HIT correct => validation forte.
    """
    samples = (
        (900.0, 0.0, 70.0, "pont A"),
        (1760.0, 0.0, 158.0, "jonction haute"),
        (1300.0, 600.0, 115.0, "chemin B"),
    )

    bad = []
    hits = 0

    for x_m, y_m, expected_z_m, label in samples:
        z_cm = _trace_landscape_z_cm(x_m, y_m)

        if z_cm is None:
            warn("CHECK TERRAIN %s : aucun hit collision Landscape." % label)
            continue

        hits += 1
        delta_m = abs(z_cm / 100.0 - expected_z_m)
        log(
            "CHECK TERRAIN %s : Z=%.2fm attendu≈%.2fm delta=%.2fm"
            % (label, z_cm / 100.0, expected_z_m, delta_m)
        )

        if delta_m > 8.0:
            bad.append("%s: delta %.2fm" % (label, delta_m))

    if bad:
        fail(
            "Le Landscape répond aux traces mais sa hauteur ne correspond pas à V11 : "
            + " | ".join(bad)
        )

    if hits == len(samples):
        log("Validation terrain V11 FORTE : 3/3 raycasts corrects.")
        return "STRONG"

    if hits > 0:
        warn(
            "Validation terrain V11 PARTIELLE : %d/%d raycasts disponibles."
            % (hits, len(samples))
        )
        return "PARTIAL"

    # Diagnostic de secours : vérifier que l'acteur Landscape existe encore,
    # possède des composants et garde bien le transform attendu. Le log d'import
    # précédent est déjà la preuve que l'API Landscape a accepté le heightmap.
    try:
        comps = landscape.get_components_by_class(unreal.LandscapeComponent)
    except Exception:
        comps = []

    loc = landscape.get_actor_location()
    scale = landscape.get_actor_scale3d()

    if not comps:
        fail("Landscape sans LandscapeComponent après import.")

    transform_ok = (
        abs(loc.x - EXPECTED_LANDSCAPE_LOCATION.x) < 2.0
        and abs(loc.y - EXPECTED_LANDSCAPE_LOCATION.y) < 2.0
        and abs(loc.z - EXPECTED_LANDSCAPE_LOCATION.z) < 2.0
        and abs(scale.x - EXPECTED_LANDSCAPE_SCALE.x) < 0.01
        and abs(scale.y - EXPECTED_LANDSCAPE_SCALE.y) < 0.01
        and abs(scale.z - EXPECTED_LANDSCAPE_SCALE.z) < 0.01
    )

    if not transform_ok:
        fail(
            "Collision non disponible ET transform Landscape inattendu : "
            "Loc=(%.1f,%.1f,%.1f) Scale=(%.3f,%.3f,%.3f)"
            % (loc.x, loc.y, loc.z, scale.x, scale.y, scale.z)
        )

    warn(
        "Validation terrain V11 SANS COLLISION : 0/3 raycasts. "
        "L'import a réussi, %d LandscapeComponent(s) existent et le transform est correct. "
        "Le pipeline continue vers Animation V05 au lieu de bloquer."
        % len(comps)
    )
    return "NO_COLLISION"



def cleanup_non_animation_polop_cameras():
    """
    Après la géographie, aucune ancienne caméra POLOP ne doit survivre.
    Les caméras du film sont exclusivement PZ_ANIM_* et seront créées par V05.
    Les caméras utilisateur non préfixées PZ_ ne sont jamais touchées.
    """
    doomed = []

    for actor in actors.get_all_level_actors():
        try:
            if not isinstance(actor, unreal.CineCameraActor):
                continue

            label = actor.get_actor_label()
            if label.startswith("PZ_") and not label.startswith("PZ_ANIM_"):
                doomed.append(actor)
        except Exception:
            pass

    if doomed:
        actors.destroy_actors(doomed)

    log("%d ancienne(s) caméra(s) POLOP hors Animation supprimée(s)." % len(doomed))


def patched_animation_v05_source():
    return _SOURCE_V05


def run_animation_v05_with_legacy_landscape_mapping(landscape):
    return run_embedded(_SOURCE_V05, "polop_animation_readable.py")


def report_animation_v05_validation():
    """
    Le master lit le rapport V05 et imprime TOUS les checks en échec dans l'Output Log,
    afin qu'un simple copier-coller du log suffise pour diagnostiquer la suite.
    """
    validation_dir = os.path.join(
        RUN_SAVED_ROOT, "ANIMATION_V05", "validation"
    )
    validation_json = os.path.join(
        validation_dir, "validation_animation_v05.json"
    )
    validation_txt = os.path.join(
        validation_dir, "validation_animation_v05.txt"
    )

    # Compatibilité avec un ancien run V05 avant Master V06.
    if not os.path.exists(validation_json):
        legacy_json = os.path.join(
            validation_dir, "validation_animation_v02.json"
        )
        if os.path.exists(legacy_json):
            validation_json = legacy_json

    if not os.path.exists(validation_json):
        warn("Rapport validation V05 introuvable : " + validation_json)
        return None

    try:
        with open(validation_json, "r", encoding="utf-8") as fh:
            report = json.load(fh)
    except Exception as exc:
        warn("Impossible de lire la validation V05 : %s" % exc)
        return None

    checks = report.get("checks", [])
    failed = [
        item for item in checks
        if item.get("status") != "OK"
    ]

    overall = report.get("overall", "UNKNOWN")
    log(
        "VALIDATION ANIMATION V05 : %s | %d/%d check(s) en échec."
        % (overall, len(failed), len(checks))
    )

    for item in failed:
        name = item.get("name", "sans_nom")
        details = {
            k: v for k, v in item.items()
            if k not in ("name", "status")
        }
        log(
            "  VALIDATION FAIL : %s | %s"
            % (name, json.dumps(details, ensure_ascii=False))
        )

    # Alias V05 plus clair, sans casser le script historique.
    try:
        alias_json = os.path.join(
            validation_dir, "validation_animation_v05.json"
        )
        with open(alias_json, "w", encoding="utf-8") as fh:
            json.dump(report, fh, indent=2, ensure_ascii=False)

        alias_txt = os.path.join(
            validation_dir, "validation_animation_v05.txt"
        )
        lines = [
            "POLOP — VALIDATION ANIMATION V05",
            "=" * 72,
            "OVERALL: " + str(overall),
            "",
        ]
        for item in checks:
            details = {
                k: v for k, v in item.items()
                if k not in ("name", "status")
            }
            lines.append(
                "%-46s %-4s | %s"
                % (
                    item.get("name", "sans_nom"),
                    item.get("status", "?"),
                    json.dumps(details, ensure_ascii=False),
                )
            )
        with open(alias_txt, "w", encoding="utf-8") as fh:
            fh.write("\n".join(lines))
        log("Rapport alias : " + alias_txt)
    except Exception as exc:
        warn("Impossible d'écrire l'alias validation V05 : %s" % exc)

    return overall


def normalize_animation_camera_focals():
    """
    UE 5.8 n'expose plus set_current_focal_length comme les anciennes versions.
    On force les focales V05 via la propriété Python actuelle après création.
    """
    focal_by_label = {
        "PZ_ANIM_CAM_OVERVIEW_TIMELINE": 35.0,
        "PZ_ANIM_CAM_17H00_CONVERGENCE": 45.0,
        "PZ_ANIM_CAM_CAVE_GUARD_LINE": 35.0,
        "PZ_ANIM_CAM_CAVE_REVEAL": 32.0,
        "PZ_ANIM_CAM_FINAL_CAVE_MASTER": 32.0,
        "PZ_ANIM_CAM_CAVE_BACKLIGHT_REVIEW": 30.0,
        "PZ_ANIM_CAM_CAVE_TOP_DEBUG": 35.0,
        # 28 mm : moins de déformation / moins de proxies géants qu'à 20 mm,
        # tout en restant suffisamment large pour une préviz subjective.
        "PZ_ANIM_CAM_POV_THOMAS_NORMAL": 28.0,
        "PZ_ANIM_CAM_POV_THOMAS_INVERSE": 28.0,
        "PZ_ANIM_CAM_POV_EVA": 28.0,
        "PZ_ANIM_CAM_POV_LEA": 28.0,
    }

    updated = 0

    for actor in actors.get_all_level_actors():
        try:
            label = actor.get_actor_label()
            focal = focal_by_label.get(label)
            if focal is None:
                continue

            actor.get_cine_camera_component().set_editor_property(
                "current_focal_length", float(focal)
            )
            updated += 1
        except Exception as exc:
            warn("Focale non appliquée à %s : %s" % (actor_label(actor), exc))

    log("%d focale(s) Animation V05 normalisée(s) pour UE 5.8." % updated)


def validate_animation_camera_authority():
    """
    Post-condition : toute caméra POLOP préfixée PZ_ doit appartenir à Animation V05.
    """
    active = []
    foreign = []

    for actor in actors.get_all_level_actors():
        try:
            if not isinstance(actor, unreal.CineCameraActor):
                continue

            label = actor.get_actor_label()
            if not label.startswith("PZ_"):
                continue

            active.append(label)
            if not label.startswith("PZ_ANIM_"):
                foreign.append(label)
        except Exception:
            pass

    if foreign:
        fail(
            "Anciennes caméras POLOP encore présentes après V05 : "
            + ", ".join(sorted(foreign))
        )

    log(
        "AUTORITÉ CAMÉRA OK : %d caméra(s) POLOP, toutes PZ_ANIM_*."
        % len(active)
    )
    for label in sorted(active):
        log("  CAMERA ACTIVE : " + label)


def run_embedded(source, virtual_name):
    log("Exécution : " + virtual_name)
    namespace = {"__name__": "polop_generated", "__file__": __file__}
    exec(compile(source, virtual_name, "exec"), namespace, namespace)
    return namespace


# V10: portable single-file entry point. Every generated run is isolated.
# Source map is read-only; a run owns its level, Content assets and Saved outputs.
SOURCE_MAP = "/Game/Main"
RUN_ID = datetime.datetime.now().strftime("%Y%m%d_%H%M%S_%f")

GENERATED_ROOT = "/Game/POLOP/Generated_V10"
RUN_MAP_ROOT = GENERATED_ROOT + "/Maps"
RUN_CONTENT_PARENT = GENERATED_ROOT + "/Runs"
WORK_MAP = RUN_MAP_ROOT + "/Previz_" + RUN_ID
RUN_ASSET_ROOT = RUN_CONTENT_PARENT + "/" + RUN_ID

PROJECT_SAVED_DIR = unreal.Paths.convert_relative_path_to_full(
    unreal.Paths.project_saved_dir()
)
RUNS_SAVED_ROOT = os.path.join(PROJECT_SAVED_DIR, "POLOP", "Runs")
RUN_SAVED_ROOT = os.path.join(RUNS_SAVED_ROOT, RUN_ID)
KEYLOG_PATH = os.path.join(RUN_SAVED_ROOT, "keylog.jsonl")

KEEP_SAVED_RUNS = 12
KEEP_CONTENT_RUNS = 8

os.makedirs(RUN_SAVED_ROOT, exist_ok=True)

_TICK_HANDLE = None
_STAGE_STARTED = 0.0
_ANIMATION = None
_GEOGRAPHY = None


def scope_embedded_sources_to_run():
    """Redirect embedded geography/animation filesystem outputs to this RUN_ID."""
    global _SOURCE_V11, _SOURCE_V05

    run_v11_dir = os.path.join(RUN_SAVED_ROOT, "V11")
    run_animation_dir = os.path.join(RUN_SAVED_ROOT, "ANIMATION_V05")

    old_v11 = 'out_dir = os.path.join(saved, "POLOP", "V11")'
    new_v11 = 'out_dir = ' + repr(run_v11_dir)

    old_anim_v11 = 'v11_dir = os.path.join(saved_dir, "POLOP", "V11")'
    new_anim_v11 = 'v11_dir = ' + repr(run_v11_dir)

    old_anim_out = '''animation_out_dir = os.path.join(
    saved_dir,
    "POLOP",
    "ANIMATION_V05"
)'''
    new_anim_out = 'animation_out_dir = ' + repr(run_animation_dir)

    if old_v11 not in _SOURCE_V11:
        raise RuntimeError("V10: V11 output redirection marker missing")
    if old_anim_v11 not in _SOURCE_V05:
        raise RuntimeError("V10: V05 V11 input redirection marker missing")
    if old_anim_out not in _SOURCE_V05:
        raise RuntimeError("V10: V05 output redirection marker missing")

    _SOURCE_V11 = _SOURCE_V11.replace(old_v11, new_v11, 1)
    _SOURCE_V05 = _SOURCE_V05.replace(old_anim_v11, new_anim_v11, 1)
    _SOURCE_V05 = _SOURCE_V05.replace(old_anim_out, new_anim_out, 1)

    os.makedirs(run_v11_dir, exist_ok=True)
    os.makedirs(run_animation_dir, exist_ok=True)

    MASTER_REPORT["run_id"] = RUN_ID
    MASTER_REPORT["saved_root"] = RUN_SAVED_ROOT
    MASTER_REPORT["content_root"] = RUN_ASSET_ROOT
    MASTER_REPORT["work_map"] = WORK_MAP


def cleanup_old_run_artifacts():
    """Keep recent generated runs only. Never touches /Game/Main or archive sources."""
    saved_deleted = []
    content_deleted = []
    map_deleted = []
    errors = []

    # Saved/POLOP/Runs/<run_id>
    try:
        names = [
            name for name in os.listdir(RUNS_SAVED_ROOT)
            if os.path.isdir(os.path.join(RUNS_SAVED_ROOT, name))
        ]
        names = sorted(names, reverse=True)
        keep = set(names[:KEEP_SAVED_RUNS])
        keep.add(RUN_ID)

        import shutil
        for name in names:
            if name in keep:
                continue
            path = os.path.join(RUNS_SAVED_ROOT, name)
            try:
                shutil.rmtree(path)
                saved_deleted.append(name)
            except Exception as exc:
                errors.append("Saved %s: %s" % (name, exc))
    except Exception as exc:
        errors.append("Saved scan: %s" % exc)

    # /Game/POLOP/Generated_V10/Runs/<run_id>
    try:
        assets_found = unreal.EditorAssetLibrary.list_assets(
            RUN_CONTENT_PARENT, True, False
        )
        run_ids = set()
        prefix = RUN_CONTENT_PARENT + "/"

        for asset_path in assets_found:
            text_path = str(asset_path)
            if not text_path.startswith(prefix):
                continue
            tail = text_path[len(prefix):]
            run_id = tail.split("/", 1)[0]
            if run_id:
                run_ids.add(run_id)

        ordered = sorted(run_ids, reverse=True)
        keep = set(ordered[:KEEP_CONTENT_RUNS])
        keep.add(RUN_ID)

        for run_id in ordered:
            if run_id in keep:
                continue
            directory = RUN_CONTENT_PARENT + "/" + run_id
            try:
                if unreal.EditorAssetLibrary.delete_directory(directory):
                    content_deleted.append(run_id)
            except Exception as exc:
                errors.append("Content %s: %s" % (run_id, exc))

        # Generated work maps matching runs removed from Content.
        maps = unreal.EditorAssetLibrary.list_assets(RUN_MAP_ROOT, False, False)
        for asset_path in maps:
            package = str(asset_path).split(".", 1)[0]
            name = package.rsplit("/", 1)[-1]
            if not name.startswith("Previz_"):
                continue
            run_id = name[len("Previz_"):]
            if run_id in content_deleted:
                try:
                    if unreal.EditorAssetLibrary.delete_asset(package):
                        map_deleted.append(run_id)
                except Exception as exc:
                    errors.append("Map %s: %s" % (run_id, exc))
    except Exception as exc:
        errors.append("Content scan: %s" % exc)

    journal(
        "cleanup_old_runs",
        keep_saved=KEEP_SAVED_RUNS,
        keep_content=KEEP_CONTENT_RUNS,
        saved_deleted=saved_deleted,
        content_deleted=content_deleted,
        map_deleted=map_deleted,
        errors=errors,
    )

    if errors:
        warn("Nettoyage anciens runs partiel : " + " | ".join(errors))


def journal(event, **details):
    """Append and flush every event, including exceptions and measured evidence."""
    row = dict(run_id=RUN_ID, utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
               event=event, details=_json_safe(details))
    with open(KEYLOG_PATH, "a", encoding="utf-8") as stream:
        stream.write(json.dumps(row, ensure_ascii=False) + "\n")
        stream.flush()
    unreal.log("POLOP V09 | " + event + " | " + json.dumps(row["details"], ensure_ascii=False))


_original_report_check = report_check


def report_check(stage, name, status, severity="INFO", details=None, action=None):
    item = _original_report_check(stage, name, status, severity, details, action)
    journal("check", **item)
    return item


def verify_height_render_target(rt, png_path):
    """Verify integer-height transport BEFORE mutating Landscape data.

    UE5.8 LandscapeEdit.cpp casts LinearColor.R straight to uint16 when RG=False.
    A normalized texture therefore needs *65535, not a 0..1 channel.
    """
    import struct
    data = open(png_path, "rb").read()
    offset, compressed = 8, bytearray()
    while offset < len(data):
        size = struct.unpack(">I", data[offset:offset+4])[0]
        if data[offset+4:offset+8] == b"IDAT":
            compressed.extend(data[offset+8:offset+8+size])
        offset += size + 12
    raw = zlib.decompress(bytes(compressed))
    measurements = []
    try:
        for x, y in ((450, 504), (650, 804), (880, 504), (915, 549)):
            offset = y * (EXPECTED_HEIGHTMAP_SIZE * 2 + 1) + 1 + x * 2
            expected = struct.unpack(">H", raw[offset:offset+2])[0]
            value = unreal.RenderingLibrary.read_render_target_raw_pixel(world, rt, x, y, False).r
            measurements.append(dict(pixel=[x, y], expected=expected, actual=value))
            if abs(value - expected) > 4.0:
                raise RuntimeError("Height transport mismatch at %s: %.3f instead of %d" % ((x, y), value, expected))
        journal("height_transport_verified", samples=measurements)
    except Exception:
        unreal.RenderingLibrary.release_render_target2d(rt)
        journal("height_transport_failed", samples=measurements)
        raise


def stop_callback():
    global _TICK_HANDLE
    if _TICK_HANDLE is not None:
        unreal.unregister_slate_post_tick_callback(_TICK_HANDLE)
        _TICK_HANDLE = None


def record_failure(exc):
    stop_callback()
    journal("failed", error=str(exc), traceback=traceback.format_exc())
    report_check("EXECUTION", "exception", "FAIL", "BLOCKER", {"error": str(exc)})
    write_master_report(exception_text=traceback.format_exc())
    unreal.log_error("POLOP V09 FAILED: " + str(exc))


def finish_generation():
    global _ANIMATION
    route_path = _GEOGRAPHY["route_path"]
    run_world_coherence_gate(_GEOGRAPHY["landscape"], route_path)
    cleanup_non_animation_polop_cameras()
    _ANIMATION = run_animation_v05_with_legacy_landscape_mapping(_GEOGRAPHY["landscape"])
    normalize_animation_camera_focals()
    validate_animation_camera_authority()
    report_animation_v05_validation()
    merge_animation_validation_into_master_report()
    report_camera_authority_state()
    journal("animation_created", sequence=_ANIMATION["sequence_full_path"],
            objective_time="16:58 -> 18:00", presentation="objective review, 1 second = 1 minute")
    for seconds in (0, 1, 2, 3, 8, 32, 52, 57, 59, 60, 61, 62):
        journal("story_sample", seconds=seconds,
                positions_m={name: _ANIMATION["eval_actor"](name, seconds)
                             for name in ("THOMAS_NORMAL", "THOMAS_INVERSE", "EVA", "LEA")})
    overall = write_master_report()
    if overall in ("FAIL", "BLOCKED"):
        raise RuntimeError("Generated animation has failing checks: " + overall)
    level = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    if not level.save_current_level():
        raise RuntimeError("Could not save generated work level")
    journal(
        "complete",
        status=overall,
        level=WORK_MAP,
        asset_root=RUN_ASSET_ROOT,
        saved_root=RUN_SAVED_ROOT,
        limitations=[
            "blockout proxies",
            "objective timeline; cinematic edit still to build",
            "ring and environmental effects not yet animated",
        ],
    )
    cleanup_old_run_artifacts()


def wait_for_landscape(delta_seconds):
    """Yield to editor ticks so layer rendering and collision really finish."""
    try:
        landscape = _GEOGRAPHY["landscape"]
        samples = [_trace_landscape_z_cm(x, y) for x, y in ((900, 0), (1300, 600), (1760, 0))]
        ready = all(value is not None and abs(value - expected) < 800
                    for value, expected in zip(samples, (7000, 11500, 15800)))
        if ready:
            stop_callback()
            journal("landscape_ready", elapsed=time.monotonic()-_STAGE_STARTED, heights_cm=samples)
            finish_generation()
        elif time.monotonic() - _STAGE_STARTED > 180:
            stop_callback()
            run_world_coherence_gate(landscape, _GEOGRAPHY["route_path"])
            raise RuntimeError("Landscape never became ready within 180 seconds")
    except Exception as exc:
        record_failure(exc)


def main():
    global world, _GEOGRAPHY, _TICK_HANDLE, _STAGE_STARTED, _SOURCE_V11, _SOURCE_V05
    # Check before opening a different map; never discard an unsaved user level.
    dirty = unreal.EditorLoadingAndSavingUtils.get_dirty_map_packages()
    if dirty:
        raise RuntimeError("Save your current level before running POLOP; source levels are never saved automatically.")
    journal("start", script=os.path.abspath(__file__), engine=unreal.SystemLibrary.get_engine_version(),
            source_map=SOURCE_MAP, work_map=WORK_MAP)
    _SOURCE_V11 = _SOURCE_V11.replace("/Game/POLOP/Generated_V09", RUN_ASSET_ROOT)
    _SOURCE_V05 = _SOURCE_V05.replace("/Game/POLOP/Generated_V09", RUN_ASSET_ROOT)
    scope_embedded_sources_to_run()

    level = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    unreal.EditorAssetLibrary.make_directory(RUN_MAP_ROOT)
    unreal.EditorAssetLibrary.make_directory(RUN_CONTENT_PARENT)
    if not level.new_level_from_template(WORK_MAP, SOURCE_MAP):
        raise RuntimeError("Could not create work level from " + SOURCE_MAP)
    world = editor_subsystem.get_editor_world()
    cleanup_old_polop_actors()
    landscape = prepare_landscape_shell()
    _GEOGRAPHY = run_embedded(_SOURCE_V11, "polop_geography_readable.py")
    _GEOGRAPHY["landscape"] = landscape
    import_heightmap_into_landscape(landscape, _GEOGRAPHY["heightmap_path"])
    _STAGE_STARTED = time.monotonic()
    journal("waiting_for_landscape", timeout_seconds=180)
    _TICK_HANDLE = unreal.register_slate_post_tick_callback(wait_for_landscape)


if __name__ == "__main__":
    try:
        main()
    except Exception as error:
        record_failure(error)
        raise
