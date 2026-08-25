"""List-type registry: each type gets template-generated init functions,
clustered in .text. Walk the cluster and read each type's keyword."""
import struct, re, sys, json, pathlib, collections
sys.path.insert(0, r"T:\eu5-engine-atlas\tools")
from pe import PE
pe = PE(r"C:\SteamLibrary\steamapps\common\Europa Universalis V\binaries\eu5.exe")
d = pe.data
text = next(s for s in pe.sections if s["name"] == ".text")
LO, HI = text["rawptr"], text["rawptr"] + text["rawsize"]
LEA = re.compile(rb"\x48\x8d[\x05\x0d\x15\x1d\x25\x2d\x35\x3d]")

def kw_of(fo, span=200):
    for m in LEA.finditer(d[fo:fo+span]):
        ins = fo + m.start()
        disp = struct.unpack_from("<i", d, ins+3)[0]
        nxt = pe.off_to_rva(ins+7)
        if nxt is None: continue
        so = pe.va_to_off(pe.image_base + nxt + disp)
        if so is None: continue
        s = d[so:so+96].split(b"\0")[0]
        if re.fullmatch(rb"[a-z][a-z0-9_]{2,60}", s):
            return s.decode()
    return None

# cluster around the known list-type inits
lo_va, hi_va = 0x140600000, 0x140680000
lo_off, hi_off = pe.va_to_off(lo_va), pe.va_to_off(hi_va)
found = {}
off = lo_off
while off < hi_off:
    if d[off] == 0xCC:
        off += 1
        continue
    fs = off
    while off < hi_off and d[off] != 0xCC:
        off += 1
    # A list type's init calls the template helpers in the 0x144D0____ band
    # (neighbor_country, owned_location and cabinet_character all do).
    # Effect inits call different registrars, so this separates them.
    helper = False
    k2 = fs
    while k2 < off - 4:
        if d[k2] == 0xE8:
            rel = struct.unpack_from("<i", d, k2 + 1)[0]
            nx = pe.off_to_rva(k2 + 5)
            if nx is not None:
                t = pe.image_base + nx + rel
                if 0x144D00000 <= t < 0x144D60000:
                    helper = True
                    break
        k2 += 1
    if helper:
        k = kw_of(fs)
        if k:
            found.setdefault(k, pe.image_base + pe.off_to_rva(fs))
print(f"keywords in the list-type cluster: {len(found)}")

vanilla = set(json.load(open("composed_bases_vanilla.json", encoding="utf-8")))
hit = set(found) & vanilla
print(f"of vanilla's 253 bases, recovered: {len(hit)}")
undoc = sorted(set(found) - vanilla)
print(f"in cluster but NEVER iterated by vanilla: {len(undoc)}\n")
print(", ".join(undoc[:45]))
json.dump({"all": sorted(found), "undocumented": undoc},
          open("list_types.json", "w", encoding="utf-8"), indent=1)
