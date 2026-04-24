from __future__ import annotations

import ctypes

GWL_EXSTYLE = -20
SPI_GETWORKAREA = 0x0030
WS_EX_LAYERED = 0x00080000
WS_EX_TRANSPARENT = 0x00000020


class RECT(ctypes.Structure):
    _fields_ = [
        ("left", ctypes.c_long),
        ("top", ctypes.c_long),
        ("right", ctypes.c_long),
        ("bottom", ctypes.c_long),
    ]


def resolve_anchored_coordinates(
    anchor: str,
    offset_x: int,
    offset_y: int,
    width: int,
    height: int,
    work_area: tuple[int, int, int, int],
) -> tuple[int, int]:
    left, top, right, bottom = work_area
    if anchor == "top_right":
        return right - width - offset_x, top + offset_y
    if anchor == "bottom_left":
        return left + offset_x, bottom - height - offset_y
    if anchor == "bottom_right":
        return right - width - offset_x, bottom - height - offset_y
    return left + offset_x, top + offset_y


def resolve_anchor_offsets(
    anchor: str,
    x: int,
    y: int,
    width: int,
    height: int,
    work_area: tuple[int, int, int, int],
) -> tuple[int, int]:
    left, top, right, bottom = work_area
    if anchor == "top_right":
        return right - width - x, y - top
    if anchor == "bottom_left":
        return x - left, bottom - height - y
    if anchor == "bottom_right":
        return right - width - x, bottom - height - y
    return x - left, y - top
