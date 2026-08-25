"""Regenerate the FULL engine define registry into defines_all.json.

hidden_defines.py computed this in memory (2,841 block-matched defines) but
only persisted the 45 vanilla-never-sets subset. The catalogue needs every
define, plus which ones vanilla sets and with what raw value.

Static work only: reads eu5.exe (RTTI helper names) and the vanilla defines
files. No game launch involved.
"""
import json
import pathlib
import re
import sys

sys.path.insert(0, r"T:\eu5-engine-atlas\tools")
from pe import PE

EXE = r"C:\SteamLibrary\steamapps\common\Europa Universalis V\binaries\eu5.exe"
GAME = pathlib.Path(r"C:\SteamLibrary\steamapps\common\Europa Universalis V\game")
OUT = pathlib.Path(r"T:\eu5-engine-atlas\defines_all.json")

# --- blocks known from vanilla's own defines files (exact split anchors) ---
blocks = set()
defines_files = [q for q in GAME.rglob("*.txt") if "defines" in str(q).lower()]
for q in defines_files:
    try:
        # strip the UTF-8 BOM: it glues to a block declared on line 1
        # (00_defines.txt opens "<BOM>NGame = {" and NGame was silently
        # lost before this - which also broke the original 2,841 count)
        raw = q.read_bytes().removeprefix(b"\xef\xbb\xbf")
        blocks.update(m.group(1).decode()
                      for m in re.finditer(rb"^(N[A-Za-z]+)\s*=\s*\{",
                                           raw, re.M))
    except OSError:
        pass
blocks = sorted(blocks, key=len, reverse=True)  # longest match wins

# --- every registered define from RTTI helper names ---
pe = PE(EXE)
pat = re.compile(rb"CDefineRegistryHelper_(N[A-Za-z0-9_]{2,90})@")
eng = {}        # "BLOCK.KEY" -> {"block": ..., "key": ...}
unsplit = []    # full names no vanilla block prefix matches
for m in pat.finditer(pe.data):
    full = m.group(1).decode()
    for b in blocks:
        if full.startswith(b) and len(full) > len(b):
            eng.setdefault(f"{b}.{full[len(b):]}",
                           {"block": b, "key": full[len(b):]})
            break
    else:
        if full not in unsplit:
            unsplit.append(full)

# --- vanilla-set keys and raw values, per block, last file wins ---
BLOCK_OPEN = re.compile(r"^\s*(N[A-Za-z]+)\s*=\s*\{")
KEYVAL = re.compile(r"^\s*([A-Z][A-Z0-9_]{2,})\s*=\s*(.+?)\s*$")
vanilla = {}  # "BLOCK.KEY" -> {"value": raw, "file": name}
for q in sorted(defines_files, key=lambda p: p.name):
    try:
        text = q.read_text(encoding="utf-8-sig", errors="replace")
    except OSError:
        continue
    block, brace_key, brace_buf, brace_depth = None, None, [], 0
    pending_key = None  # KEY = with the value starting on a later line
    for raw_ln in text.splitlines():
        ln = raw_ln.split("#", 1)[0].rstrip()
        if not ln.strip():
            continue
        if pending_key is not None:
            val = ln.strip()
            if val.startswith("{"):
                if val.count("{") > val.count("}"):
                    brace_key, brace_buf = pending_key, [val]
                    brace_depth = val.count("{") - val.count("}")
                else:
                    vanilla[f"{block}.{pending_key}"] = {
                        "value": val, "file": q.name}
            else:
                vanilla[f"{block}.{pending_key}"] = {
                    "value": val, "file": q.name}
            pending_key = None
            continue
        if brace_key is not None:
            brace_buf.append(ln.strip())
            brace_depth += ln.count("{") - ln.count("}")
            if brace_depth <= 0:
                vanilla[f"{block}.{brace_key}"] = {
                    "value": " ".join(brace_buf), "file": q.name}
                brace_key = None
            continue
        mb = BLOCK_OPEN.match(ln)
        if mb:
            block = mb.group(1)
            continue
        if block is None:
            continue
        mk = KEYVAL.match(ln)
        if mk:
            key, val = mk.group(1), mk.group(2)
            if val.startswith("{") and val.count("{") > val.count("}"):
                brace_key, brace_buf = key, [val]
                brace_depth = val.count("{") - val.count("}")
            else:
                vanilla[f"{block}.{key}"] = {"value": val, "file": q.name}
            continue
        me = re.match(r"^\s*([A-Z][A-Z0-9_]{2,})\s*=\s*$", ln)
        if me:
            pending_key = me.group(1)

set_keys = {k.split(".", 1)[1] for k in vanilla}
hidden = sorted(k for k in eng if eng[k]["key"] not in set_keys)

# The remaining unsplit names live in blocks NO vanilla file declares -
# engine-only blocks. Their block/key split is heuristic (CamelCase words
# then an ALL_CAPS key) and flagged as such; hidden by construction.
CAMEL = re.compile(r"^(N(?:[A-Z][a-z0-9]+)+)([A-Z][A-Z0-9_]+)$")
engine_only = {}
still_unsplit = []
for full in unsplit:
    m = CAMEL.match(full)
    if m:
        engine_only[f"{m.group(1)}.{m.group(2)}"] = {
            "block": m.group(1), "key": m.group(2),
            "block_source": "inferred_camelcase_split"}
    else:
        still_unsplit.append(full)

out = {
    "meta": {
        "source": "eu5.exe RTTI (CDefineRegistryHelper_) + vanilla defines files",
        "exe": EXE,
        "defines_files_read": len(defines_files),
        "registered_block_matched": len(eng),
        "engine_only_block_defines": len(engine_only),
        "still_unsplit": len(still_unsplit),
        "vanilla_set_pairs": len(vanilla),
        "hidden_never_set": len(hidden),
    },
    "defines": {
        k: {
            **eng[k],
            "vanilla_set": eng[k]["key"] in set_keys,
            **({"vanilla_value": vanilla[k]["value"],
                "vanilla_file": vanilla[k]["file"]} if k in vanilla else {}),
        }
        for k in sorted(eng)
    },
    "engine_only_blocks": {k: engine_only[k] for k in sorted(engine_only)},
    "still_unsplit_rtti_names": sorted(still_unsplit),
    "hidden": hidden,
}

# asserts that CAN fail, anchored to known defines. Two corrections to the
# published "2,841" were found on 2026-08-26 and are encoded here:
#   1. it keyed on KEY name alone (9 keys live under 2-3 blocks), and
#   2. the UTF-8 BOM hid the NGame block (declared on line 1 of
#      00_defines.txt), silently dropping every NGame.* define.
assert "NGame" in blocks, "NGame block missing - BOM regression"
assert "NGame.HOUR_TICK" in eng, "HOUR_TICK missing from RTTI split"
assert eng["NGame.HOUR_TICK"] is not None
# 54, not the published 45: the BOM fix unmasked the NCamera, NMapEditor
# and NJominiIcons blocks, adding 9 hidden defines (all debug/editor
# plumbing). The original 45 are all still present.
assert len(hidden) == 54, f"hidden count {len(hidden)} != expected 54"
old45 = set(json.load(open(r"T:\eu5-engine-atlas\hidden_defines.json")))
assert old45 <= {eng[h]["key"] for h in hidden}, (
    "a previously published hidden define went missing")
assert "NGame.HOUR_TICK" in vanilla, "HOUR_TICK missing from vanilla parse"
assert vanilla["NGame.HOUR_TICK"]["value"] == "2", (
    f"HOUR_TICK read as {vanilla['NGame.HOUR_TICK']['value']!r}, expected '2'")
assert "NDiplomacy.DIPLOMATIC_RANGE" in eng and \
    not out["defines"]["NDiplomacy.DIPLOMATIC_RANGE"]["vanilla_set"], \
    "DIPLOMATIC_RANGE should be registered and never vanilla-set"

assert len(engine_only) + len(still_unsplit) == len(unsplit)
assert len(still_unsplit) <= 5, (
    f"camelcase split left {len(still_unsplit)} names: {still_unsplit}")

OUT.write_text(json.dumps(out, indent=1), encoding="utf-8")
print(f"block-matched: {len(eng)}  engine-only-block: {len(engine_only)}  "
      f"still unsplit: {len(still_unsplit)}")
print(f"vanilla-set pairs: {len(vanilla)}  hidden: {len(hidden)}")
print(f"wrote {OUT}")
