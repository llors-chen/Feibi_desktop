from __future__ import annotations

import ctypes
from pathlib import Path
import random
import threading
import time
import tkinter as tk
from tkinter import messagebox

from .animation import GifSequence, load_gif_sequence
from .audio import AudioPlayer
from .chat_client import ChatClient, ChatError
from .chat_ui import ChatInputDialog, RoundedBubbleWindow
from .config import ChatStageConfig, ConfigError, PetConfig, load_config
from .windowing import (
    GWL_EXSTYLE,
    RECT,
    SPI_GETWORKAREA,
    WS_EX_LAYERED,
    WS_EX_TRANSPARENT,
    resolve_anchor_offsets,
    resolve_anchored_coordinates,
)

IDLE_FADE_DURATION_MS = 180
IDLE_FADE_STEPS = 9
IDLE_FADE_START_RATIO = 0.65
DEFAULT_TRANSITION_FADE_DURATION_MS = 150
TRANSITION_FADE_STEPS = 6
CHAT_TRANSITION_DURATION_MS = 1000


class DesktopPet:
    def __init__(self, root: tk.Tk, config_path: Path) -> None:
        self.root = root
        self.config_path = Path(config_path).resolve()
        self.audio_player = AudioPlayer()

        self.label = tk.Label(root, bd=0, highlightthickness=0)
        self.label.pack()

        self.current_action = ""
        self.current_sequence: GifSequence | None = None
        self.action_sequences: dict[str, list[GifSequence]] = {}
        self.config: PetConfig | None = None
        self.chat_client: ChatClient | None = None
        self.chat_history: list[dict[str, str]] = []
        self.chat_request_inflight = False
        self.chat_restore_action: str | None = None

        self.frame_index = 0
        self.animation_job: str | None = None
        self.return_job: str | None = None
        self.chat_restore_job: str | None = None
        self.idle_fade_job: str | None = None
        self.idle_action_start_time: float = 0
        self.idle_action_duration_ms: int = 0
        self.transition_job: str | None = None

        self.x = 0
        self.y = 0
        self.drag_offset_x = 0
        self.drag_offset_y = 0

        self.response_bubble = RoundedBubbleWindow(root)
        self.chat_dialog = ChatInputDialog(
            root,
            self.submit_chat_prompt,
            on_close=self.on_chat_dialog_close,
        )

        self.label.bind("<ButtonPress-1>", self.on_drag_start)
        self.label.bind("<B1-Motion>", self.on_drag_move)
        self.label.bind("<ButtonRelease-1>", self.on_drag_end)
        self.label.bind("<Button-3>", self.show_context_menu)

        self.root.protocol("WM_DELETE_WINDOW", self.close)
        self.reload_config(initial_load=True)

    def reload_config(self, initial_load: bool = False) -> None:
        previous_action = self.current_action
        config = load_config(self.config_path)
        sequences = {
            name: [
                load_gif_sequence(
                    path,
                    config.window.scale,
                    config.window.scale_mode,
                    flip_horizontal=action.flip_horizontal,
                )
                for path in action.gifs
            ]
            for name, action in config.actions.items()
        }

        self.cancel_animation()
        self.cancel_return_timer()
        self.cancel_idle_fade()

        self.config = config
        self.action_sequences = sequences
        self.chat_client = ChatClient(config.chat)
        self.audio_player.set_enabled(config.audio.enabled)
        self.audio_player.set_volume(config.sound.volume_percent)
        self.chat_history.clear()
        self.chat_request_inflight = False
        self.chat_restore_action = None
        self.cancel_chat_restore()
        self.response_bubble.hide()
        self.chat_dialog.hide()
        del initial_load

        self.apply_window_config()

        target_action = (
            previous_action
            if previous_action in self.action_sequences
            else config.behavior.default_action
        )
        self.set_action(target_action, play_sound=False)
        self.animate()

    def get_default_action(self) -> str:
        if self.config:
            return self.config.behavior.default_action
        return self.current_action

    def is_default_action(self, action_name: str) -> bool:
        return bool(self.config and action_name == self.config.behavior.default_action)

    def apply_window_config(self) -> None:
        assert self.config is not None
        window = self.config.window

        self.root.title(window.title)
        self.root.overrideredirect(True)
        self.root.attributes("-topmost", window.stay_on_top)
        self.set_root_alpha(window.alpha)
        self.root.configure(bg=window.transparent_color)
        self.label.configure(bg=window.transparent_color)

        try:
            self.root.attributes("-transparentcolor", window.transparent_color)
        except tk.TclError:
            pass

        self.root.update_idletasks()
        self.apply_click_through(window.click_through)

    def get_base_alpha(self) -> float:
        if not self.config:
            return 1.0
        return max(0.1, min(1.0, float(self.config.window.alpha)))

    def set_root_alpha(self, alpha: float) -> None:
        clamped = max(0.0, min(1.0, float(alpha)))
        try:
            self.root.attributes("-alpha", clamped)
        except tk.TclError:
            pass

    def cancel_idle_fade(self) -> None:
        if self.idle_fade_job is not None:
            self.root.after_cancel(self.idle_fade_job)
            self.idle_fade_job = None

    def start_idle_fade_transition(self) -> None:
        self.cancel_idle_fade()
        base_alpha = self.get_base_alpha()
        start_alpha = max(0.1, base_alpha * IDLE_FADE_START_RATIO)
        if abs(base_alpha - start_alpha) < 0.01:
            self.set_root_alpha(base_alpha)
            return

        step_delay = max(10, IDLE_FADE_DURATION_MS // IDLE_FADE_STEPS)
        self.set_root_alpha(start_alpha)
        step_index = 0

        def tick() -> None:
            nonlocal step_index
            step_index += 1
            progress = min(1.0, step_index / IDLE_FADE_STEPS)
            alpha = start_alpha + (base_alpha - start_alpha) * progress
            self.set_root_alpha(alpha)
            if progress < 1.0:
                self.idle_fade_job = self.root.after(step_delay, tick)
            else:
                self.idle_fade_job = None

        self.idle_fade_job = self.root.after(step_delay, tick)

    def cancel_transition(self) -> None:
        if self.transition_job is not None:
            self.root.after_cancel(self.transition_job)
            self.transition_job = None

    def get_transition_duration_ms(self) -> int:
        if not self.config:
            return DEFAULT_TRANSITION_FADE_DURATION_MS
        return max(0, int(self.config.behavior.transition_duration_ms))

    def get_action_transition_duration_ms(self, action_name: str) -> int:
        if self.config:
            action_config = self.config.actions.get(action_name)
            if (
                action_config is not None
                and action_config.transition_duration_ms is not None
            ):
                return max(0, int(action_config.transition_duration_ms))
        return self.get_transition_duration_ms()

    def fade_out(self, callback: callable, duration_ms: int | None = None) -> None:
        self.cancel_transition()
        duration_ms = self.get_transition_duration_ms() if duration_ms is None else duration_ms
        base_alpha = self.get_base_alpha()
        step_delay = max(10, duration_ms // TRANSITION_FADE_STEPS)
        step_index = 0

        def tick() -> None:
            nonlocal step_index
            step_index += 1
            progress = min(1.0, step_index / TRANSITION_FADE_STEPS)
            alpha = base_alpha * (1.0 - progress)
            self.set_root_alpha(max(0.0, alpha))
            if progress < 1.0:
                self.transition_job = self.root.after(step_delay, tick)
            else:
                self.transition_job = None
                callback()

        self.transition_job = self.root.after(step_delay, tick)

    def fade_in(self, duration_ms: int | None = None) -> None:
        self.cancel_transition()
        duration_ms = self.get_transition_duration_ms() if duration_ms is None else duration_ms
        base_alpha = self.get_base_alpha()
        step_delay = max(10, duration_ms // TRANSITION_FADE_STEPS)
        step_index = 0

        def tick() -> None:
            nonlocal step_index
            step_index += 1
            progress = min(1.0, step_index / TRANSITION_FADE_STEPS)
            alpha = base_alpha * progress
            self.set_root_alpha(max(0.0, alpha))
            if progress < 1.0:
                self.transition_job = self.root.after(step_delay, tick)
            else:
                self.transition_job = None

        self.transition_job = self.root.after(step_delay, tick)

    def transition_to_action(
        self,
        action_name: str,
        duration_ms: int = 0,
        *,
        play_sound: bool = True,
        transition_duration_ms: int | None = None,
    ) -> None:
        if transition_duration_ms is None:
            transition_duration_ms = self.get_action_transition_duration_ms(action_name)
        half_duration_ms = max(10, transition_duration_ms // 2)

        def do_switch() -> None:
            self._set_action_internal(action_name, play_sound=play_sound)
            self.idle_action_start_time = time.time() * 1000
            self.idle_action_duration_ms = duration_ms
            self.fade_in(half_duration_ms)

        self.fade_out(do_switch, half_duration_ms)

    def _set_action_internal(self, action_name: str, *, play_sound: bool = True) -> None:
        if not self.config or action_name not in self.config.actions:
            raise ConfigError(f"Unknown action: {action_name}")

        previous_action = self.current_action

        previous_action_config = self.config.actions.get(self.current_action)
        if (
            previous_action_config is not None
            and previous_action_config.play_sound_on_enter
            and previous_action_config.sounds
            and action_name != self.current_action
        ):
            self.audio_player.stop()

        self.cancel_return_timer()

        action_config = self.config.actions[action_name]
        self.current_action = action_name
        self.current_sequence = self.pick_sequence(action_name)
        self.frame_index = 0
        self.apply_sequence_geometry()

        if play_sound and action_config.play_sound_on_enter and action_config.sounds:
            self.audio_player.play_random(action_config.sounds)

    def apply_click_through(self, enabled: bool) -> None:
        try:
            hwnd = ctypes.windll.user32.GetParent(self.root.winfo_id())
            style = ctypes.windll.user32.GetWindowLongW(hwnd, GWL_EXSTYLE)
            if enabled:
                new_style = style | WS_EX_LAYERED | WS_EX_TRANSPARENT
            else:
                new_style = style & ~WS_EX_TRANSPARENT
            ctypes.windll.user32.SetWindowLongW(hwnd, GWL_EXSTYLE, new_style)
        except Exception:
            pass

    def get_work_area(self) -> tuple[int, int, int, int]:
        try:
            rect = RECT()
            if ctypes.windll.user32.SystemParametersInfoW(
                SPI_GETWORKAREA,
                0,
                ctypes.byref(rect),
                0,
            ):
                return rect.left, rect.top, rect.right, rect.bottom
        except Exception:
            pass
        return (0, 0, self.root.winfo_screenwidth(), self.root.winfo_screenheight())

    def update_position_from_anchor(self) -> None:
        if not self.config or not self.current_sequence:
            return
        position = self.config.window.initial_position
        self.x, self.y = resolve_anchored_coordinates(
            position.anchor,
            position.x,
            position.y,
            self.current_sequence.width,
            self.current_sequence.height,
            self.get_work_area(),
        )

    def store_position_from_absolute(self, x: int, y: int) -> None:
        self.x = x
        self.y = y
        if not self.config or not self.current_sequence:
            return
        position = self.config.window.initial_position
        position.x, position.y = resolve_anchor_offsets(
            position.anchor,
            x,
            y,
            self.current_sequence.width,
            self.current_sequence.height,
            self.get_work_area(),
        )

    def set_action(
        self,
        action_name: str,
        *,
        play_sound: bool = True,
        use_transition: bool = False,
        duration_ms: int = 0,
        transition_duration_ms: int | None = None,
    ) -> None:
        if use_transition and self.current_action != action_name:
            self.transition_to_action(
                action_name,
                duration_ms,
                play_sound=play_sound,
                transition_duration_ms=transition_duration_ms,
            )
            return

        self._set_action_internal(action_name, play_sound=play_sound)
        self.idle_action_start_time = time.time() * 1000
        self.idle_action_duration_ms = duration_ms
        
        if self.is_default_action(action_name):
            self.start_idle_fade_transition()
        else:
            self.cancel_idle_fade()
            self.set_root_alpha(self.get_base_alpha())

    def pick_sequence(self, action_name: str) -> GifSequence:
        sequences = self.action_sequences[action_name]
        if len(sequences) == 1:
            return sequences[0]
        return random.choice(sequences)

    def apply_sequence_geometry(self) -> None:
        if not self.current_sequence or not self.config:
            return
        self.update_position_from_anchor()
        
        action_config = self.config.actions.get(self.current_action)
        offset_x = action_config.offset_x if action_config else 0
        offset_y = action_config.offset_y if action_config else 0
        
        final_x = self.x + offset_x
        final_y = self.y + offset_y
        
        self.root.geometry(
            f"{self.current_sequence.width}x{self.current_sequence.height}+{final_x}+{final_y}"
        )
        self.update_chat_overlay_positions()

    def animate(self) -> None:
        if not self.current_sequence or not self.config:
            return

        if self.frame_index >= len(self.current_sequence.frames):
            self.frame_index = 0
            self.handle_sequence_loop()
            if not self.current_sequence or not self.config:
                return

        frames = self.current_sequence.frames
        delays = self.current_sequence.delays

        self.label.configure(image=frames[self.frame_index])
        delay = delays[self.frame_index]
        self.frame_index += 1

        self.animation_job = self.root.after(delay, self.animate)

    def handle_sequence_loop(self) -> None:
        if not self.current_sequence or not self.config:
            return

        keep_chat_input_action = (
            self.current_action == self.resolve_chat_stage_action(
                self.config.chat.input_stage
            )
            and self.chat_dialog.is_visible()
        )
        switched_action = False

        default_action = self.get_default_action()

        if self.current_action == default_action and not self.chat_request_inflight:
            next_action, duration_ms = self.pick_idle_cycle_action_with_duration()
            if next_action != self.current_action:
                self.set_action(
                    next_action,
                    play_sound=False,
                    use_transition=True,
                    duration_ms=duration_ms,
                )
                switched_action = True
        elif (
            self.current_action != default_action
            and not self.chat_request_inflight
            and not keep_chat_input_action
        ):
            elapsed = time.time() * 1000 - self.idle_action_start_time
            if self.idle_action_duration_ms == 0 or elapsed >= self.idle_action_duration_ms:
                self.set_action(default_action, play_sound=False, use_transition=True)
                switched_action = True

        if not switched_action and self.config.behavior.randomize_gif_on_loop:
            self.current_sequence = self.pick_sequence(self.current_action)
            self.apply_sequence_geometry()

    def pick_idle_cycle_action_with_duration(self) -> tuple[str, int]:
        if not self.config:
            return self.current_action, 0

        candidates: list[tuple[str, int]] = []
        weights: list[int] = []
        
        for idle_action in self.config.behavior.idle_actions:
            if idle_action.weight <= 0 or idle_action.action not in self.action_sequences:
                continue
            candidates.append((idle_action.action, idle_action.duration_ms))
            weights.append(idle_action.weight)

        if not candidates:
            return self.config.behavior.default_action, 0
        result = random.choices(candidates, weights=weights, k=1)[0]
        return result[0], result[1]

    def pick_idle_cycle_action(self) -> str:
        action, _ = self.pick_idle_cycle_action_with_duration()
        return action

    def cancel_animation(self) -> None:
        if self.animation_job is not None:
            self.root.after_cancel(self.animation_job)
            self.animation_job = None

    def cancel_return_timer(self) -> None:
        if self.return_job is not None:
            self.root.after_cancel(self.return_job)
            self.return_job = None

    def cancel_chat_restore(self) -> None:
        if self.chat_restore_job is not None:
            self.root.after_cancel(self.chat_restore_job)
            self.chat_restore_job = None

    def on_drag_start(self, event: tk.Event) -> None:
        if not self.config or not self.config.window.draggable:
            return
        self.drag_offset_x = event.x_root - self.x
        self.drag_offset_y = event.y_root - self.y

    def on_drag_move(self, event: tk.Event) -> None:
        if not self.config or not self.config.window.draggable:
            return
        self.store_position_from_absolute(
            event.x_root - self.drag_offset_x,
            event.y_root - self.drag_offset_y,
        )
        self.apply_sequence_geometry()

    def on_drag_end(self, event: tk.Event) -> None:
        del event

    def show_context_menu(self, event: tk.Event) -> None:
        if not self.config:
            return
        menu = tk.Menu(self.root, tearoff=0)
        menu.add_command(label="Chat", command=self.open_chat_dialog)
        menu.add_separator()
        for action_name in self.config.actions:
            menu.add_command(
                label=action_name.capitalize(),
                command=lambda name=action_name: self.trigger_menu_action(name),
            )
        menu.add_separator()
        menu.add_command(label="Reload Config", command=self.try_reload_from_menu)
        menu.add_command(label="Exit", command=self.close)

        try:
            menu.tk_popup(event.x_root, event.y_root)
        finally:
            menu.grab_release()

    def trigger_menu_action(self, action_name: str) -> None:
        if not self.config or action_name not in self.action_sequences:
            return
        if self.is_default_action(action_name):
            self.set_action(action_name, use_transition=True)
            return

        action_config = self.config.actions[action_name]
        duration_ms = action_config.auto_return_ms if action_config.auto_return_ms > 0 else 0
        
        self.set_action(
            action_name,
            play_sound=True,
            use_transition=True,
            duration_ms=duration_ms,
        )

    def _start_chat_loop_sound(self) -> None:
        if not self.config or not self.config.sound.enabled:
            return
        sounds = self.config.sound.chat_loop.sounds
        pause_seconds = self.config.sound.chat_loop.loop_pause_seconds
        if sounds:
            self.audio_player.play_loop(sounds, pause_seconds=pause_seconds)

    def _stop_chat_loop_sound(self) -> None:
        self.audio_player.stop_loop()

    def try_reload_from_menu(self) -> None:
        try:
            self.reload_config()
        except Exception as exc:
            messagebox.showerror("Feibi Pet", f"Failed to reload config:\n{exc}")

    def open_chat_dialog(self) -> None:
        if not self.config:
            return
        if not self.config.chat.enabled:
            self.show_chat_feedback(
                "聊天功能未启用，请先在 pet_config.json 中填写 chat 配置。",
                auto_hide_ms=4000,
            )
            return
        if self.chat_request_inflight:
            self.show_chat_feedback("正在等待模型回复，请稍候。", auto_hide_ms=3000)
            return

        self.play_chat_stage(self.config.chat.input_stage)

        anchor_x, anchor_y = self.get_chat_dialog_anchor()
        self.chat_dialog.show(anchor_x, anchor_y)

    def submit_chat_prompt(self, prompt: str) -> None:
        if not self.config or not self.chat_client:
            return
        if self.chat_request_inflight:
            self.show_chat_feedback("当前已有一条对话在处理中。", auto_hide_ms=3000)
            return

        try:
            self.chat_client.ensure_ready()
        except ChatError as exc:
            self.show_chat_feedback(str(exc), auto_hide_ms=5000)
            return

        self.chat_request_inflight = True
        self.play_chat_stage(self.config.chat.waiting_stage)
        self._start_chat_loop_sound()
        self.show_chat_feedback("思考中...", auto_hide_ms=0)

        threading.Thread(
            target=self._request_chat_reply,
            args=(prompt,),
            daemon=True,
        ).start()

    def _request_chat_reply(self, prompt: str) -> None:
        assert self.chat_client is not None
        try:
            reply = self.chat_client.request_reply(self.chat_history, prompt)
        except Exception as exc:
            self.root.after(
                0,
                lambda: self.finish_chat_request(
                    success=False,
                    prompt=prompt,
                    reply=f"对话失败：{exc}",
                ),
            )
            return

        self.root.after(
            0,
            lambda: self.finish_chat_request(
                success=True,
                prompt=prompt,
                reply=reply,
            ),
        )

    def finish_chat_request(self, *, success: bool, prompt: str, reply: str) -> None:
        if not self.config:
            return

        self.chat_request_inflight = False
        if success:
            self.append_chat_history("user", prompt)
            self.append_chat_history("assistant", reply)
            self.play_chat_stage(self.config.chat.reply_stage)
        else:
            self.play_chat_stage(self.config.chat.error_stage)

        auto_hide_ms = self.config.chat.bubble_auto_hide_ms
        self.show_chat_feedback(reply, auto_hide_ms=auto_hide_ms)
        self.schedule_chat_restore(auto_hide_ms)

    def append_chat_history(self, role: str, content: str) -> None:
        if not self.config:
            return
        self.chat_history.append({"role": role, "content": content})
        max_messages = self.config.chat.max_history * 2
        if max_messages <= 0:
            self.chat_history.clear()
            return
        self.chat_history[:] = self.chat_history[-max_messages:]

    def resolve_chat_action_name(self) -> str:
        if self.config:
            return self.config.behavior.default_action
        return self.current_action

    def resolve_chat_stage_action(self, stage: ChatStageConfig) -> str:
        if stage.action and stage.action in self.action_sequences:
            return stage.action
        return self.resolve_chat_action_name()

    def play_chat_stage(self, stage: ChatStageConfig) -> None:
        if not self.config:
            return
        chat_action = self.resolve_chat_stage_action(stage)
        if self.chat_restore_action is None:
            if self.current_action != chat_action:
                self.chat_restore_action = self.current_action
            else:
                self.chat_restore_action = self.config.behavior.default_action

        play_action_sound = stage.play_sound and not stage.sounds
        self.set_action(
            chat_action,
            play_sound=play_action_sound,
            use_transition=True,
            duration_ms=stage.duration_ms,
            transition_duration_ms=stage.transition_duration_ms,
        )
        if stage.sounds:
            self.audio_player.play_random(stage.sounds)
        self.cancel_return_timer()

    def enter_chat_action(self, *, play_sound: bool) -> None:
        if not self.config:
            return
        chat_action = self.resolve_chat_action_name()
        if self.chat_restore_action is None:
            if self.current_action != chat_action:
                self.chat_restore_action = self.current_action
            else:
                self.chat_restore_action = self.config.behavior.default_action

        self.set_action(
            chat_action,
            play_sound=play_sound,
            use_transition=True,
            transition_duration_ms=CHAT_TRANSITION_DURATION_MS,
        )
        self.cancel_return_timer()

    def schedule_chat_restore(self, auto_hide_ms: int) -> None:
        self.cancel_chat_restore()
        delay = auto_hide_ms if auto_hide_ms > 0 else 3500
        self.chat_restore_job = self.root.after(delay, self.restore_action_after_chat)

    def restore_action_after_chat(self) -> None:
        self.cancel_chat_restore()
        self._stop_chat_loop_sound()
        if not self.config:
            return
        target_action = self.chat_restore_action or self.config.behavior.default_action
        self.chat_restore_action = None
        if target_action in self.action_sequences:
            self.set_action(
                target_action,
                play_sound=False,
                use_transition=True,
                transition_duration_ms=CHAT_TRANSITION_DURATION_MS,
            )

    def on_chat_dialog_close(self) -> None:
        if self.chat_request_inflight:
            return
        self.restore_action_after_chat()

    def show_chat_feedback(self, text: str, *, auto_hide_ms: int) -> None:
        if not self.config:
            return
        anchor_x, anchor_y = self.get_response_bubble_anchor()
        self.response_bubble.show(
            text,
            anchor_x,
            anchor_y,
            max_width=self.config.chat.bubble_max_width,
            auto_hide_ms=auto_hide_ms,
        )

    def get_response_bubble_anchor(self) -> tuple[int, int]:
        width = self.current_sequence.width if self.current_sequence else 120
        return self.x + width // 2, self.y

    def get_chat_dialog_anchor(self) -> tuple[int, int]:
        width = self.current_sequence.width if self.current_sequence else 120
        height = self.current_sequence.height if self.current_sequence else 120
        return self.x + width // 2, self.y + height

    def update_chat_overlay_positions(self) -> None:
        bubble_x, bubble_y = self.get_response_bubble_anchor()
        self.response_bubble.reposition(bubble_x, bubble_y)

        dialog_x, dialog_y = self.get_chat_dialog_anchor()
        if self.chat_dialog.is_visible():
            self.chat_dialog.reposition(dialog_x, dialog_y)

    def close(self) -> None:
        self.cancel_animation()
        self.cancel_return_timer()
        self.cancel_chat_restore()
        self.cancel_idle_fade()
        self.cancel_transition()
        self._stop_chat_loop_sound()
        self.response_bubble.destroy()
        self.chat_dialog.destroy()
        self.audio_player.close()
        self.root.quit()
        self.root.destroy()
