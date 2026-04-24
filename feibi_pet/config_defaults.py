from __future__ import annotations

from typing import Any

POSITION_ANCHORS = ("top_left", "top_right", "bottom_left", "bottom_right")

DEFAULT_CONFIG: dict[str, Any] = {
    "window": {
        "title": "Feibi Pet",
        "transparent_color": "#00FF00",
        "stay_on_top": True,
        "alpha": 1.0,
        "scale": 2.0,
        "scale_mode": "nearest",
        "draggable": True,
        "click_through": False,
        "initial_position": {"anchor": "top_left", "x": 120, "y": 120},
    },
    "audio": {
        "enabled": True,
        "volume_percent": 85,
    },
    "sound": {
        "enabled": True,
        "volume_percent": 85,
        "speaking_intro": {
            "sounds": ["assets/sounds/soundpak0", "assets/sounds/soundpak1"],
            "loop_pause_seconds": 0,
        },
        "chat_loop": {
            "sounds": ["assets/sounds/soundpak2"],
            "loop_pause_seconds": 2.0,
        },
    },
    "behavior": {
        "default_action": "idle",
        "randomize_gif_on_loop": True,
        "transition_duration_ms": 150,
        "idle_actions": [
            {"action": "idle", "weight": 8, "duration_ms": 0},
            {"action": "speaking", "weight": 1, "duration_ms": 5000},
            {"action": "eating", "weight": 1, "duration_ms": 10000},
            {"action": "sleep", "weight": 1, "duration_ms": 8300},
            {"action": "push", "weight": 1, "duration_ms": 9550},
        ],
    },
    "chat": {
        "enabled": False,
        "api_key": "",
        "model": "",
        "base_url": "https://ark.cn-beijing.volces.com/api/v3",
        "timeout_seconds": 30,
        "max_history": 6,
        "skill": "phoebe",
        "skills_dir": "skills",
        "system_prompt": "",
        "bubble_max_width": 320,
        "bubble_auto_hide_ms": 15000,
        "stages": {
            "input": {
                "action": "",
                "duration_ms": 0,
                "play_sound": True,
                "sounds": [],
                "transition_duration_ms": 1000,
            },
            "waiting": {
                "action": "",
                "duration_ms": 0,
                "play_sound": False,
                "sounds": [],
                "transition_duration_ms": 1000,
            },
            "reply": {
                "action": "",
                "duration_ms": 0,
                "play_sound": True,
                "sounds": ["assets/sounds/soundpak2"],
                "transition_duration_ms": 1000,
            },
            "error": {
                "action": "",
                "duration_ms": 0,
                "play_sound": False,
                "sounds": [],
                "transition_duration_ms": 1000,
            },
        },
    },
    "actions": {
        "idle": {
            "gifs": ["assets/gifs/idle-a.gif", "assets/gifs/idle-b.gif"],
            "transition_duration_ms": 150,
        },
        "eating": {
            "gifs": ["assets/gifs/eating-a.gif"],
            "auto_return_ms": 2800,
            "return_to": "idle",
            "transition_duration_ms": 150,
            "flip_horizontal": False,
        },
        "speaking": {
            "gifs": ["assets/gifs/speaking-a.gif", "assets/gifs/speaking-b.gif"],
            "sounds": ["assets/sounds/speaking.wav"],
            "auto_return_ms": 2600,
            "return_to": "idle",
            "play_sound_on_enter": True,
            "transition_duration_ms": 150,
            "flip_horizontal": False,
        },
    },
}
