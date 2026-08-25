"""Census of every candidate registrar: functions called by many small
keyword-interning initializers. Both snake_case and CamelCase keywords."""
import struct, re, sys, collections
sys.path.insert(0, r"T:\eu5-engine-atlas\tools")
from pe import PE
pe = PE(r"C:\SteamLibrary\steamapps\common\Europa Universalis V\binaries\eu5.exe")
d = pe.data
text = next(s for s in pe.sections if s["name"] == ".text")
LO, HI = text["rawptr"], text["rawptr"] + text["rawsize"]
LEA = re.compile(rb"\x48\x8d[\x05\x0d\x15\x1d\x25\x2d\x35\x3d]")
KW = re.compile(rb"(?:[a-z][a-z0-9_]{2,60}|[A-Z][A-Za-z0-9_]{2,60})")

KNOWN = {0x1429D3D30: "EFFECTS", 0x142A2C880: "TRIGGERS",
         0x1429C9B40: "scopes", 0x1429F1DE0: "scopes", 0x144C0DE80: "scopes",
         0x1406B2C40: "GUI FUNCS",
         0x14376B0D0: "intern", 0x14376A780: "intern", 0x14371EA90: "intern"}

def fn_bounds(o):
    lo = o
    while lo > LO and d[lo-1] != 0xCC:
        lo -= 1
    hi = o
    while hi < HI and d[hi] != 0xCC:
        hi += 1
    return lo, hi

inits = {}
for m in LEA.finditer(d[LO:HI]):
    ins = LO + m.start()
    disp = struct.unpack_from("<i", d, ins+3)[0]
    nxt = pe.off_to_rva(ins+7)
    if nxt is None:
        continue
    so = pe.va_to_off(pe.image_base + nxt + disp)
    if so is None:
        continue
    s = d[so:so+96].split(b"\0")[0]
    if not KW.fullmatch(s):
        continue
    lo, hi = fn_bounds(ins)
    if hi - lo > 420:
        continue
    inits.setdefault((lo, hi), s.decode())

cnt = collections.Counter()
ex = collections.defaultdict(list)
for (lo, hi), kw in inits.items():
    k = lo
    while k < hi - 4:
        if d[k] == 0xE8:
            rel = struct.unpack_from("<i", d, k+1)[0]
            nxt = pe.off_to_rva(k+5)
            if nxt:
                t = pe.image_base + nxt + rel
                o = pe.va_to_off(t)
                if o is not None and pe.section_of_off(o) == ".text":
                    cnt[t] += 1
                    if len(ex[t]) < 5:
                        ex[t].append(kw)
        k += 1

print(f"keyword initializers considered: {len(inits)}\n")
print(f"{'address':<14}{'count':>7}  {'label':<11} sample keywords")
for va, n in cnt.most_common(22):
    lab = KNOWN.get(va, "?")
    print(f"0x{va:X} {n:7}  {lab:<11} {', '.join(ex[va][:5])[:70]}")
