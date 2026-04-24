from __future__ import annotations

import tkinter as tk
from tkinter import font as tkfont
from pathlib import Path
from typing import Callable
from PIL import Image, ImageTk

TRANSPARENT_KEY = "#FF00FF"


def draw_rounded_rectangle(
    canvas: tk.Canvas,
    x1: int,
    y1: int,
    x2: int,
    y2: int,
    radius: int,
    **kwargs: object,
) -> int:
    points = [
        x1 + radius,
        y1,
        x2 - radius,
        y1,
        x2,
        y1,
        x2,
        y1 + radius,
        x2,
        y2 - radius,
        x2,
        y2,
        x2 - radius,
        y2,
        x1 + radius,
        y2,
        x1,
        y2,
        x1,
        y2 - radius,
        x1,
        y1 + radius,
        x1,
        y1,
    ]
    return canvas.create_polygon(points, smooth=True, splinesteps=24, **kwargs)


class NinePatchBorder:
    def __init__(self, image_path: str | Path, border_width: int) -> None:
        self.border_width = border_width
        self.original_image = Image.open(str(image_path))
        self.image_refs = []

    def draw(
        self,
        canvas: tk.Canvas,
        x: int,
        y: int,
        width: int,
        height: int,
    ) -> None:
        self.image_refs.clear()
        bw = self.border_width
        img = self.original_image
        img_w, img_h = img.size

        if width <= 0 or height <= 0:
            return

        center_w = max(1, width - bw * 2)
        center_h = max(1, height - bw * 2)

        regions = [
            (0, 0, bw, bw, x, y, bw, bw),
            (img_w - bw, 0, img_w, bw, x + width - bw, y, bw, bw),
            (0, img_h - bw, bw, img_h, x, y + height - bw, bw, bw),
            (img_w - bw, img_h - bw, img_w, img_h, x + width - bw, y + height - bw, bw, bw),
            (bw, 0, img_w - bw, bw, x + bw, y, center_w, bw),
            (bw, img_h - bw, img_w - bw, img_h, x + bw, y + height - bw, center_w, bw),
            (0, bw, bw, img_h - bw, x, y + bw, bw, center_h),
            (img_w - bw, bw, img_w, img_h - bw, x + width - bw, y + bw, bw, center_h),
            (bw, bw, img_w - bw, img_h - bw, x + bw, y + bw, center_w, center_h),
        ]

        for src_x, src_y, src_x2, src_y2, dst_x, dst_y, dst_w, dst_h in regions:
            region = img.crop((src_x, src_y, src_x2, src_y2))
            if dst_w > 0 and dst_h > 0:
                region = region.resize((dst_w, dst_h), Image.LANCZOS)
            photo = ImageTk.PhotoImage(region)
            self.image_refs.append(photo)
            canvas.create_image(dst_x, dst_y, anchor="nw", image=photo)


class RoundedBubbleWindow:
    def __init__(self, master: tk.Misc) -> None:
        self.window = tk.Toplevel(master)
        self.window.withdraw()
        self.window.overrideredirect(True)
        self.window.attributes("-topmost", True)
        self.window.configure(bg=TRANSPARENT_KEY)
        try:
            self.window.attributes("-transparentcolor", TRANSPARENT_KEY)
        except tk.TclError:
            pass

        self.canvas = tk.Canvas(
            self.window,
            bg=TRANSPARENT_KEY,
            highlightthickness=0,
            bd=0,
        )
        self.canvas.pack()

        self.text_font = tkfont.Font(family="Microsoft YaHei UI", size=10)
        self.label = tk.Label(
            self.window,
            bg="white",
            fg="#202124",
            justify="left",
            anchor="nw",
            font=self.text_font,
            padx=0,
            pady=0,
        )

        self.width = 0
        self.height = 0
        self.body_height = 0
        self.anchor_x = 0
        self.anchor_y = 0
        self.hide_job: str | None = None
        self.tail_height = 14
        self.tail_half_width = 12
        self.border_width = 0
        self.corner_radius = 20
        self.border_color = "#111111"
        self.fill_color = "white"

    def show(
        self,
        text: str,
        anchor_x: int,
        anchor_y: int,
        *,
        max_width: int,
        auto_hide_ms: int,
    ) -> None:
        self.cancel_hide()
        padding_x = 18
        padding_y = 12

        self.anchor_x = anchor_x
        self.anchor_y = anchor_y

        self.label.configure(text=text, wraplength=max_width)
        self.label.update_idletasks()

        inset = self.border_width + 1
        self.body_height = self.label.winfo_reqheight() + padding_y * 2 + inset * 2
        self.width = self.label.winfo_reqwidth() + padding_x * 2 + inset * 2
        self.height = self.body_height + self.tail_height

        self.canvas.configure(width=self.width, height=self.height)
        self.canvas.delete("all")
        self.draw_bubble(self.width // 2)
        self.canvas.create_window(
            inset + padding_x,
            inset + padding_y,
            anchor="nw",
            window=self.label,
        )
        self.reposition(anchor_x, anchor_y)
        self.window.deiconify()

        if auto_hide_ms > 0:
            self.hide_job = self.window.after(auto_hide_ms, self.hide)

    def draw_bubble(self, tail_center_x: int) -> None:
        if self.width <= 0 or self.height <= 0:
            return
        self.canvas.delete("bubble_bg")
        inset = self.border_width + 1
        body_bottom = self.body_height
        min_tail_x = inset + self.corner_radius + self.tail_half_width
        max_tail_x = self.width - inset - self.corner_radius - self.tail_half_width
        tail_center_x = max(min_tail_x, min(max_tail_x, tail_center_x))
        tail_base_y = body_bottom - self.border_width

        self.canvas.create_polygon(
            tail_center_x - self.tail_half_width,
            tail_base_y,
            tail_center_x + self.tail_half_width,
            tail_base_y,
            tail_center_x,
            self.height - inset,
            fill=self.fill_color,
            outline=self.border_color,
            width=self.border_width,
            joinstyle="round",
            tags=("bubble_bg",),
        )
        draw_rounded_rectangle(
            self.canvas,
            inset,
            inset,
            self.width - inset,
            body_bottom,
            radius=self.corner_radius,
            fill=self.fill_color,
            outline=self.border_color,
            width=self.border_width,
            tags=("bubble_bg",),
        )

    def reposition(self, anchor_x: int, anchor_y: int) -> None:
        self.anchor_x = anchor_x
        self.anchor_y = anchor_y
        if self.width <= 0 or self.height <= 0:
            return
        screen_width = self.window.winfo_screenwidth()
        x = anchor_x - self.width // 2
        y = anchor_y - self.height - 4
        x = max(8, min(screen_width - self.width - 8, x))
        y = max(8, y)
        self.draw_bubble(anchor_x - x)
        self.window.geometry(f"{self.width}x{self.height}+{x}+{y}")

    def cancel_hide(self) -> None:
        if self.hide_job is not None:
            self.window.after_cancel(self.hide_job)
            self.hide_job = None

    def hide(self) -> None:
        self.cancel_hide()
        self.window.withdraw()

    def is_visible(self) -> bool:
        return self.window.state() != "withdrawn"

    def destroy(self) -> None:
        self.cancel_hide()
        self.window.destroy()


class ChatInputDialog:
    def __init__(
        self,
        master: tk.Misc,
        on_submit: Callable[[str], None],
        on_close: Callable[[], None] | None = None,
        border_image_path: str | Path | None = None,
    ) -> None:
        self.on_submit = on_submit
        self.on_close = on_close
        self.width = 380
        self.height = 248
        self.anchor_x = 0
        self.anchor_y = 0
        self.use_image_border = border_image_path is not None
        self.bg_image_ref = None

        self.window = tk.Toplevel(master)
        self.window.withdraw()
        self.window.overrideredirect(True)
        self.window.attributes("-topmost", True)
        self.window.configure(bg=TRANSPARENT_KEY)
        try:
            self.window.attributes("-transparentcolor", TRANSPARENT_KEY)
        except tk.TclError:
            pass

        self.canvas = tk.Canvas(
            self.window,
            width=self.width,
            height=self.height,
            bg=TRANSPARENT_KEY,
            highlightthickness=0,
            bd=0,
        )
        self.canvas.pack()

        if self.use_image_border:
            self._load_background_image(border_image_path)
            self._draw_background()
            padding_x = 40
            padding_y = 30
            content_bg = "white"
        else:
            draw_rounded_rectangle(
                self.canvas,
                2,
                2,
                self.width - 2,
                self.height - 2,
                radius=20,
                fill="white",
                outline="",
                width=0,
            )
            padding_x = 18
            padding_y = 16
            content_bg = "white"

        self.content = tk.Frame(
            self.window,
            bg=content_bg,
            width=self.width - padding_x * 2,
            height=self.height - padding_y * 2,
        )
        self.content.grid_columnconfigure(0, weight=1)
        self.content.grid_rowconfigure(1, weight=1)
        self.content.grid_propagate(False)
        self.canvas.create_window(
            padding_x,
            padding_y,
            anchor="nw",
            window=self.content,
            width=self.width - padding_x * 2,
            height=self.height - padding_y * 2,
        )

        self.title_label = tk.Label(
            self.content,
            text="和桌宠对话",
            bg=content_bg,
            fg="#202124",
            font=("Microsoft YaHei UI", 10, "bold"),
        )
        self.title_label.grid(row=0, column=0, sticky="w")

        self.text = tk.Text(
            self.content,
            width=36,
            height=6,
            relief="flat",
            wrap="word",
            bg=content_bg,
            fg="#202124",
            font=("Microsoft YaHei UI", 10),
            insertbackground="#202124",
        )
        self.text.grid(row=1, column=0, sticky="nsew", pady=(10, 10))

        self.buttons = tk.Frame(self.content, bg=content_bg)
        self.buttons.grid(row=2, column=0, sticky="e")

        self.close_button = tk.Button(
            self.buttons,
            text="关闭",
            command=self.hide,
            relief="flat",
            bd=0,
            padx=12,
            pady=6,
            bg="#F3F4F6",
            activebackground="#E5E7EB",
            font=("Microsoft YaHei UI", 9),
        )
        self.close_button.pack(side="right")

        self.send_button = tk.Button(
            self.buttons,
            text="发送",
            command=self.submit,
            relief="flat",
            bd=0,
            padx=12,
            pady=6,
            bg="#111827",
            fg="white",
            activebackground="#374151",
            activeforeground="white",
            font=("Microsoft YaHei UI", 9, "bold"),
        )
        self.send_button.pack(side="right", padx=(0, 8))

        self.window.bind("<Escape>", lambda _event: self.hide())
        self.text.bind("<Control-Return>", lambda _event: self.submit())
        self.text.bind("<Return>", self.handle_return_submit)

    def _load_background_image(self, image_path: str | Path) -> None:
        self.original_bg_image = Image.open(str(image_path))

    def _draw_background(self) -> None:
        self.canvas.delete("bg_image")
        scaled = self.original_bg_image.resize(
            (self.width, self.height), Image.LANCZOS
        )
        self.bg_image_ref = ImageTk.PhotoImage(scaled)
        self.canvas.create_image(0, 0, anchor="nw", image=self.bg_image_ref, tags="bg_image")

    def show(self, anchor_x: int, anchor_y: int) -> None:
        self.anchor_x = anchor_x
        self.anchor_y = anchor_y
        self.reposition(anchor_x, anchor_y)
        self.window.deiconify()
        self.text.focus_set()

    def reposition(self, anchor_x: int, anchor_y: int) -> None:
        self.anchor_x = anchor_x
        self.anchor_y = anchor_y
        screen_width = self.window.winfo_screenwidth()
        screen_height = self.window.winfo_screenheight()
        x = anchor_x - self.width // 2
        y = anchor_y + 14
        x = max(8, min(screen_width - self.width - 8, x))
        y = max(8, min(screen_height - self.height - 8, y))
        self.window.geometry(f"{self.width}x{self.height}+{x}+{y}")

    def submit(self) -> str | None:
        content = self.text.get("1.0", "end").strip()
        if not content:
            return None
        self.text.delete("1.0", "end")
        self._is_submitting = True
        self.hide()
        self.on_submit(content)
        return "break"

    def handle_return_submit(self, event: tk.Event) -> str | None:
        if event.state & 0x1:
            return None
        return self.submit()

    def hide(self) -> None:
        was_visible = self.is_visible()
        self.window.withdraw()
        if was_visible and not getattr(self, '_is_submitting', False) and self.on_close:
            self.on_close()
        self._is_submitting = False

    def is_visible(self) -> bool:
        return self.window.state() != "withdrawn"

    def destroy(self) -> None:
        self.window.destroy()
