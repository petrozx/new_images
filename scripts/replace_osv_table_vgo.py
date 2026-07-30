#!/usr/bin/env python3
"""Replace OSV data rows in MSFO korr screenshot with VGO table data."""

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

SRC = Path("images/OSV_MSFO_OOO_DO1_korr_bez_korp.png")
OUT = Path("images/OSV_MSFO_OOO_DO1_korr_vgo_bez_korp.png")

# Borders from original header (y=289)
LEFT = 295
COL_INNER = [884, 1049, 1214, 1379, 1544, 1709]
RIGHT = 1874
BORDERS = [LEFT] + COL_INNER + [RIGHT]

HEADER_BOTTOM = 290
ROW_H = 26
N_ROWS = 9
# Original body ends at y=576; wipe fully so no old grid/text remains
CLEAR_BOTTOM = 577

WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
OUTER = (160, 160, 160)
GRID = (207, 207, 207)
TOTAL_BG = (242, 242, 242)

ROWS = [
    ["021001, Денежные средства в банке", "100 000,00", "", "", "", "100 000,00", ""],
    [
        "020212, Торговая дебиторская задолженность: внутригрупповая",
        "",
        "",
        "300 000,00",
        "",
        "300 000,00",
        "",
    ],
    ["050312, Налоги к уплате НДС", "", "", "", "50 000,00", "", "50 000,00"],
    ["050313, Налоги к уплате НП", "", "", "", "50 000,00", "", "50 000,00"],
    [
        "030110, Уставный капитал: внутригрупповой",
        "",
        "100 000,00",
        "",
        "",
        "",
        "100 000,00",
    ],
    [
        "030410, Нераспределенная прибыль текущего периода: внутригрупповая",
        "",
        "",
        "",
        "200 000,00",
        "",
        "200 000,00",
    ],
    [
        "100111, Выручка по консультационным услугам: внутригрупповая",
        "",
        "",
        "250 000,00",
        "250 000,00",
        "",
        "",
    ],
    ["999999, Прибыли и убытки", "", "", "250 000,00", "250 000,00", "", ""],
    [
        "Итого",
        "100 000,00",
        "100 000,00",
        "800 000,00",
        "800 000,00",
        "400 000,00",
        "400 000,00",
    ],
]


def draw_verticals(draw: ImageDraw.ImageDraw, y0: int, y1: int) -> None:
    draw.line([(LEFT, y0), (LEFT, y1)], fill=OUTER, width=1)
    for x in COL_INNER + [RIGHT]:
        draw.line([(x, y0), (x, y1)], fill=GRID, width=1)


def main() -> None:
    img = Image.open(SRC).convert("RGB")
    draw = ImageDraw.Draw(img)
    font = ImageFont.truetype(
        "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf", 12
    )
    font_b = ImageFont.truetype(
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf", 12
    )

    data_bottom = HEADER_BOTTOM + N_ROWS * ROW_H

    # Wipe old body (text + grid + outer left stub) completely
    draw.rectangle([LEFT, HEADER_BOTTOM + 1, RIGHT, CLEAR_BOTTOM], fill=WHITE)

    for i, row in enumerate(ROWS):
        y0 = HEADER_BOTTOM + i * ROW_H
        y1 = y0 + ROW_H
        use_font = font_b if i == N_ROWS - 1 else font
        if i == N_ROWS - 1:
            draw.rectangle([LEFT + 1, y0 + 1, RIGHT - 1, y1 - 1], fill=TOTAL_BG)

        draw.text((LEFT + 8, y0 + 6), row[0], fill=BLACK, font=use_font)
        for c, val in enumerate(row[1:]):
            if not val:
                continue
            x2 = BORDERS[c + 2]
            tw = use_font.getlength(val)
            draw.text((x2 - 6 - tw, y0 + 6), val, fill=BLACK, font=use_font)

        draw.line([(LEFT, y1), (RIGHT, y1)], fill=GRID, width=1)

    # Verticals last so Итого fill does not erase column borders; stop at data_bottom
    draw_verticals(draw, HEADER_BOTTOM, data_bottom)

    img.save(OUT, "PNG")
    print(f"saved {OUT}")


if __name__ == "__main__":
    main()
