# EU5 Engine Atlas

A catalogue of what the Europa Universalis V engine can do that nobody
documented - extracted from `eu5.exe`, then **verified live in game**.

The premise: the engine ships far more script capability than its own game
files demonstrate. `refresh_map_colors` was the proof - a fully working
effect, registered in the binary, used by no vanilla file, unknown to
modders until found by hand. This project found the rest systematically.

Game version: **1.3.11**. Re-run the tools after any patch.

## Headline results

| Registry | In engine | Never used by vanilla | Verified in game |
|---|---|---|---|
| Effects | 553 | 34 | **34/34 real**, all scopes documented |
| Triggers | 1,270 | 134 | **134/134 real** |
| Scope links | 283 | 52 | **52/52 accepted**, 6 with live data |
| List types (composed) | 62+ found | 9 | **8 tested, 4 return live data** |
| GUI data functions | 10,828 | 3,824 game-facing | **577 confirmed usable**, 19k typed memberships via the engine's own dump |
| Defines | 2,975 | 54 | loaded but **behaviourally dead** where tested |

(Defines corrected 2026-08-26 from the previously published 2,841/45: a
UTF-8 BOM had hidden four whole blocks from the extraction, NGame included.
Details in [CATALOGUE.md](CATALOGUE.md).)

## How much the atlas added

"Known before" means used by vanilla's own files and therefore visible to
any modder who reads them.

| Registry | Known before | Newly found | Gain |
|---|---|---|---|
| Effects | 519 | 34 | +7% |
| Triggers | 1,136 | 134 | +12% |
| Scope links | 231 | 52 | +23% (one is a suspected extraction artifact) |
| List types | 253 | 11 | +4% |
| Defines | 2,888 | 87 | +3% (one proven dead, the rest presumed vestigial) |

GUI functions get a different claim: the 3,824 vanilla-unused functions
are listed by the `dump_data_types` console command, so they were
discoverable all along. What the atlas adds there is testing and typing:
577 confirmed usable from the console, and every function carried with
its owning type, arguments and return type.

Plus a working, syntax-documented **variable / list / map API** vanilla
never uses: arithmetic (`change/clamp/round`), lists with iteration and
sorting, maps as counted sets. And `GetDefine('BLOCK','KEY')` - an
undocumented way to read any live define from GUI or log.

## The documents

- **[CATALOGUE.md](CATALOGUE.md)** - the data layer: how everything below
  is merged into `catalogue.json`, one queryable index with explicit
  confidence levels. This is what the workbench consumes. `task_map.json`
  sits on top: task-oriented entry points ("add a map mode" lists the
  files, catalogue items, gotchas and lint rules for that job), built by
  `tools/build_task_map.py` with every reference validated.
- **[VERIFIED.md](VERIFIED.md)** - the evidence. Every probe, every control,
  every retraction, in order. This is the file that justifies every claim.
- **[CURATED.md](CURATED.md)** - the modder-useful subset, organised by
  capability family.
- **[UNDOCUMENTED.md](UNDOCUMENTED.md)** - raw lists of never-used keywords.
- **[GUI_AND_SCOPES.md](GUI_AND_SCOPES.md)** - GUI functions and scope links.
- **[DEFINES_STATUS.md](DEFINES_STATUS.md)** - defines by verification tier,
  including the finding that hidden defines are superseded duplicates:
  **"vanilla never sets it" is a red flag, not an opportunity**.
- **[HIDDEN_DEFINES.md](HIDDEN_DEFINES.md)** - the 45 never-set defines.
- **[BACKLOG.md](BACKLOG.md)** - open work + the workbench product direction.

## How it was done

1. **Extraction**: script keywords live in lazy string-interning getter
   functions; walking their registration initializers and grouping by which
   registrar they call yields each registry. RTTI (7,998 class names, binary
   unprotected) corroborates. Composed keywords (`every_X`) never appear as
   literal strings and needed their own hunt.
2. **Verification**: console probes with **armed instruments** - every probe
   file starts with a deliberately fake keyword that MUST error, or the run
   is void. Positive results come from `debug_log` sentinels and read-backs
   with known answers, never from silence. Negative controls of the same
   kind as the thing tested.
3. **Behaviour**: A/B tests across two verified game launches (defines load
   once at boot - the launch count must be checked in the log).

## Traps documented along the way (each cost a probe)

- A parse error silently aborts an entire script file before line 1 runs.
- An unresolvable script value kills a file with NO error at all.
- An unknown TRIGGER evaluates as true - sentinels cannot prove triggers.
- `Unknown effect X` vs `Unknown trigger type: "X"` - different formats.
- `error.log` rotates mid-run into `error.1.log`; single-file reads lose data.
- `debug.log` resets on launch - compare timestamps, never totals.
- Never compare log timestamps as strings across midnight.
- `strings` silently fails on the 136MB PE - use raw byte search.
- CamelCase-to-snake_case keyword derivation is ~50% wrong (acronyms).
- Loaded is not live: defines can be stored, readable and dead.

## Tools

`tools/` contains the full pipeline: PE reader, RTTI walker, registry
extractors, probe generators and log readers. Everything runs against your
own installed `eu5.exe` - nothing from the game is redistributed.
