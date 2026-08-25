"""Holdout test: how accurate is adjacency-based type inference?
Hide a known function's type, infer it from neighbours, compare."""
import json, bisect, random, collections, sys
sys.path.insert(0, r"T:\eu5-engine-atlas\tools")
import struct, re
from pe import PE
pe = PE(r"C:\SteamLibrary\steamapps\common\Europa Universalis V\binaries\eu5.exe")
d = pe.data
text = next(s for s in pe.sections if s["name"] == ".text")
LO, HI = text["rawptr"], text["rawptr"] + text["rawsize"]
LEA = re.compile(rb"\x48\x8d[\x05\x0d\x15\x1d\x25\x2d\x35\x3d]")
CAMEL = re.compile(rb"[A-Z][A-Za-z0-9_]{2,60}")
GUI_REG = 0x1406B2C40
def fn_start(o):
    while o > LO and d[o-1] != 0xCC: o -= 1
    return o
def camel_kw(fo, span=340):
    for m in LEA.finditer(d[fo:fo+span]):
        ins = fo + m.start(); disp = struct.unpack_from("<i", d, ins+3)[0]
        nxt = pe.off_to_rva(ins+7)
        if nxt is None: continue
        so = pe.va_to_off(pe.image_base + nxt + disp)
        if so is None: continue
        s = d[so:so+96].split(b"\0")[0]
        if CAMEL.fullmatch(s): return s.decode()
    return None
regs = {}
for m in re.finditer(rb"\xe8", d[LO:HI]):
    off = LO + m.start(); rel = struct.unpack_from("<i", d, off+1)[0]
    nxt = pe.off_to_rva(off+5)
    if nxt is None: continue
    if pe.image_base + nxt + rel == GUI_REG:
        fs = fn_start(off); k = camel_kw(fs)
        if k: regs.setdefault(fs, k)
seq = [regs[a] for a in sorted(regs)]
known = json.load(open("gui_type_methods.json", encoding="utf-8"))
owner = {}
for t, ms in known.items():
    for meth in ms: owner.setdefault(meth, set()).add(t)
truth = {i: next(iter(owner[f])) for i, f in enumerate(seq)
         if f in owner and len(owner[f]) == 1}
random.seed(7)
holdout = set(random.sample(sorted(truth), min(600, len(truth))))
anchors = {i: t for i, t in truth.items() if i not in holdout}
idx = sorted(anchors)
hit = miss = skip = 0
for i in sorted(holdout):
    j = bisect.bisect_left(idx, i)
    cands = [idx[k] for k in (j-1, j) if 0 <= k < len(idx)]
    if not cands: skip += 1; continue
    near = min(cands, key=lambda a: abs(a - i))
    if abs(near - i) > 6: skip += 1; continue
    if anchors[near] == truth[i]: hit += 1
    else: miss += 1
tot = hit + miss
print(f"holdout functions      : {len(holdout)}")
print(f"predicted (within 6)   : {tot}   skipped (too far): {skip}")
print(f"CORRECT                : {hit}")
print(f"wrong                  : {miss}")
print(f"\nadjacency accuracy     : {hit/tot*100:.1f}%" if tot else "n/a")
