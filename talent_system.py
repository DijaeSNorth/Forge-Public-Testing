from __future__ import annotations

from collections import OrderedDict
from typing import Any, Dict, Iterable, List, Mapping, Sequence, Tuple


def _normalize_talent_id(raw: str) -> str:
  return str(raw or "").strip().lower().replace(" ", "_")


MAX_NODES_PER_TYPE = 100
NODES_PER_TYPE = 100

TALENT_TYPE_LABELS: OrderedDict[str, str] = OrderedDict(
  [
    ("shadows", "Darkness / Shadows"),
    ("elemental", "Elemental"),
    ("cosmic", "Cosmic"),
    ("luck", "Luck"),
    ("arcane", "Arcane"),
    ("nature", "Nature"),
    ("forge", "Forge & Craft"),
    ("psionic", "Psionic"),
    ("tech", "Technology"),
    ("biotech", "Biotech"),
    ("astral", "Astral"),
    ("moon", "Moonborn"),
    ("sun", "Sunfire"),
    ("storm", "Stormbound"),
    ("frost", "Frost"),
    ("inferno", "Inferno"),
    ("seaborn", "Seaborn"),
    ("earth", "Geomancy"),
    ("metal", "Metallurgy"),
    ("wood", "Woodcraft"),
    ("beast", "Beastcraft"),
    ("wind", "Windcraft"),
    ("blood", "Bloodline"),
    ("bone", "Bonecraft"),
    ("spirit", "Spiritbound"),
    ("void", "Voidcraft"),
    ("crystal", "Crystalcraft"),
    ("toxic", "Toxcraft"),
    ("hermetic", "Hermetic"),
    ("rune", "Runecraft"),
    ("sigil", "Sigilcraft"),
    ("light", "Lightweave"),
    ("dark", "Duskborn"),
    ("time", "Chronotech"),
    ("space", "Spacetime"),
    ("quantum", "Quantum"),
    ("gravity", "Gravity"),
    ("alchemy", "Alchemy"),
    ("necromancy", "Necromancy"),
    ("divine", "Divinity"),
    ("chaos", "Chaos"),
    ("order", "Order"),
    ("rift", "Riftwalker"),
    ("mirror", "Mirrorcraft"),
    ("iron", "Ironbound"),
    ("ember", "Emberward"),
    ("myth", "Mythic Relics"),
    ("draconic", "Draconic"),
    ("fae", "Faewoven"),
    ("clockwork", "Clockwork"),
  ]
)

TALENT_CATEGORIES: Tuple[str, ...] = (
  "effects",
  "triggers",
  "enhancements",
  "utility",
)

TALENT_CATEGORY_LABELS: Mapping[str, str] = {
  "effects": "Effects",
  "triggers": "Triggers",
  "enhancements": "Enhancements",
  "utility": "Utility Stats",
}

TALENT_PATH_CATEGORY: Mapping[str, str] = {
  "shadows": "effects",
  "elemental": "enhancements",
  "cosmic": "triggers",
  "luck": "utility",
  "arcane": "triggers",
  "nature": "enhancements",
  "forge": "utility",
  "psionic": "effects",
  "tech": "enhancements",
  "biotech": "enhancements",
  "astral": "triggers",
  "moon": "utility",
  "sun": "enhancements",
  "storm": "effects",
  "frost": "effects",
  "inferno": "effects",
  "seaborn": "utility",
  "earth": "enhancements",
  "metal": "enhancements",
  "wood": "enhancements",
  "beast": "utility",
  "wind": "effects",
  "blood": "effects",
  "bone": "utility",
  "spirit": "effects",
  "void": "effects",
  "crystal": "enhancements",
  "toxic": "effects",
  "hermetic": "utility",
  "rune": "triggers",
  "sigil": "triggers",
  "light": "utility",
  "dark": "effects",
  "time": "triggers",
  "space": "triggers",
  "quantum": "triggers",
  "gravity": "triggers",
  "alchemy": "enhancements",
  "necromancy": "utility",
  "divine": "utility",
  "chaos": "effects",
  "order": "triggers",
  "rift": "triggers",
  "mirror": "triggers",
  "iron": "utility",
  "ember": "effects",
  "myth": "triggers",
  "draconic": "enhancements",
  "fae": "utility",
  "clockwork": "utility",
}


def _node(
  talent_id: str,
  name: str,
  description: str,
  talent_type: str,
  *,
  max_level: int = 1,
  cost: int = 1,
  effects: Mapping[str, float] | None = None,
  is_placeholder: bool = False,
  talent_category: str = "effects",
  prerequisites: Sequence[str] | None = None,
  tags: Sequence[str] | None = None,
) -> Dict[str, Any]:
  return {
    "id": _normalize_talent_id(talent_id),
    "name": name.strip(),
    "description": description.strip(),
    "talent_type": talent_type,
    "talent_category": _normalize_talent_id(talent_category),
    "max_level": int(max_level),
    "cost": int(cost),
    "effects": dict(effects or {}),
    "is_placeholder": bool(is_placeholder),
    "prerequisites": [str(item).strip().lower() for item in (prerequisites or ()) if str(item).strip()],
    "tags": [str(tag).strip() for tag in (tags or ()) if str(tag).strip()],
  }


def _item_talent(
  talent_type: str,
  item_name: str,
  *,
  index: int,
  bonus_key: str,
  bonus_value: float = 1.0,
  description_suffix: str = "",
  max_level: int = 1,
  cost: int = 1,
  talent_category: str = "effects",
  prerequisites: Sequence[str] | None = None,
) -> Dict[str, Any]:
  label = item_name.replace("_", " ").title()
  talent_id = f"{talent_type}_{item_name}_{index:02d}"
  effect_key = f"{bonus_key}_{item_name}"
  description = (
    f"Item-based {talent_type} affinity tied to '{label}'. "
    f"{description_suffix}".strip()
  ).strip()
  if not description.endswith("."):
    description += "."
  return _node(
    talent_id=talent_id,
    name=f"{label} {talent_type.title()}",
    description=description,
    talent_type=talent_type,
    talent_category=talent_category,
    max_level=max_level,
    cost=cost,
    effects={effect_key: float(bonus_value)},
    tags=[talent_type, "item_based", f"item:{item_name}", "affinity"],
    prerequisites=prerequisites,
  )


def _item_placeholder_node(talent_type: str, item_name: str, node_index: int) -> Dict[str, Any]:
  base = TALENT_TYPE_LABELS.get(talent_type, talent_type.replace("_", " ").title())
  talent_id = f"{talent_type}_placeholder_{node_index:03d}"
  return _node(
    talent_id=talent_id,
    name=f"{base} Item Slot {node_index}",
    description=(
      f"Placeholder item-based '{base}' node using lineage '{item_name}'. "
      "Implement concrete logic in the next pass."
    ),
    talent_type=talent_type,
    talent_category=TALENT_PATH_CATEGORY.get(talent_type, "effects"),
    is_placeholder=True,
    cost=1,
    effects={},
    tags=[talent_type, "item_based", "placeholder", f"item:{_normalize_talent_id(item_name)}"],
  )


def _core_nodes() -> List[Dict[str, Any]]:
  nodes: List[Dict[str, Any]] = [
    _node(
      "forager_sense",
      "Forager's Lens of Plenty",
      (
        "Item-based scouting lens that increases foraging material rolls by item value. "
        "Use when consuming foraging amplifiers."
      ),
      "nature",
      talent_category="utility",
      max_level=3,
      cost=1,
      effects={"forage_attempts_per_level": 1.0},
      tags=["foraging", "item_based", "consumable"],
    ),
    _node(
      "calm_ritual",
      "Calm Ward Totem",
      (
        "Item-based warding charm that lowers foraging misfire chance when a relic item is equipped."
      ),
      "shadows",
      talent_category="effects",
      max_level=2,
      cost=1,
      effects={"forage_calm_chance": 0.06},
      tags=["foraging", "item_based", "trinket", "risk_control"],
    ),
    _node(
      "forge_focus",
      "Stabilized Focal Lens",
      (
        "Item-mounted focus lens for improved slot rerolls and upgrade stability during smithing."
      ),
      "forge",
      talent_category="utility",
      max_level=2,
      cost=2,
      effects={"slot_focus_bonus": 1.0},
      tags=["forging", "item_based", "upgrade"],
    ),
    _node(
      "merchant_bargain",
      "Merchant-Coin Sigil",
      (
        "A coin-bearing sigil item that lowers marketplace listing cost by 1 shell per transaction."
      ),
      "luck",
      talent_category="utility",
      max_level=1,
      cost=1,
      effects={"market_fee_discount": 1},
      tags=["trade", "item_based", "market"],
    ),
  ]

  elemental_nodes = [
    ("water", "elemental_affinity", 1.0, "Water tags gain +1 affinity on forged item rolls.", 1, 1),
    ("wind", "elemental_affinity", 1.0, "Wind tags gain +1 affinity on forged item rolls.", 1, 1),
    ("fire", "elemental_affinity", 1.0, "Fire tags gain +1 affinity on forged item rolls.", 1, 1),
    ("earth", "elemental_affinity", 1.0, "Earth tags gain +1 affinity on forged item rolls.", 1, 1),
    ("lightning", "elemental_affinity", 1.0, "Lightning tags gain +1 affinity on forged item rolls.", 1, 1),
    ("ice", "elemental_affinity", 1.0, "Ice tags gain +1 affinity on forged item rolls.", 1, 1),
    ("poison", "elemental_affinity", 1.0, "Poison tags gain +1 affinity on forged item rolls.", 1, 1),
    ("arcane", "elemental_affinity", 1.0, "Arcane tags gain +1 affinity on forged item rolls.", 1, 1),
    ("void", "elemental_affinity", 1.0, "Void tags gain +1 affinity on forged item rolls.", 1, 1),
    ("holy", "elemental_affinity", 1.0, "Holy tags gain +1 affinity on forged item rolls.", 1, 1),
    ("steam", "elemental_damage_bonus", 0.08, "Steam-tagged items gain +8% elemental damage.", 1, 1),
    ("magma", "forge_output_bonus", 0.06, "Magma-tagged items increase core forge result value by 6%.", 2, 2),
    ("gale", "forging_speed_bonus", 0.05, "Gale items improve forging speed by 5%.", 1, 1),
    ("tempest", "slot_stability_bonus", 0.07, "Tempest items add +0.07 stability to volatile slot outcomes.", 2, 2),
    ("frost_salt", "critical_chance_bonus", 0.03, "Frost Salt nodes increase elemental critical chance by 3%.", 1, 1),
    ("ember", "elemental_affinity", 1.0, "Ember tags gain +1 affinity on forged item rolls.", 1, 1),
    ("haze", "elemental_resistance_bonus", 0.04, "Haze items improve elemental resistance gains in final calibration.", 1, 1),
    ("brine", "forage_element_bonus", 0.05, "Brine synergy increases foraging success odds for water-themed craft attempts.", 2, 1),
    ("crystal_core", "durability_bonus", 0.06, "Crystal-anchored elements raise final item durability by 6%.", 1, 1),
    ("ashfall", "burn_bonus", 0.04, "Ashfall-laced components raise burn-style roll quality by 4%.", 1, 1),
    ("aether", "magic_flux_bonus", 0.07, "Aether components raise high-variance magic-flux rolls by 7%.", 1, 2),
    ("rime", "forge_cost_reduction", 0.05, "Rime-aligned lineage lowers expensive forge reroll penalties by 5%.", 1, 2),
  ]
  for index, item_config in enumerate(elemental_nodes, start=1):
    item_name = item_config[0]
    bonus_key = item_config[1]
    bonus_value = item_config[2]
    suffix = item_config[3]
    max_level = item_config[4]
    cost = item_config[5]
    nodes.append(
      _item_talent(
        "elemental",
        item_name,
        index=index,
        bonus_key=bonus_key,
        bonus_value=bonus_value,
        description_suffix=suffix,
        max_level=max_level,
        cost=cost,
        talent_category=TALENT_PATH_CATEGORY.get("elemental", "effects"),
      )
    )
  return nodes


def _build_talent_tree() -> OrderedDict[str, Dict[str, Any]]:
  tree: OrderedDict[str, Dict[str, Any]] = OrderedDict()
  for talent in _core_nodes():
    if talent["id"] in tree:
      raise ValueError(f"Duplicate talent id: {talent['id']}")
    tree[talent["id"]] = talent

  for talent_type in TALENT_TYPE_LABELS:
    current_count = len([node for node in tree.values() if node["talent_type"] == talent_type])
    if current_count > NODES_PER_TYPE:
      raise ValueError(
        f"Talent type '{talent_type}' has {current_count} custom nodes, "
        f"but NODES_PER_TYPE is {NODES_PER_TYPE}."
      )
    for index in range(1, NODES_PER_TYPE - current_count + 1):
      item_name = f"{talent_type}_item_lineage_{index:03d}"
      talent = _item_placeholder_node(talent_type, item_name, index=index)
      node_id = talent["id"]
      if node_id in tree:
        raise ValueError(f"Duplicate generated placeholder id: {node_id}")
      tree[node_id] = talent

  # sort by path first so CLI display remains grouped and deterministic
  ordered: OrderedDict[str, Dict[str, Any]] = OrderedDict()
  for talent_type in TALENT_TYPE_LABELS:
    for node in tree.values():
      if node["talent_type"] == talent_type:
        ordered[node["id"]] = node
  return ordered


if NODES_PER_TYPE > MAX_NODES_PER_TYPE:
  raise ValueError(f"NODES_PER_TYPE ({NODES_PER_TYPE}) cannot exceed MAX_NODES_PER_TYPE ({MAX_NODES_PER_TYPE}).")


TALENT_TREE: OrderedDict[str, Dict[str, Any]] = _build_talent_tree()
TALENTS_BY_TYPE: OrderedDict[str, List[Dict[str, Any]]] = OrderedDict(
  (talent_type, [node for node in TALENT_TREE.values() if node["talent_type"] == talent_type])
  for talent_type in TALENT_TYPE_LABELS
)
TALENTS_BY_CATEGORY: OrderedDict[str, List[Dict[str, Any]]] = OrderedDict(
  (category, [node for node in TALENT_TREE.values() if node.get("talent_category") == category])
  for category in TALENT_CATEGORIES
)


def talent_node(talent_id: str) -> Dict[str, Any] | None:
  return TALENT_TREE.get(_normalize_talent_id(talent_id))


def talent_level(player_talents: Mapping[str, int], talent_id: str) -> int:
  if not isinstance(player_talents, Mapping):
    return 0
  return int(player_talents.get(_normalize_talent_id(talent_id), 0) or 0)


def talent_bonus(player_talents: Mapping[str, int], talent_id: str, effect_key: str, default: float = 0.0) -> float:
  node = talent_node(talent_id)
  if node is None:
    return default
  raw_value = node.get("effects", {}).get(effect_key)
  if not isinstance(raw_value, (int, float)):
    return default
  return talent_level(player_talents, talent_id) * float(raw_value)


def talent_nodes_for_type(talent_type: str) -> List[Dict[str, Any]]:
  return list(TALENTS_BY_TYPE.get(_normalize_talent_id(talent_type), []))


def talent_nodes_for_category(talent_category: str) -> List[Dict[str, Any]]:
  return list(TALENTS_BY_CATEGORY.get(_normalize_talent_id(talent_category), []))


def talent_types() -> Iterable[str]:
  return TALENT_TYPE_LABELS.keys()
