"""The embroidered frames round the home page's margin portraits (components/PortraitRails.tsx): six thin frames,
drawn as stitches, written to website/public/vez/okvir-<n>.svg. The site uses each as a mask over its own red ink
(and frame 4's second thread, okvir-4-plavo.svg, over a deep blue), so the colours follow the light and dark themes.

The motifs are those of South Slavic embroidery: the cross-stitch, the running stitch, the kolo's rhomb and the
eight-pointed star of Zmijanje's work (UNESCO, 2014), the "wolf's teeth" zigzag of a towel's hem, and Zmijanje's
single deep-blue thread. Each frame gives each edge its own part, so none is a plain ring of crosses.

The drawing is in CSS px for a 104 x 138.7 print (6.5rem wide) and reaches OFF px past it on every side; the CSS
scales it with the print. Run: python scripts/make_vez_frames.py
"""
import math
import os

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'website', 'public', 'vez')
W, H = 104.0, 138.667          # the print
OFF = 14.0                     # how far the drawing reaches past it on every side
SIZE = (W + 2 * OFF, H + 2 * OFF)
D6 = 6.0                       # the frame's line stands this far outside the print
STAR_R = 7.0                   # the room a corner star takes on each line


def rect(d):
    """The rectangle d px outside the print: left, top, right, bottom"""
    return OFF - d, OFF - d, OFF + W + d, OFF + H + d


def along(a, b, step):
    """Points from a to b, evenly, about step apart, both ends included"""
    n = max(1, round(math.dist(a, b) / step))
    return [(a[0] + (b[0] - a[0]) * i / n, a[1] + (b[1] - a[1]) * i / n) for i in range(n + 1)]


def diamond_cells(r):
    return [(dx, dy) for dx in range(-r, r + 1) for dy in range(-r, r + 1) if abs(dx) + abs(dy) == r]


def star8_cells(a=2, b=3):
    """The eight-pointed star: a square and a diamond laid over each other, its outline and centre"""
    inside = lambda x, y: (abs(x) <= a and abs(y) <= a) or abs(x) + abs(y) <= b
    cells = [(x, y) for x in range(-b, b + 1) for y in range(-b, b + 1) if inside(x, y)]
    edge = [(x, y) for (x, y) in cells if not all(inside(x + i, y + j) for i, j in [(1, 0), (-1, 0), (0, 1), (0, -1)])]
    return edge + [(0, 0)]


class Frame:
    """The stitches of one frame, in up to two threads: 'red' and 'blue'"""

    def __init__(self):
        self.threads = {'red': [], 'blue': []}

    def line(self, x1, y1, x2, y2, w=0.7, op=1.0, thread='red'):
        self.threads[thread].append(
            f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" stroke-width="{w}" stroke-opacity="{op}"/>')

    def cross(self, cx, cy, s=2.6, w=0.75, thread='red'):
        """A cross-stitch, the under stitch a little lighter than the one over it"""
        h = s / 2
        self.line(cx - h, cy + h, cx + h, cy - h, w, 0.75, thread)
        self.line(cx - h, cy - h, cx + h, cy + h, w, 1.0, thread)

    def run(self, a, z, step=4.0, w=0.7, thread='red'):
        """A running stitch from a to z"""
        pts = along(a, z, step)
        for (x1, y1), (x2, y2) in zip(pts, pts[1:]):
            dx, dy = (x2 - x1) * 0.16, (y2 - y1) * 0.16
            self.line(x1 + dx, y1 + dy, x2 - dx, y2 - dy, w, 1.0, thread)

    def crosses(self, a, z, step=5.2):
        for x, y in along(a, z, step):
            self.cross(x, y)

    def zigzag(self, x1, x2, y, period=7.0, amp=2.6, w=0.8):
        """The wolf's teeth"""
        pts, x, k = [], x1, 0
        while x <= x2 + 0.01:
            pts.append((x, y + (amp if k % 2 else 0)))
            x += period / 2
            k += 1
        for (a, b), (c, d) in zip(pts, pts[1:]):
            self.line(a, b, c, d, w)

    def kolo(self, cx, cy, cells=None, thread='red', cell=2.6):
        """The kolo's rhomb, or another motif of cells"""
        for dx, dy in (cells or diamond_cells(2) + [(0, 0)]):
            self.cross(cx + dx * cell, cy + dy * cell, s=cell * 0.95, w=0.7, thread=thread)

    def star(self, cx, cy, thread='red', cell=1.9):
        for dx, dy in star8_cells(2, 3):
            self.cross(cx + dx * cell, cy + dy * cell, s=1.8, w=0.6, thread=thread)

    def svg(self, thread):
        body = ''.join(self.threads[thread])
        return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{SIZE[0]:.2f}" height="{SIZE[1]:.2f}" '
                f'viewBox="0 0 {SIZE[0]:.2f} {SIZE[1]:.2f}"><g fill="none" stroke="#000" stroke-linecap="round">'
                f'{body}</g></svg>\n')


CORNERS = lambda l, t, r, b: [(l, t), (r, t), (r, b), (l, b)]


def frame_1(f):
    """Kolo, zvezde, zubi: stars in the corners, a running stitch on the sides and the top, broken there by the
    kolo's rhomb, and the wolf's teeth along the bottom"""
    l, t, r, b = rect(D6)
    mid = (l + r) / 2
    for cx, cy in CORNERS(l, t, r, b):
        f.star(cx, cy)
    f.run((l + STAR_R, t), (mid - 11, t))
    f.run((mid + 11, t), (r - STAR_R, t))
    f.kolo(mid, t)
    f.run((l, t + STAR_R), (l, b - STAR_R))
    f.run((r, t + STAR_R), (r, b - STAR_R))
    f.zigzag(l + STAR_R, r - STAR_R, b - 1.3)


def frame_2(f):
    """Krstići oko romba: a running stitch round the print; at the middle of the top and the bottom, three crosses
    on each side of the kolo's rhomb"""
    l, t, r, b = rect(D6)
    mid = (l + r) / 2
    band = 9 + 3 * 5.2
    for y in (t, b):
        f.run((l, y), (mid - band - 2, y))
        f.run((mid + band + 2, y), (r, y))
        for i in range(3):
            f.cross(mid - 11 - i * 5.2, y)
            f.cross(mid + 11 + i * 5.2, y)
        f.kolo(mid, y)
    f.run((l, t), (l, b))
    f.run((r, t), (r, b))


def frame_3(f):
    """Zvezde i zubi: the four stars, a running stitch along the top, the wolf's teeth along the bottom, the sides
    open"""
    l, t, r, b = rect(D6)
    for cx, cy in CORNERS(l, t, r, b):
        f.star(cx, cy)
    f.run((l + STAR_R, t), (r - STAR_R, t), step=4.4)
    f.zigzag(l + STAR_R, r - STAR_R, b - 1.3)


def frame_4(f):
    """Crveno i plavo: a red running stitch round the print, Zmijanje's blue in the corner stars and the rosette at
    the top"""
    l, t, r, b = rect(D6)
    mid = (l + r) / 2
    for cx, cy in CORNERS(l, t, r, b):
        f.star(cx, cy, thread='blue')
    f.run((l + STAR_R, t), (mid - 11, t))
    f.run((mid + 11, t), (r - STAR_R, t))
    f.kolo(mid, t, cells=star8_cells(2, 3), thread='blue')
    f.run((l + STAR_R, b), (r - STAR_R, b))
    f.run((l, t + STAR_R), (l, b - STAR_R))
    f.run((r, t + STAR_R), (r, b - STAR_R))


def frame_5(f):
    """Ivica peškira: a row of crosses along the top, as a towel's embroidered end, a fine running stitch down the
    sides, the wolf's teeth along the bottom, a cross at each lower corner"""
    l, t, r, b = rect(D6)
    f.crosses((l, t), (r, t))
    f.run((l, t + 5), (l, b - 4))
    f.run((r, t + 5), (r, b - 4))
    f.zigzag(l + 4, r - 4, b - 1.3)
    f.cross(l, b)
    f.cross(r, b)


def frame_6(f):
    """Ritam: the stars in the corners and, between them, three crosses then a dash, again and again"""
    l, t, r, b = rect(D6)
    for cx, cy in CORNERS(l, t, r, b):
        f.star(cx, cy)
    for a, z in [((l, t), (r, t)), ((l, b), (r, b)), ((l, t), (l, b)), ((r, t), (r, b))]:
        length = math.dist(a, z)
        ux, uy = (z[0] - a[0]) / length, (z[1] - a[1]) / length
        inner = length - 2 * STAR_R
        unit = 3 * 4.4 + 7.0            # three crosses, then a dash
        n = max(1, int(inner // unit))
        start = STAR_R + (inner - n * unit + 7.0) / 2
        for k in range(n):
            base = start + k * unit
            for i in range(3):
                d = base + i * 4.4
                f.cross(a[0] + ux * d, a[1] + uy * d)
            if k < n - 1:
                d1, d2 = base + 3 * 4.4 - 0.6, base + unit - 2.6
                f.line(a[0] + ux * d1, a[1] + uy * d1, a[0] + ux * d2, a[1] + uy * d2)


FRAMES = [frame_1, frame_2, frame_3, frame_4, frame_5, frame_6]


def main():
    os.makedirs(OUT, exist_ok=True)
    for n, draw in enumerate(FRAMES, 1):
        f = Frame()
        draw(f)
        open(os.path.join(OUT, f'okvir-{n}.svg'), 'w', encoding='utf-8', newline='\n').write(f.svg('red'))
        if f.threads['blue']:
            open(os.path.join(OUT, f'okvir-{n}-plavo.svg'), 'w', encoding='utf-8', newline='\n').write(f.svg('blue'))
    print('frames written to', os.path.normpath(OUT), sorted(os.listdir(OUT)))


main()
