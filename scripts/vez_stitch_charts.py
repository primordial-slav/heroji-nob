"""The portrait frames' stitches: the grid, its charts and the eleven frames charted one by one.

The frames round the portraits (see scripts/make_vez_frames.py) are counted-thread satin work, as the record dialog's
cloth band: each frame is charted on a grid of square cells round the 104 x 138.7 print, which is 69 x 92 cells (a cell 104/69 = 1.507 CSS px; the record dialog shows the frame at about 0.73, so it sews it at 1.11
px, the cloth's stitch), with 9 cells of room outside it (13.6 px of the 14). Every cell is one short horizontal satin
stitch. Charts are written for the top edge, their top row outermost; the other edges take them turned (the sides
transposed, the bottom flipped), and a corner's chart is mirrored into the other corners.

CHOSEN are the eleven frames charted one by one (2026-10-28, approved by the user); scripts/make_vez_stitch.py
composes the other 125 from parts and writes them all.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import make_vez_frames as V                                 # noqa: E402

NX, NY = 69, 92                                            # the print in cells
C = 104.0 / NX                                             # 1.50725 px; 138.667 / 92 is the same
ROOM = 9
MID = NX // 2                                              # the top's middle column (34)
SIZE = (132.0, 166.667)
THREADS = V.THREADS


def chart(s):
    rows = [r.strip() for r in s.strip('\n').split('\n')]
    w = max(len(r) for r in rows)
    return [r.ljust(w, '.') for r in rows]


class Grid:
    def __init__(self):
        self.cells = {}
        self.clash = []

    def put(self, col, row, ink):
        if not (-ROOM <= col < NX + ROOM and -ROOM <= row < NY + ROOM):
            self.clash.append(('out', col, row))
            return
        if 0 <= col < NX and 0 <= row < NY:
            self.clash.append(('print', col, row))
            return
        self.cells[(col, row)] = ink


def E(side, s, d):
    """a cell d out from the print (d = 0 touches it), s along the edge (left to right, top to bottom)"""
    if side == 't':
        return s, -1 - d
    if side == 'b':
        return s, NY + d
    if side == 'l':
        return -1 - d, s
    return NX + d, s


def stamp(g, side, ch, s_left, d_bottom, inks):
    """a chart on an edge: its first column at s_left, its last row at d_bottom (the top row outermost)"""
    h = len(ch)
    for r, line_ in enumerate(ch):
        for c, k in enumerate(line_):
            if k in inks:
                g.put(*E(side, s_left + c, d_bottom + h - 1 - r), inks[k])


def corners(L):
    a = -1 - L
    return {'tl': (a, a), 'tr': (NX + L, a), 'bl': (a, NY + L), 'br': (NX + L, NY + L)}


def stamp_corners(g, ch, inks, at, mirror='hv', anchor=None):
    """the chart's anchor cell (its middle by default) on each corner point, at cells out on both lines; 'h'
    mirrors it left to right on the right-hand corners, 'v' top to bottom on the lower ones"""
    h, w = len(ch), len(ch[0])
    ar, ac = anchor or (h // 2, w // 2)
    for key, (cx, cy) in corners(at).items():
        fx = -1 if 'h' in mirror and key[1] == 'r' else 1
        fy = -1 if 'v' in mirror and key[0] == 'b' else 1
        for r, line_ in enumerate(ch):
            for c, k in enumerate(line_):
                if k in inks:
                    g.put(cx + fx * (c - ac), cy + fy * (r - ar), inks[k])


def stamp_middle(g, ch, inks, d_bottom, sides='tb'):
    w = len(ch[0])
    for side in sides:
        stamp(g, side, ch, MID - w // 2, d_bottom, inks)


def edge_end(side):
    return NX if side in 'tb' else NY


def repeat(g, side, ch, inks, d_bottom, s0, s1, period):
    """the chart again and again, period apart, between s0 and s1 (inclusive), the run centred in it"""
    w = len(ch[0])
    span = s1 - s0 + 1
    if span < w:
        return []
    n = (span - w) // period + 1
    total = (n - 1) * period + w
    start = s0 + (span - total) // 2
    out = []
    for k in range(n):
        stamp(g, side, ch, start + k * period, d_bottom, inks)
        out.append(start + k * period)
    return out


def line(g, side, d, ink, s0, s1, pattern='#', phase=0):
    for s in range(s0, s1 + 1):
        if pattern[(s - s0 + phase) % len(pattern)] == '#':
            g.put(*E(side, s, d), ink)


def spans(side, a, b, gap=None):
    """from a cells past the first corner to b cells before the last; gap: half a middle's width, kept clear"""
    s0, s1 = a, edge_end(side) - 1 - b
    if gap is None:
        return [(s0, s1)]
    return [(s0, MID - gap - 1), (MID + gap + 1, s1)]


TASSEL = chart("""
.###.
#####
.###.
.#.#.
#.#.#
#.#.#
""")

KOLO9 = chart("""
....#....
...###...
..##.##..
.##...##.
##..#..##
.##...##.
..##.##..
...###...
....#....
""")


ROSETTE = chart("""
..##.##..
.###.###.
##.....##
##.###.##
...#.#...
##.###.##
##.....##
.###.###.
..##.##..
""")
LEAF5 = chart("""
....##
..####
.####.
.##...
#.....
""")
LEAF4 = chart("""
...##
.####
####.
#....
""")
LEAF4_DOWN = chart("""
#....
####.
.####
...##
""")

CURL = chart("""
..####.
.#....#
#..##.#
#.#..#.
#.#...#
.#.....
..##...
""")
LOOP = chart("""
.##.
#..#
.##.
""")


ROSE = chart("""
..###..
.#####.
###.###
##.#.##
###.###
.#####.
..###..
""")

POMEGRANATE = chart("""
.#.#.#.
..###..
.#####.
#######
###.###
#######
.#####.
..###..
""")
POM_SMALL = chart("""
#.#.#
.###.
#####
#####
.###.
..#..
""")
POM_LEAF = chart("""
..##
####
""")

TULIP = chart("""
.#...#.
.##.##.
.#####.
..###..
##.#...
.###...
...#...
""")
CARNATION = chart("""
#.#.#.#
#######
.#####.
..###..
...#.##
...###.
...#...
""")


def vine(g, side, ink, s0, s1, d, leaf=LEAF5, period=7, down=None):
    """a stem on row d, leaves leaning forward over it (and, given a chart, under it, between them)"""
    line(g, side, d, ink, s0, s1)
    starts = repeat(g, side, leaf, {'#': ink}, d + 1, s0, s1 - 1, period)
    if down:
        for s in starts[:-1]:
            stamp(g, side, down, s + period // 2, d - len(down), {'#': ink})


# ------------------------------------------------------------------ the frames
def f_slavonija(g):
    """Zlatovez: gold rosettes at the corners, a red line and a gold vine of leaves along it"""
    stamp_corners(g, ROSETTE, {'#': 'gold'}, 4)
    for side in 'tblr':
        line(g, side, 1, 'red', -2, edge_end(side) + 1)
        vine(g, side, 'gold', 0, edge_end(side) - 1, 3, period=9)


def f_crna_gora(g):
    """Zlatovez: petlje: gold curls at the corners and a pair over the middle, a gold cord with loops"""
    L = 3
    stamp_corners(g, CURL, {'#': 'gold'}, 4)
    pair = [a + '.' + a[::-1] for a in CURL]
    stamp_middle(g, pair, {'#': 'gold'}, 2, 't')
    for side in 'tblr':
        gap = 8 if side == 't' else None
        for s0, s1 in spans(side, 0, 0, gap):
            line(g, side, L, 'gold', s0, s1)
            repeat(g, side, LOOP, {'#': 'gold'}, L + 1, s0, s1, 5)


def f_banat(g):
    """Ruže i lišće: red roses at the corners and the middles, green leaves over and under a stem"""
    stamp_corners(g, ROSE, {'#': 'red'}, 4)
    stamp_middle(g, ROSE, {'#': 'red'}, 1)
    for side in 'tblr':
        gap = 5 if side in 'tb' else None
        for s0, s1 in spans(side, 0, 0, gap):
            vine(g, side, 'green', s0, s1, 4, leaf=LEAF4, period=10, down=LEAF4_DOWN)


def f_sipak(g):
    """Šipak (nar): gold pomegranates at the corners, blue pomegranates on a stem above and below, a blue double
    line down the sides"""
    stamp_corners(g, POMEGRANATE, {'#': 'gold'}, 4)
    for side in 'tb':
        line(g, side, 2, 'blue', 0, NX - 1)
        starts = repeat(g, side, POM_SMALL, {'#': 'blue'}, 3, 1, NX - 2, 10)
        for s in starts[:-1]:
            stamp(g, side, POM_LEAF, s + 6, 3, {'#': 'blue'})
    for side in 'lr':
        for d in (2, 4):
            line(g, side, d, 'blue', 0, NY - 1)


def f_lale(g):
    """Lale i karanfili: red carnations at the corners, tulips and carnations in turn on a stem above and below,
    a gold vine down the sides"""
    stamp_corners(g, CARNATION, {'#': 'red'}, 4, mirror='hv')
    for side in 'tb':
        line(g, side, 1, 'red', 1, NX - 2)
        starts = repeat(g, side, CARNATION, {}, 2, 2, NX - 3, 10)
        for k, s in enumerate(starts):
            stamp(g, side, TULIP if k % 2 else CARNATION, s, 2, {'#': 'red'})
    for side in 'lr':
        vine(g, side, 'gold', 1, NY - 2, 3)


TASSEL2 = chart("""
.###.
.###.
#####
#.#.#
#.#.#
#.#.#
#.#.#
""")
LIKA_ARROW = chart("""
...#...
..###..
.#####.
##...##
""")
LIKA_TRIANGLE = chart("""
.#.
###
""")

ZMIJ_LOZENGE = chart("""
...#...
.##.##.
##.#.##
.##.##.
...#...
""")

PAG_BAND = chart("""
..#......
.###...#.
#...#.#.#
#.#.#####
#...#....
.###.....
""")
# the plait: two rows of slanting strands, each tucked under the next
PLAIT2 = chart("""
.##.....
####....
.####.##
..######
##.####.
....####
.....##.
""")
PAG_WHEEL = chart("""
...#.#...
..#####..
.##...##.
##..#..##
.#.#.#.#.
##..#..##
.##...##.
..#####..
...#.#...
""")

SANDZ_CORNER = chart("""
....#....
...###...
..##.##..
.##+++##.
##.+++.##
.##+++##.
..##.##..
...###...
....#....
""")
SANDZ_MIDDLE = chart("""
......#......
....##.##....
..##.+++.##..
##.+++++++.##
..##.+++.##..
....##.##....
......#......
""")
# the kilim band by its phase along the edge (6 cells), rows d6 to d2; '+' black, '#' red; black lines on d7 and d1
SANDZ_PHASE = ['++.#.+', '+.###.', '.#####', '+.###.', '++.#.+']

TOOTH_UP = chart("""
..#..
.###.
#####
""")
NEUTRAL_CORNER = chart("""
....#....
...#.#...
..#.#.#..
.#.###.#.
#.#####.#
.#.###.#.
..#.#.#..
...#.#...
....#....
""")
NEUTRAL_MIDDLE = chart("""
......#......
.....###.....
....#####....
...##...##...
..##..#..##..
.##..###..##.
#############
""")

ROMA_CORNER = chart("""
....#....
...###...
..##.##..
.##.#.##.
##.#.#.##
.##.#.##.
..##.##..
...###...
....#....
""")
ROMA_MIDDLE = chart("""
......#......
....##.##....
..##..#..##..
##..##.##..##
..##..#..##..
....##.##....
......#......
""")


def braid_chart(P=12, H=6, th=3):
    """two strands as sine waves half a period apart, each a run of th stitches, crossing twice a period; at each
    crossing one strand passes over whole and the other breaks off a cell short of it, over and under in turn. One
    period, from a crossing to the next but one, so the runs start and end at a crossing"""
    import math
    n = 3
    W = P * n

    def track(ph):
        cells = set()
        for x10 in range(W * 10):
            x = x10 / 10
            y = (H - 1) / 2 * (1 - math.cos(2 * math.pi * x / P + ph))
            for k in range(th):
                xx = int(x) + k - th // 2
                if 0 <= xx < W:
                    cells.add((xx, int(round(y))))
        return cells
    A, B = track(0.0), track(math.pi)
    cells = A | B
    for i in range(2 * n):
        xc = P / 4 + i * P / 2
        over, under = (A, B) if i % 2 == 0 else (B, A)
        near = [(ox, oy) for ox, oy in over if abs(ox - xc) <= th + 2]
        for (x, y) in under:
            if abs(x - xc) <= th and (x, y) not in over and any(abs(x - ox) <= 1 and abs(y - oy) <= 1 for ox, oy in near):
                cells.discard((x, y))
    x0 = P + P // 4
    return [''.join('#' if (x, y) in cells else '.' for x in range(x0, x0 + P)) for y in range(H)]


def band_ends(g, side, d, ink, s0, s1, starts, w):
    """the row d carried on from s0 to the first motif and from the last to s1"""
    if not starts:
        return
    line(g, side, d, ink, s0, starts[0] - 1)
    line(g, side, d, ink, starts[-1] + w, s1)


def f_teeth(g):
    """Vučji zubi: a concentric lozenge at each corner, a large tooth over the middle of the top and the bottom,
    and on every edge the wolf's teeth in two rows, outward and inward, interlocking along a line"""
    stamp_corners(g, NEUTRAL_CORNER, {'#': 'red'}, 4)
    stamp_middle(g, NEUTRAL_MIDDLE, {'#': 'red'}, 1)
    down = TOOTH_UP[::-1]
    for side in 'tblr':
        for s0, s1 in spans(side, 0, 0, 7 if side in 'tb' else None):
            line(g, side, 4, 'red', s0, s1)
            starts = repeat(g, side, TOOTH_UP, {'#': 'red'}, 5, s0, s1, 6)
            for s in starts[:-1]:
                stamp(g, side, down, s + 3, 1, {'#': 'red'})


def f_lika_kapa(g):
    """Lička kapa: a tassel, knot and fringe, hanging at each corner; on every edge a red line with black arrows and
    small red stepped triangles between them"""
    L = 3
    stamp_corners(g, TASSEL2, {'#': 'ink'}, L, mirror='h', anchor=(1, 2))
    for side in 'tblr':
        s0, s1 = (0, NX - 1) if side in 'tb' else (3, NY - 1)
        line(g, side, L, 'red', s0, s1)
        starts = repeat(g, side, LIKA_ARROW, {'#': 'ink'}, L + 1, s0, s1, 12)
        for s in starts[:-1]:
            stamp(g, side, LIKA_TRIANGLE, s + 8, L + 1, {'#': 'red'})


def f_zmijanje(g):
    """Zmijanjski vez: blue lozenge rings at the corners and over the middles, and between them a chain of stepped
    lozenges, each with its eye, between two dotted rows"""
    L = 4
    stamp_corners(g, KOLO9, {'#': 'blue'}, L)
    stamp_middle(g, KOLO9, {'#': 'blue'}, 0)
    for side in 'tblr':
        for s0, s1 in spans(side, 0, 0, 5 if side in 'tb' else None):
            starts = repeat(g, side, ZMIJ_LOZENGE, {'#': 'blue'}, 2, s0, s1, 8)
            for s in starts[:-1]:
                g.put(*E(side, s + 7, 4), 'blue')
            band_ends(g, side, 4, 'blue', s0, s1, starts, 7)
            for d in (1, 7):
                line(g, side, d, 'blue', s0 + 1, s1 - 1, '#.', phase=(s0 + 1 - starts[0]) % 2)


def f_pag(g):
    """Paška čipka: lace wheels with a solid rim, a stepped eye and picots at the corners and over the middles;
    along every edge small wheels on the thread, a cluster of picots between them"""
    L = 4
    stamp_corners(g, PAG_WHEEL, {'#': 'red'}, L)
    stamp_middle(g, PAG_WHEEL[:-1] + ['.' * 9], {'#': 'red'}, 0)
    for side in 'tblr':
        for s0, s1 in spans(side, 0, 0, 5 if side in 'tb' else None):
            starts = repeat(g, side, PAG_BAND, {'#': 'red'}, 2, s0, s1, 9)
            band_ends(g, side, L, 'red', s0, s1, starts, 9)


def f_sandzak(g):
    """Sjeničko-pešterski ćilim: red stepped lozenges with a black core at the corners and over the middles; on every
    edge a kilim border, red lozenges and black teeth in turn between two black lines"""
    stamp_corners(g, SANDZ_CORNER, {'#': 'red', '+': 'ink'}, 4)
    stamp_middle(g, SANDZ_MIDDLE, {'#': 'red', '+': 'ink'}, 1)
    for side in 'tblr':
        for s0, s1 in spans(side, 0, 0, 7 if side in 'tb' else None):
            span = s1 - s0 + 1
            k = (span - 1) // 6
            a = s0 + (span - (6 * k + 1)) // 2
            b = a + 6 * k
            for d in (1, 7):
                line(g, side, d, 'ink', a, b)
            for s in range(a, b + 1):
                ph = (s - a) % 6
                for r, row in enumerate(SANDZ_PHASE):
                    kk = row[ph]
                    if kk == '#':
                        g.put(*E(side, s, 6 - r), 'red')
                    elif kk == '+' and (a < s < b or ph == 0):
                        g.put(*E(side, s, 6 - r), 'ink')


def f_plait(g):
    """Pletenica: a double lozenge at each corner and a wide one over the middles, and along every edge a plait,
    two rows of slanting strands, each tucked under the next"""
    stamp_corners(g, ROMA_CORNER, {'#': 'red'}, 4)
    stamp_middle(g, ROMA_MIDDLE, {'#': 'red'}, 1)
    h, w, period = len(PLAIT2), len(PLAIT2[0]), 8
    for side in 'tblr':
        for s0, s1 in spans(side, 0, 0, 7 if side in 'tb' else None):
            span = s1 - s0 + 1
            n = (span - w) // period + 1
            a = s0 + (span - ((n - 1) * period + w)) // 2
            b = a + (n - 1) * period + w - 1
            cells = {(a + k * period + c, 1 + h - 1 - r) for k in range(n)
                     for r, row in enumerate(PLAIT2) for c, ch in enumerate(row) if ch == '#'}
            # the strands cut at either end of the run: wear their loose ends away
            changed = True
            while changed:
                changed = False
                for (s, d) in list(cells):
                    if s < a + 3 or s > b - 3:
                        if sum((s + i, d + j) in cells for i in (-1, 0, 1) for j in (-1, 0, 1) if i or j) <= 1:
                            cells.discard((s, d))
                            changed = True
            for s, d in cells:
                g.put(*E(side, s, d), 'red')


# (set, the frame's key in make_vez_frames.SETS, its drawing)
CHOSEN = [
    ('neutralni', 'neutralni-9', f_teeth),
    ('hr-lika', 'hr-lika-1', f_lika_kapa),
    ('ba-krajina', 'ba-krajina-1', f_zmijanje),
    ('hr-dalmacija', 'hr-dalmacija-1', f_pag),
    ('hr-slavonija', 'hr-slavonija-1', f_slavonija),
    ('me-stara', 'me-stara-1', f_crna_gora),
    ('sandzak', 'sandzak-1', f_sandzak),
    ('vo-banat', 'vo-banat-3', f_banat),
    ('jevreji', 'jevreji-1', f_sipak),
    ('turci', 'turci-2', f_lale),
    ('romi', 'romi-2', f_plait),
]


def mask_svg(cells):
    """the cells as a mask: each a horizontal satin stitch, as bands/stitch.py's mask_svg"""
    els = []
    for col, row in sorted(cells, key=lambda p: (p[1], p[0])):
        x, y = 14 + col * C, 14 + row * C
        els.append(f'M{x + 0.12 * C:.2f} {y + 0.5 * C:.2f}H{x + 0.88 * C:.2f}')
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{SIZE[0]:.2f}" height="{SIZE[1]:.2f}" '
            f'viewBox="0 0 {SIZE[0]:.2f} {SIZE[1]:.2f}"><path d="{"".join(els)}" fill="none" stroke="#000" '
            f'stroke-width="{0.8 * C:.3f}" stroke-linecap="butt"/></svg>\n')
