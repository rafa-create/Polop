import unreal

# =============================================================================
# POLOP / LA BOUCLE — CAMERA CALIBRATION V07.2
#
# Corrige V07.1 qui pouvait s'arrêter après la première caméra.
#
# Ce script :
# - NE MODIFIE PAS le Landscape ;
# - NE MODIFIE PAS les guides PZ_GUIDE_* ;
# - NE MODIFIE PAS les caméras PZ_CAM_REVIEW_* ;
# - supprime/recrée uniquement les caméras PZ_CAM_CAL_V072_*.
#
# Caméras créées :
#   01_TOP_MAP
#   02_SIDE_PROFILE
#   03_BRIDGE_ALIGNMENT
#   04_HIGH_ALIGNMENT
# =============================================================================

PREFIX = "PZ_CAM_CAL_V072_"
FOLDER = "POLOP_PREVIZ/Cameras/Calibration_V07_2"

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

    unreal.log(
        "POLOP V07.2 : %d anciennes cameras supprimees."
        % len(old)
    )


def put_in_folder(actor):
    try:
        actor.set_folder_path(
            unreal.Name(FOLDER)
        )
    except Exception:
        pass


def label(actor, name):
    actor.set_actor_label(
        PREFIX + name,
        True
    )
    put_in_folder(actor)
    return actor


def create_cine(name, position, target, focal=35.0):
    cam = actors.spawn_actor_from_class(
        unreal.CineCameraActor,
        position,
        unreal.Rotator(0.0, 0.0, 0.0),
        False
    )

    if not cam:
        raise RuntimeError(
            "Impossible de creer la camera " + name
        )

    label(cam, name)

    cam.set_actor_rotation(
        unreal.MathLibrary.find_look_at_rotation(
            position,
            target
        ),
        False
    )

    try:
        cine = cam.get_cine_camera_component()
        cine.set_current_focal_length(
            float(focal)
        )
    except Exception as exc:
        unreal.log_warning(
            "Focale non appliquee sur %s : %s"
            % (name, exc)
        )

    return cam


cleanup()

CENTER = V(
    100800.0,
    0.0,
    9000.0
)

cam_01 = create_cine(
    "01_TOP_MAP",
    V(
        100800.0,
        0.0,
        300000.0
    ),
    CENTER,
    85.0
)

cam_02 = create_cine(
    "02_SIDE_PROFILE",
    V(
        100800.0,
        -145000.0,
        31000.0
    ),
    V(
        105000.0,
        0.0,
        8500.0
    ),
    50.0
)

cam_03 = create_cine(
    "03_BRIDGE_ALIGNMENT",
    V(
        74000.0,
        -23000.0,
        17500.0
    ),
    V(
        85500.0,
        3500.0,
        7200.0
    ),
    45.0
)

cam_04 = create_cine(
    "04_HIGH_ALIGNMENT",
    V(
        154000.0,
        -28000.0,
        26000.0
    ),
    V(
        178000.0,
        4000.0,
        15500.0
    ),
    45.0
)

actors.set_selected_level_actors(
    [cam_01]
)

unreal.log("============================================================")
unreal.log("POLOP V07.2 CAMERAS CREEES")
unreal.log("PZ_CAM_CAL_V072_01_TOP_MAP")
unreal.log("PZ_CAM_CAL_V072_02_SIDE_PROFILE")
unreal.log("PZ_CAM_CAL_V072_03_BRIDGE_ALIGNMENT")
unreal.log("PZ_CAM_CAL_V072_04_HIGH_ALIGNMENT")
unreal.log("============================================================")
