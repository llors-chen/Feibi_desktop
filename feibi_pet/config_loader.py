from __future__ import annotations

import json
from pathlib import Path

from .config_defaults import DEFAULT_CONFIG
from .config_models import (
    ActionConfig,
    AudioConfig,
    BehaviorConfig,
    ChatConfig,
    ChatMemoryConfig,
    ChatStageConfig,
    ConfigError,
    PetConfig,
    Position,
    SoundConfig,
    SoundPakConfig,
    WindowConfig,
)
from .config_utils import (
    coerce_anchor,
    coerce_bool,
    coerce_float,
    coerce_int,
    coerce_optional_text,
    coerce_path_list,
    coerce_scale_mode,
    coerce_text,
    load_idle_actions,
    resolve_skill_path,
    resolve_soundpak_paths,
)

DEFAULT_CHAT_STAGE_TRANSITION_MS = 1000


def ensure_default_config(config_path: Path) -> None:
    if config_path.exists():
        return
    config_path.parent.mkdir(parents=True, exist_ok=True)
    config_path.write_text(
        json.dumps(DEFAULT_CONFIG, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def load_config(config_path: str | Path) -> PetConfig:
    source_path = Path(config_path).resolve()
    ensure_default_config(source_path)

    try:
        raw = json.loads(source_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ConfigError(f"Invalid JSON in config file: {exc}") from exc

    if not isinstance(raw, dict):
        raise ConfigError("Config root must be a JSON object.")

    base_dir = source_path.parent
    window_block = raw.get("window") or {}
    audio_block = raw.get("audio") or {}
    behavior_block = raw.get("behavior") or {}
    chat_block = raw.get("chat") or {}
    actions_block = raw.get("actions") or {}

    if not isinstance(actions_block, dict):
        raise ConfigError("'actions' must be a JSON object.")
    if not isinstance(chat_block, dict):
        raise ConfigError("'chat' must be a JSON object.")

    position_block = window_block.get("initial_position") or {}
    if not isinstance(position_block, dict):
        position_block = {}

    window = WindowConfig(
        title=coerce_text(window_block.get("title"), "Feibi Pet"),
        transparent_color=coerce_text(
            window_block.get("transparent_color"), "#00FF00"
        ),
        stay_on_top=coerce_bool(window_block.get("stay_on_top"), True),
        alpha=coerce_float(window_block.get("alpha"), 1.0, 0.1, 1.0),
        scale=coerce_float(window_block.get("scale"), 2.0, 0.1, 8.0),
        scale_mode=coerce_scale_mode(window_block.get("scale_mode"), "nearest"),
        draggable=coerce_bool(window_block.get("draggable"), True),
        click_through=coerce_bool(window_block.get("click_through"), False),
        initial_position=Position(
            anchor=coerce_anchor(position_block.get("anchor"), "top_left"),
            x=coerce_int(position_block.get("x"), 120),
            y=coerce_int(position_block.get("y"), 120),
        ),
    )

    audio = AudioConfig(
        enabled=coerce_bool(audio_block.get("enabled"), True),
        volume_percent=coerce_int(audio_block.get("volume_percent"), 85, 0, 150),
    )

    sound_block = raw.get("sound") or {}
    if not isinstance(sound_block, dict):
        sound_block = {}

    speaking_intro_block = sound_block.get("speaking_intro") or {}
    if not isinstance(speaking_intro_block, dict):
        speaking_intro_block = {}
    chat_loop_block = sound_block.get("chat_loop") or {}
    if not isinstance(chat_loop_block, dict):
        chat_loop_block = {}

    sound = SoundConfig(
        enabled=coerce_bool(sound_block.get("enabled"), True),
        volume_percent=coerce_int(sound_block.get("volume_percent"), 85, 0, 150),
        speaking_intro=SoundPakConfig(
            sounds=resolve_soundpak_paths(
                speaking_intro_block.get("sounds"), base_dir
            ),
            loop_pause_seconds=coerce_float(
                speaking_intro_block.get("loop_pause_seconds"), 0.0, 0.0, 60.0
            ),
        ),
        chat_loop=SoundPakConfig(
            sounds=resolve_soundpak_paths(chat_loop_block.get("sounds"), base_dir),
            loop_pause_seconds=coerce_float(
                chat_loop_block.get("loop_pause_seconds"), 2.0, 0.0, 60.0
            ),
        ),
    )

    default_action = coerce_text(behavior_block.get("default_action"), "idle")

    skill = coerce_optional_text(chat_block.get("skill"), "phoebe")
    skill_path = resolve_skill_path(
        skill,
        chat_block.get("skills_dir"),
        base_dir,
    )
    chat_stages_block = chat_block.get("stages") or {}
    if not isinstance(chat_stages_block, dict):
        chat_stages_block = {}
    memory_block = chat_block.get("memory") or {}
    if not isinstance(memory_block, dict):
        memory_block = {}

    chat = ChatConfig(
        enabled=coerce_bool(chat_block.get("enabled"), False),
        api_key=coerce_optional_text(chat_block.get("api_key"), ""),
        model=coerce_optional_text(chat_block.get("model"), ""),
        base_url=coerce_optional_text(
            chat_block.get("base_url"),
            "https://ark.cn-beijing.volces.com/api/v3",
        ),
        timeout_seconds=coerce_float(
            chat_block.get("timeout_seconds"),
            30.0,
            min_value=5.0,
            max_value=600.0,
        ),
        max_history=coerce_int(chat_block.get("max_history"), 6, 0, 50),
        skill=skill,
        skill_path=skill_path,
        system_prompt=coerce_optional_text(chat_block.get("system_prompt"), ""),
        memory=ChatMemoryConfig(
            enabled=coerce_bool(memory_block.get("enabled"), True),
            path=_resolve_memory_path(memory_block.get("path"), base_dir),
            max_bytes=coerce_int(
                memory_block.get("max_bytes"),
                1000 * 1024,
                min_value=16 * 1024,
                max_value=64 * 1024 * 1024,
            ),
            recent_turns_after_compress=coerce_int(
                memory_block.get("recent_turns_after_compress"),
                10,
                min_value=0,
                max_value=100,
            ),
            retrieval_limit=coerce_int(
                memory_block.get("retrieval_limit"),
                5,
                min_value=0,
                max_value=30,
            ),
        ),
        bubble_max_width=coerce_int(
            chat_block.get("bubble_max_width"),
            320,
            min_value=160,
            max_value=640,
        ),
        bubble_auto_hide_ms=coerce_int(
            chat_block.get("bubble_auto_hide_ms"),
            15000,
            min_value=0,
            max_value=120000,
        ),
        input_stage=_load_chat_stage(
            chat_stages_block.get("input"),
            base_dir,
            default_action="",
            default_play_sound=True,
        ),
        waiting_stage=_load_chat_stage(
            chat_stages_block.get("waiting"),
            base_dir,
            default_action="",
            default_play_sound=False,
        ),
        reply_stage=_load_chat_stage(
            chat_stages_block.get("reply"),
            base_dir,
            default_action="",
            default_play_sound=True,
        ),
        error_stage=_load_chat_stage(
            chat_stages_block.get("error"),
            base_dir,
            default_action="",
            default_play_sound=False,
        ),
    )
    if chat.enabled:
        if not chat.api_key:
            raise ConfigError("'chat.api_key' is required when chat.enabled is true.")
        if not chat.model:
            raise ConfigError("'chat.model' is required when chat.enabled is true.")
        if chat.skill_path is not None and not chat.skill_path.exists():
            raise ConfigError(f"Chat skill file does not exist: {chat.skill_path}")

    actions = _load_actions(actions_block, base_dir, default_action)

    if not actions:
        raise ConfigError("'actions' must define at least one action.")

    available_actions = ", ".join(actions.keys())
    if default_action not in actions:
        raise ConfigError(
            f"'behavior.default_action' must be one of configured actions: "
            f"{available_actions}"
        )

    for action_name, action in actions.items():
        if action.return_to not in actions:
            raise ConfigError(
                f"Action '{action_name}' return target must be one of configured "
                f"actions: {available_actions}"
            )

    _validate_chat_stage_actions(chat, actions)

    behavior = BehaviorConfig(
        default_action=default_action,
        randomize_gif_on_loop=coerce_bool(
            behavior_block.get("randomize_gif_on_loop"), True
        ),
        transition_duration_ms=coerce_int(
            behavior_block.get("transition_duration_ms"),
            150,
            min_value=0,
            max_value=10000,
        ),
        idle_actions=load_idle_actions(behavior_block.get("idle_actions"), actions),
    )

    return PetConfig(
        source_path=source_path,
        window=window,
        audio=audio,
        sound=sound,
        behavior=behavior,
        chat=chat,
        actions=actions,
    )


def _resolve_memory_path(value: object, base_dir: Path) -> Path:
    if not isinstance(value, str) or not value.strip():
        return (base_dir / "memory" / "chat_memory.json").resolve()
    path = Path(value.strip())
    if not path.is_absolute():
        path = base_dir / path
    return path.resolve()


def _load_actions(
    actions_block: dict[str, object],
    base_dir: Path,
    default_action: str,
) -> dict[str, ActionConfig]:
    actions: dict[str, ActionConfig] = {}
    for action_name, raw_action in actions_block.items():
        if not isinstance(action_name, str) or not action_name.strip():
            raise ConfigError("Action name must be a non-empty string.")
        action_name = action_name.strip()
        if not isinstance(raw_action, dict):
            raise ConfigError(f"Action '{action_name}' must be a JSON object.")

        play_sound_on_enter = coerce_bool(
            raw_action.get("play_sound_on_enter"), False
        )
        return_to = coerce_text(raw_action.get("return_to"), default_action)

        actions[action_name] = ActionConfig(
            name=action_name,
            gifs=coerce_path_list(
                raw_action.get("gifs"), base_dir, f"actions.{action_name}.gifs"
            ),
            sounds=resolve_soundpak_paths(raw_action.get("sounds"), base_dir),
            auto_return_ms=coerce_int(
                raw_action.get("auto_return_ms"), 0, min_value=0
            ),
            return_to=return_to,
            play_sound_on_enter=play_sound_on_enter,
            offset_x=coerce_int(raw_action.get("offset_x"), 0),
            offset_y=coerce_int(raw_action.get("offset_y"), 0),
            transition_duration_ms=(
                coerce_int(
                    raw_action.get("transition_duration_ms"),
                    0,
                    min_value=0,
                    max_value=10000,
                )
                if "transition_duration_ms" in raw_action
                else None
            ),
            flip_horizontal=coerce_bool(raw_action.get("flip_horizontal"), False),
        )

    return actions


def _load_chat_stage(
    value: object,
    base_dir: Path,
    *,
    default_action: str,
    default_play_sound: bool,
) -> ChatStageConfig:
    if not isinstance(value, dict):
        value = {}

    return ChatStageConfig(
        action=coerce_optional_text(value.get("action"), default_action),
        duration_ms=coerce_int(value.get("duration_ms"), 0, min_value=0),
        play_sound=coerce_bool(value.get("play_sound"), default_play_sound),
        sounds=resolve_soundpak_paths(value.get("sounds"), base_dir),
        transition_duration_ms=coerce_int(
            value.get("transition_duration_ms"),
            DEFAULT_CHAT_STAGE_TRANSITION_MS,
            min_value=0,
            max_value=10000,
        ),
    )


def _validate_chat_stage_actions(
    chat: ChatConfig,
    actions: dict[str, ActionConfig],
) -> None:
    available_actions = ", ".join(actions.keys())
    stages = {
        "input": chat.input_stage,
        "waiting": chat.waiting_stage,
        "reply": chat.reply_stage,
        "error": chat.error_stage,
    }
    for stage_name, stage in stages.items():
        if stage.action and stage.action not in actions:
            raise ConfigError(
                f"Chat stage '{stage_name}' action must be one of configured "
                f"actions: {available_actions}"
            )
