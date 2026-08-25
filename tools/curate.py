import json, re, sys, pathlib
v = json.load(open("verified.json", encoding="utf-8"))
cls = {r["keyword"]: r["impl_class"] for k in v for r in v[k]}
kind = {r["keyword"]: k for k in v for r in v[k]}

GROUPS = [
 ("Variables, lists and maps - a whole data-structure API vanilla never touches",
  ["change_global_variable","clamp_global_variable","round_global_variable",
   "round_local_variable","clear_variable_map","clear_global_variable_map",
   "clear_local_variable_map","clear_local_variable_list",
   "remove_from_local_variable_map","remove_list_local_variable",
   "sort_local_variable_list","has_local_variable_map",
   "is_value_in_local_variable_map","local_variable_map_size","variable_map_size"]),
 ("Tooltips and presentation",
  ["custom_label","custom_description_no_bullet","current_tooltip_depth",
   "post_audio_event"]),
 ("Debugging - painful territory in Paradox modding",
  ["debug_log","debug_log_date","debug_log_scopes","random_log_scopes",
   "test_log","debug_log_details"]),
 ("Creating things",
  ["create_num_sub_unit","create_navy_country_in_location",
   "create_navy_country_from_province","create_route","add_dynasty_modifier",
   "set_automated_system"]),
 ("Economy queries",
  ["location_net_building_profit","production_method_profit","yearly_gold",
   "yearly_sailors","food_production","hire_price","mercenary_hire_cost",
   "mercenary_maintenance_cost","bond_capacity","num_bonds",
   "higher_temporary_taxes_needed","total_payment_contribution"]),
 ("Population and society queries",
  ["population_in_area","province_pop_type_population","culture_percentage_in_area",
   "heathen_population_fraction","heretic_population_fraction",
   "language_population_in_country","religion_group_population_in_country",
   "unemployed_pops_of_pop_type_in_location","unemployed_pops_of_pop_type_in_province",
   "unfilled_jobs_in_province_percentage","peasant_enfranchisment"]),
 ("Military queries",
  ["combat_side_strength","besieger_strength","unit_strength","is_bombard_phase",
   "province_army_levy_size","province_navy_levy_size","regular_navy_size",
   "available_army_levy_percentage","available_navy_levy_percentage",
   "add_recovered_army_levy_percentage","add_recovered_navy_levy_percentage",
   "lowest_war_score","war_score_of_country_side"]),
 ("Geography and control queries",
  ["area_average_control","province_average_max_control","distance_to_area",
   "harbor_capacity_in_area","num_province_definitions_in_area",
   "location_num_holy_sites","num_locations_affected","lowest_prosperity"]),
 ("Diplomacy queries",
  ["get_opinion","get_trust_equilibrium","get_antagonism","reverse_add_antagonism",
   "used_diplomatic_capacity","diplomatic_capacity_without_maintenance",
   "diplomatic_capacity_of_new_relation","in_marriage_union_with",
   "is_annexing_any_country","is_being_annexed_by","num_relations_above_limit",
   "favors_needed_to_annul_relations_with","is_mercenary_of","is_no_cb",
   "subject_level","is_subject_type_annullable"]),
 ("Logic and flow",
  ["nand","any_false","random_integer","has_game_started","has_multiple_players"]),
 ("AI weighting - for anyone modding AI behaviour",
  ["modifier_utility","join_organization_ai_desire","conquistador_utility",
   "create_market_utility","destroy_market_utility","relocate_market_utility",
   "court_language_utility","liturgical_language_utility",
   "employment_system_desire","conquer_area_preference","powerful_ally_weight",
   "union_partner_weight","ai_parliament_issue_resolution_vote_bias",
   "num_of_locations_with_high_conquer_desire","religious_view_impact"]),
]

listed = {k for _, ks in GROUPS for k in ks}
allkw = set(cls)
L = ["# Modder-useful undocumented capabilities\n\n",
     "Everything here is registered in `eu5.exe` and used by **no vanilla ",
     "script file**, so it is currently undiscoverable by normal modding.\n\n",
     "## How each entry was verified, in code only\n\n",
     "1. The keyword string exists in the binary (raw byte search, with a fake ",
     "keyword as a negative control that correctly finds nothing).\n",
     "2. It has a static initializer that interns the name and calls the effect ",
     "or trigger registrar - the same structure as known-good keywords like ",
     "`refresh_map_colors`.\n",
     "3. It appears in none of the 2,806 vanilla script files.\n",
     "4. Where a one-to-one implementing class exists, it is named below. A dash ",
     "means no 1:1 class, which is normal for keywords served by shared or ",
     "templated classes - it is not evidence against the keyword.\n\n",
     "**Not yet run in game.** Registration proves the engine knows the keyword, ",
     "not that it works in a given scope or takes the arguments you expect.\n"]
for title, ks in GROUPS:
    ks = [k for k in ks if k in allkw]
    if not ks:
        continue
    L.append(f"\n## {title}\n\n| keyword | kind | implementing class |\n|---|---|---|\n")
    for k in sorted(ks):
        L.append(f"| `{k}` | {kind[k]} | {cls[k] or '-'} |\n")
rest = sorted(allkw - listed)
L.append(f"\n## Not curated ({len(rest)})\n\nTutorial hooks, asserts and "
         "internals judged not useful for mods:\n\n")
L.append(", ".join(f"`{r}`" for r in rest) + "\n")
pathlib.Path("CURATED.md").write_text("".join(L), encoding="utf-8", newline="\n")
print(f"CURATED.md written: {len(listed & allkw)} curated, {len(rest)} set aside")
