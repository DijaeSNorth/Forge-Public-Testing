from __future__ import annotations

from dataclasses import dataclass, field, asdict
from enum import Enum
from typing import Any, Dict, List, Optional, Sequence, Tuple
import hashlib
import json
import random
import time
import uuid


class AssetClass(Enum):
  MYTHICAL_TOOL = "mythical_tool"
  PRACTICAL_TOOL = "practical_tool"
  WEAPON = "weapon"
  VEHICLE = "vehicle"
  ACCESSORY = "accessory"
  GENERIC = "generic"


class Rarity(Enum):
  COMMON = "common"
  UNCOMMON = "uncommon"
  RARE = "rare"
  EPIC = "epic"
  LEGENDARY = "legendary"
  MYTHIC = "mythic"


PORT_ADAPTERS: Dict[str, Dict[str, Any]] = {
  "universal": {
    "stat_aliases": {},
    "required_caps": ["core_asset_fields", "craft_process"],
    "notes": "Raw canonical asset schema.",
  },
  "rpg_world": {
    "stat_aliases": {"damage": "attack", "durability": "defense", "range": "reach", "weight": "encumbrance"},
    "required_caps": ["inventory", "character_equip", "craft_process"],
    "notes": "Adapter for RPG-style games with attack/defense semantics.",
  },
  "vehicle_arena": {
    "stat_aliases": {"damage": "impact", "speed": "top_speed", "range": "distance", "fuel": "energy_efficiency", "handling": "handling"},
    "required_caps": ["vehicle_system", "drivability", "craft_process"],
    "notes": "Adapter for vehicle-focused titles.",
  },
  "factory_sim": {
    "stat_aliases": {"precision": "quality", "stability": "yield", "durability": "lifespan"},
    "required_caps": ["craftable", "recipe_id", "craft_process"],
    "notes": "Adapter for production/assembly simulation games.",
  },
}

RARITY_SORT_ORDER: Tuple[Rarity, ...] = (
  Rarity.COMMON,
  Rarity.UNCOMMON,
  Rarity.RARE,
  Rarity.EPIC,
  Rarity.LEGENDARY,
  Rarity.MYTHIC,
)
RARITY_SORT_INDEX: Dict[Rarity, int] = {rarity: index for index, rarity in enumerate(RARITY_SORT_ORDER)}


def _now() -> float:
  return time.time()


def _hash_payload(payload: Dict[str, Any]) -> str:
  body = json.dumps(payload, sort_keys=True, separators=(",", ":"))
  return hashlib.sha256(body.encode("utf-8")).hexdigest()


def parse_asset_class(value: Any) -> AssetClass:
  if isinstance(value, AssetClass):
    return value
  if isinstance(value, str):
    normalized = value.strip().upper()
    if normalized in AssetClass.__members__:
      return AssetClass[normalized]
    if normalized in {member.value.upper() for member in AssetClass}:
      return AssetClass(normalized.lower())
  raise ValueError(f"Unknown asset class: {value!r}")


def parse_rarity(value: Any) -> Rarity:
  if isinstance(value, Rarity):
    return value
  if isinstance(value, str):
    normalized = value.strip().upper()
    if normalized in Rarity.__members__:
      return Rarity[normalized]
  raise ValueError(f"Unknown rarity: {value!r}")


def parse_asset_category(value: Any) -> str:
  if value is None:
    return ""
  if not isinstance(value, str):
    raise ValueError(f"Unknown category: {value!r}")
  return value.strip().lower().replace(" ", "_").replace("-", "_")


@dataclass(frozen=True)
class CraftingSource:
  source_id: str
  display_name: str
  category: str
  is_mythical: bool
  is_real_world: bool
  process_steps: List[Dict[str, Any]]
  materials: List[Dict[str, Any]]
  tools: List[str]
  requirements: List[str]
  stat_bonuses: Dict[str, float]
  stat_multipliers: Dict[str, float]
  risk_level: float
  yield_bonus: float
  enhancements: List[Dict[str, Any]]
  notes: str = ""

  def to_dict(self) -> Dict[str, Any]:
    return {
      "source_id": self.source_id,
      "display_name": self.display_name,
      "category": self.category,
      "is_mythical": self.is_mythical,
      "is_real_world": self.is_real_world,
      "process_steps": [dict(step) for step in self.process_steps],
      "materials": [dict(material) for material in self.materials],
      "tools": list(self.tools),
      "requirements": list(self.requirements),
      "stat_bonuses": dict(self.stat_bonuses),
      "stat_multipliers": dict(self.stat_multipliers),
      "risk_level": self.risk_level,
      "yield_bonus": self.yield_bonus,
      "enhancements": [dict(item) for item in self.enhancements],
      "notes": self.notes,
    }


@dataclass(frozen=True)
class AssetBlueprint:
  key: str
  display_name: str
  asset_class: AssetClass
  category: str = "misc"
  base_stats: Dict[str, float]
  lore: str = ""
  is_mythical: bool = False
  default_rarity: Rarity = Rarity.UNCOMMON
  compatibility: List[str] = field(default_factory=lambda: ["universal"])
  program_template: List[Dict[str, Any]] = field(default_factory=list)
  crafting_sources: List[CraftingSource] = field(default_factory=list)
  practical_process_tag: str = "general_fabrication"
  addon_slots: List[Dict[str, Any]] = field(default_factory=list)

  def to_dict(self) -> Dict[str, Any]:
    return {
      "key": self.key,
      "display_name": self.display_name,
      "asset_class": self.asset_class.value,
      "category": self.category,
      "base_stats": dict(self.base_stats),
      "lore": self.lore,
      "is_mythical": self.is_mythical,
      "default_rarity": self.default_rarity.value,
      "compatibility": list(self.compatibility),
      "program_template": [dict(step) for step in self.program_template],
      "crafting_sources": [source.to_dict() for source in self.crafting_sources],
      "practical_process_tag": self.practical_process_tag,
      "addon_slots": [dict(slot) for slot in self.addon_slots],
    }


@dataclass
class NFToken:
  token_id: str
  chain: str
  minted_at: float
  owner: str
  provenance_hash: str
  metadata_uri: str

  def to_dict(self) -> Dict[str, Any]:
    return asdict(self)


@dataclass
class ForgedAsset:
  asset_id: str
  blueprint_key: str
  name: str
  owner: str
  asset_class: AssetClass
  rarity: Rarity
  category: str = "misc"
  is_mythical: bool
  tags: List[str]
  stats: Dict[str, float]
  program: List[Dict[str, Any]]
  created_at: float
  version: int
  provenance_signature: str
  crafting_source_id: Optional[str] = None
  applied_enhancements: List[Dict[str, Any]] = field(default_factory=list)
  magic_effects: List[Dict[str, Any]] = field(default_factory=list)
  mythical_materials_used: List[Dict[str, Any]] = field(default_factory=list)
  addon_slots_filled: List[Dict[str, Any]] = field(default_factory=list)
  minted: bool = False
  nft: Optional[NFToken] = None

  def to_dict(self, include_token: bool = True) -> Dict[str, Any]:
    data: Dict[str, Any] = {
      "asset_id": self.asset_id,
      "blueprint_key": self.blueprint_key,
      "name": self.name,
      "owner": self.owner,
      "asset_class": self.asset_class.value,
      "rarity": self.rarity.value,
      "category": self.category,
      "is_mythical": self.is_mythical,
      "tags": list(self.tags),
      "stats": dict(self.stats),
      "program": [dict(step) for step in self.program],
      "created_at": self.created_at,
      "version": self.version,
      "provenance_signature": self.provenance_signature,
      "crafting_source_id": self.crafting_source_id,
      "applied_enhancements": [dict(item) for item in self.applied_enhancements],
      "magic_effects": [dict(item) for item in self.magic_effects],
      "mythical_materials_used": [dict(item) for item in self.mythical_materials_used],
      "addon_slots_filled": [dict(item) for item in self.addon_slots_filled],
      "minted": self.minted,
    }
    if include_token and self.nft:
      data["nft"] = self.nft.to_dict()
    return data


class GameLogic:
  """Terminal-first forge engine for portable game assets and NFT metadata."""

  def __init__(self):
    self.blueprints: Dict[str, AssetBlueprint] = {}
    self.assets: Dict[str, ForgedAsset] = {}
    self._asset_seq = 0

  def create_blueprint(
      self,
      key: str,
      display_name: str,
      asset_class: AssetClass | str,
      base_stats: Dict[str, float],
      lore: str = "",
      is_mythical: bool = False,
      default_rarity: Rarity | str = Rarity.UNCOMMON,
      compatibility: Optional[Sequence[str]] = None,
      program_template: Optional[Sequence[Dict[str, Any]]] = None,
      crafting_sources: Optional[Sequence[Dict[str, Any]]] = None,
      practical_process_tag: str = "general_fabrication",
      category: str | None = None,
      addon_slots: Optional[Sequence[Dict[str, Any]]] = None,
  ) -> AssetBlueprint:
    if key in self.blueprints:
      raise ValueError(f"Blueprint '{key}' already exists.")
    parsed_class = parse_asset_class(asset_class)
    parsed_category = self._normalize_category(category, parsed_class)
    parsed_rarity = parse_rarity(default_rarity)
    payload_stats = self._normalize_stats(dict(base_stats))

    sources = self._normalize_crafting_sources(crafting_sources, fallback_tag=key)
    normalized_slots = self._normalize_addon_slots(addon_slots, fallback_key=key)
    blueprint = AssetBlueprint(
      key=key,
      display_name=display_name,
      asset_class=parsed_class,
      category=parsed_category,
      base_stats=payload_stats,
      lore=lore,
      is_mythical=is_mythical,
      default_rarity=parsed_rarity,
      compatibility=list(compatibility) if compatibility else ["universal"],
      program_template=[dict(step) for step in (program_template or [])],
      crafting_sources=sources,
      practical_process_tag=practical_process_tag,
      addon_slots=normalized_slots,
    )
    self.blueprints[key] = blueprint
    return blueprint

  def forge_asset(
      self,
      *,
      blueprint_key: str,
      owner: str,
      name: Optional[str] = None,
      rarity: Rarity | str | None = None,
      stat_overrides: Optional[Dict[str, float]] = None,
      tags: Optional[Sequence[str]] = None,
      custom_program: Optional[Sequence[Dict[str, Any]]] = None,
      crafting_source_id: Optional[str] = None,
      addons: Optional[Sequence[Dict[str, Any]]] = None,
      slot_roll_seed: Optional[int] = None,
      slot_rolls: Optional[Dict[str, int]] = None,
      lock_slots: Optional[Sequence[str]] = None,
  ) -> str:
    if blueprint_key not in self.blueprints:
      raise KeyError(f"Blueprint '{blueprint_key}' not found.")

    blueprint = self.blueprints[blueprint_key]
    source = self._pick_crafting_source(blueprint, crafting_source_id)

    selected_rarity = parse_rarity(rarity) if rarity else blueprint.default_rarity
    mythical_materials = self._find_mythical_materials(source.materials)
    normalized_addons = self._normalize_addons(addons or [], blueprint_key=blueprint_key)
    slot_fills = self._fill_addon_slots(blueprint, source, normalized_addons, mythical_materials)
    slot_roll_budget = self._normalize_slot_roll_overrides(slot_rolls, blueprint=blueprint)
    locked_slots = set(self._normalize_string_list(lock_slots or [], "lock_slots"))
    rng = random.Random(slot_roll_seed) if slot_roll_seed is not None else random.Random()
    self._apply_magic_rolls(
      blueprint=blueprint,
      source=source,
      slot_fills=slot_fills,
      rng=rng,
      slot_roll_budget=slot_roll_budget,
      slot_roll_seed=slot_roll_seed,
      locked_slots=locked_slots,
    )

    mythics_for_upgrade = list(mythical_materials)
    for fill in slot_fills:
      if not fill.get("is_mythical"):
        continue
      if fill.get("source") == "addon":
        source_payload = fill.get("addon", {}).get("source_payload")
        if source_payload:
          mythics_for_upgrade.append(dict(source_payload))
      elif fill.get("source") == "mythical_material":
        material_payload = fill.get("mythic_material")
        if material_payload:
          mythics_for_upgrade.append(dict(material_payload))

    merged_stats = dict(blueprint.base_stats)
    merged_stats = self._apply_crafting_bonuses(merged_stats, source)
    merged_stats = self._apply_slot_bonuses(merged_stats, slot_fills)
    final_rarity = self._upgrade_rarity(selected_rarity, mythics_for_upgrade)

    if stat_overrides:
      merged_stats.update(self._normalize_stats(stat_overrides))

    self._asset_seq += 1
    asset_id = f"AST-{self._asset_seq:04d}-{uuid.uuid4().hex[:6].upper()}"
    now = _now()
    created_name = name or blueprint.display_name

    asset = ForgedAsset(
      asset_id=asset_id,
      blueprint_key=blueprint_key,
      name=created_name,
      owner=owner,
      asset_class=blueprint.asset_class,
      rarity=final_rarity,
      category=blueprint.category,
      is_mythical=blueprint.is_mythical or source.is_mythical or bool(mythics_for_upgrade),
      tags=list(tags or []),
      stats=merged_stats,
      program=self._normalize_program(list(blueprint.program_template) + list(custom_program or [])),
      created_at=now,
      version=1,
      provenance_signature="",
      crafting_source_id=source.source_id,
      applied_enhancements=[dict(item) for item in source.enhancements],
      magic_effects=self._magic_effects_for_source(source) + self._magic_effects_from_slots(slot_fills),
      mythical_materials_used=[dict(item) for item in mythics_for_upgrade],
      addon_slots_filled=[dict(fill) for fill in slot_fills],
    )
    asset.provenance_signature = self._calculate_provenance(asset, source)
    self.assets[asset_id] = asset
    return asset_id

  def program_asset(self, asset_id: str, steps: Sequence[Dict[str, Any]]) -> Dict[str, Any]:
    if asset_id not in self.assets:
      raise KeyError(f"Asset '{asset_id}' not found.")
    if not steps:
      raise ValueError("Program steps cannot be empty.")
    normalized = self._normalize_program([dict(step) for step in steps])
    self.assets[asset_id].program.extend(normalized)
    self.assets[asset_id].version += 1
    source = self._find_source(self.assets[asset_id].blueprint_key, self.assets[asset_id].crafting_source_id)
    self.assets[asset_id].provenance_signature = self._calculate_provenance(self.assets[asset_id], source)
    return self.assets[asset_id].to_dict()

  def set_slot_lock(self, asset_id: str, slot_id: str, *, locked: bool = True) -> Dict[str, Any]:
    asset = self._get_asset(asset_id)
    fill = self._get_slot_fill(asset, slot_id)
    previous = bool(fill.get("slot_locked", False))
    requested = bool(locked)
    if previous == requested:
      return asset.to_dict()

    fill["slot_locked"] = requested
    asset.version += 1
    source = self._find_source(asset.blueprint_key, asset.crafting_source_id)
    asset.provenance_signature = self._calculate_provenance(asset, source)
    return asset.to_dict()

  def reroll_slot_magic(
      self,
      asset_id: str,
      slot_ids: Optional[Sequence[str]] = None,
      *,
      seed: Optional[int] = None,
  ) -> Dict[str, Any]:
    asset = self._get_asset(asset_id)
    if slot_ids is None:
      slot_set = None
    else:
      slot_set = {str(slot_id).strip().lower() for slot_id in slot_ids if str(slot_id).strip()}
      if not slot_set:
        slot_set = None

    blueprint = self.blueprints.get(asset.blueprint_key)
    if not blueprint:
      raise KeyError(f"Blueprint '{asset.blueprint_key}' not found for asset '{asset_id}'.")
    source = self._find_source(blueprint.key, asset.crafting_source_id)
    if source is None:
      raise RuntimeError(f"Blueprint '{blueprint.key}' has no source information.")

    rng = random.Random(seed) if seed is not None else random.Random()
    changed = False
    for fill in asset.addon_slots_filled:
      slot_id = str(fill.get("slot_id") or "").strip().lower()
      if not slot_id:
        continue
      if slot_set is not None and slot_id not in slot_set:
        continue
      if bool(fill.get("slot_locked", False)):
        continue
      existing_rolls = self._safe_roll_count(fill.get("magic_roll_count"), f"slot '{slot_id}' roll count", minimum=0, default=0)
      self._set_slot_magic_rolls(
        fill=fill,
        blueprint=blueprint,
        source=source,
        roll_count=existing_rolls,
        rng=rng,
        seed=seed,
      )
      changed = True

    if not changed:
      raise ValueError("No unlocked slots were rerolled. Check slot_ids and lock state.")

    asset.version += 1
    asset.magic_effects = self._magic_effects_for_source(source) + self._magic_effects_from_slots(asset.addon_slots_filled)
    asset.provenance_signature = self._calculate_provenance(asset, source)
    return asset.to_dict()

  def increase_slot_rolls(
      self,
      asset_id: str,
      slot_id: str,
      *,
      additional_rolls: int = 1,
      seed: Optional[int] = None,
  ) -> Dict[str, Any]:
    asset = self._get_asset(asset_id)
    blueprint = self.blueprints.get(asset.blueprint_key)
    if not blueprint:
      raise KeyError(f"Blueprint '{asset.blueprint_key}' not found for asset '{asset_id}'.")
    source = self._find_source(blueprint.key, asset.crafting_source_id)
    if source is None:
      raise RuntimeError(f"Blueprint '{blueprint.key}' has no source information.")

    fill = self._get_slot_fill(asset, slot_id)
    slot_spec = self._get_slot_spec(blueprint, str(slot_id))
    max_roll_count = self._safe_roll_count(slot_spec.get("max_magic_rolls"), f"slot '{slot_id}' max_roll_count", default=3, minimum=0)
    current_roll_count = self._safe_roll_count(fill.get("magic_roll_count"), f"slot '{slot_id}' roll count", default=0, minimum=0)
    request = self._safe_roll_count(additional_rolls, "additional_rolls", minimum=1)

    if current_roll_count >= max_roll_count:
      raise ValueError(f"Slot '{slot_id}' is already at max roll count ({max_roll_count}).")

    next_roll_count = min(current_roll_count + request, max_roll_count)
    fill["magic_roll_count"] = next_roll_count
    self._set_slot_magic_rolls(
      fill=fill,
      blueprint=blueprint,
      source=source,
      roll_count=next_roll_count,
      rng=random.Random(seed) if seed is not None else random.Random(),
      seed=seed,
      preserve_previous=True,
    )

    asset.version += 1
    asset.magic_effects = self._magic_effects_for_source(source) + self._magic_effects_from_slots(asset.addon_slots_filled)
    asset.provenance_signature = self._calculate_provenance(asset, source)
    return asset.to_dict()

  def mint_asset_nft(self, asset_id: str, *, chain: str = "local", contract_hint: Optional[str] = None) -> Dict[str, Any]:
    if asset_id not in self.assets:
      raise KeyError(f"Asset '{asset_id}' not found.")
    asset = self.assets[asset_id]
    if asset.minted and asset.nft:
      return asset.nft.to_dict()

    source = self._find_source(asset.blueprint_key, asset.crafting_source_id)
    mint_payload = {
      "asset_id": asset.asset_id,
      "asset_signature": asset.provenance_signature,
      "owner": asset.owner,
      "version": asset.version,
      "crafting_source_id": asset.crafting_source_id,
      "chain": chain,
      "contract_hint": contract_hint or "demo-contract",
      "rarity": asset.rarity.value,
      "source_signature": source.source_id,
    }
    token_id = _hash_payload(mint_payload)[:32]
    metadata_uri = f"asset-nft://{chain}/{token_id}"
    token = NFToken(
      token_id=token_id,
      chain=chain,
      minted_at=_now(),
      owner=asset.owner,
      provenance_hash=asset.provenance_signature,
      metadata_uri=metadata_uri,
    )
    asset.minted = True
    asset.nft = token
    return token.to_dict()

  def export_portable_payload(self, asset_id: str, target_game: str = "universal") -> Dict[str, Any]:
    if asset_id not in self.assets:
      raise KeyError(f"Asset '{asset_id}' not found.")
    if target_game not in PORT_ADAPTERS:
      raise ValueError(f"Unknown target game profile: {target_game}")

    asset = self.assets[asset_id]
    blueprint = self.blueprints[asset.blueprint_key]
    source = self._find_source(blueprint.key, asset.crafting_source_id)
    adapter = PORT_ADAPTERS[target_game]
    stat_aliases = adapter["stat_aliases"]
    mapped_stats = {stat_aliases.get(name, name): value for name, value in asset.stats.items()}
    compatible = target_game in blueprint.compatibility or "universal" in blueprint.compatibility
    payload = {
      "portable_schema_version": "1.1.0",
      "source_game": "terminal_forge_logic",
      "target_game": target_game,
      "asset_manifest": {
        "asset_id": asset.asset_id,
        "blueprint_key": asset.blueprint_key,
        "name": asset.name,
        "asset_class": asset.asset_class.value,
        "category": asset.category,
        "rarity": asset.rarity.value,
        "is_mythical": asset.is_mythical,
        "owner": asset.owner,
        "version": asset.version,
        "tags": list(asset.tags),
        "stats": mapped_stats,
        "program": [dict(step) for step in asset.program],
        "lore": blueprint.lore,
        "created_at": asset.created_at,
        "provenance_signature": asset.provenance_signature,
        "crafting_source": source.to_dict() if source else None,
        "applied_enhancements": [dict(item) for item in asset.applied_enhancements],
        "magic_effects": [dict(item) for item in asset.magic_effects],
        "mythical_materials_used": [dict(item) for item in asset.mythical_materials_used],
        "addon_slots_filled": [dict(item) for item in asset.addon_slots_filled],
      },
      "compatibility": {
        "target_supported": compatible,
        "required_caps": adapter["required_caps"],
        "adapter_notes": adapter["notes"],
      },
      "blueprint": blueprint.to_dict(),
      "nft": asset.nft.to_dict() if asset.nft else None,
    }
    if not compatible:
      payload["compatibility"]["warning"] = f"Asset not tagged for {target_game}. Importer should validate transform behavior."
    return payload

  def get_asset(self, asset_id: str) -> ForgedAsset:
    if asset_id not in self.assets:
      raise KeyError(f"Asset '{asset_id}' not found.")
    return self.assets[asset_id]

  def list_blueprints(
      self,
      *,
      category: str | None = None,
      rarity: Rarity | str | None = None,
  ) -> List[Dict[str, Any]]:
    category_filter = parse_asset_category(category) if category else ""
    rarity_filter = parse_rarity(rarity) if rarity is not None else None
    blueprints = list(self.blueprints.values())
    if category_filter:
      blueprints = [blueprint for blueprint in blueprints if blueprint.category == category_filter]
    if rarity_filter is not None:
      blueprints = [blueprint for blueprint in blueprints if blueprint.default_rarity == rarity_filter]
    blueprints = sorted(blueprints, key=self._blueprint_sort_key)
    return [blueprint.to_dict() for blueprint in blueprints]

  def list_assets(
      self,
      *,
      category: str | None = None,
      rarity: Rarity | str | None = None,
  ) -> List[Dict[str, Any]]:
    category_filter = parse_asset_category(category) if category else ""
    rarity_filter = parse_rarity(rarity) if rarity is not None else None
    assets = list(self.assets.values())
    if category_filter:
      assets = [asset for asset in assets if asset.category == category_filter]
    if rarity_filter is not None:
      assets = [asset for asset in assets if asset.rarity == rarity_filter]
    assets = sorted(assets, key=self._asset_sort_key)
    return [asset.to_dict() for asset in assets]

  def _normalize_category(self, category: str | None, asset_class: AssetClass) -> str:
    parsed = parse_asset_category(category)
    if parsed:
      return parsed
    return self._default_category_for_class(asset_class)

  def _default_category_for_class(self, asset_class: AssetClass) -> str:
    if asset_class == AssetClass.WEAPON:
      return "weapon"
    if asset_class in {AssetClass.MYTHICAL_TOOL, AssetClass.PRACTICAL_TOOL}:
      return "tool"
    if asset_class == AssetClass.ACCESSORY:
      return "wearable"
    if asset_class == AssetClass.VEHICLE:
      return "vehicle"
    return "misc"

  def _blueprint_sort_key(self, blueprint: AssetBlueprint) -> Tuple[str, int, str]:
    return (
      blueprint.category,
      RARITY_SORT_INDEX.get(blueprint.default_rarity, 0),
      blueprint.key,
    )

  def _asset_sort_key(self, asset: ForgedAsset) -> Tuple[str, int, str, str]:
    return (
      asset.category,
      RARITY_SORT_INDEX.get(asset.rarity, 0),
      asset.name.lower(),
      asset.asset_id,
    )

  def _get_asset(self, asset_id: str) -> ForgedAsset:
    if asset_id not in self.assets:
      raise KeyError(f"Asset '{asset_id}' not found.")
    return self.assets[asset_id]

  def _get_slot_fill(self, asset: ForgedAsset, slot_id: str) -> Dict[str, Any]:
    normalized = str(slot_id or "").strip().lower()
    if not normalized:
      raise ValueError("slot_id cannot be empty.")
    for fill in asset.addon_slots_filled:
      if str(fill.get("slot_id") or "").strip().lower() == normalized:
        return fill
    raise ValueError(f"Slot '{slot_id}' not found on asset '{asset.asset_id}'.")

  def _get_slot_spec(self, blueprint: AssetBlueprint, slot_id: str) -> Dict[str, Any]:
    normalized = str(slot_id or "").strip().lower()
    for slot in blueprint.addon_slots:
      if str(slot.get("slot_id") or "").strip().lower() == normalized:
        return slot
    return {}

  def _normalize_slot_roll_overrides(
      self,
      raw: Optional[Dict[str, Any]],
      blueprint: AssetBlueprint,
  ) -> Dict[str, int]:
    if raw is None:
      return {}
    if not isinstance(raw, dict):
      raise ValueError("slot_rolls must be an object keyed by slot_id.")
    known_slots = {str(slot.get("slot_id") or "").strip().lower() for slot in blueprint.addon_slots if slot.get("slot_id")}
    overrides: Dict[str, int] = {}
    for key, value in raw.items():
      normalized_key = str(key).strip().lower()
      if not normalized_key:
        continue
      if normalized_key != "default" and normalized_key not in known_slots:
        raise ValueError(f"slot_rolls contains unknown slot '{key}'.")
      overrides[normalized_key] = self._safe_roll_count(
        value,
        f"slot_rolls['{normalized_key}']",
        minimum=0,
      )
    return overrides

  def _apply_magic_rolls(
      self,
      *,
      blueprint: AssetBlueprint,
      source: CraftingSource,
      slot_fills: List[Dict[str, Any]],
      rng: random.Random,
      slot_roll_budget: Dict[str, int],
      slot_roll_seed: Optional[int],
      locked_slots: Sequence[str],
  ) -> None:
    if not slot_fills:
      return
    locked = {str(slot_id).strip().lower() for slot_id in locked_slots}
    for fill in slot_fills:
      slot_id = str(fill.get("slot_id") or "").strip()
      slot_spec = self._get_slot_spec(blueprint, slot_id)

      default_rolls = self._safe_roll_count(
        slot_spec.get("default_magic_rolls"),
        f"slot '{slot_id}' default_magic_rolls",
        default=1,
        minimum=0,
      )
      max_rolls = self._safe_roll_count(
        slot_spec.get("max_magic_rolls"),
        f"slot '{slot_id}' max_magic_rolls",
        default=3,
        minimum=0,
      )
      if max_rolls < default_rolls:
        raise ValueError(f"slot '{slot_id}' max_magic_rolls cannot be less than default_magic_rolls.")

      requested_rolls = slot_roll_budget.get(slot_id.lower())
      if requested_rolls is None:
        requested_rolls = slot_roll_budget.get("default", default_rolls)

      roll_count = self._safe_roll_count(
        requested_rolls,
        f"slot '{slot_id}' requested roll count",
        default=default_rolls,
        minimum=0,
      )
      roll_count = min(roll_count, max_rolls)

      base_magic = self._slot_base_magic_effects(fill)
      fill["base_magic_effects"] = [dict(effect) for effect in base_magic]
      fill["magic_roll_count"] = roll_count
      fill["max_roll_count"] = max_rolls
      fill["slot_locked"] = slot_id.lower() in locked
      fill["magic_roll_seed"] = slot_roll_seed
      fill["magic_rolls"] = self._roll_magic_effects(
        fill=fill,
        source=source,
        roll_count=roll_count,
        rng=rng,
      )
      fill["magic_effects"] = [dict(effect) for effect in fill["base_magic_effects"]] + [
        dict(effect) for effect in fill["magic_rolls"]
      ]

  def _set_slot_magic_rolls(
      self,
      *,
      fill: Dict[str, Any],
      blueprint: AssetBlueprint,
      source: CraftingSource,
      roll_count: int,
      rng: random.Random,
      seed: Optional[int],
      preserve_previous: bool = False,
  ) -> None:
    current_rolls = self._safe_roll_count(fill.get("magic_roll_count"), "current roll_count", default=0, minimum=0)
    requested = self._safe_roll_count(roll_count, "roll_count", minimum=0)
    requested = max(requested, 0)
    if requested < 0:
      raise ValueError("roll_count cannot be negative.")
    slot_id = str(fill.get("slot_id") or "").strip()
    slot_spec = self._get_slot_spec(blueprint, slot_id)
    max_rolls = self._safe_roll_count(
      slot_spec.get("max_magic_rolls"),
      f"slot '{slot_id}' max_magic_rolls",
      default=3,
      minimum=0,
    )
    if requested > max_rolls:
      requested = max_rolls
    if requested < 0:
      requested = 0

    base_magic = self._slot_base_magic_effects(fill)
    fill["base_magic_effects"] = [dict(effect) for effect in base_magic]
    if requested == 0:
      fill["magic_rolls"] = []
    elif preserve_previous:
      previous = [dict(effect) for effect in fill.get("magic_rolls", []) if isinstance(effect, dict)]
      while len(previous) > requested:
        previous.pop()
      while len(previous) < requested:
        additional = self._roll_magic_effects(
          fill=fill,
          source=source,
          roll_count=1,
          rng=rng,
        )
        if not additional:
          break
        previous.extend(additional)
      fill["magic_rolls"] = previous
    else:
      fill["magic_rolls"] = self._roll_magic_effects(
        fill=fill,
        source=source,
        roll_count=requested,
        rng=rng,
      )
    fill["magic_roll_count"] = requested
    fill["magic_roll_seed"] = seed
    fill["magic_effects"] = [dict(effect) for effect in fill["base_magic_effects"]] + [
      dict(effect) for effect in fill["magic_rolls"]
    ]

  def _slot_base_magic_effects(self, fill: Dict[str, Any]) -> List[Dict[str, Any]]:
    base_raw = fill.get("base_magic_effects")
    if base_raw is None:
      base_raw = fill.get("magic_effects", [])
    base_effects: List[Dict[str, Any]] = []
    if not isinstance(base_raw, Sequence) or isinstance(base_raw, (str, bytes, dict)):
      return []
    for effect in base_raw:
      if not isinstance(effect, dict):
        continue
      if effect.get("roll_source") == "slot_roll":
        continue
      if str(effect.get("type") or "").strip().lower() == "mythic_material_slot":
        continue
      base_effects.append(dict(effect))
    return base_effects

  def _roll_magic_effects(
      self,
      *,
      fill: Dict[str, Any],
      source: CraftingSource,
      roll_count: int,
      rng: random.Random,
  ) -> List[Dict[str, Any]]:
    pool = self._magic_roll_pool(fill, source)
    if not pool or roll_count <= 0:
      return []
    rolls: List[Dict[str, Any]] = []
    for _ in range(roll_count):
      chosen = dict(rng.choice(pool))
      chosen["roll_source"] = "slot_roll"
      rolls.append(chosen)
    return rolls

  def _magic_roll_pool(self, fill: Dict[str, Any], source: Optional[CraftingSource]) -> List[Dict[str, Any]]:
    pool: List[Dict[str, Any]] = []
    for effect in self._slot_base_magic_effects(fill):
      if isinstance(effect, dict):
        pool.append(dict(effect))
    if source and source.is_mythical:
      for effect in source.enhancements:
        if isinstance(effect, dict):
          pool.append(dict(effect))
    return pool

  def source_for_blueprint(self, blueprint_key: str) -> List[Dict[str, Any]]:
    if blueprint_key not in self.blueprints:
      raise KeyError(f"Blueprint '{blueprint_key}' not found.")
    return [source.to_dict() for source in self.blueprints[blueprint_key].crafting_sources]

  def seed_demo_blueprints(self) -> None:
    if self.blueprints:
      return
    self.create_blueprint(
      key="steel_broad_sword",
      display_name="Steel Broad Sword",
      asset_class=AssetClass.WEAPON,
      is_mythical=False,
      lore="Forged as a broad cutting edge for close-range battle.",
      base_stats={"damage": 18, "speed": 22, "durability": 56, "weight": 8, "balance": 10},
      default_rarity=Rarity.UNCOMMON,
      compatibility=["universal", "rpg_world"],
      practical_process_tag="weapon_forging",
      crafting_sources=[
        {
          "source_id": "steel_broad_sword_foundry",
          "display_name": "Blacksmith High-Carbon Line",
          "category": "blade_forging",
          "is_mythical": False,
          "is_real_world": True,
          "process_steps": [
            {"step": "bloom_refinement", "duration_minutes": 30, "tools": ["furnace", "slag_separator"]},
            {"step": "blade_profile_press", "duration_minutes": 80},
            {"step": "quench_and_temper", "duration_minutes": 35, "temperature_c": 780},
            {"step": "edge_testing", "duration_minutes": 18, "tools": ["edge_rig"]},
          ],
          "materials": [
            {"material": "high_carbon_steel", "amount": 16, "unit": "kg", "purity_pct": 97.8},
            {"material": "hardening_oil", "amount": 4, "unit": "L"},
            {"material": "resin_handle_stock", "amount": 1.1, "unit": "kg"},
          ],
          "tools": ["furnace", "press", "quench_tank", "edge_rig", "polisher"],
          "requirements": ["smith_certification", "heat_signature_log"],
          "stat_bonuses": {"damage": 2, "durability": 3},
          "stat_multipliers": {"balance": 0.18},
          "risk_level": 0.08,
          "yield_bonus": 0.03,
          "enhancements": [{"type": "edge_set", "effect": "sharper_initial_cut"}],
          "notes": "Practical high-carbon forging pipeline for standard melee weapons.",
        },
        {
          "source_id": "steel_broad_sword_mythic",
          "display_name": "Emberbrand Sword Rite",
          "category": "mythic_bonding",
          "is_mythical": True,
          "is_real_world": False,
          "process_steps": [
            {"step": "ember_ink_transfer", "duration_minutes": 42, "conditions": ["high_heat_ritual"]},
            {"step": "moonsteel_binding", "duration_minutes": 24, "ritualist": True},
            {"step": "seal_inscription", "duration_minutes": 12},
          ],
          "materials": [
            {"material": "moonsteel_dust", "amount": 0.3, "unit": "kg", "purity_pct": 99.2, "is_mythical_material": True},
            {"material": "emberwax", "amount": 0.5, "unit": "kg"},
          ],
          "tools": ["runic_anvil", "moonlamp"],
          "requirements": ["ritual_auth", "lunar_window"],
          "stat_bonuses": {"damage": 7, "balance": 3, "weight": -1},
          "stat_multipliers": {"speed": 0.12},
          "risk_level": 0.22,
          "yield_bonus": 0.04,
          "enhancements": [
            {"type": "ember_brand", "effect": "burning_afterglow"},
            {"type": "mythic_resonance", "effect": "spirit_trail"},
          ],
          "notes": "Magical heat and moon-metal binding grants stronger edge retention.",
        },
      ],
      program_template=[{"action": "blade_lock", "angle_stability": 3}],
    )

    self.create_blueprint(
      key="war_hammer",
      display_name="War Hammer",
      asset_class=AssetClass.WEAPON,
      is_mythical=False,
      lore="A compact percussive weapon for chain-breaker armor penetration.",
      base_stats={"damage": 28, "stability": 24, "handling": 14, "weight": 20},
      default_rarity=Rarity.UNCOMMON,
      compatibility=["universal", "rpg_world"],
      practical_process_tag="hammer_manufacture",
      crafting_sources=[
        {
          "source_id": "war_hammer_industrial",
          "display_name": "Drop-Forge Hammer Line",
          "category": "forged_weapon_build",
          "is_mythical": False,
          "is_real_world": True,
          "process_steps": [
            {"step": "blank_cut", "duration_minutes": 24, "machines": ["plasma_cutter"]},
            {"step": "drop_forging", "duration_minutes": 95},
            {"step": "shock_tempering", "duration_minutes": 36, "temperature_c": 720},
            {"step": "shaft_alignment", "duration_minutes": 20, "tools": ["balance_station"]},
          ],
          "materials": [
            {"material": "spring_steel", "amount": 14, "unit": "kg", "purity_pct": 98.2},
            {"material": "ashwood_shaft", "amount": 1, "unit": "pc"},
            {"material": "alloy_bolts", "amount": 12, "unit": "pcs"},
          ],
          "tools": ["forge_hammer", "drop_press", "heat_treat_burner", "balance_station"],
          "requirements": ["forging_supervisor", "impact_proof_protocol"],
          "stat_bonuses": {"stability": 5, "handling": 2},
          "stat_multipliers": {"damage": 0.16},
          "risk_level": 0.14,
          "yield_bonus": 0.02,
          "enhancements": [{"type": "shock_face", "effect": "armor_entry_bonus"}],
          "notes": "A conventional forging line with strict impact-testing.",
        },
        {
          "source_id": "war_hammer_abyssal",
          "display_name": "Forgefire Hollow Rite",
          "category": "mythic_weapon_blessing",
          "is_mythical": True,
          "is_real_world": False,
          "process_steps": [
            {"step": "chime_forge", "duration_minutes": 17},
            {"step": "void_mud_bath", "duration_minutes": 29, "ritualist": True},
            {"step": "soul_ring_binding", "duration_minutes": 22},
          ],
          "materials": [
            {"material": "ash_core_ash", "amount": 0.9, "unit": "kg"},
            {"material": "void_iron", "amount": 0.2, "unit": "kg", "purity_pct": 98.6, "is_mythical_material": True},
          ],
          "tools": ["resonance_basin", "forgebell", "smoke_chamber"],
          "requirements": ["arcane_consent", "ritual_chamber"],
          "stat_bonuses": {"damage": 11, "stability": 4},
          "stat_multipliers": {"handling": -0.05},
          "risk_level": 0.41,
          "yield_bonus": 0.06,
          "enhancements": [
            {"type": "abyssal_ring", "effect": "heavy_strike_impact"},
            {"type": "stun_wave", "effect": "concussive_aura"},
          ],
          "notes": "Risk-heavy ritual adds impact force at cost of handling precision.",
        },
      ],
      program_template=[{"action": "blunt_strike", "force_curve": "concave"}],
    )

    self.create_blueprint(
      key="skyforged_saber",
      display_name="Skyforged Saber",
      asset_class=AssetClass.WEAPON,
      is_mythical=True,
      lore="Lightweight anti-gravity balance line designed for fast aerial duels.",
      base_stats={"damage": 20, "speed": 34, "durability": 38, "weight": 5, "balance": 18},
      default_rarity=Rarity.EPIC,
      compatibility=["universal", "rpg_world"],
      practical_process_tag="advanced_weapon_line",
      crafting_sources=[
        {
          "source_id": "skyforged_saber_precision",
          "display_name": "Nanofilm Sabermaking",
          "category": "precision_weapon_assembly",
          "is_mythical": False,
          "is_real_world": True,
          "process_steps": [
            {"step": "alloy_sheeting", "duration_minutes": 42, "machines": ["nanolathe"]},
            {"step": "carbon_lattice_cut", "duration_minutes": 52},
            {"step": "vibration_damp_test", "duration_minutes": 16, "tools": ["damping_rig"]},
          ],
          "materials": [
            {"material": "titanium_steel", "amount": 8.4, "unit": "kg", "purity_pct": 99.0},
            {"material": "nano_coating", "amount": 0.9, "unit": "kg"},
            {"material": "tactile_polymer", "amount": 2, "unit": "kg"},
          ],
          "tools": ["nanolathe", "laser_sinter", "damping_rig", "precision_grinder"],
          "requirements": ["electronics_clearance", "blade_alignment_cert"],
          "stat_bonuses": {"speed": 4, "balance": 4},
          "stat_multipliers": {"durability": 0.10},
          "risk_level": 0.16,
          "yield_bonus": 0.05,
          "enhancements": [{"type": "stagger_curve", "effect": "faster_recovery"}],
          "notes": "Industrial advanced forging + material science line.",
        },
        {
          "source_id": "skyforged_saber_storm",
          "display_name": "Skystorm Blessing Chamber",
          "category": "aerial_binding",
          "is_mythical": True,
          "is_real_world": False,
          "process_steps": [
            {"step": "storm_charge", "duration_minutes": 28, "conditions": ["electric_storm"]},
            {"step": "airward_sigil", "duration_minutes": 12, "ritualist": True},
          ],
          "materials": [
            {"material": "storm_silt", "amount": 0.5, "unit": "kg", "is_mythical_material": True},
            {"material": "aerial_essence", "amount": 0.3, "unit": "L"},
          ],
          "tools": ["storm_needle", "sigil_dome"],
          "requirements": ["ritual_clearance", "weather_tracking"],
          "stat_bonuses": {"speed": 14, "damage": 9},
          "stat_multipliers": {"balance": 0.11},
          "risk_level": 0.37,
          "yield_bonus": 0.07,
          "enhancements": [
            {"type": "skyline_cut", "effect": "wind_aided_strikes"},
            {"type": "electro_edge", "effect": "charge_bleed"},
          ],
          "notes": "Magical weather-channel route for highly mobile fighters.",
        },
      ],
      program_template=[{"action": "aerial_combo", "chain": 2}],
    )

    self.create_blueprint(
      key="mithril_tinker_kit",
      display_name="Mithril Tinker Kit",
      asset_class=AssetClass.PRACTICAL_TOOL,
      is_mythical=True,
      lore="Portable artisan toolkit that improves all nearby device repairs.",
      base_stats={"precision": 50, "durability": 32, "utility": 30, "weight": 4},
      default_rarity=Rarity.RARE,
      compatibility=["universal", "factory_sim", "rpg_world"],
      practical_process_tag="toolbox_assembly",
      crafting_sources=[
        {
          "source_id": "mithril_tinker_factory",
          "display_name": "Modular Workshop Line",
          "category": "tool_pack_assembly",
          "is_mythical": False,
          "is_real_world": True,
          "process_steps": [
            {"step": "component_sort", "duration_minutes": 28},
            {"step": "micro_tuning", "duration_minutes": 50},
            {"step": "pack_integration", "duration_minutes": 35},
            {"step": "field_seal", "duration_minutes": 12},
          ],
          "materials": [
            {"material": "stainless_case", "amount": 1.2, "unit": "kg", "purity_pct": 98.5},
            {"material": "tool_steel", "amount": 3.2, "unit": "kg"},
            {"material": "protective_oil", "amount": 0.5, "unit": "L"},
          ],
          "tools": ["precision_rig", "laser_drill", "assembly_bench"],
          "requirements": ["mechanical_shop", "electronics_basic_cert"],
          "stat_bonuses": {"precision": 8, "durability": 6},
          "stat_multipliers": {"utility": 0.2},
          "risk_level": 0.1,
          "yield_bonus": 0.09,
          "enhancements": [{"type": "portable_kit", "effect": "repair_buff_zone"}],
          "notes": "Real-world assembly and calibration style craftsmanship.",
        },
        {
          "source_id": "mithril_tinker_myth",
          "display_name": "Mithril Choir Blessing",
          "category": "guild_blessing",
          "is_mythical": True,
          "is_real_world": False,
          "process_steps": [
            {"step": "resonant_tuning", "duration_minutes": 18, "ritualist": True},
            {"step": "aegis_surge", "duration_minutes": 23},
          ],
          "materials": [
            {"material": "mithril_dust", "amount": 0.6, "unit": "kg", "purity_pct": 99.4, "is_mythical_material": True},
            {"material": "blue_ether", "amount": 0.4, "unit": "L"},
          ],
          "tools": ["tone_resonator", "sigil_bench"],
          "requirements": ["ritualist_licence", "choir_cave_access"],
          "stat_bonuses": {"precision": 10, "utility": 14},
          "stat_multipliers": {"durability": 0.22},
          "risk_level": 0.29,
          "yield_bonus": 0.05,
          "enhancements": [
            {"type": "harmonic_lock", "effect": "self_aligning_tools"},
            {"type": "rune_shine", "effect": "repair_stability"},
          ],
          "notes": "A magical tuning pass improves all subcomponents with slight power risk.",
        },
      ],
      program_template=[{"action": "calibration_wave", "boost": 0.08}],
    )

    self.create_blueprint(
      key="dragonhide_armor",
      display_name="Dragonhide Armor",
      asset_class=AssetClass.ACCESSORY,
      is_mythical=False,
      lore="A heavy hide-plated torso rig for field survival and movement confidence.",
      base_stats={"defense": 36, "encumbrance": 12, "durability": 54, "resistance": 14},
      default_rarity=Rarity.UNCOMMON,
      compatibility=["universal", "rpg_world"],
      practical_process_tag="wearable_manufacture",
      crafting_sources=[
        {
          "source_id": "dragonhide_realworld",
          "display_name": "Composite Armor Sewing Line",
          "category": "wearable_fabrication",
          "is_mythical": False,
          "is_real_world": True,
          "process_steps": [
            {"step": "scale_sorting", "duration_minutes": 20},
            {"step": "lamination", "duration_minutes": 50},
            {"step": "stitch_and_press", "duration_minutes": 66},
            {"step": "impact_grid_test", "duration_minutes": 30},
          ],
          "materials": [
            {"material": "reinforced_polymer_plates", "amount": 16, "unit": "pcs"},
            {"material": "bio_leather_sheet", "amount": 6, "unit": "m2"},
            {"material": "industrial_thread", "amount": 12, "unit": "rolls"},
          ],
          "tools": ["industrial_seamer", "press_vac_former", "impact_pad", "fit_rig"],
          "requirements": ["protective_gear", "ergonomics_inspection"],
          "stat_bonuses": {"defense": 8, "durability": 7},
          "stat_multipliers": {"encumbrance": 0.05},
          "risk_level": 0.11,
          "yield_bonus": 0.03,
          "enhancements": [{"type": "fit_grid", "effect": "improved_body_distribution"}],
          "notes": "Conventional manufacturing workflow for protective wearables.",
        },
        {
          "source_id": "dragonhide_mythic",
          "display_name": "Draconic Bonding Ritual",
          "category": "skin_weaving_mythic",
          "is_mythical": True,
          "is_real_world": False,
          "process_steps": [
            {"step": "ward_imprint", "duration_minutes": 24, "ritualist": True},
            {"step": "scale_awakening", "duration_minutes": 32},
          ],
          "materials": [
            {"material": "dragon_scale_powder", "amount": 1.1, "unit": "kg", "is_mythical_material": True},
            {"material": "fire_glaze", "amount": 0.6, "unit": "L"},
          ],
          "tools": ["ward_frame", "ritual_anvil", "aura_loom"],
          "requirements": ["ritual_permission", "fire_ward_site"],
          "stat_bonuses": {"defense": 14, "resistance": 10},
          "stat_multipliers": {"encumbrance": -0.08},
          "risk_level": 0.3,
          "yield_bonus": 0.05,
          "enhancements": [
            {"type": "ward_sheen", "effect": "heat_shield"},
            {"type": "scale_memory", "effect": "impact_adaptation"},
          ],
          "notes": "Mythic draconic ritual for strong resistance and adaptive defense.",
        },
      ],
      program_template=[{"action": "wearer_adapt", "layering": "adaptive"}],
    )

    self.create_blueprint(
      key="arcane_mantle",
      display_name="Arcane Mantle",
      asset_class=AssetClass.ACCESSORY,
      is_mythical=True,
      lore="A woven mantle that reduces magical backflow and improves focus for casters.",
      base_stats={"focus": 22, "magic_resistance": 18, "encumbrance": 6, "durability": 28},
      default_rarity=Rarity.EPIC,
      compatibility=["universal", "rpg_world"],
      practical_process_tag="ritual_textile_weave",
      crafting_sources=[
        {
          "source_id": "arcane_mantle_weave",
          "display_name": "Arcweave Loom Assembly",
          "category": "protective_textile",
          "is_mythical": False,
          "is_real_world": True,
          "process_steps": [
            {"step": "fiber_spooling", "duration_minutes": 40, "tools": ["smart_loom"]},
            {"step": "resin_infusion", "duration_minutes": 26},
            {"step": "pattern_cut", "duration_minutes": 18},
            {"step": "thermal_laundry", "duration_minutes": 14},
          ],
          "materials": [
            {"material": "conductive_fiber", "amount": 1.8, "unit": "kg"},
            {"material": "insulation_resin", "amount": 1, "unit": "L"},
            {"material": "cloth_backing", "amount": 3, "unit": "m2"},
          ],
          "tools": ["smart_loom", "resin_vat", "heat_cure_unit"],
          "requirements": ["textile_cert", "electrostatic_safety"],
          "stat_bonuses": {"magic_resistance": 5, "focus": 4},
          "stat_multipliers": {"durability": 0.15},
          "risk_level": 0.07,
          "yield_bonus": 0.04,
          "enhancements": [{"type": "grounding_tape", "effect": "reduced_static_feedback"}],
          "notes": "Practical wearable textile route for focused caster clothing.",
        },
        {
          "source_id": "arcane_mantle_choir",
          "display_name": "Mantle Choir Consecration",
          "category": "mythic_textile_binding",
          "is_mythical": True,
          "is_real_world": False,
          "process_steps": [
            {"step": "rune_spiral", "duration_minutes": 34, "ritualist": True},
            {"step": "chant_resonance", "duration_minutes": 18},
          ],
          "materials": [
            {"material": "luminous_thread", "amount": 0.45, "unit": "kg", "is_mythical_material": True},
            {"material": "chant_oil", "amount": 0.2, "unit": "L"},
          ],
          "tools": ["aura_loom", "resonance_chime", "sigil_tongs"],
          "requirements": ["arcane_approval", "sanctified_space"],
          "stat_bonuses": {"focus": 17, "magic_resistance": 12},
          "stat_multipliers": {"encumbrance": -0.12},
          "risk_level": 0.26,
          "yield_bonus": 0.08,
          "enhancements": [
            {"type": "warded_weave", "effect": "ambient_focus_aura"},
            {"type": "spatial_drape", "effect": "noise_suppression"},
          ],
          "notes": "Mythic weave route with magical protection effects.",
        },
      ],
      program_template=[{"action": "focus_wave", "stability_bonus": 1.2}],
    )

    self.create_blueprint(
      key="ember_hammer",
      display_name="Ember Hammer",
      asset_class=AssetClass.MYTHICAL_TOOL,
      is_mythical=True,
      lore="A mythic forging hammer that channels solar heat into every strike.",
      base_stats={"damage": 48, "durability": 34, "handling": 12, "weight": 18},
      default_rarity=Rarity.MYTHIC,
      compatibility=["universal", "rpg_world", "factory_sim"],
      practical_process_tag="forge_workshop",
      crafting_sources=[
        {
          "source_id": "ember_hammer_foundry",
          "display_name": "Solar-Heat Foundry Line",
          "category": "forging_and_heat_treatment",
          "is_mythical": False,
          "is_real_world": True,
          "process_steps": [
            {"step": "ore_sampling", "duration_minutes": 15, "tools": ["ore_roller", "XRF analyzer"]},
            {"step": "blast_furnace_alloy", "duration_minutes": 110, "temperature_c": 1380},
            {"step": "water_quench", "duration_minutes": 25, "tools": ["quench_tank", "thermocouples"]},
            {"step": "vibration_tempering", "duration_minutes": 55, "temperature_c": 420},
            {"step": "load_testing", "duration_minutes": 20, "tools": ["impact_rig"]},
          ],
          "materials": [
            {"material": "high_carbon_steel", "amount": 18, "unit": "kg", "purity_pct": 98.1},
            {"material": "charcoal", "amount": 3, "unit": "kg"},
            {"material": "quench_oil", "amount": 2, "unit": "L"},
          ],
          "tools": ["blast_furnace", "press", "lathe", "quench_tank"],
          "requirements": ["forge_certification", "quality_control_technician"],
          "stat_bonuses": {"durability": 4, "handling": 1},
          "stat_multipliers": {"damage": 0.12},
          "risk_level": 0.12,
          "yield_bonus": 0.04,
          "enhancements": [
            {"type": "impact_coating", "effect": "reduces_tool_wear_by_3pct"}
          ],
          "notes": "Industrial process mirrors traditional hammer forging with measured thermal profiles.",
        },
        {
          "source_id": "ember_hammer_ritual",
          "display_name": "Solar Eclipse Rite",
          "category": "mythic_runic_binding",
          "is_mythical": True,
          "is_real_world": False,
          "process_steps": [
            {"step": "glyph_stamping", "duration_minutes": 35, "ritualist": True},
            {"step": "lunar_catalyst_bath", "duration_minutes": 80},
            {"step": "sigil_alignment", "duration_minutes": 15, "conditions": ["full_moon"]},
          ],
          "materials": [
            {"material": "moon_iron_dust", "amount": 0.25, "unit": "kg", "purity_pct": 99.0, "is_mythical_material": True},
            {"material": "star_resin", "amount": 1, "unit": "L", "is_mythical_material": True},
          ],
          "tools": ["sigil_frame", "prism_glass_basin"],
          "requirements": ["ritual_authorization", "astronomy_window"],
          "stat_bonuses": {"damage": 14, "durability": 5, "handling": 2},
          "stat_multipliers": {"damage": 0.25},
          "risk_level": 0.34,
          "yield_bonus": 0.10,
          "enhancements": [
            {"type": "solar_aura", "effect": "ember_shock_traces", "range": 2.5},
            {"type": "ritual_forge_signature", "effect": "higher_rune_sensitivity"},
          ],
          "notes": "Mythic pass used for enhanced resonance and stronger strike impact.",
        },
      ],
      program_template=[{"action": "mythic_resonance", "mode": "ignite", "cooldown": 8}],
    )

    self.create_blueprint(
      key="precision_plow",
      display_name="Precision Plow",
      asset_class=AssetClass.PRACTICAL_TOOL,
      is_mythical=False,
      lore="A high-efficiency land tool for cultivation simulations.",
      base_stats={"durability": 72, "precision": 46, "stability": 38},
      default_rarity=Rarity.UNCOMMON,
      compatibility=["universal", "factory_sim"],
      practical_process_tag="machining",
      crafting_sources=[
        {
          "source_id": "precision_plow_cnc",
          "display_name": "CNC Milling & Heat-Cycle Assembly",
          "category": "precision_machining",
          "is_mythical": False,
          "is_real_world": True,
          "process_steps": [
            {"step": "CAD_validation", "duration_minutes": 18, "tools": ["CAM station"]},
            {"step": "CNC_milling", "duration_minutes": 48, "tolerance_mm": 0.05},
            {"step": "surface_hardening", "duration_minutes": 28, "temperature_c": 260},
            {"step": "calibration", "duration_minutes": 20, "tools": ["calibration_rig"]},
          ],
          "materials": [
            {"material": "chromium_tool_steel", "amount": 16, "unit": "kg", "purity_pct": 99.2},
            {"material": "tungsten_coating", "amount": 0.8, "unit": "kg"},
            {"material": "hydraulic_fluid", "amount": 0.9, "unit": "L"},
          ],
          "tools": ["CNC_mill", "hardness_meter", "calibration_rig", "hydraulic_press"],
          "requirements": ["mechanical_engineering_approval", "calibration_cert"],
          "stat_bonuses": {"precision": 12, "durability": 8},
          "stat_multipliers": {"stability": 0.18},
          "risk_level": 0.09,
          "yield_bonus": 0.08,
          "enhancements": [{"type": "farm_grade", "effect": "increased_soil_cut_efficiency"}],
          "notes": "Represents real machining lines used for precision agricultural attachments.",
        },
      ],
      program_template=[{"action": "resource_mining", "yield_bonus": 0.1}],
    )

    self.create_blueprint(
      key="forgehammer_maintenance_pick",
      display_name="Forgehammer Maintenance Pick",
      asset_class=AssetClass.PRACTICAL_TOOL,
      is_mythical=False,
      lore="A compact pick used for excavation and salvage cleanup work.",
      base_stats={"durability": 66, "impact": 22, "weight": 11, "handling": 24},
      default_rarity=Rarity.COMMON,
      compatibility=["universal", "factory_sim"],
      practical_process_tag="mining_tool_assembly",
      crafting_sources=[
        {
          "source_id": "maintenance_pick_press",
          "display_name": "Steel Press and Head Cast",
          "category": "tool_pressing",
          "is_mythical": False,
          "is_real_world": True,
          "process_steps": [
            {"step": "head_machining", "duration_minutes": 40},
            {"step": "impact_edge_forming", "duration_minutes": 25},
            {"step": "haft_bonding", "duration_minutes": 18},
            {"step": "abrasion_test", "duration_minutes": 12},
          ],
          "materials": [
            {"material": "forged_steel", "amount": 6.2, "unit": "kg", "purity_pct": 98.0},
            {"material": "hardline_haft", "amount": 1.2, "unit": "kg"},
          ],
          "tools": ["press_line", "impact_mill", "adhesive_bond_station"],
          "requirements": ["workshop_clearance", "impact_safety_protocol"],
          "stat_bonuses": {"impact": 4, "durability": 3},
          "stat_multipliers": {"handling": 0.07},
          "risk_level": 0.06,
          "yield_bonus": 0.05,
          "enhancements": [{"type": "wear_pad", "effect": "smoother_shaft_grip"}],
          "notes": "Standard industrial process for utility tools.",
        },
      ],
      program_template=[{"action": "shock_absorb", "mode": "balanced"}],
    )

    self.create_blueprint(
      key="sky_ward_helmet",
      display_name="Sky Ward Helmet",
      asset_class=AssetClass.ACCESSORY,
      is_mythical=True,
      lore="A lightweight helmet shell with reinforced wards for atmospheric travel.",
      base_stats={"defense": 26, "durability": 46, "encumbrance": 7, "vision": 14},
      default_rarity=Rarity.RARE,
      compatibility=["universal", "rpg_world", "vehicle_arena"],
      practical_process_tag="helmet_manufacture",
      crafting_sources=[
        {
          "source_id": "sky_ward_helmet_tech",
          "display_name": "Aerospace Composite Helmet Build",
          "category": "helmet_manufacturing",
          "is_mythical": False,
          "is_real_world": True,
          "process_steps": [
            {"step": "scan_fit", "duration_minutes": 22, "tools": ["3d_scanner"]},
            {"step": "composite_molding", "duration_minutes": 75},
            {"step": "visor_lamination", "duration_minutes": 30},
            {"step": "impact_cert_test", "duration_minutes": 25},
          ],
          "materials": [
            {"material": "reinforced_polymer", "amount": 3.5, "unit": "kg"},
            {"material": "transparent_shield", "amount": 1, "unit": "pc"},
            {"material": "sealant_foam", "amount": 1.4, "unit": "L"},
          ],
          "tools": ["3d_scanner", "compression_mold", "lamination_station", "impact_rig"],
          "requirements": ["aero_safety_cert", "ventilation_review"],
          "stat_bonuses": {"defense": 4, "vision": 3},
          "stat_multipliers": {"encumbrance": 0.03},
          "risk_level": 0.1,
          "yield_bonus": 0.02,
          "enhancements": [{"type": "airseal", "effect": "dust_protection"}],
          "notes": "Practical helmet production with fit scanning and impact testing.",
        },
        {
          "source_id": "sky_ward_helmet_ward",
          "display_name": "Aetheric Warding Layer",
          "category": "helmet_ward_binding",
          "is_mythical": True,
          "is_real_world": False,
          "process_steps": [
            {"step": "ward_glyph_draw", "duration_minutes": 17, "ritualist": True},
            {"step": "windlock_seal", "duration_minutes": 19},
          ],
          "materials": [
            {"material": "windglass_powder", "amount": 0.7, "unit": "kg", "is_mythical_material": True},
            {"material": "sky_salt", "amount": 0.2, "unit": "kg"},
          ],
          "tools": ["sigil_etcher", "aero_basin"],
          "requirements": ["ritualist", "clean_energetic_zone"],
          "stat_bonuses": {"defense": 12, "vision": 9},
          "stat_multipliers": {"encumbrance": -0.08},
          "risk_level": 0.24,
          "yield_bonus": 0.05,
          "enhancements": [
            {"type": "headward", "effect": "dizzy_resistance"},
            {"type": "wind_echo", "effect": "aether_hush"},
          ],
          "notes": "Magical warding boosts headwear utility while reducing fatigue.",
        },
      ],
      program_template=[{"action": "seal_check", "mode": "aerial"}],
    )

    self.create_blueprint(
      key="arc_lance",
      display_name="Arc Lance",
      asset_class=AssetClass.WEAPON,
      is_mythical=False,
      lore="Long-range weapon with a charge-ready channel coil.",
      base_stats={"damage": 26, "range": 60, "reload": 3, "weight": 9},
      default_rarity=Rarity.EPIC,
      compatibility=["universal", "rpg_world"],
      practical_process_tag="electronics_assembly",
      crafting_sources=[
        {
          "source_id": "arc_lance_battery",
          "display_name": "Battery-Drive Assembly Shop",
          "category": "electromagnetic_device_build",
          "is_mythical": False,
          "is_real_world": True,
          "process_steps": [
            {"step": "coil_winding", "duration_minutes": 65, "machines": ["precision_winder"]},
            {"step": "insulation_bake", "duration_minutes": 30, "temperature_c": 140},
            {"step": "EMI_shield_test", "duration_minutes": 12, "tools": ["rf_probe"]},
            {"step": "impact_verification", "duration_minutes": 16, "tools": ["range_rig"]},
          ],
          "materials": [
            {"material": "oxygen_free_copper", "amount": 3.4, "unit": "kg", "purity_pct": 99.9},
            {"material": "magnetic_alloy", "amount": 1.4, "unit": "kg", "purity_pct": 98.5},
            {"material": "dielectric_gel", "amount": 0.5, "unit": "L"},
          ],
          "tools": ["winder", "oven", "rf_meter", "solder_station", "shock_tester"],
          "requirements": ["electronics_safety_gear", "wire_clearance_check"],
          "stat_bonuses": {"range": 7, "reload": -0.5},
          "stat_multipliers": {"damage": 0.15},
          "risk_level": 0.18,
          "yield_bonus": 0.02,
          "enhancements": [{"type": "electro_stability", "effect": "reduced_overheat_rollbacks"}],
          "notes": "Uses realistic electrical assembly and thermal verification steps.",
        },
        {
          "source_id": "arc_lance_myriad_bolt",
          "display_name": "Stormglass Convergence (Mythic)",
          "category": "arcane_charge_binding",
          "is_mythical": True,
          "is_real_world": False,
          "process_steps": [
            {"step": "stormglass_harmonics", "duration_minutes": 22, "conditions": ["thunderstorm", "stormglass_available"]},
            {"step": "channel_sealing", "duration_minutes": 30, "ritualist": True},
          ],
          "materials": [
            {"material": "stormglass_shard", "amount": 0.2, "unit": "kg", "purity_pct": 100.0, "is_mythical_material": True},
            {"material": "blue_flux", "amount": 0.4, "unit": "L", "is_mythical_material": True},
          ],
          "tools": ["electromagnetic_basin", "sigil_prism"],
          "requirements": ["ritualist", "weather_window"],
          "stat_bonuses": {"damage": 16, "range": 28},
          "stat_multipliers": {"reload": -0.25},
          "risk_level": 0.41,
          "yield_bonus": 0.06,
          "enhancements": [
            {"type": "chain_bolt", "effect": "arc_chain_targets"},
            {"type": "lightning_echo", "effect": "residue_shock_aura"},
          ],
          "notes": "High-risk magical process that improves range and arc-chain behavior.",
        },
      ],
      program_template=[{"action": "charged_shot", "charge_time": 1.5}],
    )

    self.create_blueprint(
      key="aether_runner",
      display_name="Aether Runner",
      asset_class=AssetClass.VEHICLE,
      is_mythical=True,
      lore="A gravity-light hover craft tuned for difficult terrain.",
      base_stats={"speed": 120, "handling": 48, "fuel": 65, "range": 220},
      default_rarity=Rarity.LEGENDARY,
      compatibility=["universal", "vehicle_arena", "factory_sim"],
      practical_process_tag="vehicle_composite_build",
      crafting_sources=[
        {
          "source_id": "aether_runner_composite_shop",
          "display_name": "Light-Frame Composite Build Line",
          "category": "vehicle_composite_manufacturing",
          "is_mythical": False,
          "is_real_world": True,
          "process_steps": [
            {"step": "frame_print", "duration_minutes": 180, "machines": ["5_axis_CNC", "robotic_welder"]},
            {"step": "rotor_assembly", "duration_minutes": 90, "machines": ["balancing_rig"]},
            {"step": "battery_pack_integration", "duration_minutes": 40},
            {"step": "terrain_trial", "duration_minutes": 25, "tools": ["rough_track_testbed"]},
          ],
          "materials": [
            {"material": "aerospace_aluminum", "amount": 220, "unit": "kg", "purity_pct": 99.6},
            {"material": "lithium_cell_array", "amount": 95, "unit": "kWh"},
            {"material": "carbon_fiber_sheet", "amount": 18, "unit": "kg", "purity_pct": 98.0},
            {"material": "high_grade_foam", "amount": 6, "unit": "kg"},
          ],
          "tools": ["robotic_welder", "5_axis_CNC", "rotor_balancer", "dyno_tracers"],
          "requirements": ["vehicle_aerospace_audit", "battery_thermal_clearance"],
          "stat_bonuses": {"speed": 22, "handling": 10, "range": 18},
          "stat_multipliers": {"fuel": -0.08},
          "risk_level": 0.14,
          "yield_bonus": 0.06,
          "enhancements": [{"type": "adaptive_suspension", "effect": "off_road_stability"}],
          "notes": "Composite build flow mirrors lightweight EV body and propulsion production.",
        },
        {
          "source_id": "aether_runner_aeonic",
          "display_name": "Aeonic Lift Invocation",
          "category": "aetheric_binding",
          "is_mythical": True,
          "is_real_world": False,
          "process_steps": [
            {"step": "resonance_matrix_alignment", "duration_minutes": 48, "conditions": ["moonless_window"]},
            {"step": "lift_ward_etch", "duration_minutes": 26, "ritualist": True},
            {"step": "field_stabilization", "duration_minutes": 15},
          ],
          "materials": [
            {"material": "aeonic_lode_salt", "amount": 1.2, "unit": "kg", "is_mythical_material": True},
            {"material": "void_gel_lubricant", "amount": 1.0, "unit": "L", "is_mythical_material": True},
          ],
          "tools": ["rift_basin", "glyph_lasers", "stability_field_generator"],
          "requirements": ["arcane_researchers", "protected_site_clearance"],
          "stat_bonuses": {"speed": 46, "fuel": -20, "handling": 18},
          "stat_multipliers": {"range": 0.22},
          "risk_level": 0.5,
          "yield_bonus": 0.12,
          "enhancements": [
            {"type": "short_boost", "effect": "instantaneous_lift"},
            {"type": "terrain_phase", "effect": "cliff_hover_assist"},
          ],
          "notes": "Mythic levitation route that can outperform conventional limits with higher risk.",
        },
      ],
      program_template=[{"action": "drift_compensation", "assist": 0.25}],
    )

  def _normalize_stats(self, raw: Dict[str, float], *, allow_empty: bool = False) -> Dict[str, float]:
    normalized: Dict[str, float] = {}
    for key, value in raw.items():
      key_clean = str(key).strip().lower()
      if not key_clean:
        raise ValueError("Stat names must be non-empty strings.")
      numeric = self._safe_float(value, f"stat '{key_clean}'")
      if numeric < 0:
        raise ValueError(f"Stat '{key_clean}' cannot be negative.")
      normalized[key_clean] = numeric
    if not normalized and not allow_empty:
      raise ValueError("Stats cannot be empty.")
    return normalized

  def _normalize_crafting_sources(self, sources: Optional[Sequence[Dict[str, Any]]], fallback_tag: str) -> List[CraftingSource]:
    raw_sources = list(sources or [])
    if not raw_sources:
      return [
        self._build_default_source(f"{fallback_tag}_baseline", is_real_world=True),
      ]
    normalized: List[CraftingSource] = []
    for index, raw in enumerate(raw_sources, start=1):
      if not isinstance(raw, dict):
        raise ValueError("Each crafting source entry must be an object.")
      source_id = str(raw.get("source_id") or raw.get("key") or raw.get("id") or f"{fallback_tag}_source_{index}").strip()
      if not source_id:
        raise ValueError("crafting_sources entries must include a non-empty source_id.")
      display_name = str(raw.get("display_name") or raw.get("name") or source_id).strip()
      category = str(raw.get("category") or "practical_fabrication").strip()
      if not category:
        raise ValueError("crafting source category cannot be empty.")

      process_steps = self._normalize_steps(raw.get("process_steps") or raw.get("steps"), source_id)
      materials = self._normalize_materials(raw.get("materials") or [])
      tools = self._normalize_string_list(raw.get("tools"), f"tools for source '{source_id}'")
      requirements = self._normalize_string_list(raw.get("requirements"), f"requirements for source '{source_id}'")
      stat_bonuses = self._normalize_stats(raw.get("stat_bonuses") or {}, allow_empty=True)
      stat_multipliers = {name.lower(): self._safe_float(v, f"stat multipliers '{name}'")
                          for name, v in dict(raw.get("stat_multipliers") or {}).items()}
      risk_level = self._safe_float(raw.get("risk_level", 0.05), "risk_level")
      if not 0 <= risk_level <= 1:
        raise ValueError("risk_level must be between 0 and 1.")
      yield_bonus = self._safe_float(raw.get("yield_bonus", 0), "yield_bonus")
      if yield_bonus < 0:
        raise ValueError("yield_bonus cannot be negative.")
      is_mythical = bool(raw.get("is_mythical", False))
      is_real_world = bool(raw.get("is_real_world", not is_mythical))
      enhancements = self._normalize_enhancements(raw.get("enhancements") or [], source_id)
      notes = str(raw.get("notes") or "")

      normalized.append(
        CraftingSource(
          source_id=source_id,
          display_name=display_name,
          category=category,
          is_mythical=is_mythical,
          is_real_world=is_real_world,
          process_steps=process_steps,
          materials=materials,
          tools=tools,
          requirements=requirements,
          stat_bonuses=stat_bonuses,
          stat_multipliers=stat_multipliers,
          risk_level=risk_level,
          yield_bonus=yield_bonus,
          enhancements=enhancements,
          notes=notes,
        )
      )
    return normalized

  def _build_default_source(self, source_id: str, is_real_world: bool) -> CraftingSource:
    base = {
      "source_id": source_id,
      "display_name": "Baseline Workshop Process",
      "category": "general_assembly",
      "is_mythical": False,
      "is_real_world": is_real_world,
      "process_steps": [
        {"step": "layout_design", "duration_minutes": 30},
        {"step": "fabrication", "duration_minutes": 90},
        {"step": "quality_inspection", "duration_minutes": 20},
      ],
      "materials": [{"material": "alloy_steel", "amount": 10, "unit": "kg", "purity_pct": 98.0}],
      "tools": ["lathe", "welding_station", "inspection_rig"],
      "requirements": ["prototype_authorization"],
      "stat_bonuses": {},
      "stat_multipliers": {"durability": 0.05},
      "risk_level": 0.15,
      "yield_bonus": 0.0,
      "enhancements": [],
      "notes": "Fallback realistic baseline route used when no source data is provided.",
    }
    return self._normalize_single_source(base)

  def _normalize_single_source(self, raw: Dict[str, Any]) -> CraftingSource:
    normalized = self._normalize_crafting_sources([raw], fallback_tag=raw["source_id"])
    return normalized[0]

  def _normalize_steps(self, raw: Optional[Sequence[Dict[str, Any]]], source_id: str) -> List[Dict[str, Any]]:
    if raw is None:
      return []
    if not isinstance(raw, Sequence) or isinstance(raw, (str, bytes, dict)):
      raise ValueError(f"process_steps for source '{source_id}' must be a list.")
    steps: List[Dict[str, Any]] = []
    for idx, step in enumerate(raw, start=1):
      if not isinstance(step, dict):
        raise ValueError(f"process step #{idx} for source '{source_id}' must be an object.")
      step_name = str(step.get("step") or step.get("name") or f"step_{idx}").strip()
      if not step_name:
        raise ValueError(f"process step #{idx} for source '{source_id}' needs a name.")
      clean_step = dict(step)
      clean_step["step"] = step_name
      clean_step["order"] = idx
      steps.append(clean_step)
    return steps

  def _normalize_materials(self, raw: Sequence[Dict[str, Any]]) -> List[Dict[str, Any]]:
    if raw is None:
      return []
    if not isinstance(raw, Sequence) or isinstance(raw, (str, bytes, dict)):
      raise ValueError("materials must be a list.")
    materials: List[Dict[str, Any]] = []
    for idx, material in enumerate(raw, start=1):
      if not isinstance(material, dict):
        raise ValueError(f"materials item #{idx} must be an object.")
      name = str(material.get("material") or material.get("name") or "").strip()
      if not name:
        raise ValueError(f"materials item #{idx} needs a material name.")
      amount = self._safe_float(material.get("amount", 0), f"material '{name}' amount")
      if amount <= 0:
        raise ValueError(f"materials item '#{idx}' must have amount > 0.")
      unit = str(material.get("unit") or "unit").strip()
      clean = {"material": name, "amount": amount, "unit": unit}
      purity = material.get("purity_pct")
      if purity is not None:
        clean["purity_pct"] = self._safe_float(purity, f"material '{name}' purity_pct")
      for key, value in material.items():
        if key not in clean and key not in {"material", "name", "amount", "unit", "purity_pct"}:
          clean[str(key)] = value
      materials.append(clean)
    return materials

  def _normalize_addon_slots(self, raw_slots: Optional[Sequence[Dict[str, Any]]], *, fallback_key: str) -> List[Dict[str, Any]]:
    if raw_slots is None:
      return []
    if not isinstance(raw_slots, Sequence) or isinstance(raw_slots, (str, bytes, dict)):
      raise ValueError(f"addon_slots for '{fallback_key}' must be a list.")
    normalized: List[Dict[str, Any]] = []
    for index, raw in enumerate(raw_slots, start=1):
      if not isinstance(raw, dict):
        raise ValueError(f"addon_slot #{index} for '{fallback_key}' must be an object.")
      slot_id = str(raw.get("slot_id") or raw.get("id") or raw.get("name") or "").strip()
      if not slot_id:
        raise ValueError(f"addon_slot #{index} for '{fallback_key}' requires a slot_id.")
      slot_type = str(raw.get("slot_type") or "universal").strip().lower() or "universal"
      compatible = self._normalize_string_list(
        raw.get("compatible_slot_types") or raw.get("slot_types") or raw.get("compatible_with"),
        f"compatible_slot_types for slot '{slot_id}'",
      )
      compatible = [tag.lower() for tag in compatible]
      if not compatible:
        compatible = [slot_type]
      elif slot_type not in compatible:
        compatible.append(slot_type)
      if "universal" not in compatible:
        compatible.append("universal")
      default_magic_rolls = self._safe_roll_count(
        raw.get("default_magic_rolls", raw.get("magic_rolls")),
        f"default_magic_rolls for slot '{slot_id}'",
        default=1,
        minimum=0,
      )
      max_magic_rolls = self._safe_roll_count(
        raw.get("max_magic_rolls"),
        f"max_magic_rolls for slot '{slot_id}'",
        default=max(3, default_magic_rolls),
        minimum=0,
      )
      if max_magic_rolls < default_magic_rolls:
        raise ValueError(
          f"addon_slot '{slot_id}' for '{fallback_key}' cannot have max_magic_rolls less than default_magic_rolls."
        )
      normalized.append({
        "slot_id": slot_id,
        "slot_type": slot_type,
        "compatible_slot_types": compatible,
        "required": bool(raw.get("required", False)),
        "notes": str(raw.get("notes") or ""),
        "default_magic_rolls": default_magic_rolls,
        "max_magic_rolls": max_magic_rolls,
      })
    return normalized

  def _normalize_addons(self, addons: Sequence[Dict[str, Any]], blueprint_key: str) -> List[Dict[str, Any]]:
    if not isinstance(addons, Sequence) or isinstance(addons, (str, bytes, dict)):
      raise ValueError(f"add-ons for blueprint '{blueprint_key}' must be a list.")
    normalized: List[Dict[str, Any]] = []
    for index, raw in enumerate(addons, start=1):
      if not isinstance(raw, dict):
        raise ValueError(f"addon #{index} for blueprint '{blueprint_key}' must be an object.")
      addon_id = str(raw.get("addon_id") or raw.get("id") or raw.get("name") or "").strip()
      if not addon_id:
        raise ValueError(f"addon #{index} for blueprint '{blueprint_key}' requires addon_id.")
      display_name = str(raw.get("display_name") or addon_id).strip()
      slot_id = str(raw.get("slot_id") or "").strip() or None
      slot_type = str(raw.get("slot_type") or raw.get("type") or "universal").strip().lower() or "universal"
      compatible = self._normalize_string_list(
        raw.get("compatible_slot_types") or raw.get("addon_types") or raw.get("compatible_with"),
        f"compatible_slot_types for add-on '{addon_id}'",
      )
      compatible = [tag.lower() for tag in compatible]
      if not compatible:
        compatible = [slot_type]
      elif slot_type not in compatible:
        compatible.append(slot_type)
      normalized.append({
        "addon_id": addon_id,
        "display_name": display_name,
        "slot_id": slot_id,
        "slot_type": slot_type,
        "compatible_slot_types": compatible,
        "is_mythical": bool(raw.get("is_mythical") or raw.get("is_magic") or raw.get("mythical")),
        "stat_bonuses": self._normalize_stats(raw.get("stat_bonuses") or raw.get("stats") or {}, allow_empty=True),
        "magic_effects": [dict(item) for item in (raw.get("magic_effects") or raw.get("effects") or [])],
        "notes": str(raw.get("notes") or ""),
        "source_payload": dict(raw),
      })
    return normalized

  def _fill_addon_slots(
      self,
      blueprint: AssetBlueprint,
      source: CraftingSource,
      requested_addons: List[Dict[str, Any]],
      mythic_materials: List[Dict[str, Any]],
  ) -> List[Dict[str, Any]]:
    if not blueprint.addon_slots:
      return []

    remaining_addons = list(requested_addons)
    remaining_materials = list(mythic_materials)
    slot_fills: List[Dict[str, Any]] = []

    for slot in blueprint.addon_slots:
      fill = self._claim_addon_for_slot(slot, remaining_addons)
      if fill is None:
        fill = self._claim_material_for_slot(slot, remaining_materials, source.is_mythical)
      if fill is None:
        fill = {
          "source": "empty",
          "is_mythical": False,
          "status": "empty",
          "addon": None,
          "stat_bonuses": {},
          "magic_effects": [],
        }
      fill["slot_id"] = slot["slot_id"]
      fill["slot_type"] = slot.get("slot_type", "universal")
      slot_fills.append(fill)
    return slot_fills

  def _claim_addon_for_slot(self, slot: Dict[str, Any], remaining_addons: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    for index, addon in enumerate(remaining_addons):
      requested_slot = addon.get("slot_id")
      if requested_slot and requested_slot != slot["slot_id"] and requested_slot not in ("", None):
        continue
      if not self._slot_compatible(slot, addon):
        continue
      remaining_addons.pop(index)
      return {
        "source": "addon",
        "is_mythical": bool(addon.get("is_mythical")),
        "status": "filled",
        "addon": dict(addon),
        "stat_bonuses": dict(addon.get("stat_bonuses", {})),
        "magic_effects": [dict(effect) for effect in addon.get("magic_effects", [])],
      }
    return None

  def _claim_material_for_slot(self, slot: Dict[str, Any], remaining_materials: List[Dict[str, Any]], source_is_mythical: bool) -> Optional[Dict[str, Any]]:
    if not remaining_materials:
      return None

    chosen_index = None
    for index, material in enumerate(remaining_materials):
      if self._slot_matches_material(slot, material):
        chosen_index = index
        break

    if chosen_index is None and source_is_mythical:
      chosen_index = 0

    if chosen_index is None:
      return None

    material = remaining_materials.pop(chosen_index)
    return {
      "source": "mythic_material",
      "is_mythical": True,
      "status": "filled",
      "mythic_material": dict(material),
      "stat_bonuses": self._normalize_stats(material.get("stat_bonuses") or material.get("add_stat") or {}, allow_empty=True),
      "magic_effects": [dict(effect) for effect in material.get("magic_effects", [])]
      + [{
        "type": "mythic_material_slot",
        "slot_id": slot["slot_id"],
        "material": material.get("material"),
      }],
    }

  def _slot_compatible(self, slot: Dict[str, Any], addon: Dict[str, Any]) -> bool:
    slot_types = set(slot.get("compatible_slot_types", ["universal"]))
    if "universal" in slot_types:
      return True
    addon_types = set(addon.get("compatible_slot_types", []))
    if not addon_types:
      addon_types = {str(addon.get("slot_type") or "").strip().lower() or "universal"}
    return bool(slot_types.intersection(addon_types))

  def _slot_matches_material(self, slot: Dict[str, Any], material: Dict[str, Any]) -> bool:
    slot_types = set(slot.get("compatible_slot_types", ["universal"]))
    if "universal" in slot_types:
      return True
    material_type = []
    material_tags = material.get("slot_tags") or material.get("slot_type") or material.get("affinity")
    if isinstance(material_tags, (str, bytes)):
      material_tags = [material_tags]
    if isinstance(material_tags, Sequence) and not isinstance(material_tags, (bytes, bytearray, dict)):
      for raw_tag in material_tags:
        if isinstance(raw_tag, str):
          for tag in self._normalize_string_list(raw_tag.split(","), "material slot tags"):
            if tag:
              material_type.append(tag.lower())
        elif raw_tag:
          material_type.append(str(raw_tag).strip().lower())
    if not material_type:
      material_type = [str(material.get("material_type") or material.get("mythic_type") or "").strip().lower()]
      material_type = [t for t in material_type if t]
    if not material_type:
      return False
    return bool(slot_types.intersection(set(material_type)))

  def _apply_slot_bonuses(self, stats: Dict[str, float], slot_fills: List[Dict[str, Any]]) -> Dict[str, float]:
    with_bonuses = dict(stats)
    for fill in slot_fills:
      for name, delta in fill.get("stat_bonuses", {}).items():
        with_bonuses[name] = with_bonuses.get(name, 0.0) + self._safe_float(delta, f"slot bonus '{name}'")
    return with_bonuses

  def _magic_effects_from_slots(self, slot_fills: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    effects: List[Dict[str, Any]] = []
    for fill in slot_fills:
      for effect in fill.get("magic_effects", []):
        effects.append(dict(effect))
    return effects

  def _normalize_string_list(self, raw: Sequence[str], context: str) -> List[str]:
    if raw is None:
      return []
    if isinstance(raw, str):
      raw = [raw]
    if not isinstance(raw, Sequence) or isinstance(raw, (bytes, bytearray, dict)):
      raise ValueError(f"{context} must be a list of strings.")
    clean: List[str] = []
    for item in raw:
      value = str(item).strip()
      if value:
        clean.append(value)
    return clean

  def _normalize_enhancements(self, raw: Sequence[Dict[str, Any]], source_id: str) -> List[Dict[str, Any]]:
    if raw is None:
      return []
    if not isinstance(raw, Sequence) or isinstance(raw, (str, bytes, dict)):
      raise ValueError(f"enhancements for source '{source_id}' must be a list.")
    normalized: List[Dict[str, Any]] = []
    for idx, enhancement in enumerate(raw, start=1):
      if not isinstance(enhancement, dict):
        raise ValueError(f"enhancement #{idx} for source '{source_id}' must be an object.")
      normalized.append(dict(enhancement))
    return normalized

  def _find_source(self, blueprint_key: str, source_id: Optional[str]) -> Optional[CraftingSource]:
    blueprint = self.blueprints.get(blueprint_key)
    if not blueprint:
      return None
    for source in blueprint.crafting_sources:
      if source.source_id == source_id:
        return source
    return blueprint.crafting_sources[0] if blueprint.crafting_sources else None

  def _is_mythical_material(self, material: Dict[str, Any]) -> bool:
    if not isinstance(material, dict):
      return False
    explicit = (
      bool(material.get("is_mythical"))
      or bool(material.get("is_mythical_material"))
      or bool(material.get("mythic"))
    )
    if explicit:
      return explicit
    tier = str(material.get("tier") or "").strip().lower()
    return tier in {"mythical", "mythic", "legendary"}

  def _find_mythical_materials(self, materials: Sequence[Dict[str, Any]]) -> List[Dict[str, Any]]:
    return [dict(material) for material in materials if self._is_mythical_material(material)]

  def _upgrade_rarity(self, rarity: Rarity, mythical_materials: Sequence[Dict[str, Any]]) -> Rarity:
    if not mythical_materials:
      return rarity
    order = [Rarity.COMMON, Rarity.UNCOMMON, Rarity.RARE, Rarity.EPIC, Rarity.LEGENDARY, Rarity.MYTHIC]
    current_index = order.index(rarity)
    if current_index >= len(order) - 1:
      return rarity
    return order[current_index + 1]

  def _magic_effects_for_source(self, source: CraftingSource) -> List[Dict[str, Any]]:
    if not source.is_mythical:
      return []
    return [dict(effect) for effect in source.enhancements]

  def _pick_crafting_source(self, blueprint: AssetBlueprint, source_id: Optional[str]) -> CraftingSource:
    if not blueprint.crafting_sources:
      raise RuntimeError("Blueprint has no crafting sources.")
    if source_id:
      match = self._find_source(blueprint.key, source_id)
      if match is None:
        available = ", ".join(source.source_id for source in blueprint.crafting_sources)
        raise ValueError(f"Unknown crafting_source_id '{source_id}'. Available: {available}")
      return match
    return blueprint.crafting_sources[0]

  def _apply_crafting_bonuses(self, stats: Dict[str, float], source: CraftingSource) -> Dict[str, float]:
    with_bonuses: Dict[str, float] = dict(stats)
    for name, delta in source.stat_bonuses.items():
      with_bonuses[name] = with_bonuses.get(name, 0.0) + delta
    for name, multiplier in source.stat_multipliers.items():
      base = with_bonuses.get(name, 0.0)
      with_bonuses[name] = base * (1 + multiplier)
    for key, value in list(with_bonuses.items()):
      if value < 0:
        with_bonuses[key] = 0.0
    return with_bonuses

  def _normalize_program(self, steps: Sequence[Dict[str, Any]]) -> List[Dict[str, Any]]:
    normalized: List[Dict[str, Any]] = []
    for step in steps:
      if not isinstance(step, dict):
        raise ValueError("Each program step must be a dictionary.")
      if "action" not in step:
        raise ValueError("Each program step requires an 'action' key.")
      normalized.append(dict(step))
    return normalized

  def _safe_float(self, value: Any, label: str) -> float:
    try:
      numeric = float(value)
    except (TypeError, ValueError) as exc:
      raise ValueError(f"{label} must be numeric.") from exc
    return numeric

  def _safe_roll_count(
      self,
      value: Any,
      label: str,
      *,
      minimum: int = 0,
      default: int | None = None,
  ) -> int:
    if value is None:
      if default is None:
        raise ValueError(f"{label} must be a whole number >= {minimum}.")
      return default
    numeric = self._safe_float(value, label)
    if numeric < minimum or numeric != int(numeric):
      raise ValueError(f"{label} must be a whole number >= {minimum}.")
    return int(numeric)

  def _calculate_provenance(self, asset: ForgedAsset, source: Optional[CraftingSource]) -> str:
    signature_payload = {
      "asset_id": asset.asset_id,
      "blueprint_key": asset.blueprint_key,
      "name": asset.name,
      "owner": asset.owner,
      "asset_class": asset.asset_class.value,
      "rarity": asset.rarity.value,
      "is_mythical": asset.is_mythical,
      "tags": list(asset.tags),
      "stats": dict(asset.stats),
      "program": [dict(step) for step in asset.program],
      "version": asset.version,
      "crafting_source_id": asset.crafting_source_id,
      "applied_enhancements": [dict(item) for item in asset.applied_enhancements],
      "magic_effects": [dict(item) for item in asset.magic_effects],
      "mythical_materials_used": [dict(item) for item in asset.mythical_materials_used],
      "addon_slots_filled": [dict(item) for item in asset.addon_slots_filled],
      "final_rarity": asset.rarity.value,
      "category": asset.category,
      "source_process_signature": source.source_id if source else None,
      "source_category": source.category if source else None,
    }
    return _hash_payload(signature_payload)

