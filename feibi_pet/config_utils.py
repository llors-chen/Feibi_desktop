from __future__ import annotations

from pathlib import Path
from typing import Any

from .config_defaults import POSITION_ANCHORS
from .config_models import ActionConfig, ConfigError, IdleActionWeight


def coerce_bool(value: Any, default: bool) -> bool:
    if isinstance(value, bool):
        return value
    return default


def coerce_text(value: Any, default: str) -> str:
    if isinstance(value, str) and value.strip():
        return value.strip()
    return default


def coerce_optional_text(value: Any, default: str = "") -> str:
    if isinstance(value, str):
        return value.strip()
    return default


def coerce_anchor(value: Any, default: str) -> str:
    if isinstance(value, str):
        normalized = value.strip().lower().replace("-", "_")
        if normalized in POSITION_ANCHORS:
            return normalized
    return default


def coerce_int(
    value: Any,
    default: int,
    min_value: int | None = None,
    max_value: int | None = None,
) -> int:
    try:
        coerced = int(value)
    except Exception:
        return default
    if min_value is not None and coerced < min_value:
        return default
    if max_value is not None and coerced > max_value:
        return default
    return coerced


def coerce_float(
    value: Any,
    default: float,
    min_value: float | None = None,
    max_value: float | None = None,
) -> float:
    try:
        coerced = float(value)
    except Exception:
        return default
    if min_value is not None and coerced < min_value:
        return default
    if max_value is not None and coerced > max_value:
        return default
    return coerced


def coerce_path_list(
    value: Any,
    base_dir: Path,
    field_name: str,
    *,
    allow_empty: bool = False,
) -> list[Path]:
    if value is None:
        return [] if allow_empty else raise_path_error(field_name, "is required")

    raw_items: list[str]
    if isinstance(value, str):
        raw_items = [value]
    elif isinstance(value, list):
        raw_items = []
        for item in value:
            if not isinstance(item, str) or not item.strip():
                raise ConfigError(f"'{field_name}' must contain non-empty strings.")
            raw_items.append(item.strip())
    else:
        raise ConfigError(f"'{field_name}' must be a string or string list.")

    if not raw_items:
        if allow_empty:
            return []
        raise ConfigError(f"'{field_name}' must not be empty.")

    paths: list[Path] = []
    for raw_item in raw_items:
        candidate = Path(raw_item)
        if not candidate.is_absolute():
            candidate = base_dir / candidate
        candidate = candidate.resolve()
        if not candidate.exists():
            raise ConfigError(f"Missing file for '{field_name}': {candidate}")
        paths.append(candidate)
    return paths


def load_idle_actions(
    value: Any,
    available_actions: dict[str, ActionConfig],
) -> list[IdleActionWeight]:
    if not isinstance(value, list):
        return []

    result: list[IdleActionWeight] = []
    for item in value:
        if not isinstance(item, dict):
            continue
        action = coerce_optional_text(item.get("action"), "")
        weight = coerce_int(item.get("weight"), 0, min_value=0)
        duration_ms = coerce_int(item.get("duration_ms"), 0, min_value=0)
        if action and action in available_actions and weight > 0:
            result.append(
                IdleActionWeight(
                    action=action,
                    weight=weight,
                    duration_ms=duration_ms,
                )
            )

    return result


def raise_path_error(field_name: str, message: str) -> list[Path]:
    raise ConfigError(f"'{field_name}' {message}.")


def coerce_scale_mode(value: Any, default: str) -> str:
    allowed = {"nearest", "box", "bilinear", "bicubic", "lanczos"}
    if isinstance(value, str):
        normalized = value.strip().lower()
        if normalized in allowed:
            return normalized
    return default


def resolve_skill_path(
    skill: str,
    skills_dir_value: Any,
    base_dir: Path,
) -> Path | None:
    if not skill:
        return None

    skill_candidate = Path(skill)
    if skill_candidate.is_absolute():
        return skill_candidate

    if skill_candidate.suffix or "/" in skill or "\\" in skill:
        return (base_dir / skill_candidate).resolve()

    skills_dir = resolve_directory(skills_dir_value, base_dir, base_dir / "skills")
    return (skills_dir / f"{skill}.txt").resolve()


def resolve_directory(value: Any, base_dir: Path, default: Path) -> Path:
    if not isinstance(value, str) or not value.strip():
        return default.resolve()
    path = Path(value.strip())
    if not path.is_absolute():
        path = base_dir / path
    return path.resolve()


def resolve_soundpak_paths(value: Any, base_dir: Path) -> list[Path]:
    if value is None:
        return []

    raw_items: list[str]
    if isinstance(value, str):
        raw_items = [value]
    elif isinstance(value, list):
        raw_items = []
        for item in value:
            if not isinstance(item, str) or not item.strip():
                continue
            raw_items.append(item.strip())
    else:
        return []

    if not raw_items:
        return []

    paths: list[Path] = []
    audio_extensions = {".mp3", ".wav", ".ogg", ".flac", ".m4a"}

    for raw_item in raw_items:
        candidate = Path(raw_item)
        if not candidate.is_absolute():
            candidate = base_dir / candidate
        candidate = candidate.resolve()

        if not candidate.exists():
            continue

        if candidate.is_file() and candidate.suffix.lower() in audio_extensions:
            paths.append(candidate)
        elif candidate.is_dir():
            for ext in audio_extensions:
                paths.extend(sorted(candidate.glob(f"*{ext}")))

    return paths
