# Verified in game (1.3.11, 2026-08-25)

First live probe. Every result below is backed by an armed instrument: the
probe's first line is a deliberately fake effect, and the run is only
trusted because that fake produced `Unknown effect` in `error.log`. Without
that, silence would prove nothing.

## The decisive contrast

| script line | engine response | verdict |
|---|---|---|
| `zzz_atlas_sabotage_not_a_real_effect` | **`Unknown effect`** | control behaved correctly |
| `sort_local_variable_list` | `Expected opening bracket`, then **`Order not set for sorting a variable list`** | REAL, implemented |
| `change_global_variable` | `Variable not of the 'value' scope type. Type: empty` | REAL, type-validating |
| `clamp_global_variable` | same type validation | REAL |
| `round_global_variable` | same type validation | REAL |
| `post_audio_event` | `Expected opening bracket` | REAL, wants a block |
| `clear_variable_map` | no complaint | accepted as written |
| `add_internal_flag` | no complaint | accepted as written |

Not one undocumented keyword returned `Unknown effect`. The engine knows
what sorting a variable list *means* and is asking for the sort order, which
a registry stub could not do.

## Confirmed working, with correct semantics

Proven by unique sentinel strings appearing in `debug.log`, so execution
demonstrably reached each line, and each test had a known answer:

- **`debug_log`** - writes to `debug.log` with the script file and line
  number. A working, undocumented debugging tool for modders.
- **`has_multiple_players`** - correctly false in single-player.
- **`has_game_started`** - correctly true.
- **`nand`** - nand of two falses correctly evaluated true.

## Notes for the next probe

- Argument shapes are still unknown for several effects. `change_global_variable`
  and friends need a variable that already holds a *value* type;
  `sort_local_variable_list` needs a block with an order; `post_audio_event`
  needs a block.
- `debug_log` writes to **`debug.log`**, not `game.log`.
- **Logs are truncated on every game launch.** A reader that seeks to a saved
  byte offset will land past EOF and silently report nothing. This bit us on
  the first read of this very probe.

---

# Probe 3 (2026-08-25): the variable API WORKS, with confirmed syntax

Split into three files because probe 2 taught us that **one parse error
aborts the entire file** - probe 2's unconditional first `debug_log` never
ran. Each file below armed its own sabotage line, and all three armed
correctly.

## Confirmed working, with proven arithmetic

Values were written by effects and read back through triggers - a different
mechanism - and every test had a single correct answer. The `= 999`
negative control stayed silent, so the triggers discriminate.

| syntax | proof |
|---|---|
| `set_global_variable = { name = X value = 5 }` | `has_global_variable` returned true |
| `change_global_variable = { name = X add = 3 }` | read back as exactly **8** |
| `clamp_global_variable = { name = X max = 6 }` | read back as exactly **6** |
| `round_global_variable = { name = X nearest = 1 }` | 7.4 read back as exactly **7** |

## Lists hold SCOPES, not values

| syntax | proof |
|---|---|
| `add_to_global_variable_list = { name = X target = c:FRA }` | list created |
| `has_global_variable_list = X` | true |
| `is_target_in_global_variable_list = { name = X target = c:FRA }` | found it |

## Maps are keyed by SCOPES

| syntax | status |
|---|---|
| `add_to_global_variable_map = { name = X key = c:FRA value = c:ENG }` | **works** - `has_global_variable_map` confirms the map exists |
| `is_key_in_global_variable_map = { name = X key = c:FRA }` | key argument rejected: `Failed to read 'key'`. Effect side works, trigger side needs a different key form |

## Trap: "variable not set" errors that are not failures

`error.log` shows `Failed to fetch variable for 'a3_num' due to not being
set` for the very lines whose sentinels PASSED. These come from a static
validation pass that cannot see console-set state; execution succeeded
regardless. **Do not read those as failures** - only sentinels and read-back
values settle it.

---

# Probes 4-6: maps are writable and countable, but NOT key-queryable

## What works

| syntax | proof |
|---|---|
| `add_to_global_variable_map = { name = X key = c:FRA value = c:ENG }` | map created |
| `add_to_local_variable_map = { ... }` (in a country scope) | map created |
| `has_global_variable_map = X` / `has_local_variable_map = X` | true |
| `global_variable_map_size = { name = X value = 1 }` | **size read back as exactly 1** |
| `local_variable_map_size = { name = X value = 1 }` | **size read back as exactly 1** |

## What does not

`is_key_in_global_variable_map` and `is_key_in_local_variable_map` reject
**every** key form tried, always with the same `Failed to read 'key'`:

1. `key = c:FRA` (a scope, the exact form the effect accepts)
2. `target = c:FRA`
3. `key = scope:saved_scope`
4. `key = this`, evaluated inside that scope
5. `key = 1` (numeric)
6. `key = flag:c_fra`
7. `key = global_var:holder`
8. `key = c:ENG` on a **local** map
9. `key` and `value` supplied together

`is_value_in_global_variable_map` fails the same way on `value`.

**Conclusion: the key reader for map-query triggers looks unimplemented in
1.3.11.** The effect side stores a scope key happily and the size trigger
counts entries, so the storage is real - only the lookup path is dead. Nine
attempts across both scope tiers is enough to stop guessing.

## What this means for a modder

Variable maps are usable as **counted sets** (add entries, check existence,
read size) but not as lookup tables. Lists are the better tool today:
`is_target_in_global_variable_list` is confirmed working.

## Validation noise, again

`local_variable_map_size trigger [ Could not find list ... ]` appears in
error.log for a line whose sentinel PASSED. Static validation cannot see
console-created state. Judge by sentinels, not by error.log.

---

# Probe 7: sort_global_variable_list syntax

`order` takes a **script value**, not a direction keyword. Probe 1 said
"Order not set for sorting a variable list"; probe 2's `order = ascending`
produced "Cannot read [ascending] as a script value". `ascending` and
`descending` are not script tokens at all - the only occurrences in the
binary are FBX and SDL strings.

| form | result |
|---|---|
| `sort_global_variable_list = { name = X order = 1 }` | **accepted**, and the list verified intact afterwards |
| `sort_global_variable_list = { name = X order = { value = 1 } }` | **accepted** |
| `order = cabinet_stability_investment` (named script value) | **silent total rejection** |

## Trap: a bad script value kills the file with NO error

The named-script-value file executed nothing - not even its first
`debug_log` - while its sabotage line still logged, proving the file was
read. **error.log contained no explanation whatsoever.** `cabinet_stability_
investment` is real, but lives in `main_menu/common/script_values/`, so it
is presumably not resolvable from in-game script.

A loud error is recoverable; this is not. If a probe file mysteriously does
nothing, suspect an unresolvable script value reference before anything else.

## Not proven

Whether the sort actually ORDERS correctly. There is no confirmed way to
read an element back out of a variable list, so only syntax acceptance is
established here. Sorting by a constant is also degenerate by definition -
a real ordering test needs a per-element script value.

---

# Probe 8: iteration works, and sorting is CORRECT (descending)

## A fifth registry the static extraction missed

List iterators are **composed at runtime** from a prefix plus a list type, so
they never appear as literal strings in the binary - `every_country` byte-
searches to **zero hits** despite being real script. Only the parts exist:
`every_` (20), `ordered_` (3), `in_list` (2), `in_global_variable_list` (1).
Vanilla uses `every_in_global_list` 24 times, `every_in_list` 11 times.

**Any future registry hunt must account for composed keywords.** The
effect/trigger/scope/GUI extractions are all literal-string based and would
each miss this class.

## Reading list elements back

```
every_in_global_list = {
	variable = my_list
	<effects on each element>
}
```

Confirmed iterating both elements of a two-country list.

## Sorting is real and DESCENDING by default

```
sort_global_variable_list = { name = X order = var:my_key }
```

Test: three countries given distinct keys (ENG=3, FRA=1, CAS=2), added in
insertion order **ENG, FRA, CAS**, sorted, then read back.

- observed after sort: **ENG, CAS, FRA**  =  keys 3, 2, 1
- insertion order was ENG, FRA, CAS, so the list genuinely changed
- the result is exact **descending** order

This corrects the earlier "not proven" note. Sorting by a constant was
degenerate and told us nothing; sorting by a per-element variable proves it
works. `order` accepts `var:<name>` evaluated in each element's scope.

---

# Probe 9: undocumented LIST TYPES confirmed, four returning live data

Negative control `every_totally_fake_list_type_xyz` correctly reported
`Unknown effect`, so acceptance below is meaningful.

| iterator | result |
|---|---|
| `every_other_core_country` | accepted, **1 element** |
| `every_country_in_hierarchy` | accepted, **2 elements** |
| `every_friendly_country` | accepted, **1 element** |
| `every_hostile_country` | accepted, **1 element** |
| `every_country_annexing_us` | accepted, empty |
| `every_country_we_are_annexing` | accepted, empty |
| `every_country_with_succession_law` | accepted, empty |
| `every_area_with_owned_province` | accepted, empty |

Empty is not failure: `country_annexing_us` legitimately has no members when
nobody is annexing you. The four with elements prove the type resolves to
real game data, not just a parsed name.

All four prefixes should apply (`every_`, `any_`, `random_`, `ordered_`),
since that is how vanilla uses its own 253 base names - though only
`every_` was tested here.

**`every_friendly_country` and `every_hostile_country` are the most
immediately useful**: AI-facing country classifications no mod has ever
iterated.


---

# Batch verification: every undocumented effect and trigger is REAL

168 keywords tested in bare form. Verdict rule, established across probes
1-9: the engine reports `Unknown effect X` / `Unknown trigger type: X` for
something it does not know, but a **semantic** error (wrong arguments, missing
block, type mismatch) for something real. So existence can be settled without
knowing correct syntax.

| | result |
|---|---|
| Effects tested | **34 of 34 - ALL REAL** |
| Triggers tested | **109 of 134 - ALL REAL** |
| Flagged unknown by the engine | **0** |
| Still untested (chunk aborts) | 25 |

Both deliberate fakes were correctly flagged, so the instrument works in
effect position and trigger position.

## Two instrument bugs found and fixed here

**1. An unknown trigger evaluates as TRUE.** The fake trigger
`totally_fake_trigger_xyz` logged `Unknown trigger type:` *and its sentinel
still fired*. A sentinel therefore never proved a trigger was real - fakes
fire too. Only error.log settles trigger existence. Any earlier reading that
leaned on trigger sentinels was unsound.

**2. The two message formats differ.** Effects report `Unknown effect X`,
triggers report `Unknown trigger type: "X"`. A pattern written for the effect
form silently matches no trigger at all, which produced a confident but
meaningless "0 unknown triggers" until the fake-trigger control exposed it.

Neither bug would have been visible without controls in **both** positions.
Every future probe needs a fake of the same kind as the thing being tested.

## Still untested (25)

Chunks died on triggers whose bare `X = yes` form is fatally malformed
because they require blocks or value comparisons - `nand`,
`variable_map_size`, `is_value_in_local_variable_map`,
`area_average_control` and others. `nand` is already confirmed working in
probe 1, so these are syntax deaths, not evidence against the keywords:

`any_false`, `area_average_control`, `available_army_levy_percentage`, `available_navy_levy_percentage`, `besieger_strength`, `bond_capacity`, `can_start_tutorial_lesson`, `colonial_charter_distance`, `is_value_in_local_variable_map`, `join_organization_ai_desire`, `language_population_in_country`, `liturgical_language_utility`, `local_variable_map_size`, `nand`, `num_bonds`, `num_cabinet_capable_characters`, `num_explorations_including_in_construction`, `num_locations_affected`, `num_of_active_parliament_agendas`, `num_of_locations_with_high_conquer_desire`, `variable_map_size`, `vote_type`, `war_score_of_country_side`, `yearly_gold`, `yearly_sailors`

---

# COMPLETE: 168 of 168 undocumented keywords verified real

The final 25 triggers passed once each was given a plausible argument form
instead of a bare `= yes`: value triggers as `X > 0`, block triggers with a
block. All five chunks ran to completion, so the earlier aborts were purely
malformed-syntax deaths, never evidence against the keywords.

| | |
|---|---|
| Undocumented **effects** verified real | **34 / 34** |
| Undocumented **triggers** verified real | **134 / 134** |
| Flagged unknown by the engine | **0** |
| Independent fake controls correctly caught | **3** (one effect, two triggers) |

Every result rests on a control of the *same kind* as the thing tested, after
the trigger-position control exposed that assumption transferring from
effect-position was unsafe.

## What is now established end to end

- The engine registers **553 effects, 1,270 triggers, 283 scope links,
  10,828 GUI functions, 2,841 defines**, plus a composed list-type class.
- Vanilla script demonstrates only a fraction: **168** effects/triggers and
  **45** defines are never used anywhere in the game's own files.
- Every one of those 168 is real, confirmed in game.
- Working syntax is documented for variables, lists (including iteration and
  descending sort), maps (storage and counting), and 8 undocumented list
  types, 4 of which return live data.

---

# GUI data functions, pass 1 (bare / global entry points)

`debug_log` runs its string through the text system, so `[Func]` resolves.
`[GetPlayer.GetName]` returned **Hungary** and `[GetPlayer.GetCapital.GetName]`
returned **Buda** - real data, and chained calls work. Unknown functions log
`Could not find data system function 'X'`. This makes all 3,828 GUI
functions testable from the console with no mod at all.

| | |
|---|---|
| Tested (editor/asset names filtered out) | 3,828 |
| Resolve **bare** as global entry points | **395** |
| Not found bare | 3,433 |

Bare failure is NOT proof a function is fake - most are methods that need an
object (`GetName` is real but meaningless without a country). Pass 2 tests
them against `GetPlayer`.

Useful-looking globals confirmed: `CanBribeMercenary`, `CanBuildRoads`,
`CanDetachLevies`, `CanDetachMercenaries`, `CanOpenBuilding`,
`CanPlayerDoGenericAction`, `CanViewColonyScreen`, `CanChangeChildEducation`.

## TRAP: error.log ROTATES, and it invalidated a result

The first reading of this pass reported **2,392 resolved**. That was wrong.
`error.log` rotates into `error.1.log`, `error.2.log` ... when it grows, and
three of six chunks had their errors rotated out mid-run. Their functions
showed no error and were counted as resolved.

The tell was that GB1-GB3 reported **0/700** not-found while GB4-GB6 reported
~600/700 - impossible for an alphabetical split. Reading the whole rotated
chain gives a consistent ~630/700 across every chunk.

**Always read error.log AND its rotated siblings.** A single-file read
silently loses data, and silently-lost data reads as success.


---

# GUI data functions, final

| category | count |
|---|---|
| Tested (editor/asset names filtered out) | 3,828 |
| Resolve **bare** = global entry points | **395** |
| Resolve as **`GetPlayer.X`** = country methods | **90** |
| Neither | 3343 |

The large remainder is **not** evidence of fake functions. These are methods
on other types - market, building, character, unit, province - and testing
them needs the right receiver object, not a blanket `GetPlayer`. Only ~2% of
each chunk resolved against a country, which is exactly what a type-scoped
API looks like.

## Confirmed country methods worth a modder's attention

`CanColonize`, `GetActiveDisasters`, `GetActiveRebels`,
`GetBankruptcyEndDate`, `GetBondInterest`, `GetBondSize`,
`GetArmyLevyPowerInfo`, `GetCourtSpendingCost`, `GetCapitalOrParliament`,
`GetAiUtility`, plus a family of localisation variants
(`GetAltName`, `GetAltAdjective`, `GetAltLongName`, and their
`...WithFlag` forms).

## Confirmed global entry points worth attention

`CanBribeMercenary`, `CanBuildRoads`, `CanDetachLevies`,
`CanDetachMercenaries`, `CanOpenBuilding`, `CanPlayerDoGenericAction`,
`CanViewColonyScreen`, `CanChangeChildEducation`.

## Method note: timestamps, not offsets

Because `error.log` rotates mid-run, chunk results must be isolated by
**timestamp cutoff**, not by byte offset. Two readings in this pass were
wrong before that was applied - one counted 700 rotated-away functions as
successes, the other compared against a cumulative set in which no function
could ever clear. Both produced confident, plausible, wrong numbers.


---

# GUI functions: typed receivers (final tally)

Receivers proven reachable from the console: **capital/location** (Buda),
**province**, **market** (Pest Market), **area** (Transdanubia), **region**
(Carpathia), **culture** (Hungarian), **religion** (Catholicism), **map
mode**. Ruler, heir, government and the selected-object accessors do NOT
exist under those names.

| resolution path | count |
|---|---|
| Global entry points (bare `[Func]`) | **395** |
| Country methods (`GetPlayer.X`) | **90** |
| Typed receivers (location, market, culture, province, map mode) | **92** |
| **Total confirmed usable** | **577** |
| Needing receivers not yet reachable | 3251 |

The remainder is **not disproven**. Those are methods on types this probe
cannot construct from the console - building, unit, character, war, trade
node and so on. Reaching them needs an accessor chain that produces such an
object, which is a separate hunt.

## Location API worth a modder's attention

`GetActualGarrison`, `GetBlockadeProgress`, `GetBlockadeForceInfo`,
`GetClosestPort`, `GetDevastationEffect`, `GetDiseaseInfectionPercentage`,
`GetLocationSize`, `GetExports`, `CalcGoodsOutput`,
the `GetIntegration` family (`GetIntegration`, `GetIntegrationETA`,
`GetIntegrationProgress`, `GetIntegrationSpeed`) and the
`GetMaxRGOWorkers` family (`GetMaxRGOWorkersForUI`,
`GetMaxRGOWorkersLevel`, `GetMaxRGOWorkersPercentage`,
`CanIncreaseMaxRGOWorkers`).

The RGO worker functions are directly relevant to the Community Fixes Raw
Materials Finder.

---

# Scope links: 52 of 52 accepted

Tested as `link = { ... }` in country scope. Fake control
`totally_fake_scope_link_zz` was rejected and did not enter, so acceptance
below is meaningful. All four chunks ran to completion.

| | |
|---|---|
| Undocumented scope links tested | 52 |
| Accepted by the engine | **52** |
| Flagged unknown | **0** |
| Entered a scope containing live data | **6** |

## Entered with real content

`largest_army`, `largest_navy`, `country_stance`, `country_color`,
`active_chivalric_order`, `max_great_powers`.

`largest_army` and `largest_navy` are the useful pair - a direct handle on a
country's biggest force, which script currently has no documented way to
reach.

The remaining 46 were accepted but empty, which is correct for a
single-country test: links like `present_overlord` or `country_annexing_us`
have nothing to enter unless that relationship exists.

## Caveat

`yes` appears in the entered list. That is almost certainly an artifact of
the scope extraction picking up a bare token, not a real scope link. Treat
any single-word generic entry in `scopes.json` with suspicion.

---

# GUI function TYPES (static work, no probes needed)

The missing piece for a task-oriented catalogue: which type does each
function belong to.

Two sources combined:

1. **Vanilla `.gui` usage.** In Jomini you write `[MapMode.IsActive]`, where
   the prefix IS the datacontext type. 483 vanilla files yield **938 types
   and 7,197 Type.Method pairs** - ground truth.
2. **Registration adjacency.** Functions registered next to each other belong
   to the same type: `SetMapMode` sits beside `IsSet`, `IsActive` beside
   `IsToggleAction`. Walking 18,535 registrations in address order and
   spreading types from known anchors covers the rest.

| tier | count | reliability |
|---|---|---|
| Type **confirmed** from vanilla usage | **3,801** | exact |
| Type **inferred** by adjacency | **4,606** | **80% measured** |

## The 80% is measured, not asserted

600 known functions were held out, their types hidden, then predicted from
neighbours only: **461 correct, 115 wrong, 24 too far from any anchor to
guess**. So adjacency labels are a strong hint and must be presented as such
in any tool, never as fact.

## Largest type groups

`Location` (425), `Country` (283), `Player` (204),
`InternationalOrganizationsView` (159), `Character` (154),
`WarLateralView` (152), `Unit` (130), `Market` (89), `Building`, `LocationView`.

This is the data a searchable catalogue needs: a modder asking "what can I do
with a Location" gets 425 candidate functions, 250 of them confirmed by
vanilla usage.

---

# Scope context (static inference)

Vanilla wraps effects in scope-changing blocks, so the enclosing block
reveals the context an effect runs in. Scanning 2,346 in-game script files
and tracking the scope stack:

| | |
|---|---|
| Keywords with an observed scope type | **1,616** |
| Of the 168 **undocumented** keywords | **0** |

## The limitation, stated plainly

Zero is the expected answer and it matters: "undocumented" means vanilla
never uses these, so there is no usage to infer scope from. The keywords
this project exists to document are exactly the ones static scope inference
cannot reach.

46 of them carry a usable hint in the name (`create_navy_country_in_location`
-> location, `area_average_control` -> area, `create_num_sub_unit` -> unit),
but a hint is not a fact.

**Scope for undocumented keywords must be tested in game**: run each effect
inside a country scope and a location scope, and see which one errors. That
is a probe round, not a static pass.

The 1,616 observed entries remain useful as a general scope reference for
modders working with documented vocabulary.

---

# Scope requirements for all 34 undocumented effects (SOLVED)

Static inference could not reach these (vanilla never uses them), but the
engine volunteers the answer. Calibration with two known effects established
the signature:

```
add_core: Inconsistent effect scopes (country vs. location)
add_country_modifier: Inconsistent effect scopes (location vs. country)
```

It names **both** the current scope and the required one, so a single pass at
country scope documents everything. All 3 chunks armed; all 34 effects
reached.

## Require a specific scope (9)

| effect | scope |
|---|---|
| `add_dynasty_modifier` | dynasty |
| `add_recovered_army_levy_percentage` | province |
| `add_recovered_navy_levy_percentage` | province |
| `change_art_worth` | work_of_art |
| `set_art_worth` | work_of_art |
| `create_navy_country_from_province` | province |
| `create_navy_country_in_location` | location |
| `create_num_sub_unit` | location |
| `set_target_of_international_organization` | international_organization |

`work_of_art` is a scope type we did not know existed - revealed only by the
error message.

## Work at country scope (25)

`add_internal_flag`, `change_global_variable`, `clamp_global_variable`,
`round_global_variable`, `round_local_variable`, `clear_variable_map`,
`clear_global_variable_map`, `clear_local_variable_map`,
`clear_local_variable_list`, `remove_from_local_variable_map`,
`remove_list_local_variable`, `sort_local_variable_list`, `create_route`,
`custom_label`, `custom_description_no_bullet`, `post_audio_event`,
`set_automated_system`, `reverse_add_antagonism`, `debug_log`,
`debug_log_date`, `debug_log_scopes`, `random_log_scopes`, `test_log`,
`assert_read`, `stop_tutorial`.

## Method note: never compare log timestamps as strings

The first read of this round was polluted because the clock had just passed
midnight, and `"18:03" >= "00:05"` is true as text - so the filter matched
the entire previous day. Filter probe results by **filename**, which has no
rollover.

---

# GetDefine: an undocumented way to read any define in game

`define:` does NOT work as a trigger (all forms rejected). But the data
function does, through `debug_log` interpolation:

```
[GetDefine('NDiplomacy','TRUCE_YEARS')]   ->  5
```

**Two arguments, block then key.** The engine gave up the signature itself:
`Function 'GetDefine' expected 2 arguments, got 1`. No vanilla `.gui` file
uses this. It lets a modder read any live define value in game, which is
genuinely useful on its own.

## Hidden defines with confirmed non-zero defaults (10)

| define | value |
|---|---|
| `NCityGraphics.IMPOSTOR_WALL_MESH_SCALE` | 3.125 |
| `NCityGraphics.MIN_RELATIVE_SIZE_FOR_LOCKED_EDGES` | 0.8 |
| `NCityGraphics.WALL_NEW_VERTEX_MINIMUM_DISTANCE` | 0.5 |
| `NCityGraphics.TOWER_SAFE_DISTANCE_TO_GATE` | 1 |
| `NCityGraphics.WALL_MESH_SCALE` | 1 |
| `NBorder.MAX_ZOOM_STEP_CROSSING_PENALTY` | -1 |
| `NGraphics.BUILDING_PERCENTAGE_ZOOM_OUT_STEP` | 9 |
| `NGraphics.TERRAIN_MULTIPLICATION_START` | 350 |
| `NGraphics.TERRAIN_MULTIPLICATION_END` | 1200 |
| `NMapName.RENDER_AFTER_NAMES_ZOOM` | 6 |

## The limitation, and why the zeros prove nothing

**A fake define also returns 0.** `[GetDefine('NDiplomacy','NOT_REAL_QQ')]`
returned `0`, not an error. So every define reading 0 - including the
interesting AI ones (`AI_MILITARY_ASSIGNMENT_STRENGTH_FACTOR`,
`BASE_CASUS_BELLI_WARGOAL_DESIRE`, `DIPLOMATIC_RANGE`,
`GROWTH_FROM_FOOD_MULTIPLIER`) - is ambiguous from this test alone.

Their existence is still established by the RTTI extraction; only their
*value* is unconfirmed. A 0 default is plausible for disabled tuning
factors, but this instrument cannot prove it.

To settle those, a mod would have to set them to distinctive values and
GetDefine read them back after a restart - which remains backlog work.

## Note on the current session

`TRUCE_YEARS` read as **5** (vanilla) rather than the 3 Community Fixes
sets, and error.log shows `Could not find mod`. The junction removal left
the playset pointing at a missing folder, so this session is effectively
running unmodded.
