from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path


@dataclass(slots=True)
class AudioConfig:
    enabled: bool = True
    volume_percent: int = 85


@dataclass(slots=True)
class SoundPakConfig:
    sounds: list[Path] = field(default_factory=list)
    loop_pause_seconds: float = 2.0


@dataclass(slots=True)
class SoundConfig:
    enabled: bool = True
    volume_percent: int = 85
    speaking_intro: SoundPakConfig = field(default_factory=SoundPakConfig)
    chat_loop: SoundPakConfig = field(default_factory=SoundPakConfig)
