"""Infer the owning TYPE of every GUI function.

Two sources combined:
  1. vanilla .gui gives 7197 known Type.Method pairs (ground truth anchors)
  2. registration ADJACENCY - functions registered next to each other belong
     to the same type (SetMapMode sits beside IsSet, IsActive beside
     IsToggleAction)

Walk registrations in address order; each function inherits the type of the
nearest anchor in its contiguous run.
"""
import struct, re, sys, json, collections
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
    while o > LO and d[o-1] != 0xCC: o -= 1
    return o

def camel_kw(fo, span=340):
    for m in LEA.finditer(d[fo:fo+span]):
        ins = fo + m.start()
        disp = struct.unpack_from("<i", d, ins+3)[0]
        nxt = pe.off_to_rva(ins+7)
        if nxt is None: continue
        so = pe.va_to_off(pe.image_base + nxt + disp)
        if so is None: continue
        s = d[so:so+96].split(b"\0")[0]
        if CAMEL.fullmatch(s): return s.decode()
    return None

# collect (address, function) for every GUI registration
regs = {}
for m in re.finditer(rb"\xe8", d[LO:HI]):
    off = LO + m.start()
    rel = struct.unpack_from("<i", d, off+1)[0]
    nxt = pe.off_to_rva(off+5)
    if nxt is None: continue
    if pe.image_base + nxt + rel == GUI_REG:
        fs = fn_start(off)
        k = camel_kw(fs)
        if k: regs.setdefault(fs, k)
seq = [regs[a] for a in sorted(regs)]
print(f"registrations in address order: {len(seq)}")

known = json.load(open("gui_type_methods.json", encoding="utf-8"))
owner = {}
for t, ms in known.items():
    for meth in ms:
        owner.setdefault(meth, set()).add(t)
anchors = {i: next(iter(owner[f])) for i, f in enumerate(seq)
           if f in owner and len(owner[f]) == 1}
print(f"unambiguous anchors in the sequence: {len(anchors)}")

# each function takes the type of the nearest anchor
idx = sorted(anchors)
inferred = {}
import bisect
for i, f in enumerate(seq):
    if f in owner and len(owner[f]) == 1:
        inferred[f] = (next(iter(owner[f])), "vanilla")
        continue
    j = bisect.bisect_left(idx, i)
    cands = [idx[k] for k in (j-1, j) if 0 <= k < len(idx)]
    if not cands: continue
    near = min(cands, key=lambda a: abs(a - i))
    if abs(near - i) <= 6:      # only trust close neighbours
        inferred.setdefault(f, (anchors[near], "adjacency"))
byhow = collections.Counter(v[1] for v in inferred.values())
print(f"typed functions: {len(inferred)}  {dict(byhow)}")
top = collections.Counter(v[0] for v in inferred.values())
print("\nlargest inferred type groups:")
for t, n in top.most_common(12):
    print(f"   {t:30} {n}")
json.dump({k: {"type": v[0], "how": v[1]} for k, v in inferred.items()},
          open("gui_function_types.json", "w", encoding="utf-8"), indent=1)
