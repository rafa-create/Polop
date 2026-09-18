import math
import os
import json
import struct
import zlib
import binascii
import shutil
import unreal

# =============================================================================
# LA BOUCLE / POLOP — V10
# CORRECTION DU RAVIN + PONT ANCRE + GROTTE ANCRÉE + CAMERAS UTILES
#
# Dépendance volontaire : V09 doit avoir été exécutée une fois.
# V10 conserve EXACTEMENT les routes courbes V09 et modifie seulement :
# - le ravin sous le pont, recreusé APRES la sculpture des sentiers ;
# - le pont, replacé sur les deux rives avec vraie garde au sol ;
# - la terrasse locale de la grotte ;
# - les caméras proches/humaines.
#
# Génère :
#   Saved/POLOP/V10/polop_v10_heightmap_1009.png
#   Saved/POLOP/V10/route_model_v10.json
#
# Import :
#   supprimer uniquement le Landscape V09
#   Location UI : X=100800 Y=0 Z=0
#   Scale       : X=200 Y=200 Z=100
#   Flip Y      : OFF
#
# Puis exécuter previz_polop_validation_v10.py
# =============================================================================

PREFIX = "PZ_"
ROOT = "POLOP_PREVIZ"
HM_SIZE = 1009
GRID_STEP_M = 2.0
WORLD_X_MIN_M = 0.0
WORLD_Y_MIN_M = -1008.0

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
    return t*t*(3.0-2.0*t)


# -----------------------------------------------------------------------------
# FICHIERS V09
# -----------------------------------------------------------------------------

saved = unreal.Paths.convert_relative_path_to_full(unreal.Paths.project_saved_dir())
v09_dir = os.path.join(saved, "POLOP", "V09")
v10_dir = os.path.join(saved, "POLOP", "V10")
os.makedirs(v10_dir, exist_ok=True)

src_png = os.path.join(v09_dir, "polop_v09_heightmap_1009.png")
src_model = os.path.join(v09_dir, "route_model_v09.json")

if not os.path.exists(src_png):
    raise RuntimeError("V09 heightmap absent : " + src_png)
if not os.path.exists(src_model):
    raise RuntimeError("V09 route model absent : " + src_model)

dst_png = os.path.join(v10_dir, "polop_v10_heightmap_1009.png")
dst_model = os.path.join(v10_dir, "route_model_v10.json")
instructions_path = os.path.join(v10_dir, "IMPORT_V10.txt")


# -----------------------------------------------------------------------------
# PNG 16 BITS
# -----------------------------------------------------------------------------

def load_png16(path):
    data = open(path, "rb").read()
    if data[:8] != b"\x89PNG\r\n\x1a\n":
        raise RuntimeError("PNG invalide")

    pos = 8
    width = height = depth = color = None
    idat = bytearray()

    while pos < len(data):
        n = struct.unpack(">I", data[pos:pos+4])[0]
        pos += 4
        kind = data[pos:pos+4]
        pos += 4
        payload = data[pos:pos+n]
        pos += n + 4

        if kind == b"IHDR":
            width, height, depth, color, _, _, _ = struct.unpack(">IIBBBBB", payload)
        elif kind == b"IDAT":
            idat.extend(payload)
        elif kind == b"IEND":
            break

    if (width, height, depth, color) != (HM_SIZE, HM_SIZE, 16, 0):
        raise RuntimeError("Format PNG inattendu")

    raw = zlib.decompress(bytes(idat))
    stride = HM_SIZE*2 + 1
    grid = []

    for iy in range(HM_SIZE):
        row = raw[iy*stride:(iy+1)*stride]
        if row[0] != 0:
            raise RuntimeError("V10 attend le PNG filtre 0 généré par V09")

        grid.append([
            struct.unpack(">H", row[1+ix*2:3+ix*2])[0]
            for ix in range(HM_SIZE)
        ])

    return grid


def u16_to_m(v):
    return (v-32768.0)/32768.0*256.0


def m_to_u16(h):
    return max(0, min(65535, int(round(32768.0 + h/256.0*32768.0))))


def png_chunk(kind, payload):
    return (
        struct.pack(">I", len(payload))
        + kind + payload
        + struct.pack(">I", binascii.crc32(kind+payload) & 0xffffffff)
    )


def write_png16(path, grid):
    raw = bytearray()

    for row in grid:
        raw.append(0)
        for value in row:
            raw.extend(struct.pack(">H", int(value)))

    ihdr = struct.pack(">IIBBBBB", HM_SIZE, HM_SIZE, 16, 0, 0, 0, 0)
    png = bytearray(b"\x89PNG\r\n\x1a\n")
    png.extend(png_chunk(b"IHDR", ihdr))
    png.extend(png_chunk(b"IDAT", zlib.compress(bytes(raw), 9)))
    png.extend(png_chunk(b"IEND", b""))

    with open(path, "wb") as f:
        f.write(png)


grid = load_png16(src_png)


def get_height(ix, iy):
    return u16_to_m(grid[iy][ix])


def set_height(ix, iy, h):
    grid[iy][ix] = m_to_u16(h)


def world_xy(ix, iy):
    return (
        WORLD_X_MIN_M + ix*GRID_STEP_M,
        WORLD_Y_MIN_M + iy*GRID_STEP_M
    )


# -----------------------------------------------------------------------------
# 1) RAVIN : POST-PROCESS, donc les banquettes A/B ne peuvent plus le reboucher.
# -----------------------------------------------------------------------------

RAVINE_DEPTH_M = 9.0
RAVINE_SIGMA_X_M = 58.0

for iy in range(HM_SIZE):
    _, y = world_xy(0, iy)

    if y < 0.0 or y > 25.0:
        continue

    u = y / 25.0
    across = math.sin(math.pi*u) ** 4

    if across <= 1e-9:
        continue

    for ix in range(HM_SIZE):
        x, _ = world_xy(ix, iy)
        along = math.exp(-((x-900.0)/RAVINE_SIGMA_X_M)**2)
        depth = RAVINE_DEPTH_M * across * along

        if depth > 0.001:
            set_height(ix, iy, get_height(ix, iy)-depth)


# -----------------------------------------------------------------------------
# 2) TERRASSE GROTTE
# -----------------------------------------------------------------------------

CAVE_TERRACE_X = 1839.0
CAVE_TERRACE_Y = 94.5
CAVE_TERRACE_Z = 160.5
CAVE_RADIUS_M = 16.0
CAVE_SHOULDER_M = 12.0
outer = CAVE_RADIUS_M + CAVE_SHOULDER_M
rad_px = int(math.ceil(outer/GRID_STEP_M))
cx = int(round((CAVE_TERRACE_X-WORLD_X_MIN_M)/GRID_STEP_M))
cy = int(round((CAVE_TERRACE_Y-WORLD_Y_MIN_M)/GRID_STEP_M))

for iy in range(max(0,cy-rad_px), min(HM_SIZE-1,cy+rad_px)+1):
    for ix in range(max(0,cx-rad_px), min(HM_SIZE-1,cx+rad_px)+1):
        x,y = world_xy(ix,iy)
        d = math.hypot(x-CAVE_TERRACE_X, y-CAVE_TERRACE_Y)

        if d >= outer:
            continue

        w = 1.0 if d <= CAVE_RADIUS_M else smoothstep((outer-d)/CAVE_SHOULDER_M)
        current = get_height(ix,iy)
        set_height(ix,iy,current*(1.0-w)+CAVE_TERRACE_Z*w)


write_png16(dst_png, grid)


# -----------------------------------------------------------------------------
# ROUTE MODEL
# -----------------------------------------------------------------------------

model = json.load(open(src_model, "r", encoding="utf-8"))
model["version"] = "V10"
model["terrain_patch"] = {
    "ravine_depth_target_m": RAVINE_DEPTH_M,
    "cave_terrace": {
        "x_m": CAVE_TERRACE_X,
        "y_m": CAVE_TERRACE_Y,
        "z_m": CAVE_TERRACE_Z,
    },
}

inverse_distance = model["timing"]["inverse_length_m"]
calibrated_speed = inverse_distance/1000.0 / ((60.0-7.0)/60.0)

model["timing"]["inverse_speed_kmh_for_exact_60min_with_7min_pause"] = calibrated_speed
model["timing"]["inverse_total_at_calibrated_speed_min"] = 60.0

with open(dst_model, "w", encoding="utf-8") as f:
    json.dump(model, f, indent=2, ensure_ascii=False)

with open(instructions_path, "w", encoding="utf-8") as f:
    f.write(
        "POLOP V10\n\n"
        "Supprimer uniquement le Landscape V09.\n"
        "Importer : %s\n\n"
        "Location UI X=100800 Y=0 Z=0\n"
        "Rotation 0/0/0\n"
        "Scale X=200 Y=200 Z=100\n"
        "Flip Y OFF\n\n"
        "Puis lancer previz_polop_validation_v10.py\n" % dst_png
    )


# -----------------------------------------------------------------------------
# INTERPOLATION HEIGHTMAP
# -----------------------------------------------------------------------------

def height_at(x_m, y_m):
    fx = clamp((x_m-WORLD_X_MIN_M)/GRID_STEP_M, 0.0, HM_SIZE-1.0)
    fy = clamp((y_m-WORLD_Y_MIN_M)/GRID_STEP_M, 0.0, HM_SIZE-1.0)

    x0,y0 = int(math.floor(fx)), int(math.floor(fy))
    x1,y1 = min(HM_SIZE-1,x0+1), min(HM_SIZE-1,y0+1)
    tx,ty = fx-x0,fy-y0

    z00,z10 = get_height(x0,y0),get_height(x1,y0)
    z01,z11 = get_height(x0,y1),get_height(x1,y1)

    return (
        (z00*(1-tx)+z10*tx)*(1-ty)
        + (z01*(1-tx)+z11*tx)*ty
    )


# -----------------------------------------------------------------------------
# NETTOYAGE + MATERIAUX
# -----------------------------------------------------------------------------

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


MAT_A = ensure_material("M_V10_A", (0.05,0.35,1.0))
MAT_B = ensure_material("M_V10_B", (1.0,0.18,0.04))
MAT_UP = ensure_material("M_V10_UP", (0.5,0.18,0.95))
MAT_CAVE = ensure_material("M_V10_CAVE_ACCESS", (0.85,0.85,0.85))
MAT_FLANK = ensure_material("M_V10_FLANK", (0.05,0.78,0.15))
MAT_BRIDGE = ensure_material("M_V10_BRIDGE", (0.95,0.68,0.03))
MAT_DARK = ensure_material("M_V10_CAVE_DARK", (0.04,0.04,0.05))
MAT_MARK = ensure_material("M_V10_MARKER", (1.0,1.0,0.03))
MAT_THOMAS = ensure_material("M_V10_THOMAS", (0.08,0.35,1.0))
MAT_INVERSE = ensure_material("M_V10_INVERSE", (1.0,0.12,0.05))
MAT_EVA = ensure_material("M_V10_EVA", (0.75,0.15,0.85))
MAT_LEA = ensure_material("M_V10_LEA", (0.03,0.82,0.68))


def label(actor, name, folder):
    actor.set_actor_label(PREFIX+name, True)
    try:
        actor.set_folder_path(unreal.Name(ROOT+"/"+folder))
    except Exception:
        pass


def apply_material(actor, mat):
    try:
        comp = actor.get_component_by_class(unreal.StaticMeshComponent)
        if comp:
            comp.set_material(0, mat)
    except Exception:
        pass


def box(name, pos, size, mat, folder, rot=None):
    actor = actors.spawn_actor_from_object(
        CUBE, pos, rot or unreal.Rotator(0,0,0), False
    )
    label(actor,name,folder)
    actor.set_actor_scale3d(V(size[0]/100,size[1]/100,size[2]/100))
    apply_material(actor,mat)
    return actor


def sphere(name,pos,radius,mat,folder="Reperes"):
    actor = actors.spawn_actor_from_object(SPHERE,pos,unreal.Rotator(0,0,0),False)
    label(actor,name,folder)
    actor.set_actor_scale3d(V(radius/50,radius/50,radius/50))
    apply_material(actor,mat)
    return actor


def person(name,x,y,h_cm,mat):
    z = height_at(x,y)*100.0
    actor = actors.spawn_actor_from_object(
        CYLINDER,V(x*100,y*100,z+h_cm/2),unreal.Rotator(0,0,0),False
    )
    label(actor,name,"Personnages_proxy")
    actor.set_actor_scale3d(V(0.34,0.34,h_cm/100.0))
    apply_material(actor,mat)
    return actor


# -----------------------------------------------------------------------------
# GUIDES V09 REUTILISES
# -----------------------------------------------------------------------------

ROUTES = {
    name:data["samples"]
    for name,data in model["routes"].items()
}

MAT_BY_NAME = {
    "A":MAT_A, "B":MAT_B, "HAUT":MAT_UP, "GROTTE":MAT_CAVE, "FLANC":MAT_FLANK
}


def wp(p):
    x,y,_ = p
    return V(x*100,y*100,height_at(x,y)*100+45)


def dist3(a,b):
    return math.sqrt((b.x-a.x)**2+(b.y-a.y)**2+(b.z-a.z)**2)


def midpoint(a,b):
    return V((a.x+b.x)/2,(a.y+b.y)/2,(a.z+b.z)/2)


def guide(name,route,width=135):
    pts = route[::3]
    if pts[-1] != route[-1]:
        pts.append(route[-1])

    pts = [wp(p) for p in pts]

    for i,(a,b) in enumerate(zip(pts,pts[1:]),1):
        box(
            "GUIDE_%s_%03d"%(name,i),
            midpoint(a,b),
            (dist3(a,b)*1.02,width,14),
            MAT_BY_NAME[name],
            "Guides/"+name,
            unreal.MathLibrary.find_look_at_rotation(a,b)
        )


guide("A",ROUTES["A"])
guide("B",ROUTES["B"])
guide("HAUT",ROUTES["HAUT"])
guide("GROTTE",ROUTES["GROTTE"],120)
guide("FLANC",ROUTES["FLANC"],120)


# -----------------------------------------------------------------------------
# PONT V10
# -----------------------------------------------------------------------------

def make_bridge():
    ax,ay = 900.0,0.0
    bx,by = 900.0,25.0
    deck_offset_m = 0.45

    a = V(ax*100,ay*100,(height_at(ax,ay)+deck_offset_m)*100)
    b = V(bx*100,by*100,(height_at(bx,by)+deck_offset_m)*100)
    center = midpoint(a,b)
    rot = unreal.MathLibrary.find_look_at_rotation(a,b)
    length = dist3(a,b)
    width = 220.0

    box("PONT_TABLIER",center,(length,width,28),MAT_BRIDGE,"Props/Pont",rot)

    dx,dy = b.x-a.x,b.y-a.y
    horizontal = max(1.0,math.hypot(dx,dy))
    nx,ny = -dy/horizontal,dx/horizontal

    for side,sign in (("G",1),("D",-1)):
        c = V(
            center.x+nx*(width/2-10)*sign,
            center.y+ny*(width/2-10)*sign,
            center.z+65
        )
        box("PONT_GARDE_"+side,c,(length,12,105),MAT_BRIDGE,"Props/Pont",rot)

    floor_m = height_at(900.0,12.5)
    deck_m = center.z/100.0
    pillar_h_m = max(0.0,deck_m-floor_m)

    if pillar_h_m > 1:
        box(
            "PONT_PILE",
            V(90000,1250,(floor_m+pillar_h_m/2)*100),
            (65,65,pillar_h_m*100),
            MAT_BRIDGE,
            "Props/Pont"
        )


make_bridge()


# -----------------------------------------------------------------------------
# GROTTE V10
# -----------------------------------------------------------------------------

def make_cave():
    route = ROUTES["GROTTE"]
    p0,p1 = route[-2],route[-1]
    dx,dy = p1[0]-p0[0],p1[1]-p0[1]
    d = max(1e-6,math.hypot(dx,dy))
    ux,uy = dx/d,dy/d
    nx,ny = -uy,ux

    entrance_x,entrance_y = p1[0],p1[1]
    z = height_at(CAVE_TERRACE_X,CAVE_TERRACE_Y)

    tunnel_m = 8.0
    half_w = 2.8
    wall_t = 1.0
    wall_h = 4.5

    cx = entrance_x + ux*tunnel_m/2
    cy = entrance_y + uy*tunnel_m/2
    yaw = math.degrees(math.atan2(dy,dx))
    rot = unreal.Rotator(0,yaw,0)

    box(
        "GROTTE_SOL",
        V(cx*100,cy*100,(z+0.08)*100),
        (tunnel_m*100,half_w*2*100,16),
        MAT_DARK,"Props/Grotte",rot
    )

    for side,sign in (("G",1),("D",-1)):
        wx = cx+nx*(half_w+wall_t/2)*sign
        wy = cy+ny*(half_w+wall_t/2)*sign
        box(
            "GROTTE_PAROI_"+side,
            V(wx*100,wy*100,(z+wall_h/2)*100),
            (tunnel_m*100,wall_t*100,wall_h*100),
            MAT_DARK,"Props/Grotte",rot
        )

    box(
        "GROTTE_TOIT",
        V(cx*100,cy*100,(z+wall_h+0.4)*100),
        (tunnel_m*100,(half_w*2+wall_t*2)*100,80),
        MAT_DARK,"Props/Grotte",rot
    )


make_cave()


# -----------------------------------------------------------------------------
# PROXIES / REPÈRES
# -----------------------------------------------------------------------------

sphere("REPERE_CONVERGENCE_17H00",V(0,0,height_at(0,0)*100+150),75,MAT_MARK)
sphere("REPERE_JONCTION_HAUTE",V(176000,0,height_at(1760,0)*100+150),75,MAT_MARK)

person("THOMAS_NORMAL_PROXY",650,-80,180,MAT_THOMAS)
person("EVA_PROXY",654,-76,170,MAT_EVA)
person("LEA_PROXY_FLANC",810,82,135,MAT_LEA)
person("THOMAS_INVERSE_PROXY",1300,600,180,MAT_INVERSE)


# -----------------------------------------------------------------------------
# CAMÉRAS V10
# -----------------------------------------------------------------------------

def target(x,y,extra=0):
    return V(x*100,y*100,height_at(x,y)*100+extra)


def cam(name,pos,look,focal):
    try:
        actor = actors.spawn_actor_from_class(
            unreal.CineCameraActor,pos,unreal.Rotator(0,0,0),False
        )
        if not actor:
            raise RuntimeError("spawn=None")
        label(actor,"CAM_REVIEW_"+name,"Cameras/Review_V10")
        actor.set_actor_rotation(unreal.MathLibrary.find_look_at_rotation(pos,look),False)
        actor.get_cine_camera_component().set_current_focal_length(float(focal))
        unreal.log("POLOP V10 CAM OK : "+name)
        return actor
    except Exception as exc:
        unreal.log_error("POLOP V10 CAM FAIL %s : %s"%(name,exc))
        return None


specs = [
    ("01_TOP_MAP",V(100800,0,520000),V(100800,0,9000),50),
    ("02_FLANC_CLOSE",V(74500,-10000,height_at(745,-100)*100+9000),target(825,45,700),45),
    ("03_BRIDGE_A",V(79000,-15000,height_at(790,-150)*100+9000),target(900,12.5,500),45),
    ("04_BRIDGE_B",V(100000,18000,height_at(1000,180)*100+9000),target(900,12.5,500),45),
    ("05_HIGH_JUNCTION",V(168000,-11000,height_at(1680,-110)*100+5200),target(1760,0,900),42),
    ("06_CAVE_GROUNDED",V(187000,14000,height_at(1870,140)*100+650),target(1835,92,160),42),
    ("07_HUMAN_A",V(62000,-8300,height_at(620,-83)*100+220),target(670,-72,170),35),
    ("08_HUMAN_B",V(133000,60500,height_at(1330,605)*100+220),target(1290,585,170),35),
    ("09_CONVERGENCE",V(6000,-1000,height_at(60,-10)*100+260),target(8,0,150),40),
]

created = []
for s in specs:
    c = cam(*s)
    if c:
        created.append(c)

if created:
    actors.set_selected_level_actors([created[0]])


unreal.log("============================================================")
unreal.log("POLOP V10 PREPAREE")
unreal.log("Heightmap : "+dst_png)
unreal.log("Ravin cible : %.1fm"%RAVINE_DEPTH_M)
unreal.log("Vitesse Thomas inverse pour 60min avec 7min pause : %.3f km/h"%calibrated_speed)
unreal.log("CAMERAS : %d/%d"%(len(created),len(specs)))
unreal.log("IMPORT : X=100800 Y=0 Z=0 | Scale 200/200/100 | Flip Y OFF")
unreal.log("============================================================")
