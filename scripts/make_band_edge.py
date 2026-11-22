"""The red band's lower edge (the home band, and the header on the other pages): the red ends in a stitched hem with
lozenges hanging from it, a large and a small one by turns, in the counted-thread satin stitch of the portraits'
frames (scripts/vez_stitch_charts.py): each cell of the chart is one short horizontal stitch. The user's choice of
2026-11-08 among the mockups of /predlog/rub (C5).

Writes website/public/ornament/rub.svg, a mask the site fills with the band's red (globals.css, "The band's stitched
edge"), so it follows the light and dark themes. The chart's top row is the hem, right under the red; a tile is
24 cells wide, repeated along the edge.

Run: python scripts/make_band_edge.py
"""
import os

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'website', 'public', 'ornament', 'rub.svg')
CELL_W, CELL_H = 1.3, 5 / 6            # a stitch's cell in CSS px: the tile is 31.2 x 5 px

CHART = """
########################
.......##...............
.....######........##...
...##########....######.
.....######........##...
.......##...............
"""


def main():
    rows = [r.strip() for r in CHART.strip('\n').split('\n')]
    w, h = round(len(rows[0]) * CELL_W, 3), round(len(rows) * CELL_H, 3)
    stitches = ''.join(f'M{c * CELL_W + 0.12 * CELL_W:.2f} {r * CELL_H + 0.5 * CELL_H:.2f}H{c * CELL_W + 0.88 * CELL_W:.2f}'
                       for r, row in enumerate(rows) for c, ch in enumerate(row) if ch == '#')
    svg = (f'<svg xmlns="http://www.w3.org/2000/svg" width="{w:g}" height="{h:g}" viewBox="0 0 {w:g} {h:g}">'
           f'<path d="{stitches}" fill="none" stroke="#000" stroke-width="{0.82 * CELL_H:.3f}"/></svg>\n')
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    open(OUT, 'w', encoding='utf-8', newline='\n').write(svg)
    print(os.path.normpath(OUT), f'{w:g} x {h:g}', len(svg), 'bytes')


if __name__ == '__main__':
    main()
