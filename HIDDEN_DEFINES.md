# Defines the engine registers that vanilla never sets

**45 of 2,841** engine-registered defines are absent from all 10 vanilla defines files. A mod can set these the same way it sets any other define, and `eu5lint` rule S002 will accept them, because they are real registry entries.

> **Corrected 2026-08-26: the true numbers are 54 of 2,975.** A UTF-8 BOM
> hid every block declared on line 1 of a defines file (NGame, NCamera,
> NMapEditor, NJominiIcons) from the original extraction, adding 9 hidden
> defines (camera-debug/map-editor/icon plumbing), and 33 more defines live
> in blocks no vanilla file declares at all. Canonical data:
> `defines_all.json`; story: [CATALOGUE.md](CATALOGUE.md). The table below
> is the original 45.

> Registered does not mean wired to anything. A define can exist in the registry and be read by no code path. Test before shipping.

| block | define |
|---|---|
| `NAI` | `AI_ARMY_MAINTENANCE_UTILITY` |
| `NAI` | `AI_LIBERATE_SLAVES_DESIRE_BASE` |
| `NAI` | `AI_MILITARY_ASSIGNMENT_STRENGTH_FACTOR` |
| `NAI` | `AI_RIVAL_STRENGTH_DIFFERENCE_LIMIT` |
| `NAI` | `BASE_CASUS_BELLI_WARGOAL_DESIRE` |
| `NAI` | `LOAN_INTEREST_RATE_VS_BANK_LOAN_INTEREST_MULTIPLIER` |
| `NAI` | `SELL_PROVINCE_DEBT_YEARS_OF_INCOME` |
| `NBorder` | `MAX_ZOOM_STEP_CROSSING_PENALTY` |
| `NCityGraphics` | `IMPOSTOR_WALL_MESH_SCALE` |
| `NCityGraphics` | `MIN_RELATIVE_SIZE_FOR_LOCKED_EDGES` |
| `NCityGraphics` | `TOWER_SAFE_DISTANCE_TO_GATE` |
| `NCityGraphics` | `WALL_MESH_SCALE` |
| `NCityGraphics` | `WALL_NEW_VERTEX_MINIMUM_DISTANCE` |
| `NCountry` | `REBEL_CONTROL_CHANGE_LOSS` |
| `NDiplomacy` | `DIPLOMATIC_RANGE` |
| `NDynasty` | `TreeSettingsDEFAULT_COLOR` |
| `NDynasty` | `TreeSettingsDISABLED_COLOR` |
| `NEconomy` | `GROWTH_FROM_FOOD_MULTIPLIER` |
| `NEconomy` | `REPLACE_OBSOLETE_BUILDING_SPEED_INCRASE` |
| `NGameIcons` | `NAVAL_DOCTRINES_ICON_PATH` |
| `NGameIllustrations` | `UNIT_TYPE_OVERVIEW_ILLUSTRATION_MASK_PATH` |
| `NGraphics` | `BUILDING_PERCENTAGE_ZOOM_OUT_STEP` |
| `NGraphics` | `TERRAIN_MULTIPLICATION_END` |
| `NGraphics` | `TERRAIN_MULTIPLICATION_START` |
| `NJominiGraphics` | `NULL_SCHEMATIC` |
| `NMapColors` | `MAP_AI_AGGRESSIVE` |
| `NMapColors` | `MAP_AI_CAUTIOUS` |
| `NMapColors` | `MAP_AI_DEFENSIVE` |
| `NMapColors` | `MAP_AI_EXPANSIONIST` |
| `NMapColors` | `MAP_AI_FRIENDLY` |
| `NMapColors` | `MAP_AI_ISOLATIONIST` |
| `NMapColors` | `MAP_AI_OPPORTUNISTIC` |
| `NMapMarker` | `ZOOM_STEP_RANGE_CITY_DETAILS` |
| `NMapName` | `RENDER_AFTER_NAMES_ZOOM` |
| `NMercenary` | `MERCENARY_DISTANCE_CAP` |
| `NSunSettings` | `NOON_X_OFFSET` |
| `NText` | `ColoringNEGATIVE` |
| `NText` | `ColoringNEUTRAL` |
| `NText` | `ColoringPOSITIVE` |
| `NText` | `FormattingEFFECT_BASE_INDENTATION` |
| `NText` | `FormattingINDENTATION_PER_DEPTH` |
| `NText` | `FormattingTRIGGER_BASE_INDENTATION` |
| `NUnitGraphics` | `BASE_UNIT_SCHEMATIC` |
| `NVisibleLocationsGfx` | `PLAGUE_MAX_ZOOM_STEP` |
| `NWar` | `WAR_WORTH_DEVELOPMENT_RGO` |
