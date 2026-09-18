import unreal

# POLOP — CAMERAS V08.1
# Ne touche ni au Landscape ni aux guides.
# Supprime/recrée uniquement PZ_CAM_V081_*.
# Chaque caméra est créée dans un try/except : une erreur n'arrête plus la suite.

PREFIX = "PZ_CAM_V081_"
FOLDER = "POLOP_PREVIZ/Cameras/Review_V08_1"

actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)

def V(x, y, z):
    return unreal.Vector(float(x), float(y), float(z))

def cleanup():
    old = []
    for a in actors.get_all_level_actors():
        try:
            if a.get_actor_label().startswith(PREFIX):
                old.append(a)
        except Exception:
            pass
    if old:
        actors.destroy_actors(old)

def label(cam, name):
    cam.set_actor_label(PREFIX + name, True)
    try:
        cam.set_folder_path(unreal.Name(FOLDER))
    except Exception:
        pass

def make_cam(name, pos, target, focal):
    try:
        cam = actors.spawn_actor_from_class(
            unreal.CineCameraActor, pos, unreal.Rotator(0,0,0), False
        )
        if not cam:
            raise RuntimeError("spawn_actor_from_class a renvoyé None")
        label(cam, name)
        cam.set_actor_rotation(
            unreal.MathLibrary.find_look_at_rotation(pos, target), False
        )
        cine = cam.get_cine_camera_component()
        cine.set_current_focal_length(float(focal))
        unreal.log("POLOP CAM OK : " + PREFIX + name)
        return cam
    except Exception as exc:
        unreal.log_error("POLOP CAM FAIL %s : %s" % (name, exc))
        return None

cleanup()

specs = [
    ("01_TOP_MAP", V(100800,0,520000), V(100800,0,9000), 50),
    ("02_SIDE_PROFILE", V(100800,-145000,33000), V(110000,0,10000), 50),
    ("03_BRIDGE_A", V(76000,-19000,18000), V(85500,3500,7200), 42),
    ("04_BRIDGE_B", V(102000,23000,19000), V(85500,3500,7200), 42),
    ("05_HIGH_JUNCTION", V(157000,-27000,30000), V(177000,2500,16000), 45),
    ("06_CAVE_ACCESS", V(170000,-9000,22000), V(181000,7800,16200), 45),
    ("07_HUMAN_A", V(62000,-8000,4900), V(72000,-5000,5700), 35),
    ("08_HUMAN_B", V(131000,59500,13200), V(119000,52000,11000), 35),
]

created = []
for name, pos, target, focal in specs:
    cam = make_cam(name, pos, target, focal)
    if cam:
        created.append(cam)

if created:
    actors.set_selected_level_actors([created[0]])

unreal.log("============================================================")
unreal.log("POLOP CAMERAS V08.1 : %d / %d créées" % (len(created), len(specs)))
unreal.log("Si le nombre n'est pas 8, lire les lignes POLOP CAM FAIL.")
unreal.log("============================================================")
