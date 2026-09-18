import math
import os
import struct
import zlib
import binascii
import unreal

# =============================================================================
# LA BOUCLE / POLOP — PREVIZ COMPLETE V07
# LANDSCAPE HEIGHTMAP + GUIDES + CAMERAS
# Unreal Engine 5.8
#
# V03 : topologie validée.
# V04/V05 : échelle validée.
# V06 : méthode "cubes = montagne" abandonnée.
# V07 : vraie base Landscape.
#
# Ce script :
#   1. génère un heightmap PNG 16 bits 1009x1009 ;
#   2. l'enregistre dans Saved/POLOP/V07/ ;
#   3. supprime uniquement les anciens Actors dont le label commence par PZ_ ;
#   4. recrée des GUIDES fins pour A / B / chemin haut / accès grotte /
#      pont / flanc ;
#   5. recrée les caméras de revue V07.
#
# IMPORTANT :
# Le Landscape lui-même est importé manuellement une fois dans Unreal :
#
#   Shift + 2  -> Landscape
#   Manage -> Import from File
#
#   Heightmap :
#       Saved/POLOP/V07/polop_v07_heightmap_1009.png
#
#   Location :
#       X = 0
#       Y = -100800
#       Z = 0
#
#   Scale :
#       X = 200
#       Y = 200
#       Z = 100
#
#   Flip Y Axis :
#       OFF au premier essai.
#       Si le relief se retrouve inversé par rapport aux guides A/B,
#       réimporter avec Flip Y Axis ON.
#
# 1009 vertices avec X/Y Scale = 200 cm donne ~2016 m x 2016 m.
#
# =============================================================================

VERSION = "V07"
PREFIX = "PZ_"
ROOT_FOLDER = "POLOP_PREVIZ"

# -----------------------------------------------------------------------------
# LANDSCAPE
# -----------------------------------------------------------------------------

HM_SIZE = 1009
XY_SCALE_CM = 200.0

WORLD_X_MIN_M = 0.0
WORLD_X_MAX_M = 2016.0

WORLD_Y_MIN_M = -1008.0
WORLD_Y_MAX_M = 1008.0

LANDSCAPE_LOCATION_X_CM = 0.0
LANDSCAPE_LOCATION_Y_CM = -100800.0
LANDSCAPE_LOCATION_Z_CM = 0.0

LANDSCAPE_Z_SCALE = 100.0

# -----------------------------------------------------------------------------
# GUIDES
# -----------------------------------------------------------------------------

GUIDE_WIDTH_CM = 180.0
GUIDE_THICKNESS_CM = 22.0
GUIDE_Z_OFFSET_CM = 65.0

BRIDGE_WIDTH_CM = 115.0

# -----------------------------------------------------------------------------
# UNREAL
# -----------------------------------------------------------------------------

actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
asset_tools = unreal.AssetToolsHelpers.get_asset_tools()

CUBE = unreal.load_asset("/Engine/BasicShapes/Cube.Cube")
SPHERE = unreal.load_asset("/Engine/BasicShapes/Sphere.Sphere")
CYLINDER = unreal.load_asset("/Engine/BasicShapes/Cylinder.Cylinder")

if not CUBE or not SPHERE or not CYLINDER:
    raise RuntimeError("Impossible de charger les BasicShapes Unreal.")


def V(x, y, z):
    return unreal.Vector(float(x), float(y), float(z))


def gaussian(x, y, cx, cy, sx, sy, amplitude):
    dx = (x - cx) / sx
    dy = (y - cy) / sy
    return amplitude * math.exp(-(dx*dx + dy*dy))


# =============================================================================
# TERRAIN PROCEDURAL
# =============================================================================

def terrain_height_m(x_m, y_m):
    """
    Hauteur de travail en mètres.

    Le but n'est pas encore le réalisme final, mais une montagne CONTINUE
    qui porte correctement la topologie validée :
      - montée générale vers la zone haute ;
      - arête entre A et B ;
      - ravin au pont ;
      - épaulement côté A ;
      - versant plus ouvert côté B ;
      - poche plus calme près de la grotte.
    """

    # Pente générale : environ 3 m -> 104 m sur 2 km.
    h = 3.0 + 0.050 * x_m

    # Grande arête centrale séparant A et B.
    h += gaussian(
        x_m, y_m,
        1120.0, 170.0,
        300.0, 180.0,
        38.0
    )

    h += gaussian(
        x_m, y_m,
        1400.0, 165.0,
        300.0, 190.0,
        55.0
    )

    h += gaussian(
        x_m, y_m,
        1660.0, 105.0,
        250.0, 170.0,
        48.0
    )

    # Épaulement côté A.
    h += gaussian(
        x_m, y_m,
        1350.0, -165.0,
        420.0, 230.0,
        18.0
    )

    # Relief secondaire côté B.
    h += gaussian(
        x_m, y_m,
        1250.0, 470.0,
        380.0, 260.0,
        16.0
    )

    # Zone haute / grotte.
    h += gaussian(
        x_m, y_m,
        1770.0, 40.0,
        230.0, 190.0,
        26.0
    )

    # Ravin du pont.
    # Étroit selon Y, plus long selon X.
    h -= gaussian(
        x_m, y_m,
        900.0, 12.5,
        80.0, 8.5,
        30.0
    )

    # Creux / détour naturel du flanc.
    h -= gaussian(
        x_m, y_m,
        825.0, 45.0,
        125.0, 70.0,
        7.0
    )

    # Petite poche moins bombée autour de l'accès à la grotte.
    h -= gaussian(
        x_m, y_m,
        1820.0, 80.0,
        95.0, 70.0,
        8.0
    )

    # Irrégularité très douce pour éviter une surface trop mathématique.
    h += 1.8 * math.sin(x_m / 83.0) * math.cos(y_m / 113.0)
    h += 0.9 * math.sin((x_m + y_m) / 47.0)

    # La V07 reste dans la plage confortable de Z Scale 100.
    return max(0.0, min(225.0, h))


def height_m_to_u16(height_m):
    """
    Unreal avec Z Scale 100 :
      valeur interne -256..+255.992 multipliée par 100.
    32768 correspond à Z = 0.

    Conversion :
      h / 256m * 32768
    """
    value = 32768.0 + (height_m / 256.0) * 32768.0
    return max(0, min(65535, int(round(value))))


# =============================================================================
# PNG 16 BITS — STDLIB UNIQUEMENT
# =============================================================================

def png_chunk(chunk_type, payload):
    return (
        struct.pack(">I", len(payload))
        + chunk_type
        + payload
        + struct.pack(
            ">I",
            binascii.crc32(chunk_type + payload) & 0xffffffff
        )
    )


def write_png16_grayscale(filepath):
    """
    Écrit un PNG grayscale 16-bit sans Pillow / numpy.
    Compatible avec le Python embarqué d'Unreal.
    """

    unreal.log(
        "POLOP V07 : génération heightmap 1009x1009..."
    )

    raw = bytearray()

    for py in range(HM_SIZE):
        # Hypothèse d'import : première ligne = Y minimum.
        ty = py / float(HM_SIZE - 1)

        y_m = (
            WORLD_Y_MIN_M
            + ty * (WORLD_Y_MAX_M - WORLD_Y_MIN_M)
        )

        # PNG filter type = 0.
        raw.append(0)

        for px in range(HM_SIZE):
            tx = px / float(HM_SIZE - 1)

            x_m = (
                WORLD_X_MIN_M
                + tx * (WORLD_X_MAX_M - WORLD_X_MIN_M)
            )

            value = height_m_to_u16(
                terrain_height_m(x_m, y_m)
            )

            raw.extend(
                struct.pack(">H", value)
            )

    ihdr = struct.pack(
        ">IIBBBBB",
        HM_SIZE,
        HM_SIZE,
        16,  # bit depth
        0,   # grayscale
        0,   # compression
        0,   # filter
        0    # interlace
    )

    png = bytearray(b"\x89PNG\r\n\x1a\n")
    png.extend(png_chunk(b"IHDR", ihdr))
    png.extend(
        png_chunk(
            b"IDAT",
            zlib.compress(bytes(raw), 9)
        )
    )
    png.extend(png_chunk(b"IEND", b""))

    with open(filepath, "wb") as f:
        f.write(png)

    unreal.log(
        "POLOP V07 : heightmap écrit : " + filepath
    )


# =============================================================================
# SORTIE FICHIERS
# =============================================================================

saved_dir = unreal.Paths.convert_relative_path_to_full(
    unreal.Paths.project_saved_dir()
)

v07_dir = os.path.join(
    saved_dir,
    "POLOP",
    "V07"
)

os.makedirs(
    v07_dir,
    exist_ok=True
)

heightmap_path = os.path.join(
    v07_dir,
    "polop_v07_heightmap_1009.png"
)

instructions_path = os.path.join(
    v07_dir,
    "IMPORT_V07.txt"
)

write_png16_grayscale(
    heightmap_path
)

instructions = """POLOP V07 — IMPORT LANDSCAPE

Heightmap:
{heightmap}

Unreal:
Shift + 2 -> Landscape
Manage -> Import from File

Location:
X = 0
Y = -100800
Z = 0

Scale:
X = 200
Y = 200
Z = 100

Heightmap resolution:
1009 x 1009

Expected landscape:
~2016 m x 2016 m

Flip Y Axis:
OFF au premier essai.
Si les guides A/B ne correspondent pas au terrain, réimporter avec ON.

Important:
Le Landscape est le terrain.
Les Actors PZ_GUIDE_* ne sont que des traits de contrôle.
""".format(heightmap=heightmap_path)

with open(
    instructions_path,
    "w",
    encoding="utf-8"
) as f:
    f.write(instructions)


# =============================================================================
# NETTOYAGE DES ANCIENS ACTORS
# =============================================================================

def cleanup_generated_actors():
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
        "POLOP V07 : %d anciens Actors PZ_ supprimés."
        % len(old)
    )


cleanup_generated_actors()


# =============================================================================
# MATERIAUX GUIDES
# =============================================================================

def ensure_material(name, rgb):
    mat_dir = "/Game/POLOP/Previz/Materials"
    unreal.EditorAssetLibrary.make_directory(mat_dir)

    asset_path = mat_dir + "/" + name

    if unreal.EditorAssetLibrary.does_asset_exist(asset_path):
        return unreal.load_asset(asset_path)

    try:
        mat = asset_tools.create_asset(
            name,
            mat_dir,
            unreal.Material,
            unreal.MaterialFactoryNew()
        )

        color_expr = (
            unreal.MaterialEditingLibrary.create_material_expression(
                mat,
                unreal.MaterialExpressionConstant3Vector,
                -300,
                0
            )
        )

        color_expr.set_editor_property(
            "constant",
            unreal.LinearColor(
                float(rgb[0]),
                float(rgb[1]),
                float(rgb[2]),
                1.0
            )
        )

        unreal.MaterialEditingLibrary.connect_material_property(
            color_expr,
            "",
            unreal.MaterialProperty.MP_BASE_COLOR
        )

        rough_expr = (
            unreal.MaterialEditingLibrary.create_material_expression(
                mat,
                unreal.MaterialExpressionConstant,
                -300,
                150
            )
        )

        rough_expr.set_editor_property(
            "r",
            0.85
        )

        unreal.MaterialEditingLibrary.connect_material_property(
            rough_expr,
            "",
            unreal.MaterialProperty.MP_ROUGHNESS
        )

        unreal.MaterialEditingLibrary.recompile_material(mat)
        unreal.EditorAssetLibrary.save_loaded_asset(mat)
        return mat

    except Exception as exc:
        unreal.log_warning(
            "Materiau non créé %s : %s"
            % (name, exc)
        )
        return None


MAT_A = ensure_material(
    "M_V07_GUIDE_A",
    (0.05, 0.35, 1.0)
)

MAT_B = ensure_material(
    "M_V07_GUIDE_B",
    (1.0, 0.18, 0.04)
)

MAT_UP = ensure_material(
    "M_V07_GUIDE_UP",
    (0.50, 0.18, 0.95)
)

MAT_CAVE = ensure_material(
    "M_V07_GUIDE_CAVE",
    (0.85, 0.85, 0.85)
)

MAT_FLANK = ensure_material(
    "M_V07_GUIDE_FLANK",
    (0.06, 0.78, 0.15)
)

MAT_BRIDGE = ensure_material(
    "M_V07_GUIDE_BRIDGE",
    (1.0, 0.72, 0.02)
)

MAT_MARKER = ensure_material(
    "M_V07_MARKER",
    (1.0, 1.0, 0.04)
)


def apply_material(actor, material):
    if not material:
        return

    try:
        comp = actor.get_component_by_class(
            unreal.StaticMeshComponent
        )

        if comp:
         comp.set_material(
                0,
                material
            )

    except Exception:
        pass


def set_folder(actor, folder_name):
    try:
        actor.set_folder_path(
            unreal.Name(
                ROOT_FOLDER + "/" + folder_name
            )
        )
    except Exception:
        pass


def set_actor_name(actor, name, folder_name):
    actor.set_actor_label(
        PREFIX + name,
        True
    )

    set_folder(
        actor,
        folder_name
    )

    return actor


def spawn_box(
    name,
    position,
    size_xyz,
    material,
    folder_name,
    rotation=None
):
    if rotation is None:
        rotation = unreal.Rotator(
            0,
            0,
            0
        )

    actor = actors.spawn_actor_from_object(
        CUBE,
        position,
        rotation,
        False
    )

    set_actor_name(
        actor,
        name,
        folder_name
    )

    actor.set_actor_scale3d(
        V(
            size_xyz[0] / 100.0,
            size_xyz[1] / 100.0,
            size_xyz[2] / 100.0
        )
    )

    apply_material(
        actor,
        material
    )

    return actor


def spawn_sphere(
    name,
    position,
    radius,
    material,
    folder_name="Reperes"
):
    actor = actors.spawn_actor_from_object(
        SPHERE,
        position,
        unreal.Rotator(0, 0, 0),
        False
    )

    set_actor_name(
        actor,
        name,
        folder_name
    )

    actor.set_actor_scale3d(
        V(
            radius / 50.0,
            radius / 50.0,
            radius / 50.0
        )
    )

    apply_material(
        actor,
        material
    )

    return actor


# =============================================================================
# COORDONNEES VALIDÉES
# =============================================================================
#
# Valeurs en cm.
# La fonction terrain utilise mètres.
# =============================================================================

CONVERGENCE_XY = (0.0, 0.0)

A1_XY = (30000.0, -5000.0)
A2_XY = (65000.0, -8000.0)
A_BRIDGE_XY = (90000.0, 0.0)
A3_XY = (125000.0, -12000.0)
A4_XY = (155000.0, -9000.0)

HIGH_JUNCTION_XY = (176000.0, 0.0)

UP1_XY = (188000.0, -5000.0)
UP2_XY = (201000.0, -9000.0)

CAVE_ACCESS_XY = (178000.0, 6500.0)
CAVE_ENTRANCE_XY = (183000.0, 9000.0)

B4_XY = (160000.0, 35000.0)
B3_XY = (130000.0, 60000.0)
B2_XY = (105000.0, 45000.0)
B_BRIDGE_XY = (90000.0, 2500.0)

F1_XY = (86000.0, 6500.0)
F2_XY = (81000.0, 8500.0)
F3_XY = (78000.0, 5000.0)
F4_XY = (82000.0, 1200.0)

PATH_A_XY = [
    CONVERGENCE_XY,
    A1_XY,
    A2_XY,
    A_BRIDGE_XY,
    A3_XY,
    A4_XY,
    HIGH_JUNCTION_XY
]

PATH_B_XY = [
    HIGH_JUNCTION_XY,
    B4_XY,
    B3_XY,
    B2_XY,
    B_BRIDGE_XY
]

PATH_UP_XY = [
    HIGH_JUNCTION_XY,
    UP1_XY,
    UP2_XY
]

PATH_CAVE_XY = [
    HIGH_JUNCTION_XY,
    CAVE_ACCESS_XY,
    CAVE_ENTRANCE_XY
]

PATH_FLANK_XY = [
    B_BRIDGE_XY,
    F1_XY,
    F2_XY,
    F3_XY,
    F4_XY,
    A_BRIDGE_XY
]


def terrain_world_z_cm(x_cm, y_cm):
    return (
        terrain_height_m(
            x_cm / 100.0,
            y_cm / 100.0
        ) * 100.0
    )


def guide_point(xy):
    x_cm, y_cm = xy

    return V(
        x_cm,
        y_cm,
        terrain_world_z_cm(
            x_cm,
            y_cm
        ) + GUIDE_Z_OFFSET_CM
    )


def distance_3d(a, b):
    return math.sqrt(
        (b.x-a.x)**2
        + (b.y-a.y)**2
        + (b.z-a.z)**2
    )


def midpoint(a, b):
    return V(
        (a.x+b.x)/2.0,
        (a.y+b.y)/2.0,
        (a.z+b.z)/2.0
    )


def create_guide_polyline(
    name,
    points_xy,
    material,
    folder_name,
    width_cm=GUIDE_WIDTH_CM
):
    pts = [
        guide_point(p)
        for p in points_xy
    ]

    for i in range(
        len(pts)-1
    ):
        a = pts[i]
        b = pts[i+1]

        length = distance_3d(
            a,
            b
        )

        rotation = (
            unreal.MathLibrary.find_look_at_rotation(
                a,
                b
            )
        )

        spawn_box(
            "GUIDE_%s_%02d"
            % (
                name,
                i+1
            ),
            midpoint(a, b),
            (
                length * 1.015,
                width_cm,
                GUIDE_THICKNESS_CM
            ),
            material,
            folder_name,
            rotation
        )


create_guide_polyline(
    "A",
    PATH_A_XY,
    MAT_A,
    "Guides/A"
)

create_guide_polyline(
    "B",
    PATH_B_XY,
    MAT_B,
    "Guides/B"
)

create_guide_polyline(
    "HAUT",
    PATH_UP_XY,
    MAT_UP,
    "Guides/Chemin_haut"
)

create_guide_polyline(
    "GROTTE",
    PATH_CAVE_XY,
    MAT_CAVE,
    "Guides/Acces_grotte",
    145.0
)

create_guide_polyline(
    "FLANC",
    PATH_FLANK_XY,
    MAT_FLANK,
    "Guides/Flanc",
    145.0
)

create_guide_polyline(
    "PONT",
    [
        A_BRIDGE_XY,
        B_BRIDGE_XY
    ],
    MAT_BRIDGE,
    "Guides/Pont",
    BRIDGE_WIDTH_CM
)


# =============================================================================
# REPÈRES
# =============================================================================

convergence_point = guide_point(
    CONVERGENCE_XY
)

high_point = guide_point(
    HIGH_JUNCTION_XY
)

cave_point = guide_point(
    CAVE_ENTRANCE_XY
)

spawn_sphere(
    "REPERE_CONVERGENCE_17H00",
    V(
        convergence_point.x,
        convergence_point.y,
        convergence_point.z + 120.0
    ),
    80.0,
    MAT_MARKER
)

spawn_sphere(
    "REPERE_JONCTION_HAUTE",
    V(
        high_point.x,
        high_point.y,
        high_point.z + 120.0
    ),
    80.0,
    MAT_MARKER
)

spawn_sphere(
    "REPERE_GROTTE",
    V(
        cave_point.x,
        cave_point.y,
        cave_point.z + 120.0
    ),
    80.0,
    MAT_MARKER
)


# =============================================================================
# CAMÉRAS DE REVUE V07
# =====================================================================================================

def create_cine_camera(
    name,
    pos,
    target,
    focal=35.0
):
    cam = actors.spawn_actor_from_class(
        unreal.CineCameraActor,
        pos,
        unreal.Rotator(0, 0, 0),
        False
    )

    set_actor_name(
        cam,
        "CAM_REVIEW_" + name,
        "Cameras/Review_V07"
    )

    cam.set_actor_rotation(
        unreal.MathLibrary.find_look_at_rotation(
            pos,
            target
        ),
        False
    )

    try:
        cam.get_cine_camera_component().set_current_focal_length(
            float(focal)
        )
    except Exception:
        pass

    return cam


def target_at(x_cm, y_cm, extra_z_cm=0.0):
    return V(
        x_cm,
        y_cm,
        terrain_world_z_cm(
            x_cm,
            y_cm
        ) + extra_z_cm
    )


# Carte / vue aérienne générale.
cam_01 = create_cine_camera(
    "01_AERIAL_MAP",
    V(
        100800.0,
        0.0,
        225000.0
    ),
    target_at(
        100800.0,
        0.0,
        5000.0
    ),
    35.0
)

# Ensemble côté A.
cam_02 = create_cine_camera(
    "02_OVERVIEW_A",
    V(
        25000.0,
        -85000.0,
        36000.0
    ),
    target_at(
        105000.0,
        -5000.0,
        4000.0
    ),
    35.0
)

# Ensemble côté B.
cam_03 = create_cine_camera(
    "03_OVERVIEW_B",
    V(
        120000.0,
        105000.0,
        44000.0
    ),
    target_at(
        130000.0,
        25000.0,
        3500.0
    ),
    35.0
)

# Pont / flanc côté A.
cam_04 = create_cine_camera(
    "04_PONT_FLANC_A",
    V(
        76000.0,
        -23000.0,
        terrain_world_z_cm(
            76000.0,
            -23000.0
        ) + 12000.0
    ),
    target_at(
        85000.0,
        3500.0,
        800.0
    ),
    40.0
)

# Pont / flanc côté B.
cam_05 = create_cine_camera(
    "05_PONT_FLANC_B",
    V(
        101000.0,
        25000.0,
        terrain_world_z_cm(
            101000.0,
            25000.0
        ) + 12000.0
    ),
    target_at(
        85500.0,
        3500.0,
        800.0
    ),
    40.0
)

# Jonction haute.
cam_06 = create_cine_camera(
    "06_HIGH_JUNCTION",
    V(
        158000.0,
        -30000.0,
        terrain_world_z_cm(
            158000.0,
            -30000.0
        ) + 14000.0
    ),
    target_at(
        176000.0,
        0.0,
        1200.0
    ),
    42.0
)

# Accès grotte.
cam_07 = create_cine_camera(
    "07_CAVE_ACCESS",
    V(
        170000.0,
        -10000.0,
        terrain_world_z_cm(
            170000.0,
            -10000.0
        ) + 4500.0
    ),
    target_at(
        181000.0,
        7500.0,
        900.0
    ),
    45.0
)

# Sortie grotte vers B.
cam_08 = create_cine_camera(
    "08_CAVE_TO_B",
    V(
        183000.0,
        10500.0,
        terrain_world_z_cm(
            183000.0,
            10500.0
        ) + 2200.0
    ),
    target_at(
        160000.0,
        35000.0,
        1200.0
    ),
    35.0
)

# Convergence 17h00.
cam_09 = create_cine_camera(
    "09_CONVERGENCE",
    V(
        -7000.0,
        -9000.0,
        terrain_world_z_cm(
            0.0,
            0.0
        ) + 5000.0
    ),
    target_at(
        3500.0,
        300.0,
        900.0
    ),
    50.0
)

# Échelle humaine A.
cam_10 = create_cine_camera(
    "10_HUMAN_A",
    V(
        62000.0,
        -8000.0,
        terrain_world_z_cm(
            62000.0,
            -8000.0
        ) + 180.0
    ),
    target_at(
        73000.0,
        -4500.0,
        170.0
    ),
    35.0
)

# Échelle humaine B.
cam_11 = create_cine_camera(
    "11_HUMAN_B",
    V(
        131000.0,
        59500.0,
        terrain_world_z_cm(
            131000.0,
            59500.0
        ) + 180.0
    ),
    target_at(
        119000.0,
        52500.0,
        170.0
    ),
    35.0
)

actors.set_selected_level_actors(
    [cam_01]
)


# =============================================================================
# LOG FINAL
# =============================================================================

unreal.log(
    "============================================================"
)

unreal.log(
    "POLOP PREVIZ V07 PREPAREE"
)

unreal.log(
    "Heightmap : " + heightmap_path
)

unreal.log(
    "Instructions : " + instructions_path
)

unreal.log(
    "IMPORT LANDSCAPE :"
)

unreal.log(
    "Location X=0 Y=-100800 Z=0"
)

unreal.log(
    "Scale X=200 Y=200 Z=100"
)

unreal.log(
    "Flip Y Axis OFF au premier essai."
)

unreal.log(
    "Les PZ_GUIDE_* doivent reposer sur le Landscape."
)

unreal.log(
    "Camera selectionnee : PZ_CAM_REVIEW_01_AERIAL_MAP"
)

unreal.log(
    "============================================================"
)
