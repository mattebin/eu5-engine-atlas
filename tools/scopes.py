import struct, re, sys, json, pathlib
sys.path.insert(0, r"T:\eu5-engine-atlas\tools")
from pe import PE
pe = PE(r"C:\SteamLibrary\steamapps\common\Europa Universalis V\binaries\eu5.exe")
d = pe.data
text = next(s for s in pe.sections if s["name"] == ".text")
LO, HI = text["rawptr"], text["rawptr"] + text["rawsize"]
LEA = re.compile(rb"\x48\x8d[\x05\x0d\x15\x1d\x25\x2d\x35\x3d]")
SCOPE_REGISTRARS = {0x1429C9B40, 0x1429F1DE0, 0x144C0DE80}

def fn_start(o):
    while o > LO and d[o-1] != 0xCC:
        o -= 1
    return o

def kw(fo, span=300):
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

found = set()
for m in re.finditer(rb"\xe8", d[LO:HI]):
    off = LO + m.start()
    rel = struct.unpack_from("<i", d, off+1)[0]
    nxt = pe.off_to_rva(off+5)
    if nxt is None:
        continue
    if pe.image_base + nxt + rel in SCOPE_REGISTRARS:
        k = kw(fn_start(off))
        if k:
            found.add(k)

GAME = pathlib.Path(r"C:\SteamLibrary\steamapps\common\Europa Universalis V\game")
KEY = re.compile(rb"([a-z_][a-z0-9_]{2,63})\s*[=:]")
seen = set()
for sub in ("in_game", "main_menu", "loading_screen"):
    for p in (GAME / sub).rglob("*.txt"):
        try:
            seen.update(x.group(1).decode() for x in KEY.finditer(p.read_bytes()))
        except Exception:
            pass
undoc = sorted(found - seen)
print(f"scope links in engine : {len(found)}")
print(f"used by vanilla       : {len(found & seen)}")
print(f"NEVER used by vanilla : {len(undoc)}\n")
print(", ".join(undoc[:40]))
json.dump(sorted(found), open("scopes.json", "w", encoding="utf-8"), indent=1)
json.dump(undoc, open("scopes_undocumented.json", "w", encoding="utf-8"), indent=1)
