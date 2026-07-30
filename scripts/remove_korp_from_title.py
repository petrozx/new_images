#!/usr/bin/env python3
"""Точечно убрать «КОРП» из заголовка окна 1С на скриншотах.

Было:  Управление холдингом, редакция 3.3 (1С:Предприятие КОРП)
Стало: Управление холдингом, редакция 3.3 (1С:Предприятие)

Остальные пиксели изображения не меняются.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont
import pytesseract

IMAGE_EXTS = {".png", ".jpg", ".jpeg", ".webp", ".bmp", ".gif"}


def _is_dark(c: tuple[int, ...], thresh: int = 110) -> bool:
    return c[0] < thresh and c[1] < thresh and c[2] < thresh


def _median_color(samples: list[tuple[int, ...]], q: float = 0.5) -> tuple[int, ...]:
    samples = sorted(samples, key=lambda c: 0.299 * c[0] + 0.587 * c[1] + 0.114 * c[2])
    return samples[int(len(samples) * q)]


def remove_korp(image: Image.Image, *, top_fraction: float = 0.12) -> tuple[Image.Image, bool]:
    """Return (edited_image, changed)."""
    img = image.convert("RGB").copy()
    w, h = img.size
    top_h = max(40, int(h * top_fraction))
    data = pytesseract.image_to_data(
        img.crop((0, 0, w, top_h)), lang="rus+eng", output_type=pytesseract.Output.DICT
    )

    pred = None
    korp = None
    for i, text in enumerate(data["text"]):
        if not text:
            continue
        box = (data["left"][i], data["top"][i], data["width"][i], data["height"][i])
        if "КОРП" in text:
            korp = (text, *box)
        if "Предприят" in text or ("1С" in text and "Пред" in text):
            pred = (text, *box)
        elif pred is None and "1С" in text:
            pred = (text, *box)

    if korp is None:
        # Fallback: search full image top half
        data = pytesseract.image_to_data(
            img.crop((0, 0, w, max(top_h, h // 3))),
            lang="rus+eng",
            output_type=pytesseract.Output.DICT,
        )
        for i, text in enumerate(data["text"]):
            if text and "КОРП" in text:
                korp = (text, data["left"][i], data["top"][i], data["width"][i], data["height"][i])
            if text and ("Предприят" in text or "1С" in text) and pred is None:
                pred = (text, data["left"][i], data["top"][i], data["width"][i], data["height"][i])

    if korp is None:
        return img, False

    _, kx, ky, kw, kh = korp
    if pred is not None:
        _, px, py, pw, ph = pred
        scan_from, scan_to = px, kx
    else:
        px, py, pw, ph = max(0, kx - 200), ky, 200, kh
        scan_from, scan_to = px, kx

    rightmost = scan_from
    for x in range(scan_from, scan_to):
        for y in range(max(0, ky - 2), min(top_h, ky + kh + 2)):
            if _is_dark(img.getpixel((x, y)), 110):
                rightmost = x

    # Yellow/header fill from empty header band
    samples: list[tuple[int, ...]] = []
    for x in range(min(150, w // 4), min(400, w // 2)):
        for y in (1, 2, 3, max(1, top_h - 8), max(1, top_h - 7), max(1, top_h - 6)):
            if y < top_h:
                samples.append(img.getpixel((x, y)))
    # Also sample near the cover area but above text
    for x in range(max(0, kx - 30), min(w, kx + 10)):
        for y in range(0, max(1, ky - 1)):
            samples.append(img.getpixel((x, y)))
    fill = _median_color(samples, 0.75) if samples else (251, 237, 158)

    draw = ImageDraw.Draw(img)
    cover_x1 = rightmost + 2
    cover_x2 = min(w - 1, kx + kw + 6)
    cover_y1 = 0
    cover_y2 = min(top_h - 1, max(ky + kh + 8, 35))
    draw.rectangle((cover_x1, cover_y1, cover_x2, cover_y2), fill=fill)

    # Text color from title glyphs
    ts: list[tuple[int, ...]] = []
    for x in range(max(0, rightmost - 40), max(1, rightmost - 5)):
        for y in range(max(0, ky), min(top_h, ky + kh)):
            c = img.getpixel((x, y))
            if _is_dark(c, 90):
                ts.append(c)
    text_color = _median_color(ts, 0.5) if ts else (51, 51, 51)

    font = None
    for size in (13, 12, 14, 11, 15):
        for fp in (
            "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
            "/packages/agent-controller/assets/media/fonts/Inter/Inter-Regular.ttf",
        ):
            try:
                f = ImageFont.truetype(fp, size)
            except OSError:
                continue
            bb = f.getbbox(")")
            if 12 <= (bb[3] - bb[1]) <= 16:
                font = f
                break
        if font:
            break
    if font is None:
        font = ImageFont.load_default()

    tops: list[int] = []
    for x in range(max(0, rightmost - 30), rightmost):
        for y in range(5, min(top_h, 30)):
            if _is_dark(img.getpixel((x, y)), 110):
                tops.append(y)
                break
    avg_top = int(sum(tops) / len(tops)) if tops else max(8, ky)
    bb = font.getbbox(")")
    paren_x = rightmost + 2
    paren_y = avg_top - bb[1] - 1
    draw.text((paren_x, paren_y), ")", fill=text_color, font=font)
    return img, True


def process_path(src: Path, dst: Path, *, top_fraction: float) -> str:
    img = Image.open(src)
    edited, changed = remove_korp(img, top_fraction=top_fraction)
    dst.parent.mkdir(parents=True, exist_ok=True)
    if dst.suffix.lower() in {".jpg", ".jpeg"}:
        edited.save(dst, quality=95)
    else:
        edited.save(dst, optimize=True)
    return "ok" if changed else "no-korp"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path, help="Скриншот или папка")
    parser.add_argument("-o", "--output", type=Path, help="Файл или папка результата")
    parser.add_argument("--top-fraction", type=float, default=0.12)
    parser.add_argument(
        "--in-place",
        action="store_true",
        help="Перезаписать исходники (иначе пишем *_bez_korp рядом / в -o)",
    )
    args = parser.parse_args(argv)

    if args.input.is_dir():
        inputs = sorted(p for p in args.input.iterdir() if p.suffix.lower() in IMAGE_EXTS)
        out_dir = args.output or args.input.parent
        out_dir.mkdir(parents=True, exist_ok=True)
        if not inputs:
            print(f"Нет изображений в {args.input}", file=sys.stderr)
            return 1
        changed = 0
        for src in inputs:
            dst = src if args.in_place else out_dir / f"{src.stem}_bez_korp{src.suffix}"
            status = process_path(src, dst, top_fraction=args.top_fraction)
            print(f"{src.name}: {status} -> {dst}")
            if status == "ok":
                changed += 1
        print(f"Итого изменено: {changed}/{len(inputs)}")
        return 0 if changed else 2

    src = args.input
    if args.in_place:
        dst = src
    else:
        dst = args.output or src.with_name(f"{src.stem}_bez_korp{src.suffix or '.png'}")
    status = process_path(src, dst, top_fraction=args.top_fraction)
    print(f"{src.name}: {status} -> {dst}")
    return 0 if status == "ok" else 2


if __name__ == "__main__":
    raise SystemExit(main())
