"""Composed keywords: prefix + base name, assembled at runtime so they never
appear as literal strings in the binary. Learn the shape from vanilla usage."""
import re, pathlib, collections, json
GAME = pathlib.Path(r"C:\SteamLibrary\steamapps\common\Europa Universalis V\game")
PREFIXES = ("every_", "any_", "random_", "ordered_")
pat = re.compile(rb"\b(every|any|random|ordered)_([a-z][a-z0-9_]{2,50})\s*=")
used = collections.Counter()
for sub in ("in_game", "main_menu"):
    for p in (GAME / sub).rglob("*.txt"):
        try:
            for m in pat.finditer(p.read_bytes()):
                used[(m.group(1).decode(), m.group(2).decode())] += 1
        except Exception:
            pass
bases = collections.Counter()
for (pre, base), n in used.items():
    bases[base] += n
print(f"distinct composed keywords used by vanilla: {len(used)}")
print(f"distinct BASE names: {len(bases)}\n")
print("top base names:")
for b, n in bases.most_common(18):
    pres = sorted(p for (p, bb) in used if bb == b)
    print(f"   {b:34} {n:5}  prefixes: {','.join(pres)}")
json.dump(sorted(bases), open("composed_bases_vanilla.json", "w"), indent=1)
