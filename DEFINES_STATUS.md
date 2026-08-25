# Hidden defines: verification tiers

45 defines are registered in `eu5.exe` and never set by any vanilla defines
file. That is where the evidence starts, not where it ends. These tiers say
exactly how far each claim has been taken.

## Tier 3 - PROVEN INERT (do not use)

Behaviourally A/B tested with a direct, well-matched handle. Setting extreme
values changed nothing.

| define | test | result |
|---|---|---|
| `NDiplomacy.DIPLOMATIC_RANGE` | `within_diplomatic_range` at 7009 vs 1 | identical: Austria in range, 200+ countries in range, Yuan and Japan out, both times |

`within_diplomatic_range` is *the* mechanic this define names, so a null
result here is strong evidence the define is vestigial.

## Tier 2 - RETRACTED, never actually tested

`NMercenary.MERCENARY_DISTANCE_CAP` and
`NAI.AI_RIVAL_STRENGTH_DIFFERENCE_LIMIT` were briefly reported here as
"no effect detected". **That was wrong and is withdrawn.**

The intended A/B compared 9999 against 0, but debug.log shows only **one
game launch** (00:37:10) with both measurement runs after it (00:38:34 and
00:39:26, 52 seconds apart). Defines load once at startup, so both runs read
the same values from memory. Identical readings were therefore guaranteed
regardless of what the file on disk said - the comparison measured nothing.

Caught only because Matte noticed the console had echoed the script instead
of running it, which prompted a check of execution timestamps.

**Lesson: an A/B on defines requires TWO GAME LAUNCHES, and the launch
count must be verified in the log before comparing.** Editing the file
between runs changes nothing until a restart. Both defines return to Tier 1.

## Tier 1 - LOADS ONLY (existence proven, effect unknown)

Registered, lint-clean, and read back exactly after a restart via
`GetDefine`, so the engine definitely stores them. Nothing more is claimed.
No script-readable handle exists for these, so behaviour is not measurable
from the console.

`NAI.AI_ARMY_MAINTENANCE_UTILITY`, `NAI.AI_LIBERATE_SLAVES_DESIRE_BASE`,
`NAI.AI_MILITARY_ASSIGNMENT_STRENGTH_FACTOR`,
`NAI.BASE_CASUS_BELLI_WARGOAL_DESIRE`,
`NAI.LOAN_INTEREST_RATE_VS_BANK_LOAN_INTEREST_MULTIPLIER`,
`NAI.SELL_PROVINCE_DEBT_YEARS_OF_INCOME`,
`NCountry.REBEL_CONTROL_CHANGE_LOSS`,
`NMercenary.MERCENARY_DISTANCE_CAP`,
`NAI.AI_RIVAL_STRENGTH_DIFFERENCE_LIMIT`,
`NEconomy.GROWTH_FROM_FOOD_MULTIPLIER`,
`NEconomy.REPLACE_OBSOLETE_BUILDING_SPEED_INCRASE`,
`NWar.WAR_WORTH_DEVELOPMENT_RGO`

## Tier 0 - VALUE READ ONLY (never override-tested)

Confirmed to exist with a non-zero default via `GetDefine`, but never set by
a test mod. Graphics defines, deliberately left alone so nothing visual
broke.

`NCityGraphics.IMPOSTOR_WALL_MESH_SCALE` (3.125),
`NCityGraphics.MIN_RELATIVE_SIZE_FOR_LOCKED_EDGES` (0.8),
`NCityGraphics.WALL_NEW_VERTEX_MINIMUM_DISTANCE` (0.5),
`NCityGraphics.TOWER_SAFE_DISTANCE_TO_GATE` (1),
`NCityGraphics.WALL_MESH_SCALE` (1),
`NBorder.MAX_ZOOM_STEP_CROSSING_PENALTY` (-1),
`NGraphics.BUILDING_PERCENTAGE_ZOOM_OUT_STEP` (9),
`NGraphics.TERRAIN_MULTIPLICATION_START` (350),
`NGraphics.TERRAIN_MULTIPLICATION_END` (1200),
`NMapName.RENDER_AFTER_NAMES_ZOOM` (6)

## The headline

**ONE define behaviourally tested (DIPLOMATIC_RANGE), and it is inert.** One data point is not a pattern, but combined with 'vanilla never sets
them' the working hypothesis is that the set is **vestigial** -
left in the registry after the code that read them was removed. That is
exactly what "vanilla never sets them" was quietly telling us from the
start.

Anything published about these must say "registered and loaded" and must
NOT say "usable".
