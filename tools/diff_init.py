import struct, re, sys
sys.path.insert(0, r"T:\eu5-engine-atlas\tools")
from pe import PE
pe = PE(r"C:\SteamLibrary\steamapps\common\Europa Universalis V\binaries\eu5.exe")
d = pe.data
LEA = re.compile(rb"\x48\x8d[\x05\x0d\x15\x1d\x25\x2d\x35\x3d]")

def find_init(keyword):
    """the initializer function whose LEA points at this exact keyword"""
    so = d.find(keyword.encode() + b"\0")
    if so < 0:
        return None
    va = pe.image_base + pe.off_to_rva(so)
    text = next(s for s in pe.sections if s["name"] == ".text")
    lo, hi = text["rawptr"], text["rawptr"] + text["rawsize"]
    for m in LEA.finditer(d[lo:hi]):
        ins = lo + m.start()
        disp = struct.unpack_from("<i", d, ins + 3)[0]
        nxt = pe.off_to_rva(ins + 7)
        if nxt is not None and pe.image_base + nxt + disp == va:
            # back up to function start (int3 padding)
            fs = ins
            while fs > lo and d[fs-1] != 0xCC:
                fs -= 1
            return fs
    return None

def calls_in(fn_off, span=260):
    out = []
    for k in range(fn_off, min(fn_off + span, len(d) - 5)):
        if d[k] == 0xE8:
            rel = struct.unpack_from("<i", d, k + 1)[0]
            nxt = pe.off_to_rva(k + 5)
            if nxt:
                out.append(pe.image_base + nxt + rel)
    return out

for kw in ("refresh_map_colors", "close_all_views", "has_variable", "always", "current_year"):
    f = find_init(kw)
    if f is None:
        print(f"{kw:22} (not found)"); continue
    cs = calls_in(f)
    print(f"{kw:22} init@0x{pe.image_base + pe.off_to_rva(f):X}  calls: {[hex(c) for c in cs[:6]]}")
