"""Classify every batched keyword from the logs."""
import json, pathlib, re
LOGS = pathlib.Path(r"C:\Users\Matte\Documents\Paradox Interactive"
                    r"\Europa Universalis V\logs")
base = json.load(open("probe_baseline.json", encoding="utf-8"))
def tail(n):
    p = LOGS / n
    if not p.exists(): return ""
    s = p.stat().st_size
    with open(p, "rb") as f:
        f.seek(0 if s < base.get(n, 0) else base.get(n, 0))
        return f.read().decode("utf-8", errors="replace")
err, dbg = tail("error.log"), tail("debug.log")
undoc = json.load(open("undocumented.json", encoding="utf-8"))
files = json.load(open("batch_files.json", encoding="utf-8"))

unknown = set(re.findall(r"Unknown (?:effect|trigger) ([a-z_][a-z0-9_]*)", err))
print("chunk health (a dead chunk means its keywords are UNTESTED):")
dead = []
for f in files["effect_files"] + files["trigger_files"]:
    tag = f.replace("batch_", "").replace(".txt", "")
    armed = f"zzz_batch_{tag}_sabotage_not_real" in unknown
    ran = f"B_{tag}_START" in dbg
    done = f"B_{tag}_END" in dbg
    state = "ok" if (ran and done) else ("PARTIAL" if ran else "DEAD - not run or aborted")
    if not (ran and done): dead.append(f)
    print(f"   {f:16} armed={armed}  {state}")

results = {}
for kind in ("effect", "trigger"):
    real, fake, untested = [], [], []
    for kw in undoc[kind]:
        if f"B_AFTER_{kw}" in dbg or f"B_T_{kw}" in dbg:
            real.append(kw) if kw not in unknown else fake.append(kw)
        elif kw in unknown:
            fake.append(kw)
        else:
            untested.append(kw)
    results[kind] = {"real": real, "unknown": fake, "untested": untested}
    print(f"\n{kind.upper()}S: {len(real)} REAL | {len(fake)} unknown | "
          f"{len(untested)} untested")
    if fake:
        print(f"   engine does not know: {', '.join(sorted(fake)[:12])}")
json.dump(results, open("batch_results.json", "w", encoding="utf-8"), indent=1)
if dead:
    print(f"\nre-run or split these files: {dead}")
