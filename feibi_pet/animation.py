from __future__ import annotations

from dataclasses import dataclass
import itertools
from pathlib import Path

from PIL import Image, ImageTk

from .config import ConfigError


@dataclass(slots=True)
class GifSequence:
    source: Path
    frames: list[ImageTk.PhotoImage]
    delays: list[int]
    width: int
    height: int


def resolve_resample(scale_mode: str) -> Image.Resampling:
    mapping = {
        "nearest": Image.Resampling.NEAREST,
        "box": Image.Resampling.BOX,
        "bilinear": Image.Resampling.BILINEAR,
        "bicubic": Image.Resampling.BICUBIC,
        "lanczos": Image.Resampling.LANCZOS,
    }
    return mapping.get(scale_mode, Image.Resampling.NEAREST)


def make_alpha_safe_for_tk_color_key(frame: Image.Image) -> Image.Image:
    # Tk color-key transparent windows blend semi-transparent pixels with the
    # key color first, which leaves green fringes. Keep the asset alpha shape,
    # but make each visible pixel fully opaque before handing it to Tk.
    alpha_band = frame.getchannel("A")
    frame.putalpha(alpha_band.point(lambda value: 255 if value > 0 else 0))
    return frame


def load_gif_sequence(
    gif_path: Path,
    scale: float,
    scale_mode: str,
    flip_horizontal: bool = False,
) -> GifSequence:
    image = Image.open(gif_path)
    frames: list[ImageTk.PhotoImage] = []
    delays: list[int] = []
    width = 0
    height = 0
    resample = resolve_resample(scale_mode)

    try:
        for index in itertools.count():
            try:
                image.seek(index)
            except EOFError:
                break

            frame = image.convert("RGBA")
            if flip_horizontal:
                frame = frame.transpose(Image.Transpose.FLIP_LEFT_RIGHT)
            if scale != 1.0:
                source_width, source_height = frame.size
                target_width = max(1, int(source_width * scale))
                target_height = max(1, int(source_height * scale))
                frame = frame.resize((target_width, target_height), resample)

            frame = make_alpha_safe_for_tk_color_key(frame)
            width, height = frame.size
            frames.append(ImageTk.PhotoImage(frame))
            delays.append(max(20, int(image.info.get("duration", 80))))
    finally:
        image.close()

    if not frames:
        raise ConfigError(f"GIF has no readable frames: {gif_path}")

    return GifSequence(
        source=gif_path,
        frames=frames,
        delays=delays,
        width=width,
        height=height,
    )
