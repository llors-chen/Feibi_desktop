# Feibi Pet 桌面宠物

当前打包版本：`FeibiPet_v0.0.1.zip`

这是一个 Windows 桌面宠物程序。当前发布包已经打包好运行环境，解压后直接运行 `FeibiPet.exe` 即可，不需要先安装 Python 或依赖。

## 快速开始

1. 下载或找到 `FeibiPet_v0.0.1.zip`。
2. 解压整个压缩包。
3. 进入解压后的 `FeibiPet` 文件夹。
4. 双击 `FeibiPet.exe` 启动桌宠。

启动后：

- 左键拖动菲比可以移动位置。
- 右键菲比可以打开菜单。
- 菜单里可以聊天、切换动作、退出程序。
- 修改 `pet_config.json`、`skills/phoebe.txt` 或资源文件后，重启程序生效。

## 当前发布包内容

以当前 `dist/FeibiPet` 为准，发布包主要包含：

```text
FeibiPet/
├─ FeibiPet.exe             程序入口，双击启动
├─ pet_config.json          桌宠配置文件
├─ assets/
│  ├─ gifs/                 动作图片
│  ├─ images/
│  └─ sounds/
├─ skills/
│  └─ phoebe.txt            菲比角色提示词
├─ memory/
│  └─ chat_memory.json      聊天长期记忆
└─ _internal/               打包运行库，请不要删除
```

注意：`_internal` 是 PyInstaller 打包出来的运行库目录，`FeibiPet.exe` 依赖它。移动程序时请移动整个 `FeibiPet` 文件夹，不要只移动 exe。

## 功能

- 透明、无边框、置顶显示的桌宠窗口
- 支持拖动位置
- 支持右键菜单
- 支持待机随机动作
- 支持 `idle`、`push`、`eating`、`speaking`、`sleep` 五个动作
- 支持 GIF/PNG 动作资源
- 支持动作切换过渡、偏移和水平翻转
- 支持音效包播放
- 支持 OpenAI 兼容格式的大模型聊天接口
- 支持 `skills/phoebe.txt` 角色提示词
- 支持长期记忆，默认保存在 `memory/chat_memory.json`

## 右键菜单

当前程序右键菜单包含：

- `聊天`：打开聊天输入框
- `待机` / `推` / `吃` / `说话` / `睡觉`：切换到对应动作
- `退出`：关闭程序

## 配置文件

发布包内的主配置文件是：

```text
pet_config.json
```

所有路径都按 `pet_config.json` 所在目录解析。也就是说，在发布包里写：

```json
"assets/gifs/idle.gif"
```

实际对应：

```text
FeibiPet/assets/gifs/idle.gif
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

- `stay_on_top`：是否置顶。
- `draggable`：是否允许左键拖动。
- `click_through`：是否鼠标穿透。开启后可能不方便右键操作。
- `transparent_color`：透明色，当前用于窗口透明处理。
- `alpha`：窗口整体透明度，`1.0` 为不透明。
- `scale`：桌宠缩放比例。
- `scale_mode`：缩放算法，像素风推荐 `nearest`。
- `initial_position.anchor`：初始位置锚点，可选 `top_left`、`top_right`、`bottom_left`、`bottom_right`。
- `initial_position.x` / `y`：相对锚点的偏移距离。

## behavior：待机行为

当前发布包默认待机动作池：

```json
"idle_actions": [
  { "action": "idle", "weight": 20, "duration_ms": 4800 },
  { "action": "speaking", "weight": 1, "duration_ms": 5000 },
  { "action": "eating", "weight": 1, "duration_ms": 0 },
  { "action": "sleep", "weight": 1, "duration_ms": 0 },
  { "action": "push", "weight": 1, "duration_ms": 0 }
]
```

- `default_action`：默认动作，当前是 `idle`。
- `randomize_gif_on_loop`：同一个动作有多个图片时，循环时是否随机切换。
- `transition_duration_ms`：默认动作切换过渡时间，单位毫秒。
- `weight`：权重越大，越容易被随机选中。
- `duration_ms`：动作持续时间。`0` 表示按程序逻辑返回默认动作。

## actions：动作配置

当前发布包配置了五个动作：

| 动作名 | 菜单显示 | 当前资源 |
| --- | --- | --- |
| `idle` | 待机 | `assets/gifs/idle.gif` |
| `push` | 推 | `assets/gifs/push.gif` |
| `eating` | 吃 | `assets/gifs/eating.png` |
| `speaking` | 说话 | `assets/gifs/talk.gif` |
| `sleep` | 睡觉 | `assets/gifs/sleep.gif` |

单个动作示例：

```json
"speaking": {
  "gifs": ["assets/gifs/talk.gif"],
  "sounds": [
    "assets/sounds/soundpak0",
    "assets/sounds/soundpak1"
  ],
  "play_sound_on_enter": true,
  "auto_return_ms": 0,
  "return_to": "idle",
  "transition_duration_ms": 1000,
  "offset_x": 0,
  "offset_y": 0,
  "flip_horizontal": false
}
```

- `gifs`：动作图片列表，支持 GIF、PNG 等图片。
- `sounds`：动作音效列表，可以写单个音频文件，也可以写音效文件夹。
- `play_sound_on_enter`：进入该动作时是否播放音效。
- `auto_return_ms`：从右键菜单触发该动作后多久自动返回，`0` 表示不按这个字段自动返回。
- `return_to`：自动返回目标动作。
- `transition_duration_ms`：进入该动作时的过渡时间。
- `offset_x` / `offset_y`：图片偏移，用于不同动作尺寸对齐。
- `flip_horizontal`：是否水平翻转图片。

新增动作时，需要同时做这些事：

1. 把图片或音效放进 `assets`。
2. 在 `pet_config.json` 的 `actions` 里新增动作。
3. 如果要让它待机随机出现，把动作加入 `behavior.idle_actions`。
4. 如果要让它出现在聊天阶段，把动作填入 `chat.stages`。

## audio / sound：声音配置

总音频开关：

```json
"audio": {
  "enabled": true,
  "volume_percent": 50
}
```

音效包配置：

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

- `audio.enabled`：总音频开关。
- `audio.volume_percent`：总音量。
- `sound.enabled`：音效包开关。
- `sound.volume_percent`：音效包音量。
- `speaking_intro`：说话动作相关音效包。
- `chat_loop`：等待模型回复时循环播放的音效包。
- `loop_pause_seconds`：循环播放间隔。
- `sounds`：音频文件或文件夹路径列表。

## chat：聊天配置

当前发布包开启了聊天功能，并使用 OpenAI 兼容接口：

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

- `enabled`：是否启用聊天。
- `api_key`：大模型 API Key。建议换成你自己的 Key。
- `model`：模型名称。
- `base_url`：OpenAI 兼容接口地址。
- `timeout_seconds`：请求超时时间。
- `max_history`：每次请求携带的最近对话轮数。
- `skill`：角色提示词名称，`phoebe` 对应 `skills/phoebe.txt`。
- `skills_dir`：角色提示词目录。
- `system_prompt`：额外系统提示词。
- `bubble_max_width`：回复气泡最大宽度。
- `bubble_auto_hide_ms`：回复气泡自动隐藏时间，单位毫秒。

聊天接口需要兼容 `/v1/chat/completions`。如果服务商写着 OpenAI-compatible，通常修改 `api_key`、`model`、`base_url` 即可；Claude、Gemini 等原生接口不能只靠改配置直接接入。

## chat.stages：聊天阶段动作

当前发布包聊天阶段：

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

- `input`：打开输入框时。
- `waiting`：等待模型回复时。
- `reply`：模型回复成功后。
- `error`：模型回复失败后。
- `action`：阶段对应动作，必须存在于 `actions`。
- `duration_ms`：阶段持续时间。
- `transition_duration_ms`：切换到该阶段动作的过渡时间。
- `play_sound`：是否播放该阶段声音。
- `sounds`：阶段额外声音列表。为空时使用动作自身声音或不播放。

## 角色提示词和记忆

角色提示词：

```text
skills/phoebe.txt
```

修改菲比的人设、语气和行为规则时，改这个文件。修改后重启程序。

长期记忆：

```text
memory/chat_memory.json
```

如果想清空记忆，可以关闭程序后清空这个文件内容，或替换成空 JSON 结构。

## 开发运行

如果你要从源码运行，而不是使用发布包：

```powershell
pip install -r requirements.txt
python main.py
```

使用自定义配置：

```powershell
python main.py --config .\my-pet.json
```

重新打包：

```powershell
pyinstaller feibi_pet.spec --clean --noconfirm
```

打包结果会生成在：

```text
dist/FeibiPet/
```

## 常见问题

### 双击 exe 没反应

请确认是从完整的 `FeibiPet` 文件夹里启动，不要只拿出 `FeibiPet.exe`。`_internal`、`assets`、`skills`、`pet_config.json` 都需要保留在同一层目录。

### 修改配置后没有生效

请重启程序。

### 聊天无法使用

请检查：

- `chat.enabled` 是否为 `true`
- `chat.api_key` 是否有效
- `chat.model` 是否填写正确
- `chat.base_url` 是否是 OpenAI 兼容接口地址
- 网络是否能访问该接口
- 默认示例接口或 Key 可能不可用，建议换成自己的服务配置

### 图片不显示或报错

请检查：

- `actions.<动作名>.gifs` 中的路径是否正确
- 图片文件是否存在于发布包内
- 路径是否相对于 `pet_config.json`

### 音效不播放

请检查：

- `audio.enabled` 是否为 `true`
- `sound.enabled` 是否为 `true`
- `volume_percent` 是否太低
- 音效路径是否正确
- 对应动作或聊天阶段的 `play_sound` 是否开启
