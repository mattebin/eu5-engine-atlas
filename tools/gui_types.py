"""Learn Type.Method pairs from vanilla .gui usage. In Jomini GUI you write
[MapMode.IsActive] where MapMode is the datacontext TYPE, so vanilla files
reveal the type system directly."""
import re, pathlib, collections, json
GAME = pathlib.Path(r"C:\SteamLibrary\steamapps\common\Europa Universalis V\game")
pat = re.compile(rb"\[([A-Z][A-Za-z0-9_]{2,40})\.([A-Z][A-Za-z0-9_]{2,60})")
pairs = collections.Counter()
nf = 0
for p in GAME.rglob("*.gui"):
    try:
        b = p.read_bytes(); nf += 1
        for m in pat.finditer(b):
            pairs[(m.group(1).decode(), m.group(2).decode())] += 1
    except Exception:
        pass
types = collections.defaultdict(set)
for (t, meth), n in pairs.items():
    types[t].add(meth)
print(f"vanilla .gui files: {nf}")
print(f"distinct types seen: {len(types)}")
print(f"distinct Type.Method pairs: {len(pairs)}\n")
print("richest types:")
for t, ms in sorted(types.items(), key=lambda kv: -len(kv[1]))[:16]:
    print(f"   {t:28} {len(ms):4} methods   e.g. {sorted(ms)[:3]}")
json.dump({t: sorted(ms) for t, ms in types.items()},
          open("gui_type_methods.json", "w", encoding="utf-8"), indent=1)
