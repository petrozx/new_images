#!/usr/bin/env python3
"""Точечно убрать «КОРП» из заголовка окна 1С на скриншоте.

Было:  Управление холдингом, редакция 3.3 (1С:Предприятие КОРП)
Стало: Управление холдингом, редакция 3.3 (1С:Предприятие)

Остальные пиксели изображения не меняются.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont
import pytesseract

KORP_RE = re.compile(r"КОРП", re.IGNORECASE)


def _sample_fill(image: Image.Image, x: int, y: int) -> tuple[int, ...]:
    w, h = image.size
    samples = []
    for dx, dy in ((-2, -2), (-6, -1), (-10, 0), (2, -3), (-4, 1)):
        sx = min(max(0, x + dx), w - 1)
        sy = min(max(0, y + dy), h - 1)
        px = image.getpixel((sx, sy))
        samples.append(px[:3] if isinstance(px, tuple) else (px, px, px))
    samples.sort(key=lambda c: 0.299 * c[0] + 0.587 * c[1] + 0.114 * c[2])
    c = samples[len(samples) // 2]
    return (*c, 255) if image.mode == "RGBA" else c


def _find_korp_boxes(image: Image.Image, top_fraction: float) -> list[tuple[int, int, int, int, bool]]:
    width, height = image.size
    crop_h = max(40, int(height * top_fraction))
    region = image.crop((0, 0, width, crop_h))
    data = pytesseract.image_to_data(region, lang="rus+eng", output_type=pytesseract.Output.DICT)

    boxes: list[tuple[int, int, int, int, bool]] = []
    for i, text in enumerate(data["text"]):
        if not text or not KORP_RE.search(text):
            continue
        x, y, w, h = data["left"][i], data["top"][i], data["width"][i], data["height"][i]
        keep_paren = ")" in text
        # Закрашиваем ведущий пробел + «КОРП»; «)» оставляем / восстанавливаем.
        pad_left = max(3, int(h * 0.35))
        pad_y = max(1, h // 5)
        cover_w = int(w * (0.78 if keep_paren else 1.0))
        boxes.append(
            (
                max(0, x - pad_left),
                max(0, y - pad_y),
                min(width, x + cover_w),
                min(crop_h, y + h + pad_y),
                keep_paren,
            )
        )

    if boxes:
        return boxes

    # Fallback: весь кадр
    data = pytesseract.image_to_data(image, lang="rus+eng", output_type=pytesseract.Output.DICT)
    for i, text in enumerate(data["text"]):
        if not text or not KORP_RE.search(text):
            continue
        x, y, w, h = data["left"][i], data["top"][i], data["width"][i], data["height"][i]
        keep_paren = ")" in text
        pad_left = max(3, int(h * 0.35))
        pad_y = max(1, h // 5)
        cover_w = int(w * (0.78 if keep_paren else 1.0))
        boxes.append(
            (
                max(0, x - pad_left),
                max(0, y - pad_y),
                min(width, x + cover_w),
                min(height, y + h + pad_y),
                keep_paren,
            )
        )
    return boxes


def remove_korp(image: Image.Image, *, top_fraction: float = 0.15) -> tuple[Image.Image, int]:
    result = image.copy()
    boxes = _find_korp_boxes(result, top_fraction)
    draw = ImageDraw.Draw(result)
    for x1, y1, x2, y2, keep_paren in boxes:
        fill = _sample_fill(result, x1, y1)
        draw.rectangle((x1, y1, x2, y2), fill=fill)
        if keep_paren:
            font_size = max(11, y2 - y1 - 4)
            try:
                font = ImageFont.truetype(
                    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", font_size
                )
            except OSError:
                font = ImageFont.load_default()
            # Цвет текста заголовка 1С — тёмно-серый
            draw.text((x2, y1), ")", fill=(60, 60, 60), font=font)
    return result, len(boxes)


def process_path(src: Path, dst: Path, *, top_fraction: float) -> int:
    image = Image.open(src).convert("RGBA")
    cleaned, hits = remove_korp(image, top_fraction=top_fraction)
    dst.parent.mkdir(parents=True, exist_ok=True)
    if dst.suffix.lower() in {".jpg", ".jpeg"}:
        cleaned.convert("RGB").save(dst, quality=95)
    else:
        cleaned.convert("RGB").save(dst)
    return hits


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path, help="Скриншот или папка со скриншотами")
    parser.add_argument("-o", "--output", type=Path, help="Файл или папка результата")
    parser.add_argument("--top-fraction", type=float, default=0.15)
    args = parser.parse_args(argv)

    if args.input.is_dir():
        inputs = sorted(
            p
            for p in args.input.iterdir()
            if p.suffix.lower() in {".png", ".jpg", ".jpeg", ".webp", ".bmp"}
        )
        out_dir = args.output or (args.input.parent / "edited")
        out_dir.mkdir(parents=True, exist_ok=True)
        if not inputs:
            print(f"Нет изображений в {args.input}", file=sys.stderr)
            return 1
        total = 0
        for src in inputs:
            dst = out_dir / f"{src.stem}_bez_korp{src.suffix}"
            hits = process_path(src, dst, top_fraction=args.top_fraction)
            print(f"{src.name}: удалено блоков КОРП={hits} -> {dst}")
            total += hits
        return 0 if total else 2

    src = args.input
    dst = args.output or src.with_name(f"{src.stem}_bez_korp{src.suffix or '.png'}")
    hits = process_path(src, dst, top_fraction=args.top_fraction)
    print(f"Удалено блоков КОРП={hits} -> {dst}")
    return 0 if hits else 2


if __name__ == "__main__":
    raise SystemExit(main())
