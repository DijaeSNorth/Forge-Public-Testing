# Terminal-first Mythic/Practical Asset Forge

This project is now centered on **real-world inspired crafting workflows** with optional
**mythical + magical enhancements**.

- Blueprints now have a top-level `category` field (`weapon`, `tool`, `wearable`, `vehicle`, `misc`) for folder-style grouping and easier filtering.
- Blueprints also support `addon_slots` so forge outputs can describe filled addon sockets.

- Blueprints now contain explicit crafting sources:
  - materials
  - tools
  - step-by-step process stages
  - risk/yield profile
  - production/ritual requirements
  - stat effects and special enhancements
- Forge can pick any defined source path per asset:
  - practical, real-world production lines
  - magical/mythical pathways for stronger or specialized outcomes
- Asset NFTs are minted using the same provenance logic as before.
- Export payload now includes the source recipe used so other games can recreate the item behavior.

## Files

- `game_logic.py`
  - `AssetBlueprint` now includes structured `crafting_sources`
  - `ForgedAsset` stores `crafting_source_id` and `applied_enhancements`
- `AssetBlueprint` and `ForgedAsset` include a top-level `category`
  - `AssetBlueprint` supports `addon_slots`
  - `ForgedAsset` tracks `addon_slots_filled`
  - `GameLogic` functions for validating/normalizing source definitions and export details
  - Slot enchantment flow now includes roll budgeting, lock state, and reroll/increase ops
- `cli_play.py`
  - terminal interface for building/editing and forging assets
  - new slot commands: `slot_lock`, `slot_unlock`, `slot_reroll`, `slot_upgrade`

## Run

```bash
python cli_play.py
```

## Commands

- `seed` loads sample blueprints
- `blueprints [category=<cat>] [rarity=<R>] [flat=true]` lists blueprints (foldered by type + rarity by default)
- `sources <blueprint_key>` lists available crafting processes for a blueprint
- `assets [category=<cat>] [rarity=<R>] [flat=true]` lists forged assets (foldered by type + rarity by default)
- `new_blueprint <json>` create a new blueprint
- `forge <json>` forge an asset from a blueprint
- `program <asset_id> <json>` append program steps
- `mint <asset_id> [chain]` mint NFT data
- `port <asset_id> [target_game]` export cross-game payload
- `show <asset_id>` show one asset
- `slot_lock <asset_id> <slot_id>` lock a forged slot
- `slot_unlock <asset_id> <slot_id>` unlock a forged slot
- `slot_reroll <asset_id> [slot1,slot2...] [seed=<int>]` reroll unlocked slot enchantments
- `slot_upgrade <asset_id> <slot_id> [additional=<int>] [seed=<int>]` increase a slot's magic roll budget

## Example flow

```text
forge> seed
forge> blueprints
forge> blueprints category=weapon
forge> blueprints category=wearable rarity=legendary flat=true
forge> sources ember_hammer
forge> new_blueprint {"key":"volt_dagger","display_name":"Volt Dagger","asset_class":"WEAPON","base_stats":{"damage":12,"range":8},"crafting_sources":[{"source_id":"volt_dagger_foundry","display_name":"Electromagnetic Foundry","category":"weapon_assembly","is_mythical":false,"process_steps":[{"step":"coil_wind","duration_minutes":40}],"materials":[{"material":"titanium","amount":1.3,"unit":"kg"}],"tools":["winder"],"requirements":["safety_check"],"stat_bonuses":{"damage":2}}],"lore":"Electroforged blade component with modular coil housing."}
forge> forge {"blueprint_key":"volt_dagger","owner":"PlayerOne","crafting_source_id":"volt_dagger_foundry","name":"Volt Dagger Mk1","rarity":"RARE","addons":[{"addon_id":"focus_crystal","slot_id":"focus","slot_type":"focus","is_mythical":true,"stat_bonuses":{"focus":4},"magic_effects":[{"type":"energy_surge","value":"+4 focus"}]}],"stat_overrides":{"range":12}}
forge> program AST-0001-ABCDEF {"program":[{"action":"charge","value":0.2}]}
forge> slot_reroll AST-0001-ABCDEF core,grip seed=99
forge> slot_upgrade AST-0001-ABCDEF core additional=2
forge> slot_lock AST-0001-ABCDEF core
forge> mint AST-0001-ABCDEF mainnet
forge> port AST-0001-ABCDEF rpg_world
```

## Default blueprint catalog

The seeded catalog now includes:

- Swords
  - `steel_broad_sword`
- Hammers
  - `war_hammer`
- Other Weapons
  - `skyforged_saber`
  - `arc_lance`
- Tools
  - `mithril_tinker_kit`
  - `precision_plow`
  - `forgehammer_maintenance_pick`
- Wearables
  - `dragonhide_armor`
  - `arcane_mantle`
  - `sky_ward_helmet`
- Vehicle
  - `aether_runner`

### Practical vs magical source patterns

- `steel_broad_sword`
  - `steel_broad_sword_foundry` (forging)
  - `steel_broad_sword_mythic` (emberbrand rite)
- `war_hammer`
  - `war_hammer_industrial` (hammer forge)
  - `war_hammer_abyssal` (mythic burdening)
- `mithril_tinker_kit`
  - `mithril_tinker_factory` (tool bench)
  - `mithril_tinker_myth` (guild blessing)
- `dragonhide_armor`
  - `dragonhide_realworld` (composite fabrication)
  - `dragonhide_mythic` (draconic rite)

## Magic and mythic material rules

- Magical source routes contribute effects through `enhancements`, which are stored as
  `magic_effects` on forged items.
- Mythical materials (`is_mythical_material: true`) increase forged item rarity by one tier
  (capped at `MYTHIC`).
- During forge, each blueprint slot is auto-filled by:
  - explicit `addons` from the forge payload first (when compatible),
  - remaining open slots by consuming available mythic materials from the source.

## Slot magic roll system

- Each filled slot gets magic metadata:
  - `default_magic_rolls` and `max_magic_rolls` from `addon_slots` (default `1` / `3`)
  - `magic_roll_count` and `max_roll_count` are stored on forged items
  - `slot_locked` can be toggled with `slot_lock` and `slot_unlock`
- `forge(..., slot_rolls, slot_roll_seed, lock_slots)` supports:
  - overriding per-slot roll counts (example `{ "core": 2, "grip": 1 }`)
  - deterministic seeds for repeatable initial enchantment generation
  - pre-locking specific slot IDs
- `slot_reroll` can reroll unlocked slots while locked slots stay fixed.
- `slot_upgrade` raises a slot's roll budget and immediately grants extra random rolls up to that slot's max.

## Item optimization and creativity system

The terminal now includes a layered item optimization surface:

- `roles` lists available optimization profiles (DPS, Tank, Support, Controller, Balanced).
- `optimize <asset_id> [role=<role>]` evaluates one forged item with:
  - grouped stat families (`Crit Stats`, `Defense Stat`, `Mobility/Tempo`, etc.)
  - role fit score
  - creativity score for off-theme diversification
  - total score for ranking
- `benchmark [category=<cat>] [rarity=<R>] [role=<role>] [top=<n>]` ranks current assets by score.
- `eval_stats <json>` evaluates a raw payload before forging.

Recent balancing behavior in this branch:
- Rarity now changes scoring shape:
  - `common` to `mythic` scale both stat impact and enchantment value differently.
  - higher rarity has a larger stat multiplier and stronger enchantment potential.
- Enchantments are now evaluated through:
  - trigger quality (`on_crit`, `on_hit`, `on_kill`, `on_cast`, `on_move`, `state_window`, etc.)
  - condition complexity (e.g., hp thresholds, status windows, target gates)
  - cooldown/frequency pressure
  - repeated trigger diversity (same trigger repeated too much becomes less desirable)
- The optimizer now reports:
  - `enchantment_score`
  - `rarity_bonus`
  - enchantment `details` and `notes` in the same payload.

Example:

```text
roles
optimize AST-0001-ABCDEF role=dps
benchmark category=weapon role=controller top=5
eval_stats {"stats":{"damage":28,"critical_chance":14,"critical_damage":150,"mana":120,"movement_speed":8},"role":"support","rarity":"legendary","magic_effects":[{"type":"on_crit","chance":12,"value":18,"condition":{"target_hp_below":30}}]}
```
