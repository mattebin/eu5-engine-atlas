"""Defines the engine registers that no vanilla defines file ever sets."""
import re, sys, json, pathlib
sys.path.insert(0, r"T:\eu5-engine-atlas\tools")
from pe import PE
pe = PE(r"C:\SteamLibrary\steamapps\common\Europa Universalis V\binaries\eu5.exe")
d = pe.data

# Block names come from vanilla's own defines files, so the block/key split
# is exact. A naive regex mis-splits all-caps blocks: NAI + ADJUST_X becomes
# NA + IADJUST_X.
GAME0 = pathlib.Path(r"C:\SteamLibrary\steamapps\common\Europa Universalis V\game")
blocks = set()
for q in GAME0.rglob("*.txt"):
    if "defines" in str(q).lower():
        try:
            blocks.update(m.group(1).decode()
                          for m in re.finditer(rb"^(N[A-Za-z]+)\s*=\s*\{",
                                               q.read_bytes(), re.M))
        except Exception:
            pass
blocks = sorted(blocks, key=len, reverse=True)   # longest match wins
print(f"defines blocks known from vanilla: {len(blocks)}")

pat = re.compile(rb"CDefineRegistryHelper_(N[A-Za-z0-9_]{2,90})@")
eng = {}
for m in pat.finditer(d):
    full = m.group(1).decode()
    for b in blocks:
        if full.startswith(b) and len(full) > len(b):
            eng.setdefault(full[len(b):], b)
            break
print(f"defines registered in engine: {len(eng)}")

GAME = pathlib.Path(r"C:\SteamLibrary\steamapps\common\Europa Universalis V\game")
setk = set()
nf = 0
KEY = re.compile(rb"\b([A-Z][A-Z0-9_]{2,})\s*=")
for p in GAME.rglob("*.txt"):
    if "defines" not in str(p).lower():
        continue
    try:
        setk.update(m.group(1).decode() for m in KEY.finditer(p.read_bytes()))
        nf += 1
    except Exception:
        pass
print(f"vanilla defines files       : {nf}")
print(f"set by vanilla              : {len(set(eng) & setk)}")
hidden = sorted(set(eng) - setk)
print(f"NEVER set by vanilla        : {len(hidden)}\n")
for k in hidden[:30]:
    print(f"   {eng[k]}.{k}")
json.dump({k: eng[k] for k in hidden}, open("hidden_defines.json", "w"), indent=1)
