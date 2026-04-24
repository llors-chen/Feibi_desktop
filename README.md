# Feibi Pet

`feibi-pet` is a small desktop-pet framework modeled after the transparent window / GIF playback design used in `ameath`, but trimmed down to three configurable actions only:

- `idle`
- `eating`
- `speaking`

The framework reads GIF and audio resources from `pet_config.json`, supports multiple GIF files per action, and plays a configurable sound effect when entering the `speaking` state.

## Features

- Transparent, borderless, always-on-top desktop pet window
- JSON-driven resource configuration
- Configurable AI chat with OpenAI-compatible `api_key`, `model`, and `base_url`
- Skill-based system prompts loaded from `skills/*.txt`
- Multiple GIFs per action, with random switching on each loop
- Left mouse drag to move the pet
- Right click menu to chat, switch actions, reload config, or exit
- `speaking` action can play one or more configured sound files

## Project Layout

```text
feibi-pet/
├─ assets/
│  ├─ gifs/
│  └─ sounds/
├─ feibi_pet/
│  ├─ app.py
│  ├─ animation.py
│  ├─ audio.py
│  ├─ chat_client.py
│  ├─ chat_ui.py
│  ├─ config_actions.py
│  ├─ config_api.py
│  ├─ config_audio.py
│  ├─ config_defaults.py
│  ├─ config_loader.py
│  ├─ config_models.py
│  ├─ config_utils.py
│  ├─ config_window.py
│  ├─ config.py
│  ├─ pet.py
│  └─ windowing.py
├─ skills/
│  └─ phoebe.txt
├─ main.py
├─ pet_config.json
└─ README.md
```

`config.py` is kept as the compatibility import surface. The actual config pieces
live in focused modules: actions in `config_actions.py`, sound/audio in
`config_audio.py`, API chat in `config_api.py`, window settings in
`config_window.py`, defaults in `config_defaults.py`, and JSON loading/validation
in `config_loader.py`.

## Run

Install dependencies:

```powershell
pip install -r requirements.txt
```

Start the pet:

```powershell
python main.py
```

Use another config file if needed:

```powershell
python main.py --config .\my-pet.json
```

## Configure GIFs And Sound

Edit `pet_config.json`. Paths are resolved relative to that file.

Example:

```json
{
  "window": {
    "title": "Feibi Pet",
    "transparent_color": "#00FF00",
    "stay_on_top": true,
    "alpha": 1.0,
    "scale": 2.0,
    "scale_mode": "nearest",
    "draggable": true,
    "click_through": false,
    "initial_position": { "anchor": "bottom_right", "x": 20, "y": 20 }
  },
  "audio": {
    "enabled": true,
    "volume_percent": 85
  },
  "behavior": {
    "default_action": "idle",
    "randomize_gif_on_loop": true
  },
  "chat": {
    "enabled": false,
    "api_key": "your-api-key",
    "model": "ep-20260325142137-jxd6t",
    "base_url": "https://ark.cn-beijing.volces.com/api/v3",
    "timeout_seconds": 30,
    "max_history": 6,
    "skill": "phoebe",
    "skills_dir": "skills",
    "system_prompt": "",
    "bubble_max_width": 320,
    "bubble_auto_hide_ms": 15000
  },
  "actions": {
    "idle": {
      "gifs": ["assets/gifs/idle-a.gif", "assets/gifs/idle-b.gif"]
    },
    "eating": {
      "gifs": ["assets/gifs/eating-a.gif"],
      "auto_return_ms": 2800,
      "return_to": "idle"
    },
    "speaking": {
      "gifs": ["assets/gifs/speaking-a.gif", "assets/gifs/speaking-b.gif"],
      "sounds": ["assets/sounds/speaking.wav"],
      "auto_return_ms": 2600,
      "return_to": "idle",
      "play_sound_on_enter": true
    }
  }
}
```

## Notes

- Actions are loaded from `actions` in `pet_config.json`. To add a new GIF/APNG action, add a new key under `actions`, point `gifs` at one or more image files, then reference that action from `behavior.idle_actions`, `chat.stages.*.action`, or the right-click menu.
- `behavior.default_action` chooses the standby action. It does not have to be named `idle` as long as it exists in `actions`.
- `window.initial_position.anchor` supports `top_left`, `top_right`, `bottom_left`, and `bottom_right`. Hyphenated values like `bottom-right` also work.
- `window.initial_position.x` and `window.initial_position.y` are offsets from the selected anchor, so `bottom_right` with `20, 20` means "20px from the right and 20px from the bottom".
- Action sound playback is configured per action with `sounds` and `play_sound_on_enter`.
- `behavior.transition_duration_ms` controls the default fade transition duration for normal action changes, including randomized idle actions and returning to idle.
- `actions.<name>.transition_duration_ms` overrides the default transition duration when entering that action. This is useful for actions with very different frame sizes or aspect ratios, such as `sleep`.
- The chat feature uses an OpenAI-compatible API client. Fill `chat.api_key`, `chat.model`, and `chat.base_url`, then set `chat.enabled` to `true`.
- `chat.stages.input`, `chat.stages.waiting`, `chat.stages.reply`, and `chat.stages.error` control the pet animation and sounds for opening the input box, waiting for the API, receiving a reply, and handling an error. Each stage supports `action`, `duration_ms`, `play_sound`, `sounds`, and `transition_duration_ms`.
- System prompts can be stored in `skills/*.txt` and selected with `chat.skill`. The sample [skills/phoebe.txt](/E:/AI/菲比主教桌面宠物-像素画/feibi-pet/skills/phoebe.txt) is based on the `chat.py` prompt idea.
- Right click the pet and choose `Chat` to open the rounded input panel. The reply bubble is also rounded and auto-grows with content length.
- If you want the sound to finish naturally, set `auto_return_ms` to roughly match the audio length, or set it to `0` and switch back manually.
- Pet images should provide their own alpha channel. Because Tk uses color-key window transparency here, the loader keeps the alpha-defined shape but renders visible pixels as fully opaque to avoid green fringes.
- The sample assets in `assets/` are only placeholders copied from the local `ameath` project so the framework can run immediately.
