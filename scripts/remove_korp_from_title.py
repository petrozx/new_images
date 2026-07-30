#!/usr/bin/env python3
"""Точечно убрать «КОРП» из заголовка окна 1С на скриншотах.

Заливка — жёлтый цвет шапки (не белый). Остальной кадр не меняется.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont
import pytesseract

IMAGE_EXTS = {".png", ".jpg", ".jpeg", ".webp", ".bmp", ".gif"}
FONT = "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf"


def _is_dark(c, thresh=110):
    return c[0] < thresh and c[1] < thresh and c[2] < thresh


def _header_yellow_at_row(img, y, w):
    samples = []
    for x in range(min(w - 20, 700), min(w - 5, 900)):
        c = img.getpixel((x, y))
        if c[0] > 220 and c[1] > 200 and c[2] < 200:
            samples.append(c)
    if not samples:
        for x in range(620, min(w - 5, 780)):
            c = img.getpixel((x, y))
            if c[0] > 220 and c[1] > 200 and c[2] < 200:
                samples.append(c)
    if samples:
        n = len(samples)
        return tuple(sum(c[i] for c in samples) // n for i in range(3))
    return (251, 237, 158)


def _find_boxes(img, top_h):
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


def remove_korp(image: Image.Image):
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
        rightmost = kx - 6

    x1, x2 = rightmost + 1, min(w - 1, kx + kw + 4)
    y1, y2 = max(0, ky - 2), min(34, ky + kh + 3)

    for y in range(y1, y2 + 1):
        fill = _header_yellow_at_row(img, y, w)
        for x in range(x1, x2 + 1):
            img.putpixel((x, y), fill)

    ts = []
    if pred is not None:
        _, px, py, pw, ph = pred
        for x in range(px + 20, max(px + 21, rightmost - 5)):
            for y in range(py, py + ph):
                c = img.getpixel((x, y))
                if _is_dark(c, 90):
                    ts.append(c)
    text_color = (51, 51, 51)
    if ts:
        n = len(ts)
        text_color = tuple(sum(c[i] for c in ts) // n for i in range(3))

    try:
        font = ImageFont.truetype(FONT, 13)
    except OSError:
        font = ImageFont.load_default()

    tops = []
    for x in range(max(0, rightmost - 40), rightmost):
        for y in range(5, 28):
            if _is_dark(img.getpixel((x, y)), 110):
                tops.append(y)
                break
    avg_top = int(sum(tops) / len(tops)) if tops else ky
    bb = font.getbbox(")")
    ImageDraw.Draw(img).text(
        (rightmost + 2, avg_top - bb[1] - 1), ")", fill=text_color, font=font
    )
    return img, True


def process_path(src: Path, dst: Path) -> str:
    edited, changed = remove_korp(Image.open(src))
    dst.parent.mkdir(parents=True, exist_ok=True)
    if dst.suffix.lower() in {".jpg", ".jpeg"}:
        edited.save(dst, quality=95)
    else:
        edited.save(dst, optimize=True)
    return "ok" if changed else "no-korp"


def main(argv=None) -> int:
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
            n += status == "ok"
        print(f"Итого: {n}/{len(inputs)}")
        return 0 if n else 2

    src = args.input
    dst = args.output or src.with_name(f"{src.stem}_bez_korp{src.suffix or '.png'}")
    status = process_path(src, dst)
    print(f"{src.name}: {status} -> {dst}")
    return 0 if status == "ok" else 2


if __name__ == "__main__":
    raise SystemExit(main())
