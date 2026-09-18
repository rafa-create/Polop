import os
import json
import math
import struct
import zlib
import unreal

# POLOP — VALIDATION V08.2
# Sans raycast : lit directement le PNG 16 bits généré par V08.
# Vérifie aussi la transform du Landscape importé.
# Ne modifie rien dans le niveau.

HM_SIZE = 1009
SAMPLE_STEP_M = 20.0
OK_CM = 75.0
WARN_CM = 150.0

PATHS = {
    "A": [(0,0,0),(300,-50,20),(650,-80,45),(900,0,70),(1250,-120,100),(1550,-90,135),(1760,0,158)],
    "B": [(1760,0,158),(1600,350,140),(1300,600,115),(1050,450,90),(900,25,70)],
    "HAUT": [(1760,0,158),(1880,-50,172),(2010,-90,188)],
    "GROTTE": [(1760,0,158),(1780,65,158.5),(1830,90,160.5)],
    "FLANC": [(900,25,70),(860,65,66),(810,85,62),(780,50,59),(820,12,63),(900,0,70)],
}

LOS_TESTS = [
    ("A3_vs_B3", (1250,-120,100), (1300,600,115)),
    ("A4_vs_B4", (1550,-90,135), (1600,350,140)),
]

actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)

def clamp(v,a,b): return max(a,min(b,v))

def load_png16_filter0(path):
    data = open(path,"rb").read()
    if data[:8] != b"\x89PNG\r\n\x1a\n":
        raise RuntimeError("PNG invalide")
    pos = 8
    width = height = bit_depth = color_type = None
    idat = bytearray()
    while pos < len(data):
        n = struct.unpack(">I", data[pos:pos+4])[0]; pos += 4
        kind = data[pos:pos+4]; pos += 4
        payload = data[pos:pos+n]; pos += n + 4
        if kind == b"IHDR":
            width,height,bit_depth,color_type,_,_,_ = struct.unpack(">IIBBBBB", payload)
        elif kind == b"IDAT":
            idat.extend(payload)
        elif kind == b"IEND":
            break
    if width != HM_SIZE or height != HM_SIZE or bit_depth != 16 or color_type != 0:
        raise RuntimeError("Format inattendu: %sx%s depth=%s color=%s" % (width,height,bit_depth,color_type))
    raw = zlib.decompress(bytes(idat))
    stride = width * 2 + 1
    values = []
    for y in range(height):
        row = raw[y*stride:(y+1)*stride]
        if row[0] != 0:
            raise RuntimeError("Filtre PNG %d non supporté (V08 doit écrire filtre 0)" % row[0])
        values.append([struct.unpack(">H", row[1+i*2:1+i*2+2])[0] for i in range(width)])
    return values

def sample_path(path, step=SAMPLE_STEP_M):
    out=[]
    for i in range(len(path)-1):
        a,b=path[i],path[i+1]
        d=math.hypot(b[0]-a[0], b[1]-a[1])
        n=max(1,int(math.ceil(d/step)))
        start=0 if i==0 else 1
        for j in range(start,n+1):
            t=j/float(n)
            out.append((
                a[0]+(b[0]-a[0])*t,
                a[1]+(b[1]-a[1])*t,
                a[2]+(b[2]-a[2])*t
            ))
    return out

landscapes=[]
for a in actors.get_all_level_actors():
    try:
        if "Landscape" in a.get_class().get_name():
            landscapes.append(a)
    except Exception:
        pass
if not landscapes:
    raise RuntimeError("Aucun Landscape trouvé")

landscape=landscapes[0]
loc=landscape.get_actor_location()
scale=landscape.get_actor_scale3d()

saved=unreal.Paths.convert_relative_path_to_full(unreal.Paths.project_saved_dir())
png_path=os.path.join(saved,"POLOP","V08","polop_v08_heightmap_1009.png")
if not os.path.exists(png_path):
    raise RuntimeError("Heightmap V08 absent: "+png_path)

grid=load_png16_filter0(png_path)

def pixel_height_world_cm(ix,iy):
    v=grid[iy][ix]
    local_m=(v-32768.0)/32768.0*256.0
    return loc.z + local_m * scale.z

def height_at_world_m(x_m,y_m,flip_y=False):
    x_cm=x_m*100.0; y_cm=y_m*100.0
    fx=(x_cm-loc.x)/scale.x
    fy=(y_cm-loc.y)/scale.y
    if flip_y:
        fy=(HM_SIZE-1)-fy
    if fx < 0 or fy < 0 or fx > HM_SIZE-1 or fy > HM_SIZE-1:
        return None
    x0=int(math.floor(fx)); y0=int(math.floor(fy))
    x1=min(HM_SIZE-1,x0+1); y1=min(HM_SIZE-1,y0+1)
    tx=fx-x0; ty=fy-y0
    z00=pixel_height_world_cm(x0,y0); z10=pixel_height_world_cm(x1,y0)
    z01=pixel_height_world_cm(x0,y1); z11=pixel_height_world_cm(x1,y1)
    za=z00*(1-tx)+z10*tx
    zb=z01*(1-tx)+z11*tx
    return za*(1-ty)+zb*ty

def evaluate_orientation(flip):
    reports={}
    total=0.0; count=0
    for name,path in PATHS.items():
        errs=[]; outside=0; worst=None
        for x,y,z in sample_path(path):
            actual=height_at_world_m(x,y,flip)
            if actual is None:
                outside += 1
                continue
            err=actual-z*100.0
            ae=abs(err); errs.append(ae); total+=ae; count+=1
            if worst is None or ae>worst["abs_error_cm"]:
                worst={"x_m":x,"y_m":y,"expected_z_m":z,"actual_z_m":actual/100.0,"error_cm":err,"abs_error_cm":ae}
        reports[name]={
            "samples":len(sample_path(path)),
            "hits":len(errs),
            "outside":outside,
            "mean_abs_error_cm":sum(errs)/len(errs) if errs else None,
            "max_abs_error_cm":max(errs) if errs else None,
            "worst":worst,
        }
    return reports, (total/count if count else 1e30)

normal, normal_mean=evaluate_orientation(False)
flipped, flipped_mean=evaluate_orientation(True)
use_flip = flipped_mean < normal_mean
paths = flipped if use_flip else normal

def status(r):
    if r["outside"]>0 or r["max_abs_error_cm"] is None: return "FAIL"
    if r["max_abs_error_cm"] <= OK_CM: return "OK"
    if r["max_abs_error_cm"] <= WARN_CM: return "WARN"
    return "FAIL"

statuses={k:status(v) for k,v in paths.items()}

def h(x,y):
    return height_at_world_m(x,y,use_flip)

za=h(900,0); zb=h(900,25); zm=h(900,12.5)
ravine_depth=None if None in (za,zb,zm) else (((za+zb)/2.0-zm)/100.0)

def los_blocked(a,b):
    d=math.hypot(b[0]-a[0],b[1]-a[1])
    n=max(1,int(math.ceil(d/5.0)))
    for i in range(1,n):
        t=i/float(n)
        x=a[0]+(b[0]-a[0])*t
        y=a[1]+(b[1]-a[1])*t
        eye=(a[2]+1.7)+(b[2]-a[2])*t
        terrain=h(x,y)
        if terrain is not None and terrain/100.0 > eye:
            return True
    return False

los=[{"name":n,"blocked":los_blocked(a,b)} for n,a,b in LOS_TESTS]

overall="OK"
if "FAIL" in statuses.values() or ravine_depth is None or not all(x["blocked"] for x in los):
    overall="FAIL"
elif "WARN" in statuses.values():
    overall="WARN"

report={
    "version":"V08.2",
    "overall":overall,
    "landscape":{
        "label":landscape.get_actor_label(),
        "location":{"x":loc.x,"y":loc.y,"z":loc.z},
        "scale":{"x":scale.x,"y":scale.y,"z":scale.z},
    },
    "heightmap":png_path,
    "orientation":{
        "selected":"FLIPPED_Y" if use_flip else "NORMAL",
        "normal_mean_error_cm":normal_mean,
        "flipped_mean_error_cm":flipped_mean,
    },
    "paths":paths,
    "statuses":statuses,
    "ravine_depth_m":ravine_depth,
    "line_of_sight":los,
}

outdir=os.path.join(saved,"POLOP","V08","validation")
os.makedirs(outdir,exist_ok=True)
json_path=os.path.join(outdir,"validation_v08_2.json")
txt_path=os.path.join(outdir,"validation_v08_2.txt")
with open(json_path,"w",encoding="utf-8") as f:
    json.dump(report,f,indent=2,ensure_ascii=False)

lines=[
    "POLOP — VALIDATION V08.2 (HEIGHTMAP DIRECT)",
    "="*60,
    "OVERALL: "+overall,
    "Landscape loc=(%.1f, %.1f, %.1f) scale=(%.1f, %.1f, %.1f)"%(loc.x,loc.y,loc.z,scale.x,scale.y,scale.z),
    "Orientation retenue: %s | normal mean=%.1fcm | flipped mean=%.1fcm"%(
        report["orientation"]["selected"],normal_mean,flipped_mean),
    "",
    "CHEMINS",
]
for name in ["A","B","FLANC","HAUT","GROTTE"]:
    r=paths[name]
    lines.append("%-7s : %-4s | %d/%d | mean %.1fcm | max %.1fcm | outside %d"%(
        name,statuses[name],r["hits"],r["samples"],
        r["mean_abs_error_cm"] if r["mean_abs_error_cm"] is not None else -1,
        r["max_abs_error_cm"] if r["max_abs_error_cm"] is not None else -1,
        r["outside"]))
lines += [
    "",
    "RAVIN: %s m"%("N/A" if ravine_depth is None else "%.2f"%ravine_depth),
    "LOS A/B: "+", ".join("%s=%s"%(x["name"],"BLOCKED" if x["blocked"] else "VISIBLE") for x in los),
    "",
    "JSON: "+json_path,
]
with open(txt_path,"w",encoding="utf-8") as f:
    f.write("\n".join(lines))

unreal.log("============================================================")
for line in lines[:12]:
    unreal.log(line)
unreal.log("Rapport: "+txt_path)
unreal.log("============================================================")
