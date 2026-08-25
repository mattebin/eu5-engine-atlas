import struct, re, sys, json, pathlib
sys.path.insert(0, r"T:\eu5-engine-atlas\tools")
from pe import PE
pe = PE(r"C:\SteamLibrary\steamapps\common\Europa Universalis V\binaries\eu5.exe")
d = pe.data
text = next(s for s in pe.sections if s["name"] == ".text")
LO, HI = text["rawptr"], text["rawptr"] + text["rawsize"]
LEA = re.compile(rb"\x48\x8d[\x05\x0d\x15\x1d\x25\x2d\x35\x3d]")
GUI_REG = 0x1406B2C40
CAMEL = re.compile(rb"[A-Z][A-Za-z0-9_]{2,60}")

def fn_start(o):
    while o > LO and d[o-1] != 0xCC:
        o -= 1
    return o

def camel_kw(fo, span=340):
    best = None
    for m in LEA.finditer(d[fo:fo+span]):
        ins = fo + m.start()
        disp = struct.unpack_from("<i", d, ins+3)[0]
        nxt = pe.off_to_rva(ins+7)
        if nxt is None:
            continue
        so = pe.va_to_off(pe.image_base + nxt + disp)
        if so is None:
            continue
        s = d[so:so+96].split(b"\0")[0]
        if CAMEL.fullmatch(s):
            if best is None:
                best = s.decode()
    return best

found = set()
n_sites = 0
for m in re.finditer(rb"\xe8", d[LO:HI]):
    off = LO + m.start()
    rel = struct.unpack_from("<i", d, off+1)[0]
    nxt = pe.off_to_rva(off+5)
    if nxt is None:
        continue
    if pe.image_base + nxt + rel == GUI_REG:
        n_sites += 1
        k = camel_kw(fn_start(off))
        if k:
            found.add(k)

print(f"registrar call sites : {n_sites}")
print(f"GUI functions found  : {len(found)}")

# what does vanilla's own gui actually use?
GAME = pathlib.Path(r"C:\SteamLibrary\steamapps\common\Europa Universalis V\game")
used = set()
ngui = 0
for p in GAME.rglob("*.gui"):
    try:
        b = p.read_bytes(); ngui += 1
        used.update(x.group(0).decode() for x in CAMEL.finditer(b))
    except Exception:
        pass
undoc = sorted(found - used)
print(f"vanilla .gui files   : {ngui}")
print(f"used by vanilla gui  : {len(found & used)}")
print(f"NEVER used in gui    : {len(undoc)}\n")
print(", ".join(undoc[:45]))
json.dump(sorted(found), open("gui_functions.json", "w", encoding="utf-8"), indent=1)
json.dump(undoc, open("gui_undocumented.json", "w", encoding="utf-8"), indent=1)
