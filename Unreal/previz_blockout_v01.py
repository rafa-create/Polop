import math
import unreal

# LA BOUCLE / POLOP — blockout géographique V01
# Unreal Engine 5.8 — unités en centimètres.
# Ce script ne touche qu'aux Actors dont le label commence par PZ_.

PREFIX = "PZ_"
ROOT_FOLDER = "POLOP_PREVIZ"
PATH_WIDTH = 220.0
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


def midpoint(a, b):
    return V((a.x+b.x)/2, (a.y+b.y)/2, (a.z+b.z)/2)


def yaw_between(a, b):
    return math.degrees(math.atan2(b.y-a.y, b.x-a.x))


def folder(actor, path):
    try:
        actor.set_folder_path(unreal.Name(path))
    except Exception:
        pass


def label(actor, name, path):
    actor.set_actor_label(PREFIX + name, True)
    folder(actor, ROOT_FOLDER + "/" + path)
    return actor


def spawn_mesh(mesh, name, location, rotation=None, scale=None, outliner_folder="Blockout"):
    rotation = rotation or unreal.Rotator(0.0, 0.0, 0.0)
    actor = actor_system.spawn_actor_from_object(mesh, location, rotation, False)
    if not actor:
        raise RuntimeError("Échec création Actor: " + name)
    label(actor, name, outliner_folder)
    if scale:
        actor.set_actor_scale3d(scale)
    return actor


def spawn_box(name, location, size_xyz, rotation=None, outliner_folder="Blockout"):
    sx, sy, sz = size_xyz
    return spawn_mesh(
        CUBE, name, location, rotation,
        V(sx/100.0, sy/100.0, sz/100.0), outliner_folder
    )


def spawn_marker(name, location, radius=55.0, outliner_folder="Repères"):
    return spawn_mesh(
        SPHERE, name, location, None,
        V(radius/50.0, radius/50.0, radius/50.0), outliner_folder
    )


def spawn_person(name, location, height=180.0, outliner_folder="Personnages_proxy"):
    actor = spawn_mesh(
        CYLINDER, name, V(location.x, location.y, location.z + height/2), None,
        V(0.35, 0.35, height/100.0), outliner_folder
    )
    return actor


def spawn_segment(name, a, b, width=PATH_WIDTH, thickness=PATH_THICKNESS, outliner_folder="Chemins"):
    # V01 : ruban horizontal par segment, placé à l'altitude moyenne.
    # La pente précise sera sculptée après validation topologique.
    length = math.sqrt((b.x-a.x)**2 + (b.y-a.y)**2)
    center = midpoint(a, b)
    yaw = yaw_between(a, b)
    return spawn_box(
        name,
        center,
        (max(length, 20.0), width, thickness),
        unreal.Rotator(0.0, yaw, 0.0),
        outliner_folder
    )


def spawn_polyline(prefix, points, width=PATH_WIDTH, thickness=PATH_THICKNESS, outliner_folder="Chemins"):
    actors = []
    for i in range(len(points)-1):
        actors.append(spawn_segment(f"{prefix}_{i+1:02d}", points[i], points[i+1], width, thickness, outliner_folder))
    return actors


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
        unreal.log(f"POLOP PREVIZ: {len(victims)} anciens Actors supprimés.")


cleanup_previous()

# -----------------------------------------------------------------------------
# TOPOLOGIE V01
# A = montée normale de Thomas + Éva + Léa.
# B = descente de Thomas inversé.
# A et B se rejoignent en haut à la zone de la grotte.
# En bas/intermédiaire, pont et flanc permettent de passer entre A et B.
# Après B -> pont -> A, Thomas inversé atteint le point de convergence de 17h00.
# -----------------------------------------------------------------------------

CONVERGENCE_1700 = V(0, 0, 120)
A_LOW = V(650, 0, 210)
A_BRIDGE = V(1450, 0, 390)
A_HIGH = V(2400, -260, 690)
GROTTO = V(3400, 0, 980)

B_BRIDGE = V(1450, 1250, 390)
B_MID = V(2450, 1250, 690)

PATH_A = [CONVERGENCE_1700, A_LOW, A_BRIDGE, A_HIGH, GROTTO]
spawn_polyline("CHEMIN_A", PATH_A, outliner_folder="Chemin_A")

PATH_B = [GROTTO, B_MID, B_BRIDGE]
spawn_polyline("CHEMIN_B", PATH_B, outliner_folder="Chemin_B")

spawn_segment("PONT_TABLIER", A_BRIDGE, B_BRIDGE, BRIDGE_WIDTH, 18.0, "Pont")
spawn_box("PONT_PYLONE_A", V(A_BRIDGE.x, A_BRIDGE.y, A_BRIDGE.z + 90), (35, 35, 180), None, "Pont")
spawn_box("PONT_PYLONE_B", V(B_BRIDGE.x, B_BRIDGE.y, B_BRIDGE.z + 90), (35, 35, 180), None, "Pont")

FLANK_1 = V(1120, 1120, 345)
FLANK_2 = V(920, 700, 310)
FLANK_3 = V(1120, 250, 350)
PATH_FLANK = [B_BRIDGE, FLANK_1, FLANK_2, FLANK_3, A_BRIDGE]
spawn_polyline("FLANC", PATH_FLANK, width=180.0, outliner_folder="Flanc")

spawn_box("CREUX_FOND", V(1450, 625, 90), (1150, 1050, 80), None, "Relief")

spawn_box("RELIEF_CENTRAL_01", V(2200, 590, 390), (900, 620, 620), unreal.Rotator(0, -8, 0), "Relief")
spawn_box("RELIEF_CENTRAL_02", V(2850, 560, 610), (850, 680, 720), unreal.Rotator(0, 8, 0), "Relief")

spawn_box("GROTTE_PAROI_G", V(3460, -250, 1120), (520, 180, 520), None, "Grotte")
spawn_box("GROTTE_PAROI_D", V(3460, 250, 1120), (520, 180, 520), None, "Grotte")
spawn_box("GROTTE_LINTEAU", V(3460, 0, 1350), (520, 680, 120), None, "Grotte")
spawn_box("GROTTE_SOL", V(3650, 0, 960), (700, 500, 40), None, "Grotte")

spawn_marker("REPERE_CONVERGENCE_17H00", V(CONVERGENCE_1700.x, CONVERGENCE_1700.y, CONVERGENCE_1700.z + 90), 65)
spawn_marker("REPERE_LIAISON_A_PONT", V(A_BRIDGE.x, A_BRIDGE.y, A_BRIDGE.z + 70), 45)
spawn_marker("REPERE_LIAISON_B_PONT", V(B_BRIDGE.x, B_BRIDGE.y, B_BRIDGE.z + 70), 45)
spawn_marker("REPERE_GROTTE", V(GROTTO.x, GROTTO.y, GROTTO.z + 90), 55)

# Proxies : photographie de lecture spatiale, pas une chronologie simultanée.
spawn_person("THOMAS_NORMAL_PROXY", V(500, -20, 230), 180)
spawn_person("EVA_PROXY", V(650, -120, 245), 170)
spawn_person("LEA_PROXY_RETOUR_FLANC", V(1040, 610, 390), 135)
spawn_person("THOMAS_INVERSE_PROXY", V(2350, 1250, 805), 180)

cam_loc = V(-1900, -3600, 2700)
cam = actor_system.spawn_actor_from_class(unreal.CineCameraActor, cam_loc, unreal.Rotator(0, 0, 0), False)
label(cam, "CAM_OVERVIEW_GEOGRAPHIE", "Cameras")
try:
    target = V(1750, 500, 450)
    cam.set_actor_rotation(unreal.MathLibrary.find_look_at_rotation(cam_loc, target), False)
    cine = cam.get_cine_camera_component()
    cine.set_current_focal_length(35.0)
except Exception as exc:
    unreal.log_warning("POLOP PREVIZ: caméra créée mais réglage optique incomplet: " + str(exc))

seq_dir = "/Game/POLOP/Previz/Sequences"
unreal.EditorAssetLibrary.make_directory(seq_dir)
seq_path = seq_dir + "/LS_GEOGRAPHIE_V01"

if unreal.EditorAssetLibrary.does_asset_exist(seq_path):
    sequence = unreal.load_asset(seq_path)
else:
    sequence = asset_tools.create_asset(
        "LS_GEOGRAPHIE_V01",
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
unreal.log("POLOP PREVIZ V01 créée.")
unreal.log("Chemin A + Chemin B + Pont + Flanc + Grotte + Convergence 17h00.")
unreal.log("Tous les Actors générés commencent par PZ_ et sont regroupés dans POLOP_PREVIZ.")
unreal.log("Séquence: /Game/POLOP/Previz/Sequences/LS_GEOGRAPHIE_V01")
unreal.log("============================================================")
