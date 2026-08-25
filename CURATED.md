# Modder-useful undocumented capabilities

Everything here is registered in `eu5.exe` and used by **no vanilla script file**, so it is currently undiscoverable by normal modding.

## How each entry was verified, in code only

1. The keyword string exists in the binary (raw byte search, with a fake keyword as a negative control that correctly finds nothing).
2. It has a static initializer that interns the name and calls the effect or trigger registrar - the same structure as known-good keywords like `refresh_map_colors`.
3. It appears in none of the 2,806 vanilla script files.
4. Where a one-to-one implementing class exists, it is named below. A dash means no 1:1 class, which is normal for keywords served by shared or templated classes - it is not evidence against the keyword.

**Not yet run in game.** Registration proves the engine knows the keyword, not that it works in a given scope or takes the arguments you expect.

## Variables, lists and maps - a whole data-structure API vanilla never touches

| keyword | kind | implementing class |
|---|---|---|
| `change_global_variable` | effect | - |
| `clamp_global_variable` | effect | - |
| `clear_global_variable_map` | effect | - |
| `clear_local_variable_list` | effect | - |
| `clear_local_variable_map` | effect | - |
| `clear_variable_map` | effect | - |
| `has_local_variable_map` | trigger | - |
| `is_value_in_local_variable_map` | trigger | - |
| `local_variable_map_size` | trigger | - |
| `remove_from_local_variable_map` | effect | - |
| `remove_list_local_variable` | effect | - |
| `round_global_variable` | effect | - |
| `round_local_variable` | effect | - |
| `sort_local_variable_list` | effect | - |
| `variable_map_size` | trigger | - |

## Tooltips and presentation

| keyword | kind | implementing class |
|---|---|---|
| `current_tooltip_depth` | trigger | CCurrentTooltipDepthTrigger |
| `custom_description_no_bullet` | effect | - |
| `custom_label` | effect | - |
| `post_audio_event` | effect | CPostAudioEventEffect |

## Debugging - painful territory in Paradox modding

| keyword | kind | implementing class |
|---|---|---|
| `debug_log` | effect | CDebugLogEffect |
| `debug_log_date` | effect | CDebugLogDateEffect |
| `debug_log_details` | trigger | - |
| `debug_log_scopes` | effect | - |
| `random_log_scopes` | effect | - |
| `test_log` | effect | CTestLogEffect |

## Creating things

| keyword | kind | implementing class |
|---|---|---|
| `add_dynasty_modifier` | effect | - |
| `create_navy_country_from_province` | effect | - |
| `create_navy_country_in_location` | effect | - |
| `create_num_sub_unit` | effect | CCreateNumSubUnitEffect |
| `create_route` | effect | - |
| `set_automated_system` | effect | CSetAutomatedSystemEffect |

## Economy queries

| keyword | kind | implementing class |
|---|---|---|
| `bond_capacity` | trigger | CBondCapacityTrigger |
| `food_production` | trigger | - |
| `higher_temporary_taxes_needed` | trigger | CHigherTemporaryTaxesNeededTrigger |
| `hire_price` | trigger | CHirePriceTrigger |
| `location_net_building_profit` | trigger | CLocationNetBuildingProfitTrigger |
| `mercenary_hire_cost` | trigger | CMercenaryHireCostTrigger |
| `mercenary_maintenance_cost` | trigger | CMercenaryMaintenanceCostTrigger |
| `num_bonds` | trigger | CNumBondsTrigger |
| `production_method_profit` | trigger | CProductionMethodProfitTrigger |
| `total_payment_contribution` | trigger | - |
| `yearly_gold` | trigger | - |
| `yearly_sailors` | trigger | - |

## Population and society queries

| keyword | kind | implementing class |
|---|---|---|
| `culture_percentage_in_area` | trigger | - |
| `heathen_population_fraction` | trigger | - |
| `heretic_population_fraction` | trigger | - |
| `language_population_in_country` | trigger | - |
| `peasant_enfranchisment` | trigger | - |
| `population_in_area` | trigger | CPopulationInAreaTrigger |
| `province_pop_type_population` | trigger | CProvincePopTypePopulationTrigger |
| `religion_group_population_in_country` | trigger | - |
| `unemployed_pops_of_pop_type_in_location` | trigger | - |
| `unemployed_pops_of_pop_type_in_province` | trigger | - |
| `unfilled_jobs_in_province_percentage` | trigger | - |

## Military queries

| keyword | kind | implementing class |
|---|---|---|
| `add_recovered_army_levy_percentage` | effect | - |
| `add_recovered_navy_levy_percentage` | effect | - |
| `available_army_levy_percentage` | trigger | - |
| `available_navy_levy_percentage` | trigger | - |
| `besieger_strength` | trigger | - |
| `combat_side_strength` | trigger | CCombatSideStrengthTrigger |
| `is_bombard_phase` | trigger | - |
| `lowest_war_score` | trigger | - |
| `province_army_levy_size` | trigger | CProvinceArmyLevySizeTrigger |
| `province_navy_levy_size` | trigger | CProvinceNavyLevySizeTrigger |
| `regular_navy_size` | trigger | CRegularNavySizeTrigger |
| `unit_strength` | trigger | - |
| `war_score_of_country_side` | trigger | - |

## Geography and control queries

| keyword | kind | implementing class |
|---|---|---|
| `area_average_control` | trigger | CAreaAverageControlTrigger |
| `distance_to_area` | trigger | - |
| `harbor_capacity_in_area` | trigger | CHarborCapacityInAreaTrigger |
| `location_num_holy_sites` | trigger | CLocationNumHolySitesTrigger |
| `lowest_prosperity` | trigger | - |
| `num_locations_affected` | trigger | CNumLocationsAffectedTrigger |
| `num_province_definitions_in_area` | trigger | CNumProvinceDefinitionsInAreaTrigger |
| `province_average_max_control` | trigger | CProvinceAverageMaxControlTrigger |

## Diplomacy queries

| keyword | kind | implementing class |
|---|---|---|
| `diplomatic_capacity_of_new_relation` | trigger | CDiplomaticCapacityOfNewRelationTrigger |
| `diplomatic_capacity_without_maintenance` | trigger | CDiplomaticCapacityWithoutMaintenanceTrigger |
| `favors_needed_to_annul_relations_with` | trigger | - |
| `get_antagonism` | trigger | - |
| `get_opinion` | trigger | - |
| `get_trust_equilibrium` | trigger | - |
| `in_marriage_union_with` | trigger | - |
| `is_annexing_any_country` | trigger | - |
| `is_being_annexed_by` | trigger | - |
| `is_mercenary_of` | trigger | - |
| `is_no_cb` | trigger | - |
| `is_subject_type_annullable` | trigger | - |
| `num_relations_above_limit` | trigger | - |
| `reverse_add_antagonism` | effect | - |
| `subject_level` | trigger | - |
| `used_diplomatic_capacity` | trigger | CUsedDiplomaticCapacityTrigger |

## Logic and flow

| keyword | kind | implementing class |
|---|---|---|
| `any_false` | trigger | - |
| `has_game_started` | trigger | CHasGameStartedTrigger |
| `has_multiple_players` | trigger | CHasMultiplePlayersTrigger |
| `nand` | trigger | CNandTrigger |
| `random_integer` | trigger | - |

## AI weighting - for anyone modding AI behaviour

| keyword | kind | implementing class |
|---|---|---|
| `ai_parliament_issue_resolution_vote_bias` | trigger | - |
| `conquer_area_preference` | trigger | - |
| `conquistador_utility` | trigger | CConquistadorUtilityTrigger |
| `court_language_utility` | trigger | CCourtLanguageUtilityTrigger |
| `create_market_utility` | trigger | CCreateMarketUtilityTrigger |
| `destroy_market_utility` | trigger | CDestroyMarketUtilityTrigger |
| `employment_system_desire` | trigger | CEmploymentSystemDesireTrigger |
| `join_organization_ai_desire` | trigger | CJoinOrganizationAIDesireTrigger |
| `liturgical_language_utility` | trigger | CLiturgicalLanguageUtilityTrigger |
| `modifier_utility` | trigger | - |
| `num_of_locations_with_high_conquer_desire` | trigger | CNumOfLocationsWithHighConquerDesireTrigger |
| `powerful_ally_weight` | trigger | - |
| `religious_view_impact` | trigger | - |
| `relocate_market_utility` | trigger | CRelocateMarketUtilityTrigger |
| `union_partner_weight` | trigger | - |

## Not curated (56)

Tutorial hooks, asserts and internals judged not useful for mods:

`add_internal_flag`, `add_static_modifier_utility`, `agenda_for_special_status`, `assert_read`, `can_start_tutorial_lesson`, `change_art_worth`, `colonial_charter_distance`, `colonial_charter_utility`, `colonial_charter_value`, `combined_unique_special_status_power`, `country_combined_special_status_power_fraction`, `country_has_been_member_for_years`, `discount_needed_for_law_change`, `exploration_expected_cost`, `exploration_needed_time`, `has_building_with_graphical_tag_and_at_least_one_level`, `has_graphical_religion`, `heir_candidates_count`, `heir_position`, `is_alert_triggered`, `is_country_leader_of_circle`, `is_crossing`, `is_estate_loan`, `is_gamestate_tutorial_active`, `is_leader_of_any_imperial_circle_in_io`, `is_leader_of_imperial_circle`, `is_tutorial_active`, `is_tutorial_lesson_active`, `is_tutorial_lesson_completed`, `num_cabinet_capable_characters`, `num_explorations_including_in_construction`, `num_of_active_parliament_agendas`, `num_omens`, `organization_strength_relative_to_country`, `parliament_type_enabled_in_international_organization`, `parliament_type_is_enabled_in`, `parliament_type_is_locked_in`, `parliament_type_visible_in`, `parliament_type_visible_in_international_organization`, `player_proficiency_greater`, `player_proficiency_greater_eq`, `player_proficiency_less_eq`, `policy_has_ai_join_reason`, `policy_has_ai_vote_value`, `province_army_levy_percentage`, `province_navy_levy_percentage`, `relative_defensive_alliance_strength`, `remove_static_modifier_utility`, `reverse_religious_view_impact`, `set_art_worth`, `set_target_of_international_organization`, `short_term_trigger_currency_utility`, `stop_tutorial`, `subject_type_annullment_favours_required`, `this_trust_equilibrium_of_prev`, `vote_type`
