"""Generate batch probe files for every undocumented keyword.

Verdict logic (proven in probes 1-9): a keyword the engine does not know
reports 'Unknown effect'/'Unknown trigger'. A REAL keyword given wrong
arguments reports a SEMANTIC error instead ('Expected opening bracket',
'Failed to read X', type complaints). So bare-form tests classify
real-vs-fake WITHOUT knowing correct syntax.

Chunked because a genuine parse error kills an entire file silently. Each
chunk carries its own sabotage line so a dead chunk is detectable, and each
keyword gets a trailing sentinel so we can see how far a chunk got.
"""
import json, pathlib, sys

RUN = pathlib.Path(r"C:\Users\Matte\Documents\Paradox Interactive"
                   r"\Europa Universalis V\run")
undoc = json.load(open("undocumented.json", encoding="utf-8"))
CHUNK = int(sys.argv[1]) if len(sys.argv) > 1 else 18

def emit(kind, keywords, tag):
    files = []
    for i in range(0, len(keywords), CHUNK):
        part = keywords[i:i + CHUNK]
        n = i // CHUNK + 1
        name = f"batch_{tag}{n}.txt"
        L = [f"# auto-generated: {kind} batch {n} ({len(part)} keywords)",
             f"zzz_batch_{tag}{n}_sabotage_not_real = yes",
             f'debug_log = "B_{tag}{n}_START"']
        for kw in part:
            if kind == "effect":
                L.append(f"{kw} = yes")
            else:
                L.append(f"if = {{ limit = {{ {kw} = yes }} "
                         f'debug_log = "B_T_{kw}" }}')
            L.append(f'debug_log = "B_AFTER_{kw}"')
        L.append(f'debug_log = "B_{tag}{n}_END"')
        (RUN / name).write_text("\n".join(L) + "\n", encoding="utf-8",
                                newline="\n")
        files.append(name)
    return files

eff = emit("effect", undoc["effect"], "E")
trg = emit("trigger", undoc["trigger"], "T")
print(f"effects : {len(undoc['effect'])} keywords -> {len(eff)} files")
print(f"triggers: {len(undoc['trigger'])} keywords -> {len(trg)} files")
print("\nrun these in the console, in order:")
for f in eff + trg:
    print(f"   run {f}")
json.dump({"effect_files": eff, "trigger_files": trg},
          open("batch_files.json", "w"), indent=1)
