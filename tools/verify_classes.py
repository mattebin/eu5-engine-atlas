"""Code-level verification: link each keyword to the RTTI class implementing it.
Matching is done on a normalised form (lowercase, underscores stripped), so the
acronym problem that breaks CamelCase->snake conversion disappears."""
import re, json, sys, pathlib
sys.path.insert(0, r"T:\eu5-engine-atlas\tools")
from pe import PE

pe = PE(r"C:\SteamLibrary\steamapps\common\Europa Universalis V\binaries\eu5.exe")
d = pe.data
names = {n.decode() for n in re.findall(rb"\.\?AV([A-Za-z_][A-Za-z0-9_]{2,80})@", d)}

def norm(s):
    return s.replace("_", "").lower()

cls_by_norm = {}
for n in names:
    for suffix in ("Effect", "Trigger"):
        if n.startswith("C") and n.endswith(suffix):
            cls_by_norm.setdefault((norm(n[1:-len(suffix)]), suffix.lower()), []).append(n)

undoc = json.load(open("undocumented.json", encoding="utf-8"))
out = {}
for kind, kws in undoc.items():
    rows = []
    for kw in kws:
        cls = cls_by_norm.get((norm(kw), kind), [])
        present = d.count(kw.encode() + b"\0") > 0
        rows.append({"keyword": kw, "string_in_exe": present,
                     "impl_class": cls[0] if cls else None})
    out[kind] = rows
    have = sum(1 for r in rows if r["impl_class"])
    print(f"{kind:8}: {len(rows):4} undocumented | {have:4} matched to an RTTI class")

# negative control
fake = cls_by_norm.get((norm("totally_fake_effect_xyz"), "effect"), [])
print(f"\ncontrol (fake keyword) matched a class: {bool(fake)}  <- must be False")
json.dump(out, open("verified.json", "w", encoding="utf-8"), indent=1)
