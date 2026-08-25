"""Collapse observed contexts into scope TYPES, and flag the limitation:
undocumented keywords have no vanilla usage, so their scope must be guessed
from the name instead of observed."""
import json, re, collections
ctx = json.load(open("scope_context.json", encoding="utf-8"))
undoc = json.load(open("undocumented.json", encoding="utf-8"))
undoc_all = set(undoc["effect"]) | set(undoc["trigger"])

def to_type(name):
    n = name.lower()
    if re.search(r"location|loc:", n): return "location"
    if re.search(r"province", n): return "province"
    if re.search(r"country|owner|controller|actor|recipient|c:", n): return "country"
    if re.search(r"character|ruler|heir|leader|artist", n): return "character"
    if re.search(r"unit|army|navy|regiment", n): return "unit"
    if re.search(r"market", n): return "market"
    if re.search(r"area", n): return "area"
    if re.search(r"region", n): return "region"
    if re.search(r"culture", n): return "culture"
    if re.search(r"religion|faith", n): return "religion"
    if re.search(r"pop\b", n): return "pop"
    if n == "(top level)": return "(file default)"
    return None

resolved = {}
for kw, pairs in ctx.items():
    tally = collections.Counter()
    for name, n in pairs:
        t = to_type(name)
        if t: tally[t] += n
    if tally:
        resolved[kw] = tally.most_common(3)

print(f"keywords with a resolved scope type: {len(resolved)}")
have = [k for k in undoc_all if k in resolved]
print(f"of the 168 UNDOCUMENTED keywords, observed in vanilla: {len(have)}")
print("  (expected to be ~0 - undocumented means vanilla never uses them,")
print("   so their scope cannot be OBSERVED, only guessed from the name)\n")

guess = {}
for kw in sorted(undoc_all):
    t = to_type(kw)
    if t and t != "(file default)":
        guess[kw] = t
print(f"undocumented keywords with a name-based scope hint: {len(guess)}")
for k, v in list(guess.items())[:14]:
    print(f"   {k:42} -> {v}")
json.dump({"observed": resolved, "name_hint": guess},
          open("scope_types.json", "w", encoding="utf-8"), indent=1)
