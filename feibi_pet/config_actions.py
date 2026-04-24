from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path


@dataclass(slots=True)
class IdleActionWeight:
    action: str
    weight: int
    duration_ms: int = 0


@dataclass(slots=True)
class BehaviorConfig:
    default_action: str = "idle"
    randomize_gif_on_loop: bool = True
    transition_duration_ms: int = 150
    idle_actions: list[IdleActionWeight] = field(default_factory=list)


@dataclass(slots=True)
class ActionConfig:
    name: str
    gifs: list[Path]
    sounds: list[Path] = field(default_factory=list)
    auto_return_ms: int = 0
    return_to: str = ""
    play_sound_on_enter: bool = False
    offset_x: int = 0
    offset_y: int = 0
    transition_duration_ms: int | None = None
    flip_horizontal: bool = False
