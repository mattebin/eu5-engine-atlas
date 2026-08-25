"""Each keyword getter loads a global registry, then resolves its name to an
id. Group keywords by WHICH global they load -> that is the keyword's kind."""
import struct, re, sys, collections, json
sys.path.insert(0, r"T:\eu5-engine-atlas\tools")
from pe import PE

pe = PE(r"C:\SteamLibrary\steamapps\common\Europa Universalis V\binaries\eu5.exe")
d = pe.data
LEA = re.compile(rb"\x48\x8d[\x05\x0d\x15\x1d\x25\x2d\x35\x3d]")
MOVRIP = re.compile(rb"\x48\x8b[\x05\x0d\x15\x1d\x25\x2d\x35\x3d]")

def rip_target(ins_off, oplen=7):
    disp = struct.unpack_from("<i", d, ins_off + 3)[0]
    nxt = pe.off_to_rva(ins_off + oplen)
    return None if nxt is None else pe.image_base + nxt + disp

DATA = [x for x in pe.sections if x["name"] in (".data", "_RDATA")]

def in_data(va):
    """VA inside a data section, including the uninitialised tail past rawsize."""
    rva = va - pe.image_base
    return any(s["vaddr"] <= rva < s["vaddr"] + max(s["vsize"], s["rawsize"])
               for s in DATA)


def analyse(fn_va):
    """-> (keyword, registry_global_va)"""
    o = pe.va_to_off(fn_va)
    if o is None:
        return None, None
    win = d[o:o + 96]
    kw = reg = None
    for m in LEA.finditer(win):
        t = rip_target(o + m.start())
        so = pe.va_to_off(t) if t else None
        if so is None:
            continue
        s = d[so:so + 96].split(b"\0")[0]
        if re.fullmatch(rb"[a-z][a-z0-9_]{2,63}", s):
            kw = s.decode()
            break
    for m in MOVRIP.finditer(win):
        t = rip_target(o + m.start())
        if t is not None and in_data(t):
            reg = t
            break
    return kw, reg

# walk the CFG pointer run collected earlier
start, n = 0x05D05190, 32725
buckets = collections.defaultdict(list)
for i in range(n):
    v = struct.unpack_from("<Q", d, start + i * 8)[0]
    kw, reg = analyse(v)
    if kw and reg:
        buckets[reg].append(kw)

print(f"distinct registry globals: {len(buckets)}\n")
anchors = {"refresh_map_colors": "EFFECT?", "close_all_views": "EFFECT?",
           "has_variable": "TRIGGER?", "always": "TRIGGER?",
           "set_variable": "EFFECT?", "current_year": "TRIGGER?"}
for reg, kws in sorted(buckets.items(), key=lambda kv: -len(kv[1]))[:12]:
    hits = [f"{a}={t}" for a, t in anchors.items() if a in kws]
    print(f"  global 0x{reg:X}: {len(kws):5} keywords   {' '.join(hits)}")
json.dump({hex(k): sorted(v) for k, v in buckets.items()},
          open("keywords_by_registry.json", "w"), indent=1)
print("\nwritten: keywords_by_registry.json")
