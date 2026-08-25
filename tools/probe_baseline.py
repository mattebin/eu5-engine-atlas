"""Record log sizes BEFORE the probe, so the reader only sees new lines."""
import json, pathlib
LOGS = pathlib.Path(r"C:\Users\Matte\Documents\Paradox Interactive\Europa Universalis V\logs")
base = {}
for name in ("error.log", "game.log"):
    p = LOGS / name
    base[name] = p.stat().st_size if p.exists() else 0
json.dump(base, open("probe_baseline.json", "w"), indent=1)
for k, v in base.items():
    print(f"{k:12} baseline {v} bytes")
