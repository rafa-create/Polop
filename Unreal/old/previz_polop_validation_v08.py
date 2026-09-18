import json
import math
import os
import unreal

# =============================================================================
# POLOP / LA BOUCLE — VALIDATION AUTOMATIQUE V08
# Unreal Engine 5.8
#
# À exécuter APRES import du Landscape V08.
#
# Le script NE MODIFIE PAS le Landscape.
# Il :
# - détecte les Landscapes du niveau ;
# - raycast le terrain sous A / B / flanc / chemin haut / accès grotte ;
# - compare la hauteur Unreal à la hauteur canonique des chemins ;
# - mesure le ravin au pont ;
# - teste deux lignes de vue A <-> B ;
# - écrit JSON + TXT dans Saved/POLOP/V08/validation/ ;
# - crée des sphères rouges uniquement aux points qui échouent fortement.
#
# Résultat à m'envoyer :
#   Saved/POLOP/V08/validation/validation_v08.txt
# ou validation_v08.json
# =============================================================================

VERSION = "V08"
VALIDATION_PREFIX = "PZ_VALIDATION_V08_"
SAMPLE_STEP_M = 20.0
OK_CM = 75.0
WARN_CM = 150.0
FAIL_CM = 300.0
TRACE_TOP_CM = 80000.0
TRACE_BOTTOM_CM = -30000.0

actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
editor = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)
world = editor.get_editor_world()

SPHERE = unreal.load_asset("/Engine/BasicShapes/Sphere.Sphere")

PATHS = {
    "A": [
        (0.0, 0.0, 0.0),
        (300.0, -50.0, 20.0),
        (650.0, -80.0, 45.0),
        (900.0, 0.0, 70.0),
        (1250.0, -120.0, 100.0),
        (1550.0, -90.0, 135.0),
        (1760.0, 0.0, 158.0),
    ],
    "B": [
        (1760.0, 0.0, 158.0),
        (1600.0, 350.0, 140.0),
        (1300.0, 600.0, 115.0),
        (1050.0, 450.0, 90.0),
        (900.0, 25.0, 70.0),
    ],
    "HAUT": [
        (1760.0, 0.0, 158.0),
        (1880.0, -50.0, 172.0),
        (2010.0, -90.0, 188.0),
    ],
    "GROTTE": [
        (1760.0, 0.0, 158.0),
        (1780.0, 65.0, 158.5),
        (1830.0, 90.0, 160.5),
    ],
    "FLANC": [
        (900.0, 25.0, 70.0),
        (860.0, 65.0, 66.0),
        (810.0, 85.0, 62.0),
        (780.0, 50.0, 59.0),
        (820.0, 12.0, 63.0),
        (900.0, 0.0, 70.0),
    ],
}

A_BRIDGE = (900.0, 0.0, 70.0)
B_BRIDGE = (900.0, 25.0, 70.0)

LOS_TESTS = [
    {
        "name": "A3_vs_B3",
        "a": (1250.0, -120.0, 100.0),
        "b": (1300.0, 600.0, 115.0),
    },
    {
        "name": "A4_vs_B4",
        "a": (1550.0, -90.0, 135.0),
        "b": (1600.0, 350.0, 140.0),
    },
]

def V(x, y, z):
    return unreal.Vector(float(x), float(y), float(z))

def get_prop(obj, name, default=None):
    try:
        return obj.get_editor_property(name)
    except Exception:
        try:
            return getattr(obj, name)
        except Exception:
            return default

def actor_label(actor):
    if not actor:
        return ""
    try:
        return actor.get_actor_label()
    except Exception:
        return str(actor)

def class_name(actor):
    if not actor:
        return ""
    try:
        return actor.get_class().get_name()
    except Exception:
        return ""

def cleanup_validation_markers():
    old = []
    for actor in actors.get_all_level_actors():
        try:
            if actor.get_actor_label().startswith(VALIDATION_PREFIX):
                old.append(actor)
        except Exception:
            pass
    if old:
        actors.destroy_actors(old)

cleanup_validation_markers()

all_actors = actors.get_all_level_actors()
landscape_actors = []
ignore_actors = []

for actor in all_actors:
    label = actor_label(actor)
    cls = class_name(actor)
    if "Landscape" in cls:
        landscape_actors.append(actor)
    if label.startswith("PZ_"):
        ignore_actors.append(actor)

if not landscape_actors:
    raise RuntimeError(
        "Aucun Landscape détecté. Importer le Landscape V08 avant validation."
    )

def vertical_trace(x_m, y_m):
    x_cm = x_m * 100.0
    y_cm = y_m * 100.0
    start = V(x_cm, y_cm, TRACE_TOP_CM)
    end = V(x_cm, y_cm, TRACE_BOTTOM_CM)

    hit = unreal.SystemLibrary.line_trace_single(
        world,
        start,
        end,
        unreal.TraceTypeQuery.TRACE_TYPE_QUERY1,
        True,
        ignore_actors,
        unreal.DrawDebugTrace.NONE,
        True,
    )

    if not hit:
        return None

    point = get_prop(hit, "impact_point")
    hit_actor = get_prop(hit, "hit_actor")

    if point is None:
        return None

    return {
        "z_cm": float(point.z),
        "actor": actor_label(hit_actor),
        "class": class_name(hit_actor),
        "point": point,
    }

def segment_length_2d(a, b):
    return math.hypot(b[0] - a[0], b[1] - a[1])

def interpolate(a, b, t):
    return (
        a[0] + (b[0] - a[0]) * t,
        a[1] + (b[1] - a[1]) * t,
        a[2] + (b[2] - a[2]) * t,
    )

def sample_path(path, step_m=SAMPLE_STEP_M):
    samples = []
    for i in range(len(path) - 1):
        a = path[i]
        b = path[i + 1]
        length = segment_length_2d(a, b)
        count = max(1, int(math.ceil(length / step_m)))
        first = 0 if i == 0 else 1
        for j in range(first, count + 1):
            samples.append(interpolate(a, b, j / float(count)))
    return samples

def ensure_fail_material():
    path = "/Game/POLOP/Previz/Materials/M_VALIDATION_FAIL"
    if unreal.EditorAssetLibrary.does_asset_exist(path):
        return unreal.load_asset(path)

    asset_tools = unreal.AssetToolsHelpers.get_asset_tools()
    folder = "/Game/POLOP/Previz/Materials"
    mat = asset_tools.create_asset(
        "M_VALIDATION_FAIL",
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
        unreal.LinearColor(1.0, 0.0, 0.0, 1.0)
    )
    unreal.MaterialEditingLibrary.connect_material_property(
        expr,
        "",
        unreal.MaterialProperty.MP_BASE_COLOR
    )
    unreal.MaterialEditingLibrary.recompile_material(mat)
    unreal.EditorAssetLibrary.save_loaded_asset(mat)
    return mat

FAIL_MAT = ensure_fail_material()

def add_fail_marker(name, point):
    if not SPHERE:
        return

    actor = actors.spawn_actor_from_object(
        SPHERE,
        point,
        unreal.Rotator(0, 0, 0),
        False
    )
    actor.set_actor_label(
        VALIDATION_PREFIX + name,
        True
    )
    try:
        actor.set_folder_path(
            unreal.Name("POLOP_PREVIZ/Validation_V08")
        )
    except Exception:
        pass

    actor.set_actor_scale3d(V(2.0, 2.0, 2.0))

    try:
        comp = actor.get_component_by_class(unreal.StaticMeshComponent)
        if comp:
            comp.set_material(0, FAIL_MAT)
    except Exception:
        pass

path_reports = {}
global_failures = []

for path_name, path in PATHS.items():
    samples = sample_path(path)
    errors = []
    no_hits = 0
    wrong_hit_classes = []
    worst = None

    for index, sample in enumerate(samples):
        x_m, y_m, expected_z_m = sample
        hit = vertical_trace(x_m, y_m)

        if hit is None:
            no_hits += 1
            global_failures.append(
                "%s sample %d : aucun hit Landscape" % (path_name, index)
            )
            continue

        actual_z_cm = hit["z_cm"]
        expected_z_cm = expected_z_m * 100.0
        error_cm = actual_z_cm - expected_z_cm
        abs_error_cm = abs(error_cm)

        errors.append(abs_error_cm)

        if "Landscape" not in hit["class"]:
            wrong_hit_classes.append(
                {
                    "sample": index,
                    "class": hit["class"],
                    "actor": hit["actor"],
                }
            )

        if worst is None or abs_error_cm > worst["abs_error_cm"]:
            worst = {
                "sample": index,
                "x_m": x_m,
                "y_m": y_m,
                "expected_z_m": expected_z_m,
                "actual_z_m": actual_z_cm / 100.0,
                "error_cm": error_cm,
                "abs_error_cm": abs_error_cm,
            }

        if abs_error_cm >= FAIL_CM:
            add_fail_marker(
                "%s_%03d" % (path_name, index),
                V(
                    x_m * 100.0,
                    y_m * 100.0,
                    actual_z_cm + 150.0
                )
            )

    if errors:
        avg = sum(errors) / len(errors)
        maximum = max(errors)
        within_ok = sum(1 for e in errors if e <= OK_CM)
        within_warn = sum(1 for e in errors if e <= WARN_CM)
    else:
        avg = None
        maximum = None
        within_ok = 0
        within_warn = 0

    path_reports[path_name] = {
        "samples": len(samples),
        "hits": len(errors),
        "no_hits": no_hits,
        "mean_abs_error_cm": avg,
        "max_abs_error_cm": maximum,
        "within_75cm": within_ok,
        "within_150cm": within_warn,
        "wrong_hit_classes": wrong_hit_classes,
        "worst_sample": worst,
    }

hit_a = vertical_trace(A_BRIDGE[0], A_BRIDGE[1])
hit_b = vertical_trace(B_BRIDGE[0], B_BRIDGE[1])
hit_mid = vertical_trace(
    (A_BRIDGE[0] + B_BRIDGE[0]) / 2.0,
    (A_BRIDGE[1] + B_BRIDGE[1]) / 2.0,
)

ravine = {
    "valid": False,
    "depth_m": None,
}

if hit_a and hit_b and hit_mid:
    rim_avg_cm = (hit_a["z_cm"] + hit_b["z_cm"]) / 2.0
    depth_cm = rim_avg_cm - hit_mid["z_cm"]

    ravine = {
        "valid": True,
        "a_z_m": hit_a["z_cm"] / 100.0,
        "b_z_m": hit_b["z_cm"] / 100.0,
        "mid_z_m": hit_mid["z_cm"] / 100.0,
        "depth_m": depth_cm / 100.0,
    }

def line_of_sight_blocked(test):
    a = test["a"]
    b = test["b"]

    start = V(
        a[0] * 100.0,
        a[1] * 100.0,
        a[2] * 100.0 + 170.0
    )

    end = V(
        b[0] * 100.0,
        b[1] * 100.0,
        b[2] * 100.0 + 170.0
    )

    hit = unreal.SystemLibrary.line_trace_single(
        world,
        start,
        end,
        unreal.TraceTypeQuery.TRACE_TYPE_QUERY1,
        True,
        ignore_actors,
        unreal.DrawDebugTrace.NONE,
        True,
    )

    if not hit:
        return {
            "name": test["name"],
            "blocked": False,
            "hit_actor": None,
            "hit_class": None,
        }

    actor = get_prop(hit, "hit_actor")

    return {
        "name": test["name"],
        "blocked": True,
        "hit_actor": actor_label(actor),
        "hit_class": class_name(actor),
    }

los_reports = [
    line_of_sight_blocked(test)
    for test in LOS_TESTS
]

def classify_path(report):
    if report["no_hits"] > 0:
        return "FAIL"
    if report["max_abs_error_cm"] is None:
        return "FAIL"
    if report["max_abs_error_cm"] >= FAIL_CM:
        return "FAIL"
    if report["max_abs_error_cm"] > WARN_CM:
        return "WARN"
    return "OK"

statuses = {
    name: classify_path(report)
    for name, report in path_reports.items()
}

if ravine["valid"]:
    if ravine["depth_m"] >= 10.0:
        ravine_status = "OK"
    elif ravine["depth_m"] >= 5.0:
        ravine_status = "WARN"
    else:
        ravine_status = "FAIL"
else:
    ravine_status = "FAIL"

los_status = "OK" if all(
    test["blocked"]
    for test in los_reports
) else "FAIL"

overall = "OK"

if (
    "FAIL" in statuses.values()
    or ravine_status == "FAIL"
    or los_status == "FAIL"
):
    overall = "FAIL"
elif (
    "WARN" in statuses.values()
    or ravine_status == "WARN"
):
    overall = "WARN"

report = {
    "version": VERSION,
    "overall": overall,
    "landscapes_detected": [
        {
            "label": actor_label(a),
            "class": class_name(a),
            "location": {
                "x": float(a.get_actor_location().x),
                "y": float(a.get_actor_location().y),
                "z": float(a.get_actor_location().z),
            },
            "scale": {
                "x": float(a.get_actor_scale3d().x),
                "y": float(a.get_actor_scale3d().y),
                "z": float(a.get_actor_scale3d().z),
            },
        }
        for a in landscape_actors
    ],
    "tolerances_cm": {
        "ok": OK_CM,
        "warn": WARN_CM,
        "fail_marker": FAIL_CM,
    },
    "paths": path_reports,
    "path_status": statuses,
    "ravine": ravine,
    "ravine_status": ravine_status,
    "line_of_sight": los_reports,
    "line_of_sight_status": los_status,
    "failures": global_failures,
}

saved_dir = unreal.Paths.convert_relative_path_to_full(
    unreal.Paths.project_saved_dir()
)

out_dir = os.path.join(
    saved_dir,
    "POLOP",
    "V08",
    "validation"
)

os.makedirs(out_dir, exist_ok=True)

json_path = os.path.join(
    out_dir,
    "validation_v08.json"
)

txt_path = os.path.join(
    out_dir,
    "validation_v08.txt"
)

with open(json_path, "w", encoding="utf-8") as f:
    json.dump(report, f, indent=2, ensure_ascii=False)

lines = []
lines.append("POLOP — VALIDATION AUTOMATIQUE V08")
lines.append("=" * 60)
lines.append("OVERALL: %s" % overall)
lines.append("")
lines.append("LANDSCAPE")

for item in report["landscapes_detected"]:
    lines.append(
        "- %s | %s | loc=(%.1f, %.1f, %.1f) | scale=(%.2f, %.2f, %.2f)"
        % (
            item["label"],
            item["class"],
            item["location"]["x"],
            item["location"]["y"],
            item["location"]["z"],
            item["scale"]["x"],
            item["scale"]["y"],
            item["scale"]["z"],
        )
    )

lines.append("")
lines.append("CHEMINS")

for name in ["A", "B", "FLANC", "HAUT", "GROTTE"]:
    r = path_reports[name]
    lines.append(
        "%-7s : %-4s | hits %d/%d | mean %.1f cm | max %.1f cm"
        % (
            name,
            statuses[name],
            r["hits"],
            r["samples"],
            r["mean_abs_error_cm"] if r["mean_abs_error_cm"] is not None else -1,
            r["max_abs_error_cm"] if r["max_abs_error_cm"] is not None else -1,
        )
    )

    if r["worst_sample"]:
        w = r["worst_sample"]
        lines.append(
            "          pire point : x=%.1fm y=%.1fm attendu=%.2fm réel=%.2fm erreur=%+.1fcm"
            % (
                w["x_m"],
                w["y_m"],
                w["expected_z_m"],
                w["actual_z_m"],
                w["error_cm"],
            )
        )

lines.append("")
lines.append("RAVIN PONT")
lines.append(
    "status=%s | profondeur=%s m"
    % (
        ravine_status,
        ("%.2f" % ravine["depth_m"]) if ravine["depth_m"] is not None else "N/A",
    )
)

lines.append("")
lines.append("SEPARATION VISUELLE A/B")

for test in los_reports:
    lines.append(
        "- %s : %s (%s / %s)"
        % (
            test["name"],
            "BLOQUEE = OK" if test["blocked"] else "VISIBLE = FAIL",
            test["hit_actor"],
            test["hit_class"],
        )
    )

lines.append("")
lines.append("FICHIERS")
lines.append(json_path)
lines.append(txt_path)

with open(txt_path, "w", encoding="utf-8") as f:
    f.write("\n".join(lines))

unreal.log("============================================================")
unreal.log("POLOP VALIDATION V08")
unreal.log("OVERALL = " + overall)

for name in ["A", "B", "FLANC", "HAUT", "GROTTE"]:
    r = path_reports[name]
    unreal.log(
        "%s = %s | mean=%.1fcm | max=%.1fcm"
        % (
            name,
            statuses[name],
            r["mean_abs_error_cm"] if r["mean_abs_error_cm"] is not None else -1,
            r["max_abs_error_cm"] if r["max_abs_error_cm"] is not None else -1,
        )
    )

unreal.log(
    "RAVIN = %s | depth=%s m"
    % (
        ravine_status,
        ("%.2f" % ravine["depth_m"]) if ravine["depth_m"] is not None else "N/A",
    )
)

unreal.log("LOS A/B = " + los_status)
unreal.log("Rapport TXT : " + txt_path)
unreal.log("Rapport JSON : " + json_path)
unreal.log("============================================================")
