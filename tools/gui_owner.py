"""Can we recover the OWNING TYPE of each GUI function from its registration?
That is the missing piece for a task-oriented catalogue."""
import struct, re, sys
sys.path.insert(0, r"T:\eu5-engine-atlas\tools")
from pe import PE
pe = PE(r"C:\SteamLibrary\steamapps\common\Europa Universalis V\binaries\eu5.exe")
d = pe.data
LEA = re.compile(rb"\x48\x8d[\x05\x0d\x15\x1d\x25\x2d\x35\x3d]")

def strings_in(fn_off, span=420):
    out = []
    for m in LEA.finditer(d[fn_off:fn_off+span]):
        ins = fn_off + m.start()
        disp = struct.unpack_from("<i", d, ins+3)[0]
        nxt = pe.off_to_rva(ins+7)
        if nxt is None: continue
        so = pe.va_to_off(pe.image_base + nxt + disp)
        if so is None: continue
        s = d[so:so+120].split(b"\0")[0]
        if re.fullmatch(rb"[A-Za-z_][A-Za-z0-9_:<>, ]{2,80}", s):
            out.append(s.decode())
    return out

# registration inits for three known GUI functions (found earlier)
for label, va in (("SetMapMode", 0x140290F00), ("IsActive", 0x14015D8C0),
                  ("GetMapColorLedger", 0x140022C30)):
    off = pe.va_to_off(va)
    print(f"--- {label} init @0x{va:X}")
    print("    strings referenced:", strings_in(off)[:6])
