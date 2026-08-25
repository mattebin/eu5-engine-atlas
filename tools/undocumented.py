"""Which engine keywords does vanilla script never demonstrate?"""
import json, re, pathlib
GAME = pathlib.Path(r"C:\SteamLibrary\steamapps\common\Europa Universalis V\game")
atlas = json.load(open("atlas.json", encoding="utf-8"))

KEY = re.compile(rb"([a-z_][a-z0-9_]{2,63})\s*=")
seen = set()
nfiles = 0
for sub in ("in_game", "main_menu", "loading_screen"):
    for p in (GAME / sub).rglob("*.txt"):
        try:
            seen.update(m.group(1).decode() for m in KEY.finditer(p.read_bytes()))
            nfiles += 1
        except Exception:
            pass
print(f"vanilla script files scanned: {nfiles}\n")

report = {}
for kind, kws in atlas.items():
    unused = sorted(set(kws) - seen)
    report[kind] = unused
    print(f"{kind:8}: {len(kws):5} in engine | {len(kws)-len(unused):5} used by vanilla "
          f"| {len(unused):5} NEVER used")
json.dump(report, open("undocumented.json", "w", encoding="utf-8"), indent=1)

print("\n--- sample undocumented EFFECTS ---")
for k in report["effect"][:22]:
    print("   ", k)
print("\n--- sample undocumented TRIGGERS ---")
for k in report["trigger"][:12]:
    print("   ", k)
