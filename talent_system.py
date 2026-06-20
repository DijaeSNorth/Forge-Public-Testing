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
  level_weight_interval: int | None = None,
  level_weight_multiplier: float = 1.0,
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
    "level_weight_interval": int(level_weight_interval) if level_weight_interval else None,
    "level_weight_multiplier": float(level_weight_multiplier),
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
  level_weight_interval: int | None = None,
  level_weight_multiplier: float = 1.0,
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
    level_weight_interval=level_weight_interval,
    level_weight_multiplier=level_weight_multiplier,
  )


def _item_placeholder_node(
  talent_type: str,
  item_name: str,
  node_index: int,
  *,
  max_level: int = 1,
  level_weight_interval: int = 5,
  level_weight_multiplier: float = 2.0,
) -> Dict[str, Any]:
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
    max_level=max_level,
    level_weight_interval=level_weight_interval,
    level_weight_multiplier=level_weight_multiplier,
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
    ("water", "elemental_affinity", 1.0, "Applies to forged items with water resonance.", 10, 1),
    ("wind", "elemental_affinity", 1.0, "Applies to forged items with wind resonance.", 10, 1),
    ("fire", "elemental_affinity", 1.0, "Applies to forged items with fire resonance.", 10, 1),
    ("earth", "elemental_affinity", 1.0, "Applies to forged items with earth resonance.", 10, 1),
    ("lightning", "elemental_affinity", 1.0, "Applies to forged items with lightning resonance.", 10, 1),
    ("ice", "elemental_affinity", 1.0, "Applies to forged items with ice resonance.", 10, 1),
    ("poison", "elemental_affinity", 1.0, "Applies to forged items with poison resonance.", 10, 1),
    ("arcane", "elemental_affinity", 1.0, "Applies to forged items with arcane resonance.", 10, 1),
    ("void", "elemental_affinity", 1.0, "Applies to forged items with void resonance.", 10, 1),
    ("holy", "elemental_affinity", 1.0, "Applies to forged items with holy resonance.", 10, 1),
  ]
  for index, item_config in enumerate(elemental_nodes, start=1):
    item_name = item_config[0]
    bonus_key = item_config[1]
    bonus_value = item_config[2]
    suffix = item_config[3]
    max_level = item_config[4]
    cost = item_config[5]
    multiplier = 3.0 if index <= 5 else 2.25
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
        level_weight_interval=5,
        level_weight_multiplier=multiplier,
      )
    )
  return nodes


def _build_talent_tree() -> OrderedDict[str, Dict[str, Any]]:
  tree: OrderedDict[str, Dict[str, Any]] = OrderedDict()
  for talent in _core_nodes():
    if talent["id"] in tree:
      raise ValueError(f"Duplicate talent id: {talent['id']}")
    tree[talent["id"]] = talent

  template_upgrade_levels = 10
  for talent_type in TALENT_TYPE_LABELS:
    budget_used = sum(
      int(node.get("max_level", 1))
      for node in tree.values()
      if node["talent_type"] == talent_type
    )
    if budget_used > NODES_PER_TYPE:
      raise ValueError(
        f"Talent type '{talent_type}' has {budget_used} talent levels, "
        f"but NODES_PER_TYPE is {NODES_PER_TYPE}."
      )
    placeholder_index = 1
    while budget_used < NODES_PER_TYPE:
      remaining = NODES_PER_TYPE - budget_used
      placeholder_level = template_upgrade_levels if remaining >= template_upgrade_levels else remaining
      item_name = f"{talent_type}_template_upgrade_{placeholder_index:02d}"
      talent = _item_placeholder_node(
        talent_type,
        item_name,
        index=placeholder_index,
        max_level=placeholder_level,
      )
      node_id = talent["id"]
      if node_id in tree:
        raise ValueError(f"Duplicate generated placeholder id: {node_id}")
      tree[node_id] = talent
      budget_used += placeholder_level
      placeholder_index += 1

  # sort by path first so CLI display remains grouped and deterministic
  ordered: OrderedDict[str, Dict[str, Any]] = OrderedDict()
  for talent_type in TALENT_TYPE_LABELS:
    for node in tree.values():
      if node["talent_type"] == talent_type:
        ordered[node["id"]] = node
  return ordered


def _weighted_talent_bonus(level: int, base_value: float, node: Dict[str, Any]) -> float:
  interval = int(node.get("level_weight_interval") or 0)
  if interval <= 0:
    return level * base_value
  multiplier = float(node.get("level_weight_multiplier") or 1.0)
  if multiplier == 1.0:
    return level * base_value
  total = 0.0
  for current_level in range(1, level + 1):
    if current_level % interval == 0:
      total += base_value * multiplier
    else:
      total += base_value
  return total

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


def total_talent_levels(player_talents: Mapping[str, int]) -> int:
  """Return the total level investment across all known talent nodes."""
  if not isinstance(player_talents, Mapping):
    return 0
  total = 0
  for raw_talent_id, raw_level in player_talents.items():
    if not isinstance(raw_talent_id, str):
      continue
    node = talent_node(raw_talent_id)
    if node is None:
      continue
    max_level = int(node.get("max_level", 0))
    level = raw_level if isinstance(raw_level, int) else 0
    if max_level > 0:
      total += max(0, min(level, max_level))
    else:
      total += max(0, level)
  return total


def talent_bonus(player_talents: Mapping[str, int], talent_id: str, effect_key: str, default: float = 0.0) -> float:
  node = talent_node(talent_id)
  if node is None:
    return default
  raw_value = node.get("effects", {}).get(effect_key)
  if not isinstance(raw_value, (int, float)):
    return default
  return _weighted_talent_bonus(
    talent_level(player_talents, talent_id),
    float(raw_value),
    node,
  )


def talent_nodes_for_type(talent_type: str) -> List[Dict[str, Any]]:
  return list(TALENTS_BY_TYPE.get(_normalize_talent_id(talent_type), []))


def talent_nodes_for_category(talent_category: str) -> List[Dict[str, Any]]:
  return list(TALENTS_BY_CATEGORY.get(_normalize_talent_id(talent_category), []))


def talent_types() -> Iterable[str]:
  return TALENT_TYPE_LABELS.keys()





