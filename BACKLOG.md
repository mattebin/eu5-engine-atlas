# Later work

## 1. GUI functions needing unreachable receivers (3,251)

577 of 3,828 are confirmed usable. The rest are methods on types the console
cannot construct: building, unit, character, war, trade node, army, fleet,
estate, institution and similar.

**Not disproven** - untested. Reaching them needs an accessor chain that
yields such an object, e.g. a way to get a building from a location or a
unit from a country. Ruler, heir and government are NOT reachable as
`GetPlayer.GetRuler` / `.GetHeir` / `.GetGovernment` - those names do not
exist, so the chain has to be discovered rather than guessed.

Approach when resumed: mine vanilla `.gui` files for `datacontext` chains
that produce each type, then reuse those chains as receivers.

## 2. List-type recall (53 of 253)

The template-helper filter finds only one family of list types. Vanilla uses
253 base names; we recover 53 with high confidence and 9 undocumented ones.
Other list types use different template bands. Widening the filter, or
walking each band separately, should raise recall.

## 3. Hidden defines (45)

Never set by any vanilla defines file. Cannot be tested from the console -
defines need a mod file and a game restart. Several are directly relevant to
Responsive Universalis: `NAI.AI_MILITARY_ASSIGNMENT_STRENGTH_FACTOR`,
`NAI.BASE_CASUS_BELLI_WARGOAL_DESIRE`,
`NAI.AI_RIVAL_STRENGTH_DIFFERENCE_LIMIT`, `NDiplomacy.DIPLOMATIC_RANGE`,
`NEconomy.GROWTH_FROM_FOOD_MULTIPLIER`.

## 4. Composed-keyword blind spot

All five extractions match literal strings, so anything the engine assembles
at runtime is invisible to them - `every_country` byte-searches to zero hits
despite being real script. Iterators were found only by accident. There may
be other composed classes not yet imagined.
