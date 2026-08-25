"""What does each big registrar register? Sample its keywords."""
import struct, re, sys, collections
sys.path.insert(0, r"T:\eu5-engine-atlas\tools")
from pe import PE
pe = PE(r"C:\SteamLibrary\steamapps\common\Europa Universalis V\binaries\eu5.exe")
d = pe.data
text = next(s for s in pe.sections if s["name"] == ".text")
LO, HI = text["rawptr"], text["rawptr"] + text["rawsize"]
LEA = re.compile(rb"\x48\x8d[\x05\x0d\x15\x1d\x25\x2d\x35\x3d]")

CANDIDATES = [0x1429C9B40, 0x1429F1DE0, 0x144C0DE80, 0x140A01F70,
              0x14074DE00, 0x1430AAD50, 0x145B09350]

def fn_start(off):
    while off > LO and d[off-1] != 0xCC:
        off -= 1
    return off

def keyword_in(fo, span=300):
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
        if re.fullmatch(rb"[a-z][a-z0-9_]{2,63}", s):
            return s.decode()
    return None

buckets = collections.defaultdict(set)
for m in re.finditer(rb"\xe8", d[LO:HI]):
    off = LO + m.start()
    rel = struct.unpack_from("<i", d, off+1)[0]
    nxt = pe.off_to_rva(off+5)
    if nxt is None:
        continue
    tgt = pe.image_base + nxt + rel
    if tgt in CANDIDATES:
        kw = keyword_in(fn_start(off))
        if kw:
            buckets[tgt].add(kw)

for va in CANDIDATES:
    kws = sorted(buckets[va])
    print(f"\n0x{va:X}  ({len(kws)} keywords)")
    print("   ", ", ".join(kws[:14]))
