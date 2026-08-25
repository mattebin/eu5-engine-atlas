"""Which SCOPE does each effect/trigger belong in?

Vanilla script wraps effects in scope changes:
    location:x = { some_effect = ... }
    every_owned_location = { other_effect = ... }
So the enclosing scope-changing block tells us the context an effect runs in.
Walk vanilla files tracking the enclosing scope stack, and record which
scope each keyword appears under.
"""
import re, pathlib, collections, json
GAME = pathlib.Path(r"C:\SteamLibrary\steamapps\common\Europa Universalis V\game")
atlas = json.load(open("atlas.json", encoding="utf-8"))
kws = set(atlas["effect"]) | set(atlas["trigger"])

# scope-changing block openers seen in vanilla
SCOPE_OPEN = re.compile(
    r"^\s*((?:every|any|random|ordered)_[a-z_]+|[a-z_]+:[a-z_0-9]+|"
    r"owner|capital|controller|ruler|heir|province|location|country|"
    r"market|area|region|culture|religion|this|root|prev|from)\s*=\s*\{")
KEY = re.compile(r"^\s*([a-z_][a-z0-9_]{2,60})\s*=")

ctx = collections.defaultdict(collections.Counter)
nf = 0
for sub in ("in_game",):
    for p in (GAME / sub).rglob("*.txt"):
        try:
            lines = p.read_text(encoding="utf-8-sig", errors="ignore").splitlines()
        except Exception:
            continue
        nf += 1
        stack = []
        depth = 0
        for ln in lines:
            code = ln.split("#")[0]
            m = SCOPE_OPEN.match(code)
            if m:
                stack.append((depth, m.group(1)))
            k = KEY.match(code)
            if k and k.group(1) in kws:
                cur = stack[-1][1] if stack else "(top level)"
                ctx[k.group(1)][cur] += 1
            depth += code.count("{") - code.count("}")
            while stack and stack[-1][0] >= depth:
                stack.pop()
print(f"vanilla files scanned: {nf}")
print(f"keywords with observed scope context: {len(ctx)}\n")
out = {k: v.most_common(4) for k, v in ctx.items()}
json.dump(out, open("scope_context.json", "w", encoding="utf-8"), indent=1)
for k in ("add_gold", "set_variable", "add_core", "change_culture",
          "add_country_modifier", "construct_road"):
    if k in ctx:
        print(f"   {k:26} {ctx[k].most_common(3)}")
