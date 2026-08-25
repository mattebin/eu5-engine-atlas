# EU5 Engine Atlas

A catalogue of what the Europa Universalis V engine can do that nobody
documented.

The engine ships far more script capability than its own game files ever
demonstrate. `refresh_map_colors` is the proof: a fully working effect,
registered in the binary, used by no vanilla file, and unknown to modders
until it was found by hand. It is what made the Raw Materials Finder map
mode possible. There are more like it.

This project extracts the authoritative list from `eu5.exe` and publishes
it, so EU5 modders stop being limited by what Paradox happened to use.

## Status

Early. The extraction mechanism works and is self-validating; classifying
each keyword by kind is the open problem.

## What is established

- The binary is unprotected (no Denuvo, VMProtect or Themida) and RTTI-rich:
  **75,301 class descriptors, 7,998 distinct class names**, including
  `CRefreshMapColorsEffect` and `CGarrisonSortieEffect`. Script-visible
  effects map to `C<Name>Effect` classes.
- The engine defines **430 Effect classes and 1,157 Trigger classes**.
  Vanilla script uses only 332 of the effects.
- Script keywords are not stored as a plain table. Each one lives in a
  small lazy getter function that interns the string on first call
  (`if (!cached) cached = Intern("name", len)`), and pointers to those
  getters sit in `.rdata`.
- Walking that pointer region and reading the string out of each getter
  yields **3,049 keywords**. The extraction self-validates:
  `refresh_map_colors` lands immediately before `close_all_views`, matching
  how it was originally discovered by hand months earlier.

## Open problem

Effects and triggers interleave in the pointer region, because the walk
crosses many adjacent tables (32,725 pointers, of which 3,049 are keyword
getters). Position alone does not classify: `set_variable` (17299) and
`has_variable` (17473) sit close together, as do `add_country_modifier`
(31535) and `has_country_modifier` (31604). The next step is to find the
per-registry boundaries, or to link each keyword getter to the RTTI class
that owns it.

## Method notes (hard-won)

- **`strings` silently fails on this 136MB PE.** It returns nothing for
  keywords that are demonstrably present. Always use raw byte search.
- **Do not derive keywords from class names.** CamelCase to snake_case is
  roughly 50% wrong: `CConstructRGOUpgradeEffect` becomes
  `construct_r_g_o_upgrade`, but the real keyword is
  `construct_rgo_upgrade`.
- **Always byte-verify a candidate against the exe, with a deliberately
  fake name as a negative control.** A check that cannot fail proves
  nothing.

## Tools

- `tools/pe.py` - minimal PE32+ reader: sections, image base, RVA and file
  offset conversion.
- `tools/rtti.py` - MSVC RTTI walker: class name to vtable VA.
- `tools/extract_keywords.py` - walks the getter pointer region and reads
  each interned keyword.

Run them against your own installed `eu5.exe`. Nothing here redistributes
game files.
