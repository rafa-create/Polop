import os
import json
import math
import struct
import zlib
import unreal

# =============================================================================
# POLOP — VALIDATION V10
# Heightmap direct : routes, ravin, pont, grotte, LOS, timing.
# =============================================================================

HM_SIZE = 1009
OK_CM = 75.0
WARN_CM = 150.0

actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
saved = unreal.Paths.convert_relative_path_to_full(unreal.Paths.project_saved_dir())
root = os.path.join(saved,"POLOP","V10")
png_path = os.path.join(root,"polop_v10_heightmap_1009.png")
model_path = os.path.join(root,"route_model_v10.json")

if not os.path.exists(png_path):
    raise RuntimeError("Heightmap V10 absent")
if not os.path.exists(model_path):
    raise RuntimeError("route_model_v10 absent")


def load_png16(path):
    data = open(path,"rb").read()
    pos = 8
    idat = bytearray()
    whdc = None

    while pos < len(data):
        n = struct.unpack(">I",data[pos:pos+4])[0]; pos += 4
        kind = data[pos:pos+4]; pos += 4
        payload = data[pos:pos+n]; pos += n+4

        if kind == b"IHDR":
            whdc = struct.unpack(">IIBBBBB",payload)[:4]
        elif kind == b"IDAT":
            idat.extend(payload)
        elif kind == b"IEND":
            break

    if whdc != (1009,1009,16,0):
        raise RuntimeError("PNG V10 inattendu : "+str(whdc))

    raw = zlib.decompress(bytes(idat))
    stride = HM_SIZE*2+1
    grid = []

    for y in range(HM_SIZE):
        row = raw[y*stride:(y+1)*stride]
        if row[0] != 0:
            raise RuntimeError("Filtre PNG non supporté")
        grid.append([
            struct.unpack(">H",row[1+i*2:3+i*2])[0]
            for i in range(HM_SIZE)
        ])

    return grid


landscapes = []
for a in actors.get_all_level_actors():
    try:
        if "Landscape" in a.get_class().get_name():
            landscapes.append(a)
    except Exception:
        pass

if not landscapes:
    raise RuntimeError("Aucun Landscape")

landscape = landscapes[0]
loc = landscape.get_actor_location()
scale = landscape.get_actor_scale3d()
grid = load_png16(png_path)
model = json.load(open(model_path,"r",encoding="utf-8"))


def pixel_z(ix,iy):
    local_m = (grid[iy][ix]-32768.0)/32768.0*256.0
    return loc.z + local_m*scale.z


def h(x_m,y_m,flip=False):
    fx = (x_m*100.0-loc.x)/scale.x
    fy = (y_m*100.0-loc.y)/scale.y

    if flip:
        fy = (HM_SIZE-1)-fy

    if fx<0 or fy<0 or fx>HM_SIZE-1 or fy>HM_SIZE-1:
        return None

    x0,y0 = int(math.floor(fx)),int(math.floor(fy))
    x1,y1 = min(HM_SIZE-1,x0+1),min(HM_SIZE-1,y0+1)
    tx,ty = fx-x0,fy-y0

    z00,z10 = pixel_z(x0,y0),pixel_z(x1,y0)
    z01,z11 = pixel_z(x0,y1),pixel_z(x1,y1)

    return (z00*(1-tx)+z10*tx)*(1-ty)+(z01*(1-tx)+z11*tx)*ty


def evaluate(flip):
    reports = {}
    total = 0.0
    count = 0

    for name,data in model["routes"].items():
        samples = data["samples"][::2]
        if samples[-1] != data["samples"][-1]:
            samples.append(data["samples"][-1])

        errors = []
        outside = 0
        worst = None

        for x,y,z in samples:
            actual = h(x,y,flip)

            if actual is None:
                outside += 1
                continue

            err = actual-z*100.0
            ae = abs(err)
            errors.append(ae)
            total += ae
            count += 1

            if worst is None or ae>worst["abs_error_cm"]:
                worst = {
                    "x_m":x,"y_m":y,
                    "expected_z_m":z,
                    "actual_z_m":actual/100.0,
                    "error_cm":err,
                    "abs_error_cm":ae
                }

        reports[name] = {
            "hits":len(errors),
            "samples":len(samples),
            "outside":outside,
            "mean_abs_error_cm":sum(errors)/len(errors) if errors else None,
            "max_abs_error_cm":max(errors) if errors else None,
            "worst":worst,
            "length_m":data["length_m"],
            "max_grade_percent":data["max_grade_percent"],
        }

    return reports,(total/count if count else 1e30)


normal,nmean = evaluate(False)
flipped,fmean = evaluate(True)
use_flip = fmean<nmean
paths = flipped if use_flip else normal


def status(r):
    if r["outside"] or r["max_abs_error_cm"] is None:
        return "FAIL"
    if r["max_abs_error_cm"]<=OK_CM:
        return "OK"
    if r["max_abs_error_cm"]<=WARN_CM:
        return "WARN"
    return "FAIL"


statuses = {k:status(v) for k,v in paths.items()}


def H(x,y):
    return h(x,y,use_flip)


# Ravin + pont.
za,zb,zm = H(900,0),H(900,25),H(900,12.5)
ravine = None if None in (za,zb,zm) else ((za+zb)/2-zm)/100.0
bridge_end_delta = None if None in (za,zb) else abs(za-zb)/100.0
deck_z = None if None in (za,zb) else (za+zb)/200.0+0.45
bridge_clearance = None if deck_z is None or zm is None else deck_z-zm/100.0

ravine_status = "OK" if ravine is not None and ravine>=7.0 else "FAIL"
bridge_status = "OK" if (
    bridge_clearance is not None and bridge_clearance>=7.0
    and bridge_end_delta is not None and bridge_end_delta<=0.5
) else "FAIL"


# Grotte : la terrasse doit rester quasi plate entre entrée et fond court.
cave_entry = H(1830,90)
cave_back = H(1840.5,95.2)
cave_delta = None if None in (cave_entry,cave_back) else abs(cave_entry-cave_back)/100.0
cave_status = "OK" if cave_delta is not None and cave_delta<=0.75 else "FAIL"


# LOS.
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
        terrain = H(x,y)

        if terrain is not None and terrain/100.0>eye:
            return True

    return False


los = [{"name":n,"blocked":los_blocked(a,b)} for n,a,b in LOS]
los_status = "OK" if all(x["blocked"] for x in los) else "FAIL"

grade_status = "OK"
for r in paths.values():
    if r["max_grade_percent"]>25:
        grade_status="FAIL"
    elif r["max_grade_percent"]>18 and grade_status=="OK":
        grade_status="WARN"

overall = "OK"
if (
    "FAIL" in statuses.values()
    or ravine_status=="FAIL"
    or bridge_status=="FAIL"
    or cave_status=="FAIL"
    or los_status=="FAIL"
    or grade_status=="FAIL"
):
    overall="FAIL"
elif "WARN" in statuses.values() or grade_status=="WARN":
    overall="WARN"


report = {
    "version":"V10",
    "overall":overall,
    "orientation":{
        "selected":"FLIPPED_Y" if use_flip else "NORMAL",
        "normal_mean_error_cm":nmean,
        "flipped_mean_error_cm":fmean,
    },
    "paths":paths,
    "statuses":statuses,
    "ravine":{"depth_m":ravine,"status":ravine_status},
    "bridge":{
        "clearance_m":bridge_clearance,
        "end_delta_m":bridge_end_delta,
        "status":bridge_status,
    },
    "cave":{
        "entry_z_m":None if cave_entry is None else cave_entry/100.0,
        "back_z_m":None if cave_back is None else cave_back/100.0,
        "delta_m":cave_delta,
        "status":cave_status,
    },
    "line_of_sight":los,
    "line_of_sight_status":los_status,
    "grade_status":grade_status,
    "timing":model["timing"],
}

outdir = os.path.join(root,"validation")
os.makedirs(outdir,exist_ok=True)
json_path = os.path.join(outdir,"validation_v10.json")
txt_path = os.path.join(outdir,"validation_v10.txt")

with open(json_path,"w",encoding="utf-8") as f:
    json.dump(report,f,indent=2,ensure_ascii=False)

lines = [
    "POLOP — VALIDATION V10",
    "="*64,
    "OVERALL: "+overall,
    "Orientation: %s | normal %.1fcm | flipped %.1fcm"%(
        report["orientation"]["selected"],nmean,fmean
    ),
    "",
    "CHEMINS",
]

for name in ["A","B","FLANC","HAUT","GROTTE"]:
    r = paths[name]
    lines.append(
        "%-7s : %-4s | %d/%d | mean %.1fcm | max %.1fcm | pente %.1f%%"%(
            name,statuses[name],r["hits"],r["samples"],
            r["mean_abs_error_cm"] or 0,
            r["max_abs_error_cm"] or 0,
            r["max_grade_percent"]
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
    "GROTTE: %s | delta terrasse %.2fm"%(
        cave_status,cave_delta if cave_delta is not None else -1
    ),
    "LOS A/B : "+", ".join(
        "%s=%s"%(x["name"],"BLOCKED" if x["blocked"] else "VISIBLE")
        for x in los
    ),
    "PENTES : "+grade_status,
    "",
    "TIMING",
    "Thomas inverse : %.1fm"%model["timing"]["inverse_length_m"],
    "Vitesse exacte pour 60min avec 7min pause : %.3f km/h"%(
        model["timing"]["inverse_speed_kmh_for_exact_60min_with_7min_pause"]
    ),
    "",
    "JSON: "+json_path,
]

with open(txt_path,"w",encoding="utf-8") as f:
    f.write("\n".join(lines))

unreal.log("============================================================")
for line in lines[:17]:
    unreal.log(line)
unreal.log("Rapport : "+txt_path)
unreal.log("============================================================")
