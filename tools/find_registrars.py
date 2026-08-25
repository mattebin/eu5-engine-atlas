"""Find ALL registrars: functions called by many tiny 'intern one keyword'
initializers. A keyword-init is a short function whose only string operand is
a snake_case identifier. Group those inits by the non-intern function they call."""
import struct, re, sys, collections
sys.path.insert(0, r"T:\eu5-engine-atlas\tools")
from pe import PE
pe = PE(r"C:\SteamLibrary\steamapps\common\Europa Universalis V\binaries\eu5.exe")
d = pe.data
text = next(s for s in pe.sections if s["name"] == ".text")
LO, HI = text["rawptr"], text["rawptr"] + text["rawsize"]
LEA = re.compile(rb"\x48\x8d[\x05\x0d\x15\x1d\x25\x2d\x35\x3d]")

# the two known interning helpers (called by nearly every init) - ignore them
INTERN = {0x14376B0D0, 0x14376A780}

def fn_bounds(off):
    lo = off
    while lo > LO and d[lo-1] != 0xCC:
        lo -= 1
    hi = off
    while hi < HI and d[hi] != 0xCC:
        hi += 1
    return lo, hi

def keyword_of(lo, hi):
    for m in LEA.finditer(d[lo:hi]):
        ins = lo + m.start()
        disp = struct.unpack_from("<i", d, ins + 3)[0]
        nxt = pe.off_to_rva(ins + 7)
        if nxt is None:
            continue
        so = pe.va_to_off(pe.image_base + nxt + disp)
        if so is None:
            continue
        s = d[so:so+96].split(b"\0")[0]
        if re.fullmatch(rb"[a-z][a-z0-9_]{2,63}", s):
            return s.decode()
    return None

def calls(lo, hi):
    out = []
    k = lo
    while k < hi - 4:
        if d[k] == 0xE8:
            rel = struct.unpack_from("<i", d, k+1)[0]
            nxt = pe.off_to_rva(k+5)
            if nxt:
                out.append(pe.image_base + nxt + rel)
        k += 1
    return out

# start from every keyword string ref site, dedup by function
seen_fn = {}
for m in re.finditer(rb"\x48\x8d[\x05\x0d\x15\x1d\x25\x2d\x35\x3d]", d[LO:HI]):
    ins = LO + m.start()
    disp = struct.unpack_from("<i", d, ins+3)[0]
    nxt = pe.off_to_rva(ins+7)
    if nxt is None:
        continue
    so = pe.va_to_off(pe.image_base + nxt + disp)
    if so is None:
        continue
    s = d[so:so+96].split(b"\0")[0]
    if not re.fullmatch(rb"[a-z][a-z0-9_]{2,63}", s):
        continue
    lo, hi = fn_bounds(ins)
    if hi - lo > 400:            # keyword inits are small
        continue
    seen_fn[(lo, hi)] = s.decode()

reg = collections.Counter()
examples = collections.defaultdict(list)
for (lo, hi), kw in seen_fn.items():
    for c in calls(lo, hi):
        if c in INTERN:
            continue
        o = pe.va_to_off(c)
        if o is None or pe.section_of_off(o) != ".text":
            continue
        reg[c] += 1
        if len(examples[c]) < 4:
            examples[c].append(kw)

print(f"init functions considered: {len(seen_fn)}\n")
print("candidate registrars (called by many keyword inits):")
for va, n in reg.most_common(12):
    print(f"  0x{va:X}: {n:5} inits   e.g. {examples[va]}")
