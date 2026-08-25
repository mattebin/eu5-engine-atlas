"""Interpret the probe run. Fails loudly if the instrument was not armed."""
import json, pathlib, re
LOGS = pathlib.Path(r"C:\Users\Matte\Documents\Paradox Interactive\Europa Universalis V\logs")
base = json.load(open("probe_baseline.json", encoding="utf-8"))

def tail(name):
    p = LOGS / name
    if not p.exists():
        return ""
    with open(p, "rb") as f:
        f.seek(min(base.get(name, 0), p.stat().st_size))
        return f.read().decode("utf-8", errors="replace")

err, game = tail("error.log"), tail("game.log")
print(f"new error.log bytes: {len(err)} | new game.log bytes: {len(game)}\n")

SAB = "zzz_atlas_sabotage_not_a_real_effect"
armed = SAB in err
print("=" * 62)
print(f"INSTRUMENT ARMED: {armed}")
if not armed:
    print("  The deliberate fake effect produced NO error.")
    print("  => error.log is not capturing this run. Results below are VOID.")
print("=" * 62)

print("\nsentinels in game.log (proves execution reached that line):")
for s, meaning in [
    ("ATLAS_SENTINEL_debug_log_works_9f3a", "debug_log works at all"),
    ("ATLAS_SENTINEL_has_multiple_players_correctly_false_9f3a",
     "has_multiple_players evaluated, and correctly"),
    ("ATLAS_SENTINEL_has_game_started_true_9f3a", "has_game_started true"),
    ("ATLAS_SENTINEL_nand_of_two_false_is_true_9f3a", "nand computed correctly"),
]:
    print(f"   [{'HIT ' if s in game else 'miss'}] {meaning}")

PROBED = ["change_global_variable", "clamp_global_variable", "round_global_variable",
          "clear_variable_map", "sort_local_variable_list", "add_internal_flag",
          "post_audio_event", "has_multiple_players", "has_game_started", "nand"]
print("\nper-keyword errors in the new error.log slice:")
for k in PROBED:
    hits = [l for l in err.splitlines() if k in l]
    print(f"   [{'ERROR' if hits else ' ok  '}] {k:26} {hits[0][-70:] if hits else ''}")
print("\n  'ok' = the engine did not complain. That is parse-acceptance,")
print("  not proof the effect does anything. Sentinels are the real evidence.")
