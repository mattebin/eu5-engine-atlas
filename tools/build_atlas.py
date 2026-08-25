"""Classify every script keyword by which registrar its static initializer calls."""
import struct, re, sys, json, collections
sys.path.insert(0, r"T:\eu5-engine-atlas\tools")
from pe import PE

pe = PE(r"C:\SteamLibrary\steamapps\common\Europa Universalis V\binaries\eu5.exe")
d = pe.data
text = next(s for s in pe.sections if s["name"] == ".text")
LO, HI = text["rawptr"], text["rawptr"] + text["rawsize"]
LEA = re.compile(rb"\x48\x8d[\x05\x0d\x15\x1d\x25\x2d\x35\x3d]")

REGISTRARS = {0x1429D3D30: "effect", 0x142A2C880: "trigger"}

def fn_start(off):
    while off > LO and d[off - 1] != 0xCC:
        off -= 1
    return off

def keyword_in(fn_off, span=300):
    win = d[fn_off:fn_off + span]
    for m in LEA.finditer(win):
        ins = fn_off + m.start()
        disp = struct.unpack_from("<i", d, ins + 3)[0]
        nxt = pe.off_to_rva(ins + 7)
        if nxt is None:
            continue
        so = pe.va_to_off(pe.image_base + nxt + disp)
        if so is None:
            continue
        s = d[so:so + 96].split(b"\0")[0]
        if re.fullmatch(rb"[a-z][a-z0-9_]{2,63}", s):
            return s.decode()
    return None

found = collections.defaultdict(set)
for m in re.finditer(rb"\xe8", d[LO:HI]):
    off = LO + m.start()
    rel = struct.unpack_from("<i", d, off + 1)[0]
    nxt = pe.off_to_rva(off + 5)
    if nxt is None:
        continue
    tgt = pe.image_base + nxt + rel
    kind = REGISTRARS.get(tgt)
    if not kind:
        continue
    kw = keyword_in(fn_start(off))
    if kw:
        found[kind].add(kw)

for kind in ("effect", "trigger"):
    print(f"{kind:8}: {len(found[kind])} keywords")
json.dump({k: sorted(v) for k, v in found.items()},
          open("atlas.json", "w", encoding="utf-8"), indent=1)
print("\nsanity checks:")
for kw, want in (("refresh_map_colors", "effect"), ("close_all_views", "effect"),
                 ("set_variable", "effect"), ("has_variable", "trigger"),
                 ("current_year", "trigger"), ("exists", "trigger")):
    got = [k for k in found if kw in found[k]]
    print(f"   {kw:22} -> {got or '(missing)'}   expected {want}")
