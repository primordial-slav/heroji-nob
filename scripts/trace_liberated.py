"""The liberated territory, which OpenHistoricalMap doesn't have, traced from the maps of the Vojnoistorijski institut's
history of the war (Oslobodilački rat naroda Jugoslavije 1941-1945, knjiga 1, Beograd 1957, znaci.org 00001/151):
- skica 4, "Oslobođena i poluoslobođena teritorija u Jugoslaviji decembra 1941" (the whole country)
- skica 23, "Oslobođena i poluoslobođena teritorija u centralnom i zapadnom delu Jugoslavije posle kapitulacije
  Italije (septembra 1943)" (the centre and the west only)
and from the folded map at the end of Bihaćka republika, knj. 1 (Bihać 1965, znaci.org 00003/500):
- "Oslobođena teritorija Jugoslavije novembra 1942" (the whole country; the semi-liberated in flat pink)

All print the liberated territory in solid red, the VII's maps the semi-liberated ("poluoslobođena") in red hatching. A pixel is
counted by the share of red around it: nearly all red is liberated, a share of red stripes semi-liberated. The scans are
tied to the ground by towns printed on them: a few read by eye (ANCHORS) give a rough fit, the town circles found near
where some forty more should be are added, and a second-order polynomial is fitted through all of them, dropping those
that sit far off. The areas are written as lon/lat polygons to website/app/(sr)/mapa/sources/liberated.json, for
scripts/make_map_1941.py.

The scans (rendered from the PDFs at their own resolution) are kept in data-extraction/.cache/liberated/.

Usage: python scripts/trace_liberated.py [--check]   (--check writes a picture of the traces over each scan)
"""
import json
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage as ndi
from shapely.geometry import MultiPolygon, Polygon, box
from shapely.ops import unary_union

sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, str(Path(__file__).resolve().parent))
from make_unit_route import fold, gazetteer, km  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
CACHE = ROOT / 'data-extraction' / '.cache' / 'liberated'
OUT = ROOT / 'website' / 'app' / '(sr)' / 'mapa' / 'sources' / 'liberated.json'
SOURCE = 'Oslobodilački rat naroda Jugoslavije 1941-1945, knj. 1, Vojnoistorijski institut JNA, Beograd 1957'

# towns whose circles may be found on either map: name, lon, lat
TOWNS = [
    ('Ljubljana', 14.51, 46.05), ('Zagreb', 15.98, 45.81), ('Beograd', 20.46, 44.82), ('Skoplje', 21.43, 42.00),
    ('Split', 16.44, 43.51), ('Sarajevo', 18.41, 43.85), ('Niš', 21.90, 43.32), ('Podgorica', 19.26, 42.44),
    ('Rijeka', 14.44, 45.33), ('Subotica', 19.67, 46.10), ('Novi Sad', 19.84, 45.25), ('Karlovac', 15.55, 45.49),
    ('Sisak', 16.37, 45.47), ('Bihać', 15.87, 44.82), ('Banja Luka', 17.19, 44.77), ('Prijedor', 16.71, 44.98),
    ('Osijek', 18.69, 45.55), ('Vinkovci', 18.80, 45.29), ('Slavonski Brod', 18.02, 45.16), ('Tuzla', 18.67, 44.54),
    ('Zenica', 17.91, 44.20), ('Mostar', 17.81, 43.34), ('Dubrovnik', 18.09, 42.65), ('Šibenik', 15.89, 43.73),
    ('Zadar', 15.23, 44.12), ('Gospić', 15.37, 44.55), ('Knin', 16.20, 44.04), ('Livno', 17.01, 43.83),
    ('Užice', 19.84, 43.86), ('Valjevo', 19.89, 44.27), ('Kragujevac', 20.91, 44.01), ('Čačak', 20.35, 43.89),
    ('Kraljevo', 20.69, 43.73), ('Kruševac', 21.33, 43.58), ('Pirot', 22.59, 43.15), ('Vranje', 21.90, 42.55),
    ('Priština', 21.17, 42.67), ('Peć', 20.29, 42.66), ('Prizren', 20.74, 42.21), ('Tetovo', 20.97, 42.01),
    ('Prilep', 21.55, 41.35), ('Štip', 22.19, 41.75), ('Kumanovo', 21.71, 42.13), ('Šabac', 19.69, 44.76),
    ('Smederevo', 20.93, 44.67), ('Požarevac', 21.19, 44.62), ('Kikinda', 20.47, 45.83), ('Sombor', 19.11, 45.77),
    ('Maribor', 15.65, 46.55), ('Celje', 15.27, 46.24), ('Novo Mesto', 15.17, 45.80), ('Kočevje', 14.86, 45.64),
    ('Pula', 13.85, 44.87), ('Nikšić', 18.94, 42.77), ('Cetinje', 18.91, 42.39), ('Pljevlja', 19.36, 43.36),
    ('Bijelo Polje', 19.75, 43.04), ('Višegrad', 19.29, 43.78), ('Foča', 18.78, 43.51), ('Kolašin', 19.52, 42.82),
    ('Berane', 19.87, 42.84), ('Gacko', 18.53, 43.17), ('Drvar', 16.38, 44.37), ('Jajce', 17.27, 44.34),
    ('Doboj', 18.09, 44.73), ('Bijeljina', 19.21, 44.76), ('Zvornik', 19.10, 44.39), ('Bjelovar', 16.84, 45.90),
    ('Daruvar', 17.22, 45.59), ('Virovitica', 17.38, 45.83), ('Varaždin', 16.34, 46.31), ('Kruševo', 21.25, 41.37),
    ('Ogulin', 15.23, 45.27), ('Glina', 16.09, 45.34), ('Slunj', 15.59, 45.12), ('Imotski', 17.22, 43.45),
    ('Trebinje', 18.34, 42.71), ('Nevesinje', 18.11, 43.26), ('Travnik', 17.67, 44.23), ('Kupres', 17.28, 43.99),
    ('Glamoč', 16.85, 44.05), ('Bosanski Petrovac', 16.37, 44.55), ('Ključ', 16.78, 44.53), ('Sanski Most', 16.67, 44.77),
    ('Kladanj', 18.69, 44.23), ('Vlasenica', 18.94, 44.18), ('Rogatica', 19.00, 43.80), ('Goražde', 18.98, 43.67),
]
# more towns, looked for only on the maps that ask for them (on the others they were taken for letters near by)
MORE_TOWNS = [
    ('Bitola', 21.33, 41.03), ('Ohrid', 20.80, 41.12), ('Debar', 20.52, 41.52), ('Veles', 21.78, 41.72),
    ('Kočani', 22.41, 41.92), ('Strumica', 22.64, 41.44), ('Leskovac', 21.95, 43.00), ('Negotin', 22.55, 44.23),
    ('Zaječar', 22.29, 43.90), ('Bor', 22.10, 44.08), ('Vršac', 21.30, 45.12), ('Zrenjanin', 20.39, 45.38),
    ('Sremska Mitrovica', 19.61, 44.97), ('Loznica', 19.22, 44.53), ('Brčko', 18.81, 44.87), ('Obrenovac', 20.20, 44.65),
    ('Kotor', 18.77, 42.42), ('Bar', 19.10, 42.09), ('Raška', 20.61, 43.29), ('Kosovska Mitrovica', 20.87, 42.89),
    ('Žabljak', 19.12, 43.15), ('Rudo', 19.37, 43.62), ('Kranj', 14.36, 46.24), ('Novska', 16.98, 45.34),
    ('Cazin', 15.94, 44.97), ('Konjic', 17.98, 43.65), ('Bosanski Novi', 16.38, 45.05), ('Ostrožac', 15.94, 44.91),
]

# The maps traced first, before the atlas was found: no longer drawn (the atlas's series is one hand for the whole war),
# kept to compare against it with --older. Each map: its scan, the months it would be shown in, the frame of the map
# itself (pixels: left, top, right, bottom), the parts of it that are not the map (the legend, the title), and towns
# read off it by eye: name, x, y
OLDER_MAPS = [
    {
        'key': '1941-12', 'scan': 'skica04_1941-12.png', 'from': '1941-12', 'to': '1942-01',
        'label': 'decembar 1941.', 'sketch': 'skica 4',
        'frame': (28, 40, 1500, 1174), 'not_map': [(0, 1055, 335, 1174), (0, 0, 1501, 40)],
        'anchors': [('Ljubljana', 268, 211), ('Zagreb', 463, 272), ('Beograd', 1058, 476), ('Skoplje', 1200, 992),
                    ('Split', 514, 714), ('Sarajevo', 779, 656), ('Niš', 1262, 749), ('Podgorica', 896, 918),
                    ('Rijeka', 252, 345), ('Subotica', 946, 228)],
    },
    {
        'key': '1943-09', 'scan': 'skica23_1943-09.png', 'from': '1943-09', 'to': '1943-10',
        'label': 'septembar 1943. (srednji i zapadni deo zemlje)', 'sketch': 'skica 23',
        'frame': (0, 62, 1983, 1585), 'not_map': [(0, 1250, 578, 1585), (0, 0, 1983, 62), (880, 1560, 1100, 1615)],
        'anchors': [('Zagreb', 668, 264), ('Beograd', 1880, 622), ('Sarajevo', 1350, 1000), ('Split', 782, 1148),
                    ('Novi Sad', 1700, 452), ('Banja Luka', 1003, 661), ('Rijeka', 262, 452), ('Mostar', 1195, 1200),
                    ('Podgorica', 1606, 1535), ('Dubrovnik', 1281, 1468), ('Subotica', 1640, 130)],
    },
    {
        # the folded map at the end of Bihaćka republika, knj. 1 (Bihać 1965, znaci.org 00003/500, PDF page 740), at
        # half its scan's size; it draws the liberated territory in solid red, the semi-liberated in flat pink, and its
        # town circles in a grey too light for circles(), so they are found as rings of RING pixels' radius
        'key': '1942-11', 'scan': 'skica_bihac_1942-11.png', 'from': '1942-11', 'to': '1943-01',
        'label': 'novembar 1942.', 'sketch': 'karta „Oslobođena teritorija Jugoslavije novembra 1942“',
        'source': 'Bihaćka republika, knj. 1, Bihać 1965',
        'frame': (6, 6, 2378, 2120), 'not_map': [(0, 1700, 600, 2126), (1765, 0, 2405, 240)],
        'ring': 5, 'solid_gb': 138, 'more_towns': True,
        'anchors': [('Ljubljana', 297, 316), ('Karlovac', 531, 509), ('Rijeka', 272, 551), ('Maribor', 557, 159),
                    ('Banja Luka', 909, 756), ('Bihać', 601, 737), ('Jajce', 928, 892), ('Sarajevo', 1205, 1057),
                    ('Zadar', 456, 965), ('Osijek', 1247, 496), ('Subotica', 1468, 307), ('Novi Sad', 1520, 585),
                    ('Kragujevac', 1788, 981), ('Užice', 1543, 1043), ('Valjevo', 1546, 908), ('Niš', 2033, 1203),
                    ('Skoplje', 1942, 1643), ('Podgorica', 1420, 1515), ('Bitola', 1930, 1968), ('Prizren', 1777, 1571),
                    ('Peć', 1667, 1431)],
    },
]

# The Istoriski atlas oslobodilačkog rata naroda Jugoslavije (Vojnogeografski institut, Beograd 1952), photographed
# spread by spread by the Hrvatski povijesni muzej (kartevgi.hismus.hr, inv. HPM-32981; the scans in .cache/liberated/hpm/
# as atlas_NN.jpg). Ten of its maps give the liberated territory (an orange screen) and the semi-liberated, "na kojoj su
# operisale naše jedinice, ali koje nisu u to vreme čvrsto držale u svojim rukama" (a crimson screen), all on one base
# plate: the towns are read once, on the map of September 1944 (ATLAS_REF), and found on the others by registering each
# photograph to that one.
ATLAS_SOURCE = 'Istoriski atlas oslobodilačkog rata naroda Jugoslavije 1941–1945, Vojnogeografski institut, Beograd 1952'
ATLAS_REF = {
    'scan': 'hpm/atlas_30.jpg',
    'frame': (290, 100, 2760, 2280),
    'not_map': [(1250, 80, 2620, 330), (420, 1730, 930, 2010)],
    'anchors': [('Ljubljana', 649, 408), ('Karlovac', 894, 612), ('Maribor', 928, 242), ('Banja Luka', 1288, 870),
                ('Bihać', 927, 850), ('Jajce', 1305, 1019), ('Pula', 474, 813), ('Osijek', 1652, 593),
                ('Subotica', 1885, 398), ('Novi Sad', 1934, 695), ('Beograd', 2092, 848), ('Vršac', 2289, 733),
                ('Zaječar', 2546, 1146), ('Valjevo', 1953, 1039), ('Sarajevo', 1597, 1188), ('Split', 1101, 1305),
                ('Mostar', 1442, 1368), ('Dubrovnik', 1520, 1611), ('Podgorica', 1811, 1678), ('Šibenik', 966, 1224),
                ('Livno', 1239, 1196), ('Niš', 2464, 1349), ('Skoplje', 2369, 1810), ('Priština', 2289, 1585),
                ('Bitola', 2353, 2146), ('Ohrid', 2214, 2122), ('Prizren', 2191, 1745), ('Peć', 2072, 1594)],
}
# the museum's number of the photograph, the map's date, the months it is shown in on the timeline, the date for the
# map's key, and its title as printed. Every month of the timeline has a map: where the atlas has none (VI-IX 1942,
# II-III 1943, VII-VIII 1943, III 1944) the nearest in time stands in, its date in the key saying so; the Drvar map
# also from March 1944, the Sixth offensive over by February
ATLAS_MAPS = [
    (3, '1941-09', '1941-09', '1941-11', 'septembar 1941.', 'Oslobođena i poluoslobođena teritorija septembra 1941 godine'),
    (6, '1941-12', '1941-12', '1942-02', 'kraj 1941.', 'Oslobođena i poluoslobođena teritorija krajem 1941 godine'),
    (10, '1942-04', '1942-03', '1942-07', 'april 1942.', 'Oslobođena i poluoslobođena teritorija aprila 1942 godine'),
    (14, '1942-11', '1942-08', '1943-02', '26–27. XI 1942.',
     'Oslobođena i poluoslobođena teritorija u vreme Prvog zasedanja AVNOJ-a (26–27 novembra 1942 godine)'),
    (18, '1943-05', '1943-03', '1943-07', 'maj 1943.', 'Oslobođena i poluoslobođena teritorija maja 1943 godine'),
    (22, '1943-09', '1943-08', '1943-10', 'septembar 1943.',
     'Oslobođena i poluoslobođena teritorija neposredno posle kapitulacije Italije (septembra 1943 godine)'),
    (23, '1943-11', '1943-11', '1944-02', '29. XI 1943.',
     'Oslobođena i poluoslobođena teritorija za vreme Drugog zasedanja AVNOJ-a (29 novembra 1943 godine)'),
    (26, '1944-05', '1944-03', '1944-07', '25. V 1944.',
     'Oslobođena i poluoslobođena teritorija za vreme nemačkog napada na Drvar (25 maja 1944 godine)'),
    (30, '1944-09', '1944-08', '1944-10', '6. IX 1944.',
     'Oslobođena i poluoslobođena teritorija u vreme izbijanja Sovjetske armije na našu granicu (6 septembra 1944 godine)'),
    (34, '1945-01', '1944-11', '1945-04', 'januar 1945.', 'Oslobođena teritorija januara 1945 godine'),
]
# the months a map only stands in for, the atlas having none of its own for them (the page says so on the sheet)
STAND_IN = {'1942-04': ['1942-06', '1942-07'], '1942-11': ['1942-08', '1942-09', '1943-02'],
            '1943-05': ['1943-03', '1943-07'], '1943-09': ['1943-08'], '1944-05': ['1944-03']}
MAPS = [{'key': key, 'scan': f'hpm/atlas_{n:02d}.jpg', 'standIn': STAND_IN.get(key, []), 'from': fr, 'to': to, 'label': label, 'atlas': True,
         'source': ATLAS_SOURCE, 'sketch': f'karta „{title}“'} for n, key, fr, to, label, title in ATLAS_MAPS]


# ---------- the fit: pixels <-> lon/lat ----------

def terms(p, centre):
    x, y = (p[:, 0] - centre[0]) / 1000, (p[:, 1] - centre[1]) / 1000
    return np.stack([np.ones_like(x), x, y, x * x, x * y, y * y], 1)


def solve(src, dst, centre, order=2):
    A = terms(src, centre) if order == 2 else terms(src, centre)[:, :3]
    cx, *_ = np.linalg.lstsq(A, dst[:, 0], rcond=None)
    cy, *_ = np.linalg.lstsq(A, dst[:, 1], rcond=None)
    def f(pts):
        P = np.array(pts, float).reshape(-1, 2)
        B = terms(P, centre) if order == 2 else terms(P, centre)[:, :3]
        return np.stack([B @ cx, B @ cy], 1)
    return f


def place(name, lon, lat, index):
    """A town's position in GeoNames, the one of that name nearest the rough position"""
    best = None
    for glon, glat, fc, pop, gname in index.get(fold(name), []):
        if fc == 'P':
            d = km((glon, glat), (lon, lat))
            if d < 25 and (best is None or d < best[0]):
                best = (d, glon, glat)
    return (best[1], best[2]) if best else (lon, lat)


def circles(a):
    """Centres of the small printed town circles: rings of dark ink a few pixels across"""
    grey = a.mean(2)
    red = (a[..., 0] > 160) & (a[..., 1] < 120) & (a[..., 2] < 120)
    dark = (grey < 110) & ~red
    lab, n = ndi.label(dark)
    out = []
    for i, sl in enumerate(ndi.find_objects(lab), 1):
        h, w = sl[0].stop - sl[0].start, sl[1].stop - sl[1].start
        if 4 <= h <= 16 and 4 <= w <= 16 and abs(h - w) <= 4:
            comp = lab[sl] == i
            if 0.2 < comp.mean() < 0.75 and not comp[h // 2, w // 2]:
                out.append(((sl[1].start + sl[1].stop - 1) / 2, (sl[0].start + sl[0].stop - 1) / 2))
    return np.array(out)


def rings(a, r):
    """How much each pixel looks like the centre of a printed town circle of radius r: the grey ink on a ring around
    it less the ink inside (a line through it, or a letter, has ink in both)"""
    ink = np.where(np.abs(a[..., 0] - a[..., 1]) < 40, 255 - a.mean(2), 0).astype(float)
    yy, xx = np.mgrid[-r - 2:r + 3, -r - 2:r + 3]
    rr = np.hypot(xx, yy)
    ring = ((rr >= r - 1) & (rr <= r + 1)).astype(float)
    inner = (rr <= r - 2.5).astype(float)
    return ndi.convolve(ink, ring / ring.sum()) - ndi.convolve(ink, inner / inner.sum())


def snap(score, x, y, reach, least=40):
    """The best ring centre within reach of (x, y), if it is one"""
    h, w = score.shape
    t, l = max(0, int(y) - reach), max(0, int(x) - reach)
    win = score[t:min(h, int(y) + reach + 1), l:min(w, int(x) + reach + 1)]
    if win.size == 0:
        return None
    k = np.unravel_index(int(win.argmax()), win.shape)
    return (float(l + k[1]), float(t + k[0])) if win[k] > least else None


def tie(m, a, index):
    """Pixel -> lon/lat for one map: anchors, then the circles of the other towns near where the anchors put them"""
    towns = {name: place(name, lon, lat, index) for name, lon, lat in TOWNS + (MORE_TOWNS if m.get('more_towns') else [])}
    centre = (a.shape[1] / 2, a.shape[0] / 2)
    score = rings(a, m['ring']) if 'ring' in m else None
    # anchors read by eye are set on their circle's centre, where a ring is found near
    pairs = {n: (snap(score, x, y, 14) if score is not None else None) or (x, y) for n, x, y in m['anchors']}
    src = np.array([pairs[n] for n, _, _ in m['anchors']], float)
    dst = np.array([towns[n] for n, _, _ in m['anchors']])
    back = solve(dst, src, (sum(d[0] for d in dst) / len(dst), sum(d[1] for d in dst) / len(dst)), order=1)
    found = circles(a) if score is None else None
    h, w = a.shape[:2]
    for name, (lon, lat) in towns.items():
        if name in pairs:
            continue
        px, py = back([(lon, lat)])[0]
        if not (0 <= px < w and 0 <= py < h):
            continue
        if score is not None:
            hit = snap(score, px, py, 18)
            if hit:
                pairs[name] = hit
            continue
        if len(found) == 0:
            continue
        d = np.hypot(found[:, 0] - px, found[:, 1] - py)
        k = int(d.argmin())
        if d[k] < 18:
            pairs[name] = tuple(found[k])
    # fit, drop what sits far off (a letter taken for a circle), fit again
    names = list(pairs)
    for _ in range(3):
        src = np.array([pairs[n] for n in names], float)
        dst = np.array([towns[n] for n in names])
        f = solve(src, dst, centre)
        errs = np.array([km(tuple(p), tuple(q)) for p, q in zip(f(src), dst)])
        keep = [n for n, e in zip(names, errs) if e < max(6.0, 2.5 * np.median(errs)) or n in dict((a_[0], 1) for a_ in m['anchors'])]
        if len(keep) == len(names):
            break
        names = keep
    worst = sorted(zip(errs, names), reverse=True)[:4]
    print(f'  {m["key"]}: {len(names)} towns ({len(m["anchors"])} by eye), mean error {errs.mean():.1f} km; worst '
          + ', '.join(f'{n} {e:.1f}' for e, n in worst))
    return f, {n: pairs[n] for n in names}


# ---------- the atlas: one base plate, ten photographs ----------

def linework(a):
    """A photograph's lines and lettering, the same on every map of the atlas whatever its colours: grey less its blur"""
    g = a.mean(2)
    return g - ndi.gaussian_filter(g, 4)


def phase(p, q):
    """How far q is shifted from p (dx, dy), and how sure: the peak of their normalised cross-power"""
    win = np.outer(np.hanning(p.shape[0]), np.hanning(p.shape[1]))
    F = np.fft.fft2((p - p.mean()) * win) * np.conj(np.fft.fft2((q - q.mean()) * win))
    r = np.real(np.fft.ifft2(F / (np.abs(F) + 1e-9)))
    k = np.unravel_index(int(r.argmax()), r.shape)
    dy, dx = [(v + n // 2) % n - n // 2 for v, n in zip(k, r.shape)]
    return -dx, -dy, r[k] / (r.std() + 1e-9)


def register(ref, img, frame):
    """Ref pixels -> this photograph's pixels: the shift of the whole page, then that of patches all over the map,
    an affine fitted through the sure ones"""
    small = lambda e: e[::4, ::4]
    h = min(ref.shape[0], img.shape[0]) // 4 * 4
    w = min(ref.shape[1], img.shape[1]) // 4 * 4
    gx, gy, _ = phase(small(ref[:h, :w]), small(img[:h, :w]))
    gx, gy = gx * 4, gy * 4
    l, t, r, b = frame
    half = 128
    src, dst = [], []
    for cy in np.linspace(t + half, b - half, 8):
        for cx in np.linspace(l + half, r - half, 10):
            cx, cy = int(cx), int(cy)
            ix, iy = cx + gx, cy + gy
            if not (half <= iy < img.shape[0] - half and half <= ix < img.shape[1] - half):
                continue
            p = ref[cy - half:cy + half, cx - half:cx + half]
            q = img[iy - half:iy + half, ix - half:ix + half]
            if p.std() < 4:
                continue
            dx, dy, sure = phase(p, q)
            if sure > 12:
                src.append((cx, cy))
                dst.append((ix + dx, iy + dy))
    src, dst = np.array(src, float), np.array(dst, float)
    keep = np.ones(len(src), bool)
    for _ in range(4):
        A = np.c_[src[keep], np.ones(keep.sum())]
        M, *_ = np.linalg.lstsq(A, dst[keep], rcond=None)
        err = np.hypot(*(np.c_[src, np.ones(len(src))] @ M - dst).T)
        keep = err < max(2.0, 3 * np.median(err[keep]))
    print(f'    registered by {keep.sum()} of {len(src)} patches, page shift {gx:+d},{gy:+d}, '
          f'residual {np.median(err[keep]):.1f} px')
    return lambda pts: np.c_[np.array(pts, float).reshape(-1, 2), np.ones(len(pts))] @ M


def masks_atlas(a, inside):
    """The atlas's orange screen (liberated) and crimson screen (semi-liberated): each pixel's colour averaged over
    the screen's dots, leaving out the ink, the division numbers' red and the water's blue, then told by its hue"""
    R, G, B = a[..., 0], a[..., 1], a[..., 2]
    off = ((R - G > 110) & (G < 110)) | (a.mean(2) < 110) | (B > R + 8)
    wgt = (~off).astype(float)
    den = ndi.uniform_filter(wgt, 11) + 1e-6
    s = np.stack([ndi.uniform_filter(a[..., i] * wgt, 11) / den for i in range(3)], -1)
    R, G, B = s[..., 0], s[..., 1], s[..., 2]
    mx, mn = s.max(2), s.min(2)
    sat = (mx - mn) / np.maximum(mx, 1)
    d = np.maximum(mx - mn, 1e-6)
    hue = np.where(mx == R, ((G - B) / d) % 6, np.where(mx == G, (B - R) / d + 2, (R - G) / d + 4)) * 60
    orange = (hue >= 12) & (hue <= 42) & (sat > 0.2) & inside
    crimson = ((hue >= 315) | (hue < 8)) & (sat > 0.18) & inside
    liberated = ndi.binary_opening(ndi.binary_closing(orange, structure=np.ones((9, 9))), structure=np.ones((9, 9)))
    semi = crimson & ~ndi.binary_dilation(liberated, iterations=3)
    semi = ndi.binary_opening(ndi.binary_closing(semi, structure=np.ones((9, 9))), structure=np.ones((9, 9)))
    return fill_small(keep_big(liberated, 500), 4000), fill_small(keep_big(semi, 400), 3000)


def region(shape, P, frame, not_map):
    """The map itself on this photograph: the reference's frame less its legend and title, carried over by P"""
    img = Image.new('L', (shape[1], shape[0]), 0)
    d = ImageDraw.Draw(img)
    corners = lambda l, t, r, b: [tuple(p) for p in P([(l, t), (r, t), (r, b), (l, b)])]
    d.polygon(corners(*frame), fill=1)
    for box_ in not_map:
        d.polygon(corners(*box_), fill=0)
    return np.asarray(img, bool)


def tie_atlas(m, P, index):
    """Pixel -> lon/lat for one atlas map: the reference's towns, carried over by P"""
    towns = {name: place(name, lon, lat, index) for name, lon, lat in TOWNS + MORE_TOWNS}
    names = [n for n, _, _ in ATLAS_REF['anchors']]
    pos = dict(zip(names, map(tuple, P([(x, y) for _, x, y in ATLAS_REF['anchors']]))))
    # fit, drop a town the atlas sets far from where it is (its own drawing, or a circle misread), fit again
    for _ in range(3):
        src = np.array([pos[n] for n in names])
        dst = np.array([towns[n] for n in names])
        f = solve(src, dst, tuple(src.mean(0)))
        errs = np.array([km(tuple(p), tuple(q)) for p, q in zip(f(src), dst)])
        keep = [n for n, e in zip(names, errs) if e < max(5.0, 2.5 * np.median(errs))]
        if len(keep) == len(names):
            break
        dropped = sorted(set(names) - set(keep))
        names = keep
    worst = sorted(zip(errs, names), reverse=True)[:3]
    print(f'  {m["key"]}: {len(names)} towns, mean error {errs.mean():.1f} km; worst '
          + ', '.join(f'{n} {e:.1f}' for e, n in worst) + (f'; left out {", ".join(dropped)}' if len(names) < 28 else ''))
    return f, {n: pos[n] for n in names}


# ---------- the areas ----------

def masks(a, m):
    """Liberated (nearly all red) and semi-liberated (a share of red stripes) areas, as pixel masks"""
    R, G, B = a[..., 0], a[..., 1], a[..., 2]
    gb = m.get('solid_gb', 125)
    solid = (R > 165) & (G < gb) & (B < gb) & (R - G > 80)
    # the hatching's own colour: a salmon pink (about 250/200/175), its red well above its green and blue, where the
    # paper's three are nearly equal; the 1943 map also draws it in darker red stripes
    pink = (R > 170) & (R - G >= 35) & (R - B >= 45) & ~solid
    frame = np.zeros(R.shape, bool)
    l, t, r, b = m['frame']
    frame[t:b, l:r] = True
    for l, t, r, b in m['not_map']:
        frame[t:b, l:r] = False
    red = (solid & frame).astype(float)
    tinted = ((solid | pink) & frame).astype(float)
    dense = ndi.uniform_filter(red, 7)
    liberated = ndi.binary_closing(dense > 0.7, structure=np.ones((7, 7)))
    liberated = ndi.binary_opening(liberated, structure=np.ones((3, 3)))
    # the hatching: stripes a few pixels apart, a fair share of tint over a wider window, off the solid areas
    wide = ndi.uniform_filter(tinted, 15)
    semi = (wide > 0.3) & ~ndi.binary_dilation(liberated, iterations=6)
    semi = ndi.binary_closing(semi, structure=np.ones((9, 9)))
    semi = ndi.binary_opening(semi, structure=np.ones((5, 5)))
    return fill_small(keep_big(liberated, 120), 2500), fill_small(keep_big(semi, 250), 1500)


def fill_small(mask, most):
    """Holes smaller than a printed word (the map's lettering over the red) filled; larger ones kept (towns held by
    the enemy, valleys)"""
    holes = ndi.binary_fill_holes(mask) & ~mask
    lab, n = ndi.label(holes)
    sizes = ndi.sum(holes, lab, range(1, n + 1))
    return mask | np.isin(lab, [i + 1 for i, s in enumerate(sizes) if s < most])


def keep_big(mask, least):
    lab, n = ndi.label(mask)
    sizes = ndi.sum(mask, lab, range(1, n + 1))
    return np.isin(lab, [i + 1 for i, s in enumerate(sizes) if s >= least])


def polygons(mask, step=2):
    """A mask as polygons in pixel coordinates: its rows' runs as boxes, joined and simplified"""
    small = mask[::step, ::step]
    boxes = []
    for y, row in enumerate(small):
        xs = np.flatnonzero(np.diff(np.concatenate([[0], row.astype(np.int8), [0]])))
        for x0, x1 in zip(xs[::2], xs[1::2]):
            boxes.append(box(x0 * step, y * step, x1 * step, (y + 1) * step))
    if not boxes:
        return []
    joined = unary_union(boxes).simplify(1.6)
    parts = list(joined.geoms) if isinstance(joined, MultiPolygon) else [joined]
    return [p for p in parts if isinstance(p, Polygon) and p.area > 150]


def to_lonlat(poly, f):
    ring = lambda coords: [[round(float(lon), 4), round(float(lat), 4)] for lon, lat in f(list(coords))]
    return [ring(poly.exterior.coords)] + [ring(i.coords) for i in poly.interiors]


def main():
    index = gazetteer()
    out = []
    older = '--older' in sys.argv
    ref = linework(np.asarray(Image.open(CACHE / ATLAS_REF['scan']).convert('RGB')).astype(float))
    for m in (OLDER_MAPS if older else MAPS):
        a = np.asarray(Image.open(CACHE / m['scan']).convert('RGB')).astype(int)
        if m.get('atlas'):
            P = register(ref, linework(a.astype(float)), ATLAS_REF['frame'])
            f, used = tie_atlas(m, P, index)
            lib, semi = masks_atlas(a.astype(float), region(a.shape, P, ATLAS_REF['frame'], ATLAS_REF['not_map']))
        else:
            f, used = tie(m, a, index)
            lib, semi = masks(a, m)
        lib_p, semi_p = polygons(lib), polygons(semi)
        print(f'  {m["key"]}: {len(lib_p)} liberated areas, {len(semi_p)} semi-liberated')
        out.append({'key': m['key'], 'from': m['from'], 'to': m['to'], 'label': m['label'], 'standIn': m.get('standIn', []),
                    'source': f'{m.get("source", SOURCE)}, {m["sketch"]}',
                    'liberated': [to_lonlat(p, f) for p in lib_p], 'semi': [to_lonlat(p, f) for p in semi_p]})
        if '--check' in sys.argv:
            img = Image.fromarray((a * 0.6 + 100).astype('uint8'))
            d = ImageDraw.Draw(img)
            for p in lib_p:
                d.line(list(p.exterior.coords), fill=(0, 120, 0), width=3)
            for p in semi_p:
                d.line(list(p.exterior.coords), fill=(0, 60, 220), width=3)
            for name, (x, y) in used.items():
                d.ellipse((x - 6, y - 6, x + 6, y + 6), outline=(200, 0, 160), width=2)
            img.save(CACHE / f'check_{m["key"]}{"_older" if older else ""}.png')
    if older:
        return
    OUT.parent.mkdir(exist_ok=True)
    OUT.write_text(json.dumps({'source': SOURCE, 'maps': out}, ensure_ascii=False), encoding='utf-8')
    print(f'wrote {OUT.relative_to(ROOT)}')


if __name__ == '__main__':
    main()
