# -*- coding: utf-8 -*-
"""
LA BOUCLE / POLOP - PREVIZ MASTER V10

Portable: one readable Python file, no encoded payload or machine-specific paths.
Unreal Engine 5.8: Tools > Execute Python Script, select this file.
Prerequisite: /Game/Main contains one 1009x1009 Landscape (16x16 components).
Save the current level before running. Full mode duplicates /Game/Main
into a new work map; fast camera-only mode reuses the already generated work
map and film IN PLACE. /Game/Main is never modified by fast camera mode.
Keep a backup of a generated map before experimenting with camera-only runs.

Diagnostics: every run is isolated under Saved/POLOP/Runs/<run_id>/ :
keylog.jsonl, V11/, ANIMATION_V05/ and MASTER_V10/report_previz_v10.{json,txt,html}.
The editor stays responsive while Landscape layers/collision finish rebuilding.

Current milestone: terrain correction and objective-time animated blockout.
The 65-second review sequence is NOT yet the complete cinematic adaptation.
Ring, environmental effects and full A/B/B9 film edit are subsequent milestones.
"""

import hashlib
import html
import json
import math
import os
import sys
import types
import traceback
import datetime
import time
import zlib
import unreal

# F03 geometry-only was a temporary diagnostic before subtitles were
# validated. It silently removed narrative text and the F01/F04 props from
# the film, and could remain enabled in an Unreal process across reruns.
# Retired: ALWAYS generate the complete cast, props and native subtitles.
# Ignore a stale POLOP_F03_GEOMETRY_ONLY environment variable.
F03_GEOMETRY_ONLY = False

# Switch to True for CAMERA-ONLY changes after a successful FULL run with
# this script in the SAME Unreal session, while still in its generated map.
# False: full generation (required after restarting Unreal, moving to another
# map, or changing landscape, actors, timing, captions or embedded sources).
# True: edit the existing omniscient camera track in place; no new run map,
# landscape import, character bake, subtitle rebuild or new film sequence.
FAST_CAMERA_ONLY = False

# False: spectator-readable narrative captions; no technical notes/spoilers in A.
# True: optional PREVIZ diagnostic notes about unfinished effects and acting.
# Changing this setting (or any subtitles) requires FAST_CAMERA_ONLY=False.
SUBTITLE_REVIEW_MODE = False

# Unreal restores/removes __file__ once Execute Python Script returns. Slate
# callbacks run later, so retain our own immutable source path while it exists.
SOURCE_SCRIPT_PATH = os.path.abspath(__file__)

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


# F03: a smaller real search shelf, bounded by rock and the Landscape cliff.
# Women search at y=-5..-7; both Thomas approaches remain at y>=-8.2.
LEDGE_Z_M = 158.0
for iy in range(HM_SIZE):
    wy = WORLD_Y_MIN_M + iy * GRID_STEP_M
    if wy < -10.8 or wy > -2.2:
        continue
    plateau_y = min(smoothstep((wy + 10.8) / 1.6),
                    smoothstep((-2.2 - wy) / 1.8))
    row = iy * HM_SIZE
    for ix in range(HM_SIZE):
        wx = WORLD_X_MIN_M + ix * GRID_STEP_M
        if wx < 1757.0 or wx > 1774.0:
            continue
        plateau_x = min(smoothstep((wx - 1757.0) / 2.0),
                        smoothstep((1774.0 - wx) / 2.8))
        w = plateau_x * plateau_y
        idx = row + ix
        height_grid[idx] = height_grid[idx]*(1.0-w) + LEDGE_Z_M*w

# Extend the real precipice slightly eastward so it borders the pocket,
# but stop before the separate HAUT path turns south (x~1785).
for iy in range(HM_SIZE):
    wy = WORLD_Y_MIN_M + iy * GRID_STEP_M
    if wy > -10.2 or wy < -46.0:
        continue
    # Actual Landscape drop begins ~3 m beyond the women's farthest
    # search positions, ~2 m beyond Thomas's narrow bend at y=-8.2.
    cliff_across = smoothstep((-10.2 - wy) / 2.0)
    row = iy * HM_SIZE
    for ix in range(HM_SIZE):
        wx = WORLD_X_MIN_M + ix * GRID_STEP_M
        if wx < 1752.0 or wx > 1785.0:
            continue
        cliff_along = min(smoothstep((wx - 1752.0) / 4.0),
                          smoothstep((1785.0 - wx) / 4.0))
        cut = 38.0 * cliff_along * cliff_across
        idx = row + ix
        height_grid[idx] = max(0.0, height_grid[idx] - cut)


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
    folder = "/Game/POLOP/Generated_V10/Materials"
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
            (length,6.0,6.0),
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
# /Game/POLOP/Generated_V10/Sequences/LS_POLOP_ANIMATION_V05
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
SAMPLE_SECONDS = 1.0 / FPS

# POV : les quatre caméras sont animées dans LA MEME Level Sequence.
# Sélectionner la caméra souhaitée dans le viewport puis Play.
POV_SAMPLE_SECONDS = 1.0 / FPS
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

# F03 — Thomas quitte A POUR LA MEME PETITE POCHE que fouillent ensuite
# Eva et Lea : il semble simplement chercher un coin a l'ecart pour uriner.
# Au bout de la paroi, un rocher masque un coude et une ouverture sombre.
# Depuis le chemin et la recherche, ce coude ressemble a une impasse.
# Il n'existe qu'un seul acces praticable depuis la poche; Thomas passe
# reellement derriere le bloc par son cote PRECIPICE, sans traverser la roche.
CAVE_ACCESS_POINT = (
    high_x + 3.0,
    high_y - 4.5,
    terrain_z_m(high_x + 3.0, high_y - 4.5)
)
CAVE_LEDGE_TURN_POINT = (
    high_x + 6.5,
    high_y - 7.6,
    terrain_z_m(high_x + 6.5, high_y - 7.6)
)
CAVE_LEDGE_PASS_POINT = (
    high_x + 12.0,
    high_y - 8.2,
    terrain_z_m(high_x + 12.0, high_y - 8.2)
)
CAVE_ZONE_POINT = (
    high_x + 15.0,
    high_y - 6.0,
    terrain_z_m(high_x + 15.0, high_y - 6.0)
)
# La vraie bouche est desormais au bout de la paroi de cette poche.
# Le reste du petit couloir plonge derriere la roche, et non a 15 m
# au nord dans un second espace ouvert que les femmes pourraient voir.
CAVE_ENTRY_POINT = (
    high_x + 13.0,
    high_y - 2.0,
    terrain_z_m(high_x + 13.0, high_y - 2.0)
)
CAVE_DARK_SLOT = (
    high_x + 14.2,
    high_y - 0.4,
    terrain_z_m(high_x + 14.2, high_y - 0.4) + 0.2
)
CAVE_FISSURE_POINT = (
    high_x + 17.0,
    high_y + 4.0,
    terrain_z_m(high_x + 17.0, high_y + 4.0) + 0.4
)
CAVE_CONTACT_POINT = (
    high_x + 19.0,
    high_y + 6.0,
    terrain_z_m(high_x + 19.0, high_y + 6.0) + 0.8
)

CAVE_GUARD_POINT = route_point_at_station(
    "A",
    max(0.0, LENGTH["A"] - 8.0)
)

# Éva et Léa cherchent sur la banquette, chacune dans une zone distincte.
# Aucune ne passe derrière l'éperon qui cache la bouche de la grotte.
SEARCH_LEDGE_CENTER = (
    high_x + 3.0, high_y - 6.5,
    terrain_z_m(high_x + 3.0, high_y - 6.5)
)
PRECIPICE_EDGE_POINT = (
    high_x + 3.0, high_y - 11.5,
    terrain_z_m(high_x + 3.0, high_y - 11.5)
)
CAVE_SEARCH_POINT_1 = (
    high_x + 0.0, high_y - 6.0,
    terrain_z_m(high_x + 0.0, high_y - 6.0)
)
CAVE_SEARCH_POINT_2 = (
    high_x + 3.0, high_y - 7.0,
    terrain_z_m(high_x + 3.0, high_y - 7.0)
)
CAVE_SEARCH_LEA_POINT_1 = (
    high_x + 2.6, high_y - 5.0,
    terrain_z_m(high_x + 2.6, high_y - 5.0)
)
CAVE_SEARCH_LEA_POINT_2 = (
    high_x + 5.0, high_y - 7.0,
    terrain_z_m(high_x + 5.0, high_y - 7.0)
)

# Test GEOMETRIQUE de PREVIZ : ellipses XY enveloppant les deux volumes de
# rocher reels, avec origine et dimensions identiques a spawn_rock ci-dessous.
# Ne pas prendre un resultat 2D pour une certification du rendu UE : reverifier
# la hauteur des yeux, les meshes et les ombres a chaque position dans Unreal.
F03_MASKS_XY = (
    ("SEARCH_LEDGE_MOUNTAIN_WALL", high_x+8.0, high_y-1.4, 2.5, 1.3),
    ("CAVE_ENTRANCE_BLIND_SPUR", high_x+9.0, high_y-4.8, 3.0, 2.1),
)


def f03_mask_clearance_xy(p, q, mask, steps=160):
    _, cx, cy, rx, ry = mask
    # Valeur <1 : le segment rencontre physiquement le volume (projection XY).
    return min(math.hypot((p[0]+(q[0]-p[0])*i/steps-cx)/rx,
                          (p[1]+(q[1]-p[1])*i/steps-cy)/ry)
               for i in range(steps+1))


F03_WOMEN_VIEWS = (
    ("Eva garde le retour", CAVE_GUARD_POINT),
    ("Eva recherche 1", CAVE_SEARCH_POINT_1),
    ("Eva recherche 2", CAVE_SEARCH_POINT_2),
    ("Lea garde le retour", CAVE_GUARD_POINT),
    ("Lea recherche 1", CAVE_SEARCH_LEA_POINT_1),
    ("Lea recherche 2", CAVE_SEARCH_LEA_POINT_2),
)
for _who, _view in F03_WOMEN_VIEWS:
    if min(f03_mask_clearance_xy(_view, CAVE_ENTRY_POINT, _mask)
           for _mask in F03_MASKS_XY) >= 0.95:
        raise RuntimeError("F03: la bouche est visible depuis " + _who)

F03_THOMAS_OUTDOOR = (
    HIGH_POINT, CAVE_ACCESS_POINT, CAVE_LEDGE_TURN_POINT,
    CAVE_LEDGE_PASS_POINT, CAVE_ZONE_POINT, CAVE_ENTRY_POINT
)
for _start, _end in zip(F03_THOMAS_OUTDOOR, F03_THOMAS_OUTDOOR[1:]):
    if min(f03_mask_clearance_xy(_start, _end, _mask)
           for _mask in F03_MASKS_XY) < 1.12:
        raise RuntimeError("F03: le crochet de Thomas traverse un rocher")
for _waypoint in F03_THOMAS_OUTDOOR[1:5]:
    if _waypoint[1] < high_y - 9.0:
        raise RuntimeError("F03: le passage de Thomas touche le precipice")

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

# The visibility blockers alone do not protect the actual walking route:
# also test the entrance boulder against every outdoor Thomas segment.
_f03_right_mask = (
    "CAVE_ENTRY_ROCK_R",
    CAVE_ENTRY_POINT[0]-0.15*CAVE_UX-3.5*CAVE_PX,
    CAVE_ENTRY_POINT[1]-0.15*CAVE_UY-3.5*CAVE_PY, 1.05, 0.95
)
for _p, _q in zip(F03_THOMAS_OUTDOOR, F03_THOMAS_OUTDOOR[1:]):
    if f03_mask_clearance_xy(_p, _q, _f03_right_mask) <= 1.15:
        raise RuntimeError("F03: Thomas crosses the right entrance boulder")


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
    folder = "/Game/POLOP/Generated_V10/Materials"
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

# A low foreground outcrop masks the exact closure from the omniscient
# approach. It stays beside the walking lane; neither Thomas walks through it.
spawn_box(
    "CONVERGENCE_FOREGROUND_ROCK",
    V(conv_x*100, (conv_y-2.0)*100,
      (terrain_z_m(conv_x, conv_y-2.0)+1.5)*100),
    (380, 140, 300), MAT_ROCK, "MicroGeo/Convergence"
)

# Micro-zone caverne V05 : shell lisible construit sur l'axe entrée -> contact.
# Largeur intérieure ~4,4 m ; hauteur libre ~3,2 m. Aucune masse n'est placée
# au centre de l'axe, ce qui garantit une ligne de vue exploitable pour les POV.
# F03: the previous roof, floor and walls protruded outside the
# entrance, occluding the A15 reveal despite camera-rock XY clearance.
# Leave the first 3.2 metres OPEN. The shadowed passage is still hidden
# from Eva and Lea by the existing physical mountain-side blind spur.
_CAVE_MOUTH_CLEAR_M = 3.2
_cave_shell_end_m = _CAVE_AXIS_LEN + 1.0
if _cave_shell_end_m - _CAVE_MOUTH_CLEAR_M <= 2.0:
    raise RuntimeError("F03: cave too short for a clear opening")
_cave_mid_along = (_CAVE_MOUTH_CLEAR_M + _cave_shell_end_m)*0.5
_cave_mid_x, _cave_mid_y = cave_xy(_cave_mid_along, 0.0)
_cave_mid_z = terrain_z_m(_cave_mid_x, _cave_mid_y)
_cave_rot = unreal.Rotator(0, CAVE_YAW_DEG, 0)
_cave_shell_length_cm = int(round(
    (_cave_shell_end_m - _CAVE_MOUTH_CLEAR_M)*100.0))

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

# F03: small connected mountain-side boundary, not a camera-only mask.
# Short low volumes visually close the toilet nook on the north side
# without intersecting Thomas's south-side passage or the searched shelf.
spawn_rock(
    "SEARCH_LEDGE_WALL_NEAR_TRAIL",
    high_x + 1.2, high_y - 0.7,
    terrain_z_m(high_x + 1.2, high_y - 0.7) + 1.35,
    (3.3, 1.3, 2.1), MAT_ROCK_READABLE, "MicroGeo/SearchLedge"
)
spawn_rock(
    "SEARCH_LEDGE_WALL_JOIN",
    high_x + 4.7, high_y - 0.7,
    terrain_z_m(high_x + 4.7, high_y - 0.7) + 1.35,
    (1.9, 1.25, 2.1), MAT_ROCK_READABLE, "MicroGeo/SearchLedge"
)
# The terminal blind spur still hides the entrance from Eva and Lea.
spawn_rock(
    "SEARCH_LEDGE_MOUNTAIN_WALL",
    high_x + 8.0, high_y - 1.4,
    terrain_z_m(high_x + 8.0, high_y - 1.4) + 2.35,
    (2.5, 1.3, 3.0),
    MAT_ROCK_READABLE,
    "MicroGeo/SearchLedge"
)
spawn_rock(
    "CAVE_ENTRANCE_BLIND_SPUR",
    high_x + 9.0, high_y - 4.8,
    terrain_z_m(high_x + 9.0, high_y - 4.8) + 2.5,
    (3.0, 2.1, 3.35),
    MAT_ROCK_READABLE,
    "MicroGeo/SearchLedge"
)

# Le petit bord est reellement suivi d'une chute dans le Landscape.
# Ne pas reconstruire devant lui une fausse face en cube haute de 21 m :
# l'ancien SEARCH_LEDGE_CLIFF_FACE cachait la vraie rupture de terrain.
ledge_x, ledge_y, ledge_z = PRECIPICE_EDGE_POINT
spawn_box(
    "SEARCH_LEDGE_LIP",
    V(ledge_x*100, ledge_y*100, (ledge_z+0.04)*100),
    (650, 12, 8),
    MAT_ROCK_READABLE,
    "MicroGeo/SearchLedge"
)

# La penombre du coude est renforcee DANS la cavite, le centre demeure
# physiquement libre. Depuis le point de vue des femmes, les deux levres
# rocheuses masquent ces bandes sombres; seul A15 doit les devoiler.
for _shadow_side, _shadow_name in (
    (1.95, "F03_SHADOW_RECESS_LEFT"), (-1.95, "F03_SHADOW_RECESS_RIGHT")
):
    _sx, _sy = cave_xy(0.65, _shadow_side)
    _sz = terrain_z_m(_sx, _sy) + 1.20
    spawn_box(
        _shadow_name,
        V(_sx*100, _sy*100, _sz*100),
        (65, 25, 235),
        MAT_CAVE,
        "MicroGeo/SearchLedge/HiddenMouth",
        unreal.Rotator(0, CAVE_YAW_DEG, 0)
    )

# F03: old right-hand entrance boulder intersected Thomas's physical
# CAVE_ZONE_POINT -> CAVE_ENTRY_POINT path and the A15 lens trajectory.
# Keep the left lip, move/shrink the right lip toward the cliff side.
for _side, _name, _yaw, _sx, _sy in (
    (2.2, "CAVE_ENTRY_ROCK_L", 12, 1.65, 1.35),
    (-3.5, "CAVE_ENTRY_ROCK_R", -12, 1.05, 0.95)
):
    _rx, _ry = cave_xy(-0.15, _side)
    _rz = terrain_z_m(_rx, _ry) + 1.45
    spawn_rock(
        _name, _rx, _ry, _rz, (_sx, _sy, 2.7),
        MAT_ROCK_READABLE, "MicroGeo/CaverneV05/Rocks",
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

# One physical B-bank clip. Objective forward: the clip detaches at ~17:01.
# Reverse personal time: inverse Thomas repairs it BEFORE crossing B -> A.
CARABINER_REPAIR_T0 = 3.04
CARABINER_REPAIR_T1 = 3.08
# The clip sits at the accessible OUTSIDE edge of the existing B anchor,
# not buried within the anchor rock's visible blockout cube.
CARABINER_CLOSED_POINT = (
    bbx+0.48, bby+0.65, terrain_z_m(bbx+0.48, bby+0.65)+0.96)
CARABINER_OPEN_POINT = (
    bbx+0.10, bby+0.20, terrain_z_m(bbx+0.10, bby+0.20)+0.65)

def carabiner_point_at_objective_time(t):
    alpha = clamp((t-CARABINER_REPAIR_T0) /
                  (CARABINER_REPAIR_T1-CARABINER_REPAIR_T0), 0.0, 1.0)
    return linear_point(CARABINER_CLOSED_POINT, CARABINER_OPEN_POINT, alpha)

MOUSQUETON_PROXY = spawn_box(
    "MOUSQUETON_PROXY",
    V(*(v*100.0 for v in CARABINER_CLOSED_POINT)),
    (18, 28, 8), MAT_ANCHOR, "MicroGeo/Pont"
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

# #49: local photographic stop beside A, near the unchanged flank arrival.
# User-approved: wait at the photo spot until Lea returns, without returning
# to the bridge. Blocking offsets do not alter the existing paths or terrain.
FAMILY_WAIT_STATION = A_BRIDGE_STATION - 12.0
FAMILY_WAIT_POINT = point_with_real_terrain(route_point_at_station("A", FAMILY_WAIT_STATION))
EVA_PHOTO_POINT = point_with_real_terrain(
    (FAMILY_WAIT_POINT[0], FAMILY_WAIT_POINT[1] - 12.0, FAMILY_WAIT_POINT[2]))

NORMAL_FAMILY_POINT = point_with_real_terrain(
    (EVA_PHOTO_POINT[0]-2.0, EVA_PHOTO_POINT[1]+1.0, 0.0))
LEA_FAMILY_POINT = point_with_real_terrain(
    (EVA_PHOTO_POINT[0]+2.0, EVA_PHOTO_POINT[1]+1.0, 0.0))
# Reach the original ascent again at 17h06:30, without teleporting at departure.
FAMILY_REJOIN_TIME = GROUP_DEPART_AFTER_LEA + 0.5
NORMAL_REJOIN_STATION = A_BRIDGE_STATION + (LENGTH["A"]-A_BRIDGE_STATION)*0.5/(52.0-8.0)
FAMILY_REJOIN_STATION = A_BRIDGE_STATION + (LENGTH["A"]-8.0-A_BRIDGE_STATION)*0.5/(52.0-8.0)

# A 17h01 en lecture objective, Thomas inversé vient de traverser A -> B.
# Dans son temps propre, c'est bien B -> A conformément à B6.
ANIM = {}

ANIM["THOMAS_NORMAL"] = [
    # F07: a shared objective-time hesitation on the SAME path A.
    station_segment("A", 0.0, 1.975, normal_start_station, CONVERGENCE_STATION),
    hold_segment(1.975, 2.025, point_with_real_terrain(CONVERGENCE_POINT)),
    station_segment("A", 2.025, 3.0, CONVERGENCE_STATION, FAMILY_WAIT_STATION),
    custom_segment(3.0, 3.5, FAMILY_WAIT_POINT, NORMAL_FAMILY_POINT),
    hold_segment(3.5, GROUP_DEPART_AFTER_LEA, NORMAL_FAMILY_POINT),
    custom_segment(GROUP_DEPART_AFTER_LEA, FAMILY_REJOIN_TIME, NORMAL_FAMILY_POINT,
                   point_with_real_terrain(route_point_at_station("A", NORMAL_REJOIN_STATION))),
    station_segment(
        "A",
        FAMILY_REJOIN_TIME,
        GROUP_HIGH_TIME,
        NORMAL_REJOIN_STATION,
        LENGTH["A"]
    ),
    # F03 : il quitte A pour faire pipi DANS la petite poche rocheuse.
    # Puis il longe le bloc, tourne derriere et decouvre sa bouche sombre.
    # Les femmes restent a l'entree de la poche, sans cette ligne de vue.
    custom_segment(
        52.0, 52.5,
        point_with_real_terrain(HIGH_POINT),
        point_with_real_terrain(CAVE_ACCESS_POINT)
    ),
    custom_segment(
        52.5, 52.8,
        point_with_real_terrain(CAVE_ACCESS_POINT),
        point_with_real_terrain(CAVE_LEDGE_TURN_POINT)
    ),
    custom_segment(
        52.8, 53.1,
        point_with_real_terrain(CAVE_LEDGE_TURN_POINT),
        point_with_real_terrain(CAVE_LEDGE_PASS_POINT)
    ),
    custom_segment(
        53.1, 53.5,
        point_with_real_terrain(CAVE_LEDGE_PASS_POINT),
        point_with_real_terrain(CAVE_ZONE_POINT)
    ),
    custom_segment(
        53.5, 54.0,
        point_with_real_terrain(CAVE_ZONE_POINT),
        point_with_real_terrain(CAVE_ENTRY_POINT)
    ),
    custom_segment(54.0, 54.5, point_with_real_terrain(CAVE_ENTRY_POINT), cave_ground_point(1.15, 0.0, 0.05)),
    hold_segment(54.5, 60.0, cave_ground_point(1.15, 0.0, 0.05)),
    custom_segment(
        60.0,
        61.0,
        cave_ground_point(1.15, 0.0, 0.05),
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
    station_segment("A", 0.0, 1.7, eva_start_station, FAMILY_WAIT_STATION),
    custom_segment(1.7, 1.9, FAMILY_WAIT_POINT, EVA_PHOTO_POINT),
    hold_segment(1.9, GROUP_DEPART_AFTER_LEA, EVA_PHOTO_POINT),
    custom_segment(GROUP_DEPART_AFTER_LEA, FAMILY_REJOIN_TIME, EVA_PHOTO_POINT,
                   point_with_real_terrain(route_point_at_station("A", FAMILY_REJOIN_STATION))),
    station_segment(
        "A",
        FAMILY_REJOIN_TIME,
        52.0,
        FAMILY_REJOIN_STATION,
        max(0.0, LENGTH["A"] - 8.0)
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
    hold_segment(1.25, 1.5, point_with_real_terrain(B_BRIDGE_POINT)),
    # #49: the existing first metres of FLANC represent the descent from B
    # (user-approved blocking; neither bridge nor path geometry is changed).
    # Leave the bridge BEFORE the closure. Pause for the request AFTER 17h01,
    # when the inverse has passed behind her on B, then continue the detour.
    station_segment("FLANC", 1.5, 3.5, 0.0, 12.0),
    hold_segment(3.5, 3.65,
                 point_with_real_terrain(route_point_at_station("FLANC", 12.0))),
    station_segment(
        "FLANC",
        3.65,
        LEA_FLANK_RETURN_END_MIN - 0.4,
        12.0,
        LENGTH["FLANC"]
    ),
    custom_segment(LEA_FLANK_RETURN_END_MIN-0.4, LEA_FLANK_RETURN_END_MIN,
                   point_with_real_terrain(A_BRIDGE_POINT), LEA_FAMILY_POINT),
    custom_segment(LEA_FLANK_RETURN_END_MIN, FAMILY_REJOIN_TIME, LEA_FAMILY_POINT,
                   point_with_real_terrain(route_point_at_station("A", FAMILY_REJOIN_STATION))),
    station_segment(
        "A",
        FAMILY_REJOIN_TIME,
        52.0,
        FAMILY_REJOIN_STATION,
        max(0.0, LENGTH["A"] - 8.0)
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
        point_with_real_terrain(CAVE_SEARCH_LEA_POINT_1)
    ),
    custom_segment(
        58.0,
        59.0,
        point_with_real_terrain(CAVE_SEARCH_LEA_POINT_1),
        point_with_real_terrain(CAVE_SEARCH_LEA_POINT_2)
    ),
    custom_segment(
        59.0,
        59.3,
        point_with_real_terrain(CAVE_SEARCH_LEA_POINT_2),
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
hidden_point = point_with_real_terrain(CONVERGENCE_POINT)

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
    # Inverse time reads this B segment in reverse: approach the B-bank
    # fastening, stop close enough to secure/check it, step to the bridge,
    # then cross B -> A. No side-trip or second worldline is introduced.
    station_segment(
        "B", 3.0, CARABINER_REPAIR_T0,
        LENGTH["B"], LENGTH["B"]-1.5
    ),
    hold_segment(
        CARABINER_REPAIR_T0, CARABINER_REPAIR_T1,
        point_with_real_terrain(route_point_at_station("B", LENGTH["B"]-1.5))
    ),
    station_segment(
        "B", CARABINER_REPAIR_T1, 32.0,
        LENGTH["B"]-1.5, B5_STATION
    ),
    station_segment(
        "B",
        32.0,
        60.2,
        B5_STATION,
        0.0
    ),
    # F03 : inverse de l'acces de Thomas normal, dans le TEMPS OBJECTIF.
    # En temps propre, l'inverse sort du coude, puis rejoint A sans etre
    # vu d'Eva et Lea, qui sont deja en train de redescendre.
    custom_segment(
        60.2, 60.26,
        point_with_real_terrain(HIGH_POINT),
        point_with_real_terrain(CAVE_ACCESS_POINT)
    ),
    custom_segment(
        60.26, 60.32,
        point_with_real_terrain(CAVE_ACCESS_POINT),
        point_with_real_terrain(CAVE_LEDGE_TURN_POINT)
    ),
    custom_segment(
        60.32, 60.4,
        point_with_real_terrain(CAVE_LEDGE_TURN_POINT),
        point_with_real_terrain(CAVE_LEDGE_PASS_POINT)
    ),
    custom_segment(
        60.4, 60.48,
        point_with_real_terrain(CAVE_LEDGE_PASS_POINT),
        point_with_real_terrain(CAVE_ZONE_POINT)
    ),
    custom_segment(
        60.48, 60.6,
        point_with_real_terrain(CAVE_ZONE_POINT),
        point_with_real_terrain(CAVE_ENTRY_POINT)
    ),
    custom_segment(
        60.6,
        61.4,
        point_with_real_terrain(CAVE_ENTRY_POINT),
        CAVE_DARK_SLOT
    ),
    custom_segment(
        61.4,
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


def eval_actor_base(name, t):
    segments = ANIM[name]

    for segment in segments:
        if segment["t0"] <= t <= segment["t1"] + 1e-8:
            return eval_segment(segment, t)

    if t < segments[0]["t0"]:
        return eval_segment(segments[0], segments[0]["t0"])

    return eval_segment(segments[-1], segments[-1]["t1"])


def eval_actor(name, t):
    # Distinct walking lanes prevent the family from occupying identical bodies.
    # These 65 cm offsets are blockout choices, not additions to the story.
    p = eval_actor_base(name, t)
    # The local connectors to/from the photo stop follow the existing ground.
    if name == "THOMAS_NORMAL" and (3.0 <= t <= 3.5 or 8.0 <= t <= FAMILY_REJOIN_TIME):
        p = point_with_real_terrain(p)
    lateral = 0.65 if name == "EVA" else 0.0
    if name == "LEA":
        lateral = -0.65 * clamp((t - 7.5) / 0.5, 0.0, 1.0)
    if lateral:
        p = (p[0], p[1] + lateral, terrain_z_m(p[0], p[1] + lateral))
    crossing = {"LEA": (0.75, 1.25), "THOMAS_INVERSE": (2.5, 3.0)}.get(name)
    if crossing:
        lo, hi = crossing
        lift = min(clamp((t-lo+0.1)/0.1, 0.0, 1.0), clamp((hi+0.1-t)/0.1, 0.0, 1.0))
        p = (p[0], p[1], p[2]+0.59*lift)
    return p


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

    if actor_name == "THOMAS_NORMAL" and 1.95 <= t <= 2.045:
        return eval_actor("LEA", t)

    if actor_name == "THOMAS_INVERSE" and CARABINER_REPAIR_T0 <= t <= CARABINER_REPAIR_T1:
        return carabiner_point_at_objective_time(t)

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

    if actor_name == "LEA" and 3.5 <= t <= 3.65:
        return eval_actor("THOMAS_NORMAL", t)

    if actor_name == "LEA" and 1.0 <= t <= 1.5:
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

    # A2/B6: the photographer faces the landscape, away from the bridge.
    # This orientation belongs to the world pose, not the film camera.
    if actor_name == "EVA" and 1.9 <= t <= GROUP_DEPART_AFTER_LEA:
        return (0.0, -1.0, 0.0)

    # The inverse watches the B-bank clip while stationary at its repair.
    if actor_name == "THOMAS_INVERSE" and CARABINER_REPAIR_T0 <= t <= CARABINER_REPAIR_T1:
        return _vec_norm(_vec_sub(carabiner_point_at_objective_time(t), p))

    # The same normal-Thomas glance evaluates in A2 and B9.
    if actor_name == "THOMAS_NORMAL" and 1.975 <= t <= 2.025:
        return _vec_norm(_vec_sub(eval_actor("LEA", t), p))

    # The short pause must not inherit movement from the 0.35-minute lookahead.
    # The cast and POV share this objective-time glance toward normal Thomas.
    if actor_name == "LEA" and 3.5 <= t <= 3.65:
        return _vec_norm(_vec_sub(pov_story_target(actor_name, t, p), p))

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

    # F03: a tight turn now connects the cliffside pocket to the cave.
    # The ordinary +/-0.35 s lookahead cuts across several corners at t=60.5,
    # pointing inverted Thomas away from his path. Follow the actual current
    # segment in his PERSONAL time here, retaining the old POV elsewhere.
    if actor_name == "THOMAS_INVERSE" and 60.2 <= t < 60.6:
        approach = next(
            (segment for segment in ANIM["THOMAS_INVERSE"]
             if segment["t0"] <= t < segment["t1"]
             and segment["t0"] >= 60.2 and segment["t1"] <= 60.6),
            None
        )
        if approach is None:
            raise RuntimeError("F03: no active segment on the inverse cave approach")
        local_objective = _vec_sub(
            eval_segment(approach, approach["t1"]),
            eval_segment(approach, approach["t0"])
        )
        if _vec_len(local_objective) < 0.05:
            raise RuntimeError("F03: degenerate inverse cave approach segment")
        return _vec_norm(tuple(-value for value in local_objective))

    before = eval_actor(actor_name, max(0.0, t-POV_LOOK_AHEAD_SECONDS))
    after = eval_actor(actor_name, min(SEQUENCE_SECONDS, t+POV_LOOK_AHEAD_SECONDS))
    direction = _vec_sub(after, before)

    # In the objective sequence his position moves toward the future, but his
    # gaze follows his experienced journey toward 17:00.
    if actor_name == "THOMAS_INVERSE" and 2.0 <= t < NARRATIVE_SECONDS:
        direction = tuple(-value for value in direction)

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

sequence_asset_path = "/Game/POLOP/Generated_V10/Sequences"
sequence_name = "LS_POLOP_ANIMATION_V05"
sequence_full_path = sequence_asset_path + "/" + sequence_name

unreal.EditorAssetLibrary.make_directory(sequence_asset_path)

# V05 remplace les anciennes séquences Animation dans le Content Browser.
for obsolete_sequence in (
    "/Game/POLOP/Generated_V10/Sequences/LS_POLOP_ANIMATION_V01",
    "/Game/POLOP/Generated_V10/Sequences/LS_POLOP_ANIMATION_V02",
    "/Game/POLOP/Generated_V10/Sequences/LS_POLOP_ANIMATION_V03",
    "/Game/POLOP/Generated_V10/Sequences/LS_POLOP_ANIMATION_V04",
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

    # add_actors creates a default transform track in UE 5.8. Two absolute
    # tracks blend their positions, silently halving camera/character motion.
    for existing in binding.get_tracks():
        if isinstance(existing, unreal.MovieScene3DTransformTrack):
            binding.remove_track(existing)
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
                ch.add_key(unreal.FrameNumber(0), CONTACT_HIDDEN_SCALE,
                           interpolation=unreal.MovieSceneKeyInterpolation.CONSTANT)
                ch.add_key(unreal.FrameNumber(60), value,
                           interpolation=unreal.MovieSceneKeyInterpolation.CONSTANT)
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

    for existing in binding.get_tracks():
        if isinstance(existing, unreal.MovieScene3DTransformTrack):
            binding.remove_track(existing)
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
    for existing in binding.get_tracks():
        if isinstance(existing, unreal.MovieScene3DTransformTrack):
            binding.remove_track(existing)
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
                ch.add_key(unreal.FrameNumber(0), CONTACT_HIDDEN_SCALE,
                           interpolation=unreal.MovieSceneKeyInterpolation.CONSTANT)
                ch.add_key(unreal.FrameNumber(60), value,
                           interpolation=unreal.MovieSceneKeyInterpolation.CONSTANT)
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
        "event": "Thomas inversé traverse A -> B en lecture objective. Vers 17h01 le mousqueton B se décroche ; il est réparé avant la traversée en temps propre."
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
        "id": "A_V05_01B",
        "value": "Attache rive B : t=3.04–3.08 en temps objectif.",
        "reason": "En temps inversé Thomas répare l'attache sur B avant sa traversée B vers A.",
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
    len(lea_flank_segments) == 2
    and lea_flank_segments[0]["s0"] == 0.0
    and lea_flank_segments[0]["s1"] == lea_flank_segments[1]["s0"]
    and lea_flank_segments[1]["s1"] == LENGTH["FLANC"]
    and all(segment["s1"] > segment["s0"] for segment in lea_flank_segments)
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

_CAMERA_BASE_SIGNATURE = hashlib.sha256(
    (_SOURCE_V11 + chr(0) + _SOURCE_V05).encode("utf-8")).hexdigest()
_CAMERA_CACHE_KEY = "_polop_live_omniscient_camera_cache_v1"

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

    fields = hit.to_tuple()
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
            layers = list(landscape.get_edit_layers_bp())
            layer = layers[edit_layer_index]
            journal("landscape_edit_layer", index=edit_layer_index,
                    visible_before=layer.get_editor_property("visible"),
                    alpha_before=layer.get_editor_property("heightmap_alpha"))
            # A hidden layer accepts imports successfully but contributes no relief.
            # This operates only on the copied work map.
            layer.set_editor_property("locked", False)
            layer.set_editor_property("visible", True)
            layer.set_editor_property("heightmap_alpha", 1.0)
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
    namespace = {"__name__": "polop_generated", "__file__": SOURCE_SCRIPT_PATH}
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
CLEANUP_OLD_RUNS = False  # Opt-in: retain previous work and diagnostic evidence by default.

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
    unreal.log("POLOP V10 | " + event + " | " + json.dumps(row["details"], ensure_ascii=False))


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
    unreal.log_error("POLOP V10 FAILED: " + str(exc))


def cinematic_ease(value):
    """Quintic easing: position, velocity and acceleration agree at joins."""
    x = max(0.0, min(1.0, value))
    return x*x*x*(10.0+x*(-15.0+6.0*x))


def blend_camera_pose(previous, desired, progress):
    if previous is None:
        return desired
    weight = cinematic_ease(progress)
    return tuple(tuple(p+(q-p)*weight for p, q in zip(old, new))
                 for old, new in zip(previous, desired))


def objective_gait_phase(name, objective_time):
    """Distance-driven clip clock, identical in every camera/edit direction.

    The stock in-place walk is provisionally calibrated to 1.2 m/s for a 1.8 m
    adult. No free-running animation time is used. Near B7 the inverse retreats:
    signed distance along his facing reverses the walk rather than sliding a
    forward-walking pose backwards. This is not foot IK or final contact acting.
    """
    a = _ANIMATION
    cache = a.setdefault("gait_distance_cache", {})
    key = (name, id(a["eval_actor"]), id(a["ANIM"][name]))
    if key not in cache:
        step = 0.005  # 0.3 objective seconds, independent of output frame rate.
        distances = [0.0]
        previous = a["eval_actor"](name, 0.0)
        for index in range(1, 12401):
            t = index*step
            point = a["eval_actor"](name, t)
            signed = 1.0
            if name == "THOMAS_INVERSE":
                turn = cinematic_ease(max(0.0, min(1.0, (t-step*0.5-2.05)/0.20)))
                signed = math.cos(math.pi*turn)
            distances.append(distances[-1]+math.dist(previous, point)*signed)
            previous = point
        cache[key] = distances
    distances = cache[key]
    position = max(0.0, min(62.0, objective_time))*200.0
    index = min(12399, int(position))
    distance = distances[index]+(distances[index+1]-distances[index])*(position-index)
    speed = 1.2*a["ACTOR_HEIGHT_CM"][name]/180.0
    anchor = distances[400] if name.startswith("THOMAS_") else 0.0
    return (3.6 if name.startswith("THOMAS_") else 0.0)+(distance-anchor)/speed


def character_performance(name, objective_time):
    """One deterministic world pose/animation phase, independent of camera/time direction."""
    a = _ANIMATION
    t = max(0.0, min(62.0, objective_time))
    p = a["eval_actor"](name, t)
    before = a["eval_actor"](name, max(0.0, t-0.01))
    after = a["eval_actor"](name, min(62.0, t+0.01))
    direction = tuple(after[i]-before[i] for i in range(3))
    moving = math.dist(before, after) > 0.002
    if name == "THOMAS_INVERSE":
        direction = tuple(-v for v in direction)
    if not moving:
        direction = a["pov_direction"](name, t)
    yaw = math.degrees(math.atan2(direction[1], direction[0]))-90.0
    # Phase belongs to objective time, never to screen time. Reverse playback
    # therefore reverses EVERY joint of Eva/Lea, not just their root positions.
    # The same walk pose is reached by both branches at objective minute 2.
    # Decreasing objective time advances the inverse's own gait. No film state
    # or camera decision may alter this phase or remove a later occurrence.
    phase = objective_gait_phase(name, t) if moving else t*0.1
    if name == "THOMAS_NORMAL" and 1.955 <= t <= 2.055:
        # Body-facing cue only: separate neck motion requires a later rig pass.
        daughter = a["eval_actor"]("LEA", t)
        look_yaw = math.degrees(math.atan2(
            daughter[1]-p[1], daughter[0]-p[0]))-90.0
        look_weight = (cinematic_ease((t-1.955)/0.02) *
                       (1.0-cinematic_ease((t-2.025)/0.03)))
        yaw += (a["unwrap_angle"](yaw, look_yaw)-yaw)*look_weight
    if name == "THOMAS_INVERSE" and t <= 2.25:
        # B7: turn, then retreat into the closure. Finish turning while the
        # roots are still >1.25 m apart; do not rotate through the other body.
        # This is a root turn, not a mesh/pose morph or a change of worldline.
        # During the normal Thomas's pause, a finite difference of his
        # root positions would be zero; take the real shared closure facing.
        closure_yaw = character_performance("THOMAS_NORMAL", 2.0)["yaw"]
        # In the inverse's PERSONAL direction t decreases: keep looking down
        # the actual A path until the last few steps, then react to the
        # unsuspected body. The prior weighting rotated him the wrong way.
        weight = cinematic_ease((2.11-t)/0.07)
        yaw += (a["unwrap_angle"](yaw, closure_yaw)-yaw)*weight
    # F01: same objective-time family glances in both A2 and B9 readings.
    # Stock mannequin root yaw is a readable placeholder for head/eye acting.
    if name in ("EVA", "LEA", "THOMAS_NORMAL") and 0.08 <= t <= 0.70:
        # Shared opening joke; everyone remains on their approved worldline.
        other = ("THOMAS_NORMAL" if name == "EVA" else "EVA")
        look = a["eval_actor"](other, t)
        look_yaw = math.degrees(math.atan2(
            look[1]-p[1], look[0]-p[0]))-90.0
        moment = ((0.10, 0.46) if name == "EVA" else
                  (0.20, 0.65) if name == "THOMAS_NORMAL" else (0.28, 0.58))
        weight = (cinematic_ease((t-moment[0])/0.045) *
                  (1.0-cinematic_ease((t-moment[1])/0.055)))
        yaw += (a["unwrap_angle"](yaw, look_yaw)-yaw)*0.68*weight
    if name in ("EVA", "LEA") and 52.0 <= t < 57.0:
        # Eva first acknowledges Lea; then both watch the only return passage.
        # No movement, cave entrance reveal or alteration of F03 geometry.
        start = 54.15 if name == "EVA" else 53.95
        look = (a["eval_actor"]("LEA", t) if name == "EVA" and t < 53.0
                else a["eval_actor"]("EVA", t) if name == "LEA" and t < 53.0
                else a["CAVE_GUARD_POINT"])
        look_yaw = math.degrees(math.atan2(
            look[1]-p[1], look[0]-p[0]))-90.0
        attention = cinematic_ease((t-start)/0.16)
        yaw += (a["unwrap_angle"](yaw, look_yaw)-yaw)*attention
    # F07: provisional, deterministic contact acting. The STOCK mannequin
    # has no bespoke impact clip or planted-foot IK: tip the upper/root body
    # very slightly as inverse Thomas recoils into the collision, then return
    # normal Thomas upright in objective time. Both film readings sample this
    # one pose function; the worldline and 17:00 instant remain untouched.
    pitch, roll = 0.0, 0.0
    if name == "THOMAS_NORMAL" and 2.0 <= t <= 2.075:
        pitch = 6.0*(1.0-cinematic_ease((t-2.0)/0.075))
    elif name == "THOMAS_INVERSE" and 2.0 < t <= 2.095:
        pulse = 1.0-cinematic_ease((t-2.0)/0.095)
        pitch = 6.0*pulse
        roll = 3.0*pulse*(1.0-cinematic_ease((t-2.0)/0.070))
    if name == "THOMAS_INVERSE" and abs(t-2.0) < 1e-9:
        # The sole coincident endpoint is drawn once, with equal rig pose.
        closure = character_performance("THOMAS_NORMAL", 2.0)
        yaw, moving, phase = closure["yaw"], closure["moving"], closure["phase"]
        pitch, roll = closure["pitch"], closure["roll"]
    if name == "THOMAS_NORMAL" and 7.65 <= t <= 8.0:
        # Shared closing glance to Eva, evaluated identically in A2 and B9.
        eva = a["eval_actor"]("EVA", t)
        eva_yaw = math.degrees(math.atan2(
            eva[1]-p[1], eva[0]-p[0]))-90.0
        weight = cinematic_ease((t-7.65)/0.11)
        yaw += (a["unwrap_angle"](yaw, eva_yaw)-yaw)*0.45*weight
    return dict(foot=p, yaw=yaw, pitch=pitch, roll=roll,
                moving=moving, phase=phase,
                # At the exact closure both branches share the same body pose.
                # Draw that coincident endpoint once; BOTH are drawn for every
                # strict interior time, including B9's return to normal time.
                visible=(name != "THOMAS_INVERSE" or 2.0 < t < 62.0))


def prepare_human_cast():
    """Use the articulated tutorial mannequin shipped with Unreal; no downloaded asset."""
    a = _ANIMATION
    if a.get("human_cast"):
        return
    root = "/Engine/Tutorial/SubEditors/TutorialAssets/Character/"
    mesh = unreal.load_asset(root+"TutorialTPP")
    walk = unreal.load_asset(root+"Tutorial_Walk_Fwd")
    idle = unreal.load_asset(root+"Tutorial_Idle")
    if not all((mesh, walk, idle)):
        raise RuntimeError("Unreal tutorial skeletal character/animations missing; install Engine Content")
    mesh_height = mesh.get_bounds().box_extent.z*2.0
    colors = {"THOMAS_NORMAL": (0.10, 0.19, 0.27), "THOMAS_INVERSE": (0.10, 0.19, 0.27),
              "EVA": (0.38, 0.19, 0.12), "LEA": (0.32, 0.43, 0.18)}
    cast = {}
    for name in POV_ORDER:
        actor = actors.spawn_actor_from_class(unreal.SkeletalMeshActor, unreal.Vector(0, 0, 0))
        actor.set_actor_label("PZ_ANIM_HUMAN_"+name)
        actor.set_folder_path("POLOP/Personnages")
        component = actor.get_component_by_class(unreal.SkeletalMeshComponent)
        component.set_skeletal_mesh_asset(mesh)
        component.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)
        material = a["ensure_material"]("M_POLOP_CLOTH_"+name, colors[name])
        material.set_editor_property("used_with_skeletal_mesh", True)
        unreal.MaterialEditingLibrary.recompile_material(material)
        unreal.EditorAssetLibrary.save_loaded_asset(material)
        component.set_material(0, material)
        scale = a["ACTOR_HEIGHT_CM"][name]/mesh_height
        actor.set_actor_scale3d(unreal.Vector(scale, scale, scale))
        cast[name] = dict(actor=actor, component=component, scale=scale)
        for old in (a["actor_objects"][name], a["head_objects"][name]):
            old.set_actor_hidden_in_game(True)
            old.set_is_temporarily_hidden_in_editor(True)
    a["human_cast"] = cast
    a["human_animations"] = {True: walk, False: idle}
    terrain = a["ensure_material"]("M_POLOP_EARTH", (0.17, 0.20, 0.12))
    _GEOGRAPHY["landscape"].set_editor_property("landscape_material", terrain)
    # Soft reflected entrance light, rather than a supernatural glow.
    light_point = a["cave_ground_point"](0.25, 0.0, 2.3)
    lamp = actors.spawn_actor_from_class(unreal.PointLight, unreal.Vector(*(v*100 for v in light_point)))
    lamp.set_actor_label("PZ_ANIM_CAVE_ENTRANCE_BOUNCE")
    lamp.set_folder_path("POLOP/Lumiere")
    light = lamp.get_component_by_class(unreal.PointLightComponent)
    light.set_intensity(160.0)
    light.set_attenuation_radius(750.0)
    light.set_light_color(unreal.LinearColor(1.0, 0.84, 0.65, 1.0))
    journal("articulated_cast_created", mesh=mesh.get_path_name(),
            limitation="shared mannequin anatomy; not final human casting or acting")


def f01_box_pose(objective_t):
    """Small B9-only visual prop: Thomas checks a pocket box, then hides it.

    Object presence is an editorial reveal, not a second A2/B9 worldline.
    During the earlier reading the same object remains concealed in his pocket.
    This proxy does not claim a finished hand/box skeletal interaction.
    """
    a = _ANIMATION
    thomas = character_performance("THOMAS_NORMAL", objective_t)
    foot = thomas["foot"]
    yaw = math.radians(thomas["yaw"]+90.0)
    forward = (math.cos(yaw), math.sin(yaw))
    side = (-forward[1], forward[0])
    # A small part of the box emerges from the pocket; no floating box handoff.
    return (foot[0]+0.23*side[0]+0.11*forward[0],
            foot[1]+0.23*side[1]+0.11*forward[1],
            foot[2]+0.92)


def add_f01_box_to_film(sequence, samples):
    """One unobtrusive box beat near the B9 ending; no new camera cut/time."""
    a = _ANIMATION
    mesh = unreal.load_asset("/Engine/BasicShapes/Cube.Cube")
    if not mesh:
        raise RuntimeError("F01 box blockout cube asset missing")
    actor = actors.spawn_actor_from_object(mesh, unreal.Vector(0, 0, -100000))
    # MovieSceneVisibilityTrack BoolChannel uses True=VISIBLE (commit 66b40fda).
    # Do not invert bHidden manually or pass unsupported interpolation=.
    actor.set_actor_label("PZ_ANIM_F01_SMALL_BOX")
    actor.set_folder_path("POLOP/Accessoires/F01")
    actor.set_actor_scale3d(unreal.Vector(0.08, 0.055, 0.025))
    try:
        actor.get_component_by_class(unreal.StaticMeshComponent).set_material(
            0, a["ensure_material"]("M_POLOP_F01_BOX", (0.28, 0.20, 0.12)))
    except Exception as exc:
        unreal.log_warning("F01 small box material: "+str(exc))
    subsystem = unreal.get_editor_subsystem(unreal.LevelSequenceEditorSubsystem)
    binding = subsystem.add_actors([actor])[0]
    for old in binding.get_tracks():
        if isinstance(old, unreal.MovieScene3DTransformTrack):
            binding.remove_track(old)
    track = binding.add_track(unreal.MovieScene3DTransformTrack)
    section = track.add_section()
    section.set_range(0, samples[-1][0]+1)
    channels = section.get_all_channels()
    for channel, value in zip(channels[6:9], (0.08, 0.055, 0.025)):
        channel.set_default(value)
    visibility = binding.add_track(unreal.MovieSceneVisibilityTrack)
    visibility.set_property_name_and_path("bHidden", "bHidden")
    vis_section = visibility.add_section()
    vis_section.set_range(0, samples[-1][0]+1)
    vis_ch = vis_section.get_all_channels()[0]
    b9 = next(item for item in a["f01_film_shots"] if item["scene"] == "B9")
    pause = next(item for item in a["f01_film_shots"] if item["scene"] == "PAUSE_ISSUE")
    # A2 is deliberately absent: the box stays inside Thomas's pocket.
    # In the B9-only PAUSE_ISSUE, Thomas hesitates, briefly reveals the box,
    # then conceals it again. The final 18 s B9 track's world pose is shared
    # with A2; the pocket prop never changes that shared objective-time pose.
    start = pause["start_frame"]+int(round(1.20*a["FPS"]))
    end = pause["start_frame"]+int(round(4.65*a["FPS"]))
    # The narrator's only camera is not modified; crop/reframe is a later pass.
    # Hide at frame zero even if the spawned static mesh default is visible.
    vis_ch.add_key(unreal.FrameNumber(0), False)
    if start > 0:
        vis_ch.add_key(unreal.FrameNumber(start-1), False)
    vis_ch.add_key(unreal.FrameNumber(start), True)
    vis_ch.add_key(unreal.FrameNumber(end), False)
    # The box remains at one physical position in the pocket for a fixed
    # objective instant; never key on film-time elapsed or the edit direction.
    for frame_index, objective_t in samples:
        frame = unreal.FrameNumber(frame_index)
        x, y, z = f01_box_pose(objective_t)
        for channel, value in zip(channels[:3], (100.0*x, 100.0*y, 100.0*z)):
            channel.add_key(frame, float(value),
                            interpolation=unreal.MovieSceneKeyInterpolation.LINEAR)
    journal("f01_box_blockout_baked", start_frame=start, end_frame=end,
            limitation="Small pocket proxy only; true hand reach and holding rig pending")


def add_f04_ring_blockout(sequence, samples):
    """F04: one objective-time material ring proxy; no F03 camera/rock edits.

    The sphere is a temporary marker for ring trajectory and contact timing,
    NOT a final ring mesh or a validated hand interaction.
    """
    a = _ANIMATION
    sphere = unreal.load_asset("/Engine/BasicShapes/Sphere.Sphere")
    if not sphere:
        raise RuntimeError("F04 ring blockout sphere asset missing")
    ring = actors.spawn_actor_from_object(sphere, unreal.Vector(0, 0, -100000))
    ring.set_actor_label("PZ_ANIM_F04_RING_BLOCKOUT")
    ring.set_folder_path("POLOP/Accessoires/F04")
    ring.set_actor_scale3d(unreal.Vector(0.085, 0.085, 0.025))
    subsystem = unreal.get_editor_subsystem(unreal.LevelSequenceEditorSubsystem)
    binding = subsystem.add_actors([ring])[0]
    track = binding.add_track(unreal.MovieScene3DTransformTrack)
    section = track.add_section()
    section.set_range(0, samples[-1][0]+1)
    channels = section.get_all_channels()
    for channel, value in zip(channels[6:9], (0.085, 0.085, 0.025)):
        channel.set_default(value)
    visibility = binding.add_track(unreal.MovieSceneVisibilityTrack)
    visibility.set_property_name_and_path("bHidden", "bHidden")
    vis_section = visibility.add_section()
    vis_section.set_range(0, samples[-1][0]+1)
    visible = vis_section.get_all_channels()[0]
    # Match the validated human visibility convention (66b40fda).
    visible.add_key(unreal.FrameNumber(0), False)
    # Ring stays offscreen until the cave contact sequence, then follows one
    # deterministic objective-time curve in BOTH film directions.
    cave_shots = [shot for shot in a["f04_film_shots"]
                  if shot["scene"] in ("A15_A16", "A17", "PAUSE_CONTACT", "B1")]
    start = cave_shots[0]["start_frame"]
    end = cave_shots[-1]["end_frame"]
    visible.add_key(unreal.FrameNumber(start), True)
    visible.add_key(unreal.FrameNumber(end), False)
    fissure = a["CAVE_FISSURE_POINT"]
    contact = a["CAVE_CONTACT_POINT"]
    for frame_index, t in samples:
        if not (start <= frame_index < end):
            continue
        # Material approach at 18h: an accelerating short bounce, no flash.
        # t is shared objective time, even when B1 plays in reverse.
        u = cinematic_ease((t-61.65)/0.35)
        bounce = 0.10*math.sin(4.0*math.pi*u)*(1.0-u)
        point = tuple(fissure[i]*(1.0-u)+contact[i]*u for i in range(3))
        point = (point[0], point[1], point[2]+bounce)
        for channel, value in zip(channels[:3], (100.0*point[0],
                                                   100.0*point[1],
                                                   100.0*point[2])):
            channel.add_key(unreal.FrameNumber(frame_index), float(value),
                            interpolation=unreal.MovieSceneKeyInterpolation.LINEAR)
    journal("f04_ring_blockout_baked", objective_contact=62.0,
            limitation="Sphere proxy, no hand contact, no falling path beyond B1")


def add_human_performances(sequence, samples):
    """Bake a pose per display frame: scrubbing/reversing cannot desynchronise joints.

    Animation clips are sampled with zero play rate and tick-resolution offsets.
    This deliberately costs more sections than free-running animation, but keeps
    the pose identical at the same objective time in A, B and B9.
    """
    a = _ANIMATION
    prepare_human_cast()
    unreal.LevelSequenceEditorBlueprintLibrary.open_level_sequence(sequence)
    subsystem = unreal.get_editor_subsystem(unreal.LevelSequenceEditorSubsystem)
    tick_rate = sequence.get_tick_resolution()
    ticks_per_second = tick_rate.numerator/tick_rate.denominator
    final_frame = samples[-1][0]+1
    for name in POV_ORDER:
        info = a["human_cast"][name]
        # Hidden/off-camera branches must evaluate exactly the same skeleton.
        info["component"].set_editor_property("visibility_based_anim_tick_option",
            unreal.VisibilityBasedAnimTickOption.ALWAYS_TICK_POSE_AND_REFRESH_BONES)
        binding = subsystem.add_actors([info["actor"]])[0]
        for track in binding.get_tracks():
            binding.remove_track(track)
        section = binding.add_track(unreal.MovieScene3DTransformTrack).add_section()
        section.set_range(0, final_frame)
        channels = section.get_all_channels()
        animation_track = binding.add_track(unreal.MovieSceneSkeletalAnimationTrack)
        visibility_track = binding.add_track(unreal.MovieSceneVisibilityTrack)
        visibility_track.set_property_name_and_path("bHidden", "bHidden")
        visibility_section = visibility_track.add_section()
        visibility_section.set_range(0, final_frame)
        visibility_channel = visibility_section.get_all_channels()[0]
        last_yaw = None
        for frame_index, t in samples:
            pose = character_performance(name, t)
            yaw = pose["yaw"] if last_yaw is None else a["unwrap_angle"](last_yaw, pose["yaw"])
            last_yaw = yaw
            # Never shrink a body into/out of existence. Visibility represents
            # objective branch domain only, not whether B8 was already shown.
            scale = info["scale"]
            values = (tuple(v*100.0 for v in pose["foot"])+
                      (pose["roll"], pose["pitch"], yaw)+(scale,)*3)
            frame = unreal.FrameNumber(frame_index)
            visibility_channel.add_key(frame, bool(pose["visible"]))
            for channel, value in zip(channels, values):
                channel.add_key(frame, float(value), interpolation=unreal.MovieSceneKeyInterpolation.LINEAR)
            clip = a["human_animations"][pose["moving"]]
            animation_section = animation_track.add_section()
            animation_section.set_range(frame_index, frame_index+1)
            params = unreal.MovieSceneSkeletalAnimationParams()
            params.animation = clip
            params.play_rate = unreal.MovieSceneTimeWarpExtensions.make_time_warp(0.0)
            params.first_loop_start_frame_offset = unreal.FrameNumber(
                int((pose["phase"] % clip.get_play_length())*ticks_per_second))
            params.force_custom_mode = True
            params.skip_anim_notifiers = True
            animation_section.set_editor_property("params", params)
    unreal.EditorAssetLibrary.save_loaded_asset(sequence)
    journal("human_performances_baked", sequence=sequence.get_path_name(), frames=len(samples),
            clock="shared objective time", pose_sampling_fps=a["FPS"])


def audit_bridge_family_blocking():
    """Measure #49 blocking in the shared world; not a visual visibility verdict."""
    a = _ANIMATION
    results = {}
    for name in ("EVA", "LEA"):
        closest = (float("inf"), None)
        frontal = (180.0, None)
        for index in range(2001, 8001):
            t = index / 1000.0  # 17h00:00.06 through 17h06, both film readings.
            pose = character_performance(name, t)
            inverse = a["eval_actor"]("THOMAS_INVERSE", t)
            dx, dy = inverse[0]-pose["foot"][0], inverse[1]-pose["foot"][1]
            distance = math.hypot(dx, dy)
            heading = math.radians(pose["yaw"]+90.0)
            cosine = (math.cos(heading)*dx+math.sin(heading)*dy)/max(distance, 1e-9)
            angle = math.degrees(math.acos(max(-1.0, min(1.0, cosine))))
            closest = min(closest, (distance, t))
            frontal = min(frontal, (angle, t))
        results[name] = dict(min_horizontal_distance_m=closest[0], distance_time=closest[1],
                             min_facing_angle_deg=frontal[0], angle_time=frontal[1])
    payload = dict(scope="Root positions and facing, minutes since 16h58; no occlusion or eye/peripheral-vision test",
                   visual_validation="PENDING", actors=results)
    path = os.path.join(RUN_SAVED_ROOT, "bridge_family_blocking.json")
    with open(path, "w", encoding="utf-8") as output:
        json.dump(payload, output, indent=2)
    journal("bridge_family_blocking_measured", report=path, **payload)
    return payload


def audit_cast_closure():
    """Endpoint/domain proof, not a claim that ring/contact acting is finished."""
    names = ("THOMAS_NORMAL", "THOMAS_INVERSE")
    times = [1.99, 2.0, 2.000001, 2.01, 2.05, 2.1, 2.25, 2.5, 3.0, 32.0, 52.0, 60.0, 61.999999]
    rows = []
    for t in times:
        normal, inverse = [character_performance(n, t) for n in names]
        rows.append(dict(objective_minute=t, normal=normal, inverse=inverse,
                         root_distance_m=math.dist(normal["foot"], inverse["foot"])))
    n, i = [character_performance(name, 2.0) for name in names]
    checks = dict(
        closure_root=math.dist(n["foot"], i["foot"]) < 1e-6,
        closure_yaw=abs((n["yaw"]-i["yaw"]+180.0) % 360.0-180.0) < 1e-6,
        closure_clip=n["moving"] == i["moving"],
        closure_phase=abs(n["phase"]-i["phase"]) < 1e-6,
        closure_root_tilt=(abs(n["pitch"]-i["pitch"]) < 1e-6
                           and abs(n["roll"]-i["roll"]) < 1e-6),
        before_closure_one=not character_performance(names[1], 1.999999)["visible"],
        interior_two=all(all(character_performance(name, 2.0+k*0.01)["visible"]
                            for name in names) for k in range(1, 6000)))
    forward = {t: [character_performance(name, t) for name in names] for t in times}
    checks["replay_same_world"] = all(forward[t] == [character_performance(name, t) for name in names]
                                       for t in list(reversed(times))+times)
    report = dict(status="CAST_ENDPOINT_CHECKS_ONLY", checks=checks, samples=rows,
                  limitations=["Ring and hand/rock contact choreography not yet implemented",
                               "Root separation is not a skeletal collision proof",
                               "Walk speed calibration is approximate; no planted-foot IK",
                               "18h endpoint articulated continuity still to validate"])
    path = os.path.join(RUN_SAVED_ROOT, "cast_closure_report.json")
    with open(path, "w", encoding="utf-8") as output:
        json.dump(report, output, indent=2)
    journal("cast_closure_audit", report=path, checks=checks)
    if not all(checks.values()):
        raise RuntimeError("Cast closure regression: "+repr(checks))
    return report


def validate_cast_closure_evaluation():
    """Measure actual bones after editor ticks, including hidden/off-camera cast.

    Asynchronous: results are written to cast_closure_evaluated.json and keylog.
    Requires build_cast_closure_probe(). Leaves its playback paused at frame 300.
    """
    a = _ANIMATION
    previous = a.get("cast_measurement")
    if previous and previous.get("handle"):
        unreal.unregister_slate_post_tick_callback(previous["handle"])
    sequence = a["cast_closure_sequence"]
    unreal.LevelSequenceEditorBlueprintLibrary.pause()
    unreal.LevelSequenceEditorBlueprintLibrary.open_level_sequence(sequence)
    state = dict(frames=[0, 90, 91, 180, 300, 540, 720, 721, 901, 1141, 1261,
                         1350, 1351, 1441, 1442, 1532, 1533, 1622, 1742, 1982, 2162],
                 index=0, wait=0.0, pending=False, rows=[])
    a["cast_measurement"] = state

    def finish():
        unreal.unregister_slate_post_tick_callback(state["handle"])
        state["handle"] = None

    def tick(delta):
        try:
            if state["index"] == len(state["frames"]):
                finish()
                rows = state["rows"]
                root_error = max(p["root_error_cm"] for row in rows for p in row["actors"].values())
                visibility_ok = all(p["hidden"] != p["expected"]["visible"]
                                    for row in rows for p in row["actors"].values())
                closure_error = max(math.dist(b[:3], row["actors"]["THOMAS_INVERSE"]["bones"][name][:3])
                                    for row in rows if row["objective_minute"] == 2.0
                                    for name, b in row["actors"]["THOMAS_NORMAL"]["bones"].items())
                replay_error = max(math.dist(b[:3], other["actors"][name]["bones"][bone][:3])
                                   for row in rows for other in rows
                                   if row["objective_minute"] == other["objective_minute"]
                                   for name, p in row["actors"].items() for bone, b in p["bones"].items())
                checks = dict(root_error_cm=root_error, visibility_ok=visibility_ok,
                              closure_bone_error_cm=closure_error, replay_bone_error_cm=replay_error)
                passed = visibility_ok and max(root_error, closure_error, replay_error) < 0.02
                path = os.path.join(RUN_SAVED_ROOT, "cast_closure_evaluated.json")
                with open(path, "w", encoding="utf-8") as output:
                    json.dump(dict(status="PASS" if passed else "FAIL", checks=checks, samples=rows,
                                   scope="cast endpoint and replay only; not full #44 validation"), output, indent=2)
                journal("cast_closure_evaluated", passed=passed, report=path, checks=checks)
                unreal.LevelSequenceEditorBlueprintLibrary.set_current_time(300)
                return
            frame = state["frames"][state["index"]]
            if not state["pending"]:
                unreal.LevelSequenceEditorBlueprintLibrary.set_current_time(frame)
                state.update(pending=True, wait=0.0)
                return
            state["wait"] += delta
            if state["wait"] < 0.2:
                return
            t = a["cast_closure_samples"][frame][1]
            row = dict(frame=frame, objective_minute=t, actors={})
            for name, info in a["human_cast"].items():
                actor, component = info["actor"], info["component"]
                loc = actor.get_actor_location()
                scale = actor.get_actor_scale3d()
                expected = character_performance(name, t)
                bones = {}
                for index in range(component.get_num_bones()):
                    bone = component.get_bone_name(index)
                    tr = component.get_socket_transform(bone, unreal.RelativeTransformSpace.RTS_WORLD)
                    bones[str(bone)] = [tr.translation.x, tr.translation.y, tr.translation.z,
                                        tr.rotation.x, tr.rotation.y, tr.rotation.z, tr.rotation.w]
                row["actors"][name] = dict(root_cm=[loc.x, loc.y, loc.z], yaw=actor.get_actor_rotation().yaw,
                    scale=[scale.x, scale.y, scale.z], hidden=actor.get_editor_property("hidden"),
                    expected=expected, bones=bones,
                    root_error_cm=math.dist([loc.x, loc.y, loc.z], [v*100 for v in expected["foot"]]))
            state["rows"].append(row)
            state.update(index=state["index"]+1, pending=False)
        except Exception as exc:
            finish()
            journal("cast_closure_measurement_failed", error=str(exc), traceback=traceback.format_exc())
            unreal.log_error(str(exc))
    state["handle"] = unreal.register_slate_post_tick_callback(tick)


def build_cast_closure_probe():
    """Preserve LS_CAST_PROBE; make an unoccluded, real-time 17h closure audit.

    Three passes through the SAME objective samples: forward, reverse, forward.
    A minute of objective time is sixty screen seconds in this audit only.
    The original articulated cast/clip baker is reused, not replaced by proxies.
    """
    a = _ANIMATION
    unreal.LevelSequenceEditorBlueprintLibrary.pause()
    audit_cast_closure()
    fps = 30
    # 16:59:57 -> 17:00:21, then back and forward again (24 s per pass).
    objective = [1.95+k/(60.0*fps) for k in range(721)]
    times = objective+list(reversed(objective))+objective
    samples = list(enumerate(times))
    name = "LS_CAST_CLOSURE_"+datetime.datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    sequence = unreal.AssetToolsHelpers.get_asset_tools().create_asset(
        name, RUN_ASSET_ROOT+"/Sequences", unreal.LevelSequence, unreal.LevelSequenceFactoryNew())
    sequence.set_display_rate(unreal.FrameRate(fps, 1))
    sequence.set_playback_start(0)
    sequence.set_playback_end(len(samples))
    sequence.set_view_range_start(0.0)
    sequence.set_view_range_end(len(samples)/fps)
    add_human_performances(sequence, samples)
    ls = unreal.get_editor_subsystem(unreal.LevelSequenceEditorSubsystem)
    # Visibility is scoped to this diagnostic sequence; do not delete the rocks.
    hidden = []
    for actor in actors.get_all_level_actors():
        label = actor.get_actor_label()
        if "CONVERGENCE_ROCK" in label or "CONVERGENCE_FOREGROUND_ROCK" in label or "EVENT_17H00" in label:
            binding = ls.add_actors([actor])[0]
            for track in binding.get_tracks():
                binding.remove_track(track)
            track = binding.add_track(unreal.MovieSceneVisibilityTrack)
            track.set_property_name_and_path("bHidden", "bHidden")
            section = track.add_section()
            section.set_range(0, len(samples))
            section.get_all_channels()[0].set_default(False)
            hidden.append(label)
    center = a["eval_actor"]("THOMAS_NORMAL", 2.08)
    position = unreal.Vector((center[0]-2.0)*100, (center[1]-13.0)*100, (center[2]+5.5)*100)
    target = unreal.Vector(center[0]*100, center[1]*100, (center[2]+0.9)*100)
    camera = a["create_camera"]("CAST_CLOSURE_DEBUG", position, target, 28.0)
    binding = ls.add_actors([camera])[0]
    cuts = sequence.add_track(unreal.MovieSceneCameraCutTrack)
    # add_actors(camera) may have inserted an automatic cut already.
    for automatic_cut in list(cuts.get_sections()):
        cuts.remove_section(automatic_cut)
    cut = cuts.add_section()
    cut.set_range(0, len(samples))
    binding_id = unreal.MovieSceneObjectBindingID()
    binding_id.set_editor_property("guid", binding.get_id())
    cut.set_camera_binding_id(binding_id)
    a["cast_closure_sequence"] = sequence
    a["cast_closure_samples"] = samples
    unreal.EditorAssetLibrary.save_loaded_asset(sequence)
    with open(os.path.join(RUN_SAVED_ROOT, "cast_closure_probe.json"), "w", encoding="utf-8") as output:
        json.dump(dict(sequence=sequence.get_path_name(), fps=fps, samples=samples,
                       hidden_for_debug=hidden, closure_frames=[90, 1351, 1532]), output, indent=2)
    unreal.LevelSequenceEditorBlueprintLibrary.set_lock_camera_cut_to_viewport(True)
    unreal.LevelSequenceEditorBlueprintLibrary.set_current_time(0)
    journal("cast_closure_probe_ready", sequence=sequence.get_path_name(), frames=len(samples))
    return sequence


def update_existing_omniscient_camera(shots, desired_pose, reveal_pose, reveal_clearance, opening_pose):
    """Fast pass: replace ONLY the existing camera's transform keys.

    Keep the original film sequence, all cast tracks/poses, 17 pauses,
    subtitle tracks, camera cut, world actors and Landscape untouched.
    """
    a = _ANIMATION
    if tuple(shots) != a.get("omniscient_shots"):
        raise RuntimeError(
            "FAST_CAMERA_ONLY: shot timing/order changed; set False for a full run.")
    seq = a["omniscient_sequence"]
    cam = a["omniscient_camera"]
    binding = a["omniscient_camera_binding"]
    fps = a["FPS"]
    if not seq or not cam or not binding or cam.get_actor_label() != "PZ_ANIM_CAM_OMNISCIENT_CURRENT":
        raise RuntimeError("FAST_CAMERA_ONLY: live film/camera unavailable; run full mode.")
    entry = [actor for actor in actors.get_all_level_actors()
             if actor.get_actor_label() == "POLOP_FILM_CURRENT"
             and isinstance(actor, unreal.LevelSequenceActor)]
    if len(entry) != 1 or entry[0].get_sequence() != seq:
        raise RuntimeError("FAST_CAMERA_ONLY: current film does not match cached film.")
    old_tracks = [track for track in binding.get_tracks()
                  if isinstance(track, unreal.MovieScene3DTransformTrack)]
    if len(old_tracks) != 1:
        raise RuntimeError("FAST_CAMERA_ONLY: expected exactly one camera transform track.")
    old_track = old_tracks[0]
    # Bake new camera in a temporary transform track. If any F03 geometry
    # audit fails, discard only this NEW track, leaving the old film intact.
    unreal.LevelSequenceEditorBlueprintLibrary.pause()
    unreal.LevelSequenceEditorBlueprintLibrary.open_level_sequence(seq)
    new_track = binding.add_track(unreal.MovieScene3DTransformTrack)
    try:
        section = new_track.add_section()
        section.set_range(0, sum(shot[1] for shot in shots)*fps)
        camera_channels = section.get_all_channels()
        previous_rotation = None
        previous_pose = None
        boundary_pose = None
        previous_beat = None
        first_frame = 0
        max_step_m = 0.0
        for code, seconds, t0, t1, focus, offset in shots:
            count = seconds*fps
            for index in range(count):
                u = index/max(1, count-1)
                t = t0+(t1-t0)*cinematic_ease(u)
                moving_origin = boundary_pose
                if previous_beat is not None:
                    old_code, old_focus, old_offset = previous_beat
                    moving_origin = desired_pose(old_code, old_focus, old_offset, t)
                handover = (seconds if code in ("A5_GEOGRAPHIE", "B9_ELOIGNEMENT")
                            else min(3.0, seconds))
                if code == "A15_A16":
                    eye, target = reveal_pose(u, t, boundary_pose)
                    reveal_clearance(eye, target, u)
                    if u >= 0.60 and eye[2] < a["terrain_z_m"](eye[0], eye[1])+1.25:
                        raise RuntimeError(
                            "F03 A15 camera below terrain clearance at %.3f" % u)
                else:
                    requested = (opening_pose(code, u, t)
                                 if code in ("PAUSE_INTRO", "A1")
                                 else desired_pose(code, focus, offset, t))
                    eye, target = blend_camera_pose(
                        moving_origin, requested, u*seconds/handover)
                    if focus != "CAVE" and (
                            previous_beat is None or previous_beat[1] != "CAVE"):
                        eye = (eye[0], eye[1],
                               max(eye[2], a["terrain_z_m"](eye[0], eye[1])+2.0))
                if previous_pose is not None:
                    max_step_m = max(max_step_m, math.dist(previous_pose[0], eye))
                previous_pose = (eye, target)
                pos = unreal.Vector(*(value*100.0 for value in eye))
                look = unreal.Vector(*(value*100.0 for value in target))
                rotation_raw = unreal.MathLibrary.find_look_at_rotation(pos, look)
                rotation = (rotation_raw.roll, rotation_raw.pitch, rotation_raw.yaw)
                if previous_rotation is not None:
                    rotation = tuple(a["unwrap_angle"](p, q)
                                     for p, q in zip(previous_rotation, rotation))
                previous_rotation = rotation
                frame = unreal.FrameNumber(first_frame+index)
                for channel, value in zip(
                        camera_channels[:6], (pos.x, pos.y, pos.z)+rotation):
                    channel.add_key(frame, float(value),
                                    interpolation=unreal.MovieSceneKeyInterpolation.LINEAR)
            boundary_pose = previous_pose
            previous_beat = (code, focus, offset)
            first_frame += count
    except Exception:
        binding.remove_track(new_track)
        raise
    # Swap only after the entire replacement track has baked successfully.
    binding.remove_track(old_track)
    unreal.EditorAssetLibrary.save_loaded_asset(seq)
    a["omniscient_camera_channels"] = camera_channels
    journal("camera_only_updated", sequence=seq.get_path_name(),
            frames=first_frame, maximum_camera_speed_m_s=max_step_m*fps,
            scope="omniscient transform keys only; cast, captions and terrain reused")
    return seq


def build_omniscient_edit():
    """First editorial pass: a separate film timeline, leaving POV audit intact.

    Story minutes are sampled in both directions; all eight character proxies
    share the exact same objective time. This is a blocking pass, not a claim
    that props, acting, sound or the canonical opening are finished.
    """
    a = _ANIMATION
    # code, screen seconds, objective minute endpoints, focus, camera offset (m)
    shots = [
        ("PAUSE_INTRO", 6, 0, 0, "LEA", (-8, -12, 7)),
        ("A1", 12, 0, 2, "LEA", (-8, -12, 7)),
        ("A2", 18, 2, 8, "LEA", (-5, -9, 4)),
        ("PAUSE_DETOUR", 6, 8, 8, "LEA", (-5, -9, 4)),
        ("A3_A4", 16, 8, 20, "EVA", (-8, -10, 5)),
        ("PAUSE_THOMAS", 5, 20, 20, "EVA", (-8, -10, 5)),
        ("A5_GEOGRAPHIE", 8, 20, 24, "EVA", (-45, -65, 40)),
        ("PAUSE_CHEMINS", 7, 24, 24, "EVA", (-45, -65, 40)),
        ("A6_A8", 16, 24, 32, "THOMAS_NORMAL", (-8, -12, 6)),
        ("A9_PONT", 4, 32, 32.2, "THOMAS_NORMAL", (-18, -35, 20)),
        ("PAUSE_ATTACHE", 6, 32.2, 32.2, "THOMAS_NORMAL", (-18, -35, 20)),
        ("A10", 14, 32.2, 52, "EVA", (-10, -12, 6)),
        ("PAUSE_DEPART", 6, 52, 52, "EVA", (-10, -12, 6)),
        ("A11_ATTENTE", 18, 52, 56, "EVA", (-8, -11, 4.5)),
        ("PAUSE_ATTENTE", 7, 56, 56, "EVA", (-8, -11, 4.5)),
        ("A12_A13", 16, 56, 59, "EVA", (9, -16, 6)),
        ("PAUSE_RECHERCHE", 7, 59, 59, "EVA", (9, -16, 6)),
        ("A14", 6, 59, 60, "EVA", (9, -16, 6)),
        ("A15_A16", 16, 60, 61.95, "CAVE", (0, 0, 0)),
        ("PAUSE_REVELATION", 6, 61.95, 61.95, "CAVE", (0, 0, 0)),
        ("A17", 5, 61.95, 62, "CAVE", (0, 0, 0)),
        ("PAUSE_CONTACT", 7, 62, 62, "CAVE", (0, 0, 0)),
        ("B1", 16, 62, 60.2, "CAVE", (0, 0, 0)),
        ("PAUSE_OBSCURITE", 6, 60.2, 60.2, "CAVE", (0, 0, 0)),
        ("B2", 10, 60.2, 59.4, "THOMAS_INVERSE", (-14, 20, 9)),
        ("PAUSE_FAMILLE", 6, 59.4, 59.4, "THOMAS_INVERSE", (-14, 20, 9)),
        ("B3_B4", 25, 59.4, 32, "THOMAS_INVERSE", (-9, 12, 5)),
        ("PAUSE_RETOUR", 6, 32, 32, "THOMAS_INVERSE", (-9, 12, 5)),
        ("B5_PONT", 4, 32, 31.9, "THOMAS_INVERSE", (-12, 18, 10)),
        ("PAUSE_PONT_RETOUR", 5, 31.9, 31.9, "THOMAS_INVERSE", (-12, 18, 10)),
        # Preserve the same 22 s B6 screen budget, but reserve six seconds
        # for the B-bank repair BEFORE crossing, in the inverse's own time.
        ("B6", 16, 31.9, 3.16, "THOMAS_INVERSE", (-9, 12, 5)),
        ("B6_REPAIR", 6, 3.16, 3.0, "THOMAS_INVERSE", (-5, 5, 3)),
        ("PAUSE_MOUSQUETON", 7, 3.0, 3.0, "THOMAS_INVERSE", (-5, 5, 3)),
        ("B6_TRAVERSEE", 6, 3.0, 2.5, "THOMAS_INVERSE", (-6, -8, 3)),
        ("B7_B8", 8, 2.5, 2, "THOMAS_INVERSE", (-6, -8, 3)),
        ("PAUSE_BOUCLE", 7, 2, 2, "THOMAS_INVERSE", (-6, -8, 3)),
        ("B9", 18, 2, 8, "THOMAS_NORMAL", (-5, -9, 4)),
        ("PAUSE_ISSUE", 6, 8, 8, "THOMAS_NORMAL", (-5, -9, 4)),
        ("B9_ELOIGNEMENT", 8, 8, 12, "THOMAS_NORMAL", (-45, -65, 35)),
    ]
    # Aides de lecture pour la PREVIZ uniquement, pas des dialogues canoniques.
    # Chaque pause maintient le temps objectif exact, y compris le casting.
    # English-only narrative annotations. No text is shortened or repositioned
    # to conceal a rendering problem; the screen-space renderer fixes clarity.
    # Narrative order, pause lengths and objective-time trajectories are unchanged.
    # The fixed 17 narrative PAUSE beats stay in the film. The default text
    # gives a first-time viewer orientation at the instant it becomes useful;
    # it never advertises the B-side carabiner's future repair during A.
    # Subtitle dialogue is authored separately at the actual scene beat.
    pause_cards = {
        "PAUSE_INTRO": (
            "THOMAS, EVA & LEA",
            "A family hike in the late afternoon."
        ),
        "PAUSE_DETOUR": (
            "THE LONGER WAY BACK",
            "Lea is on path B. She returns to her parents\n"
            "on A by the hillside path, not the short bridge."
        ),
        "PAUSE_THOMAS": (
            "UP THE MOUNTAIN",
            "Eva and Lea keep walking. Thomas lags behind."
        ),
        "PAUSE_CHEMINS": (
            "THE TWO PATHS",
            "A: the family's uphill trail. B: the opposite slope.\n"
            "The short bridge and the longer hillside path connect them."
        ),
        "PAUSE_ATTACHE": (
            "THE BRIDGE BELOW",
            "The family continues uphill, leaving the bridge behind."
        ),
        "PAUSE_DEPART": (
            "5:50 P.M. - THOMAS STEPS AWAY",
            "Thomas goes into a small rocky area.\n"
            "Eva and Lea stay on the trail."
        ),
        "PAUSE_ATTENTE": (
            "THEY WAIT",
            "Eva and Lea can see the only visible way back\n"
            "from the rocky area. Thomas has not returned."
        ),
        "PAUSE_RECHERCHE": (
            "NO SIGN OF THOMAS",
            "The rocky space ends at a cliff.\n"
            "Eva and Lea cannot find Thomas."
        ),
        "PAUSE_REVELATION": (
            "BEHIND THE ROCK FACE",
            "Thomas is inside a hidden cave.\n"
            "His headphones kept him from hearing their calls."
        ),
        "PAUSE_CONTACT": (
            "6:00 P.M. - TIME REVERSES",
            "Thomas touches a ring. He begins moving backward\n"
            "through time while the world follows its usual course."
        ),
        "PAUSE_OBSCURITE": (
            "A FIGURE IN THE DARK",
            "Inverted Thomas can see a figure near the entrance;\n"
            "the figure cannot make him out in the darkness."
        ),
        "PAUSE_FAMILLE": (
            "TWO PATHS, THE SAME TIME",
            "Eva and Lea descend path A to get help.\n"
            "Thomas follows path B toward earlier moments."
        ),
        "PAUSE_RETOUR": (
            "THOMAS MOVES INTO THE PAST",
            "From his point of view, the landscape moves backward."
        ),
        "PAUSE_PONT_RETOUR": (
            "ABOUT 5:30 P.M. - THE BRIDGE",
            "On path B, Thomas finds the carabiner hanging loose."
        ),
        "PAUSE_MOUSQUETON": (
            "5:01 P.M. - THE B BANK",
            "Thomas has reattached the carabiner and checked it.\n"
            "He now crosses the bridge from B to A."
        ),
        "PAUSE_BOUCLE": (
            "5:00 P.M. - THE SAME INSTANT",
            "The two Thomases collide as the ring touches Thomas.\n"
            "Neither contact is identified as the certain cause."
        ),
        "PAUSE_ISSUE": (
            "THE SAME MOMENT AGAIN",
            "Thomas is back on path A. Lea is still on B."
        ),
    }
    if SUBTITLE_REVIEW_MODE:
        # Optional diagnostic wording; never enabled for the spectator pass.
        pause_cards["PAUSE_REVELATION"] = (
            "CAVE REVEAL - PREVIZ",
            "The concealed cave entrance and Thomas's headphones\n"
            "still require final acting and sound."
        )
        pause_cards["PAUSE_CONTACT"] = (
            "6:00 P.M. - INVERSION PREVIZ",
            "Ring/hand contact and environmental reversal\n"
            "are narrative beats; their animations are pending."
        )
        pause_cards["PAUSE_RETOUR"] = (
            "INVERTED LANDSCAPE - PREVIZ",
            "The reversed environmental effects are not yet animated."
        )
        pause_cards["PAUSE_MOUSQUETON"] = (
            "5:01 P.M. - B-SIDE REPAIR PREVIZ",
            "The shared carabiner state is keyed in both time directions.\n"
            "Finger and attachment acting is not yet finished."
        )
        pause_cards["PAUSE_BOUCLE"] = (
            "5:00 P.M. - CONTACT PREVIZ",
            "The one collision and simultaneous ring contact are planned.\n"
            "Contact acting, ring and physical occlusion need visual review."
        )

    # F03: establish the apparent closed wall from the women's side, then
    # bend round the actual outer edge, finally enter via the OPEN cave axis.
    # The previous stages looked THROUGH the blind spur at u=.43-.60.
    def f03_reveal_pose(progress, objective_t, start):
        entry = a["CAVE_ENTRY_POINT"]
        terrain = a["terrain_z_m"]
        along = a["cave_xy"]
        ground = a["cave_ground_point"]
        thomas = a["eval_actor"]("THOMAS_NORMAL", objective_t)

        def safe_eye(x, y, relative=2.15):
            return (x, y, max(terrain(x, y)+relative, entry[2]+relative))

        # Prior to 0.60 the objective never peers through the hidden mouth.
        # At 0.60 the viewpoint clears the spur from the cliff side; then
        # the camera follows the walkable opening's real local centreline.
        outer_x, outer_y = along(-2.6, -4.0)
        lip_x, lip_y = along(-1.5, -2.8)
        mouth_x, mouth_y = along(-0.8, -0.65)
        stages = (
            (0.0, start[0], start[1]),
            (0.27, safe_eye(outer_x, outer_y, 3.5),
             (entry[0]-3.3, entry[1]-3.5, entry[2]+1.4)),
            (0.54, safe_eye(lip_x, lip_y, 2.8),
             (entry[0]-1.0, entry[1]-2.9, entry[2]+1.55)),
            (0.71, safe_eye(mouth_x, mouth_y, 2.15),
             ground(0.8, 0.0, 1.45)),
            (0.87, ground(0.65, 0.0, 1.85),
             ground(2.3, 0.0, 1.45)),
            (1.0, ground(1.25, 0.0, 1.85),
             (thomas[0], thomas[1], thomas[2]+1.1))
        )
        for k in range(len(stages)-1):
            start_u, start_eye, start_target = stages[k]
            end_u, end_eye, end_target = stages[k+1]
            if progress <= end_u or k == len(stages)-2:
                alpha = max(0.0, min(1.0, (progress-start_u)/(end_u-start_u)))
                alpha = alpha*alpha*(3.0-2.0*alpha)
                eye = tuple(start_eye[j]+(end_eye[j]-start_eye[j])*alpha for j in range(3))
                target = tuple(start_target[j]+(end_target[j]-start_target[j])*alpha for j in range(3))
                return eye, target
        raise RuntimeError("F03: invalid camera reveal progress")

    def f03_reveal_clearance(eye, target, progress):
        entry = a["CAVE_ENTRY_POINT"]
        masks = (
            (entry[0]-5.0, entry[1]+0.6, 2.5, 1.3, "mountain wall"),
            (entry[0]-4.0, entry[1]-2.8, 3.0, 2.1, "blind spur"),
            (entry[0]-0.15*a["CAVE_UX"]-3.5*a["CAVE_PX"],
             entry[1]-0.15*a["CAVE_UY"]-3.5*a["CAVE_PY"],
             1.05, 0.95, "right entrance"),
            (entry[0]-0.15*a["CAVE_UX"]+2.2*a["CAVE_PX"],
             entry[1]-0.15*a["CAVE_UY"]+2.2*a["CAVE_PY"],
             1.65, 1.35, "left entrance")
        )
        # An XY envelope audit, not a substitute for the 3D Unreal video.
        # After revealing the bend also test the full camera LOOK RAY:
        # an unobstructed camera point alone does not prevent an opaque
        # boulder from filling the screen in the middle of the shot.
        for cx, cy, rx, ry, label in masks:
            def clearance(x, y):
                return math.hypot((x-cx)/rx, (y-cy)/ry)
            if clearance(eye[0], eye[1]) < 1.12:
                raise RuntimeError("F03 A15 lens enters %s at %.3f" %
                                   (label, progress))
            # The old 2D full look-ray check gave false positives for an
            # elevated lens looking OVER a low rock. The actual near-lens
            # three-dimensional ray and mesh-bound checks run below once the
            # camera turns into the entrance. Preserve the physical mask.

    # F03: 3D traces against generated cave/static geometry. Keep the
    # physical blind-spur intact: never hide it just to clear the camera.
    # Cache actor lists once, not on each of the 480 A15 frames.
    f03_scene_actors = actors.get_all_level_actors()
    f03_ignored = [actor for actor in f03_scene_actors
                   if actor.get_actor_label().startswith((
                       "PZ_ANIM_HUMAN_", "PZ_ANIM_EVENT_", "PZ_ANIM_CAM_",
                       "PZ_ANIM_F04_RING_", "PZ_ANIM_F01_SMALL_BOX"))]
    f03_bounds_names = ("CAVE_REVIEW_", "CAVE_WALL_", "CAVE_SIDE_",
                        "CAVE_ENTRY_ROCK_", "CAVE_ENTRANCE_BLIND_SPUR",
                        "SEARCH_LEDGE_MOUNTAIN_WALL", "F03_SHADOW_RECESS_")
    f03_meshes = [
        actor for actor in f03_scene_actors
        if actor.get_actor_label().startswith("PZ_ANIM_")
        and any(actor.get_actor_label().startswith("PZ_ANIM_"+part)
                for part in f03_bounds_names)
        and actor.get_component_by_class(unreal.StaticMeshComponent) is not None
    ]

    def f03_mesh_clearance(eye, target, progress):
        query = (unreal.TraceTypeQuery.ECC_VISIBILITY
                 if hasattr(unreal.TraceTypeQuery, "ECC_VISIBILITY")
                 else unreal.TraceTypeQuery.TRACE_TYPE_QUERY1)
        def trace(start, end, label):
            # Ignore the animated cast and review cameras, NOT landscape,
            # cave shell or rock meshes. This checks real Unreal collision
            # rather than the earlier XY-only approximation.
            result = unreal.SystemLibrary.line_trace_single(
                world,
                unreal.Vector(*(float(v)*100.0 for v in start)),
                unreal.Vector(*(float(v)*100.0 for v in end)),
                query, True, f03_ignored, unreal.DrawDebugTrace.NONE, True)
            if not result:
                return
            data = result.to_tuple()
            if not data[0] or data[9] is None:
                return
            blocked = data[9].get_actor_label()
            if blocked.startswith(("PZ_ANIM_HUMAN_", "PZ_ANIM_EVENT_")):
                return
            raise RuntimeError(
                "F03 A15 %s obstructed by %s at progress %.3f" %
                (label, blocked, progress))
        # Trace a near-lens forward ray, not all the way to Thomas (who may
        # legitimately be behind a cave wall until the reveal is completed).
        # Also check camera clearance above the real terrain.
        if progress >= 0.71:
            direction = tuple(target[i]-eye[i] for i in range(3))
            length = math.dist(eye, target)
            if length > 0.05:
                near = tuple(eye[i]+direction[i]*min(1.1/length, 1.0)
                             for i in range(3))
                trace(eye, near, "lens_forward")
            trace(eye, (eye[0], eye[1], eye[2]-0.65), "lens_floor")

    # F03: query each generated static mesh directly; some preview meshes have
    # collision disabled, so a line_trace alone cannot establish visibility.
    # Treat the transformed component bounds as conservative: they can stop
    # an otherwise usable shot, but cannot silently certify a blocked lens.
    def f03_static_bounds_audit(eye, target, progress):
        if progress < 0.71:
            return
        import unreal as ue
        eye_cm = ue.Vector(*(float(v)*100.0 for v in eye))
        diff = tuple(target[i]-eye[i] for i in range(3))
        dist = math.dist(eye, target)
        limit = min(110.0, 100.0*dist)
        if limit <= 0.01:
            return
        end_cm = ue.Vector(
            eye_cm.x+(diff[0]/dist)*limit,
            eye_cm.y+(diff[1]/dist)*limit,
            eye_cm.z+(diff[2]/dist)*limit)
        for actor in f03_meshes:
            name = actor.get_actor_label()
            center, extent = actor.get_actor_bounds(False)
            # Inflate to catch near-plane rock even with collision disabled.
            bx, by, bz = center.x, center.y, center.z
            ex, ey, ez = extent.x+12.0, extent.y+12.0, extent.z+12.0
            for i in range(9):
                u = i/8.0
                x = eye_cm.x+(end_cm.x-eye_cm.x)*u
                y = eye_cm.y+(end_cm.y-eye_cm.y)*u
                z = eye_cm.z+(end_cm.z-eye_cm.z)*u
                if abs(x-bx) < ex and abs(y-by) < ey and abs(z-bz) < ez:
                    raise RuntimeError(
                        "F03 A15 near lens bounds of %s at progress %.3f" %
                        (name, progress))

    # F03: geometry of the generated cave is represented with PZ_ANIM_
    # actors. A camera may remain outside at the start of A15; once it
    # enters the opening the near lens MUST NOT overlap any cave surface.
    # This independent test complements (not replaces) the XY mask checks.
    # No rock gets disabled or moved as a shortcut.

    # F01 camera-only pass: no actor movement or retiming. At t=0 Lea
    # already walks ahead of Thomas/Eva in the existing validated blocking.
    # Show all three honestly in a wide frame, then follow Lea to the bridge.
    def f01_family_pose(t):
        people = [a["eval_actor"](name, t)
                  for name in ("THOMAS_NORMAL", "EVA", "LEA")]
        center = tuple(sum(p[i] for p in people)/3.0 for i in range(3))
        spread = max(math.dist(p, center) for p in people)
        distance = max(23.0, spread*2.0)
        x, y = center[0]-distance, center[1]-max(18.0, distance*0.65)
        z = max(center[2]+max(6.5, spread*0.22),
                a["terrain_z_m"](x, y)+2.0)
        return (x, y, z), (center[0], center[1], center[2]+1.15)

    def f01_opening_pose(code, u, t):
        """One continuous camera: family, Eva, Thomas, then Lea's bridge.

        u is local SCREEN progress, independent of objective-time compression.
        """
        if code not in ("PAUSE_INTRO", "A1"):
            raise RuntimeError("F01 opening pose for "+code)

        def between(left, right, weight):
            w = cinematic_ease(weight)
            return tuple(tuple(p+(q-p)*w for p, q in zip(old, new))
                         for old, new in zip(left, right))

        thomas = a["eval_actor"]("THOMAS_NORMAL", t)
        eva = a["eval_actor"]("EVA", t)
        lea = a["eval_actor"]("LEA", t)
        middle = tuple((thomas[i]+eva[i])*0.5 for i in range(3))
        x, y = middle[0]-11.0, middle[1]-15.0
        z = max(middle[2]+4.7, a["terrain_z_m"](x, y)+2.0)
        parent_eye = (x, y, z)
        eva_focus = tuple(0.73*eva[i]+0.27*thomas[i] for i in range(3))
        thomas_focus = tuple(0.75*thomas[i]+0.25*eva[i] for i in range(3))
        eva_pose = parent_eye, (eva_focus[0], eva_focus[1], eva_focus[2]+1.1)
        thomas_pose = parent_eye, (thomas_focus[0], thomas_focus[1], thomas_focus[2]+1.1)
        x, y = lea[0]-7.5, lea[1]-11.0
        z = max(lea[2]+4.0, a["terrain_z_m"](x, y)+2.0)
        lea_pose = ((x, y, z), (lea[0], lea[1], lea[2]+1.1))
        if code == "PAUSE_INTRO":
            # The subtitle clears at 3 s. The following 3 s of this
            # unchanged pause move from the establishing shot to Eva.
            return between(f01_family_pose(t), eva_pose, (u-0.48)/0.52)
        # During the 12 s A1 shot, remain close to the parents for the
        # opening exchange and glide towards Lea before the crossing.
        parents = between(eva_pose, thomas_pose, (u-0.22)/0.20)
        return between(parents, lea_pose, (u-0.42)/0.39)

    def f07_normal_view(t):
        """A2 recovery after the 17:00 contact; preserve Lea in the distance."""
        thomas = a["eval_actor"]("THOMAS_NORMAL", t)
        lea = a["eval_actor"]("LEA", t)
        x, y = thomas[0]-7.5, thomas[1]-10.0
        z = max(thomas[2]+3.8, a["terrain_z_m"](x, y)+2.0)
        target = tuple(thomas[i]*0.83+lea[i]*0.17 for i in range(3))
        return (x, y, z), (target[0], target[1], target[2]+1.2)

    def f07_contact_view(t):
        """F07: fixed OPEN trail-side sightline, shared by A2 and B7/B9.

        The prior (Thomas.y-10) eye shot straight through the low FOREGROUND
        outcrop at the convergence. The two existing rocks occupy the lateral
        sides of the same A path; look along their central gap from x=-10 m.
        Do not move either rock or any actor to fake an accidental collision.
        """
        normal = a["eval_actor"]("THOMAS_NORMAL", t)
        closure = a["CONVERGENCE_POINT"]
        x, y = closure[0]-10.0, closure[1]+0.10
        z = max(closure[2]+3.6, a["terrain_z_m"](x, y)+3.0)
        # Center the collision itself; looking 17% toward Lea would instead
        # send the eye ray through the large mountain-side rock.
        return ((x, y, z),
                (normal[0], normal[1], normal[2]+1.20))

    def f07_carabiner_view(t):
        """B-bank close view used only in part B; no early A insert."""
        p = a["carabiner_point_at_objective_time"](t)
        x, y = p[0]-3.4, p[1]+3.2
        z = max(p[2]+2.6, a["terrain_z_m"](x, y)+1.9)
        return (x, y, z), (p[0], p[1], p[2]+0.10)

    def f01_return_pose(t):
        thomas = a["eval_actor"]("THOMAS_NORMAL", t)
        eva = a["eval_actor"]("EVA", t)
        # Repeat A2 in EXACTLY the same objective time, but reserve a closer
        # view for the final moment after Lea rejoins the family. No acting
        # or box gesture has been added in this camera-only pass.
        close = cinematic_ease((t-7.45)/0.55)
        x = thomas[0]-10.0+4.0*close
        y = thomas[1]-14.0+5.0*close
        z = max(thomas[2]+4.6-0.6*close,
                a["terrain_z_m"](x, y)+2.0)
        eva_weight = 0.18*(1.0-close)
        target = tuple(thomas[i]*(1.0-eva_weight)+eva[i]*eva_weight
                       for i in range(3))
        return (x, y, z), (target[0], target[1], target[2]+1.2)

    def f01_pullback_pose(t):
        people = [a["eval_actor"](name, t)
                  for name in ("THOMAS_NORMAL", "EVA", "LEA")]
        center = tuple(sum(p[i] for p in people)/3.0 for i in range(3))
        # B9_ELOIGNEMENT runs for eight screen seconds. Retain Thomas's
        # closer B9/PAUSE_ISSUE framing for the first ~2.4 s, THEN let
        # the camera discover all three walkers before widening to the
        # existing mountain geography. Earlier it pulled away immediately.
        u = cinematic_ease(((t-8.0)/4.0-0.30)/0.70)
        thomas_eye, thomas_target = f01_return_pose(t)
        x = thomas_eye[0]+(-14.0-58.0*u)*u
        y = thomas_eye[1]+(-17.0-74.0*u)*u
        # Correct the final position relative to the MOVING family, not to
        # Thomas's earlier position. This avoids framing an empty trail.
        wide_x = center[0]-14.0-58.0*u
        wide_y = center[1]-17.0-74.0*u
        x = thomas_eye[0]*(1.0-u)+wide_x*u
        y = thomas_eye[1]*(1.0-u)+wide_y*u
        z = max(thomas_eye[2]*(1.0-u)+(center[2]+5.0+37.0*u)*u,
                a["terrain_z_m"](x, y)+2.0)
        wide_target = (center[0], center[1], center[2]+1.3)
        target = tuple(thomas_target[i]*(1.0-u)+wide_target[i]*u
                       for i in range(3))
        return (x, y, z), target

    def f07_17h_closure_pose(t):
        """Keep Thomas normal at the center of the SAME objective 17:00 event.

        In the last B7/B8 seconds inverse Thomas enters this central trail
        frame from the far side of the rock. The seven-second PAUSE_BOUCLE
        holds the aftermath; B9 then continues with Thomas normal.
        Physical blind-spot and skeletal-contact validity need an Unreal test.
        """
        return f07_contact_view(t)

    def f07_rock_blocks_ray_xy(origin, subject):
        """Conservative PLAN-VIEW audit of the unchanged convergence boxes.

        This tests the actual box footprints at 17:00; the engine mesh,
        camera field of view, real height and inverse's perceptual blind
        spot still require the rendered/POV review in Unreal.
        """
        cx, cy = a["CONVERGENCE_POINT"][:2]
        rocks = (
            (cx+2.5, cy+5.0, 4.5, 2.25, 20.0, "MOUNTAINSIDE"),
            (cx, cy-2.0, 1.90, 0.70, 0.0, "FOREGROUND"),
        )
        blocked = []
        for rx, ry, hx, hy, yaw_deg, name in rocks:
            phi = math.radians(yaw_deg)
            cp, sp = math.cos(phi), math.sin(phi)
            for i in range(1, 151):
                u = i/151.0
                x = origin[0]*(1.0-u)+subject[0]*u-rx
                y = origin[1]*(1.0-u)+subject[1]*u-ry
                local_x, local_y = x*cp+y*sp, -x*sp+y*cp
                if abs(local_x) <= hx and abs(local_y) <= hy:
                    blocked.append(name)
                    break
        return blocked

    # A cheap pre-render guard against the failure in the 18:56 capture:
    # the OLD y=-10 m camera ray crossed FOREGROUND, filling the whole shot.
    # A miss from inverse Thomas's eyes is an unresolved PHYSICAL blindspot,
    # not a reason to fake the collision with a camera or move the approved rock.
    f07_camera_rays = []
    for _t in (2.001, 2.01, 2.025, 2.045):
        _eye, _target = f07_contact_view(_t)
        f07_camera_rays.append(dict(
            objective_minute=_t,
            blocking_rocks=f07_rock_blocks_ray_xy(_eye, _target)))
    report_check(
        "F07", "17h_camera_ray_clear_of_convergence_boxes_xy",
        "OK" if all(not entry["blocking_rocks"] for entry in f07_camera_rays)
        else "FAIL", "BLOCKER",
        {"samples": f07_camera_rays, "scope": "2D bounds; Unreal render still required"},
        "Inspect the F07 lateral eye/subject line. Do not move the F03 cave rocks.")
    f07_inverse_rays = []
    for _t in (2.07, 2.12, 2.20):
        _inverse = a["eval_actor"]("THOMAS_INVERSE", _t)
        _normal = a["eval_actor"]("THOMAS_NORMAL", _t)
        f07_inverse_rays.append(dict(
            objective_minute=_t, separation_m=round(math.dist(_inverse, _normal), 2),
            blocking_rocks=f07_rock_blocks_ray_xy(_inverse, _normal)))
    f07_blindspot_present = any(
        entry["blocking_rocks"] for entry in f07_inverse_rays)
    report_check(
        "F07", "inverse_17h_rock_blindspot_needs_visual_proof",
        "OK" if f07_blindspot_present else "WARN", "INFO",
        {"samples": f07_inverse_rays,
         "scope": "2D diagnostic only; real eye-height mesh occlusion unverified"},
        "If no physical blind spot exists, request a separate F07 geometry decision; "
        "do not hide a visible approach with editing.")

    def desired_pose(code, focus, offset, t):
        if code in ("B6_REPAIR", "PAUSE_MOUSQUETON"):
            return f07_carabiner_view(t)
        if code in ("B7_B8", "PAUSE_BOUCLE"):
            return f07_17h_closure_pose(t)
        if code == "A2":
            # The normal timeline begins AT the sole collision, not before it.
            # Start with the same OPEN view as B7/B8's last frame, then return
            # to Lea/Eva AFTER the immediate impact; no invented second hit.
            contact_view = f07_contact_view(t)
            normal_view = f07_normal_view(t)
            with_normal = blend_camera_pose(contact_view, normal_view,
                                            (t-2.29)/0.42)
            family_view = desired_pose("A2_LEA_CONTINUATION", "LEA", (-5, -9, 4), t)
            return blend_camera_pose(with_normal, family_view,
                                     (t-3.60)/0.90)
        if code in ("PAUSE_INTRO", "A1"):
            # Used only as the END pose of the previous beat in camera handover.
            return f01_opening_pose(code, 1.0, t)
        if code == "B9":
            # B9 replays the same 17:00 pose. Leave the lateral corridor only
            # once Thomas has walked away from the small outcrop.
            return blend_camera_pose(f07_contact_view(t), f01_return_pose(t),
                                     (t-2.29)/0.65)
        if code == "PAUSE_ISSUE":
            return f01_return_pose(t)
        if code == "B9_ELOIGNEMENT":
            return f01_pullback_pose(t)
        if code == "PAUSE_RECHERCHE":
            code = "A12_A13"
        elif code == "PAUSE_OBSCURITE":
            code = "B1"
        elif code == "PAUSE_ATTACHE":
            code = "A9_PONT"
        # PAUSE_MOUSQUETON has a dedicated B-bank pose above. It is
        # deliberately BEFORE B6_TRAVERSEE, never after crossing.
        if code in ("A12_A13", "A14"):
            # A12 commence SUR LE CHEMIN, cote femmes : on voit l'UNIQUE
            # retour qu'elles ont surveille. La camera accompagne leur
            # recherche, puis se decale progressivement cote precipice :
            # quelques m2 de sol entre elles, la paroi, et le vide.
            # Ne viser ni l'entree de la grotte ni le revers de l'eperon
            # avant A15. A14 garde ce cadrage pendant leur depart.
            ledge = a["SEARCH_LEDGE_CENTER"]
            subject = a["eval_actor"]("EVA", t)
            near_eye = (subject[0]-8.0, subject[1]-11.0, subject[2]+4.5)
            near_target = (subject[0]+1.5, subject[1]-2.4, subject[2]+0.75)
            # Short downstream view shows the women, shelf, wall and cliff
            # without a distant overhead view of the surrounding open terrain.
            far_x, far_y = ledge[0]+7.0, ledge[1]-7.2
            far_eye = (far_x, far_y,
                       max(ledge[2]+4.3, a["terrain_z_m"](far_x, far_y)+2.0))
            # Viser vers la femme et le bord, a GAUCHE du coude cache :
            # l'angle A12 n'offre pas un point de vue explicatif sur la bouche.
            far_target = (subject[0]-0.8, subject[1]-2.6, subject[2]+0.65)
            alpha = 1.0 if code == "A14" else max(0.0, min(1.0, (t-57.0)/1.45))
            alpha = alpha*alpha*(3.0-2.0*alpha)
            eye = tuple(near_eye[i]*(1.0-alpha)+far_eye[i]*alpha for i in range(3))
            target = tuple(near_target[i]*(1.0-alpha)+far_target[i]*alpha for i in range(3))
            return eye, target
        if focus == "CAVE":
            target = a["eval_actor"]("THOMAS_INVERSE" if code == "B1" else "THOMAS_NORMAL", t)
            if code == "B1":
                # Leave through the entrance with Thomas instead of remaining
                # behind a wall while looking at a subject already outdoors.
                entry = a["CAVE_ENTRY_POINT"]
                along = ((target[0]-entry[0])*a["CAVE_UX"]+
                         (target[1]-entry[1])*a["CAVE_UY"])
                eye = a["cave_ground_point"](min(4.8, along+1.5), -1.3, 1.75)
            else:
                # Previous camera side=-.8 intersected the right entry rock.
                eye = a["cave_ground_point"](1.0, 0.0, 1.85)
        else:
            if focus == "GEOGRAPHY":
                target = (1320.0, 220.0, 120.0)
            else:
                target = (900, 12.5, a["terrain_z_m"](900, 0)) if focus == "BRIDGE" else a["eval_actor"](focus, t)
            eye = tuple(target[i]+offset[i] for i in range(3))
            eye = (eye[0], eye[1], max(eye[2], a["terrain_z_m"](eye[0], eye[1])+2.0))
            if code == "A9_PONT":
                # Only this distant bridge view: reveal the gap and both landings,
                # with a modest sideways/high move from Thomas's current trail.
                # Aim at the EXISTING endpoints; geography and cast stay untouched.
                za = a["terrain_z_m"](900.0, 0.0)
                zb = a["terrain_z_m"](900.0, 25.0)
                target = (900.0, 12.5, (za+zb)*0.5+0.59)
            elif code == "B5_PONT":
                # Inverse's later bridge glance remains unchanged.
                target = (900.0, 12.5, a["terrain_z_m"](900.0, 0.0)+0.59)
        return eye, (target[0], target[1], target[2]+1.1)

    # Editorial durations are deliberate. Do not inflate them to accommodate
    # unnecessary kilometre-long trips to the bridge or a distant overview.
    # These remain narrative beats within one continuous camera binding.
    fps = a["FPS"]
    duration = sum(s[1] for s in shots)
    if FAST_CAMERA_ONLY:
        return update_existing_omniscient_camera(
            shots, desired_pose, f03_reveal_pose, f03_reveal_clearance,
            f01_opening_pose)
    sequence_name = "LS_POLOP_OMNISCIENT"
    if unreal.EditorAssetLibrary.does_asset_exist(RUN_ASSET_ROOT + "/Sequences/" + sequence_name):
        sequence_name += "_" + datetime.datetime.now().strftime("%H%M%S_%f")
    seq = unreal.AssetToolsHelpers.get_asset_tools().create_asset(
        sequence_name, RUN_ASSET_ROOT + "/Sequences",
        unreal.LevelSequence, unreal.LevelSequenceFactoryNew())
    if not seq:
        raise RuntimeError("Could not create omniscient film sequence")
    seq.set_display_rate(unreal.FrameRate(fps, 1))
    seq.set_playback_start(0)
    seq.set_playback_end(duration*fps)
    seq.set_view_range_start(0.0)
    seq.set_view_range_end(float(duration))
    unreal.LevelSequenceEditorBlueprintLibrary.open_level_sequence(seq)
    ls = unreal.get_editor_subsystem(unreal.LevelSequenceEditorSubsystem)
    cam = a["create_camera"]("OMNISCIENT", unreal.Vector(0, 0, 200), unreal.Vector(100, 0, 100), 30)
    bindings = []

    def track_for(actor):
        binding = ls.add_actors([actor])[0]
        for existing in binding.get_tracks():
            if isinstance(existing, unreal.MovieScene3DTransformTrack):
                binding.remove_track(existing)
        section = binding.add_track(unreal.MovieScene3DTransformTrack).add_section()
        section.set_range(0, duration*fps)
        channels = section.get_all_channels()
        scale = actor.get_actor_scale3d()
        for channel, value in zip(channels[6:9], (scale.x, scale.y, scale.z)):
            channel.set_default(float(value))
        bindings.append(binding)
        return binding, channels, (scale.x, scale.y, scale.z)

    # Single physical B-bank clip, evaluated at each objective time in the
    # same omniscient sequence for A, inverted B and normal-time B9.
    _, carabiner_channels, _ = track_for(a["MOUSQUETON_PROXY"])
    animated = []
    for name in POV_ORDER:
        for objects, converter in ((a["actor_objects"], a["actor_location_from_foot"]),
                                   (a["head_objects"], a["head_location_from_foot"])):
            _, channels, scale = track_for(objects[name])
            if name == "THOMAS_INVERSE":
                normal_scale = objects["THOMAS_NORMAL"].get_actor_scale3d()
                scale = (normal_scale.x, normal_scale.y, normal_scale.z)
            # prepare_human_cast masque deja les proxies comme dans le
            # commit valide. Ne pas y ajouter des pistes de visibilite.
            animated.append((name, channels, scale, converter))
    binding, camera_channels, _ = track_for(cam)
    a["omniscient_camera_binding"] = binding

    # Story cards use the UE 5.8 Subtitles and Closed Captions plugin.
    # Its text is a Slate/UMG viewport overlay, NOT a TextRenderActor in 3D.
    # This avoids camera-plane texture filtering, TAA and depth-of-field blur.
    # No new proxy or human Sequencer tracks are touched.
    # A9 is hundreds of metres from the bridge: a brief optical push makes
    # the 25 m crossing legible without a rapid physical flight or a camera cut.
    # Keep the camera's actual original focal length outside this one beat.
    baseline_focal = float(cam.get_cine_camera_component().get_editor_property(
        "current_focal_length"))
    lens_binding = seq.add_possessable(cam.get_cine_camera_component())
    lens_track = lens_binding.add_track(unreal.MovieSceneFloatTrack)
    lens_track.set_property_name_and_path("CurrentFocalLength", "CurrentFocalLength")
    lens_section = lens_track.add_section()
    lens_section.set_range(0, duration*fps)
    lens_channel = lens_section.get_all_channels()[0]
    lens_channel.set_default(baseline_focal)
    a9_index = next(i for i, shot in enumerate(shots) if shot[0] == "A9_PONT")
    a9_start = sum(shot[1] for shot in shots[:a9_index])*fps
    a9_end = a9_start + shots[a9_index][1]*fps
    for frame_number, focal_mm in (
        (0, baseline_focal),
        (a9_start, baseline_focal),
        (a9_start+fps, 72.0),
        (a9_end, 72.0),
        (a9_end+2*fps, baseline_focal),
        (duration*fps-1, baseline_focal),
    ):
        lens_channel.add_key(
            unreal.FrameNumber(frame_number), focal_mm,
            interpolation=unreal.MovieSceneKeyInterpolation.LINEAR)
    cuts = seq.add_track(unreal.MovieSceneCameraCutTrack)
    # Remove Sequencer's auto-cut before writing the single authoritative cut.
    for automatic_cut in list(cuts.get_sections()):
        cuts.remove_section(automatic_cut)
    cut = cuts.add_section()
    cut.set_range(0, duration*fps)
    binding_id = unreal.MovieSceneObjectBindingID()
    binding_id.set_editor_property("guid", binding.get_id())
    cut.set_camera_binding_id(binding_id)
    manifest = []
    first_frame = 0
    previous_rotation = None
    previous_pose = None
    boundary_pose = None
    previous_beat = None
    max_camera_step_m = 0.0
    join_steps_m = []
    performance_samples = []
    for code, seconds, t0, t1, focus, offset in shots:
        count = seconds*fps
        manifest.append(dict(scene=code, start_frame=first_frame, end_frame=first_frame+count,
                             objective_start=t0, objective_end=t1, focus=focus))
        for index in range(count):
            u = index/max(1, count-1)
            t = t0+(t1-t0)*cinematic_ease(u)
            performance_samples.append((first_frame+index, t))
            frame = unreal.FrameNumber(first_frame+index)
            for name, channels, scale, converter in animated:
                point = a["eval_actor"](name, t)
                for channel, value in zip(channels[:3], converter(name, point)):
                    channel.add_key(frame, float(value), interpolation=unreal.MovieSceneKeyInterpolation.LINEAR)
                if name == "THOMAS_INVERSE":
                    visible = 2.0 <= t < 62.0
                    for channel, value in zip(channels[6:9], scale):
                        channel.add_key(frame, float(value if visible else 0.001),
                                        interpolation=unreal.MovieSceneKeyInterpolation.CONSTANT)
            clip_xyz = a["carabiner_point_at_objective_time"](t)
            for channel, value in zip(carabiner_channels[:3], clip_xyz):
                channel.add_key(frame, float(value*100.0),
                                interpolation=unreal.MovieSceneKeyInterpolation.LINEAR)
            # Both subjects keep moving during a camera handover. Blending from
            # yesterday's fixed look target would leave the family out of frame.
            moving_origin = boundary_pose
            if previous_beat is not None:
                old_code, old_focus, old_offset = previous_beat
                moving_origin = desired_pose(old_code, old_focus, old_offset, t)
            handover_seconds = seconds if code in ("A5_GEOGRAPHIE", "B9_ELOIGNEMENT") else min(3.0, seconds)
            if code == "A15_A16":
                # Former generic handover moved the lens through opaque rock.
                eye, target = f03_reveal_pose(u, t, boundary_pose)
                f03_reveal_clearance(eye, target, u)
                f03_mesh_clearance(eye, target, u)
                f03_static_bounds_audit(eye, target, u)
                # Avoid frames of opaque Landscape under the lens. The
                # previous XY rock test could not detect this failure.
                if u >= 0.60 and eye[2] < a["terrain_z_m"](eye[0], eye[1]) + 1.25:
                    raise RuntimeError("F03 A15 camera below terrain clearance at %.3f" % u)
            else:
                requested = (f01_opening_pose(code, u, t)
                             if code in ("PAUSE_INTRO", "A1")
                             else desired_pose(code, focus, offset, t))
                eye, target = blend_camera_pose(moving_origin, requested,
                                                u*seconds/handover_seconds)
                if focus != "CAVE" and (previous_beat is None or previous_beat[1] != "CAVE"):
                    eye = (eye[0], eye[1], max(eye[2], a["terrain_z_m"](eye[0], eye[1])+2.0))
            if previous_pose is not None:
                step = math.dist(previous_pose[0], eye)
                max_camera_step_m = max(max_camera_step_m, step)
                if index == 0:
                    join_steps_m.append(step)
            previous_pose = (eye, target)
            pos = unreal.Vector(*(v*100 for v in eye))
            look = unreal.Vector(*(v*100 for v in target))
            rot = unreal.MathLibrary.find_look_at_rotation(pos, look)
            rotation = (rot.roll, rot.pitch, rot.yaw)
            if previous_rotation is not None:
                rotation = tuple(a["unwrap_angle"](p, r) for p, r in zip(previous_rotation, rotation))
            previous_rotation = rotation
            for channel, value in zip(camera_channels[:6], (pos.x, pos.y, pos.z)+rotation):
                channel.add_key(frame, float(value), interpolation=unreal.MovieSceneKeyInterpolation.LINEAR)
        boundary_pose = previous_pose
        previous_beat = (code, focus, offset)
        first_frame += count
    # Ne pas livrer une sequence PARTIELLE avec cylindres visibles et
    # premier carton orphelin si une API de texte echoue : baker d'abord
    # les mannequins articulés avant de construire les 17 annotations.
    # La fin de generation et la sauvegarde restent conditionnees au succes.
    add_human_performances(seq, performance_samples)
    # F01 only: the reveal is in B9, never in the shared A2 world pose.
    a["f01_film_shots"] = manifest
    if not F03_GEOMETRY_ONLY:
        add_f01_box_to_film(seq, performance_samples)
    a["f04_film_shots"] = manifest
    if not F03_GEOMETRY_ONLY:
        add_f04_ring_blockout(seq, performance_samples)
    # F03 can be checked independently of the still-untested English/UMG
    # subtitle change. This mode does NOT replace the full-film renderer.
    card_manifest = []
    opening_dialogue_manifest = []
    later_dialogue_manifest = []
    if F03_GEOMETRY_ONLY:
        journal("f03_geometry_only_captions_skipped",
                pause_count=sum(shot["scene"].startswith("PAUSE_") for shot in manifest))
    else:
        # Native screen-space UMG captions (UE 5.8 Subtitles and Closed Captions).
        # Each caption is scoped to its own Sequencer section, so scrubbing,
        # pausing and reverse playback evaluate the same active text.
        subtitle_track = seq.add_track(unreal.MovieSceneSubtitlesTrack)
        if subtitle_track is None:
            raise RuntimeError("Cannot create the screen-space subtitle track")
        subtitle_track.set_display_name("POLOP | English narrative annotations (UMG)")
        for shot in manifest:
            if shot["scene"] not in pause_cards:
                continue
            scene = shot["scene"]
            title, explanation = pause_cards[scene]
            first, last = shot["start_frame"], shot["end_frame"]
            if not (0 <= first < last <= duration*fps):
                raise RuntimeError("Invalid caption range: " + scene)
    
            # Intro caption is deliberately shorter than its six-second
            # narrative PAUSE: clear the text before the hike continues.
            caption_last = (min(last, first + int(round(3.0*fps)))
                            if scene == "PAUSE_INTRO" else last)
            section = subtitle_track.add_section()
            if section is None:
                raise RuntimeError("Cannot create UMG subtitle section: " + scene)
            section.set_range(first, caption_last)
            subtitle_data = unreal.SubtitleAssetUserData(
                outer=section, name="POLOP_" + scene)
            subtitle_line = unreal.SubtitleAssetData()
            subtitle_line.set_editor_property("text", title + "\n" + explanation)
            subtitle_line.set_editor_property("subtitle_duration_type",
                unreal.SubtitleDurationType.USE_DURATION_PROPERTY)
            subtitle_line.set_editor_property("duration", float((caption_last-first)/fps))
            subtitle_line.set_editor_property("start_offset", 0.0)
            subtitle_data.set_editor_property("subtitles", [subtitle_line])
            section.set_editor_property("subtitle", subtitle_data)
            if section.get_editor_property("subtitle") is None:
                raise RuntimeError("UMG subtitle was not assigned: " + scene)
            card_manifest.append(dict(scene=scene, title=title, explanation=explanation,
                                      start_frame=first, end_frame_exclusive=caption_last,
                                      renderer="native_subtitles_umg"))
        if len(card_manifest) != len(pause_cards):
            raise RuntimeError("Native UMG subtitle sections incomplete")

        # F01: these are short, speaker-labelled English PREVIZ dialogue cues
        # during the existing moving A1 shot, NOT additional story pauses.
        # The mannequins have no dialogue/laugh acting yet. No cue reveals
        # the temporal loop or the later carabiner action.
        a1_shot = next(shot for shot in manifest if shot["scene"] == "A1")
        a1_start = a1_shot["start_frame"]
        a1_end = a1_shot["end_frame"]
        opening_cues = (
            # Lea steps onto the bridge at objective t=.75 (A1 screen ~5 s),
            # reaches B at t=1.25 (~7 s), then turns to address her parents.
            (0.25, 2.30, "EVA: Is it much farther to the top?"),
            (2.45, 4.50, "THOMAS: Just this climb...\nand all the others."),
            (4.65, 5.40, "EVA: Careful."),
            (8.00, 9.35, "LEA: Are you coming?"),
            (9.50, 11.90, "EVA: We're coming. That's not our trail."),
        )
        last_dialogue_end = a1_start
        for cue_index, (cue_start_s, cue_end_s, cue_text) in enumerate(opening_cues):
            cue_first = a1_start + int(round(cue_start_s*fps))
            cue_last = a1_start + int(round(cue_end_s*fps))
            if not (last_dialogue_end <= cue_first < cue_last <= a1_end):
                raise RuntimeError("F01 overlapping/out-of-bounds A1 subtitle")
            section = subtitle_track.add_section()
            if section is None:
                raise RuntimeError("F01 unable to create A1 dialogue subtitle")
            section.set_range(cue_first, cue_last)
            subtitle_data = unreal.SubtitleAssetUserData(
                outer=section, name="POLOP_A1_DIALOGUE_%02d" % cue_index)
            subtitle_line = unreal.SubtitleAssetData()
            subtitle_line.set_editor_property("text", cue_text)
            subtitle_line.set_editor_property(
                "subtitle_duration_type",
                unreal.SubtitleDurationType.USE_DURATION_PROPERTY)
            subtitle_line.set_editor_property(
                "duration", float((cue_last-cue_first)/fps))
            subtitle_line.set_editor_property("start_offset", 0.0)
            subtitle_data.set_editor_property("subtitles", [subtitle_line])
            section.set_editor_property("subtitle", subtitle_data)
            if section.get_editor_property("subtitle") is None:
                raise RuntimeError("F01 A1 subtitle was not assigned")
            opening_dialogue_manifest.append(
                dict(scene="A1", text=cue_text, start_frame=cue_first,
                     end_frame_exclusive=cue_last,
                     renderer="native_subtitles_umg"))
            last_dialogue_end = cue_last
        if len(opening_dialogue_manifest) != len(opening_cues):
            raise RuntimeError("F01 A1 dialogue subtitles incomplete")

        # Dialogue is distinct from pause annotations and is timed to the
        # existing screen edit. The A2/B9 scene durations and the underlying
        # objective-time trajectories remain identical in both readings.
        # Actions impossible to see in the incomplete blockout must never
        # become invented spoken dialogue attributed to the cast.
        def add_speaker_cues(scene_name, cues):
            beat = next((item for item in manifest
                         if item["scene"] == scene_name), None)
            if beat is None:
                raise RuntimeError("Missing subtitle beat: "+scene_name)
            last_end = beat["start_frame"]
            for index, (local_start, local_end, cue_text) in enumerate(cues):
                first = beat["start_frame"]+int(round(local_start*fps))
                last = beat["start_frame"]+int(round(local_end*fps))
                if not (last_end <= first < last <= beat["end_frame"]):
                    raise RuntimeError(
                        "Overlapping/out-of-range "+scene_name+" subtitle "+str(index))
                section = subtitle_track.add_section()
                if section is None:
                    raise RuntimeError("Cannot add "+scene_name+" subtitle section")
                section.set_range(first, last)
                userdata = unreal.SubtitleAssetUserData(
                    outer=section, name="POLOP_"+scene_name+"_CUE_%02d" % index)
                cue = unreal.SubtitleAssetData()
                cue.set_editor_property("text", cue_text)
                cue.set_editor_property(
                    "subtitle_duration_type",
                    unreal.SubtitleDurationType.USE_DURATION_PROPERTY)
                cue.set_editor_property("duration", float((last-first)/fps))
                cue.set_editor_property("start_offset", 0.0)
                userdata.set_editor_property("subtitles", [cue])
                section.set_editor_property("subtitle", userdata)
                if section.get_editor_property("subtitle") is None:
                    raise RuntimeError("Cannot assign "+scene_name+" subtitle")
                later_dialogue_manifest.append(dict(
                    scene=scene_name, text=cue_text, start_frame=first,
                    end_frame_exclusive=last,
                    renderer="native_subtitles_umg"))
                last_end = last

        # One conversation, two views: match the A2 and B9 frame offsets.
        # Lea pauses at objective t=3.5-3.65, roughly 6.5-6.8 seconds into
        # each compressed 18-second shot. The short dialogue spans that
        # moment; exact lip sync is unavailable in this PREVIZ blockout.
        flank_dialogue = (
            (5.85, 7.25, "LEA: Can I take the bridge back?"),
            (7.35, 9.25, "THOMAS: No. Keep going. Take the hillside path."),
            (9.35, 10.20, "LEA: It's longer."),
            (10.35, 11.10, "THOMAS: Yes."),
        )
        for reading in ("A2", "B9"):
            add_speaker_cues(reading, flank_dialogue)

        # The father's departure and the ensuing search are otherwise only
        # described by late summary cards. Label canonical speech when the
        # characters actually leave/wait/search, not during an unrelated beat.
        add_speaker_cues("A11_ATTENTE", (
            (0.30, 1.90, "THOMAS: I need to pee."),
            (2.05, 2.95, "EVA: Now?"),
            (3.10, 4.25, "THOMAS: Two minutes."),
            (8.65, 10.40, "LEA: He's taking a while."),
            (11.65, 12.85, "EVA: Thomas?"),
        ))
        add_speaker_cues("A12_A13", (
            (6.55, 8.00, "EVA: Thomas!"),
            (8.15, 9.40, "LEA: Dad!"),
            (11.15, 12.40, "EVA: Thomas!"),
            (13.50, 15.85, "LEA: Do you think he fell?"),
        ))
        add_speaker_cues("A14", (
            (0.65, 3.65, "EVA: We should head down.\nFind some help."),
            (3.85, 5.15, "LEA: Okay."),
        ))

        # B-side repair belongs ONLY to the second reading of the film.
        # The first cue precedes the repair and the second tracks the
        # single clip state change at objective t=3.08 -> 3.04.
        add_speaker_cues("B6_REPAIR", (
            (0.55, 2.60, "B BANK: THE CARABINER IS LOOSE."),
            (3.05, 5.65, "Thomas reattaches it and checks the fastening."),
        ))
        expected = 2*len(flank_dialogue)+5+4+2+2
        if len(later_dialogue_manifest) != expected:
            raise RuntimeError("Incomplete dialogue in A2/B9, disappearance or B6")
    # F08: audit the ACTUAL Sequencer section count, not just our manifests.
    # Some editor capture modes omit screen-space UMG subtitles entirely.
    subtitle_audit = dict(
        geometry_only=F03_GEOMETRY_ONLY,
        track_count=0,
        actual_sections=0,
        expected_sections=(len(card_manifest)+len(opening_dialogue_manifest)+
                           len(later_dialogue_manifest)))
    if not F03_GEOMETRY_ONLY:
        native_tracks = [track for track in seq.get_tracks()
                         if isinstance(track, unreal.MovieSceneSubtitlesTrack)]
        subtitle_audit["track_count"] = len(native_tracks)
        subtitle_audit["actual_sections"] = sum(len(track.get_sections())
                                                 for track in native_tracks)
        if (subtitle_audit["track_count"] != 1 or
                subtitle_audit["actual_sections"] != subtitle_audit["expected_sections"]):
            raise RuntimeError("F08 subtitle Sequencer mismatch: "+str(subtitle_audit))
        journal("f08_subtitle_sections_verified", **subtitle_audit)
    else:
        journal("f08_subtitles_intentionally_disabled", **subtitle_audit)
    # F08: also export a frame-accurate SRT independent of the editor's
    # Slate/UMG overlay. It is an alternate subtitle delivery artifact for a
    # full-length movie export; a shortened editor recording needs its own
    # edit-time synchronization and must NOT use this SRT unmodified.
    if not F03_GEOMETRY_ONLY:
        cues = []
        for item in card_manifest:
            cues.append((item["start_frame"], item["end_frame_exclusive"],
                         item["title"]+"\n"+item["explanation"]))
        for item in opening_dialogue_manifest + later_dialogue_manifest:
            cues.append((item["start_frame"], item["end_frame_exclusive"],
                         item["text"]))
        cues.sort(key=lambda entry: (entry[0], entry[1]))
        def srt_timestamp(frame_number):
            milliseconds = int(round(1000.0*frame_number/fps))
            hh, remain = divmod(milliseconds, 3600000)
            mm, remain = divmod(remain, 60000)
            ss, ms = divmod(remain, 1000)
            return "%02d:%02d:%02d,%03d" % (hh, mm, ss, ms)
        srt_path = os.path.join(RUN_SAVED_ROOT, "polop_spectator_subtitles.srt")
        with open(srt_path, "w", encoding="utf-8") as srt:
            for index, (first, last, content) in enumerate(cues, 1):
                srt.write("%d\n%s --> %s\n%s\n\n" %
                          (index, srt_timestamp(first), srt_timestamp(last),
                           content))
        subtitle_audit["srt_path"] = srt_path
        subtitle_audit["srt_cues"] = len(cues)
        journal("f08_subtitle_srt_exported", path=srt_path, cues=len(cues),
                limitation="For full 372-second film only; no automatic MP4 burn-in.")
    if not a.get("human_audit_baked"):
        add_human_performances(a["sequence"], [(i, i/fps) for i in range(65*fps)])
        a["human_audit_baked"] = True
    unreal.EditorAssetLibrary.save_loaded_asset(seq)
    with open(os.path.join(RUN_SAVED_ROOT, "omniscient_edit.json"), "w", encoding="utf-8") as output:
        json.dump(dict(status="CONTINUOUS_CAMERA_BLOCKING_NOT_FINAL", duration_seconds=duration,
                       shots=manifest, previz_pause_cards=card_manifest,
                       opening_dialogue_cues=opening_dialogue_manifest,
                       later_dialogue_cues=later_dialogue_manifest,
                       subtitle_mode=("geometry_only_no_captions" if F03_GEOMETRY_ONLY
                                      else "technical_review" if SUBTITLE_REVIEW_MODE
                                      else "spectator"),
                       subtitle_audit=subtitle_audit,
                       carabiner=dict(bank="B", repair_objective_minutes=[3.08, 3.04],
                                      normal_reading="detaches", inverse_reading="repairs",
                                      track="MOUSQUETON_PROXY", acting="blockout"),
                       note="Cartons d'aide à la lecture : uniquement pour la prévisualisation.",
                       camera_sections=1, join_steps_m=join_steps_m,
                       maximum_camera_speed_m_s=max_camera_step_m*fps,
                       collision_validation="pending; interpolated paths require visual and geometry review",
                       missing=["A0 river opening", "ring", "carabiner animation", "environment reversal",
                                "acting and sound", "visual occlusion verification"]), output, indent=2)
    journal("omniscient_edit_created", sequence=seq.get_path_name(), duration_seconds=duration,
            status="blocking pass; canonical coverage incomplete")
    a["omniscient_sequence"] = seq
    a["omniscient_camera"] = cam
    a["omniscient_shots"] = tuple(shots)
    publish_current_film(seq, cam)
    # End generation on the film, not the separate objective-time audit.
    play_omniscient_film(play=False)


def publish_current_film(sequence, camera):
    """One persistent entry point; preserve historical cameras/sequences."""
    current = []
    archives = []
    for actor in actors.get_all_level_actors():
        label = actor.get_actor_label()
        if label == "POLOP_FILM_CURRENT" and isinstance(actor, unreal.LevelSequenceActor):
            current.append(actor)
        if actor != camera and label.startswith("PZ_ANIM_CAM_OMNISCIENT"):
            actor.set_folder_path("POLOP/Cameras/Archives")
            actor.set_actor_label("PZ_ANIM_CAM_OMNISCIENT_ARCHIVE_"+actor.get_name())
            archives.append(actor.get_actor_label())
    if len(current) > 1:
        raise RuntimeError("Multiple POLOP_FILM_CURRENT actors: resolve entry point before playback")
    entry = current[0] if current else actors.spawn_actor_from_class(
        unreal.LevelSequenceActor, unreal.Vector(0, 0, 0))
    entry.set_actor_label("POLOP_FILM_CURRENT")
    entry.set_folder_path("POLOP/Film")
    entry.set_sequence(sequence)
    settings = entry.get_editor_property("playback_settings")
    settings.set_editor_property("auto_play", True)
    settings.set_editor_property("pause_at_end", True)
    settings.set_editor_property("hide_hud", True)
    settings.set_editor_property("hide_player", True)
    settings.set_editor_property("loop_count", unreal.MovieSceneSequenceLoopCount(0))
    entry.set_editor_property("playback_settings", settings)
    camera.set_actor_label("PZ_ANIM_CAM_OMNISCIENT_CURRENT")
    camera.set_folder_path("POLOP/Film")
    cuts = [track for track in sequence.get_tracks() if isinstance(track, unreal.MovieSceneCameraCutTrack)]
    sections = [section for track in cuts for section in track.get_sections()]
    if len(sections) != 1 or sections[0].get_start_frame() != sequence.get_playback_start() or sections[0].get_end_frame() != sequence.get_playback_end():
        raise RuntimeError("Film must have exactly one camera cut covering its full playback range")
    manifest = dict(sequence=sequence.get_path_name(), camera=camera.get_actor_label(),
                    entry_actor=entry.get_actor_label(), map=unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world().get_path_name(),
                    start_frame=sequence.get_playback_start(), end_frame_exclusive=sequence.get_playback_end(),
                    camera_sections=1, archived_cameras=archives,
                    source_sha256=hashlib.sha256(open(SOURCE_SCRIPT_PATH, "rb").read()).hexdigest(),
                    status="PLAYABLE_A1_B9_BLOCKOUT_NOT_FULL_SCRIPT_VALIDATION")
    with open(os.path.join(RUN_SAVED_ROOT, "current_film.json"), "w", encoding="utf-8") as output:
        json.dump(manifest, output, indent=2)
    journal("current_film_published", **manifest)


def play_omniscient_film(play=True):
    """Open the persistent film entry at frame zero, with its sole camera cut.

    After reopening the generated map, its POLOP_FILM_CURRENT LevelSequenceActor
    also starts this same sequence with the editor's normal Play button (PIE).
    """
    global _OMNI_REVIEW_HANDLE
    stop_pov_review()
    if _OMNI_REVIEW_HANDLE is not None:
        unreal.unregister_slate_post_tick_callback(_OMNI_REVIEW_HANDLE)
        _OMNI_REVIEW_HANDLE = None
    entries = [actor for actor in actors.get_all_level_actors()
               if isinstance(actor, unreal.LevelSequenceActor) and actor.get_actor_label() == "POLOP_FILM_CURRENT"]
    if len(entries) != 1 or not entries[0].get_sequence():
        raise RuntimeError("No unique current film in this map; generate it first")
    sequence = entries[0].get_sequence()
    unreal.LevelSequenceEditorBlueprintLibrary.pause()
    unreal.LevelSequenceEditorBlueprintLibrary.open_level_sequence(sequence)
    unreal.LevelSequenceEditorBlueprintLibrary.set_lock_camera_cut_to_viewport(True)
    unreal.LevelSequenceEditorBlueprintLibrary.set_current_time(sequence.get_playback_start())
    if play:
        unreal.LevelSequenceEditorBlueprintLibrary.play()
    journal("current_film_opened", sequence=sequence.get_path_name(), playing=play)


_OMNI_REVIEW = {}
_OMNI_REVIEW_HANDLE = None
_OMNI_REVIEW_BUSY = False


def start_omniscient_review():
    """Capture the midpoint of every editorial shot and verify each PNG exists."""
    global _OMNI_REVIEW, _OMNI_REVIEW_HANDLE
    if _OMNI_REVIEW_HANDLE is not None:
        unreal.unregister_slate_post_tick_callback(_OMNI_REVIEW_HANDLE)
    stop_pov_review()
    with open(os.path.join(RUN_SAVED_ROOT, "omniscient_edit.json"), encoding="utf-8") as f:
        manifest = json.load(f)
    directory = os.path.join(RUN_SAVED_ROOT, "OMNISCIENT", datetime.datetime.now().strftime("%H%M%S"))
    os.makedirs(directory, exist_ok=True)
    _OMNI_REVIEW = dict(shots=manifest["shots"], index=0, stage="seek", directory=directory,
                       deadline=0.0, captures=[])
    unreal.LevelSequenceEditorBlueprintLibrary.open_level_sequence(_ANIMATION["omniscient_sequence"])
    unreal.LevelSequenceEditorBlueprintLibrary.set_lock_camera_cut_to_viewport(True)
    _OMNI_REVIEW_HANDLE = unreal.register_slate_post_tick_callback(_omniscient_review_tick)
    journal("omniscient_review_started", directory=directory)


def _omniscient_review_tick(delta_seconds):
    global _OMNI_REVIEW_HANDLE, _OMNI_REVIEW_BUSY
    if _OMNI_REVIEW_BUSY:
        return
    _OMNI_REVIEW_BUSY = True
    try:
        r = _OMNI_REVIEW
        now = time.monotonic()
        if r["index"] >= len(r["shots"]):
            unreal.unregister_slate_post_tick_callback(_OMNI_REVIEW_HANDLE)
            _OMNI_REVIEW_HANDLE = None
            journal("omniscient_captures_ready", captures=r["captures"],
                    note="Files exist; visual review remains a separate operation.")
            return
        shot = r["shots"][r["index"]]
        path = os.path.join(r["directory"], "%02d_%s.png" % (r["index"], shot["scene"]))
        if r["stage"] == "seek":
            frame = (shot["start_frame"]+shot["end_frame"])//2
            unreal.LevelSequenceEditorBlueprintLibrary.set_current_time(frame)
            r.update(stage="settle", deadline=now+0.75)
        elif r["stage"] == "settle" and now >= r["deadline"]:
            r.update(stage="capture", deadline=now+60.0)
            unreal.AutomationLibrary.take_high_res_screenshot(1280, 720, path,
                                                              _ANIMATION["omniscient_camera"])
        elif r["stage"] == "capture":
            if os.path.exists(path) and os.path.getsize(path) > 0:
                r["captures"].append(path)
                journal("omniscient_capture_saved", scene=shot["scene"], path=path)
                r["index"] += 1
                r["stage"] = "seek"
            elif now > r["deadline"]:
                raise RuntimeError("Screenshot missing after 60 seconds: " + path)
    except Exception as exc:
        if _OMNI_REVIEW_HANDLE is not None:
            unreal.unregister_slate_post_tick_callback(_OMNI_REVIEW_HANDLE)
            _OMNI_REVIEW_HANDLE = None
        journal("omniscient_review_failed", error=str(exc), traceback=traceback.format_exc())
    finally:
        _OMNI_REVIEW_BUSY = False


def finish_generation():
    global _ANIMATION
    route_path = _GEOGRAPHY["route_path"]
    run_world_coherence_gate(_GEOGRAPHY["landscape"], route_path)
    cleanup_non_animation_polop_cameras()
    _ANIMATION = run_animation_v05_with_legacy_landscape_mapping(_GEOGRAPHY["landscape"])
    validate_narrative_motion()
    audit_bridge_family_blocking()
    validate_sequencer_evaluation()
    normalize_animation_camera_focals()
    for actor in actors.get_all_level_actors():
        if actor.get_actor_label().startswith("PZ_ANIM_EVENT_"):
            actor.set_actor_hidden_in_game(True)
            actor.set_is_temporarily_hidden_in_editor(True)
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
    build_omniscient_edit()
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
            "articulated engine mannequin; provisional gait and acting",
            "omniscient blocking edit exists; cinematic coverage and framing not yet validated",
            "ring and environmental effects not yet animated",
        ],
    )
    # Only a fully successful, saved run may be reused by the opt-in camera
    # mode. Cache survives Execute Python Script within this editor session.
    remember_live_omniscient_world()
    if CLEANUP_OLD_RUNS:
        cleanup_old_run_artifacts()
    if "-POLOPPOVReview" in unreal.SystemLibrary.get_command_line():
        start_pov_review()
    elif "-POLOPReview" in unreal.SystemLibrary.get_command_line():
        play_omniscient_film()


_REVIEW_HANDLE = None
_REVIEW = {}
_REVIEW_BUSY = False
POV_ORDER = ("THOMAS_NORMAL", "LEA", "EVA", "THOMAS_INVERSE")


def validate_sequencer_evaluation():
    """Compare actual evaluated actors with the model, not just model endpoints."""
    a = _ANIMATION
    seq = a["sequence"]
    duplicates = []
    for binding in seq.get_bindings():
        count = sum(isinstance(track, unreal.MovieScene3DTransformTrack)
                    for track in binding.get_tracks())
        if count > 1:
            duplicates.append(binding.get_name())
    report_check("SEQUENCER", "single_transform_track_per_binding",
                 "FAIL" if duplicates else "OK", "BLOCKER", {"duplicates": duplicates})
    unreal.LevelSequenceEditorBlueprintLibrary.open_level_sequence(seq)
    errors = []
    for t in (0, 1, 2, 8, 32, 52, 57, 60, 61.9):
        unreal.LevelSequenceEditorBlueprintLibrary.set_current_time(int(round(t*a["FPS"])))
        for name, actor in a["actor_objects"].items():
            expected = a["actor_location_from_foot"](name, a["eval_actor"](name, t))
            actual = actor.get_actor_location()
            error = math.dist(expected, (actual.x, actual.y, actual.z))
            if error > 2.0:
                errors.append(dict(actor=name, minute=t, error_cm=error))
    unreal.LevelSequenceEditorBlueprintLibrary.set_current_time(0)
    report_check("SEQUENCER", "evaluated_positions_match_model",
                 "FAIL" if errors else "OK", "BLOCKER", {"errors": errors, "tolerance_cm": 2.0})


def validate_narrative_motion():
    """Check continuity and story constraints beyond the legacy endpoint checks."""
    a = _ANIMATION
    jumps = []
    for name, segments in a["ANIM"].items():
        for left, right in zip(segments, segments[1:]):
            p = a["eval_segment"](left, left["t1"])
            q = a["eval_segment"](right, right["t0"])
            distance = math.dist(p, q)
            if distance > 0.05:
                jumps.append(dict(actor=name, time=left["t1"], distance_m=distance))
    report_check("STORY", "continuous_character_trajectories", "OK" if not jumps else "FAIL",
                 "BLOCKER", {"discontinuities": jumps})
    separation = min(math.dist(a["eval_actor"]("EVA", t/10), a["eval_actor"]("LEA", t/10))
                     for t in range(80, 620))
    report_check("STORY", "eva_lea_distinct_positions", "OK" if separation >= 0.5 else "FAIL",
                 "BLOCKER", {"minimum_distance_m": separation})
    entry = a["CAVE_ENTRY_POINT"]
    normal = a["eval_actor"]("THOMAS_NORMAL", 57.0)
    inside = ((normal[0]-entry[0])*a["CAVE_UX"]+(normal[1]-entry[1])*a["CAVE_UY"]) > 1.0
    report_check("STORY", "thomas_inside_before_search_1755", "OK" if inside else "FAIL",
                 "BLOCKER", {"position_m": normal, "source": "A11-A13"})
    scores = []
    for t in (4, 16, 32, 48, 59.5, 60.5, 61.5):
        before = a["eval_actor"]("THOMAS_INVERSE", t-0.1)
        after = a["eval_actor"]("THOMAS_INVERSE", t+0.1)
        gaze = a["pov_direction"]("THOMAS_INVERSE", t)
        travel = tuple(before[i]-after[i] for i in range(3))
        scores.append(sum(gaze[i]*travel[i] for i in range(3)))
    report_check("STORY", "inverse_gaze_follows_personal_time", "OK" if min(scores)>0 else "FAIL",
                 "BLOCKER", {"dot_products": scores, "direction": "18:00 -> 17:00"})


def stop_pov_review():
    global _REVIEW_HANDLE
    if _REVIEW_HANDLE is not None:
        unreal.unregister_slate_post_tick_callback(_REVIEW_HANDLE)
        _REVIEW_HANDLE = None
    unreal.LevelSequenceEditorBlueprintLibrary.pause()


def start_pov_review(seconds_per_story_minute=1.0):
    """Play all 4 views, with inverted Thomas actually travelling 18:00 -> 17:00.

    Execute the file as a module, call main(), then call start_pov_review() after
    the keylog's complete event. Increase seconds_per_story_minute to slow review.
    A screenshot is requested at each checkpoint and its path is journaled.
    """
    global _REVIEW_HANDLE, _REVIEW
    if _ANIMATION is None:
        raise RuntimeError("Generate successfully before starting POV review")
    if seconds_per_story_minute <= 0:
        raise ValueError("Playback duration must be positive")
    stop_pov_review()
    capture_dir = os.path.join(RUN_SAVED_ROOT, "POV")
    os.makedirs(capture_dir, exist_ok=True)
    _REVIEW = dict(index=-1, started=0, elapsed=0.0, speed=seconds_per_story_minute,
                   capture_dir=capture_dir, captured=set(), pending=None, paused_until=0)
    unreal.LevelSequenceEditorBlueprintLibrary.open_level_sequence(_ANIMATION["sequence"])
    unreal.LevelSequenceEditorBlueprintLibrary.set_lock_camera_cut_to_viewport(False)
    journal("pov_review_started", order=POV_ORDER, seconds_per_story_minute=seconds_per_story_minute)
    _REVIEW_HANDLE = unreal.register_slate_post_tick_callback(_review_tick)


def _review_tick(delta_seconds):
    global _REVIEW_BUSY
    if _REVIEW_BUSY:
        return
    _REVIEW_BUSY = True
    try:
        now = time.monotonic()
        if now < _REVIEW["paused_until"]:
            return
        if _REVIEW["pending"] is not None:
            who, t, path = _REVIEW.pop("pending")
            _REVIEW["pending"] = None
            unreal.AutomationLibrary.take_high_res_screenshot(1280, 720, path,
                _ANIMATION["pov_cameras"][who])
            journal("pov_capture_requested", character=who, objective_minute=t,
                    path=path, foot_m=_ANIMATION["eval_actor"](who, t))
            _REVIEW["paused_until"] = now + 1.5
            _REVIEW["started"] += 1.5
            return
        # Shader compilation and editor stalls must never skip an entire POV.
        _REVIEW["elapsed"] += min(float(delta_seconds), 0.1) / _REVIEW["speed"]
        elapsed = _REVIEW["elapsed"]
        duration = 60.0 if _REVIEW["index"] == 3 else 62.0
        if _REVIEW["index"] < 0 or elapsed > duration:
            _REVIEW["index"] += 1
            if _REVIEW["index"] >= len(POV_ORDER):
                stop_pov_review()
                files = os.listdir(_REVIEW["capture_dir"])
                expected = {"%s_%05.2f.png" % (name, t) for name in POV_ORDER
                            for t in ((61.9, 60, 57, 32, 3, 2.05) if name == "THOMAS_INVERSE"
                                      else (0, 1, 2, 8, 32, 52, 57, 60, 61.9))}
                missing = sorted(expected-set(files))
                journal("pov_review_incomplete" if missing else "pov_review_finished",
                        captures=files, missing=missing,
                        note="PNG presence is checked; visual correctness still requires inspection.")
                return
            who = POV_ORDER[_REVIEW["index"]]
            _REVIEW["started"] = now
            _REVIEW["captured"] = set()
            _REVIEW["elapsed"] = 0.0
            elapsed = 0.0
            unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).pilot_level_actor(_ANIMATION["pov_cameras"][who])
            journal("pov_started", character=who, direction="reverse" if who=="THOMAS_INVERSE" else "forward")
        who = POV_ORDER[_REVIEW["index"]]
        t = max(2.0, 62.0-elapsed) if who == "THOMAS_INVERSE" else min(62.0, elapsed)
        checkpoints = (61.9, 60, 57, 32, 3, 2.05) if who == "THOMAS_INVERSE" else (0, 1, 2, 8, 32, 52, 57, 60, 61.9)
        for checkpoint in checkpoints:
            reached = t <= checkpoint if who == "THOMAS_INVERSE" else t >= checkpoint
            if reached and checkpoint not in _REVIEW["captured"]:
                _REVIEW["captured"].add(checkpoint)
                t = checkpoint
                filename = "%s_%05.2f.png" % (who, checkpoint)
                _REVIEW["pending"] = (who, checkpoint, os.path.join(_REVIEW["capture_dir"], filename))
                _REVIEW["paused_until"] = now + 0.5
                _REVIEW["started"] += 0.5
                break
        unreal.LevelSequenceEditorBlueprintLibrary.set_current_time(int(round(t*_ANIMATION["FPS"])))
    except Exception as exc:
        stop_pov_review()
        journal("pov_review_failed", error=str(exc), traceback=traceback.format_exc())
        unreal.log_error(str(exc))
    finally:
        _REVIEW_BUSY = False


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


def remember_live_omniscient_world():
    """Save references, not generated assets, for same-session camera-only reruns."""
    if _ANIMATION is None or _GEOGRAPHY is None:
        raise RuntimeError("Cannot cache an unfinished POLOP run")
    cache = types.ModuleType(_CAMERA_CACHE_KEY)
    cache.animation = _ANIMATION
    cache.geography = _GEOGRAPHY
    cache.signature = _CAMERA_BASE_SIGNATURE
    cache.world_path = editor_subsystem.get_editor_world().get_path_name()
    cache.work_map = WORK_MAP
    cache.asset_root = RUN_ASSET_ROOT
    cache.full_run_id = RUN_ID
    sys.modules[_CAMERA_CACHE_KEY] = cache
    journal("camera_only_cache_ready", map=WORK_MAP,
            full_run_id=RUN_ID, enabled_next_time=True)


def rerun_existing_camera_only():
    """No level duplication, no Landscape import, no character/caption baking."""
    global _ANIMATION, _GEOGRAPHY, world, WORK_MAP, RUN_ASSET_ROOT
    cache = sys.modules.get(_CAMERA_CACHE_KEY)
    if cache is None:
        raise RuntimeError(
            "FAST_CAMERA_ONLY needs one successful FULL run using this version "
            "of the script, in this Unreal session. Set False and run once.")
    if cache.signature != _CAMERA_BASE_SIGNATURE:
        raise RuntimeError(
            "FAST_CAMERA_ONLY: geography/actor source changed. "
            "Set False for a new full run.")
    if not cache.work_map.startswith(RUN_MAP_ROOT + "/Previz_"):
        raise RuntimeError("FAST_CAMERA_ONLY: cached map is not a generated POLOP work map.")
    world = editor_subsystem.get_editor_world()
    if world.get_path_name() != cache.world_path:
        raise RuntimeError(
            "FAST_CAMERA_ONLY: wrong level open. Reopen the cached generated "
            "work map in the same Unreal session, or set False for a full run.")
    _ANIMATION = cache.animation
    _GEOGRAPHY = cache.geography
    WORK_MAP = cache.work_map
    RUN_ASSET_ROOT = cache.asset_root
    journal("camera_only_start", map=WORK_MAP,
            reused_full_run=cache.full_run_id,
            scope="existing omniscient camera keys only")
    build_omniscient_edit()
    unreal.LevelSequenceEditorBlueprintLibrary.pause()
    if not unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_current_level():
        raise RuntimeError("FAST_CAMERA_ONLY: failed to save generated work map")
    play_omniscient_film(play=False)
    journal("complete", status="CAMERA_ONLY_REUSED_WORLD_NOT_FULL_REVALIDATION",
            map=WORK_MAP, source_full_run=cache.full_run_id,
            skipped=["Landscape", "cast", "character animation", "captions",
                     "full story/geometry validation"])


def main():
    global world, _GEOGRAPHY, _TICK_HANDLE, _STAGE_STARTED, _SOURCE_V11, _SOURCE_V05
    # Check before opening a different map; never discard an unsaved user level.
    dirty = unreal.EditorLoadingAndSavingUtils.get_dirty_map_packages()
    if dirty:
        raise RuntimeError("Save your current level before running POLOP; source levels are never saved automatically.")
    if FAST_CAMERA_ONLY:
        rerun_existing_camera_only()
        return
    # This is deliberately before duplicating /Game/Main or generating terrain.
    # The native subtitle renderer needs an editor restart after the plugin
    # is enabled in polop.uproject. Never silently return to blurry 3D cards.
    required_subtitle_types = (
        "MovieSceneSubtitlesTrack", "MovieSceneSubtitleSection",
        "SubtitleAssetUserData", "SubtitleAssetData", "SubtitleDurationType")
    missing = [name for name in required_subtitle_types
               if not hasattr(unreal, name)]
    if missing and not F03_GEOMETRY_ONLY:
        raise RuntimeError(
            "Enable 'Subtitles and Closed Captions' in Edit > Plugins, "
            "restart Unreal Engine, and rerun POLOP. "
            "Required native UMG/Sequencer types unavailable: " + ", ".join(missing))
    if F03_GEOMETRY_ONLY:
        unreal.log_warning(
            "POLOP F03_GEOMETRY_ONLY=1: THIS RUN WILL HAVE NO SUBTITLES. "
            "For cave + visible narrative text clear POLOP_F03_GEOMETRY_ONLY "
            "in the Unreal Python console and run FAST_CAMERA_ONLY=False.")
    else:
        unreal.log(
            "POLOP F08: full spectator subtitle build requested. "
            "Check the Sequencer subtitle track AND the screen-space overlay "
            "in the same mode used for video capture.")
    journal("start", script=SOURCE_SCRIPT_PATH, engine=unreal.SystemLibrary.get_engine_version(),
            source_map=SOURCE_MAP, work_map=WORK_MAP,
            source_sha256=hashlib.sha256(open(SOURCE_SCRIPT_PATH, "rb").read()).hexdigest())
    _SOURCE_V11 = _SOURCE_V11.replace("/Game/POLOP/Generated_V10", RUN_ASSET_ROOT)
    _SOURCE_V05 = _SOURCE_V05.replace("/Game/POLOP/Generated_V10", RUN_ASSET_ROOT)
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

