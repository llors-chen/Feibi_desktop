from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from .config_actions import ActionConfig, BehaviorConfig, IdleActionWeight
from .config_api import ChatConfig, ChatMemoryConfig, ChatStageConfig
from .config_audio import AudioConfig, SoundConfig, SoundPakConfig
from .config_window import Position, WindowConfig


class ConfigError(ValueError):
    pass


@dataclass(slots=True)
class PetConfig:
    source_path: Path
    window: WindowConfig
    audio: AudioConfig
    sound: SoundConfig
    behavior: BehaviorConfig
    chat: ChatConfig
    actions: dict[str, ActionConfig]


__all__ = [
    "ActionConfig",
    "AudioConfig",
    "BehaviorConfig",
    "ChatConfig",
    "ChatMemoryConfig",
    "ChatStageConfig",
    "ConfigError",
    "IdleActionWeight",
    "PetConfig",
    "Position",
    "SoundConfig",
    "SoundPakConfig",
    "WindowConfig",
]
