from __future__ import annotations

from dataclasses import dataclass
from dataclasses import field
from pathlib import Path


@dataclass(slots=True)
class ChatStageConfig:
    action: str = ""
    duration_ms: int = 0
    play_sound: bool = False
    sounds: list[Path] = field(default_factory=list)
    transition_duration_ms: int = 1000


@dataclass(slots=True)
class ChatConfig:
    enabled: bool = False
    api_key: str = ""
    model: str = ""
    base_url: str = ""
    timeout_seconds: float = 30.0
    max_history: int = 6
    skill: str = ""
    skill_path: Path | None = None
    system_prompt: str = ""
    bubble_max_width: int = 320
    bubble_auto_hide_ms: int = 15000
    input_stage: ChatStageConfig = field(default_factory=ChatStageConfig)
    waiting_stage: ChatStageConfig = field(default_factory=ChatStageConfig)
    reply_stage: ChatStageConfig = field(default_factory=ChatStageConfig)
    error_stage: ChatStageConfig = field(default_factory=ChatStageConfig)
