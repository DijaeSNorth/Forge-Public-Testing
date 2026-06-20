from __future__ import annotations

import json
import random
from typing import Any, Dict, List, Tuple

from game_logic import GameLogic, parse_asset_class, parse_rarity
from item_optimization import ItemOptimizationEngine
from talent_system import (
  TALENT_TREE as TALENT_CATALOG,
  TALENT_CATEGORIES,
  TALENT_CATEGORY_LABELS,
  TALENT_PATH_CATEGORY,
  TALENTS_BY_TYPE,
  TALENT_TYPE_LABELS,
  talent_nodes_for_category,
  total_talent_levels,
  talent_bonus,
  talent_level,
  talent_node,
)

RARITY_SORT_ORDER = ["common", "uncommon", "rare", "epic", "legendary", "mythic"]
DEFAULT_PROFILE: Dict[str, Any] = {
  "username": "PlayerOne",
  "forge_name": "Aether Forge",
  "starting_role": "balanced",
  "starting_island": "Bermuda Abyss",
  "player_level": 1,
}

ISLANDS: Dict[str, Dict[str, Any]] = {
  "bermuda_abyss": {
    "zone": "Bermuda Abyss",
    "travel_cost": 0,
    "lore": "Storm-stitched reefs with unstable ore veins and deep, salted fog.",
    "material_pool": {
      "storm_iron_ore": 8,
      "black_salt": 11,
      "rift_whisper_algae": 6,
      "ghostwood_resin": 7,
      "coral_shards": 10,
    },
    "cosmetic_pool": {
      "moon_shroud_mask": 3,
      "salt_lantern_charm": 4,
      "hull_stitched_cloak": 2,
    },
  },
  "atlantian_deep": {
    "zone": "Atlantean Deep",
    "travel_cost": 2,
    "lore": "Sunken architecture rings with static light and forgotten moontech.",
    "material_pool": {
      "sunken_brass": 12,
      "moonstone_glass": 7,
      "tideglass_powder": 8,
      "aetheric_algae": 5,
      "ancient_gel": 6,
      "triton_signal_brace": 3,
    },
    "cosmetic_pool": {
      "coral_tiara": 2,
      "voidglass_visor": 2,
      "sea_crown_chain": 1,
    },
  },
  "oakvault_cay": {
    "zone": "Oakvault Cay",
    "travel_cost": 3,
    "lore": "A mangrove of hollow boughs and wind-trapped resin tides.",
    "material_pool": {
      "vine_iron_leaf": 9,
      "oak_coral": 7,
      "resonant_pitch": 6,
      "brinefruit": 5,
      "salt_crystal": 8,
    },
    "cosmetic_pool": {
      "oak_shell_amulet": 2,
      "coconut_lantern_hilt": 3,
      "reef_root_band": 2,
    },
  },
  "poveglia_mire": {
    "zone": "Poveglia Mire",
    "travel_cost": 4,
    "lore": "Fog-choked marshes where old curses leave echoing bloom trails.",
    "material_pool": {
      "mire_glass_shards": 8,
      "bog_amber": 7,
      "pale_fiber": 6,
      "moss_iron": 9,
      "echo_root": 4,
    },
    "cosmetic_pool": {
      "mire_veil": 2,
      "shiver_ring": 2,
      "salted_eye_patch": 3,
    },
  },
  "hashima_iron_reef": {
    "zone": "Hashima Iron Reef",
    "travel_cost": 5,
    "lore": "A steel-choked reef with wrecked anchors and hard-forged veins.",
    "material_pool": {
      "iron_bone_scale": 10,
      "deep_anchor_flux": 5,
      "rustsilver_flakes": 7,
      "kelpsteel_thread": 8,
      "black_tide_ash": 6,
    },
    "cosmetic_pool": {
      "iron_witch_brooch": 2,
      "deep_hull_binder": 2,
      "reef_silk_mask": 1,
    },
  },
}

ISLAND_ORDER = [
  "bermuda_abyss",
  "atlantian_deep",
  "oakvault_cay",
  "poveglia_mire",
  "hashima_iron_reef",
]

ISLAND_PORTALS: Dict[str, Dict[str, str]] = {}
ISLAND_MATERIAL_POOLS: Dict[str, Dict[str, int]] = {}
COSMETIC_BOUNTIES: Dict[str, Dict[str, int]] = {}
ISLAND_TRAVEL_COSTS: Dict[str, int] = {}

for _island_id, _island_data in ISLANDS.items():
  zone_key = str(_island_data["zone"]).lower()
  ISLAND_PORTALS[zone_key] = {"id": _island_id, "zone": _island_data["zone"]}
  ISLAND_PORTALS[_island_id] = {"id": _island_id, "zone": _island_data["zone"]}
  ISLAND_MATERIAL_POOLS[_island_id] = _island_data["material_pool"]
  COSMETIC_BOUNTIES[_island_id] = _island_data["cosmetic_pool"]
  ISLAND_TRAVEL_COSTS[_island_id] = int(_island_data["travel_cost"])

def _normalize_island_name(island_id: str) -> str:
  return ISLANDS.get(island_id, ISLANDS["bermuda_abyss"])["zone"]


PAGE_HELP: Dict[str, str] = {
  "forge": "forge",
  "inventory": "inventory",
  "talents": "talents",
  "market": "market",
  "map": "map",
}

TALENT_TREE: Dict[str, Dict[str, Any]] = TALENT_CATALOG


def _load_json(payload: str) -> Dict[str, Any]:
  try:
    return json.loads(payload)
  except json.JSONDecodeError as exc:
    raise ValueError("Invalid JSON. Use a single JSON object as the command payload.") from exc


def _parse_flags(raw: str | None) -> Dict[str, str]:
  if not raw:
    return {}
  flags: Dict[str, str] = {}
  for token in raw.split():
    normalized = token.strip()
    if not normalized:
      continue
    normalized = normalized.lstrip("-")
    if "=" in normalized:
      key, value = normalized.split("=", 1)
      if key:
        flags[key.lower()] = value
      continue
    if normalized.lower() == "flat":
      flags["flat"] = "true"
      continue
    if "category" not in flags:
      flags["category"] = normalized
    elif "rarity" not in flags:
      flags.setdefault("rarity", normalized)
  return flags


def _normalize_talent_id(raw: str) -> str:
  return str(raw or "").strip().lower().replace(" ", "_")


def _format_talent_type_header(talent_type: str) -> str:
  return TALENT_TYPE_LABELS.get(_normalize_talent_id(talent_type), talent_type)


def _print_talent_categories() -> None:
  print("")
  print("TALENT CATEGORIES")
  print("-----------------")
  for category in TALENT_CATEGORIES:
    display_category = TALENT_CATEGORY_LABELS.get(category, category.title())
    print(f"{display_category} ({category})")
    assigned_types = [
      talent_type
      for talent_type in TALENT_TYPE_LABELS
      if TALENT_PATH_CATEGORY.get(talent_type, "effects") == category
    ]
    for talent_type in assigned_types:
      print(f"  - {_format_talent_type_header(talent_type)}")
    if not assigned_types:
      print("  (no paths assigned)")
  print("")


def _parse_pairs(raw: str | None) -> Dict[str, str]:
  if not raw:
    return {}
  parsed: Dict[str, str] = {}
  for token in raw.split():
    if "=" not in token:
      continue
    key, value = token.split("=", 1)
    if key:
      parsed[key.lower()] = value
  return parsed


def _bucket_by_category_and_rarity(items: List[Dict[str, Any]]) -> Dict[str, Dict[str, List[Dict[str, Any]]]]:
  buckets: Dict[str, Dict[str, List[Dict[str, Any]]]] = {}
  for item in items:
    category = str(item.get("category") or "misc")
    rarity = str(item.get("rarity") or "common")
    category_bucket = buckets.setdefault(category, {})
    rarity_bucket = category_bucket.setdefault(rarity, [])
    rarity_bucket.append(item)
  ordered: Dict[str, Dict[str, List[Dict[str, Any]]]] = {}
  for category in sorted(buckets):
    by_rarity: Dict[str, List[Dict[str, Any]]] = {}
    known = buckets[category]
    for rarity in RARITY_SORT_ORDER:
      if rarity in known:
        by_rarity[rarity] = sorted(known[rarity], key=lambda row: str(row.get("name", "")))
    for rarity in sorted(known.keys()):
      if rarity not in by_rarity:
        by_rarity[rarity] = sorted(known[rarity], key=lambda row: str(row.get("name", "")))
    ordered[category] = by_rarity
  return ordered


def _print_payload(payload: Dict[str, Any]) -> None:
  print(json.dumps(payload, indent=2, sort_keys=True))


def _print_title_screen() -> None:
  print("")
  print("==============================================================")
  print("=                THE ISLAND FORGE ARCHIVE                     =")
  print("=   Bermuda myths, atlantis whispers, and practical relic-work.  =")
  print("=        Craft. Explore. Trade. Survive the unknown.          =")
  print("==============================================================")
  print("")


def _input_or_default(prompt: str, fallback: str) -> str:
  response = input(prompt).strip()
  return response if response else fallback


def _select_page(raw: str | None) -> str:
  if not raw:
    return ""
  clean = raw.strip().lower()
  if clean in PAGE_HELP:
    return clean
  if clean in {"shop", "trading", "marketplace"}:
    return "market"
  if clean in {"forge", "workshop"}:
    return "forge"
  if clean in {"bag", "inv", "inventory"}:
    return "inventory"
  if clean in {"skill", "talent", "talents"}:
    return "talents"
  if clean in {"map", "atlas", "locations", "islands"}:
    return "map"
  return ""


def _normalize_island(raw: str | None) -> Tuple[str, str]:
  if not raw:
    zone = "bermuda_abyss"
    return ISLAND_PORTALS[zone]["id"], _normalize_island_name(zone)
  key = raw.strip().lower()
  match = ISLAND_PORTALS.get(key)
  if match:
    return match["id"], match["zone"]
  for candidate in ISLAND_PORTALS.values():
    if key == candidate["id"] or key == candidate["zone"].lower():
      return candidate["id"], candidate["zone"]
  return ISLAND_PORTALS["bermuda_abyss"]["id"], ISLAND_PORTALS["bermuda_abyss"]["zone"]


def _choose_island() -> str:
  print("Available island routes:")
  for island_id in ISLAND_ORDER:
    info = ISLANDS[island_id]
    print(f"  - {info['zone']} (travel cost: {info['travel_cost']} shell{'s' if info['travel_cost'] != 1 else ''})")
  while True:
    raw = input("Choose a starting island (default: Bermuda Abyss): ").strip().lower()
    if not raw:
      return "Bermuda Abyss"
    if raw.isdigit():
      index = int(raw)
      if 1 <= index <= len(ISLAND_ORDER):
        return ISLANDS[ISLAND_ORDER[index - 1]]["zone"]
    if raw in ISLAND_PORTALS:
      return ISLAND_PORTALS[raw]["zone"]
    for item in ISLAND_PORTALS.values():
      if raw == item["id"] or raw == item["zone"].lower():
        return item["zone"]
    print("Unknown island. Choose Bermuda Abyss, Atlantean Deep, Oakvault Cay, Poveglia Mire, or Hashima Iron Reef.")


def _choose_role(profile_roles: List[str]) -> str:
  role_options = ", ".join(profile_roles)
  while True:
    role = input(f"Choose a starting optimization focus [{role_options}] (default: balanced): ").strip().lower()
    if not role:
      return "balanced"
    if role in profile_roles:
      return role
    print(f"Unknown role '{role}'. Try one of: {role_options}")


def _create_profile(optimizer: ItemOptimizationEngine) -> Dict[str, Any]:
  print("")
  print("PROFILE CREATION")
  print("-" * 16)
  print("Create your profile before boarding the island systems.")
  username = _input_or_default(f"Adventurer name [{DEFAULT_PROFILE['username']}]: ", DEFAULT_PROFILE["username"]).strip()
  forge_name = _input_or_default(f"Forge name [{DEFAULT_PROFILE['forge_name']}]: ", DEFAULT_PROFILE["forge_name"]).strip()
  starting_island = _choose_island()
  roles = sorted(list(optimizer.role_profiles().keys()))
  starting_role = _choose_role(roles)
  print("")
  print("Profile created.")
  print(f"  Name: {username}")
  print(f"  Forge: {forge_name}")
  print(f"  Island: {starting_island}")
  print(f"  Starting role: {starting_role}")
  print("")
  return {
    "username": username,
    "forge_name": forge_name,
    "starting_island": starting_island,
    "starting_role": starting_role,
  }


def _seed_player_state(profile: Dict[str, Any]) -> Dict[str, Any]:
  starting_island_id = _normalize_island(profile["starting_island"])[0]
  profile_level = int(profile.get("player_level", 1))
  return {
    "sea_shells": 30,
    "talent_points": 2,
    "player_level": profile_level,
    "talents": {},
    "materials": {
      "storm_iron_ore": 2,
      "black_salt": 1,
      "sea_silk": 1,
    },
    "cosmetics": {
      "shell_coil": 1,
    },
    "forage_boons": 0,
    "current_island": starting_island_id,
    "travel_log": [starting_island_id],
    "market_listings": {},
    "next_listing_id": 1,
  }


def _show_tutorial(profile: Dict[str, str]) -> None:
  print("")
  print("TUTORIAL INTRO")
  print("-" * 13)
  print(f"{profile['username']}, this isle is built from two currents:")
  print("- Bermuda lore: rumors, fog, curses, and unstable resources.")
  print("- Atlantean lore: drowned ruins, impossible architecture, forgotten tech.")
  print("")
  print("Main places to play:")
  print("  Forge         -> Build, refine, slot, and optimize artifacts.")
  print("  Map          -> Browse routes and travel to active islands.")
  print("  Inventory     -> Collect foraged materials and crafted cosmetics.")
  print("  Talents       -> Manage player growth and foraging/performance boons.")
  print("  Marketplace   -> Trade materials/cosmetics with NPCs and offers.")
  print("")
  print("Basic flow today:")
  print("  1) `go map`, then `travel <island>` to set your active island.")
  print("  2) `go inventory`, then `forage attempts=<n>`, `materials`, `cosmetics`")
  print("  3) `go forge`, then `seed`, `blueprints`, `forge { ... }`")
  print("  4) `go market`, then `market`, `buy`, `sell`")
  print("  5) `go talents`, then `talents` and `learn_talent <id>`")
  print("")
  print("Type `help` in any page for page-appropriate commands.")
  print("Press Enter to continue.")
  input("")
  print("")


def _print_profile_card(profile: Dict[str, str], player_state: Dict[str, Any]) -> None:
  print("")
  print("PROFILE CARD")
  print("-" * 11)
  print(f"  Adventurer    : {profile['username']}")
  print(f"  Forge         : {profile['forge_name']}")
  print(f"  Home Island   : {profile['starting_island']}")
  print(f"  Active Island : {_normalize_island_name(player_state['current_island'])}")
  print(f"  Role Focus    : {profile['starting_role']}")
  print(f"  Sea Shells    : {player_state['sea_shells']}")
  print(f"  Talents       : {player_state['talent_points']} unspent points")
  print("")


def _format_materials(materials: Dict[str, Any]) -> List[str]:
  if not materials:
    return ["  (no materials yet)"]
  lines: List[str] = []
  for key in sorted(materials.keys()):
    lines.append(f"  - {key}: {materials[key]}")
  return lines


def _format_cosmetics(cosmetics: Dict[str, Any]) -> List[str]:
  if not cosmetics:
    return ["  (no cosmetics yet)"]
  lines: List[str] = []
  for key in sorted(cosmetics.keys()):
    lines.append(f"  - {key}: {cosmetics[key]}")
  return lines


def _print_islands() -> None:
  print("")
  print("KNOWN ISLAND ZONES")
  print("------------------")
  for index, island_id in enumerate(ISLAND_ORDER, start=1):
    island = ISLANDS[island_id]
    print(f"{index}) {island['zone']}")
    print(f"   Lore: {island['lore']}")
    materials = ", ".join(sorted(island["material_pool"].keys()))
    cosmetics = ", ".join(sorted(island["cosmetic_pool"].keys()))
    print(
      "   Materials: "
      f"{materials} | Travel cost: {island['travel_cost']} shell{'s' if island['travel_cost'] != 1 else ''}"
    )
    print(f"   Cosmetics: {cosmetics}")
    print("")
  print("")


def _print_nav(profile: Dict[str, str], player_state: Dict[str, Any], current_page: str) -> None:
  print("")
  print(f"Current page: {current_page.upper()}")
  print(f"Home island  : {profile['starting_island']}")
  print(f"Active island: {_normalize_island_name(player_state['current_island'])}")
  print("Use `go <forge|inventory|talents|market|map>` to switch.")
  print("")


def _roll_foraging_rewards(player_state: Dict[str, Any], island_id: str, *, attempt_count: int = 1) -> Tuple[Dict[str, int], Dict[str, int], List[str]]:
  island_data = ISLANDS.get(island_id, ISLANDS["bermuda_abyss"])
  material_pool = island_data["material_pool"]
  cosmetic_pool = island_data["cosmetic_pool"]

  forager_level = talent_level(player_state["talents"], "forager_sense")
  calm_bonus = talent_bonus(player_state["talents"], "calm_ritual", "forage_calm_chance")
  attempts = attempt_count + int(forager_level)
  bonus = max(0.0, calm_bonus)

  material_gain: Dict[str, int] = {}
  cosmetic_gain: Dict[str, int] = {}
  notes: List[str] = []

  materials = list(material_pool.keys())
  weights = [material_pool[item] for item in materials]

  for _ in range(attempts):
    if random.random() < 0.08 + bonus:
      notes.append("A quiet pocket reduced bad weather risk while foraging.")
    picked = random.choices(materials, weights=weights, k=1)[0]
    qty = random.randint(1, 2 + max(0, forager_level))
    material_gain[picked] = material_gain.get(picked, 0) + qty
    player_state["materials"][picked] = player_state["materials"].get(picked, 0) + qty

  if random.random() < 0.22 + (forager_level * 0.06):
    cosmetic_candidates = list(cosmetic_pool.keys())
    cosmetic_weights = [cosmetic_pool[item] for item in cosmetic_candidates]
    found = random.choices(cosmetic_candidates, weights=cosmetic_weights, k=1)[0]
    cosmetic_gain[found] = cosmetic_gain.get(found, 0) + 1
    player_state["cosmetics"][found] = player_state["cosmetics"].get(found, 0) + 1
    notes.append(f"Discovered a hidden cosmetic: {found}.")

  if not notes:
    notes.append("No dramatic finds this run; your haul is stable but quiet.")

  return material_gain, cosmetic_gain, notes


def _travel_to_island(player_state: Dict[str, Any], destination_raw: str) -> bool:
  if not destination_raw:
    print("Usage: travel <island id or island name>")
    return False

  destination_id, destination_zone = _normalize_island(destination_raw)
  if destination_id == player_state["current_island"]:
    print(f"You are already in {destination_zone}.")
    return True

  fee = ISLAND_TRAVEL_COSTS.get(destination_id, 0)
  if player_state["sea_shells"] < fee:
    print(f"Need {fee} Sea Shells to sail to {destination_zone}.")
    return False

  player_state["sea_shells"] -= fee
  player_state["current_island"] = destination_id
  player_state.setdefault("travel_log", [])
  if destination_id not in player_state["travel_log"]:
    player_state["travel_log"].append(destination_id)

  if fee == 0:
    print(f"Arrived at {destination_zone}.")
  else:
    print(f"Traveled to {destination_zone} for {fee} Sea Shells.")
  return True


def _handle_map_command(
  profile: Dict[str, str],
  player_state: Dict[str, Any],
  cmd: str,
  rest: List[str],
) -> bool:
  if cmd in {"map", "islands", "atlas", "locations"}:
    if rest:
      print("Map commands do not take arguments.")
      return True
    _print_islands()
    print(f"Home island  : {profile['starting_island']}")
    print(f"Active island: {_normalize_island_name(player_state['current_island'])}")
    print("")
    return True

  if cmd == "travel_log":
    print("")
    print("TRAVEL LOG")
    print("----------")
    for island_id in player_state.get("travel_log", []):
      print(f"  - {_normalize_island_name(island_id)}")
    print("")
    return True

  if cmd == "where":
    print("")
    print("LOCATIONS")
    print("---------")
    print(f"Home island  : {profile['starting_island']}")
    print(f"Active island: {_normalize_island_name(player_state['current_island'])}")
    print("")
    return True

  return False


def _print_market(player_state: Dict[str, Any]) -> None:
  print("")
  print("MARKETPLACE")
  print("----------")
  print(f"Sea Shells: {player_state['sea_shells']}")
  listings = player_state["market_listings"]
  if not listings:
    print("  No private listings currently.")
  else:
    for listing_id, listing in sorted(listings.items()):
      print(
        f"  {listing_id} | {listing['category']} | {listing['item']} x{listing['quantity']} "
        f"@ {listing['price']} shell(s) total from {listing['seller']}"
      )
  print("")
  print("Open marketplace has seeded offers:")
  print("  [A1] material | black_salt x3 @ 6")
  print("  [A2] cosmetic | moon_shroud_mask x1 @ 15")
  print("  [A3] material | ancient_gel x4 @ 11")
  print("")


def _print_talents(player_state: Dict[str, Any]) -> None:
  _print_talent_categories()
  print("")
  print("Use `talents category=<category>` or `talents type=<type>` to inspect nodes.")
  print("Use `talent_categories` for full category + path listing.")
  print("")
  print("Installed:")
  if not player_state["talents"]:
    print("  (none)")
  else:
    for talent_id, level in sorted(player_state["talents"].items()):
      tree = TALENT_TREE.get(talent_id, {})
      print(
        f"  - [{TALENT_TYPE_LABELS.get(tree.get('talent_type', 'misc'), tree.get('talent_type', 'misc')).upper()}] "
        f"{tree.get('name', talent_id)} (level {level}/{tree.get('max_level', 0)})"
      )
  print("")
  return


def _print_talents_by_filter(
  player_state: Dict[str, Any],
  *,
  category_filter: str | None = None,
  type_filter: str | None = None,
) -> None:
  print("")
  print("TALENTS")
  print("-------")
  player_level = int(player_state.get("player_level", 1))
  used_levels = total_talent_levels(player_state["talents"])
  print(f"Unspent points: {player_state['talent_points']}")
  print(f"Talent levels used: {used_levels}/{player_level}")
  print("Installed:")
  if not player_state["talents"]:
    print("  (none)")
  else:
    for talent_id, level in sorted(player_state["talents"].items()):
      tree = TALENT_TREE.get(talent_id, {})
      print(
        f"  - [{TALENT_TYPE_LABELS.get(tree.get('talent_type', 'misc'), tree.get('talent_type', 'misc')).upper()}] "
        f"{tree.get('name', talent_id)} (level {level}/{tree.get('max_level', 0)})"
      )
  print("")
  print("Available:")

  def _print_type_block(talent_type: str) -> None:
    print(f"[{_format_talent_type_header(talent_type)}]")
    available = False
    for talent in TALENTS_BY_TYPE.get(talent_type, []):
      talent_id = talent["id"]
      owned = player_state["talents"].get(talent_id, 0)
      if owned >= talent["max_level"]:
        continue
      available = True
      placeholder = " | placeholder" if talent.get("is_placeholder") else ""
      print(
        f"  {talent_id} | {talent['name']}{placeholder} | cost: {talent['cost']} | "
        f"next: {owned}/{talent['max_level']} | {talent['description']}"
      )
    if not available:
      print("  (no available talents in this branch)")

  if type_filter:
    talent_type = _normalize_talent_id(type_filter)
    if talent_type not in TALENT_TYPE_LABELS:
      print("  (unknown talent type)")
      print("")
      print("Use `talents category=<category>` or `talents type=<type>` to filter.")
      print("")
      return
    print(f"Type filter: {_format_talent_type_header(talent_type)}")
    _print_type_block(talent_type)
    print("")
    print("Use `learn_talent <talent_id>` to spend points.")
    print("")
    return

  if category_filter:
    category = _normalize_talent_id(category_filter)
    if category not in TALENT_CATEGORIES:
      print("  (unknown talent category)")
      print("")
      print("Use `talents category=<category>` or `talents type=<type>` to filter.")
      print("")
      return
    print(f"Category filter: {TALENT_CATEGORY_LABELS.get(category, category.title())}")
    print(f"Total nodes: {len(talent_nodes_for_category(category))}")
    for talent_type in TALENT_TYPE_LABELS:
      if TALENT_PATH_CATEGORY.get(talent_type, "effects") != category:
        continue
      _print_type_block(talent_type)
    print("")
    print("Use `learn_talent <talent_id>` to spend points.")
    print("")
    return

  for talent_type in TALENT_TYPE_LABELS:
    print(f"[{_format_talent_type_header(talent_type)}]")
    available = False
    for talent in TALENTS_BY_TYPE.get(talent_type, []):
      talent_id = talent["id"]
      owned = player_state["talents"].get(talent_id, 0)
      if owned >= talent["max_level"]:
        continue
      available = True
      placeholder = " | placeholder" if talent.get("is_placeholder") else ""
      print(
        f"  {talent_id} | {talent['name']}{placeholder} | cost: {talent['cost']} | "
        f"next: {owned}/{talent['max_level']} | {talent['description']}"
      )
    if not available:
      print("  (no available talents in this branch)")
  print("")
  print("Use `learn_talent <talent_id>` to spend points.")
  print("")


def _print_help(page: str) -> None:
  if page == "forge":
    print("Forge page commands:")
    print("  title                              show title screen")
    print("  profile                            show current profile")
    print("  tutorial                           replay onboarding tutorial")
    print("  seed                               create sample blueprints")
    print("  blueprints [category=<cat>] [rarity=<R>] [flat=true]   list blueprints (foldered by type/rarity by default)")
    print("  sources <blueprint_key>             list crafting processes for blueprint")
    print("  assets [category=<cat>] [rarity=<R>] [flat=true]         list forged assets (foldered by type/rarity by default)")
    print("  new_blueprint <json>               create blueprint")
    print("  forge <json>                       forge asset from blueprint")
    print("  slot_lock <asset_id> <slot_id>     lock a magic slot")
    print("  slot_unlock <asset_id> <slot_id>   unlock a magic slot")
    print("  slot_reroll <asset_id> [slot1,slot2..] [seed=<int>]   reroll unlocked magic slots")
    print("  slot_upgrade <asset_id> <slot_id> [additional=<int>] [seed=<int>]   add extra magic rolls")
    print("  program <asset_id> <json>          append behavior program to an asset")
    print("  roles                              list optimization profiles")
    print("  optimize <asset_id> [role=<role>]  analyze one item")
    print("  benchmark [category=<cat>] [rarity=<R>] [role=<role>] [top=<n>] [flat=true]   rank assets by score")
    print("  eval_stats <json>                  evaluate raw stats payload (+ optional rarity/magic_effects/applied_enhancements)")
    print("  mint <asset_id> [chain]            mint NFT for item")
    print("  port <asset_id> [target]           export portable payload")
    print("  show <asset_id>                    show one item")
    print("  go <forge|inventory|talents|market|map>  switch to another main place")
    print("  map                                show map overview")
    print("  exit / quit                        leave")
  elif page == "inventory":
    print("Inventory page commands:")
    print("  profile                            show current profile")
    print("  materials                          list gathered materials")
    print("  cosmetics                          list gathered cosmetics")
    print("  forage [attempts=<n>]              gather materials on active island")
    print("  map | islands | atlas | locations  review all known zones")
    print("  travel_log                         show known visited zones")
    print("  where                              show home and active islands")
    print("  transfer_asset <asset_id>           move forged item to storage (placeholder)")
    print("  travel <island id or island name>  sail to an island")
    print("  go <forge|talents|market|map>      switch place")
    print("  title                              show title screen")
    print("  tutorial                           replay onboarding tutorial")
    print("  exit / quit                        leave")
  elif page == "talents":
    print("Talents page commands:")
    print("  profile                            show current profile")
    print("  talents                            show talent status")
    print("  talents category=<cat> [type=<type>]   list talents by category or type")
    print("  talent_categories                  list talent categories and type breakdown")
    print("  talent_search <term>               search talent ids/names/descriptions")
    print("  learn_talent <talent_id>           spend points")
    print("  go <forge|inventory|market|map>        switch place")
    print("  map                               show map overview")
    print("  title                              show title screen")
    print("  tutorial                           replay onboarding tutorial")
    print("  exit / quit                        leave")
  elif page == "market":
    print("Marketplace commands:")
    print("  profile                            show current profile")
    print("  market                             show active marketplace board")
    print("  buy <listing_id>                   buy seeded/private listing")
    print("  sell <category> <item> <qty> <price>   place item to your listing")
    print("  reclaim <listing_id>                reclaim your listing")
    print("  go <forge|inventory|talents|map>       switch place")
    print("  map                               show map overview")
    print("  travel <island id or island name>  sail to an island")
    print("  travel_log                         show known visited zones")
    print("  where                              show home and active islands")
    print("  title                              show title screen")
    print("  tutorial                           replay onboarding tutorial")
    print("  exit / quit                        leave")
  else:
    print("Map commands:")
    print("  profile                            show current profile")
    print("  map | islands | atlas | locations  review all known zones")
    print("  travel <island id or island name>  sail to an island")
    print("  travel_log                         show known visited zones")
    print("  where                              show home and active islands")
    print("  go <forge|inventory|talents|market|map> switch place")
    print("  title                              show title screen")
    print("  tutorial                           replay onboarding tutorial")
    print("  exit / quit                        leave")


def _handle_forge_command(
  game: GameLogic,
  optimizer: ItemOptimizationEngine,
  cmd: str,
  rest: List[str],
) -> bool:
  if cmd == "seed":
    game.seed_demo_blueprints()
    print("Seed blueprints already loaded.")
    return True

  if cmd == "blueprints":
    filters = _parse_flags(rest[0] if rest else None)
    blueprints = game.list_blueprints(
      category=filters.get("category") or filters.get("type"),
      rarity=filters.get("rarity"),
    )
    if filters.get("flat", "").lower() in {"1", "true", "yes", "y"}:
      _print_payload({"blueprints": blueprints})
    else:
      _print_payload({"folders": _bucket_by_category_and_rarity(blueprints)})
    return True

  if cmd == "sources":
    if not rest:
      print("Usage: sources <blueprint_key>")
      return True
    payload = game.source_for_blueprint(rest[0].strip())
    _print_payload({"blueprint_key": rest[0].strip(), "crafting_sources": payload})
    return True

  if cmd == "assets":
    filters = _parse_flags(rest[0] if rest else None)
    assets = game.list_assets(
      category=filters.get("category") or filters.get("type"),
      rarity=filters.get("rarity"),
    )
    if filters.get("flat", "").lower() in {"1", "true", "yes", "y"}:
      _print_payload({"assets": assets})
    else:
      _print_payload({"folders": _bucket_by_category_and_rarity(assets)})
    return True

  if cmd == "new_blueprint":
    if not rest:
      print("Usage: new_blueprint <json>")
      return True
    payload = _load_json(rest[0])
    blueprint = game.create_blueprint(
      key=payload["key"],
      display_name=payload["display_name"],
      asset_class=parse_asset_class(payload["asset_class"]),
      category=payload.get("category"),
      base_stats=payload["base_stats"],
      lore=payload.get("lore", ""),
      is_mythical=bool(payload.get("is_mythical", False)),
      default_rarity=parse_rarity(payload.get("default_rarity", "UNCOMMON")),
      compatibility=payload.get("compatibility"),
      program_template=payload.get("program_template") or [],
      crafting_sources=payload.get("crafting_sources") or [],
      practical_process_tag=payload.get("practical_process_tag", "general_fabrication"),
      addon_slots=payload.get("addon_slots") or [],
    )
    _print_payload({"blueprint": blueprint.to_dict()})
    return True

  if cmd == "forge":
    if not rest:
      print("Usage: forge <json>")
      return True
    payload = _load_json(rest[0])
    asset_id = game.forge_asset(
      blueprint_key=payload["blueprint_key"],
      owner=payload["owner"],
      name=payload.get("name"),
      rarity=parse_rarity(payload["rarity"]) if payload.get("rarity") else None,
      stat_overrides=payload.get("stat_overrides"),
      tags=payload.get("tags"),
      custom_program=payload.get("program"),
      crafting_source_id=payload.get("crafting_source_id"),
      addons=payload.get("addons") or [],
      slot_roll_seed=payload.get("slot_roll_seed"),
      slot_rolls=payload.get("slot_rolls"),
      lock_slots=payload.get("lock_slots"),
    )
    print(f"Forged asset id: {asset_id}")
    _print_payload(game.get_asset(asset_id).to_dict())
    return True

  if cmd == "slot_lock":
    if not rest:
      print("Usage: slot_lock <asset_id> <slot_id>")
      return True
    parts = rest[0].split()
    if len(parts) != 2:
      print("Usage: slot_lock <asset_id> <slot_id>")
      return True
    _print_payload(game.set_slot_lock(parts[0], parts[1], locked=True))
    return True

  if cmd == "slot_unlock":
    if not rest:
      print("Usage: slot_unlock <asset_id> <slot_id>")
      return True
    parts = rest[0].split()
    if len(parts) != 2:
      print("Usage: slot_unlock <asset_id> <slot_id>")
      return True
    _print_payload(game.set_slot_lock(parts[0], parts[1], locked=False))
    return True

  if cmd == "slot_reroll":
    if not rest:
      print("Usage: slot_reroll <asset_id> [slot1,slot2..] [seed=<int>]")
      return True
    parts = rest[0].split()
    asset_id = parts[0]
    slot_ids = None
    seed: int | None = None
    if len(parts) > 1:
      remaining = []
      for token in parts[1:]:
        if "=" in token:
          key, value = token.split("=", 1)
          if key.lower() == "seed":
            try:
              seed = int(value)
            except ValueError:
              raise ValueError("seed must be an integer.")
          else:
            raise ValueError(f"Unsupported option '{token}'.")
        elif token.strip():
          remaining.append(token.strip())
      if remaining:
        slot_ids = [item for chunk in remaining for item in chunk.split(",") if item.strip()]
    _print_payload(game.reroll_slot_magic(asset_id, slot_ids=slot_ids, seed=seed))
    return True

  if cmd == "slot_upgrade":
    if not rest:
      print("Usage: slot_upgrade <asset_id> <slot_id> [additional=<int>] [seed=<int>]")
      return True
    parts = rest[0].split()
    if len(parts) < 2:
      print("Usage: slot_upgrade <asset_id> <slot_id> [additional=<int>] [seed=<int>]")
      return True
    asset_id = parts[0]
    slot_id = parts[1]
    additional = 1
    seed = None
    for token in parts[2:]:
      if "=" not in token:
        raise ValueError(f"Unsupported option '{token}'.")
      key, value = token.split("=", 1)
      if key.lower() == "additional":
        try:
          additional = int(value)
        except ValueError:
          raise ValueError("additional must be an integer.")
      elif key.lower() == "seed":
        try:
          seed = int(value)
        except ValueError:
          raise ValueError("seed must be an integer.")
      else:
        raise ValueError(f"Unsupported option '{token}'.")
    _print_payload(game.increase_slot_rolls(asset_id, slot_id, additional_rolls=additional, seed=seed))
    return True

  if cmd == "program":
    if not rest:
      print("Usage: program <asset_id> <json>")
      return True
    parts = rest[0].split(maxsplit=1)
    if len(parts) != 2:
      print("Usage: program <asset_id> <json>")
      return True
    asset_id = parts[0]
    payload = _load_json(parts[1])
    steps = payload.get("program")
    if not isinstance(steps, list):
      print("Program payload should include {'program':[...]} with at least one step.")
      return True
    _print_payload(game.program_asset(asset_id, steps))
    return True

  if cmd == "roles":
    _print_payload({"roles": optimizer.role_profiles()})
    return True

  if cmd == "optimize":
    if not rest:
      print("Usage: optimize <asset_id> [role=<role>]")
      return True
    parts = rest[0].split()
    asset_id = parts[0]
    options = _parse_pairs(" ".join(parts[1:]))
    role = options.get("role", "balanced")
    asset = game.get_asset(asset_id).to_dict()
    _print_payload({"asset_id": asset_id, "optimization": optimizer.evaluate(asset, role=role)})
    return True

  if cmd == "eval_stats":
    if not rest:
      print("Usage: eval_stats <json>")
      return True
    payload = _load_json(rest[0])
    if not isinstance(payload, dict):
      print("eval_stats expects JSON object.")
      return True
    role = str(payload.get("role", "balanced"))
    stats = payload.get("stats", {})
    if not isinstance(stats, dict):
      print("eval_stats expects {'stats': {...}, 'role': '<role>'}.")
      return True
    result = optimizer.evaluate(
      {
        "asset_id": str(payload.get("asset_id", "custom")),
        "name": str(payload.get("name", "custom")),
        "rarity": str(payload.get("rarity", "uncommon")),
        "stats": stats,
        "magic_effects": payload.get("magic_effects", []),
        "applied_enhancements": payload.get("applied_enhancements", []),
      },
      role=role,
    )
    _print_payload({"optimization": result})
    return True

  if cmd == "benchmark":
    if not rest:
      filters = {}
    else:
      filters = _parse_flags(rest[0])
    role = filters.get("role", "balanced")
    try:
      top = int(filters.get("top", "10"))
    except ValueError:
      top = 10
    top = max(1, top)
    assets = game.list_assets(
      category=filters.get("category") or filters.get("type"),
      rarity=filters.get("rarity"),
    )
    ranked = optimizer.benchmark(assets, role=role)
    _print_payload({"role": role, "top": top, "results": ranked[:top]})
    return True

  if cmd == "mint":
    if not rest:
      print("Usage: mint <asset_id> [chain]")
      return True
    parts = rest[0].split()
    asset_id = parts[0]
    chain = parts[1] if len(parts) > 1 else "local"
    _print_payload({"nft": game.mint_asset_nft(asset_id, chain=chain)})
    return True

  if cmd == "port":
    if not rest:
      print("Usage: port <asset_id> [target]")
      return True
    parts = rest[0].split()
    asset_id = parts[0]
    target = parts[1] if len(parts) > 1 else "universal"
    _print_payload(game.export_portable_payload(asset_id, target_game=target))
    return True

  if cmd == "show":
    if not rest:
      print("Usage: show <asset_id>")
      return True
    _print_payload(game.get_asset(rest[0].strip()).to_dict())
    return True

  return False


def _handle_inventory_command(
  game: GameLogic,
  profile: Dict[str, str],
  player_state: Dict[str, Any],
  cmd: str,
  rest: List[str],
) -> bool:
  if cmd == "materials":
    print("")
    print("MATERIALS")
    print("---------")
    for line in _format_materials(player_state["materials"]):
      print(line)
    print("")
    return True

  if cmd == "cosmetics":
    print("")
    print("COSMETICS")
    print("---------")
    for line in _format_cosmetics(player_state["cosmetics"]):
      print(line)
    print("")
    return True

  if cmd == "forage":
    attempts = 1
    if rest:
      tokens = rest[0].split()
      if tokens:
        for token in tokens:
          if "=" in token:
            key, value = token.split("=", 1)
            if key.lower() == "attempts":
              try:
                attempts = max(1, int(value))
              except ValueError:
                print("attempts must be an integer.")
                return True
            else:
              print(f"Unsupported option '{token}'.")
              return True
          else:
            print("Foraging is tied to your active island.")
            print("Use `travel <island>` first, then run `forage`.")
            return True
    island_id = player_state["current_island"]
    resolved_name = _normalize_island_name(island_id)
    player_state["current_island"] = island_id
    material_gain, cosmetic_gain, notes = _roll_foraging_rewards(player_state, island_id, attempt_count=attempts)
    if not material_gain and not cosmetic_gain:
      print(f"No notable finds from {resolved_name}.")
    else:
      print(f"Foraging in {resolved_name}...")
      for material, count in sorted(material_gain.items()):
        print(f"  +{count} {material}")
      for cosmetic, count in sorted(cosmetic_gain.items()):
        print(f"  +{count} COSMETIC: {cosmetic}")
    for note in notes:
      print(f"  {note}")
    print("")
    return True

  if cmd == "islands":
    _print_islands()
    return True

  if cmd == "transfer_asset":
    if not rest:
      print("Usage: transfer_asset <asset_id>")
      return True
    _ = rest[0].strip()
    print("Storage transfer placeholder: asset routing hooks are wired for future work.")
    return True

  return False


def _handle_talent_command(
  profile: Dict[str, str],
  player_state: Dict[str, Any],
  cmd: str,
  rest: List[str],
) -> bool:
  if cmd == "talents":
    flags = _parse_flags(rest[0] if rest else None)
    category_filter = flags.get("category")
    type_filter = flags.get("type")
    if category_filter and category_filter in TALENT_TYPE_LABELS and not type_filter:
      type_filter = category_filter
      category_filter = None
    if rest and not flags:
      for token in rest[0].split():
        normalized = _normalize_talent_id(token)
        if normalized in TALENT_CATEGORIES and not category_filter:
          category_filter = normalized
          continue
        if normalized in TALENT_TYPE_LABELS and not type_filter:
          type_filter = normalized
    _print_talents(player_state, category_filter=category_filter, type_filter=type_filter)
    return True

  if cmd == "talent_categories":
    _print_talent_categories()
    return True

  if cmd == "learn_talent":
    if not rest:
      print("Usage: learn_talent <talent_id>")
      return True
    talent_id = rest[0].strip().lower()
    talent = talent_node(talent_id)
    if talent is None:
      print(f"Unknown talent '{talent_id}'.")
      return True
    current = talent_level(player_state["talents"], talent_id)
    if current >= talent["max_level"]:
      print(f"{talent['name']} already at max level.")
      return True
    prerequisites = talent.get("prerequisites", [])
    for prerequisite in prerequisites:
      if talent_level(player_state["talents"], prerequisite) <= 0:
        print(f"{talent['name']} requires '{prerequisite}' to be learned first.")
        return True
    profile_level = int(profile.get("player_level", 1))
    talent_levels_allocated = total_talent_levels(player_state["talents"])
    if talent_levels_allocated + 1 > profile_level:
      print(
        f"Profile level {profile_level} reached: you can only invest "
        f"{profile_level} talent levels in total right now."
      )
      return True
    cost = talent["cost"]
    if player_state["talent_points"] < cost:
      print(f"Need {cost} talent points for {talent['name']}.")
      return True
    player_state["talent_points"] -= cost
    player_state["talents"][talent_id] = current + 1
    print(f"Learned {talent['name']} ({current + 1}/{talent['max_level']}).")
    return True

  if cmd == "talent_search":
    if not rest:
      print("Usage: talent_search <term>")
      return True
    query = rest[0].strip().lower()
    if not query:
      print("Usage: talent_search <term>")
      return True
    print("")
    print(f"TALENT SEARCH: '{query}'")
    print("-----------------------")
    matches = []
    for nodes in TALENTS_BY_TYPE.values():
      for talent in nodes:
        haystack = " ".join(
          [
            talent["id"],
            talent["name"].lower(),
            talent["description"].lower(),
            talent.get("talent_type", "").lower(),
          ]
        )
        if query in haystack:
          matches.append(talent)
    if not matches:
      print("  (no matches)")
    else:
      for talent in matches:
        print(
          f"  {talent['id']} | {talent['name']} | level cap {talent['max_level']} | "
          f"{TALENT_TYPE_LABELS.get(talent['talent_type'], talent['talent_type'])} | "
          f"{TALENT_CATEGORY_LABELS.get(talent.get('talent_category', 'effects'), 'Effects')}"
        )
    print("")
    return True

  return False


def _handle_market_command(player_state: Dict[str, Any], cmd: str, rest: List[str]) -> bool:
  if cmd == "market":
    _print_market(player_state)
    return True

  if cmd == "buy":
    if not rest:
      print("Usage: buy <listing_id>")
      return True
    listing_id = rest[0].strip().upper()
    seeded = {
      "A1": {"seller": "Bermuda Cartel", "category": "material", "item": "black_salt", "quantity": 3, "price": 6},
      "A2": {"seller": "Deep Cartel", "category": "cosmetic", "item": "moon_shroud_mask", "quantity": 1, "price": 15},
      "A3": {"seller": "Atlan Research", "category": "material", "item": "ancient_gel", "quantity": 4, "price": 11},
    }
    listing = seeded.get(listing_id)
    if not listing:
      if listing_id in player_state["market_listings"]:
        listing = player_state["market_listings"][listing_id]
        if listing["price"] > player_state["sea_shells"]:
          print("Not enough shells for this listing.")
          return True
        player_state["sea_shells"] -= listing["price"]
        bucket = player_state["cosmetics"] if listing["category"] == "cosmetic" else player_state["materials"]
        bucket[listing["item"]] = bucket.get(listing["item"], 0) + listing["quantity"]
        del player_state["market_listings"][listing_id]
        print(f"Bought {listing['quantity']}x {listing['item']} for {listing['price']} shells.")
        return True
      print("Listing not found.")
      return True
    if listing["price"] > player_state["sea_shells"]:
      print("Not enough shells for this listing.")
      return True
    player_state["sea_shells"] -= listing["price"]
    bucket = player_state["cosmetics"] if listing["category"] == "cosmetic" else player_state["materials"]
    bucket[listing["item"]] = bucket.get(listing["item"], 0) + listing["quantity"]
    print(f"Bought {listing['quantity']}x {listing['item']} for {listing['price']} shells.")
    return True

  if cmd == "sell":
    if not rest:
      print("Usage: sell <category> <item> <qty> <price>")
      return True
    parts = rest[0].split()
    if len(parts) < 4:
      print("Usage: sell <category> <item> <qty> <price>")
      return True
    category = parts[0].lower()
    item_name = parts[1]
    try:
      qty = int(parts[2])
      price = int(parts[3])
    except ValueError:
      print("quantity and price must be integers.")
      return True
    if qty <= 0 or price <= 0:
      print("quantity and price must be positive.")
      return True
    bucket = player_state["cosmetics"] if category == "cosmetic" else player_state["materials"]
    if bucket.get(item_name, 0) < qty:
      print(f"Not enough {item_name} in inventory.")
      return True
    bucket[item_name] -= qty
    if bucket[item_name] <= 0:
      del bucket[item_name]
    listing_id = f"PLY-{player_state['next_listing_id']:03d}"
    player_state["next_listing_id"] += 1
    discount = int(talent_bonus(player_state["talents"], "merchant_bargain", "market_fee_discount", 0))
    listing_price = max(1, price - discount)
    player_state["market_listings"][listing_id] = {
      "seller": "You",
      "category": category,
      "item": item_name,
      "quantity": qty,
      "price": listing_price,
    }
    print(f"Placed listing {listing_id} to market: {qty}x {item_name} for {player_state['market_listings'][listing_id]['price']} shells.")
    return True

  if cmd == "reclaim":
    if not rest:
      print("Usage: reclaim <listing_id>")
      return True
    listing_id = rest[0].strip().upper()
    listing = player_state["market_listings"].get(listing_id)
    if not listing:
      print("Listing not found.")
      return True
    if listing.get("seller") != "You":
      print("Cannot reclaim public listing.")
      return True
    bucket = player_state["cosmetics"] if listing["category"] == "cosmetic" else player_state["materials"]
    bucket[listing["item"]] = bucket.get(listing["item"], 0) + listing["quantity"]
    del player_state["market_listings"][listing_id]
    print(f"Reclaimed listing {listing_id} and recovered {listing['quantity']}x {listing['item']}.")
    return True

  return False


def _run_game_loop(game: GameLogic, optimizer: ItemOptimizationEngine, profile: Dict[str, str], player_state: Dict[str, Any]) -> None:
  current_page = "forge"
  _print_nav(profile, player_state, current_page)
  print("Type `help` for page commands.")

  while True:
    try:
      raw = input(f"{profile['forge_name']}|{current_page}> ").strip()
    except EOFError:
      print("")
      print("Session closed.")
      break

    if not raw:
      continue
    command, *rest = raw.split(maxsplit=1)
    cmd = command.lower()

    if cmd in {"exit", "quit", "q"}:
      break

    try:
      if cmd in {"map", "islands", "atlas", "locations", "travel_log", "where"}:
        if _handle_map_command(profile, player_state, cmd, rest):
          continue

      if cmd == "travel":
        destination = rest[0].strip() if rest else ""
        _travel_to_island(player_state, destination)
        continue

      if cmd == "help":
        _print_help(current_page)
        continue

      if cmd == "title":
        _print_title_screen()
        continue

      if cmd == "profile":
        _print_profile_card(profile, player_state)
        continue

      if cmd == "tutorial":
        _show_tutorial(profile)
        continue

      if cmd == "go":
        if not rest:
          print("Usage: go <forge|inventory|talents|market|map>")
          continue
        next_page = _select_page(rest[0])
        if not next_page:
          print("Unknown page. Choose forge, inventory, talents, market, or map.")
          continue
        current_page = next_page
        _print_nav(profile, player_state, current_page)
        if current_page == "forge":
          print("Main page: Forge")
        continue

      if current_page == "forge" and _handle_forge_command(game, optimizer, cmd, rest):
        continue

      if current_page == "inventory" and _handle_inventory_command(game, profile, player_state, cmd, rest):
        continue

      if current_page == "talents" and _handle_talent_command(profile, player_state, cmd, rest):
        continue

      if current_page == "market" and _handle_market_command(player_state, cmd, rest):
        continue

      if current_page == "map" and _handle_map_command(profile, player_state, cmd, rest):
        continue

      print("Unknown command. Type 'help'.")
    except ValueError as exc:
      print(f"Error: {exc}")
    except KeyError as exc:
      print(f"Error: {exc}")


def main() -> None:
  game = GameLogic()
  game.seed_demo_blueprints()
  optimizer = ItemOptimizationEngine()
  _print_title_screen()
  profile = _create_profile(optimizer)
  player_state = _seed_player_state(profile)
  _show_tutorial(profile)
  _print_nav(profile, player_state, "forge")
  _run_game_loop(game, optimizer, profile, player_state)


if __name__ == "__main__":
  main()

