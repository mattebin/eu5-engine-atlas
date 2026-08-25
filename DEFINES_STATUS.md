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

## Tier 2 - NO EFFECT DETECTED (properly tested, handles may be insensitive)

| define | handle | 0 | 9999 |
|---|---|---|---|
| `NMercenary.MERCENARY_DISTANCE_CAP` | world count of `has_mercenaries` | over 400 | over 400 |
| `NAI.AI_RIVAL_STRENGTH_DIFFERENCE_LIMIT` | world count of `can_rival` | 100-400 | 100-400 |

**This test is valid** - two verified game launches (00:43:10 with zeros,
00:45:50 with 9999), each with its measurement run after it, launch
timestamps checked in debug.log before drawing any conclusion.

Kept below Tier 3 because the handles may simply not be sensitive to these
defines: `has_mercenaries` might not consult a distance cap at all. Absence
of a signal through one handle is weaker than the `DIPLOMATIC_RANGE` result,
where the handle was the exact mechanic the define names.

### An earlier version of this section was WRONG and was retracted

The first attempt reported the same conclusion from a comparison that never
happened: only one launch occurred, so both runs read identical values from
memory. Defines load once at startup, so editing the file between runs
changes nothing.

Two habits came out of that, both now standard here:
**verify the launch count in the log before comparing**, and remember that
**debug.log resets on every launch**, so cumulative counts mislead - compare
timestamps, not totals.

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
