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
