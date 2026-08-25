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
