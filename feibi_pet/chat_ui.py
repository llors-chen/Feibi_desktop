from __future__ import annotations

import tkinter as tk
from tkinter import font as tkfont
from pathlib import Path
from typing import Callable
from PIL import Image, ImageTk

TRANSPARENT_KEY = "#FF00FF"
CHATBOX_TRANSPARENT_THRESHOLD = 12
CHATBOX_WIDTH = 340
CHATBOX_HEIGHT = 76
CHATBOX_SOURCE_MARGINS = (510, 150, 185, 145)
CHATBOX_OUTPUT_MARGINS = (119, 35, 43, 34)
CHATBOX_CONTENT_X = 119
CHATBOX_CONTENT_Y = 35
CHATBOX_CONTENT_RIGHT = 43
CHATBOX_CONTENT_BOTTOM = 34
CHATBOX_TEXT_BG = "#91D7F2"
CHATBOX_TEXT_FG = "#2D171C"
INPUT_BORDER_OUTER = "#3A080D"
INPUT_BORDER_INNER = "#FFFFFF"
INPUT_RADIUS = 16
REPLY_BUBBLE_BG = "#A7DFF6"
REPLY_BUBBLE_BORDER = "#3A080D"
REPLY_BUBBLE_TEXT = "#2D171C"


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


class NinePatchImage:
    def __init__(
        self,
        image_path: str | Path,
        source_margins: tuple[int, int, int, int],
    ) -> None:
        self.original_image = Image.open(str(image_path)).convert("RGBA")
        self.source_margins = source_margins
        self.image_ref: ImageTk.PhotoImage | None = None

    def render(
        self,
        width: int,
        height: int,
        output_margins: tuple[int, int, int, int],
    ) -> Image.Image:
        img = self.original_image
        img_w, img_h = img.size

        if width <= 0 or height <= 0:
            return Image.new("RGBA", (1, 1), (0, 0, 0, 0))

        src_left, src_top, src_right, src_bottom = self.source_margins
        dst_left, dst_top, dst_right, dst_bottom = self._fit_margins(
            width,
            height,
            output_margins,
        )
        src_x = (0, src_left, img_w - src_right, img_w)
        src_y = (0, src_top, img_h - src_bottom, img_h)
        dst_x = (0, dst_left, width - dst_right, width)
        dst_y = (0, dst_top, height - dst_bottom, height)
        output = Image.new("RGBA", (width, height), (0, 0, 0, 0))

        for row in range(3):
            for col in range(3):
                sx1, sx2 = src_x[col], src_x[col + 1]
                sy1, sy2 = src_y[row], src_y[row + 1]
                dx1, dx2 = dst_x[col], dst_x[col + 1]
                dy1, dy2 = dst_y[row], dst_y[row + 1]
                dst_w = dx2 - dx1
                dst_h = dy2 - dy1
                if sx2 <= sx1 or sy2 <= sy1 or dst_w <= 0 or dst_h <= 0:
                    continue
                region = img.crop((sx1, sy1, sx2, sy2))
                if region.size != (dst_w, dst_h):
                    region = region.resize((dst_w, dst_h), Image.LANCZOS)
                output.alpha_composite(region, (dx1, dy1))

        return output

    def draw(
        self,
        canvas: tk.Canvas,
        x: int,
        y: int,
        width: int,
        height: int,
        output_margins: tuple[int, int, int, int],
        *,
        tag: str = "nine_patch",
    ) -> None:
        rendered = self.render(width, height, output_margins)
        self.image_ref = ImageTk.PhotoImage(
            flatten_alpha_to_key(rendered, TRANSPARENT_KEY, CHATBOX_TRANSPARENT_THRESHOLD)
        )
        canvas.create_image(x, y, anchor="nw", image=self.image_ref, tags=tag)

    def _fit_margins(
        self,
        width: int,
        height: int,
        margins: tuple[int, int, int, int],
    ) -> tuple[int, int, int, int]:
        left, top, right, bottom = margins
        if left + right > width:
            scale = width / max(1, left + right)
            left = int(left * scale)
            right = max(0, width - left)
        if top + bottom > height:
            scale = height / max(1, top + bottom)
            top = int(top * scale)
            bottom = max(0, height - top)
        return left, top, right, bottom


def flatten_alpha_to_key(
    image: Image.Image,
    transparent_key: str,
    alpha_threshold: int,
) -> Image.Image:
    key = tuple(int(transparent_key[i : i + 2], 16) for i in (1, 3, 5))
    output = Image.new("RGB", image.size, key)
    rgba = image.convert("RGBA")
    pixels = rgba.load()
    out_pixels = output.load()
    width, height = rgba.size

    for y in range(height):
        for x in range(width):
            r, g, b, a = pixels[x, y]
            if a > alpha_threshold:
                out_pixels[x, y] = (r, g, b)

    return output


class RoundedBubbleWindow:
    def __init__(
        self,
        master: tk.Misc,
        border_image_path: str | Path | None = None,
    ) -> None:
        self.background = (
            NinePatchImage(border_image_path, CHATBOX_SOURCE_MARGINS)
            if border_image_path is not None
            else None
        )
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

        self.text_font = tkfont.Font(family="Microsoft YaHei UI", size=9)

        self.width = 0
        self.height = 0
        self.anchor_x = 0
        self.anchor_y = 0
        self.hide_job: str | None = None

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

        self.anchor_x = anchor_x
        self.anchor_y = anchor_y

        text_id = self.canvas.create_text(
            0,
            0,
            anchor="nw",
            text=text,
            width=max_width,
            font=self.text_font,
            fill=REPLY_BUBBLE_TEXT,
            tags=("measure_text",),
        )
        bbox = self.canvas.bbox(text_id) or (0, 0, max_width, 24)
        self.canvas.delete("measure_text")
        text_width = min(max_width, max(1, bbox[2] - bbox[0]))
        text_height = max(1, bbox[3] - bbox[1])

        self.width = max(260, text_width + CHATBOX_CONTENT_X + CHATBOX_CONTENT_RIGHT)
        self.height = max(92, text_height + CHATBOX_CONTENT_Y + CHATBOX_CONTENT_BOTTOM)

        self.canvas.configure(width=self.width, height=self.height)
        self.canvas.delete("all")
        self.draw_background()
        content_width = max(1, self.width - CHATBOX_CONTENT_X - CHATBOX_CONTENT_RIGHT)
        self.canvas.create_text(
            CHATBOX_CONTENT_X,
            CHATBOX_CONTENT_Y,
            anchor="nw",
            text=text,
            width=content_width,
            font=self.text_font,
            fill=REPLY_BUBBLE_TEXT,
            tags=("reply_text",),
        )
        self.reposition(anchor_x, anchor_y)
        self.window.deiconify()

        if auto_hide_ms > 0:
            self.hide_job = self.window.after(auto_hide_ms, self.hide)

    def draw_background(self) -> None:
        if self.background is None:
            draw_rounded_rectangle(
                self.canvas,
                2,
                2,
                self.width - 2,
                self.height - 2,
                radius=18,
                fill=REPLY_BUBBLE_BG,
                outline=REPLY_BUBBLE_BORDER,
                width=3,
                tags=("bubble_bg",),
            )
            return
        self.background.draw(
            self.canvas,
            0,
            0,
            self.width,
            self.height,
            CHATBOX_OUTPUT_MARGINS,
            tag="bubble_bg",
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
        del border_image_path
        self.on_submit = on_submit
        self.on_close = on_close
        self.width = CHATBOX_WIDTH
        self.height = CHATBOX_HEIGHT
        self.anchor_x = 0
        self.anchor_y = 0
        self._is_submitting = False

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

        self._draw_background()
        padding_x = 18
        padding_y = 14
        content_width = self.width - padding_x * 2
        content_height = self.height - padding_y * 2
        content_bg = CHATBOX_TEXT_BG

        self.content = tk.Frame(
            self.window,
            bg=content_bg,
            width=content_width,
            height=content_height,
        )
        self.content.grid_columnconfigure(0, weight=1)
        self.content.grid_rowconfigure(0, weight=1)
        self.content.grid_propagate(False)
        self.canvas.create_window(
            padding_x,
            padding_y,
            anchor="nw",
            window=self.content,
            width=content_width,
            height=content_height,
        )

        self.text = tk.Text(
            self.content,
            width=36,
            height=6,
            relief="flat",
            borderwidth=0,
            highlightthickness=0,
            wrap="word",
            bg=content_bg,
            fg=CHATBOX_TEXT_FG,
            font=("Microsoft YaHei UI", 9),
            insertbackground=CHATBOX_TEXT_FG,
            padx=0,
            pady=0,
        )
        self.text.grid(row=0, column=0, sticky="nsew")

        self.window.bind("<Escape>", lambda _event: self.hide())
        self.window.bind("<Button-3>", self.handle_refresh)
        self.canvas.bind("<Button-3>", self.handle_refresh)
        self.content.bind("<Button-3>", self.handle_refresh)
        self.text.bind("<Button-3>", self.handle_refresh)
        self.text.bind("<Return>", self.handle_return_submit)

    def _draw_background(self) -> None:
        self.canvas.delete("input_bg")
        draw_rounded_rectangle(
            self.canvas,
            1,
            1,
            self.width - 1,
            self.height - 1,
            radius=INPUT_RADIUS,
            fill=CHATBOX_TEXT_BG,
            outline=INPUT_BORDER_OUTER,
            width=3,
            tags=("input_bg",),
        )
        draw_rounded_rectangle(
            self.canvas,
            6,
            6,
            self.width - 6,
            self.height - 6,
            radius=INPUT_RADIUS - 5,
            fill="",
            outline=INPUT_BORDER_INNER,
            width=2,
            tags=("input_bg",),
        )

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

    def reset(self) -> None:
        self._is_submitting = False
        self.text.delete("1.0", "end")

    def handle_refresh(self, event: tk.Event) -> str:
        del event
        self.reset()
        self.hide()
        return "break"

    def hide(self, *, notify: bool = True) -> None:
        was_visible = self.is_visible()
        self.window.withdraw()
        if (
            notify
            and was_visible
            and not getattr(self, '_is_submitting', False)
            and self.on_close
        ):
            self.on_close()
        self._is_submitting = False

    def is_visible(self) -> bool:
        return self.window.state() != "withdrawn"

    def destroy(self) -> None:
        self.window.destroy()
