"""The embroidered frames round the soldiers' portraits: on the home page's margin portraits
(components/PortraitRails.tsx) and in the record dialog, round the photograph or the grey stand-in.

A soldier's frame comes from a set: the set of the part of the land he was born in (Lika, Banat, Herzegovina,
Sandžak...), each from that part's own needlework and its peoples' together, none named; or the set of the
nationality his record prints (Jews, Albanians, Slovaks, Czechs, Rusyns, Ukrainians, Russians, Turks, Roma, Italians,
Germans and Austrians, Hungarians); or, where neither is known, the neutral set. scripts/build_vez.py gives each soldier his set; the site
picks the frame within it by his name, so he wears the same one wherever he is shown.

The motifs are South Slavic needlework's and the neighbours': Zmijanje's blue embroidery (UNESCO 2014), the stećci
(UNESCO 2016), Idrija's bobbin lace (UNESCO 2018), the lace of Pag (UNESCO 2009), the Pirot and Sjenica-Pešter
kilims, Konavle's silk, the gold work of Slavonia and Montenegro, the Lika cap, the šling of Vojvodina, the
xhubleta (UNESCO 2022), Blaudruck (UNESCO 2018) and the others DESIGN.md lists. A frame is composed from parts, a
motif for the corners, one for each edge, one over the middle of the top (and the bottom); the frames are drawn in
CSS px round a 104 x 138.7 print and reach OFF px past it, and each of a frame's threads (at most two) is its own
SVG, a mask the site fills with that thread's ink, so the colours follow the light and dark themes.

Writes website/app/data/vez.json (each frame's inks, the sets as frame numbers, which set is neutral, which three the
home page shows one face of at most) and data-extraction/places/vez_sets.json (the sets by name, for
scripts/build_vez.py), then has scripts/make_vez_stitch.py write the frames themselves, website/public/vez/<n>.svg (and
<n>-2.svg for a second thread): since 2026-10-28 they are counted-thread satin work composed from the same parts, not
the line drawings this script makes, which --sheet still shows. After changing the sets' order or number, run
scripts/build_vez.py --write again.

Run: python scripts/make_vez_frames.py [--sheet page.html]
"""
import argparse
import json
import math
import os

W, H = 104.0, 138.667
OFF = 14.0
SIZE = (W + 2 * OFF, H + 2 * OFF)
D = 6.0                                    # the frame's line stands this far outside the print
THREADS = ('red', 'blue', 'gold', 'green', 'ink')


def rect(d=D):
    return OFF - d, OFF - d, OFF + W + d, OFF + H + d


def corners(l, t, r, b):
    """tl, tr, br, bl with the angle that turns 'up' outward along the diagonal"""
    return [((l, t), -45), ((r, t), 45), ((r, b), 135), ((l, b), -135)]


def dist(a, b):
    return math.hypot(b[0] - a[0], b[1] - a[1])


def tf(cx, cy, ang):
    a = math.radians(ang)
    return lambda x, y: (cx + x * math.cos(a) - y * math.sin(a), cy + x * math.sin(a) + y * math.cos(a))


class Frame:
    def __init__(self):
        self.threads = {k: [] for k in THREADS}

    def line(self, x1, y1, x2, y2, w=0.55, ink='red'):
        self.threads[ink].append(f'<line x1="{x1:.2f}" y1="{y1:.2f}" x2="{x2:.2f}" y2="{y2:.2f}" stroke-width="{w}"/>')

    def path(self, pts, w=0.5, ink='red', closed=False):
        if len(pts) < 2:
            return
        d = 'M' + ' L'.join(f'{x:.2f},{y:.2f}' for x, y in pts) + (' Z' if closed else '')
        self.threads[ink].append(f'<path d="{d}" stroke-width="{w}"/>')

    def circle(self, cx, cy, r, w=0.45, ink='red'):
        self.threads[ink].append(f'<circle cx="{cx:.2f}" cy="{cy:.2f}" r="{r:.2f}" stroke-width="{w}"/>')

    def ellipse(self, cx, cy, rx, ry, ang, w=0.45, ink='red'):
        self.threads[ink].append(f'<ellipse cx="{cx:.2f}" cy="{cy:.2f}" rx="{rx:.2f}" ry="{ry:.2f}" '
                                 f'transform="rotate({ang:.1f} {cx:.2f} {cy:.2f})" stroke-width="{w}"/>')

    def cross(self, cx, cy, s=2.2, w=0.55, ink='red'):
        h = s / 2
        self.line(cx - h, cy + h, cx + h, cy - h, w * 0.85, ink)
        self.line(cx - h, cy - h, cx + h, cy + h, w, ink)

    def svg(self, ink):
        return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{SIZE[0]:.2f}" height="{SIZE[1]:.2f}" '
                f'viewBox="0 0 {SIZE[0]:.2f} {SIZE[1]:.2f}"><g fill="none" stroke="#000" stroke-linecap="round" '
                f'stroke-linejoin="round">{"".join(self.threads[ink])}</g></svg>\n')


# ------------------------------------------------------------------ an edge: a -> z, n outward, gaps along it
class Edge:
    def __init__(self, a, z, n, gaps=()):
        self.a, self.z, self.n = a, z, n
        self.L = dist(a, z)
        self.u = ((z[0] - a[0]) / self.L, (z[1] - a[1]) / self.L)
        self.gaps = gaps

    def P(self, s, d=0.0):
        return (self.a[0] + self.u[0] * s + self.n[0] * d, self.a[1] + self.u[1] * s + self.n[1] * d)

    def free(self, s, margin=0.0):
        return not any(g0 - margin <= s <= g1 + margin for g0, g1 in self.gaps)

    def spans(self):
        """the stretches outside the gaps"""
        out, s0 = [], 0.0
        for g0, g1 in sorted(self.gaps):
            if g0 > s0:
                out.append((s0, g0))
            s0 = max(s0, g1)
        if s0 < self.L:
            out.append((s0, self.L))
        return [(a, b) for a, b in out if b - a > 0.8]

    def every(self, step, start=None):
        """evenly spaced positions, about step apart, skipping the gaps"""
        n = max(1, round(self.L / step))
        p = self.L / n
        return [(k + 0.5) * p for k in range(n) if self.free((k + 0.5) * p, p * 0.45)], p

    @property
    def angle(self):
        return math.degrees(math.atan2(self.u[1], self.u[0]))


def curve(f, e, fn, ink, w=0.5, step=0.4):
    """a curve along the edge: fn(s) -> distance out, drawn over each free stretch"""
    for s0, s1 in e.spans():
        pts, s = [], s0
        while s <= s1 + 1e-6:
            pts.append(e.P(s, fn(s)))
            s += step
        f.path(pts, w, ink)


# ------------------------------------------------------------------ edge motifs
def e_line(f, e, ink):
    for s0, s1 in e.spans():
        f.line(*e.P(s0), *e.P(s1), 0.5, ink)


def e_double(f, e, ink):
    for s0, s1 in e.spans():
        for d in (-0.75, 0.75):
            f.line(*e.P(s0, d), *e.P(s1, d), 0.4, ink)


def e_run(f, e, ink):
    for s0, s1 in e.spans():
        n = max(1, round((s1 - s0) / 4.0))
        p = (s1 - s0) / n
        for k in range(n):
            f.line(*e.P(s0 + k * p + p * 0.16), *e.P(s0 + (k + 1) * p - p * 0.16), 0.6, ink)


def e_crosses(f, e, ink, step=4.4, size=1.9):
    for s in e.every(step)[0]:
        f.cross(*e.P(s), s=size, w=0.5, ink=ink)


def e_small_crosses(f, e, ink):
    e_crosses(f, e, ink, step=3.4, size=1.4)


def e_teeth(f, e, ink, h=2.4, period=6.0):
    for s0, s1 in e.spans():
        n = max(1, round((s1 - s0) / period))
        p = (s1 - s0) / n
        f.path([e.P(s0 + i * p / 2, h if i % 2 else 0) for i in range(2 * n + 1)], 0.55, ink)


def e_triangles(f, e, ink):
    ss, p = e.every(5.0)
    for s in ss:
        f.path([e.P(s - 1.7), e.P(s, 2.6), e.P(s + 1.7)], 0.5, ink)
        f.path([e.P(s - 0.8), e.P(s, 1.3), e.P(s + 0.8)], 0.4, ink)


def e_chevrons(f, e, ink):
    for s in e.every(4.0)[0]:
        f.path([e.P(s - 1.4, 0.8), e.P(s, 2.4), e.P(s + 1.4, 0.8)], 0.5, ink)


def e_rhombs(f, e, ink, step=4.2, d=1.5):
    ss, p = e.every(step)
    for s in ss:
        h = min(p / 2 - 0.2, d)
        f.path([e.P(s - h), e.P(s, d), e.P(s + h), e.P(s, -d), e.P(s - h)], 0.45, ink)


def e_rhomb_cross(f, e, ink):
    ss, p = e.every(4.2)
    for i, s in enumerate(ss):
        if i % 2:
            f.cross(*e.P(s), s=1.6, w=0.45, ink=ink)
        else:
            f.path([e.P(s - 1.4), e.P(s, 1.4), e.P(s + 1.4), e.P(s, -1.4), e.P(s - 1.4)], 0.45, ink)


def e_lattice(f, e, ink):
    for s0, s1 in e.spans():
        n = max(1, round((s1 - s0) / 3.4))
        p = (s1 - s0) / n
        for ph in (0, 1):
            f.path([e.P(s0 + i * p, 1.4 if (i + ph) % 2 else -1.4) for i in range(n + 1)], 0.4, ink)
        for d in (-1.4, 1.4):
            f.line(*e.P(s0, d), *e.P(s1, d), 0.3, ink)


def e_steps(f, e, ink, h=2.4, tooth=6.0):
    for s0, s1 in e.spans():
        n = max(1, round((s1 - s0) / tooth))
        p = (s1 - s0) / n
        pts = []
        for k in range(n):
            b = s0 + k * p
            for da, dh in [(0, 0), (0, h / 3), (p / 6, h / 3), (p / 6, 2 * h / 3), (p / 3, 2 * h / 3), (p / 3, h),
                           (2 * p / 3, h), (2 * p / 3, 2 * h / 3), (5 * p / 6, 2 * h / 3), (5 * p / 6, h / 3), (p, h / 3), (p, 0)]:
                pts.append(e.P(b + da, dh))
        f.path(pts, 0.45, ink)


def e_hooks(f, e, ink):
    for s0, s1 in e.spans():
        f.line(*e.P(s0), *e.P(s1), 0.45, ink)
    for s in e.every(6.0)[0]:
        f.path([e.P(s - 1.8), e.P(s - 1.8, 2.8), e.P(s + 1.8, 2.8), e.P(s + 1.8, 1.2), e.P(s - 0.2, 1.2), e.P(s - 0.2, 2.0),
                e.P(s + 0.6, 2.0)], 0.45, ink)


def e_turtles(f, e, ink):
    ss, p = e.every(19.0)
    for s0, s1 in e.spans():
        f.line(*e.P(s0), *e.P(s1), 0.45, ink)
    for s in ss:
        turtle(f, *e.P(s), ink, e.angle)


def e_wave(f, e, ink):
    per = e.L / max(2, round(e.L / 11))
    curve(f, e, lambda s: 1.3 * math.sin(2 * math.pi * s / per), ink)


def e_vine(f, e, ink):
    per = e.L / max(2, round(e.L / 17))
    curve(f, e, lambda s: 1.6 * math.sin(2 * math.pi * s / per), ink)
    k = 0
    while (k + 0.25) * per < e.L - 1:
        s = (k + 0.25) * per
        if k % 2 == 0 and e.free(s, 3):
            bx, by = e.P(s, 1.6)
            tip = e.P(s, 3.2)
            f.line(bx, by, *tip, 0.45, ink)
            for ang in (-70, 0, 70):
                rad = math.radians(ang)
                dx = e.n[0] * math.cos(rad) - e.n[1] * math.sin(rad)
                dy = e.n[0] * math.sin(rad) + e.n[1] * math.cos(rad)
                f.circle(tip[0] + dx, tip[1] + dy, 0.75, 0.4, ink)
        k += 1


def e_leafy(f, e, ink, flowers=False):
    per = e.L / max(2, round(e.L / 11))
    curve(f, e, lambda s: 1.2 * math.sin(2 * math.pi * s / per) + 1.6, ink)
    k = 0
    while (k + 0.25) * per < e.L:
        s = (k + 0.25) * per
        if e.free(s, 2.5):
            side = 1 if k % 2 == 0 else -1
            if side == 1:
                base = e.P(s, 2.8)
                if flowers and k % 4 == 0:
                    flower4(f, *e.P(s, 4.4), 1.0, ink)
                else:
                    tip = e.P(s + 1.6, 4.8)
                    m1 = e.P(s + 0.3, 4.0)
                    m2 = e.P(s + 1.4, 3.4)
                    f.path([base, m1, tip, m2, base], 0.4, ink)
        k += 1


def e_leafy_flowers(f, e, ink):
    e_leafy(f, e, ink, flowers=True)


def e_flowers(f, e, ink, leaf_ink=None):
    if isinstance(ink, tuple):
        ink, leaf_ink = ink
    e_line(f, e, leaf_ink or ink)
    for s in e.every(13.0)[0]:
        flower4(f, *e.P(s), 1.4, ink)
        for ds in (-3.6, 3.6):
            if e.free(s + ds):
                cx, cy = e.P(s + ds, 1.1)
                f.ellipse(cx, cy, 1.2, 0.5, e.angle + (30 if ds > 0 else -30), 0.4, leaf_ink or ink)


def e_eyelets(f, e, ink):
    e_line(f, e, ink)
    for s in e.every(16.0)[0]:
        eyelet_flower(f, *e.P(s), 1.7, 5, math.atan2(e.n[1], e.n[0]), ink)
        for ds in (-5.0, 5.0):
            if e.free(s + ds):
                cx, cy = e.P(s + ds, 1.3)
                f.ellipse(cx, cy, 1.1, 0.5, e.angle + (35 if ds > 0 else -35), 0.4, ink)


def e_scallops(f, e, ink):
    e_line(f, e, ink)
    ss, p = e.every(5.6)
    for s in ss:
        f.path([e.P(s - p / 2 + p / 2 * (1 - math.cos(math.pi * i / 12)), 2.3 * math.sin(math.pi * i / 12)) for i in range(13)], 0.5, ink)
        f.circle(*e.P(s, 0.95), 0.55, 0.4, ink)


def e_ladder(f, e, ink):
    for s0, s1 in e.spans():
        for d in (-1.3, 1.3):
            f.line(*e.P(s0, d), *e.P(s1, d), 0.4, ink)
    ss, p = e.every(3.4)
    for s in ss:
        f.ellipse(*e.P(s), p / 2 - 0.5, 0.75, e.angle, 0.4, ink)


def e_loops(f, e, ink, h=3.2, period=4.2):
    for s0, s1 in e.spans():
        n = max(1, round((s1 - s0) / period))
        p = (s1 - s0) / n
        pts, t = [], 0.0
        while t <= 2 * math.pi * n + 1e-6:
            pts.append(e.P(s0 + p * t / (2 * math.pi) - 1.5 * math.sin(t), (h / 2) * (1 - math.cos(t))))
            t += 0.12
        f.path(pts, 0.5, ink)


def e_scrolls(f, e, ink):
    per = e.L / max(2, round(e.L / 11))
    curve(f, e, lambda s: 1.4 * math.sin(2 * math.pi * s / per), ink)
    k = 0
    while (k + 0.25) * per < e.L:
        s = (k + 0.25) * per
        if e.free(s, 2.5):
            cx, cy = e.P(s, 2.9)
            scroll(f, cx, cy, math.atan2(-e.n[1], -e.n[0]), 1.1, 1.5, 1, ink)
        k += 1


def e_rope(f, e, ink):
    s = 0.0
    while s < e.L - 1:
        if e.free(s, 1):
            f.path([e.P(s, -1.2), e.P(s + 1.3, -0.2), e.P(s + 2.0, 1.2)], 0.5, ink)
        s += 2.4


def e_spirals(f, e, ink):
    ss, p = e.every(5.6)
    for s in ss:
        cx, cy = e.P(s, 1.4)
        scroll(f, cx, cy, math.atan2(e.n[1], e.n[0]), 1.25, 1.6, 1, ink)
        f.path([e.P(s - p / 2), e.P(s - 0.4), (cx, cy)], 0.45, ink)


def e_arcades(f, e, ink):
    e_line(f, e, ink)
    ss, p = e.every(5.0)
    for s in ss:
        r = p / 2 - 0.6
        f.path([e.P(s - r)] + [e.P(s - r * math.cos(math.pi * j / 10), 1.2 + r * math.sin(math.pi * j / 10)) for j in range(11)]
               + [e.P(s + r)], 0.4, ink)


def e_tape(f, e, ink):
    e_double(f, e, ink)
    s = 1.0
    while s < e.L - 0.5:
        if e.free(s):
            f.line(*e.P(s, -0.75), *e.P(s, 0.75), 0.3, ink)
        s += 2.2
    for s in e.every(6.5)[0]:
        f.circle(*e.P(s, 2.0), 0.7, 0.4, ink)


def e_tape_wave(f, e, ink):
    per = e.L / max(2, round(e.L / 15))
    for off in (-0.75, 0.75):
        curve(f, e, lambda s, o=off: 1.5 * math.sin(2 * math.pi * s / per) + o, ink, 0.45)
    s = 1.2
    while s < e.L - 1:
        if e.free(s):
            d = 1.5 * math.sin(2 * math.pi * s / per)
            f.line(*e.P(s, d - 0.75), *e.P(s, d + 0.75), 0.3, ink)
        s += 2.2
    k = 0
    while (k + 0.25) * per < e.L:
        s = (k + 0.25) * per
        if e.free(s, 1):
            f.circle(*e.P(s, 3.3), 0.7, 0.4, ink)
        k += 1


def e_pag(f, e, ink):
    e_line(f, e, ink)
    for s in e.every(4.6)[0]:
        f.path([e.P(s - 1.4), e.P(s, 1.9), e.P(s + 1.4)], 0.4, ink)


def e_chain(f, e, ink):
    ss, p = e.every(2.6)
    for s in ss:
        f.ellipse(*e.P(s), 1.6, 0.9, e.angle, 0.45, ink)


def e_fringe(f, e, ink):
    e_line(f, e, ink)
    s = 0.8
    while s < e.L:
        if e.free(s):
            f.line(*e.P(s), *e.P(s, 2.6), 0.35, ink)
        s += 1.7


def e_circles_crosses(f, e, ink):
    ss, p = e.every(4.6)
    for i, s in enumerate(ss):
        if i % 2:
            f.circle(*e.P(s), 1.1, 0.45, ink)
        else:
            f.line(*e.P(s - 1.3), *e.P(s + 1.3), 0.5, ink)
            f.line(*e.P(s, -1.3), *e.P(s, 1.3), 0.5, ink)


def e_dots(f, e, ink):
    e_line(f, e, ink)
    ss, p = e.every(3.2)
    for i, s in enumerate(ss):
        cx, cy = e.P(s, 2.1)
        if i % 2 == 0:
            for k in range(5):
                a = 2 * math.pi * k / 5
                f.circle(cx + 0.9 * math.cos(a), cy + 0.9 * math.sin(a), 0.45, 0.35, ink)
        else:
            f.circle(cx, cy, 0.35, 0.35, ink)


def e_ribbon(f, e, ink):
    for s0, s1 in e.spans():
        n = max(1, round((s1 - s0) / 4.2))
        p = (s1 - s0) / n
        for off in (0.0, 1.3):
            f.path([e.P(s0 + i * p / 2, off + (1.8 if i % 2 else 0)) for i in range(2 * n + 1)], 0.45, ink)


def e_rings(f, e, ink):
    """linked rings, a kolo with no dancers: each ring through the next"""
    ss, p = e.every(2.7)
    for s in ss:
        f.circle(*e.P(s, 0.4), 1.55, 0.45, ink)


def e_knit(f, e, ink):
    s = 1.0
    while s < e.L - 1:
        if e.free(s, 1):
            f.path([e.P(s - 1.3, 1.6), e.P(s, 0.2), e.P(s + 1.3, 1.6)], 0.45, ink)
        s += 2.6


def e_bands(f, e, ink):
    for s0, s1 in e.spans():
        for d in (0.0, 3.2):
            f.line(*e.P(s0, d), *e.P(s1, d), 0.5, ink)


def e_pomegranates(f, e, ink):
    per = e.L / max(2, round(e.L / 13))
    curve(f, e, lambda s: 1.0 * math.sin(2 * math.pi * s / per), ink, 0.45)
    k = 0
    while (k + 0.25) * per < e.L:
        s = (k + 0.25) * per
        if k % 2 == 0 and e.free(s, 3):
            pomegranate(f, *e.P(s, 3.0), e.angle - 90 + (0 if True else 0), ink, 0.75)
        k += 1


def e_birds(f, e, ink):
    e_line(f, e, ink)
    for i, s in enumerate(e.every(9.0)[0]):
        bird(f, *e.P(s, 1.8), e.angle, ink, 1 if i % 2 else -1)


def e_stars(f, e, ink):
    for s in e.every(8.0)[0]:
        star8(f, *e.P(s), ink, 1.3)


def offset(edge_fn, d):
    """an edge motif moved d out from the line"""
    def g(f, e, ink):
        a = (e.a[0] + e.n[0] * d, e.a[1] + e.n[1] * d)
        z = (e.z[0] + e.n[0] * d, e.z[1] + e.n[1] * d)
        edge_fn(f, Edge(a, z, e.n, e.gaps), ink)
    return g


def e_rcross(f, e, ink):
    """small crosses at the rhombs' centres (e_rhombs)"""
    for s in e.every(4.2)[0]:
        f.cross(*e.P(s), s=1.1, w=0.4, ink=ink)


def e_sparse_crosses(f, e, ink):
    for s in e.every(10.0)[0]:
        f.cross(*e.P(s), s=1.3, w=0.45, ink=ink)


def e_sparse_rhombs(f, e, ink):
    for s in e.every(6.5)[0]:
        rhomb(f, *e.P(s, 1.9), 1.3, ink)


def e_matyo_row(f, e, ink):
    for s in e.every(13.0)[0]:
        matyo_rose(f, *e.P(s), 2.2, ink)


def out_angle(e):
    """the angle that turns a motif's 'up' outward from the edge"""
    return math.degrees(math.atan2(e.n[1], e.n[0])) + 90


def e_oya(f, e, ink):
    """Oya, the needle lace of a Turkish kerchief's edge: scallops, a small flower on each"""
    e_line(f, e, ink)
    ss, p = e.every(6.4)
    for i, s in enumerate(ss):
        f.path([e.P(s - p / 2 + p / 2 * (1 - math.cos(math.pi * j / 12)), 1.8 * math.sin(math.pi * j / 12)) for j in range(13)], 0.45, ink)
        if i % 2:
            tulip(f, *e.P(s, 2.6), out_angle(e), ink, 0.42)
        else:
            flower4(f, *e.P(s, 2.9), 0.8, ink)


def e_garden(f, e, ink):
    """The Ottoman garden of tulips and carnations, in turn along the edge"""
    for i, s in enumerate(e.every(9.0)[0]):
        if i % 2:
            carnation(f, *e.P(s, 0.6), out_angle(e), 0.42, ink)
        else:
            tulip(f, *e.P(s, 0.8), out_angle(e), ink, 0.55)


def e_basket(f, e, ink):
    """Basket weave: three strands along the edge, then three across, in turn"""
    ss, p = e.every(3.2)
    for i, s in enumerate(ss):
        h = p / 2 - 0.3
        if i % 2:
            for d in (-1.0, 0.0, 1.0):
                f.line(*e.P(s - h, d), *e.P(s + h, d), 0.35, ink)
        else:
            for ds in (-0.9, 0.0, 0.9):
                f.line(*e.P(s + ds, -1.3), *e.P(s + ds, 1.3), 0.35, ink)


def e_plait(f, e, ink):
    """A plait of two strands crossing"""
    per = e.L / max(2, round(e.L / 5.2))
    for ph in (0.0, math.pi):
        curve(f, e, lambda s, ph=ph: 1.3 * math.sin(2 * math.pi * s / per + ph), ink, 0.5)


EDGES = {k[2:]: v for k, v in globals().items() if k.startswith('e_')}
EDGES.update({'fringe_out': offset(e_fringe, 2.6), 'ribbon_out': offset(e_ribbon, 1.4), 'loops_out': offset(e_loops, 1.6), 'line_out': offset(e_line, 4.2), 'line_in': offset(e_line, -1.2)})


# ------------------------------------------------------------------ point motifs
def turtle(f, cx, cy, ink='red', ang=0.0, s=1.0):
    p = tf(cx, cy, ang)
    d = 2.6 * s
    f.path([p(0, -d), p(d, 0), p(0, d), p(-d, 0), p(0, -d)], 0.5, ink)
    f.path([p(0, -d * 0.45), p(d * 0.45, 0), p(0, d * 0.45), p(-d * 0.45, 0), p(0, -d * 0.45)], 0.4, ink)
    for sx, sy in [(1, 1), (1, -1), (-1, 1), (-1, -1)]:
        x0, y0 = sx * d / 2, sy * d / 2
        f.path([p(x0, y0), p(x0 + sx * 1.5, y0 + sy * 1.5), p(x0 + sx * 2.4, y0 + sy * 1.5)], 0.4, ink)


def scroll(f, cx, cy, start, turns=1.6, rmax=4.0, sgn=1, ink='gold'):
    N = 70
    pts = []
    for k in range(N + 1):
        u = k / N
        a = start + sgn * 2 * math.pi * turns * u
        r = rmax * (1 - u) + 0.5 * u
        pts.append((cx + r * math.cos(a), cy + r * math.sin(a)))
    f.path(pts, 0.5, ink)


def flower4(f, cx, cy, r=1.3, ink='red'):
    for k in range(4):
        a = math.pi / 4 + k * math.pi / 2
        f.ellipse(cx + r * math.cos(a), cy + r * math.sin(a), r, r * 0.5, math.degrees(a), 0.4, ink)
    f.circle(cx, cy, 0.4, 0.35, ink)


def eyelet_flower(f, cx, cy, R=1.9, petals=5, rot=0.0, ink='red'):
    f.circle(cx, cy, 0.6, 0.4, ink)
    for k in range(petals):
        a = 2 * math.pi * k / petals + rot
        f.ellipse(cx + R * math.cos(a), cy + R * math.sin(a), 0.95, 0.5, math.degrees(a), 0.4, ink)


def star8(f, cx, cy, ink='red', cell=1.9):
    inside = lambda x, y: (abs(x) <= 2 and abs(y) <= 2) or abs(x) + abs(y) <= 3
    cells = [(x, y) for x in range(-3, 4) for y in range(-3, 4) if inside(x, y)]
    edge = [(x, y) for (x, y) in cells if not all(inside(x + i, y + j) for i, j in [(1, 0), (-1, 0), (0, 1), (0, -1)])]
    for dx, dy in edge + [(0, 0)]:
        f.cross(cx + dx * cell, cy + dy * cell, s=cell * 0.95, w=0.5, ink=ink)


def kolo(f, cx, cy, ink='red', cell=2.2, r=2):
    cells = [(dx, dy) for dx in range(-r, r + 1) for dy in range(-r, r + 1) if abs(dx) + abs(dy) == r] + [(0, 0)]
    for dx, dy in cells:
        f.cross(cx + dx * cell, cy + dy * cell, s=cell * 0.95, w=0.5, ink=ink)


def wheel(f, cx, cy, R=4.0, ink='red'):
    f.circle(cx, cy, R, 0.5, ink)
    f.circle(cx, cy, 1.3, 0.45, ink)
    for k in range(8):
        a = 2 * math.pi * k / 8 + math.pi / 8
        f.line(cx + 1.3 * math.cos(a), cy + 1.3 * math.sin(a), cx + R * math.cos(a), cy + R * math.sin(a), 0.35, ink)
    for k in range(16):
        a1, a2 = 2 * math.pi * k / 16, 2 * math.pi * (k + 1) / 16
        rr = R * (0.66 if k % 2 else 0.59)
        f.line(cx + rr * math.cos(a1), cy + rr * math.sin(a1), cx + R * 0.62 * math.cos(a2), cy + R * 0.62 * math.sin(a2), 0.3, ink)


def rosette(f, cx, cy, R=4.0, ink='blue'):
    f.circle(cx, cy, R, 0.5, ink)
    for k in range(4):
        a = math.radians(45 + 90 * k)
        f.ellipse(cx + R * 0.4 * math.cos(a), cy + R * 0.4 * math.sin(a), R * 0.4, R * 0.22, math.degrees(a), 0.45, ink)
    f.circle(cx, cy, 0.5, 0.4, ink)


def carnation(f, cx, cy, ang=0, s=1.0, ink='red'):
    p = tf(cx, cy, ang)
    q = lambda pts: [p(x * s, y * s) for x, y in pts]
    f.path(q([(0, 2.2), (0, -2.2)]), 0.5, ink)
    f.path(q([(-2.6, -1.2), (0, -3.4), (2.6, -1.2)]), 0.5, ink)
    f.path(q([(-3.6, -3.6)] + [(-3.6 + k * 0.9, -(7.6 if k % 2 else 5.2)) for k in range(1, 8)] + [(3.6, -3.6)]), 0.5, ink)
    f.path(q([(-3.6, -3.6), (-2.6, -1.2)]), 0.5, ink)
    f.path(q([(3.6, -3.6), (2.6, -1.2)]), 0.5, ink)
    for sg in (-1, 1):
        f.path(q([(0, 0.6), (sg * 2.8, -0.2), (sg * 5.0, 1.2), (sg * 2.6, 1.6), (0, 0.6)]), 0.4, ink)


def tulip(f, cx, cy, ang=0, ink='blue', s=1.0):
    p = tf(cx, cy, ang)
    q = lambda pts: [p(x * s, y * s) for x, y in pts]
    f.path(q([(0, 3.0), (0, -0.6)]), 0.5, ink)
    f.path(q([(-2.4, -0.6), (-2.9, -3.6), (-1.2, -2.4), (0, -4.8), (1.2, -2.4), (2.9, -3.6), (2.4, -0.6)]), 0.5, ink)
    f.path(q([(-2.4, -0.6), (0, 0.4), (2.4, -0.6)]), 0.5, ink)
    for sg in (-1, 1):
        f.path(q([(0, 2.4), (sg * 2.6, 1.0), (sg * 3.4, 2.4), (0, 2.4)]), 0.4, ink)


def stepped(f, cx, cy, cells, ang, ink, c=0.85):
    p = tf(cx, cy, ang)
    for dx, dy in cells:
        f.cross(*p(dx * c, -dy * c), s=c * 0.9, w=0.4, ink=ink)


STEPPED_TULIP = [(0, 0), (0, 1), (0, 2), (-1, 2), (1, 2), (-2, 3), (2, 3), (-1, 3), (1, 3), (0, 3), (-2, 4), (2, 4), (0, 4), (-2, 5), (0, 5), (2, 5)]
STEPPED_CARNATION = [(0, 0), (1, 1), (-1, 1), (1, -1), (-1, -1), (2, 0), (-2, 0), (0, 2), (0, -2), (2, 2), (-2, -2), (2, -2), (-2, 2)]


def stair_rhomb(f, cx, cy, ink='red', R=3, step=1.0):
    n = int(R / step)
    pts = [(cx, cy - R)]
    for i in range(n):                                  # top to right, right to bottom, ...
        pts += [(cx + i * step, cy - R + (i + 1) * step), (cx + (i + 1) * step, cy - R + (i + 1) * step)]
    for i in range(n):
        pts += [(cx + R - i * step, cy + (i + 1) * step), (cx + R - (i + 1) * step, cy + (i + 1) * step)]
    for i in range(n):
        pts += [(cx - i * step, cy + R - (i + 1) * step), (cx - (i + 1) * step, cy + R - (i + 1) * step)]
    for i in range(n):
        pts += [(cx - R + i * step, cy - (i + 1) * step), (cx - R + (i + 1) * step, cy - (i + 1) * step)]
    f.path(pts, 0.45, ink)


def tassel(f, cx, cy, ink='ink'):
    f.circle(cx, cy, 1.5, 0.5, ink)
    for dx in (-1.2, -0.6, 0, 0.6, 1.2):
        f.line(cx + dx * 0.8, cy + 1.4, cx + dx * 1.6, cy + 4.6, 0.35, ink)


def pomegranate(f, cx, cy, ang=0, ink='blue', s=1.0):
    p = tf(cx, cy, ang)
    q = lambda pts: [p(x * s, y * s) for x, y in pts]
    pts = [(1.9 * math.cos(2 * math.pi * k / 24), 0.3 + 1.9 * math.sin(2 * math.pi * k / 24)) for k in range(25)]
    f.path(q(pts), 0.45, ink)
    f.path(q([(-1.0, -1.4), (-0.9, -2.6), (-0.3, -1.9), (0, -2.9), (0.3, -1.9), (0.9, -2.6), (1.0, -1.4)]), 0.45, ink)
    for x, y in [(-0.6, 0.0), (0.6, 0.0), (0, 0.9), (-0.6, 1.2), (0.6, 1.2)]:
        f.circle(*p(x * s, y * s), 0.25, 0.3, ink)


def bird(f, cx, cy, ang=0, ink='red', facing=1, s=1.0):
    p = tf(cx, cy, ang)
    q = lambda pts: [p(facing * x * s, y * s) for x, y in pts]
    f.path(q([(-2.2, 0.4), (-0.8, -0.8), (1.0, -0.8), (2.0, -1.6), (1.8, -0.4), (0.8, 0.6), (-1.2, 0.8), (-2.2, 0.4)]), 0.4, ink)
    f.path(q([(-0.4, -0.6), (0.2, -2.0), (0.8, -0.8)]), 0.35, ink)


def rose(f, cx, cy, R=1.8, ink='red'):
    f.circle(cx, cy, R, 0.45, ink)
    f.circle(cx, cy, R * 0.45, 0.4, ink)
    for k in range(5):
        a = 2 * math.pi * k / 5
        f.line(cx + R * 0.45 * math.cos(a), cy + R * 0.45 * math.sin(a), cx + R * math.cos(a), cy + R * math.sin(a), 0.3, ink)


def matyo_rose(f, cx, cy, R=3.0, ink='red'):
    for k in range(8):
        a = 2 * math.pi * k / 8
        f.ellipse(cx + R * 0.62 * math.cos(a), cy + R * 0.62 * math.sin(a), R * 0.42, R * 0.26, math.degrees(a), 0.4, ink)
    f.circle(cx, cy, R * 0.3, 0.4, ink)


def rhomb(f, cx, cy, d=1.4, ink='red', w=0.45):
    f.path([(cx, cy - d), (cx + d, cy), (cx, cy + d), (cx - d, cy), (cx, cy - d)], w, ink)


def konavle_square(f, cx, cy, ink='green'):
    f.path([(cx - 3, cy - 3), (cx + 3, cy - 3), (cx + 3, cy + 3), (cx - 3, cy + 3), (cx - 3, cy - 3)], 0.45, ink)
    rhomb(f, cx, cy, 3, ink)
    f.cross(cx, cy, s=1.5, w=0.45, ink=ink)


def sprig(f, cx, cy, ang, ink='red', leaf='ink'):
    p = tf(cx, cy, ang)
    f.path([p(0, 2.4), p(0, -2.4)], 0.45, leaf)
    f.circle(*p(0, -3.4), 1.1, 0.45, ink)
    f.circle(*p(0, -3.4), 0.35, 0.35, ink)
    for sg in (-1, 1):
        f.ellipse(*p(sg * 1.4, -0.2), 1.1, 0.45, ang + sg * 40, 0.4, leaf)
        f.circle(*p(sg * 2.2, -2.0), 0.7, 0.4, ink)


# corners: (draw(f, cx, cy, ang, ink), clearance on each edge)
CORNER = {
    'none': (lambda f, x, y, a, i: None, 0.0),
    'cross': (lambda f, x, y, a, i: f.cross(x, y, s=3.2, w=0.6, ink=i), 2.6),
    'star8': (lambda f, x, y, a, i: star8(f, x, y, i), 7.0),
    'star8s': (lambda f, x, y, a, i: star8(f, x, y, i, 1.4), 5.2),
    'kolo': (lambda f, x, y, a, i: kolo(f, x, y, i, 2.2), 5.6),
    'kolo1': (lambda f, x, y, a, i: kolo(f, x, y, i, 1.9, 1), 3.4),
    'rhomb': (lambda f, x, y, a, i: rhomb(f, x, y, 2.6, i, 0.55), 3.4),
    'rhomb2': (lambda f, x, y, a, i: (rhomb(f, x, y, 3.0, i, 0.5), rhomb(f, x, y, 1.4, i, 0.4)), 3.8),
    'stair': (lambda f, x, y, a, i: stair_rhomb(f, x, y, i), 3.8),
    'wheel': (lambda f, x, y, a, i: wheel(f, x, y, 3.6, i), 4.2),
    'rosette': (lambda f, x, y, a, i: rosette(f, x, y, 3.6, i), 4.2),
    'carnation': (lambda f, x, y, a, i: carnation(f, x, y, a, 0.7, i), 4.8),
    'scarnation': (lambda f, x, y, a, i: stepped(f, x, y, STEPPED_CARNATION, 0, i), 3.0),
    'stulip': (lambda f, x, y, a, i: stepped(f, x, y, STEPPED_TULIP, a, i, 0.7), 4.0),
    'tulip': (lambda f, x, y, a, i: tulip(f, x, y, a, i, 0.75), 4.0),
    'tassel': (lambda f, x, y, a, i: tassel(f, x, y, i), 2.2),
    'scroll': (lambda f, x, y, a, i: scroll(f, x, y, math.radians(a - 90) + math.pi, 1.4, 3.4, 1, i), 4.2),
    'knot': (lambda f, x, y, a, i: [f.circle(x + dx * 1.5, y + dy * 1.5, 1.4, 0.45, i) for dx, dy in [(1, 0), (-1, 0), (0, 1), (0, -1)]], 4.4),
    'eyelet': (lambda f, x, y, a, i: eyelet_flower(f, x, y, 2.3, 6, 0, i), 4.0),
    'flower4': (lambda f, x, y, a, i: flower4(f, x, y, 1.8, i), 3.8),
    'square': (lambda f, x, y, a, i: konavle_square(f, x, y, i), 3.6),
    'circlecross': (lambda f, x, y, a, i: (f.circle(x, y, 2.9, 0.5, i), f.line(x - 1.6, y, x + 1.6, y, 0.5, i), f.line(x, y - 1.6, x, y + 1.6, 0.5, i)), 3.4),
    'rose': (lambda f, x, y, a, i: rose(f, x, y, 2.4, i), 3.0),
    'matyo': (lambda f, x, y, a, i: matyo_rose(f, x, y, 3.2, i), 3.8),
    'ring': (lambda f, x, y, a, i: (f.circle(x, y, 4.1, 0.45, i), f.circle(x, y, 2.7, 0.45, i), f.circle(x, y, 0.8, 0.4, i)), 4.6),
    'pomegranate': (lambda f, x, y, a, i: pomegranate(f, x, y, a, i, 1.2), 3.6),
    'sprig': (lambda f, x, y, a, i: sprig(f, x, y, a, i, i), 4.4),
    'bird': (lambda f, x, y, a, i: bird(f, x, y, 0, i, 1 if a in (45, 135) else -1, 1.1), 3.0),
}

# over the middle of the top (or the bottom): (draw(f, cx, cy, out, ink), half the gap it needs)
CENTRE = {
    'kolo': (lambda f, x, y, o, i: kolo(f, x, y, i, 2.2), 6.0),
    'kolo1': (lambda f, x, y, o, i: kolo(f, x, y, i, 1.9, 1), 3.6),
    'star8': (lambda f, x, y, o, i: star8(f, x, y, i, 1.6), 6.0),
    'wheel': (lambda f, x, y, o, i: wheel(f, x, y, 4.0, i), 4.8),
    'rosette': (lambda f, x, y, o, i: rosette(f, x, y, 3.8, i), 4.6),
    'tulip': (lambda f, x, y, o, i: tulip(f, x, y - o * 0.4, 0 if o < 0 else 180, i), 4.6),
    'stulip': (lambda f, x, y, o, i: stepped(f, x, y + o * -1.8, STEPPED_TULIP, 0 if o < 0 else 180, i), 3.4),
    'carnation': (lambda f, x, y, o, i: carnation(f, x, y + 0.0, 0 if o < 0 else 180, 0.85, i), 6.0),
    'turtle': (lambda f, x, y, o, i: turtle(f, x, y, i), 5.2),
    'scrolls': (lambda f, x, y, o, i: [scroll(f, x + sg * 3.4, y + o * 2.8, math.pi / 2 + (0 if sg < 0 else math.pi), 1.3, 2.8, sg, i) for sg in (-1, 1)], 7.0),
    'buttons': (lambda f, x, y, o, i: [f.circle(x + dx, y + o * 2.3, 1.15, 0.45, i) for dx in (-3.2, 0, 3.2)], 5.0),
    'flower4': (lambda f, x, y, o, i: flower4(f, x, y, 1.9, i), 4.0),
    'rose': (lambda f, x, y, o, i: rose(f, x, y, 2.4, i), 3.2),
    'sprig': (lambda f, x, y, o, i: sprig(f, x, y + 0.8 * (-o), 0 if o < 0 else 180, i, i), 4.6),
    'cross': (lambda f, x, y, o, i: f.cross(x, y, s=3.6, w=0.6, ink=i), 2.6),
    'rhomb2': (lambda f, x, y, o, i: (rhomb(f, x, y, 3.2, i, 0.5), rhomb(f, x, y, 1.5, i, 0.4)), 3.8),
    'stair': (lambda f, x, y, o, i: stair_rhomb(f, x, y, i), 3.8),
    'eyelet': (lambda f, x, y, o, i: eyelet_flower(f, x, y, 2.3, 6, 0, i), 3.8),
    'pomegranate': (lambda f, x, y, o, i: pomegranate(f, x, y, 0 if o < 0 else 180, i, 1.3), 3.6),
    'matyo': (lambda f, x, y, o, i: matyo_rose(f, x, y, 3.0, i), 3.6),
    'birds': (lambda f, x, y, o, i: [bird(f, x + sg * 3.4, y + o * 1.6, 0, i, -sg) for sg in (-1, 1)], 6.6),
    'square': (lambda f, x, y, o, i: konavle_square(f, x, y, i), 3.6),
    'circlecross': (lambda f, x, y, o, i: CORNER['circlecross'][0](f, x, y, 0, i), 3.4),
    'tassels': (lambda f, x, y, o, i: [tassel(f, x + dx, y + 0.8, i) for dx in (-2.6, 2.6)], 4.4),
}


def compose(spec):
    """spec: c (corner, ink), t / b / s (top, bottom, sides: an (edge, ink) or a list of them; tb for both top and
    bottom), m / mb (top / bottom middle, ink); or draw: a function of the frame"""
    f = Frame()
    if 'draw' in spec:
        spec['draw'](f)
        used = [k for k in THREADS if f.threads[k]]
        assert len(used) <= 2, used
        return f
    l, t, r, b = rect()
    mid = (l + r) / 2
    cname, cink = spec.get('c', ('none', 'red'))
    draw_c, R = CORNER[cname]
    for (cx, cy), ang in corners(l, t, r, b):
        draw_c(f, cx, cy, ang, cink)
    for key, (a, z, n) in [('t', ((l + R, t), (r - R, t), (0, -1))), ('b', ((l + R, b), (r - R, b), (0, 1))),
                           ('sl', ((l, t + R), (l, b - R), (-1, 0))), ('sr', ((r, t + R), (r, b - R), (1, 0)))]:
        parts = spec.get(key) or spec.get('s' if key.startswith('s') else 'tb') or spec.get(key[0])
        if isinstance(parts, tuple):
            parts = [parts]
        gaps = []
        mkey = {'t': 'm', 'b': 'mb'}.get(key)
        if mkey and spec.get(mkey):
            half = CENTRE[spec[mkey][0]][1]
            gaps = [(mid - half - (l + R), mid + half - (l + R))]
        for name, ink in parts:
            EDGES[name](f, Edge(a, z, n, gaps), ink)
    for mkey, y, o in (('m', t, -1), ('mb', b, 1)):
        if spec.get(mkey):
            name, ink = spec[mkey]
            CENTRE[name][0](f, mid, y, o, ink)
    used = [k for k in THREADS if f.threads[k]]
    assert len(used) <= 2, (spec, used)
    return f


# ------------------------------------------------------------------ frames drawn whole
def zig(f, x1, x2, y, period=7.0, amp=2.6, w=0.8, ink='red'):
    """The wolf's teeth, as the first six frames draw them"""
    pts, x, k = [], x1, 0
    while x <= x2 + 0.01:
        pts.append((x, y + (amp if k % 2 else 0)))
        x += period / 2
        k += 1
    f.path(pts, w, ink)


def run(f, a, z, ink='red'):
    e_run(f, Edge(a, z, (0, -1)), ink)


def along(a, z, step):
    n = max(1, round(dist(a, z) / step))
    return [(a[0] + (z[0] - a[0]) * i / n, a[1] + (z[1] - a[1]) * i / n) for i in range(n + 1)]


def first_six(n):
    """The six frames the margin portraits wore first (now the neutral ones): Kolo, zvezde, zubi; Krstići oko romba;
    Zvezde i zubi; Crveno i plavo; Ivica peškira; Ritam"""
    def draw(f):
        l, t, r, b = rect()
        mid = (l + r) / 2
        S = 7.0                                   # the room a corner star takes on each line
        stars = lambda ink='red': [star8(f, cx, cy, ink) for (cx, cy), _ in corners(l, t, r, b)]
        if n == 1:
            stars()
            run(f, (l + S, t), (mid - 11, t))
            run(f, (mid + 11, t), (r - S, t))
            kolo(f, mid, t, 'red', 2.6)
            run(f, (l, t + S), (l, b - S))
            run(f, (r, t + S), (r, b - S))
            zig(f, l + S, r - S, b - 1.3)
        elif n == 2:
            band = 9 + 3 * 5.2
            for y in (t, b):
                run(f, (l, y), (mid - band - 2, y))
                run(f, (mid + band + 2, y), (r, y))
                for i in range(3):
                    f.cross(mid - 11 - i * 5.2, y, s=2.6, w=0.75)
                    f.cross(mid + 11 + i * 5.2, y, s=2.6, w=0.75)
                kolo(f, mid, y, 'red', 2.6)
            run(f, (l, t), (l, b))
            run(f, (r, t), (r, b))
        elif n == 3:
            stars()
            run(f, (l + S, t), (r - S, t))
            zig(f, l + S, r - S, b - 1.3)
        elif n == 4:
            stars('blue')
            run(f, (l + S, t), (mid - 11, t))
            run(f, (mid + 11, t), (r - S, t))
            star8(f, mid, t, 'blue', 2.6)
            run(f, (l + S, b), (r - S, b))
            run(f, (l, t + S), (l, b - S))
            run(f, (r, t + S), (r, b - S))
        elif n == 5:
            for x, y in along((l, t), (r, t), 5.2):
                f.cross(x, y, s=2.6, w=0.75)
            run(f, (l, t + 5), (l, b - 4))
            run(f, (r, t + 5), (r, b - 4))
            zig(f, l + 4, r - 4, b - 1.3)
            f.cross(l, b, s=2.6, w=0.75)
            f.cross(r, b, s=2.6, w=0.75)
        elif n == 6:
            stars()
            for a, z in [((l, t), (r, t)), ((l, b), (r, b)), ((l, t), (l, b)), ((r, t), (r, b))]:
                length = dist(a, z)
                ux, uy = (z[0] - a[0]) / length, (z[1] - a[1]) / length
                inner = length - 2 * S
                unit = 3 * 4.4 + 7.0              # three crosses, then a dash
                k_n = max(1, int(inner // unit))
                start = S + (inner - k_n * unit + 7.0) / 2
                for k in range(k_n):
                    base = start + k * unit
                    for i in range(3):
                        d = base + i * 4.4
                        f.cross(a[0] + ux * d, a[1] + uy * d, s=2.6, w=0.75)
                    if k < k_n - 1:
                        d1, d2 = base + 3 * 4.4 - 0.6, base + unit - 2.6
                        f.line(a[0] + ux * d1, a[1] + uy * d1, a[0] + ux * d2, a[1] + uy * d2, 0.7)
    return draw


def assisi(ink):
    def draw(f):
        """Assisi work: a band filled with cross-stitch, the motif left bare and outlined in black"""
        l, t, r, b = rect()
        mid = (l + r) / 2
        for y, out in ((t, -1), (b, 1)):
            cy = y + out * 0.95
            for row in (0, 1):
                x = l + 2
                while x <= r - 2:
                    yy = y + out * row * 1.9
                    bare = abs(x - mid) + abs(yy - cy) < 3.4 or any(abs(x - (mid + sx * 22)) + abs(yy - cy) < 2.6 for sx in (-1, 1))
                    if not bare:
                        f.cross(x, yy, s=1.5, w=0.4, ink=ink)
                    x += 1.9
            rhomb(f, mid, cy, 3.0, 'ink')
            for sx in (-1, 1):
                rhomb(f, mid + sx * 22, cy, 2.2, 'ink')
        e_run(f, Edge((l, t + 4), (l, b - 2), (-1, 0)), ink)
        e_run(f, Edge((r, t + 4), (r, b - 2), (1, 0)), ink)
    return draw


def teeth_only(f):
    l, t, r, b = rect()
    e_teeth(f, Edge((l, t), (r, t), (0, -1)), 'red')
    e_teeth(f, Edge((l, b), (r, b), (0, 1)), 'red')


# ------------------------------------------------------------------ the frames, and the sets a soldier's frame comes from
# Frames used by more than one set
SHARED = {
    'havlija': ('Havlija: lale i karanfili', {'c': ('carnation', 'red'), 'tb': ('rhombs', 'red'), 's': ('leafy_flowers', 'gold'), 'm': ('tulip', 'gold')}),
    'havlija-zlato': ('Havlija: zlatni karanfili', {'c': ('carnation', 'gold'), 'tb': ('rhombs', 'red'), 's': ('leafy', 'gold'), 'm': ('tulip', 'red')}),
    'stecak-loza': ('Stećak: loza i rozeta', {'c': ('rosette', 'ink'), 'tb': ('rope', 'ink'), 's': ('vine', 'ink'), 'm': ('rosette', 'ink')}),
    'stecak-spirala': ('Stećak: spirala i arkade', {'c': ('rosette', 'red'), 't': ('spirals', 'red'), 'b': ('arcades', 'red'), 's': ('rope', 'red'), 'm': ('rosette', 'red')}),
    'stecak-plavo': ('Stećak: spirala, plavo', {'c': ('rosette', 'blue'), 't': ('spirals', 'blue'), 'b': ('arcades', 'blue'), 's': ('rope', 'blue'), 'm': ('rosette', 'blue')}),
    'xhubleta': ('Xhubleta', {'tb': [('bands', 'ink'), ('teeth', 'red')], 's': [('line', 'ink'), ('sparse_rhombs', 'red')]}),
    'kosovski': ('Kosovski vez, crveno i zlato', {'c': ('kolo1', 'gold'), 'tb': ('crosses', 'red'), 's': ('crosses', 'red'), 'm': ('kolo1', 'gold'), 'mb': ('kolo1', 'gold')}),
}

# name, then its frames: a key of SHARED, or (title, spec). The neutral set comes first; the sets of the three
# nationalities the home page shows at most one face of are CAPPED.
SETS = [
    ('neutralni', [(t, {'draw': first_six(i)}) for i, t in enumerate(
        ['Kolo, zvezde, zubi', 'Krstići oko romba', 'Zvezde i zubi', 'Crveno i plavo', 'Ivica peškira', 'Ritam'], 1)] + [
        ('Bod napred', {'tb': ('run', 'red'), 's': ('run', 'red')}),
        ('Krstići u uglovima', {'c': ('cross', 'red'), 'tb': ('line_in', 'red'), 's': ('line', 'red')}),
        ('Vučji zubi', {'draw': teeth_only}),
    ]),
    # Slovenija
    ('si-gorenjska', [
        ('Nageljčki', {'c': ('carnation', 'red'), 'tb': ('tape', 'blue'), 's': ('tape', 'blue')}),
        ('Nagelj na vrhu', {'c': ('cross', 'blue'), 'm': ('carnation', 'red'), 'tb': ('small_crosses', 'blue'), 's': ('run', 'red')}),
        ('Nageljčki v križcih', {'c': ('scarnation', 'red'), 'tb': ('crosses', 'blue'), 's': ('line', 'blue'), 'm': ('kolo1', 'red')}),
    ]),
    ('si-primorska', [
        ('Idrijska čipka i nagelj', {'c': ('ring', 'blue'), 'tb': ('tape_wave', 'blue'), 's': ('tape_wave', 'blue'), 'm': ('carnation', 'red')}),
        ('Idrijski trak', {'c': ('ring', 'ink'), 'tb': ('tape', 'ink'), 's': ('tape', 'ink')}),
        ('Čipka, crveno', {'c': ('carnation', 'red'), 'tb': ('tape_wave', 'red'), 's': ('tape', 'red')}),
    ]),
    ('si-dolenjska', [
        ('Belokranjski vez', {'c': ('cross', 'red'), 'tb': [('line', 'red'), ('triangles', 'ink')], 's': ('run', 'red'), 'm': ('star8', 'red'), 'mb': ('star8', 'red')}),
        ('Križci i trouglovi', {'c': ('rhomb2', 'red'), 'tb': ('triangles', 'red'), 's': ('small_crosses', 'ink')}),
        ('Krugovi i krstovi', {'c': ('circlecross', 'ink'), 'tb': ('rhomb_cross', 'red'), 's': ('run', 'ink'), 'm': ('star8', 'red')}),
    ]),
    ('si-stajerska', [
        ('Venac nageljčića', {'c': ('carnation', 'red'), 'tb': ('flowers', 'red'), 's': ('wave', 'blue')}),
        ('Crveno i plavo', {'c': ('flower4', 'red'), 'tb': ('teeth', 'blue'), 's': ('run', 'red'), 'm': ('rose', 'red')}),
        ('Strelice', {'c': ('kolo1', 'blue'), 'tb': ('chevrons', 'red'), 's': ('double', 'blue')}),
    ]),
    # Hrvatska
    ('hr-lika', [
        ('Lička kapa', {'c': ('tassel', 'ink'), 'tb': [('line', 'red'), ('chevrons', 'ink')], 's': [('line', 'red'), ('sparse_crosses', 'ink')]}),
        ('Lička pregača', {'t': [('double', 'red'), ('rhomb_cross', 'ink')], 'b': [('rhomb_cross', 'ink'), ('fringe_out', 'red')], 's': ('run', 'red')}),
        ('Čarape', {'c': ('stair', 'red'), 'tb': ('teeth', 'ink'), 's': ('crosses', 'red')}),
        ('Crveno i crno', {'c': ('tassel', 'ink'), 'tb': ('rhombs', 'red'), 's': ('run', 'ink')}),
    ]),
    ('hr-kordun', [
        ('Romb i krst', {'c': ('rhomb2', 'ink'), 't': ('rhomb_cross', 'red'), 'b': [('rhomb_cross', 'red'), ('fringe_out', 'ink')], 's': ('run', 'ink')}),
        ('Strelice', {'c': ('cross', 'red'), 'tb': ('chevrons', 'red'), 's': ('double', 'ink'), 'm': ('rhomb2', 'ink')}),
        ('Zubi', {'c': ('kolo1', 'red'), 'tb': ('teeth', 'ink'), 's': ('small_crosses', 'red')}),
    ]),
    ('hr-banija', [
        ('Stepenice', {'c': ('stair', 'ink'), 'tb': ('steps', 'red'), 's': ('run', 'ink')}),
        ('Trouglovi', {'c': ('cross', 'ink'), 'tb': ('triangles', 'red'), 's': ('rhombs', 'ink')}),
        ('Rese', {'c': ('tassel', 'red'), 't': ('rhombs', 'ink'), 'b': [('rhombs', 'ink'), ('fringe_out', 'red')], 's': ('line', 'red')}),
    ]),
    ('hr-zagora', [
        ('Vrlika', {'c': ('rhomb', 'gold'), 't': ('teeth', 'red'), 'b': [('teeth', 'red'), ('fringe_out', 'gold')], 's': [('line', 'red'), ('sparse_crosses', 'gold')]}),
        ('Zvezde i zlato', {'c': ('star8s', 'red'), 'tb': ('rhomb_cross', 'gold'), 's': ('run', 'red')}),
        ('Pregača s resama', {'c': ('cross', 'gold'), 't': ('chevrons', 'red'), 'b': [('chevrons', 'red'), ('fringe_out', 'red')], 's': ('double', 'gold')}),
    ]),
    ('hr-dalmacija', [
        ('Paška čipka', {'c': ('wheel', 'red'), 'tb': ('pag', 'red'), 's': ('pag', 'red'), 'm': ('wheel', 'red'), 'mb': ('wheel', 'red')}),
        ('Paška mreža', {'c': ('wheel', 'ink'), 'tb': ('lattice', 'ink'), 's': ('pag', 'ink')}),
        ('Bela čipka', {'c': ('eyelet', 'ink'), 'tb': ('scallops', 'ink'), 's': ('line', 'ink'), 'm': ('wheel', 'ink')}),
    ]),
    ('hr-dubrovnik', [
        ('Konavoski vez', {'c': ('square', 'green'), 'tb': [('rhombs', 'red'), ('rcross', 'green')], 's': [('double', 'red'), ('sparse_crosses', 'green')]}),
        ('Konavle, zeleno', {'c': ('square', 'red'), 'tb': ('rhombs', 'green'), 's': ('double', 'green')}),
        ('Konavle, zlato', {'c': ('star8s', 'red'), 'tb': ('teeth', 'gold'), 's': ('run', 'red'), 'm': ('square', 'gold')}),
    ]),
    ('hr-slavonija', [
        ('Zlatovez', {'c': ('eyelet', 'gold'), 'tb': [('line', 'red'), ('leafy', 'gold')], 's': [('line', 'red'), ('leafy', 'gold')]}),
        ('Zlatni cvetovi', {'c': ('rose', 'red'), 'tb': ('leafy_flowers', 'gold'), 's': ('line', 'gold')}),
        ('Zlatni uvojci', {'c': ('flower4', 'gold'), 'tb': ('scrolls', 'gold'), 's': ('double', 'red'), 'm': ('rose', 'red')}),
    ]),
    ('hr-zagorje', [
        ('Zlato na crvenom', {'c': ('flower4', 'red'), 'tb': [('line', 'red'), ('leafy', 'gold')], 's': ('run', 'gold')}),
        ('Cvetne marame', {'c': ('rose', 'red'), 'tb': ('flowers', 'red'), 's': ('wave', 'red')}),
        ('Grančice', {'c': ('sprig', 'red'), 'tb': ('run', 'gold'), 's': ('leafy', 'gold')}),
    ]),
    ('hr-posavina', [
        ('Cvetovi na plavom', {'c': ('flower4', 'red'), 'tb': ('flowers', ('red', 'blue')), 's': ('flowers', ('red', 'blue'))}),
        ('Plavi cvetovi', {'c': ('flower4', 'blue'), 'tb': ('flowers', ('blue', 'red')), 's': ('run', 'red')}),
        ('Ruže i talas', {'c': ('rose', 'red'), 'tb': ('wave', 'blue'), 's': ('wave', 'blue'), 'm': ('flower4', 'red'), 'mb': ('flower4', 'red')}),
    ]),
    ('hr-istra', [
        ('Mreža', {'c': ('wheel', 'red'), 'tb': ('lattice', 'red'), 's': ('pag', 'red')}),
        ('Festoni', {'c': ('eyelet', 'red'), 'tb': ('scallops', 'red'), 's': ('double', 'red')}),
        ('Bela mreža', {'c': ('kolo1', 'ink'), 'tb': ('lattice', 'ink'), 's': ('run', 'ink')}),
    ]),
    # Bosna i Hercegovina
    ('ba-krajina', [
        ('Zmijanjski vez', {'c': ('kolo', 'blue'), 'tb': ('run', 'blue'), 's': ('crosses', 'blue'), 'm': ('kolo', 'blue'), 'mb': ('kolo', 'blue')}),
        ('Zmijanjske zvezde', {'c': ('star8', 'blue'), 'tb': ('run', 'blue'), 's': ('run', 'blue'), 'm': ('star8', 'blue')}),
        'stecak-loza',
        ('Zmijanje: krstići', {'c': ('kolo1', 'blue'), 'tb': ('crosses', 'blue'), 's': ('small_crosses', 'blue')}),
    ]),
    ('ba-cazin', [
        'havlija', 'stecak-spirala',
        ('Lale', {'c': ('tulip', 'gold'), 'tb': ('rhombs', 'gold'), 's': ('leafy', 'red')}),
    ]),
    ('ba-hercegovina', [
        ('Hercegovačka marama', {'c': ('scarnation', 'red'), 'tb': ('small_crosses', 'ink'), 's': ('small_crosses', 'ink'), 'm': ('stulip', 'red'), 'mb': ('stulip', 'red')}),
        'stecak-loza', 'stecak-spirala',
        ('Marama, plavo', {'c': ('scarnation', 'blue'), 'tb': ('small_crosses', 'red'), 's': ('line', 'blue'), 'm': ('stulip', 'blue')}),
    ]),
    ('ba-srednja', [
        'havlija', 'havlija-zlato', 'stecak-plavo',
        ('Lale u nizu', {'c': ('tulip', 'red'), 'tb': ('leafy_flowers', 'red'), 's': ('rhombs', 'gold')}),
    ]),
    ('ba-tuzla', [
        'havlija', 'stecak-spirala',
        ('Posavska čipka', {'c': ('eyelet', 'ink'), 'tb': ('scallops', 'ink'), 's': ('line', 'ink'), 'm': ('flower4', 'ink')}),
        ('Cvetovi', {'c': ('flower4', 'red'), 'tb': ('flowers', ('red', 'blue')), 's': ('run', 'blue')}),
    ]),
    ('ba-istok', [
        'stecak-loza', 'havlija-zlato', 'stecak-plavo',
        ('Stećak: arkade', {'c': ('rosette', 'ink'), 'tb': ('arcades', 'ink'), 's': ('rope', 'ink')}),
    ]),
    # Crna Gora
    ('me-stara', [
        ('Zlatovez: petlje', {'c': ('scroll', 'gold'), 'tb': [('line', 'gold'), ('loops', 'gold')], 's': [('line', 'gold'), ('loops', 'gold')], 'm': ('scrolls', 'gold')}),
        ('Gajtan i zlato', {'c': ('scroll', 'gold'), 'tb': [('double', 'red'), ('ribbon_out', 'gold')], 's': [('double', 'red'), ('ribbon_out', 'gold')], 'm': ('buttons', 'gold')}),
        ('Dolama', {'c': ('knot', 'ink'), 'tb': [('line', 'red'), ('loops_out', 'ink')], 's': [('line', 'red'), ('loops_out', 'ink')]}),
        ('Zlatni uvojci', {'c': ('knot', 'gold'), 'tb': ('scrolls', 'gold'), 's': ('scrolls', 'gold')}),
    ]),
    ('me-brda', [
        ('Stećak: traka i uže', {'c': ('scroll', 'blue'), 'tb': ('ribbon', 'blue'), 's': ('rope', 'blue')}),
        ('Crveni gajtan', {'c': ('knot', 'red'), 'tb': ('loops', 'red'), 's': ('line', 'ink')}),
        ('Stećak, tamno', {'c': ('rosette', 'ink'), 'tb': ('ribbon', 'ink'), 's': ('rope', 'ink')}),
        ('Zlato na crvenom', {'c': ('knot', 'gold'), 'tb': ('scrolls', 'gold'), 's': ('line', 'red')}),
    ]),
    ('me-boka', [
        ('Dobrotska čipka', {'c': ('eyelet', 'ink'), 'tb': ('scallops', 'ink'), 's': ('ladder', 'ink')}),
        ('Zlato na svili', {'c': ('flower4', 'gold'), 'tb': ('leafy', 'gold'), 's': ('line', 'red')}),
        ('Bokeška mreža', {'c': ('wheel', 'ink'), 'tb': ('lattice', 'ink'), 's': ('line', 'ink')}),
    ]),
    ('sandzak', [
        ('Sjeničko-pešterski ćilim', {'c': ('stair', 'red'), 'tb': ('steps', 'ink'), 's': ('steps', 'ink'), 'm': ('turtle', 'red'), 'mb': ('turtle', 'red')}),
        ('Ćilim: lale', {'c': ('stulip', 'red'), 'tb': ('rhombs', 'ink'), 's': ('steps', 'red'), 'm': ('turtle', 'ink')}),
        'havlija',
        ('Plave lale', {'c': ('tulip', 'blue'), 'tb': ('steps', 'red'), 's': ('rhombs', 'blue')}),
    ]),
    ('albanci', [
        'xhubleta',
        ('Pruge i rombovi', {'c': ('rhomb2', 'red'), 'tb': ('bands', 'ink'), 's': ('crosses', 'red')}),
        'kosovski',
    ]),
    # Srbija, Kosovo, Vojvodina, Makedonija
    ('rs-sumadija', [
        ('Grančice', {'c': ('sprig', 'red'), 'm': ('sprig', 'red'), 'tb': ('small_crosses', 'red'), 's': ('small_crosses', 'red')}),
        ('Kolo: prstenovi', {'c': ('cross', 'red'), 't': ('rings', 'red'), 'b': ('run', 'red'), 'mb': ('kolo', 'red'), 's': ('run', 'red')}),
        ('Kolo, romb', {'c': ('kolo1', 'red'), 'tb': ('crosses', 'red'), 's': ('run', 'ink'), 'm': ('kolo', 'red')}),
        ('Cvetni vez', {'c': ('rose', 'red'), 'tb': ('flowers', ('red', 'ink')), 's': ('wave', 'ink')}),
    ]),
    ('rs-zapad', [
        ('Zlatibor', {'c': ('stair', 'red'), 'tb': ('rhombs', 'red'), 's': ('double', 'blue')}),
        ('Kuke', {'c': ('cross', 'blue'), 'tb': ('hooks', 'red'), 's': ('double', 'blue')}),
        ('Kolo: prstenovi', {'c': ('rhomb2', 'red'), 'tb': ('rings', 'red'), 's': ('run', 'red')}),
    ]),
    ('rs-istok', [
        ('Timok (čarape)', {'c': ('rhomb', 'ink'), 'tb': [('line', 'ink'), ('chevrons', 'red')], 's': ('knit', 'red'), 'm': ('flower4', 'red')}),
        ('Pletivo', {'c': ('stair', 'ink'), 'tb': ('knit', 'red'), 's': ('knit', 'red')}),
        ('Romb i krst', {'c': ('rhomb2', 'red'), 'tb': ('rhomb_cross', 'ink'), 's': ('run', 'red')}),
    ]),
    ('rs-jug', [
        ('Pirotski ćilim: kornjače', {'c': ('stair', 'red'), 'tb': ('turtles', 'red'), 's': ('steps', 'red')}),
        ('Pirotski ćilim: kuke', {'c': ('stair', 'red'), 'tb': ('hooks', 'blue'), 's': ('steps', 'red')}),
        ('Kornjače u sredini', {'c': ('cross', 'red'), 'tb': ('steps', 'ink'), 's': ('steps', 'ink'), 'm': ('turtle', 'red'), 'mb': ('turtle', 'red')}),
        ('Plave stepenice', {'c': ('stair', 'blue'), 'tb': ('turtles', 'red'), 's': ('double', 'blue')}),
    ]),
    ('rs-kosovo', [
        'kosovski',
        ('Romb i zlato', {'c': ('rhomb2', 'gold'), 'tb': ('rhomb_cross', 'red'), 's': ('run', 'red')}),
        'xhubleta',
    ]),
    ('vo-srem', [
        ('Tkane pregače', {'c': ('rhomb', 'ink'), 'tb': ('steps', 'red'), 's': ('double', 'ink')}),
        ('Šling', {'c': ('eyelet', 'red'), 'tb': ('scallops', 'red'), 's': ('scallops', 'red')}),
        ('Belo i zlato', {'c': ('eyelet', 'gold'), 'tb': ('ladder', 'gold'), 's': ('ladder', 'gold')}),
        ('Romb i krst', {'c': ('rhomb2', 'red'), 'tb': ('rhomb_cross', 'ink'), 's': ('line', 'red')}),
    ]),
    ('vo-banat', [
        ('Cvetni vez', {'c': ('rose', 'red'), 'tb': ('flowers', ('red', 'green')), 's': ('wave', 'green')}),
        ('Šling: cvetovi', {'c': ('eyelet', 'blue'), 'tb': ('eyelets', 'blue'), 's': ('eyelets', 'blue')}),
        ('Ruže i lišće', {'c': ('rose', 'red'), 'tb': ('leafy', 'green'), 's': ('leafy', 'green'), 'm': ('rose', 'red'), 'mb': ('rose', 'red')}),
        ('Cvetovi na zelenom', {'c': ('flower4', 'red'), 'tb': ('eyelets', 'red'), 's': ('line', 'green')}),
    ]),
    ('vo-backa', [
        ('Šling: festoni', {'c': ('eyelet', 'red'), 'tb': ('scallops', 'red'), 's': ('scallops', 'red')}),
        ('Šling zlatom', {'c': ('flower4', 'gold'), 'tb': ('scallops', 'gold'), 's': ('ladder', 'gold')}),
        ('Šling: cvetovi', {'c': ('eyelet', 'red'), 'tb': ('eyelets', 'red'), 's': ('line', 'red')}),
        ('Plavi cvetovi', {'c': ('rose', 'blue'), 'tb': ('flowers', ('blue', 'red')), 's': ('run', 'blue')}),
    ]),
    ('mk', [
        ('Krstovi i kolca', {'c': ('circlecross', 'red'), 'tb': ('circles_crosses', 'red'), 's': ('chain', 'ink')}),
        ('Sindžir i potište', {'c': ('kolo1', 'ink'), 'tb': ('chain', 'red'), 's': [('line', 'red'), ('teeth', 'ink')]}),
        ('Ptice', {'c': ('cross', 'red'), 'tb': ('birds', 'red'), 's': ('chain', 'ink')}),
    ]),
    # by the nationality a soldier's record prints
    ('jevreji', [
        ('Šipak (nar)', {'c': ('pomegranate', 'gold'), 'tb': ('pomegranates', 'blue'), 's': ('double', 'blue')}),
        ('Šipak, zlato', {'c': ('pomegranate', 'blue'), 'tb': ('double', 'gold'), 's': ('pomegranates', 'gold'), 'm': ('pomegranate', 'blue')}),
    ]),
    ('slovaci', [
        ('Čičmany', {'c': ('cross', 'ink'), 'tb': ('teeth', 'ink'), 's': ('triangles', 'ink')}),
        ('Slovački cvetni vez', {'c': ('tulip', 'red'), 'tb': ('leafy_flowers', 'green'), 's': ('run', 'red')}),
    ]),
    ('cesi', [
        ('Modrotisk', {'tb': [('dots', 'blue'), ('line_out', 'blue')], 's': [('dots', 'blue'), ('line_out', 'blue')]}),
        ('Moravski cvetovi', {'c': ('flower4', 'red'), 'tb': ('flowers', ('red', 'ink')), 's': ('run', 'ink')}),
    ]),
    ('rusini', [
        ('Rusinski vez', {'c': ('star8s', 'red'), 'tb': ('rhomb_cross', 'ink'), 's': ('run', 'red')}),
        ('Ruže i strelice', {'c': ('rose', 'red'), 'tb': ('chevrons', 'ink'), 's': ('crosses', 'red')}),
    ]),
    ('ukrajinci', [
        ('Vyshyvanka', {'c': ('star8s', 'ink'), 'tb': ('rhombs', 'red'), 's': ('crosses', 'ink'), 'm': ('star8', 'red')}),
        ('Crveno i crno', {'c': ('kolo1', 'red'), 'tb': ('teeth', 'ink'), 's': ('rhombs', 'red')}),
    ]),
    ('rusi', [
        ('Ptice', {'c': ('bird', 'red'), 'tb': ('rhombs', 'red'), 's': ('run', 'red'), 'm': ('birds', 'red')}),
        ('Ptice u nizu', {'c': ('cross', 'red'), 'tb': ('birds', 'red'), 's': ('double', 'red')}),
    ]),
    ('italijani', [
        ('Punto Assisi', {'draw': assisi('red')}),
        ('Punto Assisi, plavo', {'draw': assisi('blue')}),
    ]),
    ('nemci', [
        ('Blaudruck', {'c': ('flower4', 'blue'), 'tb': [('dots', 'blue'), ('line_out', 'blue')], 's': [('dots', 'blue'), ('line_out', 'blue')]}),
        ('Kreuzstich', {'c': ('star8s', 'red'), 'tb': ('crosses', 'red'), 's': ('double', 'blue')}),
    ]),
    ('madjari', [
        ('Matyó', {'c': ('matyo', 'red'), 'tb': ('matyo_row', 'blue'), 's': ('wave', 'blue')}),
        ('Kékfestés', {'c': ('eyelet', 'blue'), 'tb': [('dots', 'blue'), ('line_out', 'blue')], 's': ('line', 'blue')}),
    ]),
    ('turci', [
        ('Oja', {'c': ('tulip', 'red'), 'tb': ('oya', 'red'), 's': ('oya', 'red')}),
        ('Lale i karanfili', {'c': ('carnation', 'red'), 'tb': ('garden', 'red'), 's': ('leafy', 'gold')}),
    ]),
    ('romi', [
        ('Pletena korpa', {'c': ('rhomb2', 'red'), 'tb': ('basket', 'ink'), 's': ('basket', 'ink')}),
        ('Pletenica', {'c': ('knot', 'red'), 'tb': ('plait', 'red'), 's': ('plait', 'red')}),
    ]),
]
CAPPED = ['italijani', 'nemci', 'madjari']

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
OUT = os.path.join(ROOT, 'website', 'public', 'vez')
MANIFEST = os.path.join(ROOT, 'website', 'app', 'data', 'vez.json')
BACKEND = os.path.join(ROOT, 'data-extraction', 'places', 'vez_sets.json')
HEX = {'red': '#8e1f20', 'blue': '#1f2d5a', 'gold': '#8c6a22', 'green': '#2f5d3f', 'ink': '#2a2724'}


def frames_and_sets():
    """every frame once, by key, and each set as the keys of its frames"""
    frames, sets = {}, []
    for name, items in SETS:
        keys = []
        for i, item in enumerate(items, 1):
            if isinstance(item, str):
                key, (title, spec) = item, SHARED[item]
            else:
                key, (title, spec) = f'{name}-{i}', item
            frames.setdefault(key, (title, spec))
            keys.append(key)
        sets.append((name, keys))
    return frames, sets


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--sheet', help='also write an HTML page of every frame, set by set, to this path')
    args = ap.parse_args()
    frames, sets = frames_and_sets()
    keys = list(frames)
    inks, drawn = [], {}
    for key in keys:
        f = compose(dict(frames[key][1]))
        inks.append([k for k in THREADS if f.threads[k]])
        drawn[key] = f
    index = {k: n for n, k in enumerate(keys)}
    names = [name for name, _ in sets]
    manifest = {'frames': inks, 'sets': [[index[k] for k in ks] for _, ks in sets],
                'neutral': names.index('neutralni'), 'capped': [names.index(c) for c in CAPPED]}
    with open(MANIFEST, 'w', encoding='utf-8', newline='\n') as fh:
        fh.write('{\n  "frames": ' + json.dumps(manifest['frames']) + ',\n  "sets": ' + json.dumps(manifest['sets'])
                 + f',\n  "neutral": {manifest["neutral"]},\n  "capped": {json.dumps(manifest["capped"])}\n}}\n')
    with open(BACKEND, 'w', encoding='utf-8', newline='\n') as fh:
        json.dump({'about': 'The embroidered frames\' sets in the order website/app/data/vez.json numbers them '
                            '(scripts/make_vez_frames.py); scripts/build_vez.py gives each soldier one.',
                   'sets': [[name, [[k, frames[k][0]] for k in ks]] for name, ks in sets]},
                  fh, ensure_ascii=False, indent=1)
        fh.write('\n')
    if args.sheet:
        rows = ''
        for name, ks in sets:
            cells = ''.join(
                f'<figure><div class="f"><div class="p"></div>'
                + ''.join(drawn[k].svg(ink).replace('stroke="#000"', f'stroke="{HEX[ink]}"') for ink in inks[index[k]])
                + f'</div><figcaption>{frames[k][0]}</figcaption></figure>' for k in ks)
            rows += f'<section><h2>{name}</h2><div class="row">{cells}</div></section>'
        open(args.sheet, 'w', encoding='utf-8').write(
            '<!doctype html><meta charset="utf-8"><style>body{margin:0;padding:8px 14px;background:#fbfaf8;'
            'font:12.5px Georgia,serif;color:#1c1a18}h2{font-size:14px;font-weight:normal;margin:6px 0 3px}'
            'section{display:inline-block;vertical-align:top;margin-right:22px}.row{display:flex;gap:2px 8px}'
            'figure{margin:0;text-align:center;width:150px}.f{position:relative;width:145px;height:183px}'
            '.f svg{position:absolute;inset:0;width:100%;height:100%}.p{position:absolute;left:15.4px;top:15.4px;'
            'width:114.2px;height:152.3px;background:#d2ccc2}figcaption{line-height:1.15;min-height:2.3em}</style>' + rows)
    print(f'{len(keys)} frames in {len(sets)} sets')
    import make_vez_stitch                         # the frames themselves, stitched
    make_vez_stitch.write(OUT)


if __name__ == '__main__':
    main()
