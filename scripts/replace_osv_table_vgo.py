#!/usr/bin/env python3
"""Replace OSV data rows in MSFO korr screenshot with VGO table data."""

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

SRC = Path("images/OSV_MSFO_OOO_DO1_korr_bez_korp.png")
OUT = Path("images/OSV_MSFO_OOO_DO1_korr_vgo_bez_korp.png")

COL = [296, 884, 1049, 1214, 1379, 1544, 1709, 1874]
HEADER_BOTTOM = 290
ROW_H = 26
N_ROWS = 9
CLEAR_BOTTOM = 577

WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GRID = (180, 180, 180)
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


def main() -> None:
    img = Image.open(SRC).convert("RGB")
    draw = ImageDraw.Draw(img)
    font = ImageFont.truetype(
        "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf", 12
    )
    font_b = ImageFont.truetype(
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf", 12
    )

    left, right = COL[0], COL[-1]
    data_bottom = HEADER_BOTTOM + N_ROWS * ROW_H

    draw.rectangle([left, HEADER_BOTTOM + 1, right, CLEAR_BOTTOM], fill=WHITE)
    for x in COL:
        draw.line([(x, HEADER_BOTTOM), (x, CLEAR_BOTTOM)], fill=GRID, width=1)

    for i, row in enumerate(ROWS):
        y0 = HEADER_BOTTOM + i * ROW_H
        y1 = y0 + ROW_H
        use_font = font_b if i == N_ROWS - 1 else font
        if i == N_ROWS - 1:
            draw.rectangle([left + 1, y0 + 1, right - 1, y1 - 1], fill=TOTAL_BG)
        draw.line([(left, y1), (right, y1)], fill=GRID, width=1)

        draw.text((COL[0] + 6, y0 + 6), row[0], fill=BLACK, font=use_font)
        for c, val in enumerate(row[1:]):
            if not val:
                continue
            x2 = COL[c + 2]
            tw = use_font.getlength(val)
            draw.text((x2 - 6 - tw, y0 + 6), val, fill=BLACK, font=use_font)

    draw.line([(left, data_bottom), (right, data_bottom)], fill=GRID, width=1)
    img.save(OUT, "PNG")
    print(f"saved {OUT}")


if __name__ == "__main__":
    main()
