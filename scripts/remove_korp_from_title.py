#!/usr/bin/env python3
"""Точечно убрать «КОРП» из заголовка окна 1С на скриншотах.

Было:  Управление холдингом, редакция 3.3 (1С:Предприятие КОРП)
Стало: Управление холдингом, редакция 3.3 (1С:Предприятие)
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont
import pytesseract

IMAGE_EXTS = {".png", ".jpg", ".jpeg", ".webp", ".bmp", ".gif"}
FONT_CANDIDATES = [
    "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
]


def _is_dark(c: tuple[int, ...], thresh: int = 110) -> bool:
    return c[0] < thresh and c[1] < thresh and c[2] < thresh


def _median_color(samples: list[tuple[int, ...]], q: float = 0.5) -> tuple[int, ...]:
    samples = sorted(samples, key=lambda c: 0.299 * c[0] + 0.587 * c[1] + 0.114 * c[2])
    return samples[max(0, min(len(samples) - 1, int((len(samples) - 1) * q)))]


def _find_boxes(img: Image.Image, top_h: int):
    data = pytesseract.image_to_data(
        img.crop((0, 0, img.size[0], top_h)), lang="rus+eng", output_type=pytesseract.Output.DICT
    )
    pred = korp = None
    for i, text in enumerate(data["text"]):
        if not text:
            continue
        box = (text, data["left"][i], data["top"][i], data["width"][i], data["height"][i])
        if "КОРП" in text:
            korp = box
        if "Предприят" in text:
            pred = box
        elif pred is None and "1С" in text:
            pred = box
    return pred, korp


def remove_korp(image: Image.Image) -> tuple[Image.Image, bool]:
    img = image.convert("RGB").copy()
    w, h = img.size
    pred = korp = None
    top_h = 40
    for frac in (0.10, 0.12, 0.15, 0.18, 0.22):
        top_h = max(40, int(h * frac))
        pred, korp = _find_boxes(img, top_h)
        if korp:
            break
    if not korp:
        return img, False

    _, kx, ky, kw, kh = korp
    if pred is not None:
        _, px, py, pw, ph = pred
        rightmost = px
        for x in range(px, px + pw):
            for y in range(max(0, py), min(top_h, py + ph)):
                if _is_dark(img.getpixel((x, y)), 115):
                    rightmost = x
        ocr_end = px + pw - 1
        if abs(ocr_end - rightmost) <= 8:
            rightmost = max(rightmost, ocr_end - 1)
    else:
        rightmost = kx - 8
        for x in range(max(0, kx - 160), kx - 2):
            for y in range(max(0, ky), min(top_h, ky + kh)):
                if _is_dark(img.getpixel((x, y)), 115):
                    rightmost = x

    samples: list[tuple[int, ...]] = []
    for x in range(120, min(500, w - 1)):
        for y in (1, 2, 3, 4):
            samples.append(img.getpixel((x, y)))
        for y in range(max(1, top_h - 6), top_h):
            samples.append(img.getpixel((x, min(h - 1, y))))
    fill = _median_color(samples, 0.8) if samples else (251, 237, 158)

    draw = ImageDraw.Draw(img)
    cover_x1 = rightmost + 1
    cover_x2 = min(w - 1, kx + kw + 12)
    cover_y1 = 0
    cover_y2 = min(h - 1, max(36, ky + kh + 12))
    draw.rectangle((cover_x1, cover_y1, cover_x2, cover_y2), fill=fill)

    for x in range(cover_x1, cover_x2 + 1):
        for y in range(cover_y1, cover_y2 + 1):
            c = img.getpixel((x, y))
            if _is_dark(c, 140) or (
                c[0] < 180 and c[1] < 180 and abs(c[0] - c[1]) < 40 and c[0] < fill[0] - 30
            ):
                img.putpixel((x, y), fill)

    ts: list[tuple[int, ...]] = []
    if pred is not None:
        _, px, py, pw, ph = pred
        for x in range(px + 10, max(px + 11, rightmost - 5)):
            for y in range(py, py + ph):
                c = img.getpixel((x, y))
                if _is_dark(c, 90):
                    ts.append(c)
    text_color = _median_color(ts, 0.5) if ts else (51, 51, 51)

    font = None
    for size in (13, 12, 14):
        for fp in FONT_CANDIDATES:
            try:
                f = ImageFont.truetype(fp, size)
                bb = f.getbbox(")")
                if 12 <= bb[3] - bb[1] <= 15:
                    font = f
                    break
            except OSError:
                pass
        if font:
            break
    if font is None:
        font = ImageFont.load_default()

    tops: list[int] = []
    for x in range(max(0, rightmost - 40), rightmost):
        for y in range(5, 28):
            if _is_dark(img.getpixel((x, y)), 110):
                tops.append(y)
                break
    avg_top = int(sum(tops) / len(tops)) if tops else 10
    bb = font.getbbox(")")
    draw.text((rightmost + 2, avg_top - bb[1] - 1), ")", fill=text_color, font=font)
    return img, True


def process_path(src: Path, dst: Path) -> str:
    edited, changed = remove_korp(Image.open(src))
    dst.parent.mkdir(parents=True, exist_ok=True)
    if dst.suffix.lower() in {".jpg", ".jpeg"}:
        edited.save(dst, quality=95)
    else:
        edited.save(dst, optimize=True)
    return "ok" if changed else "no-korp"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path)
    parser.add_argument("-o", "--output", type=Path)
    args = parser.parse_args(argv)

    if args.input.is_dir():
        inputs = sorted(p for p in args.input.iterdir() if p.suffix.lower() in IMAGE_EXTS)
        out_dir = args.output or args.input.parent
        out_dir.mkdir(parents=True, exist_ok=True)
        if not inputs:
            print(f"Нет изображений в {args.input}", file=sys.stderr)
            return 1
        n = 0
        for src in inputs:
            dst = out_dir / f"{src.stem}_bez_korp{src.suffix}"
            status = process_path(src, dst)
            print(f"{src.name}: {status} -> {dst.name}")
            if status == "ok":
                n += 1
        print(f"Итого: {n}/{len(inputs)}")
        return 0 if n else 2

    src = args.input
    dst = args.output or src.with_name(f"{src.stem}_bez_korp{src.suffix or '.png'}")
    status = process_path(src, dst)
    print(f"{src.name}: {status} -> {dst}")
    return 0 if status == "ok" else 2


if __name__ == "__main__":
    raise SystemExit(main())
