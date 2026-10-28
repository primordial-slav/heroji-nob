"""The oak sprig in the middle of the section rules (.unit-year-head: "Šta je novo", "Istražite", the years on the
Jedinice page): three English oak leaves and two acorns on a thin red rule.

Writes website/public/ornament/hrast.svg, a mask: the site fills it with the rule's red, so it follows the light
and dark themes. The leaves' midribs and the acorns' rims are cut out of it. Drawn in CSS px on a 44 x 14 box whose
rule runs at y = 9 (globals.css, .unit-year-head::after).

Run: python scripts/make_rule_sprig.py
"""
import math
import os

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'website', 'public', 'ornament', 'hrast.svg')
W, H, RULE = 44.0, 14.0, 9.0

# an English oak's leaf, along x from the stalk (0) to the tip (1): the upper edge, lobes and notches
OAK = [(0.00, 0.00), (0.035, 0.11), (0.08, 0.07), (0.13, 0.05), (0.19, 0.19), (0.25, 0.22), (0.30, 0.10), (0.37, 0.27),
       (0.45, 0.30), (0.50, 0.13), (0.57, 0.31), (0.65, 0.31), (0.69, 0.14), (0.76, 0.27), (0.83, 0.24), (0.86, 0.12),
       (0.92, 0.17), (0.98, 0.09), (1.00, 0.00)]


def catmull(pts, n=5):
    out = []
    for i in range(len(pts) - 1):
        p0, p1, p2, p3 = pts[max(i - 1, 0)], pts[i], pts[i + 1], pts[min(i + 2, len(pts) - 1)]
        for j in range(n):
            t = j / n
            out.append(tuple(0.5 * (2 * b + (-a + c) * t + (2 * a - 5 * b + 4 * c - d) * t * t + (-a + 3 * b - 3 * c + d) * t ** 3)
                             for a, b, c, d in zip(p0, p1, p2, p3)))
    out.append(pts[-1])
    return out


def poly(pts):
    return '<path d="M' + ' L'.join(f'{x:.2f},{y:.2f}' for x, y in pts) + ' Z"/>'


def line(x1, y1, x2, y2, w):
    return f'<line x1="{x1:.2f}" y1="{y1:.2f}" x2="{x2:.2f}" y2="{y2:.2f}" stroke-width="{w}"/>'


def leaf(base, ang, L, stalk):
    """an oak leaf from base, pointing at ang (degrees, 0 = right, -90 = up): its shape, stalk and midrib"""
    a = math.radians(ang)
    ux, uy = math.cos(a), math.sin(a)
    nx, ny = -uy, ux
    sx, sy = base[0] + stalk * ux, base[1] + stalk * uy
    upper = catmull(OAK)
    lower = catmull([(min(1.0, x + 0.025) if 0 < x < 1 else x, y * 0.95) for x, y in OAK])
    pts = [(sx + ux * L * x + nx * L * y, sy + uy * L * x + ny * L * y) for x, y in upper]
    pts += [(sx + ux * L * x - nx * L * y, sy + uy * L * x - ny * L * y) for x, y in lower[::-1]]
    return ([poly(pts)], [line(base[0], base[1], sx, sy, 0.6)],
            [line(sx + ux * L * 0.08, sy + uy * L * 0.08, sx + ux * L * 0.8, sy + uy * L * 0.8, 0.45)])


def acorn(x, y, ang, s):
    """an acorn hanging from (x, y) toward ang: its cup, nut and stalk, and the line between cup and nut"""
    a = math.radians(ang)
    ux, uy = math.cos(a), math.sin(a)
    nx, ny = -uy, ux
    cx, cy = x + ux * 1.3 * s, y + uy * 1.3 * s
    cup = [(cx + nx * 1.15 * s * math.cos(math.pi * i / 12) - ux * 0.9 * s * math.sin(math.pi * i / 12),
            cy + ny * 1.15 * s * math.cos(math.pi * i / 12) - uy * 0.9 * s * math.sin(math.pi * i / 12)) for i in range(13)]
    ex, ey = cx + ux * 1.25 * s, cy + uy * 1.25 * s
    nut = (f'<ellipse cx="{ex:.2f}" cy="{ey:.2f}" rx="{1.45 * s:.2f}" ry="{0.95 * s:.2f}" '
           f'transform="rotate({ang:.1f} {ex:.2f} {ey:.2f})"/>')
    return ([poly(cup), nut], [line(x, y, cx - ux * 0.8 * s, cy - uy * 0.8 * s, 0.6)],
            [line(cx + nx * 1.05 * s, cy + ny * 1.05 * s, cx - nx * 1.05 * s, cy - ny * 1.05 * s, 0.45)])


def main():
    x, y = W / 2, RULE - 0.5
    parts = [leaf((x - 1.0, y), -160, 8.6, 0.7), leaf((x + 1.0, y), -20, 8.6, 0.7), leaf((x, y), -90, 7.2, 0.7),
             acorn(x - 3.2, y, 125, 0.7), acorn(x + 3.2, y, 55, 0.7)]
    fills = ''.join(e for p in parts for e in p[0])
    stalks = ''.join(e for p in parts for e in p[1])
    cuts = ''.join(e for p in parts for e in p[2])
    svg = (f'<svg xmlns="http://www.w3.org/2000/svg" width="{W:g}" height="{H:g}" viewBox="0 0 {W:g} {H:g}">'
           f'<defs><mask id="m" maskUnits="userSpaceOnUse" x="0" y="0" width="{W:g}" height="{H:g}">'
           f'<rect width="{W:g}" height="{H:g}" fill="#fff"/><g stroke="#000" stroke-linecap="round">{cuts}</g></mask></defs>'
           f'<g mask="url(#m)"><g fill="#000">{fills}</g>'
           f'<g stroke="#000" stroke-linecap="round" fill="none">{stalks}</g></g></svg>\n')
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    open(OUT, 'w', encoding='utf-8', newline='\n').write(svg)
    print(os.path.normpath(OUT), len(svg), 'bytes')


if __name__ == '__main__':
    main()
