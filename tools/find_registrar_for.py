"""Given an anchor keyword, locate its registration initializer and report
which functions it calls. Shared callees across anchors of the same kind =
that kind's registrar."""
import struct, re, sys
sys.path.insert(0, r"T:\eu5-engine-atlas\tools")
from pe import PE
pe = PE(r"C:\SteamLibrary\steamapps\common\Europa Universalis V\binaries\eu5.exe")
d = pe.data
text = next(s for s in pe.sections if s["name"] == ".text")
LO, HI = text["rawptr"], text["rawptr"] + text["rawsize"]
LEA = re.compile(rb"\x48\x8d[\x05\x0d\x15\x1d\x25\x2d\x35\x3d]")
INTERN = {0x14376B0D0, 0x14376A780, 0x14371EA90}

def refs_to(s: bytes):
    """file offsets of LEA instructions pointing at this exact C string"""
    out = []
    pos = 0
    while True:
        i = d.find(s + b"\0", pos)
        if i < 0:
            break
        pos = i + 1
        rva = pe.off_to_rva(i)
        if rva is None:
            continue
        va = pe.image_base + rva
        for m in LEA.finditer(d[LO:HI]):
            ins = LO + m.start()
            disp = struct.unpack_from("<i", d, ins + 3)[0]
            nxt = pe.off_to_rva(ins + 7)
            if nxt is not None and pe.image_base + nxt + disp == va:
                out.append(ins)
    return out

def fn_start(o):
    while o > LO and d[o-1] != 0xCC:
        o -= 1
    return o

def callees(fo, span=320):
    out = []
    for k in range(fo, min(fo + span, HI - 5)):
        if d[k] == 0xE8:
            rel = struct.unpack_from("<i", d, k+1)[0]
            nxt = pe.off_to_rva(k+5)
            if nxt:
                t = pe.image_base + nxt + rel
                if t not in INTERN:
                    out.append(t)
    return out

for anchor in sys.argv[1:]:
    hits = refs_to(anchor.encode())
    print(f"\n=== {anchor} : {len(hits)} code reference(s)")
    for h in hits[:3]:
        fo = fn_start(h)
        cs = callees(fo)
        print(f"   init@0x{pe.image_base + pe.off_to_rva(fo):X} calls "
              f"{[hex(c) for c in cs[:7]]}")
