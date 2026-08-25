"""Batch-test GUI data functions through debug_log string interpolation.

Discovered in gui1: debug_log runs its string through the text system, so
[Func] resolves. Unknown functions log
    Could not find data system function 'X'
and - critically - the text system PRE-RESOLVES every string in the file,
so all functions are reported even when execution aborts. error.log alone
classifies them; no sentinels needed.

Two passes, because a bare [Func] only works for GLOBAL entry points:
  bare      -> [Func]              identifies global functions
  on player -> [GetPlayer.Func]    identifies country-type methods
"""
import json, pathlib, sys
RUN = pathlib.Path(r"C:\Users\Matte\Documents\Paradox Interactive"
                   r"\Europa Universalis V\run")
funcs = json.load(open("gui_undocumented.json", encoding="utf-8"))
import re
NOISE = re.compile(r"Anim|Material|Layout|Editor|Keyframe|Skeleton|Mesh|Import|"
                   r"Texture|Shader|Blend|Bone|Curve|Timeline|Gizmo|Viewport|Tool")
funcs = [f for f in funcs if not NOISE.search(f)]
CH = int(sys.argv[1]) if len(sys.argv) > 1 else 500
mode = sys.argv[2] if len(sys.argv) > 2 else "bare"
files = []
for i in range(0, len(funcs), CH):
    part = funcs[i:i+CH]
    n = i//CH + 1
    tag = "GB" if mode == "bare" else "GP"
    name = f"gui_{tag}{n}.txt"
    L = [f"# GUI {mode} batch {n}: {len(part)} functions.",
         "# Verdict comes from error.log only: 'Could not find data system",
         "# function' = unavailable. Silence = the engine resolved it.",
         f'debug_log = "{tag}{n}_START"',
         # controls, one known-good and one known-fake
         'debug_log = "CTRL_GOOD_[GetPlayer.GetName]"',
         'debug_log = "CTRL_FAKE_[GetDefinitelyNotARealFuncZZ]"']
    for f in part:
        expr = f"[{f}]" if mode == "bare" else f"[GetPlayer.{f}]"
        L.append(f'debug_log = "{expr}"')
    (RUN / name).write_text("\n".join(L) + "\n", encoding="utf-8", newline="\n")
    files.append(name)
json.dump({"files": files, "funcs": funcs, "mode": mode},
          open(f"gui_batch_{mode}.json", "w"), indent=1)
print(f"{len(funcs)} functions -> {len(files)} files ({mode} mode)")
for f in files: print(f"   run {f}")
