#!/usr/bin/env python3
"""Remove the word «КОРП» from 1C window title bars on screenshots.

Finds «КОРП» / «КОРП)» via OCR (preferably in the top title strip) and paints
over it with nearby background pixels so the caption becomes
«… (1С:Предприятие)» instead of «… (1С:Предприятие КОРП)».
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

from PIL import Image, ImageDraw
import pytesseract

KORP_RE = re.compile(r"КОРП", re.IGNORECASE)


def _sample_fill_color(image: Image.Image, box: tuple[int, int, int, int]) -> tuple[int, ...]:
    """Pick a background color from pixels just above/left of the box."""
    x1, y1, x2, y2 = box
    width, height = image.size
    samples: list[tuple[int, ...]] = []
    for dx, dy in ((-3, -2), (-8, -1), (2, -3), (-12, 0), (x2 - x1 + 2, -2)):
        sx = min(max(0, x1 + dx), width - 1)
        sy = min(max(0, y1 + dy), height - 1)
        samples.append(image.getpixel((sx, sy))[:3] if image.mode != "RGB" else image.getpixel((sx, sy)))
    # Median-ish: sort by luminance and take middle
    samples.sort(key=lambda c: 0.299 * c[0] + 0.587 * c[1] + 0.114 * c[2])
    color = samples[len(samples) // 2]
    if image.mode == "RGBA":
        return (*color[:3], 255)
    return color[:3] if image.mode == "RGB" else color


def _iter_korp_boxes(
    image: Image.Image, *, top_fraction: float
) -> list[tuple[int, int, int, int, bool]]:
    """Return boxes (x1, y1, x2, y2, keep_closing_paren) for OCR hits with КОРП."""
    width, height = image.size
    crop_h = max(1, int(height * top_fraction))
    regions = [
        (0, 0, width, crop_h),
        (0, 0, width, height),
    ]
    seen: set[tuple[int, int, int, int]] = set()
    boxes: list[tuple[int, int, int, int, bool]] = []

    for left, top, right, bottom in regions:
        region = image.crop((left, top, right, bottom))
        data = pytesseract.image_to_data(region, lang="rus+eng", output_type=pytesseract.Output.DICT)
        found_in_region = False
        for i, text in enumerate(data["text"]):
            if not text or not KORP_RE.search(text):
                continue
            x, y, w, h = data["left"][i], data["top"][i], data["width"][i], data["height"][i]
            keep_paren = ")" in text
            # Cover « КОРП» (with leading space). If the token is «КОРП)», leave room for «)».
            pad_left = max(4, w // 6)
            pad_y = max(1, h // 6)
            cover_w = w
            if keep_paren:
                # Roughly the width of «)» in the same font size.
                cover_w = max(1, int(w * 0.82))
            box = (
                left + max(0, x - pad_left),
                top + max(0, y - pad_y),
                left + min(region.size[0], x + cover_w),
                top + min(region.size[1], y + h + pad_y),
            )
            key = box[:4]
            if key not in seen:
                seen.add(key)
                boxes.append((*box, keep_paren))
                found_in_region = True
        if found_in_region:
            break
    return boxes


def remove_korp(image: Image.Image, *, top_fraction: float = 0.12) -> tuple[Image.Image, int]:
    """Return a copy of *image* with КОРП painted out, and the hit count."""
    result = image.copy()
    boxes = _iter_korp_boxes(result, top_fraction=top_fraction)
    draw = ImageDraw.Draw(result)
    for x1, y1, x2, y2, keep_paren in boxes:
        fill = _sample_fill_color(result, (x1, y1, x2, y2))
        draw.rectangle((x1, y1, x2, y2), fill=fill)
        if keep_paren:
            # Restore closing parenthesis of «(1С:Предприятие)».
            font_size = max(12, y2 - y1 - 2)
            try:
                from PIL import ImageFont

                font = ImageFont.truetype(
                    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", font_size
                )
            except Exception:
                font = None
            text_fill = (50, 50, 50)
            draw.text((x2 + 1, y1 - 1), ")", fill=text_fill, font=font)
    return result, len(boxes)


def process_path(src: Path, dst: Path, *, top_fraction: float) -> int:
    image = Image.open(src).convert("RGBA")
    cleaned, hits = remove_korp(image, top_fraction=top_fraction)
    dst.parent.mkdir(parents=True, exist_ok=True)
    # Keep PNG for screenshots; otherwise preserve format when possible.
    if dst.suffix.lower() in {".jpg", ".jpeg"}:
        cleaned.convert("RGB").save(dst, quality=95)
    else:
        cleaned.convert("RGB").save(dst)
    return hits


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path, help="Input screenshot or directory")
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        help="Output file or directory (default: <input>_bez_korp next to input)",
    )
    parser.add_argument(
        "--top-fraction",
        type=float,
        default=0.12,
        help="Fraction of image height treated as title bar (default: 0.12)",
    )
    args = parser.parse_args(argv)

    inputs: list[Path]
    if args.input.is_dir():
        inputs = sorted(
            p
            for p in args.input.iterdir()
            if p.suffix.lower() in {".png", ".jpg", ".jpeg", ".webp", ".bmp"}
        )
        out_dir = args.output or (args.input.parent / f"{args.input.name}_bez_korp")
        out_dir.mkdir(parents=True, exist_ok=True)
        if not inputs:
            print(f"No images found in {args.input}", file=sys.stderr)
            return 1
        total = 0
        for src in inputs:
            dst = out_dir / src.name
            hits = process_path(src, dst, top_fraction=args.top_fraction)
            print(f"{src.name}: removed {hits} КОРП box(es) -> {dst}")
            total += hits
        print(f"Done. Total boxes: {total}")
        return 0 if total else 2

    src = args.input
    if args.output:
        dst = args.output
    else:
        dst = src.with_name(f"{src.stem}_bez_korp{src.suffix or '.png'}")
    hits = process_path(src, dst, top_fraction=args.top_fraction)
    print(f"Removed {hits} КОРП box(es) -> {dst}")
    return 0 if hits else 2


if __name__ == "__main__":
    raise SystemExit(main())
