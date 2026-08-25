# The catalogue data layer

`catalogue.json` is the single queryable index the modding workbench
consumes. It merges every registry and every piece of evidence in this repo
into one file: binary extraction, vanilla usage, in-game probes, the
engine's own `dump_data_types` output, scope requirements, GUI typing,
define tiers and the curated syntax from [VERIFIED.md](VERIFIED.md).

Built by `tools/build_catalogue.py`. Rebuild any time with:

```bash
python tools/build_catalogue.py
```

Inputs that need regenerating after a game patch, in order:
`tools/build_defines_all.py` (reads eu5.exe + vanilla files), the in-game
`dump_data_types` console command followed by `tools/parse_data_types.py`,
then the builder. The builder is deterministic and asserts every published
count; a sabotaged input fails the build (tested with `--sabotage`).

## Shape

```json
{
  "meta":  { "statuses": {...}, "counts": {...}, "built": "..." },
  "items": { "<kind>:<name>": { ... } }
}
```

Kinds: `effect`, `trigger`, `scope_link`, `list_type`, `gui_function`,
`define`. Ids look like `effect:debug_log`, `define:NGame.HOUR_TICK`,
`gui:GetActualGarrison`, `list_type:friendly_country`.

## The confidence model

Two separate layers, deliberately not conflated:

**1. Item status** - one enum value answering "should a modder reach for
this", with a numeric `usability` for ranking:

| status | usability | meaning |
|---|---|---|
| `confirmed_working` | 100 | positive in-game evidence: read-back with a known answer, sentinel, or live data |
| `vanilla` | 90 | vanilla's own files use it, so it works at least as vanilla uses it |
| `verified_real` | 80 | the engine provably knows it (semantic error, never `Unknown X`); behaviour and arguments unproven |
| `accepted` | 60 | accepted by the engine with no live data seen, or a define proven loaded but not proven live |
| `registered` | 25 | present in the binary or the dump, untested |
| `inferred` | 20 | existence known only from a low-confidence extraction band |
| `dead` | 0 | positive evidence it does NOTHING - listed so nobody wastes an evening on it |

`usability` is mostly `status`-derived; a few items are manually docked
(the `yes` scope-link artifact, GUI extraction noise).

**2. Attribute sources** - each typed attribute carries where it came from,
because an item can be confirmed working while its type label is a guess:

- `scope.source`: `probe` (engine's own scope error, exact) >
  `vanilla_inference` (observed enclosing blocks, with counts) >
  `name_hint` (a hint, not a fact).
- `gui.types[].source`: `dump` (engine self-documentation, includes
  `returns`/`args`/`desc`) > `vanilla_gui` (seen as `Type.Method` in .gui
  files) > `adjacency_80pct` (registration-order inference, measured 80%
  accurate - present it as a hint, never as fact).
- `define.tier` 0-3 per DEFINES_STATUS.md, plus `value_read` /
  `value_read_confirmed` (a GetDefine read of 0 proves nothing - fakes
  also read 0).

`undocumented: true` means no vanilla file uses it - the atlas's core
value. `evidence` lists the sources behind every item.

## Querying

`tools/catalogue_query.py` demonstrates the intended access patterns:

```bash
python tools/catalogue_query.py --stats
```

```bash
python tools/catalogue_query.py --kind effect --status confirmed_working
```

```bash
python tools/catalogue_query.py --kind gui_function --type Location --min-usability 90
```

```bash
python tools/catalogue_query.py --search variable_map
```

```bash
python tools/catalogue_query.py --kind define --block NAI --undocumented
```

## Corrections found while building this (2026-08-26, static evidence)

1. **The defines registry is 2,975 entries, not 2,841.** Two independent
   bugs in the original count: (a) it keyed on KEY name alone while 9 keys
   live under 2-3 blocks; (b) the UTF-8 BOM glued to block names declared
   on line 1 of a defines file, silently hiding the `NGame`, `NCamera`,
   `NMapEditor` and `NJominiIcons` blocks - `NGame.HOUR_TICK` itself was
   missing from the old count. Fixing the BOM also revealed **9 new hidden
   defines** (never set by vanilla; all camera-debug/map-editor/icon
   plumbing), so the hidden set is now **54**, and 33 further defines live
   in blocks no vanilla file declares at all (`engine_only_blocks` in
   `defines_all.json`, block split heuristic and flagged).
2. **The map key-lookup triggers are not dead.** Console probes rejected
   every key form (VERIFIED.md probes 4-6), but vanilla uses
   `is_key_in_global_variable_map = { name = ... target = root }` in
   hre.txt, reads map values via the quoted accessor
   `"global_variable_map(name|key)"`, exposes
   `GetVariableFromGlobalVariableMap(Arg0, Arg1)` in the data API, and has
   a `key_in_variable_map` list type. The catalogue carries both facts;
   trust the vanilla forms.
3. **The GUI binary extraction has 7 noise entries** (category headers
   like `Common`, `GUI`, `Uncategorized` and two `CPdx*Setting` class
   names), exposed by a 99.9% cross-check against the dump. Flagged in
   their items.

## Size and coverage

21,328 items: 553 effects, 1,270 triggers, 283 scope links, 485 list-type
bases, 15,762 GUI functions (10,828 from the binary + 4,934 more from the
dump: script-scope promotes and argument-taking functions the registrar
walk cannot see), 2,975 defines. GUI functions carry 19k+ typed
memberships with return types and descriptions from the dump.
