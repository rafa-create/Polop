import unreal

PREFIX = "PZ_CAM_CAL_V071_"
FOLDER = "POLOP_PREVIZ/Cameras/Calibration_V07_1"

actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)

def V(x, y, z):
    return unreal.Vector(float(x), float(y), float(z))

def cleanup():
    old = []
    for actor in actors.get_all_level_actors():
        try:
            if actor.get_actor_label().startswith(PREFIX):
                old.append(actor)
        except Exception:
            pass
    if old:
        actors.destroy_actors(old)

def set_folder(actor):
    try:
        actor.set_folder_path(unreal.Name(FOLDER))
    except Exception:
        pass

def tag(actor, name):
    actor.set_actor_label(PREFIX + name, True)
    set_folder(actor)
    return actor

def create_top_ortho(name, position, target, ortho_width):
    cam = actors.spawn_actor_from_class(
        unreal.CameraActor, position, unreal.Rotator(0, 0, 0), False
    )
    tag(cam, name)
    cam.set_actor_rotation(
        unreal.MathLibrary.find_look_at_rotation(position, target), False
    )
    comp = cam.get_camera_component()
    comp.set_editor_property(
        "projection_mode", unreal.CameraProjectionMode.ORTHOGRAPHIC
    )
    comp.set_editor_property("ortho_width", float(ortho_width))
    return cam

def create_cine(name, position, target, focal=35.0):
    cam = actors.spawn_actor_from_class(
        unreal.CineCameraActor, position, unreal.Rotator(0, 0, 0), False
    )
    tag(cam, name)
    cam.set_actor_rotation(
        unreal.MathLibrary.find_look_at_rotation(position, target), False
    )
    try:
        cam.get_cine_camera_component().set_current_focal_length(float(focal))
    except Exception:
        pass
    return cam

cleanup()

CENTER = V(100800, 0, 9000)

cam_01 = create_top_ortho(
    "01_TOP_ORTHO_FIXED",
    V(100800, 0, 230000),
    CENTER,
    225000
)

cam_02 = create_cine(
    "02_SIDE_PROFILE",
    V(100800, -125000, 32000),
    V(110000, 0, 9000),
    50.0
)

cam_03 = create_cine(
    "03_BRIDGE_ALIGNMENT",
    V(76000, -18000, 17000),
    V(86000, 3500, 7000),
    45.0
)

cam_04 = create_cine(
    "04_HIGH_ALIGNMENT",
    V(158000, -23000, 25500),
    V(178000, 4500, 15500),
    45.0
)

actors.set_selected_level_actors([cam_01])

unreal.log("============================================================")
unreal.log("POLOP V07.1 CAMERAS DE CALIBRATION CREEES")
unreal.log("01_TOP_ORTHO_FIXED")
unreal.log("02_SIDE_PROFILE")
unreal.log("03_BRIDGE_ALIGNMENT")
unreal.log("04_HIGH_ALIGNMENT")
unreal.log("Selection : PZ_CAM_CAL_V071_01_TOP_ORTHO_FIXED")
unreal.log("============================================================")
