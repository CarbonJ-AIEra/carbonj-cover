#!/usr/bin/env python3
"""Apply the bundled CarbonJ top panel to a completed cover."""

from __future__ import annotations

import argparse
import json
import os
import uuid
from pathlib import Path
from typing import Any

from PIL import Image


DEFAULT_WORDMARK_ASSET = Path(__file__).resolve().parents[1] / "assets" / "carbonj-fixed-top-wordmark.png"
DEFAULT_PILL_ASSET = DEFAULT_WORDMARK_ASSET
DEFAULT_AVATAR_ASSET = Path(__file__).resolve().parents[1] / "assets" / "carbonj-fixed-top-avatar.png"
DEFAULT_TOP_INSET_CM = 0.7
DEFAULT_CONTENT_GAP_CM = 0.35
REFERENCE_DPI = 96.0
REFERENCE_WIDTH = 850.0
REFERENCE_WORDMARK_X = 104.0
REFERENCE_WORDMARK_Y = 0.0
REFERENCE_WORDMARK_WIDTH = 163.0
REFERENCE_WORDMARK_HEIGHT = 66.0
REFERENCE_AVATAR_X = 28.0
REFERENCE_AVATAR_Y = 0.0
REFERENCE_AVATAR_SIZE = 66.0


def apply_fixed_top_panel(
    base_path: Path,
    output_path: Path,
    pill_path: Path = DEFAULT_WORDMARK_ASSET,
    avatar_path: Path = DEFAULT_AVATAR_ASSET,
    top_inset_cm: float = DEFAULT_TOP_INSET_CM,
) -> dict[str, Any]:
    """Scale the locked pill and high-resolution avatar to fixed top-panel coordinates."""
    if top_inset_cm < 0:
        raise ValueError("top_inset_cm must be non-negative")
    if not pill_path.is_file():
        raise FileNotFoundError(f"fixed top wordmark asset is missing: {pill_path}")
    if not avatar_path.is_file():
        raise FileNotFoundError(f"fixed top avatar asset is missing: {avatar_path}")

    with (
        Image.open(base_path) as base_image,
        Image.open(pill_path) as pill_image,
        Image.open(avatar_path) as avatar_image,
    ):
        canvas = base_image.convert("RGBA")
        wordmark = pill_image.convert("RGBA")
        if wordmark.getchannel("A").getbbox() is None:
            raise RuntimeError(f"fixed top wordmark has no visible alpha content: {pill_path}")

        scale = canvas.width / REFERENCE_WIDTH
        top_inset_px = round(top_inset_cm / 2.54 * REFERENCE_DPI)
        panel_y = top_inset_px
        wordmark_x = round(REFERENCE_WORDMARK_X * scale)
        wordmark_y = panel_y + round(REFERENCE_WORDMARK_Y * scale)
        wordmark_width = max(1, round(REFERENCE_WORDMARK_WIDTH * scale))
        wordmark_height = max(1, round(REFERENCE_WORDMARK_HEIGHT * scale))
        wordmark = wordmark.resize((wordmark_width, wordmark_height), Image.Resampling.LANCZOS)
        avatar_size = max(1, round(REFERENCE_AVATAR_SIZE * scale))
        avatar_x = round(REFERENCE_AVATAR_X * scale)
        avatar_y = panel_y + round(REFERENCE_AVATAR_Y * scale)
        avatar = avatar_image.convert("RGBA").resize((avatar_size, avatar_size), Image.Resampling.LANCZOS)
        layer = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
        layer.alpha_composite(wordmark, (wordmark_x, wordmark_y))
        layer.alpha_composite(avatar, (avatar_x, avatar_y))
        merged = Image.alpha_composite(canvas, layer).convert("RGB")

        output_path.parent.mkdir(parents=True, exist_ok=True)
        temp_path = output_path.with_name(f".{output_path.name}.{uuid.uuid4().hex}.tmp.png")
        merged.save(temp_path, format="PNG", optimize=True, dpi=(REFERENCE_DPI, REFERENCE_DPI))
        os.replace(temp_path, output_path)

    return {
        "mode": "fixed_asset_alpha_composite",
        "wordmark_asset": str(pill_path),
        "avatar_asset": str(avatar_path),
        "base_image": str(base_path),
        "output_image": str(output_path),
        "canvas": {"width": canvas.width, "height": canvas.height},
        "panel": {
            "x": min(wordmark_x, avatar_x),
            "y": panel_y,
            "width": max(wordmark_x + wordmark_width, avatar_x + avatar_size) - min(wordmark_x, avatar_x),
            "height": max(wordmark_y + wordmark_height, avatar_y + avatar_size) - panel_y,
            "scale": scale,
            "visible_top_px": top_inset_px,
            "top_inset_cm": top_inset_cm,
            "reference_dpi": REFERENCE_DPI,
        },
        "content_start": {
            "gap_below_panel_cm": DEFAULT_CONTENT_GAP_CM,
            "gap_below_panel_px": round(DEFAULT_CONTENT_GAP_CM / 2.54 * REFERENCE_DPI),
            "target_y": panel_y
            + max(wordmark_height, avatar_size)
            + round(DEFAULT_CONTENT_GAP_CM / 2.54 * REFERENCE_DPI),
        },
        "wordmark": {
            "x": wordmark_x,
            "y": wordmark_y,
            "width": wordmark_width,
            "height": wordmark_height,
            "source_width": pill_image.width,
            "source_height": pill_image.height,
        },
        "avatar": {
            "x": avatar_x,
            "y": avatar_y,
            "width": avatar_size,
            "height": avatar_size,
            "source_width": avatar_image.width,
            "source_height": avatar_image.height,
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base", required=True, type=Path, help="Completed cover before the fixed panel")
    parser.add_argument("--output", required=True, type=Path, help="Final cover path")
    parser.add_argument("--wordmark", "--pill", dest="wordmark", type=Path, default=DEFAULT_WORDMARK_ASSET, help="Locked high-resolution transparent brand wordmark")
    parser.add_argument("--avatar", type=Path, default=DEFAULT_AVATAR_ASSET, help="Locked high-resolution circular avatar")
    parser.add_argument("--top-inset-cm", type=float, default=DEFAULT_TOP_INSET_CM)
    args = parser.parse_args()

    record = apply_fixed_top_panel(
        args.base.expanduser().resolve(),
        args.output.expanduser().resolve(),
        args.wordmark.expanduser().resolve(),
        args.avatar.expanduser().resolve(),
        args.top_inset_cm,
    )
    print(json.dumps(record, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
