import os
import json
import math
import struct
import zlib
import unreal

# =============================================================================
# POLOP — VALIDATION AUTOMATIQUE V09
# Lit directement le heightmap V09 + route_model_v09.json.
# Ne dépend pas des collisions Unreal et ne modifie pas le niveau.
# =============================================================================

HM_SIZE = 1009
OK_CM = 75.0
WARN_CM = 150.0

actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)


def load_png16(path):
    data = open(path,"rb").read()
    if data[:8] != b"\x89PNG\r\n\x1a\n":
        raise RuntimeError("PNG invalide")

    pos = 8
    width = height = depth = color = None
    chunks = bytearray()

    while pos < len(data):
        n = struct.unpack(">I",data[pos:pos+4])[0]
        pos += 4
        kind = data[pos:pos+4]
        pos += 4
        payload = data[pos:pos+n]
        pos += n + 4

        if kind == b"IHDR":
            width,height,depth,color,_,_,_ = struct.unpack(">IIBBBBB",payload)
        elif kind == b"IDAT":
            chunks.extend(payload)
        elif kind == b"IEND":
            break

    if (width,height,depth,color) != (HM_SIZE,HM_SIZE,16,0):
        raise RuntimeError("Format inattendu : %s"%(str((width,height,depth,color)),))

    raw = zlib.decompress(bytes(chunks))
    stride = HM_SIZE*2+1
    grid = []

    for y in range(HM_SIZE):
        row = raw[y*stride:(y+1)*stride]
        if row[0] != 0:
            raise RuntimeError("Filtre PNG non supporté : %d"%row[0])
        grid.append([
            struct.unpack(">H",row[1+i*2:3+i*2])[0]
            for i in range(HM_SIZE)
        ])

    return grid


landscapes = []
for actor in actors.get_all_level_actors():
    try:
        if "Landscape" in actor.get_class().get_name():
            landscapes.append(actor)
    except Exception:
        pass

if not landscapes:
    raise RuntimeError("Aucun Landscape trouvé")

landscape = landscapes[0]
loc = landscape.get_actor_location()
scale = landscape.get_actor_scale3d()

saved = unreal.Paths.convert_relative_path_to_full(unreal.Paths.project_saved_dir())
root = os.path.join(saved,"POLOP","V09")
png_path = os.path.join(root,"polop_v09_heightmap_1009.png")
route_path = os.path.join(root,"route_model_v09.json")

if not os.path.exists(png_path):
    raise RuntimeError("Heightmap V09 absent : "+png_path)
if not os.path.exists(route_path):
    raise RuntimeError("route_model_v09.json absent : "+route_path)

grid = load_png16(png_path)
model = json.load(open(route_path,"r",encoding="utf-8"))


def pixel_z_cm(ix,iy):
    v = grid[iy][ix]
    local_m = (v-32768.0)/32768.0*256.0
    return loc.z + local_m*scale.z


def height_world_cm(x_m,y_m,flip=False):
    fx = (x_m*100.0-loc.x)/scale.x
    fy = (y_m*100.0-loc.y)/scale.y

    if flip:
        fy = (HM_SIZE-1)-fy

    if fx < 0 or fy < 0 or fx > HM_SIZE-1 or fy > HM_SIZE-1:
        return None

    x0,y0 = int(math.floor(fx)),int(math.floor(fy))
    x1,y1 = min(HM_SIZE-1,x0+1),min(HM_SIZE-1,y0+1)
    tx,ty = fx-x0,fy-y0

    z00,z10 = pixel_z_cm(x0,y0),pixel_z_cm(x1,y0)
    z01,z11 = pixel_z_cm(x0,y1),pixel_z_cm(x1,y1)

    za = z00*(1-tx)+z10*tx
    zb = z01*(1-tx)+z11*tx
    return za*(1-ty)+zb*ty


def evaluate(flip):
    reports = {}
    total = 0.0
    count = 0

    for name,data in model["routes"].items():
        samples = data["samples"]
        test_samples = samples[::2]
        if test_samples[-1] != samples[-1]:
            test_samples.append(samples[-1])

        errors = []
        outside = 0
        worst = None

        for x,y,z in test_samples:
            actual = height_world_cm(x,y,flip)

            if actual is None:
                outside += 1
                continue

            err = actual-z*100.0
            ae = abs(err)
            errors.append(ae)
            total += ae
            count += 1

            if worst is None or ae > worst["abs_error_cm"]:
                worst = {
                    "x_m":x,"y_m":y,
                    "expected_z_m":z,
                    "actual_z_m":actual/100.0,
                    "error_cm":err,
                    "abs_error_cm":ae,
                }

        reports[name] = {
            "samples":len(test_samples),
            "hits":len(errors),
            "outside":outside,
            "mean_abs_error_cm":sum(errors)/len(errors) if errors else None,
            "max_abs_error_cm":max(errors) if errors else None,
            "worst":worst,
            "length_m":data["length_m"],
            "max_grade_percent":data["max_grade_percent"],
        }

    return reports,(total/count if count else 1e30)


normal,normal_mean = evaluate(False)
flipped,flipped_mean = evaluate(True)
use_flip = flipped_mean < normal_mean
paths = flipped if use_flip else normal


def status(r):
    if r["outside"] or r["max_abs_error_cm"] is None:
        return "FAIL"
    if r["max_abs_error_cm"] <= OK_CM:
        return "OK"
    if r["max_abs_error_cm"] <= WARN_CM:
        return "WARN"
    return "FAIL"


statuses = {name:status(r) for name,r in paths.items()}


def h(x,y):
    return height_world_cm(x,y,use_flip)


za,zb,zm = h(900,0),h(900,25),h(900,12.5)
ravine = None if None in (za,zb,zm) else ((za+zb)/2.0-zm)/100.0

bridge_deck = None if None in (za,zb) else (za+zb)/200.0 + 0.45
bridge_clearance = None if bridge_deck is None or zm is None else bridge_deck-zm/100.0
bridge_end_delta = None if None in (za,zb) else abs(za-zb)/100.0

LOS = [
    ("A3_vs_B3",(1250,-120,100),(1300,600,115)),
    ("A4_vs_B4",(1550,-90,135),(1600,350,140)),
]


def los_blocked(a,b):
    d = math.hypot(b[0]-a[0],b[1]-a[1])
    n = max(1,int(math.ceil(d/5.0)))

    for i in range(1,n):
        t = i/float(n)
        x = a[0]+(b[0]-a[0])*t
        y = a[1]+(b[1]-a[1])*t
        eye = (a[2]+1.7)+(b[2]-a[2])*t
        terrain = h(x,y)
        if terrain is not None and terrain/100.0 > eye:
            return True
    return False


los = [{"name":n,"blocked":los_blocked(a,b)} for n,a,b in LOS]

grade_status = "OK"
for r in paths.values():
    if r["max_grade_percent"] > 25.0:
        grade_status = "FAIL"
    elif r["max_grade_percent"] > 18.0 and grade_status == "OK":
        grade_status = "WARN"

ravine_status = "OK" if ravine is not None and ravine >= 5.0 else "FAIL"
los_status = "OK" if all(x["blocked"] for x in los) else "FAIL"
bridge_status = "OK" if (
    bridge_clearance is not None
    and bridge_clearance >= 5.0
    and bridge_end_delta is not None
    and bridge_end_delta <= 1.0
) else "FAIL"

overall = "OK"
if (
    "FAIL" in statuses.values()
    or ravine_status == "FAIL"
    or los_status == "FAIL"
    or bridge_status == "FAIL"
    or grade_status == "FAIL"
):
    overall = "FAIL"
elif "WARN" in statuses.values() or grade_status == "WARN":
    overall = "WARN"


report = {
    "version":"V09",
    "overall":overall,
    "landscape":{
        "location":{"x":loc.x,"y":loc.y,"z":loc.z},
        "scale":{"x":scale.x,"y":scale.y,"z":scale.z},
    },
    "orientation":{
        "selected":"FLIPPED_Y" if use_flip else "NORMAL",
        "normal_mean_error_cm":normal_mean,
        "flipped_mean_error_cm":flipped_mean,
    },
    "paths":paths,
    "statuses":statuses,
    "grade_status":grade_status,
    "ravine_depth_m":ravine,
    "ravine_status":ravine_status,
    "bridge":{
        "deck_z_m":bridge_deck,
        "clearance_mid_m":bridge_clearance,
        "end_height_delta_m":bridge_end_delta,
        "status":bridge_status,
    },
    "line_of_sight":los,
    "line_of_sight_status":los_status,
    "timing":model.get("timing",{}),
}

outdir = os.path.join(root,"validation")
os.makedirs(outdir,exist_ok=True)
json_path = os.path.join(outdir,"validation_v09.json")
txt_path = os.path.join(outdir,"validation_v09.txt")

with open(json_path,"w",encoding="utf-8") as f:
    json.dump(report,f,indent=2,ensure_ascii=False)

lines = [
    "POLOP — VALIDATION V09",
    "="*64,
    "OVERALL: "+overall,
    "Orientation: %s | normal %.1fcm | flipped %.1fcm"%(
        report["orientation"]["selected"],normal_mean,flipped_mean
    ),
    "",
    "CHEMINS COURBES",
]

for name in ["A","B","FLANC","HAUT","GROTTE"]:
    r = paths[name]
    lines.append(
        "%-7s : %-4s | %d/%d | mean %.1fcm | max %.1fcm | longueur %.1fm | pente max %.1f%%"%(
            name,statuses[name],r["hits"],r["samples"],
            r["mean_abs_error_cm"] or 0.0,
            r["max_abs_error_cm"] or 0.0,
            r["length_m"],r["max_grade_percent"]
        )
    )

lines += [
    "",
    "RAVIN : %s | %.2fm"%(ravine_status,ravine if ravine is not None else -1),
    "PONT  : %s | clearance %.2fm | delta rives %.2fm"%(
        bridge_status,
        bridge_clearance if bridge_clearance is not None else -1,
        bridge_end_delta if bridge_end_delta is not None else -1
    ),
    "LOS A/B : "+", ".join("%s=%s"%(x["name"],"BLOCKED" if x["blocked"] else "VISIBLE") for x in los),
    "PENTES : "+grade_status,
    "",
    "TIMING",
    "A : %.1fm / %.1fmin"%(
        report["timing"].get("A_length_m",-1),
        report["timing"].get("A_minutes_at_2_2_kmh",-1)
    ),
    "Thomas inverse : %.1fm / %.1fmin total"%(
        report["timing"].get("inverse_length_m",-1),
        report["timing"].get("inverse_total_with_7min_pause",-1)
    ),
    "Flanc : %.1fm"%report["timing"].get("flank_length_m",-1),
    "",
    "JSON: "+json_path,
]

with open(txt_path,"w",encoding="utf-8") as f:
    f.write("\n".join(lines))

unreal.log("============================================================")
for line in lines[:16]:
    unreal.log(line)
unreal.log("Rapport : "+txt_path)
unreal.log("============================================================")
