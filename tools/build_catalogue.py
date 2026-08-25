"""Build catalogue.json - the single queryable index behind the workbench.

Merges every registry and every piece of evidence in this repo into one
file: binary extraction, vanilla usage, in-game probe results, the engine's
own data_types dump, scope requirements, GUI typing, define tiers and the
curated syntax established in VERIFIED.md.

Confidence model (meta.statuses documents it in the output):

  status             usability  meaning
  confirmed_working  100  positive in-game evidence: read-back, sentinel,
                          live data, or resolved with real data
  vanilla            90   vanilla's own files use it, so it works as used
  verified_real      80   engine provably knows it (semantic error, not
                          "Unknown X"); behaviour/arguments unproven
  accepted           60   engine accepted it in a probe with no live data,
                          or a define proven loaded but not proven live
  registered         25   extracted from the binary or the dump only
  inferred           20   existence or attribute known only by inference
  dead               0    positive evidence it does NOTHING (do not use)

Attribute-level confidence is separate from item status: e.g. a GUI
function can be confirmed_working while its type label is an 80%-accurate
adjacency guess. Every typed attribute carries its source.

Sources ranked: probe (1.3.11, VERIFIED.md) > vanilla files (1.3.11) >
data_types dump (dated 2026-07-15, confirmed current to 1.3.11; 99.9%
name overlap with the binary extraction) > binary extraction (1.3.11) >
adjacency/name inference.
"""
import argparse
import datetime
import json
import pathlib
import re
import sys

ROOT = pathlib.Path(r"T:\eu5-engine-atlas")
OUT = ROOT / "catalogue.json"

USABILITY = {"confirmed_working": 100, "vanilla": 90, "verified_real": 80,
             "accepted": 60, "registered": 25, "inferred": 20, "dead": 0}

V = "VERIFIED.md"  # evidence shorthand


def J(name):
    return json.loads((ROOT / name).read_text(encoding="utf-8"))


# ---------------------------------------------------------------------------
# Curated constants. Every entry is probe evidence recorded only in prose in
# VERIFIED.md, encoded here with its evidence pointer. Update BOTH places.
# ---------------------------------------------------------------------------

SYNTAX = {
    "effect:set_global_variable":
        ("set_global_variable = { name = X value = 5 }", f"{V}: Probe 3"),
    "effect:change_global_variable":
        ("change_global_variable = { name = X add = 3 }", f"{V}: Probe 3"),
    "effect:clamp_global_variable":
        ("clamp_global_variable = { name = X max = 6 }", f"{V}: Probe 3"),
    "effect:round_global_variable":
        ("round_global_variable = { name = X nearest = 1 }", f"{V}: Probe 3"),
    "effect:add_to_global_variable_list":
        ("add_to_global_variable_list = { name = X target = c:FRA }  "
         "(lists hold SCOPES, not values)", f"{V}: Probe 3"),
    "trigger:has_global_variable_list":
        ("has_global_variable_list = X", f"{V}: Probe 3"),
    "trigger:is_target_in_global_variable_list":
        ("is_target_in_global_variable_list = { name = X target = c:FRA }",
         f"{V}: Probe 3"),
    "effect:add_to_global_variable_map":
        ("add_to_global_variable_map = { name = X key = c:FRA value = c:ENG }"
         "  (maps are keyed by SCOPES)", f"{V}: Probes 3-6"),
    "trigger:has_global_variable_map":
        ("has_global_variable_map = X", f"{V}: Probes 4-6"),
    "trigger:has_local_variable_map":
        ("has_local_variable_map = X", f"{V}: Probes 4-6"),
    "trigger:global_variable_map_size":
        ("global_variable_map_size = { name = X value = 1 }", f"{V}: Probes 4-6"),
    "trigger:local_variable_map_size":
        ("local_variable_map_size = { name = X value = 1 }", f"{V}: Probes 4-6"),
    "effect:sort_global_variable_list":
        ("sort_global_variable_list = { name = X order = var:my_key }  "
         "(order = script value evaluated per element; DESCENDING; "
         "named script values from main_menu kill the file silently)",
         f"{V}: Probes 7-8"),
    "effect:debug_log":
        ('debug_log = "text [DataFunc] interpolates"  (writes debug.log '
         "with file+line; runs GUI data functions)", f"{V}: Probe 1"),
    "effect:post_audio_event":
        ("post_audio_event = { ... }  (block form required; exact keys "
         "unknown)", f"{V}: Probe 1"),
}

# proven live by read-back / sentinel / live data
CONFIRMED_EFFECTS = {
    "set_global_variable", "change_global_variable", "clamp_global_variable",
    "round_global_variable", "add_to_global_variable_list",
    "add_to_global_variable_map", "add_to_local_variable_map",
    "sort_global_variable_list", "debug_log",
}
CONFIRMED_TRIGGERS = {
    "has_global_variable", "has_global_variable_list",
    "is_target_in_global_variable_list", "has_global_variable_map",
    "has_local_variable_map", "global_variable_map_size",
    "local_variable_map_size", "has_multiple_players", "has_game_started",
    "nand",
}

# console probes rejected every key/value form (9 forms, both scope tiers),
# but vanilla DOES use these in script files - so they are not dead, the
# console context or the tried forms were the problem (static find
# 2026-08-26: in_game/common/country_interactions/hre.txt uses
# `is_key_in_global_variable_map = { name = ... target = root }`).
MAP_LOOKUP_NOTE = (
    "Console probes (1.3.11) rejected every key form tried (9 forms). "
    "Vanilla uses this in real script with `target = <scope>` "
    "(hre.txt), and reads map VALUES via the quoted accessor "
    '"global_variable_map(name|key)" and the data function '
    "GetVariableFromGlobalVariableMap. Trust the vanilla form.")
MAP_LOOKUP_TRIGGERS = {
    "is_key_in_global_variable_map", "is_key_in_local_variable_map",
    "is_value_in_global_variable_map", "is_value_in_local_variable_map",
}

# Keywords PROVEN real that the binary registrar walk MISSED (found
# 2026-08-26 when task-map validation rejected them). The walk has false
# negatives inside keyword families - set_variable missing while its
# local/global twins are present, etc. Cause unknown, on the backlog.
# CONSEQUENCE FOR CONSUMERS: absence from the catalogue is NOT evidence a
# keyword is unknown. Any linter rule must treat this list's existence as
# proof that catalogue-absence cannot fail a keyword.
EXTRACTION_MISSED = {
    # id: (status, evidence)
    "effect:set_variable": ("vanilla", "used in 360 vanilla files"),
    "trigger:has_local_variable": ("vanilla", "used in 5 vanilla files"),
    "effect:add_breach": ("vanilla", "used in 2 vanilla files; "
                                     "remove_breach IS in the registry"),
    "trigger:global_variable_map_size": (
        "confirmed_working", f"{V}: probes 4-6, size read back exactly"),
}

# binary GUI extraction noise: category headers and class names that the
# registrar walk scraped as keywords (exposed by the dump cross-check)
GUI_EXTRACTION_NOISE = {"Common", "GUI", "Script", "Uncategorized",
                        "InternalClausewitzGUI", "CPdxIntSetting",
                        "CPdxVector2fSetting"}

# Probe 9: list types tested as every_<base>; elements found
LIST_PROBE = {
    "other_core_country": 1, "country_in_hierarchy": 2,
    "friendly_country": 1, "hostile_country": 1,
    "country_annexing_us": 0, "country_we_are_annexing": 0,
    "country_with_succession_law": 0, "area_with_owned_province": 0,
}

SCOPE_LINKS_LIVE = {"largest_army", "largest_navy", "country_stance",
                    "country_color", "active_chivalric_order",
                    "max_great_powers"}

# DEFINES_STATUS.md tiers for the hidden defines (max tier per define)
DEFINE_TIERS = {
    "NDiplomacy.DIPLOMATIC_RANGE": 3,
    "NMercenary.MERCENARY_DISTANCE_CAP": 2,
    "NAI.AI_RIVAL_STRENGTH_DIFFERENCE_LIMIT": 2,
    "NAI.AI_ARMY_MAINTENANCE_UTILITY": 1,
    "NAI.AI_LIBERATE_SLAVES_DESIRE_BASE": 1,
    "NAI.AI_MILITARY_ASSIGNMENT_STRENGTH_FACTOR": 1,
    "NAI.BASE_CASUS_BELLI_WARGOAL_DESIRE": 1,
    "NAI.LOAN_INTEREST_RATE_VS_BANK_LOAN_INTEREST_MULTIPLIER": 1,
    "NAI.SELL_PROVINCE_DEBT_YEARS_OF_INCOME": 1,
    "NCountry.REBEL_CONTROL_CHANGE_LOSS": 1,
    "NEconomy.GROWTH_FROM_FOOD_MULTIPLIER": 1,
    "NEconomy.REPLACE_OBSOLETE_BUILDING_SPEED_INCRASE": 1,
    "NWar.WAR_WORTH_DEVELOPMENT_RGO": 1,
    "NCityGraphics.IMPOSTOR_WALL_MESH_SCALE": 0,
    "NCityGraphics.MIN_RELATIVE_SIZE_FOR_LOCKED_EDGES": 0,
    "NCityGraphics.WALL_NEW_VERTEX_MINIMUM_DISTANCE": 0,
    "NCityGraphics.TOWER_SAFE_DISTANCE_TO_GATE": 0,
    "NCityGraphics.WALL_MESH_SCALE": 0,
    "NBorder.MAX_ZOOM_STEP_CROSSING_PENALTY": 0,
    "NGraphics.BUILDING_PERCENTAGE_ZOOM_OUT_STEP": 0,
    "NGraphics.TERRAIN_MULTIPLICATION_START": 0,
    "NGraphics.TERRAIN_MULTIPLICATION_END": 0,
    "NMapName.RENDER_AFTER_NAMES_ZOOM": 0,
}
TIER_LABEL = {3: "PROVEN INERT (do not use)",
              2: "no effect detected (handles may be insensitive)",
              1: "loads and reads back (sentinel-proven), effect unknown",
              0: "non-zero default read via GetDefine, never override-tested"}

HIDDEN_DEFINE_NOTE = ('"Vanilla never sets it" is a RED FLAG: the one '
                      "behaviourally tested hidden define is inert, and the "
                      "explanation (superseded duplicates) predicts the rest "
                      "are too. See DEFINES_STATUS.md.")


def parse_curated():
    """CURATED.md tables -> {keyword: (family, impl_class)} + not-curated set."""
    text = (ROOT / "CURATED.md").read_text(encoding="utf-8")
    fam, out, not_curated = None, {}, set()
    for ln in text.splitlines():
        if ln.startswith("## "):
            fam = ln[3:].split(" - ")[0].strip()
            if fam.startswith("How each entry"):
                fam = None
            continue
        m = re.match(r"^\|\s*`([a-z0-9_]+)`\s*\|\s*(effect|trigger)\s*\|"
                     r"\s*([^|]*)\|", ln)
        if m and fam and not fam.startswith("Not curated"):
            cls = m.group(3).strip()
            out[m.group(1)] = (fam, None if cls in ("-", "") else cls)
        if fam and fam.startswith("Not curated"):
            not_curated.update(re.findall(r"`([a-z0-9_]+)`", ln))
    return out, not_curated


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--sabotage", action="store_true",
                    help="corrupt one input in memory; the build MUST fail")
    args = ap.parse_args()

    atlas = J("atlas.json")
    undoc = J("undocumented.json")
    verified = J("verified.json")
    effect_scopes = J("effect_scopes.json")
    scope_types = J("scope_types.json")
    scopes_all = J("scopes.json")
    scopes_undoc = set(J("scopes_undocumented.json"))
    scope_results = J("scope_results.json")
    list_all = J("list_types.json")
    list_full = J("list_types_full.json")
    composed_vanilla = set(J("composed_bases_vanilla.json"))
    gui_all = J("gui_functions.json")
    gui_undoc = set(J("gui_undocumented.json"))
    gui_tested = set(J("gui_batch_bare.json")["funcs"])
    gui_bare = set(J("gui_bare_results.json")["resolved"])
    gui_player = set(J("gui_player_methods.json"))
    gui_typed = set(J("gui_typed_resolved.json"))
    typed_recv = J("typed_batch.json")["recv"]
    gui_types_inf = J("gui_function_types.json")
    gui_type_methods = J("gui_type_methods.json")
    dump = J("data_types_dump.json")
    defs = J("defines_all.json")
    hidden_vals = J("hidden_define_values.json")

    if args.sabotage:
        undoc["effect"].remove("debug_log")

    curated, not_curated = parse_curated()
    undoc_eff = set(undoc["effect"])
    undoc_trg = set(undoc["trigger"])
    impl = {r["keyword"]: r["impl_class"]
            for k in verified for r in verified[k]}

    # vanilla .gui usage: method -> [types]
    vanilla_gui_types = {}
    for t, ms in gui_type_methods.items():
        for mname in ms:
            vanilla_gui_types.setdefault(mname, []).append(t)
    # dump membership: name -> [(type, entry)] ; None type = global
    dump_owners = {}
    for name, e in dump["globals"].items():
        dump_owners.setdefault(name, []).append((None, e))
    for t, members in dump["types"].items():
        for name, e in members.items():
            dump_owners.setdefault(name, []).append((t, e))

    items = {}

    def add(item_id, item):
        assert item_id not in items, f"id collision: {item_id}"
        assert item["status"] in USABILITY, item["status"]
        assert item.get("evidence"), f"no evidence: {item_id}"
        item["usability"] = item.get("usability", USABILITY[item["status"]])
        items[item_id] = item

    # ------------------------------------------------------------ effects/triggers
    for kind, names, undoc_set, confirmed_set in (
            ("effect", atlas["effect"], undoc_eff, CONFIRMED_EFFECTS),
            ("trigger", atlas["trigger"], undoc_trg, CONFIRMED_TRIGGERS)):
        for name in names:
            item_id = f"{kind}:{name}"
            it = {"kind": kind, "name": name,
                  "undocumented": name in undoc_set}
            ev = ["atlas.json (binary registrar walk)"]
            if name in undoc_set:
                it["status"] = "verified_real"
                ev.append(f"{V}: 168/168 batch verification")
                if impl.get(name):
                    it["impl_class"] = impl[name]
            else:
                it["status"] = "vanilla"
                ev.append("used by vanilla script files")
            if name in confirmed_set:
                it["status"] = "confirmed_working"
                ev.append(f"{V}: probe read-back/sentinel")
            if name in MAP_LOOKUP_TRIGGERS and kind == "trigger":
                it.setdefault("notes", []).append(MAP_LOOKUP_NOTE)
            if name in curated:
                it["family"], cls = curated[name]
                it["curated"] = True
                if cls and "impl_class" not in it:
                    it["impl_class"] = cls
            elif name in not_curated:
                it["curated"] = False
            sk = f"{kind}:{name}"
            if sk in SYNTAX:
                it["syntax"], syn_ev = SYNTAX[sk]
                ev.append(syn_ev)
            # scope information, best source wins
            if kind == "effect" and name in effect_scopes["required_scope"]:
                it["scope"] = {"required": effect_scopes["required_scope"][name],
                               "source": "probe"}
                ev.append(f"{V}: scope requirements for all 34")
            elif kind == "effect" and name in effect_scopes["country_scope"]:
                it["scope"] = {"ok_in": ["country"], "source": "probe"}
                ev.append(f"{V}: scope requirements for all 34")
            elif name in scope_types["observed"]:
                obs = [[s, n] for s, n in scope_types["observed"][name]
                       if s not in ("(top level)", "(file default)")]
                if obs:
                    it["scope"] = {"observed": obs,
                                   "source": "vanilla_inference"}
            elif name in scope_types["name_hint"]:
                it["scope"] = {"hint": scope_types["name_hint"][name],
                               "source": "name_hint"}
            it["evidence"] = ev
            add(item_id, it)

    # ------------------------------------------------------------ scope links
    for name in scopes_all:
        item_id = f"scope:{name}"
        it = {"kind": "scope_link", "name": name,
              "undocumented": name in scopes_undoc}
        ev = ["scopes.json (binary extraction)"]
        if name in scopes_undoc:
            if name in SCOPE_LINKS_LIVE:
                it["status"] = "confirmed_working"
                it["scope_link"] = {"entered_live": True}
                ev.append(f"{V}: scope links 52/52, entered with data")
            elif name == "yes":
                it["status"] = "registered"
                it["usability"] = 5
                it.setdefault("notes", []).append(
                    "Almost certainly an extraction artifact (bare token), "
                    "not a real scope link.")
            else:
                it["status"] = "accepted"
                ev.append(f"{V}: scope links 52/52 accepted (empty is "
                          "correct for a single-country test)")
        else:
            it["status"] = "vanilla"
            ev.append("used by vanilla script files")
        it["evidence"] = ev
        add(item_id, it)

    # ------------------------------------------------------------ list types
    lt_binary = set(list_all["all"])
    lt_undoc = set(list_all["undocumented"])
    lt_cand = set(list_full["candidates"])
    for name in sorted(lt_binary | composed_vanilla | lt_cand):
        item_id = f"list_type:{name}"
        it = {"kind": "list_type", "name": name,
              "undocumented": name not in composed_vanilla,
              "list_type": {
                  "prefixes": ["every_", "any_", "random_", "ordered_"],
                  "sources": [s for s, ok in (
                      ("binary_high_confidence", name in lt_binary),
                      ("vanilla_usage", name in composed_vanilla),
                      ("binary_candidate", name in lt_cand)) if ok]}}
        ev = []
        if name in composed_vanilla:
            it["status"] = "vanilla"
            ev.append("composed_bases_vanilla.json (vanilla script usage)")
        elif name in LIST_PROBE:
            n = LIST_PROBE[name]
            it["list_type"]["probe"] = {"tested_as": f"every_{name}",
                                        "elements": n}
            it["status"] = "confirmed_working" if n > 0 else "accepted"
            ev.append(f"{V}: Probe 9 (empty is not failure)")
        elif name in lt_binary:
            it["status"] = "registered"
            ev.append("list_types.json (binary template band)")
        else:
            it["status"] = "inferred"
            ev.append("list_types_full.json candidates (low-confidence band)")
        if name in lt_undoc or name in LIST_PROBE:
            it.setdefault("notes", []).append(
                "Only the every_ prefix was probe-tested; the other three "
                "prefixes are how vanilla uses its own base names.")
        it["evidence"] = ev or ["list_types.json"]
        add(item_id, it)

    # ------------------------------------------------------------ GUI functions
    dump_meta_tag = f"data_types dump {dump['meta']['dump_file_date']}"
    for name in sorted(set(gui_all) | set(dump_owners)):
        item_id = f"gui:{name}"
        in_binary = name in set(gui_all)
        g = {"in_binary_1_3_11": in_binary,
             "in_dump": name in dump_owners}
        it = {"kind": "gui_function", "name": name,
              "undocumented": name in gui_undoc, "gui": g}
        ev = []
        if in_binary:
            ev.append("gui_functions.json (binary registrar walk)")
        # resolution from probes
        res = []
        if name in gui_bare:
            res.append({"path": "bare_global"})
        if name in gui_player:
            res.append({"path": "GetPlayer"})
        if name in gui_typed:
            res.append({"path": "typed",
                        "receiver": typed_recv.get(name)})
        if res:
            g["resolution"] = res
            it["status"] = "confirmed_working"
            ev.append(f"{V}: GUI passes (577 confirmed usable)")
        elif name not in gui_undoc and in_binary:
            it["status"] = "vanilla"
            ev.append("used by vanilla .gui files")
        elif name in gui_tested:
            it["status"] = "registered"
            g["tested_unreachable"] = True
            it.setdefault("notes", []).append(
                "Tested bare and via GetPlayer without resolving; needs a "
                "receiver the console cannot construct. Untested, not "
                "disproven.")
            ev.append(f"{V}: GUI passes")
        else:
            it["status"] = "registered"
            if name in dump_owners and not in_binary:
                ev.append(dump_meta_tag)
        # type labels, all sources kept with provenance
        tlist = []
        seen_types = set()
        for t, e in dump_owners.get(name, []):
            tname = t or "(global)"
            if tname in seen_types:
                continue
            seen_types.add(tname)
            entry = {"type": tname, "source": "dump"}
            for fld in ("def_type", "returns", "desc"):
                if e.get(fld):
                    entry[fld] = e[fld]
            if e.get("args"):
                entry["args"] = e["args"]
            tlist.append(entry)
        for t in vanilla_gui_types.get(name, []):
            if t not in seen_types:
                seen_types.add(t)
                tlist.append({"type": t, "source": "vanilla_gui"})
        inf = gui_types_inf.get(name)
        if inf and inf["type"] not in seen_types:
            src = ("vanilla_gui" if inf["how"] == "vanilla"
                   else "adjacency_80pct")
            tlist.append({"type": inf["type"], "source": src})
        if tlist:
            g["types"] = tlist
        if name in dump_owners:
            ev.append(dump_meta_tag)
        if name in GUI_EXTRACTION_NOISE:
            it["usability"] = 5
            it.setdefault("notes", []).append(
                "Likely binary-extraction noise (category header or class "
                "name), not a data function; absent from the dump.")
        it["evidence"] = ev or ["gui_functions.json"]
        add(item_id, it)

    # keywords the binary walk missed but that are proven real
    for miss_id, (status, why) in EXTRACTION_MISSED.items():
        kind, name = miss_id.split(":", 1)
        it = {"kind": kind, "name": name,
              "undocumented": status != "vanilla",
              "status": status,
              "extraction_missed": True,
              "notes": ["Missed by the binary registrar walk (family gap); "
                        "proven real independently. Catalogue absence is "
                        "NOT evidence of non-existence."],
              "evidence": [why]}
        if miss_id in SYNTAX:
            it["syntax"], syn_ev = SYNTAX[miss_id]
            it["evidence"].append(syn_ev)
        add(miss_id, it)

    # GetDefine is real (probe-proven) even though no registry lists it
    if "gui:GetDefine" in items:
        gd = items["gui:GetDefine"]
        gd["status"] = "confirmed_working"
        gd["usability"] = 100
        gd["syntax"] = ("[GetDefine('NDiplomacy','TRUCE_YEARS')]  "
                        "(two args: block, key; reads any live define)")
        gd.setdefault("notes", []).append(
            "A fake key also returns 0 - a zero read proves nothing.")
        gd["evidence"].append(f"{V}: GetDefine")

    # ------------------------------------------------------------ defines
    for full, d in {**defs["defines"], **defs["engine_only_blocks"]}.items():
        item_id = f"define:{full}"
        engine_only = "block_source" in d
        de = {"block": d["block"], "key": d["key"],
              "vanilla_set": d.get("vanilla_set", False)}
        it = {"kind": "define", "name": full,
              "undocumented": not de["vanilla_set"], "define": de}
        ev = ["defines_all.json (eu5.exe RTTI + vanilla defines files)"]
        if engine_only:
            de["block_source"] = d["block_source"]
            it["status"] = "registered"
            it.setdefault("notes", []).append(
                "Block never declared by any vanilla file; block/key split "
                "is a CamelCase heuristic.")
        elif de["vanilla_set"]:
            it["status"] = "vanilla"
            de["vanilla_value"] = d.get("vanilla_value")
            de["vanilla_file"] = d.get("vanilla_file")
        else:
            tier = DEFINE_TIERS.get(full)
            if tier is not None:
                de["tier"] = tier
                de["tier_label"] = TIER_LABEL[tier]
                ev.append("DEFINES_STATUS.md")
            if full in hidden_vals:
                de["value_read"] = hidden_vals[full]
                de["value_read_confirmed"] = hidden_vals[full] != "0"
                if hidden_vals[full] == "0":
                    it.setdefault("notes", []).append(
                        "Read as 0 via GetDefine, but a fake define also "
                        "reads 0 - the value is unconfirmed.")
            if tier == 3:
                it["status"] = "dead"
                ev.append(f"{V}: loaded does NOT mean live (A/B)")
            elif tier in (0, 1, 2):
                it["status"] = "accepted"
                ev.append(f"{V}: hidden defines proven loaded")
            else:
                it["status"] = "registered"
            it.setdefault("notes", []).append(HIDDEN_DEFINE_NOTE)
        it["evidence"] = ev
        add(item_id, it)

    # ------------------------------------------------------------ validation
    counts = {}
    for it in items.values():
        counts.setdefault(it["kind"], {}).setdefault(it["status"], 0)
        counts[it["kind"]][it["status"]] += 1

    def total(kind):
        return sum(counts.get(kind, {}).values())

    # 553/1270 from the walk + the proven extraction misses
    assert total("effect") == 553 + 2, total("effect")
    assert total("trigger") == 1270 + 2, total("trigger")
    assert items["trigger:global_variable_map_size"]["extraction_missed"]
    assert total("scope_link") == 283, total("scope_link")
    assert sum(1 for i in items.values()
               if i["kind"] == "effect" and i["undocumented"]) == 34
    assert sum(1 for i in items.values()
               if i["kind"] == "trigger" and i["undocumented"]) == 134 + 1
    # +1 = global_variable_map_size, probe-proven but walk-missed
    assert sum(1 for i in items.values()
               if i["kind"] == "scope_link" and i["undocumented"]) == 52
    n_gui_conf = counts["gui_function"].get("confirmed_working", 0)
    assert n_gui_conf == 577 + 1, f"GUI confirmed {n_gui_conf} != 577+GetDefine"
    assert total("define") == 2975, (
        f"defines {total('define')} != 2975 (RTTI enumeration)")
    assert counts["define"].get("dead", 0) == 1  # DIPLOMATIC_RANGE
    assert items["effect:debug_log"]["status"] == "confirmed_working"
    assert items["define:NGame.HOUR_TICK"]["define"]["vanilla_value"] == "2"
    assert items["scope:largest_army"]["status"] == "confirmed_working"
    assert items["list_type:friendly_country"]["status"] == "confirmed_working"
    assert items["gui:GetDefine"]["status"] == "confirmed_working"
    for it in items.values():
        assert 0 <= it["usability"] <= 100

    meta = {
        "project": "eu5-engine-atlas catalogue",
        "game_version": "1.3.11",
        "built": datetime.datetime.now().strftime("%Y-%m-%d %H:%M"),
        "builder": "tools/build_catalogue.py",
        "statuses": {s: {"usability": u} for s, u in USABILITY.items()},
        "dump_note": ("GUI type/return/desc data from the data_types dump "
                      "of 2026-07-15, confirmed current to 1.3.11 (99.9% "
                      "name overlap with the binary extraction); after any "
                      "patch re-run dump_data_types + parse_data_types.py "
                      "+ this builder"),
        "recall_warning": ("the binary registrar walk has proven false "
                          "negatives (see items with extraction_missed); "
                          "absence from this catalogue is NOT evidence a "
                          "keyword does not exist - linter rules must "
                          "never fail a keyword for being absent here"),
        "counts": counts,
        "items_total": len(items),
    }
    OUT.write_text(json.dumps({"meta": meta, "items": items}, indent=1),
                   encoding="utf-8")
    print(json.dumps(counts, indent=1, sort_keys=True))
    print(f"items: {len(items)}  wrote {OUT}")


if __name__ == "__main__":
    main()
