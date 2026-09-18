import math
import unreal

# LA BOUCLE / POLOP — blockout géographique V02
# Objectif: même topologie que V01, mais lisible visuellement.
# UE 5.8 / unités en centimètres.
# Sécurité: le script ne supprime que les Actors dont le label commence par PZ_.

PREFIX = "PZ_"
ROOT_FOLDER = "POLOP_PREVIZ"
PATH_WIDTH_A = 260.0
PATH_WIDTH_B = 220.0
PATH_WIDTH_FLANK = 150.0
PATH_THICKNESS = 24.0
BRIDGE_WIDTH = 115.0

actor_system = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
asset_tools = unreal.AssetToolsHelpers.get_asset_tools()

CUBE = unreal.load_asset("/Engine/BasicShapes/Cube.Cube")
SPHERE = unreal.load_asset("/Engine/BasicShapes/Sphere.Sphere")
CYLINDER = unreal.load_asset("/Engine/BasicShapes/Cylinder.Cylinder")

if not CUBE or not SPHERE or not CYLINDER:
    raise RuntimeError("Impossible de charger les BasicShapes d'Unreal Engine.")


def V(x, y, z):
    return unreal.Vector(float(x), float(y), float(z))


def folder(actor, path):
    try:
        actor.set_folder_path(unreal.Name(path))
    except Exception:
        pass


def label(actor, name, path):
    actor.set_actor_label(PREFIX + name, True)
    folder(actor, ROOT_FOLDER + "/" + path)
    return actor


def cleanup_previous():
    victims = []
    for actor in actor_system.get_all_level_actors():
        try:
            if actor.get_actor_label().startswith(PREFIX):
                victims.append(actor)
        except Exception:
            pass
    if victims:
        actor_system.destroy_actors(victims)
        unreal.log(f"POLOP PREVIZ V02: {len(victims)} anciens Actors PZ_ supprimés.")


def ensure_material(name, rgb):
    mat_dir = "/Game/POLOP/Previz/Materials"
    unreal.EditorAssetLibrary.make_directory(mat_dir)
    path = f"{mat_dir}/{name}"

    if unreal.EditorAssetLibrary.does_asset_exist(path):
        return unreal.load_asset(path)

    try:
        mat = asset_tools.create_asset(
            name,
            mat_dir,
            unreal.Material,
            unreal.MaterialFactoryNew()
        )
        expr = unreal.MaterialEditingLibrary.create_material_expression(
            mat, unreal.MaterialExpressionConstant3Vector, -300, 0
        )
        expr.set_editor_property(
            "constant",
            unreal.LinearColor(float(rgb[0]), float(rgb[1]), float(rgb[2]), 1.0)
        )
        unreal.MaterialEditingLibrary.connect_material_property(
            expr, "", unreal.MaterialProperty.MP_BASE_COLOR
        )

        rough = unreal.MaterialEditingLibrary.create_material_expression(
            mat, unreal.MaterialExpressionConstant, -300, 160
        )
        rough.set_editor_property("r", 0.85)
        unreal.MaterialEditingLibrary.connect_material_property(
            rough, "", unreal.MaterialProperty.MP_ROUGHNESS
        )

        unreal.MaterialEditingLibrary.recompile_material(mat)
        unreal.EditorAssetLibrary.save_loaded_asset(mat)
        return mat
    except Exception as exc:
        unreal.log_warning(f"POLOP PREVIZ: matériau {name} non créé: {exc}")
        return None


def apply_material(actor, material):
    if not material:
        return
    try:
        comp = actor.get_component_by_class(unreal.StaticMeshComponent)
        if comp:
            comp.set_material(0, material)
    except Exception as exc:
        unreal.log_warning("POLOP PREVIZ: application matériau impossible: " + str(exc))


def spawn_mesh(mesh, name, location, rotation=None, scale=None, outliner_folder="Blockout", material=None):
    rotation = rotation or unreal.Rotator(0.0, 0.0, 0.0)
    actor = actor_system.spawn_actor_from_object(mesh, location, rotation, False)
    if not actor:
        raise RuntimeError("Échec création Actor: " + name)
    label(actor, name, outliner_folder)
    if scale:
        actor.set_actor_scale3d(scale)
    apply_material(actor, material)
    return actor


def spawn_box(name, location, size_xyz, rotation=None, outliner_folder="Blockout", material=None):
    sx, sy, sz = size_xyz
    return spawn_mesh(
        CUBE, name, location, rotation,
        V(sx / 100.0, sy / 100.0, sz / 100.0),
        outliner_folder, material
    )


def spawn_marker(name, location, radius=55.0, outliner_folder="Reperes", material=None):
    return spawn_mesh(
        SPHERE, name, location, None,
        V(radius / 50.0, radius / 50.0, radius / 50.0),
        outliner_folder, material
    )


def spawn_person(name, location, height=180.0, outliner_folder="Personnages_proxy", material=None):
    return spawn_mesh(
        CYLINDER,
        name,
        V(location.x, location.y, location.z + height / 2),
        None,
        V(0.35, 0.35, height / 100.0),
        outliner_folder,
        material
    )


def segment_rotation_and_length(a, b):
    dx = b.x - a.x
    dy = b.y - a.y
    dz = b.z - a.z
    horizontal = math.sqrt(dx * dx + dy * dy)
    length = math.sqrt(dx * dx + dy * dy + dz * dz)
    yaw = math.degrees(math.atan2(dy, dx))
    pitch = math.degrees(math.atan2(dz, horizontal))
    return unreal.Rotator(pitch, yaw, 0.0), length


def midpoint(a, b):
    return V((a.x + b.x) / 2, (a.y + b.y) / 2, (a.z + b.z) / 2)


def spawn_segment(name, a, b, width, thickness, outliner_folder, material):
    rotation, length = segment_rotation_and_length(a, b)
    return spawn_box(
        name,
        midpoint(a, b),
        (max(length, 20.0), width, thickness),
        rotation,
        outliner_folder,
        material
    )


def spawn_polyline(prefix, points, width, folder_name, material):
    out = []
    for i in range(len(points) - 1):
        out.append(
            spawn_segment(
                f"{prefix}_{i+1:02d}",
                points[i], points[i+1],
                width, PATH_THICKNESS,
                folder_name, material
            )
        )
    return out


def spawn_text(name, text, location, rotation=None, world_size=120.0, color=None):
    rotation = rotation or unreal.Rotator(0.0, 0.0, 0.0)
    actor = actor_system.spawn_actor_from_class(
        unreal.TextRenderActor, location, rotation, False
    )
    label(actor, name, "Etiquettes")
    comp = actor.get_component_by_class(unreal.TextRenderComponent)
    if comp:
        comp.set_text(unreal.Text(text))
        comp.set_world_size(world_size)
        if color:
            comp.set_text_render_color(color)
        try:
            comp.set_horizontal_alignment(unreal.HorizTextAligment.EHTA_CENTER)
        except Exception:
            pass
    return actor


cleanup_previous()

MAT_A = ensure_material("M_PREVIZ_CHEMIN_A", (0.10, 0.35, 0.95))
MAT_B = ensure_material("M_PREVIZ_CHEMIN_B", (0.95, 0.28, 0.12))
MAT_FLANK = ensure_material("M_PREVIZ_FLANC", (0.18, 0.75, 0.24))
MAT_BRIDGE = ensure_material("M_PREVIZ_PONT", (0.95, 0.75, 0.08))
MAT_RELIEF = ensure_material("M_PREVIZ_RELIEF", (0.25, 0.25, 0.25))
MAT_GROTTO = ensure_material("M_PREVIZ_GROTTE", (0.12, 0.12, 0.12))
MAT_NORMAL = ensure_material("M_PREVIZ_THOMAS_NORMAL", (0.15, 0.45, 1.0))
MAT_INVERSE = ensure_material("M_PREVIZ_THOMAS_INVERSE", (1.0, 0.20, 0.12))
MAT_EVA = ensure_material("M_PREVIZ_EVA", (0.75, 0.20, 0.85))
MAT_LEA = ensure_material("M_PREVIZ_LEA", (0.10, 0.85, 0.75))
MAT_MARKER = ensure_material("M_PREVIZ_REPERE", (1.0, 1.0, 0.1))

CONVERGENCE_1700 = V(0, 0, 120)

A_LOW = V(650, 0, 210)
A_BRIDGE = V(1450, 0, 390)
A_HIGH = V(2400, -260, 690)
GROTTO = V(3400, 0, 980)

B_BRIDGE = V(1450, 1250, 390)
B_MID = V(2450, 1250, 690)

PATH_A = [CONVERGENCE_1700, A_LOW, A_BRIDGE, A_HIGH, GROTTO]
PATH_B = [GROTTO, B_MID, B_BRIDGE]

spawn_polyline("CHEMIN_A", PATH_A, PATH_WIDTH_A, "Chemin_A", MAT_A)
spawn_polyline("CHEMIN_B", PATH_B, PATH_WIDTH_B, "Chemin_B", MAT_B)

spawn_segment(
    "PONT_TABLIER", A_BRIDGE, B_BRIDGE,
    BRIDGE_WIDTH, 18.0, "Pont", MAT_BRIDGE
)
spawn_box(
    "PONT_PYLONE_A",
    V(A_BRIDGE.x, A_BRIDGE.y, A_BRIDGE.z + 90),
    (35, 35, 180), None, "Pont", MAT_BRIDGE
)
spawn_box(
    "PONT_PYLONE_B",
    V(B_BRIDGE.x, B_BRIDGE.y, B_BRIDGE.z + 90),
    (35, 35, 180), None, "Pont", MAT_BRIDGE
)

FLANK_1 = V(1120, 1120, 345)
FLANK_2 = V(920, 700, 310)
FLANK_3 = V(1120, 250, 350)
PATH_FLANK = [B_BRIDGE, FLANK_1, FLANK_2, FLANK_3, A_BRIDGE]
spawn_polyline("FLANC", PATH_FLANK, PATH_WIDTH_FLANK, "Flanc", MAT_FLANK)

spawn_box(
    "RELIEF_CENTRAL_01",
    V(2200, 590, 500),
    (900, 640, 720),
    unreal.Rotator(0, -8, 0),
    "Relief", MAT_RELIEF
)
spawn_box(
    "RELIEF_CENTRAL_02",
    V(2900, 560, 730),
    (900, 720, 850),
    unreal.Rotator(0, 8, 0),
    "Relief", MAT_RELIEF
)
spawn_box(
    "CREUX_FOND",
    V(1450, 625, 90),
    (1150, 1050, 80),
    None, "Relief", MAT_RELIEF
)

spawn_box(
    "GROTTE_PAROI_G",
    V(3500, -250, 1120),
    (520, 180, 520),
    None, "Grotte", MAT_GROTTO
)
spawn_box(
    "GROTTE_PAROI_D",
    V(3500, 250, 1120),
    (520, 180, 520),
    None, "Grotte", MAT_GROTTO
)
spawn_box(
    "GROTTE_LINTEAU",
    V(3500, 0, 1350),
    (520, 680, 120),
    None, "Grotte", MAT_GROTTO
)
spawn_box(
    "GROTTE_SOL",
    V(3700, 0, 960),
    (800, 520, 40),
    None, "Grotte", MAT_GROTTO
)

spawn_marker(
    "REPERE_CONVERGENCE_17H00",
    V(CONVERGENCE_1700.x, CONVERGENCE_1700.y, CONVERGENCE_1700.z + 110),
    70, material=MAT_MARKER
)
spawn_marker(
    "REPERE_GROTTE",
    V(GROTTO.x, GROTTO.y, GROTTO.z + 110),
    55, material=MAT_MARKER
)

spawn_person(
    "THOMAS_NORMAL_PROXY",
    V(700, -70, 245),
    180, material=MAT_NORMAL
)
spawn_person(
    "EVA_PROXY",
    V(820, 80, 260),
    170, material=MAT_EVA
)
spawn_person(
    "LEA_PROXY_RETOUR_FLANC",
    V(1050, 650, 390),
    135, material=MAT_LEA
)
spawn_person(
    "THOMAS_INVERSE_PROXY",
    V(2350, 1250, 800),
    180, material=MAT_INVERSE
)

flat = unreal.Rotator(-90.0, 0.0, 0.0)
spawn_text(
    "TXT_A", "A - MONTEE NORMALE",
    V(2050, -360, 870), flat, 120,
    unreal.Color(40, 120, 255, 255)
)
spawn_text(
    "TXT_B", "B - DESCENTE INVERSEE",
    V(2350, 1550, 900), flat, 120,
    unreal.Color(255, 70, 40, 255)
)
spawn_text(
    "TXT_PONT", "PONT",
    V(1450, 625, 520), flat, 100,
    unreal.Color(255, 220, 40, 255)
)
spawn_text(
    "TXT_FLANC", "FLANC",
    V(850, 680, 470), flat, 90,
    unreal.Color(60, 220, 80, 255)
)
spawn_text(
    "TXT_GROTTE", "GROTTE",
    V(3500, 0, 1550), flat, 120,
    unreal.Color(255, 255, 255, 255)
)
spawn_text(
    "TXT_CONVERGENCE", "CONVERGENCE 17H00",
    V(0, -220, 400), flat, 105,
    unreal.Color(255, 255, 40, 255)
)

cam_loc = V(-2200, -4300, 3900)
cam = actor_system.spawn_actor_from_class(
    unreal.CineCameraActor,
    cam_loc,
    unreal.Rotator(0, 0, 0),
    False
)
label(cam, "CAM_OVERVIEW_GEOGRAPHIE", "Cameras")

try:
    target = V(1750, 500, 520)
    cam.set_actor_rotation(
        unreal.MathLibrary.find_look_at_rotation(cam_loc, target),
        False
    )
    cine = cam.get_cine_camera_component()
    cine.set_current_focal_length(28.0)
except Exception as exc:
    unreal.log_warning(
        "POLOP PREVIZ: caméra créée mais réglage optique incomplet: " + str(exc)
    )

seq_dir = "/Game/POLOP/Previz/Sequences"
unreal.EditorAssetLibrary.make_directory(seq_dir)
seq_path = seq_dir + "/LS_GEOGRAPHIE_V02"

if unreal.EditorAssetLibrary.does_asset_exist(seq_path):
    sequence = unreal.load_asset(seq_path)
else:
    sequence = asset_tools.create_asset(
        "LS_GEOGRAPHIE_V02",
        seq_dir,
        unreal.LevelSequence,
        unreal.LevelSequenceFactoryNew()
    )

if sequence:
    sequence.set_display_rate(unreal.FrameRate(numerator=24, denominator=1))
    sequence.set_playback_start(0)
    sequence.set_playback_end(240)
    unreal.EditorAssetLibrary.save_loaded_asset(sequence)

actor_system.set_selected_level_actors([cam])

unreal.log("============================================================")
unreal.log("POLOP PREVIZ V02 créée.")
unreal.log("BLEU = A / ROUGE = B / JAUNE = pont / VERT = flanc.")
unreal.log("La V02 aligne aussi les segments sur la pente réelle.")
unreal.log("Séquence: /Game/POLOP/Previz/Sequences/LS_GEOGRAPHIE_V02")
unreal.log("============================================================")
