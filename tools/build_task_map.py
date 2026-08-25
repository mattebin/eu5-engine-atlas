"""Build task_map.json - task-oriented entry points into the catalogue.

A modder says "I want to make a map mode" and gets the relevant files,
catalogue items, gotchas and lint rules for that job, instead of needing
the vocabulary first. Consumed by the workbench next to catalogue.json.

Every reference is validated at build time:
  - catalogue item ids against catalogue.json
  - lint rule ids against eu5lint's rules.py, parsed LIVE from the checker
    repo so newly added rules are seen automatically (the linter stays a
    separate program; this is the data contract between them)
  - vanilla path claims against the actual install

Content is curated from probe-verified knowledge (VERIFIED.md, the vault
engine notes, eu5lint's VERIFICATION.md). No speculation: every gotcha
traces to a verified finding.
"""
import argparse
import datetime
import json
import pathlib
import re

ROOT = pathlib.Path(r"T:\eu5-engine-atlas")
GAME = pathlib.Path(r"C:\SteamLibrary\steamapps\common\Europa Universalis V\game")
LINTER = pathlib.Path(r"T:\eu5-mod-checker\eu5lint\rules.py")
OUT = ROOT / "task_map.json"

T = {}  # task key -> definition


def task(key, title, summary, files, items, lint_rules, gotchas, sources):
    T[key] = {"title": title, "summary": summary, "files": files,
              "items": items, "lint_rules": lint_rules, "gotchas": gotchas,
              "sources": sources}


# ---------------------------------------------------------------------------

task(
    "map_mode",
    "Add a map mode",
    "Script-defined map modes with map_color per location. Added files "
    "work; no override of vanilla map_modes.txt needed.",
    files=[
        {"path": "in_game/gfx/map/map_modes/",
         "role": "mode definitions (added files work; schema documented in "
                 "a comment block inside vanilla map_modes.txt)",
         "vanilla_example": "in_game/gfx/map/map_modes/map_modes.txt"},
        {"path": "main_menu/gfx/interface/icons/map_modes/",
         "role": "mode icon as <key>.dds loose file"},
        {"path": "in_game/common/on_action/",
         "role": "precompute per-location variables (on_game_start + "
                 "monthly/daily pulses) for variable-driven colours",
         "vanilla_example": "in_game/common/on_action/location_pulses.txt"},
    ],
    items=["effect:refresh_map_colors", "effect:set_variable",
           "effect:set_global_variable", "effect:change_variable",
           "gui:SetMapMode", "gui:GetMapColorLedger", "gui:IsActive"],
    lint_rules=["W105", "W106"],
    gotchas=[
        "Colours repaint ONLY when a subscribed counter ticks "
        "(color_refresh_counters, 34 counter names in vanilla "
        "map_modes.txt). No counter fires on script variable changes; "
        "Day = repaint every game day is the lazy fallback.",
        "In-mode repaint recipe: a category = hidden twin mode with "
        "identical map_color plus GUI watcher widgets that ping-pong "
        "SetMapMode a<->b; each mode ENTRY recomputes colours. "
        "refresh_map_colors does NOT repaint the active mode.",
        "Vanilla ships hidden map modes (category = hidden) a mod can "
        "copy-unhide: winter severity, hemisphere, sea currents, "
        "selected_goods and more.",
        "map_color supports rgb/hsv literals, lerp, and var: reads "
        "(root = location). Proven at scale by the 43-mode Zorange mod.",
        "The map colour ledger content (GetMapColorLedger) is engine-fed "
        "per mode, not script-feedable.",
    ],
    sources=["vault knowledge/eu5-engine-internals (map modes, solved "
             "2026-08-25)", "CF Raw Materials Finder v1.4.0"])

task(
    "defines_tuning",
    "Tune engine defines",
    "Per-key overrides of the 2,975-define registry. The catalogue knows "
    "every registered define, which ones vanilla sets, and their values.",
    files=[
        {"path": "loading_screen/common/defines/",
         "role": "defines live HERE (even gameplay ones); per-key override "
                 "inside the correct N* block, zz_ filename prefix wins",
         "vanilla_example": "loading_screen/common/defines/00_defines.txt"},
    ],
    items=["define:NGame.HOUR_TICK", "define:NUnit.ARMY_MOVEMENT_SPEED",
           "define:NCombat.HOURS_PER_PHASE",
           "define:NAI.CONQUER_DESIRE_CB_BONUS", "gui:GetDefine"],
    lint_rules=["E005", "S002", "S004", "W104"],
    gotchas=[
        "Defines load ONCE at boot; an A/B test needs two verified game "
        "launches (check the launch count in debug.log).",
        "Wrong N* block = silently inert. Last-loaded filename wins per "
        "key (zzz_ beats zz_ regardless of mod order).",
        "'Vanilla never sets it' is a RED FLAG, not an opportunity: the "
        "one behaviourally tested hidden define is inert (superseded "
        "duplicate). 54 such defines are catalogued with tiers.",
        "GetDefine('BLOCK','KEY') reads any live define from GUI or "
        "debug_log interpolation, but a fake key also returns 0.",
        "Define comments can LIE (the 10x CABINET_ACTION_SKILL_MODIFIER "
        "doc error). Only probes settle semantics.",
        "Any per-tick accrual is suspect under HOUR_TICK mods: movement "
        "and combat advance per TICK, calendar tasks per day.",
    ],
    sources=["DEFINES_STATUS.md", "VERIFIED.md (GetDefine, A/B)",
             "vault knowledge/eu5-engine-internals (defines system)"])

task(
    "ai_behaviour",
    "Change AI behaviour",
    "The AI surface script can reach: generic actions with ai_will_do "
    "scoring, AI-desire triggers, and the NAI define block.",
    files=[
        {"path": "in_game/common/generic_actions/",
         "role": "script-defined contextual actions the AI (and player "
                 "automation) takes: select_trigger, ai_tick cadence, "
                 "effect, ai_will_do score"},
        {"path": "in_game/common/generic_action_ai_lists/",
         "role": "gates which actions a country considers"},
        {"path": "loading_screen/common/defines/",
         "role": "NAI block defines (vanilla-set ones are the live knobs)"},
    ],
    items=["trigger:conquer_area_preference", "trigger:powerful_ally_weight",
           "trigger:union_partner_weight", "trigger:modifier_utility",
           "trigger:join_organization_ai_desire",
           "trigger:employment_system_desire",
           "trigger:create_market_utility", "trigger:conquistador_utility",
           "scope:largest_army", "scope:largest_navy",
           "list_type:friendly_country", "list_type:hostile_country"],
    lint_rules=["S002"],
    gotchas=[
        "Generic actions are a full AI-behaviour surface defines cannot "
        "reach (vanilla's garrison-sortie AI: ratio > 5.0 checked every "
        "35 days - why undermanned sieges are never punished).",
        "every_friendly_country / every_hostile_country iterate AI-facing "
        "country classifications no vanilla mod has ever used "
        "(probe-verified live).",
        "The netcode has NO script or defines surface; AI load reduction "
        "is the only MP lever.",
        "The hidden NAI defines (never set by vanilla) are presumed "
        "vestigial; tune the ones vanilla sets.",
    ],
    sources=["vault knowledge/eu5-engine-internals (generic actions)",
             "VERIFIED.md (probe 9, scope links)", "CURATED.md (AI family)"])

task(
    "event_scripting",
    "Events, on_actions and scripted effects",
    "Standard content scripting plus the undocumented variable/list/map "
    "API with probe-established syntax.",
    files=[
        {"path": "in_game/events/", "role": "event files"},
        {"path": "in_game/common/on_action/",
         "role": "hooks: on_siege_won/lost, on_location_occupied/lost, "
                 "on_annexed family, pulses. No on_siege_started exists."},
        {"path": "in_game/common/scripted_effects/",
         "role": "shared effect blocks",
         "vanilla_example": "in_game/common/scripted_effects/"
                            "international_organization_effects.txt"},
        {"path": "in_game/common/script_values/", "role": "shared values"},
    ],
    items=["effect:set_global_variable", "effect:change_global_variable",
           "effect:clamp_global_variable", "effect:round_global_variable",
           "effect:add_to_global_variable_list",
           "effect:sort_global_variable_list",
           "effect:add_to_global_variable_map",
           "trigger:is_target_in_global_variable_list",
           "trigger:has_global_variable_map",
           "trigger:global_variable_map_size",
           "trigger:is_key_in_global_variable_map",
           "list_type:key_in_variable_map", "effect:debug_log",
           "effect:random_log_scopes", "trigger:nand", "trigger:any_false",
           "trigger:random_integer"],
    lint_rules=["E001", "W102"],
    gotchas=[
        "A parse error silently aborts the WHOLE file before line 1 runs; "
        "an unresolvable script value kills the file with NO error at all.",
        "Scope-link comparisons need ?=; plain = on an empty link aborts "
        "the script. exists does not work on event-target links.",
        "References resolve at PARSE TIME in file order: forward "
        "references fail half-silently while effects still apply.",
        "Lists hold SCOPES; sort order = script value per element, "
        "descending. Maps: write with key=, query with target= (the "
        "vanilla form; console probes rejected key= in every form).",
        "Global variables persist in saves and are MP-shared; country "
        "variables are per-country and MP-safe.",
        "debug_log writes to debug.log with file+line and interpolates "
        "[DataFunctions] - the undocumented debugging tool.",
    ],
    sources=["VERIFIED.md (probes 1-8 + 2026-08-26 addendum)",
             "vault knowledge/eu5-jomini-modding-gotchas"])

task(
    "gui_interface",
    "GUI and interface mods",
    "Hot-reloadable .gui work over the 15,754-function data API, typed "
    "end to end in the catalogue.",
    files=[
        {"path": "in_game/gui/", "role": ".gui files (hot-reload live)"},
        {"path": "in_game/common/scripted_guis/",
         "role": "click logic (does NOT hot-reload; restart)"},
        {"path": "main_menu/localization/",
         "role": "loc .yml (restart; \\n must be the two-character escape)"},
    ],
    items=["gui:GetPlayer", "gui:GetName", "gui:MakeScope",
           "gui:GetScriptedGui", "gui:Localize", "gui:Concatenate",
           "gui:EqualTo_string", "gui:PdxGuiTriggerAllAnimations"],
    lint_rules=["E008", "E009", "W103", "W106"],
    gotchas=[
        "type definitions must sit inside a types GroupName { } block; an "
        "instance referencing a failed type is silently dropped.",
        "No boolean literals in GUI script: tautology tricks "
        "Or(F, Not(F)) = true.",
        "Item wrappers are per-datamodel-call copies: visible rows keep "
        "stale wrappers; mutate the visible row's own wrapper.",
        "NEVER write mod files while eu5.exe runs (hot-reload parses "
        "half-written files); atomic single-file swaps of .gui are safe.",
        "gui files affect the checksum (unlike EU4); a mod replacing base "
        "templates restyles other mods' windows.",
        "dump_data_types (console, -debug_mode) regenerates the full data "
        "API reference the catalogue's GUI typing is built from.",
        "A hidden parent gates its children: hover-immune UI must be a "
        "SIBLING or widen the parent's visible gate via blockoverride.",
    ],
    sources=["vault knowledge/eu5-jomini-modding-gotchas (GUI techniques)",
             "vault knowledge/eu5-engine-internals (GUI system)"])

task(
    "modifier_systems",
    "Modifiers: auto, static, scaled",
    "Three modifier systems with different binding rules; picking the "
    "wrong one fails silently.",
    files=[
        {"path": "in_game/common/auto_modifiers/",
         "role": "country/IO scope ONLY, applied automatically; scope "
                 "comes from the FILE, names are free-form"},
        {"path": "main_menu/common/static_modifiers/",
         "role": "the engine's SCALED system; block names are exe-bound, "
                 "invented names are dead weight"},
        {"path": "main_menu/common/modifier_type_definitions/",
         "role": "registry of every grantable modifier key",
         "vanilla_example": "main_menu/common/modifier_type_definitions/"
                            "00_modifier_types.txt"},
    ],
    items=["effect:add_country_modifier", "effect:add_dynasty_modifier"],
    lint_rules=["E003", "E004", "E007", "S003"],
    gotchas=[
        "A category = location auto modifier loads without error and is "
        "silently NEVER evaluated (cost a pillar for days).",
        "Duplicate static-modifier keys in ADDED files are DROPPED (first "
        "definition wins) - why full-file copies are needed. Database "
        "entry modes (INJECT:key etc.) are the sanctioned alternative, "
        "untested on static_modifiers.",
        "auto modifier extras proven live at 23k users: requires_real, "
        "hide_effects, and scales_with = <script_value> which can read "
        "country variables = runtime-adjustable modifier of anything.",
        "Saves do not persist auto/static modifiers by name (derived "
        "state); save-grep cannot verify them.",
    ],
    sources=["vault knowledge/eu5-jomini-modding-gotchas (2026-07-22..24 + "
             "probe-verified 08-08/09)", "eu5lint VERIFICATION.md"])

task(
    "military_content",
    "Units, spawning, siege and combat",
    "Spawn effects with exe-embedded usage docs, live siege script "
    "surface, and the undocumented military query triggers.",
    files=[
        {"path": "in_game/common/unit_types/", "role": "unit types"},
        {"path": "in_game/common/unit_categories/", "role": "categories"},
        {"path": "in_game/common/generic_actions/",
         "role": "the only surface for siege-initiation style rules "
                 "(no defines exist for besieger-vs-garrison gating)"},
    ],
    items=["effect:create_num_sub_unit_of_category",
           "effect:create_sub_unit_with_owner", "effect:create_num_sub_unit",
           "effect:spawn_army_levy_unit", "effect:garrison_sortie",
           "effect:add_breach", "effect:change_siege_progress",
           "effect:set_garrison_size", "effect:create_rebel",
           "trigger:garrison_strength", "trigger:besieger_strength",
           "trigger:combat_side_strength", "trigger:unit_strength",
           "trigger:regular_navy_size", "trigger:province_army_levy_size",
           "scope:combat_attacker", "scope:combat_defender",
           "list_type:country_annexing_us"],
    lint_rules=["W104"],
    gotchas=[
        "Fresh-spawned units start at 0 strength and low morale; rebels "
        "via create_rebel rise battle-ready (the reliable on-demand "
        "battle recipe).",
        "Siege initiation gating does NOT exist in defines (all 65 "
        "SIEGE/GARRISON keys enumerated); use generic actions.",
        "garrison_sortie: if the defender loses, the fort is INSTANTLY "
        "occupied (exe usage doc).",
        "create_num_sub_unit requires location scope; "
        "create_navy_country_in_location location, "
        "create_navy_country_from_province province (probe-verified).",
        "Combat advances per TICK with a hardcoded 2h step; tick mods "
        "must scale NCombat rates (shipped in Responsive Universalis).",
    ],
    sources=["vault knowledge/eu5-engine-internals (siege surface, combat)",
             "VERIFIED.md (scope requirements)", "CURATED.md"])

task(
    "debugging_workflow",
    "Probe, verify and debug a mod",
    "The verification discipline that made the atlas trustworthy, usable "
    "by any modder.",
    files=[
        {"path": "loading_screen/common/defines/",
         "role": "define overrides to test (two launches for an A/B)"},
    ],
    items=["effect:debug_log", "effect:debug_log_date",
           "effect:debug_log_scopes", "effect:random_log_scopes",
           "trigger:current_tooltip_depth", "gui:GetDefine",
           "effect:test_log", "trigger:has_game_started",
           "trigger:has_multiple_players"],
    lint_rules=["E005", "S002"],
    gotchas=[
        "Launch with -tdebug; console `run <file>` executes effect files "
        "from Documents/Paradox Interactive/Europa Universalis V/run/ in "
        "player-country scope.",
        "Arm every probe: first line = a deliberately fake keyword that "
        "MUST error, or the run proves nothing. Controls must be the "
        "SAME KIND as the thing tested - unknown TRIGGERS evaluate TRUE "
        "and use a different error format than effects.",
        "error.log ROTATES into error.1.log mid-run; debug.log RESETS on "
        "launch; filter by timestamp, never string-compare across "
        "midnight, never seek to saved byte offsets.",
        "Static validation noise: 'Failed to fetch variable' lines appear "
        "for lines whose sentinels PASSED. Judge by sentinels and "
        "read-backs, never by error.log alone.",
        "The error.log profile on ONE fresh campaign load vs a known "
        "baseline is the only valid acceptance test for setup changes.",
    ],
    sources=["VERIFIED.md (method + traps)", "README.md (traps list)",
             "vault knowledge/eu5-engine-internals (console probing)"])


# ---------------------------------------------------------------------------

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--sabotage", action="store_true")
    args = ap.parse_args()

    cat = json.loads((ROOT / "catalogue.json").read_text(encoding="utf-8"))
    items = cat["items"]
    if args.sabotage:
        T["map_mode"]["items"].append("effect:totally_fake_effect_xyz")

    # validate lint rule ids LIVE against the checker repo
    lint_ids = None
    if LINTER.exists():
        lint_ids = set(re.findall(r'@rule\("([EWS]\d{3})"',
                                  LINTER.read_text(encoding="utf-8")))
        assert len(lint_ids) >= 19, f"only {len(lint_ids)} lint rules found"

    n_item_refs = 0
    for key, t in T.items():
        for ref in t["items"]:
            assert ref in items, f"{key}: unknown catalogue item {ref}"
            n_item_refs += 1
        if lint_ids is not None:
            for r in t["lint_rules"]:
                assert r in lint_ids, f"{key}: unknown lint rule {r}"
        for f in t["files"]:
            ex = f.get("vanilla_example")
            if ex and GAME.is_dir():
                assert (GAME / ex).exists(), f"{key}: missing vanilla {ex}"
        # attach current status snapshots so the workbench can rank
        t["item_status"] = {ref: {"status": items[ref]["status"],
                                  "usability": items[ref]["usability"]}
                            for ref in t["items"]}

    assert len(T) == 8, len(T)
    out = {
        "meta": {
            "project": "eu5-engine-atlas task map",
            "built": datetime.datetime.now().strftime("%Y-%m-%d %H:%M"),
            "builder": "tools/build_task_map.py",
            "catalogue_built": cat["meta"]["built"],
            "lint_rules_seen": sorted(lint_ids) if lint_ids else None,
            "tasks": len(T),
            "item_refs": n_item_refs,
        },
        "tasks": T,
    }
    OUT.write_text(json.dumps(out, indent=1), encoding="utf-8")
    print(f"tasks: {len(T)}  item refs: {n_item_refs}  "
          f"lint rules seen: {len(lint_ids) if lint_ids else 'n/a'}")
    print(f"wrote {OUT}")


if __name__ == "__main__":
    main()
