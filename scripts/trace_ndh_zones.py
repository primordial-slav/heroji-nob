"""The lines inside NDH in 1941 that OpenHistoricalMap doesn't have, traced from the printed map in the repo root
(mapa jugoslavije.jpg, "Podela Jugoslavije posle okupacije, aprila 1941 godine"):
- the German-Italian demarcation line (solid dark blue on the print)
- the line between Italy's zones II and III (dashed)
- that line's variant (dotted)

Each line is printed in dark blue. A rough guide read off the scan (GUIDES, in the scan's pixels) is snapped to the
blue pixels near it; the solid line is taken whole from its pieces of the blue mask. The scan is tied to the ground
by towns printed on it (CONTROL: pixel -> GeoNames position), with a second-order polynomial, and the lines are
written as lon/lat to website/app/(sr)/mapa/sources/ndh-zones-1941.json, for scripts/make_map_1941.py.

Usage: python scripts/trace_ndh_zones.py [--check]   (--check also writes a picture of the traces over the scan)
"""
import json
import math
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage as ndi

sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, str(Path(__file__).resolve().parent))
from make_unit_route import fold, gazetteer, km  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
SCAN = ROOT / 'mapa jugoslavije.jpg'
OUT = ROOT / 'website' / 'app' / '(sr)' / 'mapa' / 'sources' / 'ndh-zones-1941.json'

# towns printed on the scan: name, pixel (x, y) of its circle, rough lon/lat to pick the right one in GeoNames
CONTROL = [
    ('Karlovac', 690, 583, 15.55, 45.49), ('Glina', 855, 655, 16.09, 45.34), ('Bihać', 780, 870, 15.87, 44.82),
    ('Slunj', 695, 743, 15.59, 45.12), ('Banja Luka', 1167, 897, 17.19, 44.77), ('Prijedor', 1022, 805, 16.71, 44.98),
    ('Sisak', 935, 590, 16.37, 45.47), ('Petrinja', 898, 610, 16.28, 45.44), ('Bosanska Krupa', 862, 844, 16.15, 44.88),
    ('Ključ', 1048, 993, 16.78, 44.53), ('Mrkonjić Grad', 1135, 1038, 17.08, 44.42), ('Jajce', 1187, 1070, 17.27, 44.34),
    ('Gračac', 793, 1100, 15.85, 44.30), ('Udbina', 747, 987, 15.77, 44.53), ('Ogulin', 598, 670, 15.23, 45.27),
    ('Knin', 878, 1195, 16.20, 44.04), ('Split', 950, 1407, 16.44, 43.51), ('Šibenik', 780, 1310, 15.89, 43.73),
    ('Sinj', 997, 1321, 16.64, 43.70), ('Livno', 1113, 1280, 17.01, 43.83), ('Duvno', 1175, 1328, 17.23, 43.72),
    ('Imotski', 1202, 1415, 17.22, 43.45), ('Glamoč', 1085, 1210, 16.85, 44.05), ('Kupres', 1190, 1218, 17.28, 43.99),
    ('Bugojno', 1245, 1190, 17.45, 44.06), ('Prozor', 1297, 1285, 17.61, 43.82), ('Konjic', 1399, 1356, 17.96, 43.65),
    ('Mostar', 1354, 1478, 17.81, 43.34), ('Travnik', 1277, 1103, 17.67, 44.23), ('Zenica', 1390, 1132, 17.91, 44.20),
    ('Drvar', 922, 1042, 16.38, 44.37), ('Bosansko Grahovo', 932, 1135, 16.36, 44.18), ('Teslić', 1368, 972, 17.86, 44.61),
    ('Sarajevo', 1532, 1270, 18.41, 43.85), ('Kalinovik', 1544, 1417, 18.45, 43.50), ('Gacko', 1571, 1558, 18.53, 43.17),
    ('Nevesinje', 1448, 1518, 18.11, 43.26), ('Bileća', 1543, 1672, 18.43, 42.87), ('Trebinje', 1513, 1742, 18.34, 42.71),
    ('Višegrad', 1795, 1303, 19.29, 43.78), ('Ljubuški', 1268, 1535, 17.55, 43.20), ('Visoko', 1462, 1216, 18.18, 43.99),
]

# rough courses read off the scan, in its pixels; each is snapped to the printed line near it
GUIDES = {
    'zone_ii_iii': [(600, 605), (615, 645), (630, 680), (655, 715), (675, 750), (690, 790), (705, 840), (720, 865),
                    (740, 890), (755, 910), (770, 940), (785, 970), (795, 1005), (815, 1025), (850, 1035), (880, 1050),
                    (930, 1070), (970, 1085), (995, 1110), (1020, 1130), (1045, 1160), (1065, 1185), (1085, 1200),
                    (1110, 1215), (1140, 1222), (1170, 1225), (1200, 1230), (1240, 1260), (1280, 1300), (1310, 1330),
                    (1340, 1370), (1350, 1430), (1380, 1450), (1420, 1480), (1460, 1500), (1490, 1520), (1520, 1545),
                    (1550, 1570), (1570, 1590), (1590, 1595)],
    'zone_variant': [(1020, 1155), (1025, 1200), (1045, 1240), (1085, 1270), (1130, 1280), (1145, 1310), (1170, 1340),
                     (1200, 1355), (1250, 1370), (1300, 1400), (1350, 1420), (1400, 1445), (1460, 1465), (1520, 1495),
                     (1570, 1510), (1600, 1525)],
}
# the demarcation line's pieces of the blue mask (see --check), in order from Zagreb to Višegrad: their bounding
# boxes in the scan's pixels, and the line's course between pieces where the print is too dark to read
DEMARCATION_BOXES = [(735, 445, 860, 690), (800, 660, 930, 805), (915, 780, 1140, 1000), (1105, 960, 1155, 1020),
                     (1115, 1030, 1150, 1100), (1145, 1090, 1270, 1200), (1255, 1170, 1475, 1360),
                     (1465, 1345, 1550, 1385), (1540, 1335, 1620, 1385), (1760, 1310, 1835, 1380)]


def blue(a, loose=False):
    r, g, b = a[..., 0], a[..., 1], a[..., 2]
    if loose:
        return (b - r > 30) & (b - g > 15) & (r < 150) & (g < 150)
    return (b - r > 45) & (b - g > 25) & (r < 110) & (g < 110)


def resample(pts, step):
    out = [pts[0]]
    for (x1, y1), (x2, y2) in zip(pts, pts[1:]):
        d = math.hypot(x2 - x1, y2 - y1)
        n = max(1, int(d // step))
        out += [(x1 + (x2 - x1) * k / n, y1 + (y2 - y1) * k / n) for k in range(1, n + 1)]
    return out


def snap(guide, mask, radius=13):
    """Each point of the guide moved to the middle of the printed pixels around it; where the print is blank
    (between dashes or dots) the guide's point stays"""
    ys, xs = np.nonzero(mask)
    tree = {}
    for x, y in zip(xs, ys):
        tree.setdefault((x // 16, y // 16), []).append((x, y))
    out = []
    for gx, gy in resample(guide, 5):
        near = [(x, y) for cx in range(int(gx // 16) - 1, int(gx // 16) + 2) for cy in range(int(gy // 16) - 1, int(gy // 16) + 2)
                for x, y in tree.get((cx, cy), []) if math.hypot(x - gx, y - gy) <= radius]
        if len(near) >= 3:
            out.append((float(np.mean([p[0] for p in near])), float(np.mean([p[1] for p in near]))))
        else:
            out.append((gx, gy))
    # a running mean takes out the jitter of the halftone
    sm = []
    for i in range(len(out)):
        win = out[max(0, i - 3): i + 4]
        sm.append((sum(p[0] for p in win) / len(win), sum(p[1] for p in win) / len(win)))
    return sm


def chain_pixels(px):
    """A piece of a printed line as an ordered polyline: its pixels in cells of 6 px, walked from one end"""
    cells = {}
    for x, y in px:
        cells.setdefault((x // 6, y // 6), []).append((x, y))
    nodes = [(float(np.mean([p[0] for p in v])), float(np.mean([p[1] for p in v]))) for v in cells.values()]
    if len(nodes) < 2:
        return nodes
    c = (np.mean([n[0] for n in nodes]), np.mean([n[1] for n in nodes]))
    start = max(nodes, key=lambda n: math.hypot(n[0] - c[0], n[1] - c[1]))
    path, left = [start], set(nodes) - {start}
    while left:
        nxt = min(left, key=lambda n: math.hypot(n[0] - path[-1][0], n[1] - path[-1][1]))
        if math.hypot(nxt[0] - path[-1][0], nxt[1] - path[-1][1]) > 30:
            break
        path.append(nxt)
        left.discard(nxt)
    return path


def demarcation(mask):
    line = []
    for x0, y0, x1, y1 in DEMARCATION_BOXES:
        sub = mask[y0:y1, x0:x1]
        lab, n = ndi.label(ndi.binary_dilation(sub, iterations=4))
        if n == 0:
            continue
        sizes = ndi.sum(sub, lab, range(1, n + 1))
        biggest = int(np.argmax(sizes)) + 1
        ys, xs = np.nonzero((lab == biggest) & sub)
        piece = chain_pixels(list(zip(xs + x0, ys + y0)))
        if line and math.hypot(piece[-1][0] - line[-1][0], piece[-1][1] - line[-1][1]) < math.hypot(piece[0][0] - line[-1][0], piece[0][1] - line[-1][1]):
            piece = piece[::-1]
        line += piece
    sm = []
    for i in range(len(line)):
        win = line[max(0, i - 2): i + 3]
        sm.append((sum(p[0] for p in win) / len(win), sum(p[1] for p in win) / len(win)))
    return sm


def fit(control, index):
    """Pixel -> lon/lat, a second-order polynomial through the towns, with each town's fit error in km"""
    src, dst, names = [], [], []
    for name, px, py, lon, lat in control:
        best = None
        for glon, glat, fc, pop, gname in index.get(fold(name), []):
            if fc == 'P':
                d = km((glon, glat), (lon, lat))
                if d < 25 and (best is None or d < best[0]):
                    best = (d, glon, glat)
        if best is None:
            print(f'  control: {name} not found near {lon}, {lat}; using the rough position')
            best = (0, lon, lat)
        src.append((px, py))
        dst.append((best[1], best[2]))
        names.append(name)
    src, dst = np.array(src, float), np.array(dst)
    def terms(p):
        x, y = (p[:, 0] - 1200) / 1000, (p[:, 1] - 1100) / 1000
        return np.stack([np.ones_like(x), x, y, x * x, x * y, y * y], 1)
    A = terms(src)
    cx, *_ = np.linalg.lstsq(A, dst[:, 0], rcond=None)
    cy, *_ = np.linalg.lstsq(A, dst[:, 1], rcond=None)
    pred = np.stack([A @ cx, A @ cy], 1)
    errs = [km(tuple(p), tuple(d)) for p, d in zip(pred, dst)]
    worst = sorted(zip(errs, names), reverse=True)[:5]
    print(f'  fit: {len(names)} towns, mean error {np.mean(errs):.1f} km; worst ' + ', '.join(f'{n} {e:.1f}' for e, n in worst))
    return lambda pts: [tuple(v) for v in np.stack([terms(np.array(pts, float)) @ cx, terms(np.array(pts, float)) @ cy], 1)]


def main():
    a = np.asarray(Image.open(SCAN).convert('RGB')).astype(int)
    mask, loose = blue(a), blue(a, loose=True)
    lines_px = {'demarcation': demarcation(mask)}
    for key, guide in GUIDES.items():
        lines_px[key] = snap(guide, loose)
    to_lonlat = fit(CONTROL, gazetteer())
    out = {k: [[round(lon, 5), round(lat, 5)] for lon, lat in to_lonlat(v)] for k, v in lines_px.items()}
    OUT.parent.mkdir(exist_ok=True)
    OUT.write_text(json.dumps({'source': 'mapa jugoslavije.jpg (Podela Jugoslavije posle okupacije, aprila 1941)',
                               'lines': out}, ensure_ascii=False), encoding='utf-8')
    print(f'wrote {OUT.relative_to(ROOT)}: ' + ', '.join(f'{k} {len(v)} points' for k, v in out.items()))
    if '--check' in sys.argv:
        img = Image.fromarray((a * 0.55 + 110).astype('uint8'))
        d = ImageDraw.Draw(img)
        colours = {'demarcation': (0, 90, 220), 'zone_ii_iii': (0, 150, 0), 'zone_variant': (220, 0, 160)}
        for k, v in lines_px.items():
            d.line(v, fill=colours[k], width=4)
        for name, px, py, *_ in CONTROL:
            d.ellipse((px - 6, py - 6, px + 6, py + 6), outline=(200, 0, 0), width=2)
        check = ROOT / 'map-experiment' / '_ndh_zones_check.jpg'
        img.crop((500, 400, 1900, 1800)).resize((1000, 1000)).save(check, quality=85)
        print(f'check picture: {check.relative_to(ROOT)}')


if __name__ == '__main__':
    main()
