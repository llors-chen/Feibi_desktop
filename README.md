# Feibi Pet 桌面宠物

`Feibi Pet` 是一个可配置的桌面宠物程序。它会读取 `pet_config.json` 中的配置，显示透明无边框桌宠窗口，播放 GIF/PNG 动作和音效，并支持基于大模型 API 的简单对话功能。

当前项目主要面向中文用户，常用操作包括：

- 显示桌面宠物
- 拖动宠物位置
- 右键打开菜单
- 切换动作
- 打开聊天输入框
- 重新加载配置
- 修改角色提示词

## 功能说明

- 透明、无边框、可置顶的桌面宠物窗口
- 通过 `pet_config.json` 配置窗口、动作、声音、聊天等功能
- 每个动作可以配置一个或多个 GIF/PNG 图片
- 支持动作随机播放和动作切换过渡
- 支持进入动作时播放音效
- 支持 OpenAI 兼容格式的大模型聊天接口
- 支持从 `skills/*.txt` 加载角色提示词
- 支持长期记忆，记忆文件默认保存在 `memory/chat_memory.json`
- 右键菜单支持聊天、切换动作、重新加载配置和退出

## 目录结构

```text
Feibi_desktop/
├─ assets/
│  ├─ gifs/             桌宠动作图片
│  └─ sounds/           音效文件
├─ feibi_pet/           程序源码
│  ├─ chat_client.py    聊天 API 调用
│  ├─ chat_memory.py    长期记忆
│  ├─ chat_ui.py        聊天输入框和回复气泡
│  ├─ config_loader.py  配置读取和校验
│  ├─ pet.py            桌宠主逻辑
│  └─ ...
├─ memory/              聊天记忆文件
├─ skills/
│  └─ phoebe.txt        菲比角色提示词
├─ main.py              启动入口
├─ pet_config.json      主配置文件
└─ README.md            使用说明
```

## 运行程序

先安装依赖：

```powershell
pip install -r requirements.txt
```

启动桌宠：

```powershell
python main.py
```

如果需要使用另一份配置文件：

```powershell
python main.py --config .\my-pet.json
```

## window：窗口配置

```json
"window": {
  "title": "Feibi Pet",
  "stay_on_top": true,
  "draggable": true,
  "click_through": false,
  "transparent_color": "#00FF00",
  "alpha": 1.0,
  "scale": 0.5,
  "scale_mode": "nearest",
  "initial_position": {
    "anchor": "bottom_right",
    "x": 20,
    "y": 20
  }
}
```

- `title`：窗口标题。
- `stay_on_top`：是否置顶显示。
- `draggable`：是否允许鼠标左键拖动。
- `click_through`：是否鼠标穿透。开启后可能不方便右键操作。
- `transparent_color`：透明色。默认绿色用于窗口透明处理。
- `alpha`：窗口整体透明度，`1.0` 为不透明。
- `scale`：桌宠缩放比例。
- `scale_mode`：缩放算法，像素风推荐使用 `nearest`。
- `initial_position.anchor`：初始位置锚点，可选 `top_left`、`top_right`、`bottom_left`、`bottom_right`。
- `initial_position.x` / `y`：相对锚点的偏移距离。

## audio：总音频配置

```json
"audio": {
  "enabled": true,
  "volume_percent": 50
}
```

- `enabled`：是否启用音频。
- `volume_percent`：总音量百分比。

## sound：循环音效配置

```json
"sound": {
  "enabled": true,
  "volume_percent": 50,
  "speaking_intro": {
    "loop_pause_seconds": 0,
    "sounds": [
      "assets/sounds/soundpak0",
      "assets/sounds/soundpak1"
    ]
  },
  "chat_loop": {
    "loop_pause_seconds": 3.0,
    "sounds": [
      "assets/sounds/soundpak2"
    ]
  }
}
```

- `enabled`：是否启用音效包播放。
- `volume_percent`：音效音量百分比。
- `speaking_intro`：进入说话状态时可播放的音效包。
- `chat_loop`：等待模型回复时循环播放的音效包。
- `loop_pause_seconds`：循环播放之间的间隔秒数。
- `sounds`：音效文件或音效文件夹路径列表。

## behavior：待机行为配置

```json
"behavior": {
  "default_action": "idle",
  "randomize_gif_on_loop": true,
  "transition_duration_ms": 800,
  "idle_actions": [
    {
      "action": "idle",
      "weight": 20,
      "duration_ms": 4800
    }
  ]
}
```

- `default_action`：默认动作名称，必须存在于 `actions` 中。
- `randomize_gif_on_loop`：同一个动作有多个图片时，是否循环时随机切换。
- `transition_duration_ms`：普通动作切换时的默认过渡时间，单位毫秒。
- `idle_actions`：待机时可随机触发的动作列表。
- `idle_actions[].action`：要触发的动作名称。
- `idle_actions[].weight`：权重，越大越容易出现。
- `idle_actions[].duration_ms`：动作持续时间。`0` 表示不自动按这个时间返回。

## chat：聊天配置

```json
"chat": {
  "enabled": true,
  "api_key": "your-api-key",
  "model": "your-model",
  "base_url": "https://example.com/v1",
  "timeout_seconds": 30,
  "max_history": 6,
  "memory": {
    "enabled": true,
    "path": "memory/chat_memory.json",
    "max_bytes": 1024000,
    "recent_turns_after_compress": 10,
    "retrieval_limit": 5
  },
  "skill": "phoebe",
  "skills_dir": "skills",
  "system_prompt": "",
  "bubble_max_width": 260,
  "bubble_auto_hide_ms": 8000
}
```

- `enabled`：是否启用聊天功能。
- `api_key`：大模型 API Key。
- `model`：模型名称。
- `base_url`：API 地址。当前代码使用 OpenAI 兼容的 `chat.completions` 格式。
- `timeout_seconds`：接口超时时间，单位秒。
- `max_history`：每次请求带上的最近对话轮数。
- `skill`：角色提示词名称，例如 `phoebe` 对应 `skills/phoebe.txt`。
- `skills_dir`：角色提示词目录。
- `system_prompt`：额外追加的系统提示词。通常留空即可。
- `bubble_max_width`：回复气泡最大宽度。
- `bubble_auto_hide_ms`：回复气泡自动隐藏时间，单位毫秒。

聊天接口说明：

- 当前聊天调用使用 OpenAI 兼容格式。
- 如果服务商提供 `/v1/chat/completions` 或 OpenAI-compatible 接口，通常只需要修改 `api_key`、`model`、`base_url`。
- Claude、Gemini 等原生 API 格式不完全一致，不能只改配置，需要额外适配代码。

## chat.memory：长期记忆配置

```json
"memory": {
  "enabled": true,
  "path": "memory/chat_memory.json",
  "max_bytes": 1024000,
  "recent_turns_after_compress": 10,
  "retrieval_limit": 5
}
```

- `enabled`：是否启用长期记忆。
- `path`：记忆文件保存路径。
- `max_bytes`：记忆文件最大体积。超过后会压缩旧记忆。
- `recent_turns_after_compress`：压缩后保留的最近对话轮数。
- `retrieval_limit`：每次对话最多检索几条相关记忆。

## chat.stages：聊天阶段动作

```json
"stages": {
  "input": {
    "action": "push",
    "duration_ms": 0,
    "transition_duration_ms": 1000,
    "play_sound": true,
    "sounds": []
  },
  "waiting": {
    "action": "eating",
    "duration_ms": 0,
    "transition_duration_ms": 1000,
    "play_sound": false,
    "sounds": []
  },
  "reply": {
    "action": "speaking",
    "duration_ms": 8000,
    "transition_duration_ms": 1000,
    "play_sound": true,
    "sounds": [
      "assets/sounds/soundpak2"
    ]
  },
  "error": {
    "action": "idle",
    "duration_ms": 0,
    "transition_duration_ms": 1000,
    "play_sound": false,
    "sounds": []
  }
}
```

- `input`：打开输入框时的动作。
- `waiting`：等待模型回复时的动作。
- `reply`：模型回复成功后的动作。
- `error`：模型回复失败后的动作。
- `action`：阶段对应的动作名称，必须存在于 `actions` 中。
- `duration_ms`：阶段持续时间，单位毫秒。
- `transition_duration_ms`：切换到该阶段动作的过渡时间。
- `play_sound`：是否播放该阶段配置的声音。
- `sounds`：该阶段播放的声音列表。为空时不额外播放。

## actions：动作配置

```json
"actions": {
  "idle": {
    "gifs": [
      "assets/gifs/idle.gif"
    ],
    "sounds": [],
    "play_sound_on_enter": false,
    "auto_return_ms": 0,
    "return_to": "idle",
    "transition_duration_ms": 800,
    "offset_x": 0,
    "offset_y": 0,
    "flip_horizontal": false
  }
}
```

`actions` 下面的每个键都是一个动作名称，例如 `idle`、`push`、`eating`、`speaking`、`sleep`。

- `gifs`：动作图片列表，支持 GIF、PNG 等可加载图片。
- `sounds`：动作音效列表。
- `play_sound_on_enter`：进入该动作时是否播放 `sounds`。
- `auto_return_ms`：进入该动作后多久自动返回，单位毫秒。`0` 表示不自动返回。
- `return_to`：自动返回时切换到哪个动作。
- `transition_duration_ms`：进入该动作时的过渡时间。不填则使用全局默认值。
- `offset_x` / `offset_y`：动作图片显示偏移，用于不同图片尺寸对齐。
- `flip_horizontal`：是否水平翻转图片。

新增动作时，需要：

1. 在 `actions` 中新增动作配置。
2. 确认 `gifs` 指向的图片文件存在。
3. 如果要待机随机触发，把动作名加入 `behavior.idle_actions`。
4. 如果要用于聊天阶段，把动作名填入 `chat.stages.*.action`。

## 角色提示词

角色提示词放在 `skills` 目录中。例如：

```text
skills/phoebe.txt
```

如果配置中写：

```json
"skill": "phoebe",
"skills_dir": "skills"
```

程序会读取：

```text
skills/phoebe.txt
```

修改角色性格、说话风格、记忆规则时，优先修改这个文件。重启程序。

## 常见问题

### 修改配置后没有生效

请重启程序。

### 聊天无法使用

请检查：

- `chat.enabled` 是否为 `true`
- `chat.api_key` 是否填写
- `chat.model` 是否填写正确
- `chat.base_url` 是否为 OpenAI 兼容接口地址
- 网络是否能访问该接口
- 暴露的api是垃圾口，是不是会出错，建议更换为自己的

### 图片不显示或报错

请检查：

- `actions.<动作名>.gifs` 中的路径是否正确
- 图片文件是否真的存在
- 路径是否相对于 `pet_config.json`

### 音效不播放

请检查：

- `audio.enabled` 是否为 `true`
- `sound.enabled` 是否为 `true`
- `volume_percent` 是否太低
- 音效路径是否正确
- 对应动作或聊天阶段的 `play_sound` 是否开启
