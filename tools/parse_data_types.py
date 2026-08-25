"""Parse the engine's own dump_data_types output into data_types_dump.json.

The dump is the engine self-documenting its GUI data-function API: every
global and every Type.Member with definition kind (promote = returns a
navigable object, function = plain call), argument count, return type and
often a description.

PROVENANCE: the dump on disk is dated 2026-07-15 and is current to 1.3.11
(Matte, 2026-08-26), corroborated by a 99.9% name overlap with the 1.3.11
binary extraction (10,820 of 10,828; the 8 leftovers are extraction noise
plus one plausible real miss). Facts from it are tagged source "dump".
After any future patch: dump_data_types in console (-debug_mode), then
re-run this parser.
"""
import json
import pathlib
import re
import sys

DUMP_DIR = pathlib.Path(
    r"C:\Users\Matte\Documents\Paradox Interactive\Europa Universalis V"
    r"\logs\data_types")
OUT = pathlib.Path(r"T:\eu5-engine-atlas\data_types_dump.json")

NAME = re.compile(r"^([A-Za-z_][A-Za-z0-9_]*)(?:\.([A-Za-z_][A-Za-z0-9_]*))?"
                  r"\s*(\(\s*([^)]*)\s*\))?\s*$")


def parse_entry(block):
    lines = [ln.rstrip() for ln in block.splitlines() if ln.strip()]
    if not lines:
        return None
    m = NAME.match(lines[0])
    if not m:
        return None
    owner, member, has_args, args = m.group(1), m.group(2), m.group(3), m.group(4)
    entry = {
        "args": len([a for a in args.split(",") if a.strip()]) if has_args else 0,
    }
    for ln in lines[1:]:
        if ln.startswith("Description:"):
            entry["desc"] = ln[len("Description:"):].strip()
        elif ln.startswith("Definition type:"):
            entry["def_type"] = ln[len("Definition type:"):].strip()
        elif ln.startswith("Return type:"):
            entry["returns"] = ln[len("Return type:"):].strip()
    if member is None:
        return ("global", owner, entry)
    return ("member", owner, member, entry)


def main():
    if not DUMP_DIR.is_dir():
        sys.exit(f"dump dir not found: {DUMP_DIR}")
    files = sorted(DUMP_DIR.glob("*.txt"))
    if not files:
        sys.exit("no dump files found")

    globals_, types, type_names = {}, {}, set()
    n_entries = 0
    for f in files:
        text = f.read_text(encoding="utf-8", errors="replace")
        for block in text.split("-----------------------"):
            got = parse_entry(block)
            if not got:
                continue
            n_entries += 1
            if got[0] == "global":
                _, name, entry = got
                if entry.get("def_type") == "Type":
                    type_names.add(name)
                    continue
                # promote beats function when the same name appears as both
                prev = globals_.get(name)
                if prev is None or "promote" in entry.get("def_type", "").lower():
                    globals_[name] = entry
            else:
                _, owner, member, entry = got
                prev = types.setdefault(owner, {}).get(member)
                if prev is None or "promote" in entry.get("def_type", "").lower():
                    types[owner][member] = entry

    n_members = sum(len(v) for v in types.values())
    out = {
        "meta": {
            "source": "dump_data_types console command output",
            "dump_file_date": "2026-07-15",
            "game_version_caveat": ("pre-dates the 1.3.11 extraction/probes; "
                                    "regenerate on current patch to refresh"),
            "files": [f.name for f in files],
            "entries_parsed": n_entries,
        },
        "globals": globals_,
        "types": {k: types[k] for k in sorted(types)},
        "declared_types": sorted(type_names),
    }
    # asserts that CAN fail: known-real anchors must be present
    assert "GetPlayer" in globals_, "GetPlayer missing - parse is broken"
    assert "GetDefine" in globals_ or any(
        "GetDefine" in t for t in types), "GetDefine missing from dump"
    assert n_members > 10000, f"suspiciously few members: {n_members}"
    OUT.write_text(json.dumps(out, indent=1), encoding="utf-8")
    print(f"globals: {len(globals_)}  types-with-members: {len(types)}  "
          f"members: {n_members}  declared types: {len(type_names)}")
    print(f"wrote {OUT}")


if __name__ == "__main__":
    main()
