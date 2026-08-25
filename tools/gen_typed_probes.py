"""Test type-scoped GUI functions against the RIGHT receiver.

Receivers proven working from the console (recv.txt):
  capital/location, province, market, area, region, culture, religion, mapmode
Functions are routed by name: anything containing 'Market' is tested on the
market object, 'Province' on the province, and so on. Untyped names default
to the location receiver, the most common type.
"""
import json, pathlib, re
RUN = pathlib.Path(r"C:\Users\Matte\Documents\Paradox Interactive"
                   r"\Europa Universalis V\run")
bare = json.load(open("gui_bare_results.json", encoding="utf-8"))
methods = set(json.load(open("gui_player_methods.json", encoding="utf-8")))
todo = [f for f in bare["not_found"] if f not in methods]

RECV = [
 ("Market",   "GetPlayer.GetCapital.GetMarket"),
 ("Province", "GetPlayer.GetCapital.GetProvince"),
 ("Area",     "GetPlayer.GetCapital.GetArea"),
 ("Region",   "GetPlayer.GetCapital.GetRegion"),
 ("Culture",  "GetPlayer.GetCulture"),
 ("Religion", "GetPlayer.GetReligion"),
 ("MapMode",  "GetMapMode('raw_material')"),
]
def receiver(fn):
    for key, expr in RECV:
        if key.lower() in fn.lower():
            return expr
    return "GetPlayer.GetCapital"      # default: location

CH = 700
files = []
for i in range(0, len(todo), CH):
    part = todo[i:i+CH]
    n = i//CH + 1
    name = f"typed_TY{n}.txt"
    L = [f"# typed batch {n}: {len(part)} functions on inferred receivers",
         f'debug_log = "TY{n}_START"',
         'debug_log = "TCTRL_GOOD_[GetPlayer.GetCapital.GetName]"',
         'debug_log = "TCTRL_FAKE_[GetPlayer.GetCapital.NotARealMethodQQ]"']
    for f in part:
        L.append(f'debug_log = "[{receiver(f)}.{f}]"')
    (RUN / name).write_text("\n".join(L) + "\n", encoding="utf-8", newline="\n")
    files.append(name)
json.dump({"files": files, "funcs": todo,
           "recv": {f: receiver(f) for f in todo}},
          open("typed_batch.json", "w"), indent=1)
import collections
dist = collections.Counter(receiver(f).split(".")[-1] for f in todo)
print(f"{len(todo)} functions -> {len(files)} files")
print("receiver distribution:", dict(dist))
for f in files: print(f"   run {f}")
