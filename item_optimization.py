from __future__ import annotations

import math
import re
from collections import Counter
from dataclasses import dataclass
from typing import Any, Dict, Iterable, List, Mapping, Tuple


@dataclass(frozen=True)
class StatGroup:
  id: str
  name: str
  category: str
  aliases: Tuple[str, ...]
  normalize_as_percent: bool = False


@dataclass(frozen=True)
class RoleProfile:
  id: str
  name: str
  description: str
  weights: Mapping[str, float]
  core_groups: Tuple[str, ...]
  creative_floor: float = 0.25


STAT_GROUPS: Tuple[StatGroup, ...] = (
  StatGroup(
    "core_damage",
    "Core Damage",
    "Damage Stat",
    (
      "damage",
      "dmg",
      "attack",
      "weapon_damage",
      "spell_damage",
      "physical_damage",
      "magic_damage",
      "ability_power",
      "attack_power",
      "spell_power",
      "dps",
      "base_damage",
      "base_attack",
      "weapon_power",
      "raw_power",
      "power",
    ),
  ),
  StatGroup(
    "crit_stats",
    "Crit Stats",
    "Damage Stat",
    (
      "critical_chance",
      "crit_chance",
      "crit",
      "critical_strike_chance",
      "critical_damage",
      "crit_damage",
      "critical_damage_multiplier",
      "crit_multiplier",
      "crit_mult",
    ),
  ),
  StatGroup(
    "penetration",
    "Penetration",
    "Damage Stat",
    (
      "penetration",
      "armor_pen",
      "armor_penetration",
      "magic_pen",
      "magic_penetration",
      "spell_pen",
      "resist_pen",
      "flat_pen",
      "percent_pen",
    ),
  ),
  StatGroup(
    "on_hit",
    "Hit Effect",
    "Damage Stat",
    (
      "on_hit",
      "onhit",
      "lifesteal",
      "life_steal",
      "vamp",
      "vampiric",
      "thorns",
      "heal_on_hit",
      "damage_on_hit",
      "leech",
      "proc",
      "procs",
      "chain",
      "rampage",
    ),
  ),
  StatGroup(
    "health_core",
    "Health/EHP",
    "Defense Stat",
    (
      "health",
      "hp",
      "vitality",
      "life",
      "max_hp",
      "health_points",
      "evasion_hp",
      "tank_health",
      "base_hp",
    ),
  ),
  StatGroup(
    "shield",
    "Shield/Barrier",
    "Defense Stat",
    (
      "shield",
      "absorb",
      "barrier",
      "ward",
      "aegis",
      "fortify",
      "block_shield",
    ),
  ),
  StatGroup(
    "regen",
    "Health Sustain",
    "Defense Stat",
    (
      "health_regen",
      "hp_regen",
      "regen",
      "recovery",
      "healing",
      "heal_power",
      "healing_power",
      "life_regen",
    ),
  ),
  StatGroup(
    "resistance",
    "Resistance",
    "Defense Stat",
    (
      "resistance",
      "resist",
      "magic_resistance",
      "physical_resistance",
      "armor",
      "armour",
      "damage_reduction",
      "evasion",
      "dodge",
      "deflect",
      "block",
    ),
  ),
  StatGroup(
    "avoidance",
    "Avoidance",
    "Defense Stat",
    (
      "tenacity",
      "cc_res",
      "cc_resistance",
      "stun_resistance",
      "control_resistance",
      "knockback",
      "knockdown",
      "stagger_resist",
      "stability",
    ),
  ),
  StatGroup(
    "mobility",
    "Mobility",
    "Mobility/Tempo",
    (
      "movement_speed",
      "move_speed",
      "speed",
      "run_speed",
      "walk_speed",
      "acceleration",
      "mobility",
    ),
  ),
  StatGroup(
    "tempo",
    "Attack/Cast Tempo",
    "Mobility/Tempo",
    (
      "attack_speed",
      "attack_rate",
      "cast_speed",
      "haste",
      "cooldown",
      "ability_haste",
      "cdr",
      "action_speed",
    ),
    True,
  ),
  StatGroup(
    "resource",
    "Resource",
    "Utility",
    (
      "mana",
      "energy",
      "stamina",
      "focus",
      "rage",
      "essence",
      "soul",
      "ammo",
      "charge",
    ),
  ),
  StatGroup(
    "resource_regen",
    "Resource Regeneration",
    "Utility",
    (
      "mana_regen",
      "energy_regen",
      "stamina_regen",
      "resource_regen",
      "focus_regen",
      "spell_vamp",
    ),
  ),
  StatGroup(
    "utility",
    "Utility & Control",
    "Utility",
    (
      "utility",
      "cc",
      "stun",
      "slow",
      "knockup",
      "silence",
      "interrupt",
      "interrupt_chance",
      "buff",
      "debuff",
      "resist_all",
      "tenacity",
      "visibility",
      "utility_power",
      "control",
      "block",
      "interrupt",
    ),
  ),
  StatGroup(
    "primary_attributes",
    "Primary Attributes",
    "Primary Architecture",
    (
      "strength",
      "str",
      "agility",
      "agi",
      "intelligence",
      "int",
      "wisdom",
      "spirit",
      "dexterity",
    ),
  ),
  StatGroup(
    "secondary_attributes",
    "Secondary Stats",
    "Primary Architecture",
    (
      "crit_rating",
      "mastery",
      "versatility",
      "haste_rating",
      "mastery_rating",
      "versatility_rating",
      "accuracy",
      "critical_rating",
      "avoidance_rating",
      "mult",
    ),
  ),
)


ROLE_PROFILES: Mapping[str, RoleProfile] = {
  "dps": RoleProfile(
    id="dps",
    name="DPS",
    description="Focuses on burst and sustained kill pressure.",
    weights={
      "core_damage": 2.2,
      "crit_stats": 2.0,
      "penetration": 1.5,
      "on_hit": 1.0,
      "tempo": 1.1,
      "mobility": 0.6,
      "primary_attributes": 0.4,
    },
    core_groups=("core_damage", "crit_stats", "penetration"),
  ),
  "tank": RoleProfile(
    id="tank",
    name="Tank",
    description="Prioritizes survivability and control while staying on target.",
    weights={
      "health_core": 2.2,
      "resistance": 1.9,
      "shield": 1.7,
      "regen": 1.2,
      "avoidance": 1.4,
      "utility": 0.9,
      "mobility": 0.6,
    },
    core_groups=("health_core", "resistance", "shield"),
  ),
  "support": RoleProfile(
    id="support",
    name="Support",
    description="Optimized for enablement, utility, and team endurance.",
    weights={
      "utility": 2.0,
      "resource": 1.8,
      "resource_regen": 1.4,
      "resistance": 1.1,
      "regen": 1.0,
      "mobility": 0.6,
      "core_damage": 0.4,
    },
    core_groups=("utility", "resource", "resource_regen"),
  ),
  "controller": RoleProfile(
    id="controller",
    name="Controller",
    description="Designed for crowd control, pressure, and tempo manipulation.",
    weights={
      "utility": 1.9,
      "tempo": 1.2,
      "mobility": 0.8,
      "core_damage": 1.2,
      "on_hit": 0.7,
      "primary_attributes": 0.5,
    },
    core_groups=("utility", "tempo"),
  ),
  "balanced": RoleProfile(
    id="balanced",
    name="Balanced",
    description="Generalist profile for mixed builds.",
    weights={
      "core_damage": 1.2,
      "health_core": 1.2,
      "resistance": 1.0,
      "crit_stats": 1.0,
      "mobility": 0.8,
      "tempo": 0.8,
      "resource": 0.7,
      "utility": 0.7,
    },
    core_groups=("core_damage", "health_core", "resistance"),
  ),
}


_GROUP_BY_ID = {group.id: group for group in STAT_GROUPS}
_DEFAULT_ROLE = "balanced"

_META_GROUPS = {
  "dps": {"core_damage", "crit_stats", "penetration"},
  "tank": {"health_core", "resistance", "shield"},
  "support": {"utility", "resource", "resource_regen"},
  "controller": {"utility", "tempo"},
  "balanced": {"core_damage", "resistance", "utility"},
}

_RARITY_POWER_PROFILE: Mapping[str, Mapping[str, float]] = {
  "common": {
    "stat_multiplier": 1.00,
    "enchant_multiplier": 0.90,
    "rarity_bonus": 0.5,
    "trigger_cap": 1.8,
  },
  "uncommon": {
    "stat_multiplier": 1.12,
    "enchant_multiplier": 1.00,
    "rarity_bonus": 0.8,
    "trigger_cap": 2.3,
  },
  "rare": {
    "stat_multiplier": 1.28,
    "enchant_multiplier": 1.2,
    "rarity_bonus": 1.2,
    "trigger_cap": 2.9,
  },
  "epic": {
    "stat_multiplier": 1.45,
    "enchant_multiplier": 1.4,
    "rarity_bonus": 1.8,
    "trigger_cap": 3.8,
  },
  "legendary": {
    "stat_multiplier": 1.62,
    "enchant_multiplier": 1.65,
    "rarity_bonus": 2.6,
    "trigger_cap": 5.2,
  },
  "mythic": {
    "stat_multiplier": 1.85,
    "enchant_multiplier": 2.0,
    "rarity_bonus": 3.8,
    "trigger_cap": 6.4,
  },
}

_GROUP_SOFT_CAPS = {
  "core_damage": 5.0,
  "crit_stats": 1.8,
  "penetration": 1.2,
  "on_hit": 2.2,
  "health_core": 5.5,
  "shield": 4.0,
  "regen": 4.0,
  "resistance": 3.5,
  "avoidance": 2.5,
  "mobility": 2.2,
  "tempo": 2.2,
  "resource": 3.0,
  "resource_regen": 2.8,
  "utility": 2.0,
  "primary_attributes": 1.8,
  "secondary_attributes": 2.0,
}

_ENCHANT_TRIGGER_ALIASES = {
  "on_crit": "on_crit",
  "on_critical": "on_crit",
  "oncritical": "on_crit",
  "crit_chance": "on_crit",
  "when_critical": "on_crit",
  "critical": "on_crit",

  "on_hit": "on_hit",
  "on_attacks": "on_hit",
  "attack_hit": "on_hit",
  "onhit": "on_hit",
  "proc_on_hit": "on_hit",

  "on_kill": "on_kill",
  "kill": "on_kill",
  "on_elite": "on_elite",
  "on_boss": "on_elite",

  "on_cast": "on_cast",
  "cast": "on_cast",
  "while_casting": "on_cast",

  "on_dash": "on_move",
  "on_move": "on_move",
  "on_dodge": "on_move",
  "after_dash": "on_move",
  "mobility_boost": "on_move",

  "while_channeling": "state_window",
  "while_moving": "state_window",
  "while_stationary": "state_window",
  "while_low_hp": "state_window",

  "below_health": "state_window",
  "low_health": "state_window",
  "below_25_hp": "state_window",

  "on_shield": "state_window",
  "while_shielded": "state_window",
}

_ENCHANT_GROUP_ALIASES = {
  "crit": "crit_stats",
  "critical": "crit_stats",
  "crit_boost": "crit_stats",
  "lifesteal": "on_hit",
  "vampiric": "on_hit",
  "heal": "regen",
  "healing": "regen",
  "regen": "regen",
  "shield": "shield",
  "barrier": "shield",
  "armor": "resistance",
  "resist": "resistance",
  "dodge": "avoidance",
  "stun": "utility",
  "cc": "utility",
  "mobility": "mobility",
  "speed": "mobility",
  "tempo": "tempo",
  "cast_speed": "tempo",
  "attack_speed": "tempo",
  "cooldown": "tempo",
}

_VALUE_KEYS = (
  "value",
  "amount",
  "magnitude",
  "bonus",
  "buff",
  "mult",
  "multiplier",
  "chance",
  "rating",
)



def _normalize_key(raw: str) -> str:
  lowered = (raw or "").strip().lower()
  normalized = "".join(ch if ch.isalnum() else "_" for ch in lowered)
  while "__" in normalized:
    normalized = normalized.replace("__", "_")
  return normalized.strip("_")


class ItemOptimizationEngine:
  def _safe_float(self, value: Any) -> float:
    try:
      numeric = float(value)
    except (TypeError, ValueError):
      return 0.0
    if not math.isfinite(numeric):
      return 0.0
    return numeric

  def _extract_first_number(self, value: Any) -> float:
    if value is None:
      return 0.0
    text = str(value)
    match = re.search(r"-?[0-9]+(?:\\.[0-9]+)?", text)
    if not match:
      return self._safe_float(value)
    return self._safe_float(match.group(0))

  def _parse_rarity_profile(self, item_payload: Mapping[str, Any]) -> Dict[str, float]:
    raw_rarity = str(item_payload.get("rarity", "uncommon") or "uncommon").strip().lower()
    return dict(_RARITY_POWER_PROFILE.get(raw_rarity, _RARITY_POWER_PROFILE["uncommon"]))

  def _match_group(self, stat_key: str) -> str:
    normalized = _normalize_key(stat_key)
    for group in STAT_GROUPS:
      for alias in group.aliases:
        pattern = _normalize_key(alias)
        if normalized == pattern or normalized.startswith(f"{pattern}_") or f"_{pattern}_" in f"_{normalized}_":
          return group.id
      for alias in group.aliases:
        pattern = _normalize_key(alias)
        if pattern in normalized:
          return group.id
    return "utility"

  def _stat_value(self, group_id: str, value: float) -> float:
    magnitude = max(0.0, self._safe_float(value))
    if magnitude <= 0:
      return 0.0

    if group_id in _GROUP_BY_ID and _GROUP_BY_ID[group_id].normalize_as_percent:
      magnitude = magnitude / 100.0

    soft_cap = _GROUP_SOFT_CAPS.get(group_id, 10000.0)
    if magnitude > soft_cap:
      magnitude = soft_cap + math.log1p(magnitude - soft_cap)
    magnitude = max(0.0, min(magnitude, 10000.0))
    return max(0.0, math.log1p(magnitude))

  def _group_stats(self, stats: Mapping[str, Any]) -> Dict[str, float]:
    grouped: Dict[str, float] = {}
    for stat_name, raw in stats.items():
      group_id = self._match_group(stat_name)
      if group_id not in grouped:
        grouped[group_id] = 0.0
      grouped[group_id] += self._stat_value(group_id, raw)
    return grouped

  def _weighted_score(self, grouped: Mapping[str, float], role: RoleProfile) -> Tuple[float, Dict[str, float]]:
    breakdown: Dict[str, float] = {}
    total = 0.0
    for group_id, amount in grouped.items():
      weight = role.weights.get(group_id, 0.0)
      if weight == 0.0:
        continue
      contribution = amount * weight
      breakdown[group_id] = contribution
      total += contribution
    return total, breakdown

  def _dedupe_text(self, value: Any) -> str:
    return "".join(ch for ch in str(value) if ch.isalnum() or ch in "_-").strip().lower()

  def _collect_condition_signals(self, effect: Mapping[str, Any]) -> Tuple[List[str], bool]:
    raw_conditions = []
    condition = effect.get("condition") or effect.get("conditions") or effect.get("when") or effect.get("requires")
    if condition:
      if isinstance(condition, Mapping):
        for key, raw_value in condition.items():
          normalized_key = _normalize_key(str(key))
          signal = normalized_key
          if raw_value not in (None, ""):
            if isinstance(raw_value, bool):
              signal = f"{signal}:{str(raw_value).lower()}"
            else:
              value = self._extract_first_number(raw_value)
              if value:
                signal = f"{signal}:{value}"
          raw_conditions.append(signal)
      elif isinstance(condition, (list, tuple, set)):
        for raw in condition:
          if isinstance(raw, Mapping):
            for key, raw_value in raw.items():
              raw_conditions.append(f"{_normalize_key(str(key))}:{self._extract_first_number(raw_value)}")
          elif raw is not None:
            text = str(raw).strip().lower()
            if text:
              raw_conditions.append(text)
      else:
        text = str(condition).strip()
        if text:
          raw_conditions.append(text)

    for key in ("target", "phase", "target_class", "target_type", "time_window", "resource", "health_state", "status"):
      raw = effect.get(key)
      if raw not in (None, ""):
        text = self._dedupe_text(raw)
        if text:
          raw_conditions.append(f"{key}:{text}")

    explicit_gating = False
    for key in ("hp_percent", "hp_below", "hp_above", "mana_percent", "distance", "cooldown", "requires_channel"):
      if effect.get(key) not in (None, ""):
        explicit_gating = True
        break

    seen = []
    for cond in raw_conditions:
      compact = _normalize_key(cond)
      if compact:
        seen.append(compact)
    compacted = sorted(set(seen))
    return compacted, explicit_gating

  def _effect_group(self, effect: Mapping[str, Any]) -> str:
    direct = effect.get("family") or effect.get("group") or effect.get("category")
    if isinstance(direct, str):
      normalized_direct = _normalize_key(direct)
      if normalized_direct in _GROUP_BY_ID:
        return normalized_direct
    for key in list(effect.keys()):
      if key in {"type", "effect", "name", "id", "mode", "source", "notes", "description"}:
        continue
      normalized = _normalize_key(str(key))
      group_guess = self._match_group(normalized)
      if group_guess != "utility":
        return group_guess

    raw_type = str(effect.get("type") or effect.get("name") or effect.get("effect") or "").strip()
    normalized_type = _normalize_key(raw_type)
    if normalized_type in _ENCHANT_GROUP_ALIASES:
      return _ENCHANT_GROUP_ALIASES[normalized_type]
    for alias, group_id in _ENCHANT_GROUP_ALIASES.items():
      alias_norm = _normalize_key(alias)
      if alias_norm in normalized_type or normalized_type in alias_norm:
        return group_id
    return "utility"

  def _effect_trigger(self, effect: Mapping[str, Any]) -> str:
    for key in ("trigger", "event", "on", "when"):
      raw = effect.get(key)
      if not raw:
        continue
      normalized = _normalize_key(str(raw))
      if normalized in _ENCHANT_TRIGGER_ALIASES:
        return _ENCHANT_TRIGGER_ALIASES[normalized]
      for alias, trigger_id in _ENCHANT_TRIGGER_ALIASES.items():
        if _normalize_key(alias) in normalized or normalized in _normalize_key(alias):
          return trigger_id

    type_hint = str(effect.get("type") or effect.get("name") or effect.get("effect") or "").strip()
    type_norm = _normalize_key(type_hint)
    if type_norm in _ENCHANT_TRIGGER_ALIASES:
      return _ENCHANT_TRIGGER_ALIASES[type_norm]

    for alias, trigger_id in _ENCHANT_TRIGGER_ALIASES.items():
      alias_norm = _normalize_key(alias)
      if alias_norm in type_norm or type_norm in alias_norm:
        return trigger_id

    if any(_normalize_key(token) in effect for token in ("on_crit", "on_hit", "on_kill", "on_cast")):
      return "on_misc"
    return ""

  def _effect_value(self, effect: Mapping[str, Any], group_id: str) -> float:
    candidates: List[float] = []
    for key in _VALUE_KEYS:
      candidates.append(self._extract_first_number(effect.get(key)))

    for key in ("stats", "stat_mods", "modifiers"):
      values = effect.get(key)
      if isinstance(values, Mapping):
        for stat_name, raw in values.items():
          if self._match_group(str(stat_name)) == group_id:
            candidates.append(self._extract_first_number(raw))
    for key in effect.keys():
      if key in _VALUE_KEYS:
        continue
      if _match_group(str(key)) == group_id:
        candidates.append(self._extract_first_number(effect.get(key)))

    magnitude = max(candidates) if candidates else 0.0
    magnitude = max(0.0, magnitude)

    if group_id in _GROUP_BY_ID and _GROUP_BY_ID[group_id].normalize_as_percent:
      magnitude /= 100.0
    return max(0.0, magnitude)

  def _evaluate_enchantments(self, item_payload: Mapping[str, Any], role: RoleProfile, rarity_profile: Mapping[str, float]) -> Dict[str, Any]:
    raw_effects = []
    for field_name in ("magic_effects", "applied_enhancements"):
      raw_block = item_payload.get(field_name)
      if isinstance(raw_block, list):
        raw_effects.extend(raw_block)

    if not raw_effects:
      return {
        "score": 0.0,
        "raw_total": 0.0,
        "effect_count": 0,
        "active_triggers": 0,
        "complexity": 0.0,
        "details": {
          "dominant_condition_depth": 0,
          "trigger_diversity": 0,
          "condition_density": 0.0,
          "notes": ["No enchantments to evaluate for triggers/conditions."],
        },
      }

    total_score = 0.0
    raw_total = 0.0
    trigger_counter: Counter[str] = Counter()
    group_scores: Dict[str, float] = {}
    condition_counts: List[int] = []
    condition_tokens: List[str] = []

    for raw in raw_effects:
      if not isinstance(raw, Mapping):
        continue
      effect = dict(raw)
      group_id = self._effect_group(effect)
      trigger = self._effect_trigger(effect)
      conditions, explicit_gate = self._collect_condition_signals(effect)
      condition_counts.append(len(conditions))
      condition_tokens.extend(conditions)

      if trigger:
        trigger_counter[trigger] += 1

      base = self._effect_value(effect, group_id)
      role_weight = role.weights.get(group_id, 0.45)
      if base <= 0:
        continue

      base_weighted = math.log1p(base) * role_weight
      if trigger:
        base_weighted *= 1.25

      if conditions:
        condition_ratio = min(1.5, 0.4 + 0.25 * len(conditions))
        if explicit_gate:
          condition_ratio += 0.15
      else:
        condition_ratio = 0.9

      cooldown = self._safe_float(effect.get("cooldown") or effect.get("cd") or 0)
      cooldown_ratio = 1.0 / (1.0 + max(0.0, cooldown) / 14.0)
      duration = self._safe_float(effect.get("duration") or 0)
      duration_ratio = 1.0 + min(0.5, max(0.0, duration) / 24.0)

      effect_score = base_weighted * condition_ratio * cooldown_ratio * duration_ratio
      total_score += effect_score
      raw_total += base
      group_scores[group_id] = group_scores.get(group_id, 0.0) + effect_score

    effects_count = sum(1 for raw in raw_effects if isinstance(raw, Mapping))
    trigger_diversity = len(trigger_counter)
    if effects_count > 0:
      repeated_trigger_penalty = 0.0
      for count in trigger_counter.values():
        if count > 1:
          repeated_trigger_penalty += (count - 1) * 0.22
    else:
      repeated_trigger_penalty = 0.0

    active_triggers = len([count for count in trigger_counter.values() if count > 0])
    complexity = 0.0
    if condition_counts:
      avg_conditions = sum(condition_counts) / len(condition_counts)
      complexity += min(2.5, avg_conditions * 0.7)
      condition_density = avg_conditions / max(1.0, active_triggers + 1.0)
      complexity += condition_density * 0.6

    diversity_bonus = min(1.8, trigger_diversity * 0.35)
    raw_total *= rarity_profile["enchant_multiplier"]
    total_score = (total_score * rarity_profile["enchant_multiplier"]) + diversity_bonus + complexity - repeated_trigger_penalty

    notes = []
    if active_triggers == 0:
      notes.append("No explicit trigger conditions; effects behave like passive modifiers.")
    elif active_triggers < 2:
      notes.append("One trigger type; add another trigger family for richer play loops.")
    if condition_counts and max(condition_counts) > 2:
      notes.append("Includes high-threshold condition checks for tactical windows.")
    if repeated_trigger_penalty > 0:
      notes.append("Same trigger repeats reduce trigger diversity and can flatten gameplay.")

    dominant_condition = []
    if condition_tokens:
      counted = Counter(condition_tokens)
      dominant_condition = [token for token, _ in counted.most_common(2)]

    enchantment_score = max(0.0, total_score)
    # trigger_budget keeps powerful rare items flavorful but prevents over-optimized trigger chains
    trigger_cap = rarity_profile["trigger_cap"]
    enchantment_score = min(enchantment_score, trigger_cap)

    return {
      "score": round(enchantment_score * 10.0, 2),
      "raw_total": round(raw_total, 3),
      "effect_count": effects_count,
      "active_triggers": active_triggers,
      "complexity": round(complexity, 3),
      "group_scores": {group: round(value, 3) for group, value in sorted(group_scores.items(), key=lambda item: item[1], reverse=True)},
      "details": {
        "trigger_diversity": trigger_diversity,
        "condition_density": round(sum(condition_counts) / len(condition_counts), 3) if condition_counts else 0.0,
        "dominant_condition_depth": dominant_condition[0] if dominant_condition else "",
        "trigger_penalty": round(repeated_trigger_penalty, 3),
        "notes": notes,
      },
    }

  def _creativity_bonus(self, grouped: Mapping[str, float], role: RoleProfile) -> Tuple[float, Dict[str, Any]]:
    active_groups = [group for group, amount in grouped.items() if amount > 0]
    if not active_groups:
      return 0.0, {
        "active_groups": 0,
        "messages": ["Item has no recognized stats."],
      }

    total = sum(grouped.values()) or 1.0
    sorted_groups = sorted(grouped.items(), key=lambda item: item[1], reverse=True)
    top = sorted_groups[0][0] if sorted_groups else None
    dominant_ratio = (sorted_groups[0][1] / total) if sorted_groups else 0.0

    meta_overlap = len(set(active_groups) & set(_META_GROUPS.get(role.id, set())))
    meta_clamp = min(0.22, meta_overlap * 0.07)

    category_mix = {
      _GROUP_BY_ID.get(group, StatGroup("utility", "Utility", "Utility", ("utility",))).category
      for group in active_groups
    }
    cross_category_bonus = max(0.0, len(category_mix) - 2) * 0.7
    family_diversity = max(0.0, len(active_groups) - 1) * 1.4
    off_theme = [group for group in active_groups if group not in role.core_groups]
    off_theme_bonus = min(1.0, len(off_theme) / max(1, len(role.core_groups))) * 2.2
    balance_penalty = max(0.0, dominant_ratio - 0.70) * 18.0

    bonus = (
      family_diversity
      + off_theme_bonus
      + cross_category_bonus
      - balance_penalty
      - meta_clamp * 5.0
    )
    bonus = max(0.0, bonus)

    messages: List[str] = []
    if len(active_groups) < 2:
      messages.append("Consider adding one off-theme family to improve creative diversity.")
    if dominant_ratio > 0.70:
      messages.append(f"Reduce concentration on '{top}' to unlock more build paths.")
    if meta_overlap >= 2:
      messages.append("Meta-cluster detected; mixed stat families score higher.")
    if off_theme:
      messages.append("Creative mix already present via non-core stat families.")

    return bonus, {
      "active_groups": len(active_groups),
      "dominant_ratio": dominant_ratio,
      "meta_overlap": meta_overlap,
      "meta_clamp": round(meta_clamp, 3),
      "messages": messages,
    }

  def _apply_rarity_and_enchant_balance(self, stats_score: float, enchantment_score: float, role: RoleProfile,
                                      rarity_profile: Mapping[str, float], details: Dict[str, Any]) -> float:
    rarity_boost = rarity_profile["stat_multiplier"]
    raw_total = stats_score * rarity_boost
    rarity_anchor = rarity_profile["rarity_bonus"]
    return max(0.0, raw_total + enchantment_score + rarity_anchor)

  def evaluate(self, item_payload: Mapping[str, Any], role: str = _DEFAULT_ROLE) -> Dict[str, Any]:
    stats = item_payload.get("stats", {})
    if not isinstance(stats, Mapping):
      raise ValueError("Item payload missing `stats` map.")

    normalized_role = (role or _DEFAULT_ROLE).strip().lower()
    profile = ROLE_PROFILES.get(normalized_role, ROLE_PROFILES[_DEFAULT_ROLE])
    rarity_profile = self._parse_rarity_profile(item_payload)

    grouped = self._group_stats(stats)

    role_raw, role_breakdown = self._weighted_score(grouped, profile)
    role_score = round(role_raw * 10.0 * rarity_profile["stat_multiplier"], 2)
    creativity, details = self._creativity_bonus(grouped, profile)
    creativity_score = round(creativity * 6.5, 2)

    enchantments = self._evaluate_enchantments(item_payload, profile, rarity_profile)
    enchantment_score = enchantments["score"]

    final_meta = 1.0 - details["meta_clamp"]
    total_score = round(
      (role_score * final_meta)
      + creativity_score
      + enchantment_score
      + rarity_profile["rarity_bonus"],
      2,
    )
    total_score = max(0.0, total_score)

    grouped_summary: Dict[str, Dict[str, Any]] = {}
    for group_id, score in sorted(grouped.items(), key=lambda item: item[1], reverse=True):
      group = _GROUP_BY_ID.get(group_id)
      grouped_summary[group_id] = {
        "group": group.name if group else group_id,
        "category": group.category if group else "Utility",
        "value": round(score, 3),
        "weight_for_role": profile.weights.get(group_id, 0.0),
        "role_contribution": round(role_breakdown.get(group_id, 0.0) * 10.0 * rarity_profile["stat_multiplier"], 2),
      }

    summary = {
      "asset_id": item_payload.get("asset_id", item_payload.get("blueprint_key", "")),
      "name": item_payload.get("name", item_payload.get("blueprint_key", "Unknown")),
      "rarity": str(item_payload.get("rarity", "uncommon")).lower(),
      "role": profile.name,
      "role_score": role_score,
      "creativity_score": creativity_score,
      "enchantment_score": enchantment_score,
      "rarity_bonus": round(rarity_profile["rarity_bonus"], 2),
      "total_score": total_score,
      "group_summary": grouped_summary,
      "stats_count": len(stats),
      "family_count": len([value for value in grouped.values() if value > 0]),
      "enchantments": enchantments,
      "creativity": details,
    }

    return summary

  def benchmark(self, assets: Iterable[Mapping[str, Any]], role: str = _DEFAULT_ROLE, include_role_score: bool = True) -> List[Dict[str, Any]]:
    ranked = []
    for asset in assets:
      score = self.evaluate(asset, role=role)
      ranked.append(score)
    if include_role_score:
      ranked.sort(key=lambda row: row["total_score"], reverse=True)
    else:
      ranked.sort(key=lambda row: row["total_score"], reverse=True)
    for index, row in enumerate(ranked, start=1):
      row["rank"] = index
    return ranked

  def role_profiles(self) -> Dict[str, Dict[str, Any]]:
    profiles: Dict[str, Dict[str, Any]] = {}
    for key, profile in ROLE_PROFILES.items():
      profiles[key] = {
        "id": profile.id,
        "name": profile.name,
        "description": profile.description,
        "core_groups": list(profile.core_groups),
      }
    return profiles
