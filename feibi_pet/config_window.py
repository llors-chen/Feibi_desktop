from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(slots=True)
class Position:
    anchor: str = "top_left"
    x: int = 120
    y: int = 120


@dataclass(slots=True)
class WindowConfig:
    title: str = "Feibi Pet"
    transparent_color: str = "#00FF00"
    stay_on_top: bool = True
    alpha: float = 1.0
    scale: float = 2.0
    scale_mode: str = "nearest"
    draggable: bool = True
    click_through: bool = False
    initial_position: Position = field(default_factory=Position)
