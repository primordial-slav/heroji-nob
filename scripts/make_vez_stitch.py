"""Every portrait frame in counted-thread satin stitch, written to website/public/vez/<n>.svg (and <n>-2.svg for a
second thread), the frame numbers and threads as scripts/make_vez_frames.py gives them (it runs this after writing
website/app/data/vez.json). The stitches and the grid are scripts/vez_stitch_charts.py's.

The eleven frames charted one by one (vez_stitch_charts.CHOSEN: 8, 21, 34, 40, 52, 67, 78, 105, 114, 133, 135) are
taken as they are; the other 125 are composed from make_vez_frames' specs, as it composes the drawn frames: a corner
motif, a band for each edge, a middle motif, each charted once. The rules:
- a chart's '#' is the part's own thread, '+' the frame's other thread (or the same where the frame has one), 'S' the
  band's line, in the thread of the line the spec names with it;
- an edge given only a line, a running stitch or a few scattered marks takes the frame's other edges' band (its marks
  as the second thread), so no edge is bare; a frame with no band at all has one of its set's (FALLBACK);
- no crosses, X's, stars or hooks: crosses become stepped lozenges, stars stepped octagons, the four-petal flower a
  ring of picots, a circle with a cross concentric rings, hooks battlements, turtles kilim medallions.

Run: python scripts/make_vez_stitch.py (or scripts/make_vez_frames.py, which writes the manifest first)
"""
import json
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import make_vez_frames as V                                 # noqa: E402
import vez_stitch_charts as S                               # noqa: E402
from vez_stitch_charts import chart, Grid, E, NX, NY, MID, mask_svg, THREADS  # noqa: E402,F401

APPROVED = {8, 21, 34, 40, 52, 67, 78, 105, 114, 133, 135}

# ================================================================== corners: (chart, mirror, centre's distance out)
LOZ7 = chart("""
...#...
..###..
.#####.
###+###
.#####.
..###..
...#...
""")
OCT9 = chart("""
..#####..
.#######.
##.....##
##.+++.##
##.+++.##
##.+++.##
##.....##
.#######.
..#####..
""")
OCT7 = chart("""
..###..
.#####.
##...##
##.+.##
##...##
.#####.
..###..
""")
KOLO7 = chart("""
...#...
..###..
.##.##.
##.+.##
.##.##.
..###..
...#...
""")
RHOMB9 = chart("""
....#....
...#.#...
..#...#..
.#..+..#.
#..+++..#
.#..+..#.
..#...#..
...#.#...
....#....
""")
STECAK_ROSETTE = chart("""
..#####..
.#.....#.
#..###..#
#.#####.#
#.##+##.#
#.#####.#
#..###..#
.#.....#.
..#####..
""")
CARN = chart("""
#.#.#.#
#######
.#####.
..###..
...#.++
...+++.
...+...
""")
TULIP_C = chart("""
.#...#.
.##.##.
.#####.
..###..
++.+...
.+++...
...+...
""")
KNOT = chart("""
..###..
.#####.
##...##
##.+.##
##...##
.#####.
..###..
""")
FLOWER = chart("""
..#.#..
.#####.
##...##
#..+..#
##...##
.#####.
..#.#..
""")
SQUARE9 = chart("""
#########
#.......#
#...+...#
#..+++..#
#.+++++.#
#..+++..#
#...+...#
#.......#
#########
""")
RINGS9 = chart("""
..#####..
.##...##.
##.....##
#..+++..#
#..+.+..#
#..+++..#
##.....##
.##...##.
..#####..
""")
MATYO = chart("""
..##.##..
.###.###.
##.....##
##.+++.##
...+.+...
##.+++.##
##.....##
.###.###.
..##.##..
""")
SPRIG = chart("""
..###..
.#####.
.#####.
..###..
...+.++
...+++.
.++.+..
.+++...
""")
BIRD = chart("""
.....##..
....#.###
#...###..
##.####..
.#++++#..
..####...
...+.+...
""")
CURL7 = S.CURL
TASSEL = S.TASSEL2

CORNER = {
    'cross': (LOZ7, 'hv', 4), 'star8': (OCT9, 'hv', 4), 'star8s': (OCT7, 'hv', 4),
    'kolo': (S.KOLO9, 'hv', 4), 'kolo1': (KOLO7, 'hv', 4), 'rhomb': (RHOMB9, 'hv', 4), 'rhomb2': (S.ROMA_CORNER, 'hv', 4),
    'stair': (S.SANDZ_CORNER, 'hv', 4), 'wheel': (S.PAG_WHEEL, 'hv', 4), 'rosette': (STECAK_ROSETTE, 'hv', 4),
    'carnation': (CARN, 'hv', 4), 'scarnation': (CARN, 'hv', 4), 'stulip': (TULIP_C, 'hv', 4), 'tulip': (TULIP_C, 'hv', 4),
    'tassel': (TASSEL, 'h', 3), 'scroll': (CURL7, 'hv', 4), 'knot': (KNOT, 'hv', 4), 'eyelet': (S.ROSETTE, 'hv', 4),
    'flower4': (FLOWER, 'hv', 4), 'square': (SQUARE9, 'hv', 4), 'circlecross': (RINGS9, 'hv', 4), 'rose': (S.ROSE, 'hv', 4),
    'matyo': (MATYO, 'hv', 4), 'ring': (RINGS9, 'hv', 4), 'pomegranate': (S.POMEGRANATE, 'hv', 4),
    'sprig': (SPRIG, 'hv', 4), 'bird': (BIRD, 'h', 4),
}

# ================================================================== middles: chart, its last row's distance out
BUTTONS = chart("""
.###..###..###.
##+##.#+#.##+##
.###..###..###.
""")
BUTTONS = chart("""
.###...###...###.
#####.#####.#####
##+##.##+##.##+##
#####.#####.#####
.###...###...###.
""")
TASSELS = chart("""
.###...###.
.###...###.
#####.#####
#.#.#.#.#.#
#.#.#.#.#.#
#.#.#.#.#.#
""")
BIRDS = chart("""
......##.....##......
.....#.###.###.#.....
##...###.....###...##
.##.####.....####.##.
..#++++#.....#++++#..
...####.......####...
""")
LOZ9 = chart("""
....#....
...###...
..#####..
.###+###.
###+++###
.###+###.
..#####..
...###...
....#....
""")
MIDDLE = {
    'kolo': (S.KOLO9, 0), 'kolo1': (KOLO7, 1), 'star8': (OCT9, 0), 'wheel': (S.PAG_WHEEL[:-1] + ['.' * 9], 0),
    'rosette': (STECAK_ROSETTE, 0), 'tulip': (S.TULIP, 1), 'stulip': (S.TULIP, 1), 'carnation': (S.CARNATION, 1),
    'turtle': (S.SANDZ_MIDDLE, 1), 'scrolls': ([a + '.' + a[::-1] for a in CURL7], 2), 'buttons': (BUTTONS, 2),
    'flower4': (FLOWER, 1), 'rose': (S.ROSE, 1), 'sprig': (SPRIG, 1), 'cross': (LOZ9, 0), 'rhomb2': (S.ROMA_MIDDLE, 1),
    'stair': (S.SANDZ_MIDDLE, 1), 'eyelet': (S.ROSETTE, 0), 'pomegranate': (S.POMEGRANATE, 1), 'matyo': (MATYO, 0),
    'birds': (BIRDS, 2), 'square': (SQUARE9, 0), 'circlecross': (RINGS9, 0), 'tassels': (TASSELS, 2),
}

# ================================================================== bands
# rows: the tile, top row outermost; d: its last row's distance out; per: period (the tile's width by default);
# keep: how much of the last tile ends the run (a motif without what comes after it); dbl: rows of a double line
def B(rows, d, per=None, keep=None, prune=False, dbl=(1, 7)):
    ch = chart(rows) if isinstance(rows, str) else rows
    return {'rows': ch, 'd': d, 'per': per or len(ch[0]), 'keep': keep or len(ch[0]), 'prune': prune, 'dbl': dbl}


def wavy(P, amp, thick, mid=4.0, extra=None):
    """a band that waves: thick rows about mid + amp*sin, one period; extra(x, y) -> a char for other cells"""
    rows = {}
    for x in range(P):
        y = mid + amp * math.sin(2 * math.pi * (x + 0.5) / P)
        for t in range(thick):
            rows[(x, int(round(y - (thick - 1) / 2 + t)))] = '#'
    prev = None
    for x in range(P + 1):
        y = int(round(mid + amp * math.sin(2 * math.pi * (x + 0.5) / P)))
        if prev is not None and abs(y - prev) > 1:
            for yy in range(min(y, prev) + 1, max(y, prev)):
                rows[(x % P, yy)] = '#'
        prev = y
    if extra:
        for (x, y), k in extra(P, mid, amp).items():
            rows.setdefault((x % P, y), k)
    ds = [y for _, y in rows]
    lo, hi = min(ds), max(ds)
    out = [''.join(rows.get((x, y), '.') for x in range(P)) for y in range(hi, lo - 1, -1)]
    return out, lo


def bay_dots(P, mid, amp):
    """a small block in each bay of the wave: over the trough, under the crest"""
    q = P // 4
    hi, lo = int(round(mid + amp)), int(round(mid - amp))
    out = {}
    for dx in (0, 1):
        out[(q * 3 + dx - 1, hi - 1)] = '+'
        out[(q * 3 + dx - 1, hi - 2)] = '+'
        out[(q + dx - 1, lo + 1)] = '+'
        out[(q + dx - 1, lo + 2)] = '+'
    return out


WAVE_ROWS, WAVE_D = wavy(12, 1.6, 2, 4.0, bay_dots)
TAPEW_ROWS, TAPEW_D = wavy(16, 1.4, 3, 4.0, lambda P, m, a: {(P // 4 * 3, int(round(m + a)) - 2): '+',
                                                            (P // 4, int(round(m - a)) + 2): '+'})
ROPE = S.braid_chart(12, 6, 3)

BANDS = {
    'runs': B("""
###.
#.##
+++.
#.##
###.
""", 2),
    'rhythm': B("""
.##..##..##.........
####.####.####.SSSSS
.##..##..##.........
""", 3, per=21, keep=14),
    'tape': B("""
..+.....
.+.+....
########
#.#.#.#.
########
......+.
""", 2),
    'tape_wave': B(TAPEW_ROWS, TAPEW_D, prune=True),
    'small_crosses': B("""
.###..+++.
#####+++++
.###..+++.
""", 3),
    'crosses': B("""
...#......
.#####....
###+###.+.
.#####....
...#......
""", 2, per=10, keep=7),
    'triangles': B("""
...#....
..#+#...
.#+++#..
#######.
SSSSSSSS
""", 2, keep=7),
    'rhomb_cross': B("""
...#.......
.##.##..++.
##...##++++
.##.##..++.
...#.......
""", 2, keep=7),
    'rhombs': B("""
+.+.+.+.
...#....
.##.##..
##.+.##S
.##.##..
...#....
+.+.+.+.
""", 1, keep=7),
    'flowers': B("""
.###.....
#####....
##.##.++.
.###.+++.
..+.++...
+++++++++
""", 2, keep=5),
    'wave': B(WAVE_ROWS, WAVE_D, prune=True),
    'teeth': B("""
..#...
.###..
#####.
SSSSSS
+...++
.....+
""", 2, keep=5),
    'chevrons': B("""
...#........
..###.......
.#####...+..
##...##.+++.
SSSSSSSSSSSS
""", 3, keep=7),
    'steps': B("""
...##...
..####..
.##++##.
##++++##
SSSSSSSS
""", 2),
    'lattice': B("""
.###....
#.+.#...
.###....
.....###
#...#.+.
.....###
""", 2, keep=5),
    'scallops': B("""
..###...
.#####..
##.+.##.
SSSSSSSS
""", 3, keep=7),
    'pag': B(S.PAG_BAND, 2, keep=5),
    'leafy': None, 'leafy_line': None, 'vine': None,
    'leafy_flowers': B("""
....##.....###...
..####....#####..
.####.....#+++#..
.##........###...
#...........#....
SSSSSSSSSSSSSSSSS
""", 3, per=17, keep=6),
    'scrolls': B("""
.###....
#...#...
#.#.#...
#..#....
.#......
SSSSSSSS
""", 3),
    'spirals': B("""
.###...###....
#...#.#...#...
#.#.#.#.#.#...
#..#...#..#...
.#.......#....
SSSSSSSSSSSSSS
""", 3),
    'rope': B(ROPE, 1),
    'arcades': B("""
..##..
.#..#.
#....#
#.+..#
#....#
SSSSSS
""", 2),
    'ribbon': B("""
##..+..#
.##...##
..##.##.
+..###..
""", 3),
    'loops': B("""
.##..
#..#.
.##..
SSSSS
""", 3, keep=4),
    'ladder': B("""
SSSSSSSS
.##..++.
.##..++.
.##..++.
SSSSSSSS
""", 2),
    'eyelets': B("""
.###......
#...#.....
#.+.#..##.
#...#.###.
.###.##...
SSSSSSSSSS
""", 2, keep=5),
    'circles_crosses': B("""
.###...+..
#...#.+++.
#.#.#+++++
#...#.+++.
.###...+..
""", 2, keep=5),
    'chain': B("""
..###....
.#...#...
#.....#++
.#...#...
..###....
""", 2, keep=7),
    'birds': B("""
......##.....##.......
.....#.###.###.#......
##...###.....###...##.
.##.####.....####.##..
..#++++#.....#++++#...
...####.......####....
SSSSSSSSSSSSSSSSSSSSSS
""", 2),
    'knit': B("""
#...#.......
##.##.+...+.
.###..++.++.
..#....+++..
........+...
""", 3),
    'hooks': B("""
###.....
###.....
SSSSSSSS
....+++.
....+++.
""", 2),
    'turtles': B("""
..###....
.#+++#...
#+++++#SS
.#+++#...
..###....
""", 2, keep=7),
    'rings': B("""
.###.
#...#
#.+.#
#...#
.###.
""", 2),
    'bands': B("""
########
..+...+.
########
+...+...
########
""", 2),
    'xhubleta': B("""
########
...+....
..+++...
.+++++..
########
........
########
""", 1),
    'pomegranates': B("""
#.#.#.....
.###......
#####.....
#####.....
.###..++..
..#..++++.
SSSSSSSSSS
""", 2, keep=5, dbl=(1,)),
    'matyo_row': B("""
..###......
.#####.....
###.###.++.
##.+.##++..
###.###....
.#####.....
..###......
""", 1, keep=7),
    'oya': B("""
...###...
..#####..
...###...
.........
.#######.
##.....##
SSSSSSSSS
""", 2),
    'basket': B("""
####+.+.
####+.+.
+.+.####
+.+.####
""", 3),
    'dots': B("""
##..+.
##....
...##.
.+.##.
##....
##..+.
""", 2),
    'plait': B(S.PLAIT2, 1, prune=True),
}
THIN = {'line', 'double', 'run', 'line_in', 'line_out', 'sparse_crosses', 'sparse_rhombs'}
OVER = {'fringe_out', 'rcross'}
# frames whose specs give no band anywhere: one of the set's
FALLBACK = {6: 'runs', 7: 'small_crosses', 53: 'crosses'}
EDGE_ALIAS = {'ribbon_out': 'ribbon', 'loops_out': 'loops'}


def run_cells(band, s0, s1, shift=0):
    """the band's cells over s0..s1, centred, as {(s, d): char}"""
    rows, per, keep = band['rows'], band['per'], band['keep']
    h, w = len(rows), len(rows[0])
    span = s1 - s0 + 1
    if span < keep:
        return {}, s0, s0 - 1
    n = (span - keep) // per + 1
    total = (n - 1) * per + keep
    a = s0 + (span - total) // 2
    b = a + total - 1
    cells = {}
    for k in range(n):
        for r, row in enumerate(rows):
            for c, ch in enumerate(row):
                if ch != '.' and (k < n - 1 or c < keep):
                    cells[(a + k * per + c, band['d'] + shift + h - 1 - r)] = ch
    if band['prune']:
        changed = True
        while changed:
            changed = False
            for (s, d) in list(cells):
                if s < a + 3 or s > b - 3:
                    if sum((s + i, d + j) in cells for i in (-1, 0, 1) for j in (-1, 0, 1) if i or j) <= 1:
                        del cells[(s, d)]
                        changed = True
    return cells, a, b


def put(g, side, cells, inks):
    for (s, d), ch in cells.items():
        if ch in inks and inks[ch]:
            g.put(*E(side, s, d), inks[ch])


def vine_cells(s0, s1, kind):
    """the leafy vines of the approved frames: 'leafy_line' as Slavonia's (a line inside, leaves rising), the others
    as Banat's (leaves over and under a stem)"""
    g = {}
    if kind == 'leafy_line':
        for s in range(s0, s1 + 1):
            g[(s, 1)] = 'S'
            g[(s, 3)] = '#'
        leaf, d, per, down = S.LEAF5, 4, 9, None
    else:
        for s in range(s0, s1 + 1):
            g[(s, 4)] = '#'
        leaf, d, per, down = S.LEAF4, 5, 10, S.LEAF4_DOWN
    w = len(leaf[0])
    span = s1 - 1 - s0 + 1
    n = (span - w) // per + 1
    start = s0 + (span - ((n - 1) * per + w)) // 2
    for k in range(n):
        for r, row in enumerate(leaf):
            for c, ch in enumerate(row):
                if ch == '#':
                    g[(start + k * per + c, d + len(leaf) - 1 - r)] = '+' if kind == 'vine_acc' else '#'
        if down and k < n - 1:
            for r, row in enumerate(down):
                for c, ch in enumerate(row):
                    if ch == '#':
                        g[(start + k * per + per // 2 + c, 4 - len(down) + len(down) - 1 - r)] = '#'
    return g


# ================================================================== composing a frame
def parts_of(spec, key):
    p = spec.get(key) or spec.get('s' if key in ('sl', 'sr') else 'tb') or spec.get(key[0])
    if p is None:
        return []
    return [p] if isinstance(p, tuple) else list(p)


def frame_inks(spec):
    return [k for k in THREADS if k in json.dumps(spec)]


def plan(spec, key, n, inks):
    """(band name, main ink, second ink, line ink, double?, fringe ink, line_out ink) for one edge"""
    parts = parts_of(spec, key)
    body = [p for p in parts if p[0] not in THIN and p[0] not in OVER]
    thin = [p for p in parts if p[0] in THIN]
    over = {p[0]: p[1] for p in parts if p[0] in OVER}
    if not body:
        for other in ('tb', 't', 'b', 's'):
            ob = [p for p in (parts_of(spec, other) if other in spec else []) if p[0] not in THIN and p[0] not in OVER]
            if ob:
                body = ob[:1]
                break
    if not body:
        body = [(FALLBACK[n], thin[0][1] if thin else inks[0])]
    if key in ('sl', 'sr') and body[0][0] == 'birds' and not [p for p in parts if p[0] == 'birds']:
        body = [('rhombs', body[0][1])]
    name, ink = body[0]
    acc = None
    if isinstance(ink, tuple):
        ink, acc = ink
    if len(body) > 1:                               # xhubleta: black stripes, red teeth
        names = {b[0] for b in body}
        if names == {'bands', 'teeth'}:
            name = 'xhubleta'
            ink = dict(body)['bands']
            acc = dict(body)['teeth']
    name = EDGE_ALIAS.get(name, name)
    line_ink = None
    dbl = False
    lo = None
    for t, ti in thin:
        if t in ('line', 'double', 'line_in') and line_ink is None:
            line_ink, dbl = ti, t == 'double'
        if t == 'line_out':
            lo = ti
    if name == 'leafy' and line_ink and not dbl:
        name = 'leafy_line'
    if acc is None:
        acc = over.get('rcross')
    if acc is None:
        for t, ti in thin:
            if ti != ink:
                acc = ti
                break
    if acc is None:
        others = [i for i in inks if i != ink]
        acc = others[0] if others else ink
    return name, ink, acc, line_ink or ink, dbl and bool(line_ink), over.get('fringe_out'), lo


def draw_edge(g, side, s0, s1, p):
    name, ink, acc, line_ink, dbl, fringe, line_out = p
    inks = {'#': ink, '+': acc, 'S': line_ink}
    if name in ('leafy', 'leafy_line', 'vine'):
        cells = vine_cells(s0, s1, name)
        put(g, side, cells, inks)
        return
    band = BANDS[name]
    shift = 0
    if fringe:                                     # room for the fringe outside: the band's bare edge rows go
        band = dict(band)
        rows = list(band['rows'])
        while band['d'] + len(rows) - 1 > 5 and not any(k in rows[0] for k in '#S') and not any(k in rows[-1] for k in '#S'):
            rows = rows[1:-1]
            band['d'] += 1
        band['rows'] = rows
        top = band['d'] + len(rows) - 1
        shift = max(min(0, 5 - top), 1 - band['d'])
    cells, a, b = run_cells(band, s0, s1, shift)
    if name == 'pag':                              # the thread carried on to the corner's and the middle's wheels
        for s in list(range(s0, a)) + list(range(b + 1, s1 + 1)):
            cells[(s, 4)] = '#'
    if dbl:
        for d in band['dbl']:
            for s in range(a, b + 1):
                cells.setdefault((s, d), 'S')
    put(g, side, cells, inks)
    if fringe:
        for s in range(a, b + 1):
            g.put(*E(side, s, 6), fringe)
            if (s - a) % 2 == 0:
                for d in (7, 8):
                    g.put(*E(side, s, d), fringe)
    if line_out:
        for s in range(a, b + 1):
            g.put(*E(side, s, 8), line_out)


def compose(spec, n):
    g = Grid()
    inks = frame_inks(spec)
    other = lambda ink: next((i for i in inks if i != ink), ink)
    cname, cink = spec.get('c', ('none', 'red'))
    if cname != 'none':
        ch, mirror, at = CORNER[cname]
        anchor = (1, 2) if cname == 'tassel' else None
        S.stamp_corners(g, ch, {'#': cink, '+': other(cink)}, at, mirror=mirror, anchor=anchor)
    gaps = {}
    for mkey, side in (('m', 't'), ('mb', 'b')):
        if spec.get(mkey):
            name, ink = spec[mkey]
            ch, d = MIDDLE[name]
            S.stamp_middle(g, ch, {'#': ink, '+': other(ink)}, d, side)
            gaps[side] = len(ch[0]) // 2 + 1
    for side, key in (('t', 't'), ('b', 'b'), ('l', 'sl'), ('r', 'sr')):
        p = plan(spec, key, n, inks)
        if cname == 'tassel' and side in 'lr':
            spans = [(3, NY - 1)]
        elif cname == 'none' and side in 'tb':
            spans = S.spans(side, -9, -9, gaps.get(side))
        else:
            spans = S.spans(side, 0, 0, gaps.get(side))
        for s0, s1 in spans:
            draw_edge(g, side, s0, s1, p)
    return g


# ================================================================== the frames drawn whole in make_vez_frames.py
def assisi(ink):
    def draw(g):
        """Punto Assisi: a band of stitches with the motifs left bare, each outlined in black"""
        for side in 'tb':
            voids = [(MID, 3)] + [(MID + k * 13, 2) for k in (-4, -3, -2, -1, 1, 2, 3, 4)]
            for s in range(-8, NX + 8):
                for d in range(2, 7):
                    v = min(abs(s - cx) + abs(d - 4) - r for cx, r in voids)
                    if v > 1:
                        g.put(*E(side, s, d), ink)
                    elif v == 1:
                        g.put(*E(side, s, d), 'ink')
        for side in 'lr':
            voids = [(s, 1) for s in range(4, NY - 3, 8)]
            for s in range(0, NY):
                for d in range(3, 6):
                    v = min(abs(s - cx) + abs(d - 4) - r for cx, r in voids)
                    if v > 1:
                        g.put(*E(side, s, d), ink)
                    elif v == 1:
                        g.put(*E(side, s, d), 'ink')
    return draw


DRAWN = {
    0: {'c': ('star8', 'red'), 't': ('runs', 'red'), 'm': ('kolo', 'red'), 's': ('runs', 'red'), 'b': ('teeth', 'red')},
    1: {'tb': ('crosses', 'red'), 'm': ('kolo', 'red'), 'mb': ('kolo', 'red'), 's': ('runs', 'red')},
    2: {'c': ('star8', 'red'), 't': ('runs', 'red'), 'b': ('teeth', 'red'), 's': ('teeth', 'red')},
    3: {'c': ('star8', 'blue'), 'm': ('star8', 'blue'), 'tb': ('runs', 'red'), 's': ('runs', 'red'),
        '_acc': 'blue'},
    4: {'c': ('cross', 'red'), 't': ('crosses', 'red'), 'b': ('teeth', 'red'), 's': ('runs', 'red')},
    5: {'c': ('star8', 'red'), 'tb': ('rhythm', 'red'), 's': ('rhythm', 'red')},
}


def stitched(n, key, spec):
    if n in DRAWN:
        sp = dict(DRAWN[n])
        acc = sp.pop('_acc', None)
        if acc:                                    # the blue of the stars into the red band
            sp['tb'] = [('runs', 'red'), ('line_in', 'blue')]
            sp['s'] = [('runs', 'red'), ('line_in', 'blue')]
            g = compose(sp, n)
            return g
        return compose(sp, n)
    if 'draw' in spec:                             # Assisi
        g = Grid()
        assisi('red' if n == 126 else 'blue')(g)
        return g
    return compose(dict(spec), n)


def write(out=V.OUT):
    """every frame's threads as masks in out; the threads must be the drawn frame's, which vez.json lists"""
    frames, _ = V.frames_and_sets()
    keys = list(frames)
    chosen = {keys.index(key): draw for _, key, draw in S.CHOSEN}
    assert set(chosen) == APPROVED
    os.makedirs(out, exist_ok=True)
    for old in os.listdir(out):
        if old.endswith('.svg'):
            os.remove(os.path.join(out, old))
    for n, key in enumerate(keys):
        spec = frames[key][1]
        drawn = V.compose(dict(spec))
        want = [k for k in THREADS if drawn.threads[k]]
        if n in chosen:
            g = Grid()
            chosen[n](g)
        else:
            g = stitched(n, key, spec)
        layers = [k for k in THREADS if any(v == k for v in g.cells.values())]
        assert layers == want, (n, key, layers, want)
        for i, ink in enumerate(layers):
            cells = [p for p, v in g.cells.items() if v == ink]
            with open(os.path.join(out, f'{n}{"-2" if i else ""}.svg'), 'w', encoding='utf-8', newline='\n') as fh:
                fh.write(mask_svg(cells))
        clash = sorted({c for c in g.clash if c[0] == 'print'})
        if clash:
            print(n, key, 'stitches on the print:', clash[:6], len(clash))
    print(f'{len(keys)} stitched frames written to {os.path.normpath(out)}')


if __name__ == '__main__':
    write()
