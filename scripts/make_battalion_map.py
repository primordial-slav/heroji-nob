"""The ground of a battalion's close-up sheets on the map page (/mapa/bataljon, local only): the hills as contours,
the railway, the roads, the rivers and lakes, the villages and the heights the books give as "kota".

Sources, each cached in data-extraction/.cache/battalion/:
- elevation: AWS Terrain Tiles (Mapzen's terrarium encoding; in Europe EU-DEM, produced using Copernicus data and
  information funded by the European Union, and SRTM), zoom 12, about 27 m a pixel here
- railway, roads, rivers, lakes, hamlets and peaks: OpenStreetMap (ODbL, (c) OpenStreetMap contributors), one
  Overpass request for the region
- villages and heights: GeoNames (CC BY 4.0), the country files make_unit_route.py uses

The sheet is in kilometres from the region's middle, x to the east and y to the south (at this size a plain
equirectangular grid is true to a few metres). Writes website/app/(sr)/mapa/bataljon/terrain/<region>.ts, one file
a region, which the page loads when an episode there is opened.

    python scripts/make_battalion_map.py [region ...]                 write the regions' ground (all without one)
    python scripts/make_battalion_map.py --kote region lon lat [km]   where a height the book gives is: the DEM's
                                                                      summits within km (1.5) of a guess
"""
import io
import json
import math
import subprocess
import sys
import time
import unicodedata
import zipfile
from pathlib import Path

import contourpy
import numpy as np
from PIL import Image
from scipy import ndimage
from shapely.geometry import LineString, Point

sys.stdout.reconfigure(encoding='utf-8')
ROOT = Path(__file__).resolve().parents[1]
CACHE = ROOT / 'data-extraction' / '.cache' / 'battalion'
GEONAMES = ROOT / 'data-extraction' / '.cache' / 'map1941' / 'geonames'
OUT_DIR = ROOT / 'website' / 'app' / '(sr)' / 'mapa' / 'bataljon' / 'terrain'

# Where the 2. bataljon of the Prva lička fought in 1942, a sheet each. `towns` are lettered as towns; `old_rail`
# draws the lines OpenStreetMap has as disused or abandoned, where the book shows them working in the war; `jna`
# adds places the book names that OSM lacks, read from the JNA map 1:25,000 (quality/tk25) or GeoNames: name, lon,
# lat, kind
REGIONS = {
    # the plašćanska dolina, Mala Kapela and the country round Brinje and Dabar: the summer of 1942
    'kapela': {'west': 15.00, 'east': 15.58, 'south': 44.84, 'north': 45.22,
               'towns': {'Plaški', 'Brinje', 'Otočac', 'Saborsko', 'Vrhovine', 'Josipdol', 'Ogulin'},
               # the northern of Pothum Plaščanski's two hamlets Vorkapići, by the 388 crossing (OSM has neither)
               'jna': [('Vorkapići', 15.3442, 45.1379, 'hamlet')]},
    # the Lika valley under Velebit, Kosinj to Pazarišta and Perušić: September 1942; Gospić and its railway: 1943
    'kosinj': {'west': 15.10, 'east': 15.50, 'south': 44.45, 'north': 44.80,
               'towns': {'Gospić', 'Perušić', 'Gornji Kosinj', 'Donji Kosinj'}},
    # Glina and the Maja's valley up to Šamarica: October 1942
    'glina': {'west': 15.96, 'east': 16.30, 'south': 45.20, 'north': 45.42,
              'towns': {'Glina', 'Petrinja', 'Topusko'}, 'old_rail': True,
              'jna': [('Crni Lug', 16.1060, 45.3268, 'village'), ('Jukinac', 16.0975, 45.3485, 'hamlet')]},
    # Slunj, the Korana and Melnice, Lađevac and Rakovica: November 1942
    'slunj': {'west': 15.45, 'east': 15.73, 'south': 44.97, 'north': 45.20,
              'towns': {'Slunj', 'Rakovica'},
              # GeoNames: the church above Brezovac and the locality by it, where the II stood in July 1942
              'jna': [('Sveta Petka', 15.6564, 45.0531, 'hamlet'), ('Oklinak', 15.6750, 45.0542, 'hamlet')]},
    # the Una between Dvor and Kostajnica, and Zrinska gora: the end of November 1942
    'dvor': {'west': 16.28, 'east': 16.58, 'south': 45.03, 'north': 45.25,
             'towns': {'Dvor', 'Hrvatska Kostajnica', 'Bosanska Kostajnica', 'Novi Grad'}},
    # Gračac, Bruvno, Mazin and the Lapac valley: January and February 1943 (to Jošan and Kulen-Vakuf in the north)
    'gracac': {'west': 15.70, 'east': 16.12, 'south': 44.24, 'north': 44.62,
               'towns': {'Gračac', 'Bruvno', 'Mazin', 'Donji Lapac', 'Gornji Lapac', 'Srb', 'Udbina'},
               # the hamlet Vagan in its valley west of the road from Mazin to Gornji Lapac (JNA map 470-2-2,
               # GeoNames; OSM has only Vagan Popinski)
               'jna': [('Vagan', 15.9564, 44.4944, 'hamlet')]},
    # Udbina, Komić and the Lika railway from Medak to Lovinac: December 1942
    'lovinac': {'west': 15.45, 'east': 15.86, 'south': 44.31, 'north': 44.59,
                'towns': {'Udbina', 'Lovinac', 'Medak', 'Sveti Rok'},
                # Kurjak's hamlet Baste, where the road west to Ploča leaves the road south to Komić
                'jna': [('Baste', 15.7208, 44.4923, 'hamlet')]},
}
REGION: dict = {}
LON0 = LAT0 = KX = 0.0
KY = 110.574                                     # km a degree of latitude


def use(key: str):
    """Set the region the functions below work in"""
    global REGION, LON0, LAT0, KX
    REGION = {'key': key, **REGIONS[key]}
    LON0 = (REGION['west'] + REGION['east']) / 2
    LAT0 = (REGION['south'] + REGION['north']) / 2
    KX = 111.320 * math.cos(math.radians(LAT0))  # km a degree of longitude here


ZOOM = 12
STEP = 50                                        # the contours' interval, in metres
INDEX = 250                                      # every fifth drawn stronger


def km(lon: float, lat: float) -> tuple[float, float]:
    return (lon - LON0) * KX, (LAT0 - lat) * KY


def fetch(url: str, path: Path, data: str | None = None) -> Path:
    if path.exists():
        return path
    path.parent.mkdir(parents=True, exist_ok=True)
    cmd = ['curl', '-sS', '-L', '-f', '-m', '600', '-A', 'knjiga-boraca-map/1.0', '-o', str(path), url]
    if data is not None:
        query = path.with_suffix('.query')
        query.write_text(data, encoding='utf-8')
        cmd[1:1] = ['--data-urlencode', f'data@{query}']
    for attempt in range(4):
        if subprocess.run(cmd).returncode == 0:
            time.sleep(0.3)                      # gently, one request at a time
            return path
        time.sleep(5 * (attempt + 1))
    raise SystemExit(f'could not fetch {url}')


# ---------- the elevation ----------

def tile_x(lon: float) -> float:
    return (lon + 180) / 360 * 2 ** ZOOM


def tile_y(lat: float) -> float:
    r = math.radians(lat)
    return (1 - math.log(math.tan(r) + 1 / math.cos(r)) / math.pi) / 2 * 2 ** ZOOM


def tile_lon(x: float) -> float:
    return x / 2 ** ZOOM * 360 - 180


def tile_lat(y: float) -> float:
    return math.degrees(math.atan(math.sinh(math.pi * (1 - 2 * y / 2 ** ZOOM))))


def elevation():
    """The region's heights in metres, with each column's longitude and each row's latitude (the tiles are Web
    Mercator, so both are separable)"""
    x0, x1 = int(tile_x(REGION['west'])), int(tile_x(REGION['east']))
    y0, y1 = int(tile_y(REGION['north'])), int(tile_y(REGION['south']))
    rows = []
    for ty in range(y0, y1 + 1):
        row = []
        for tx in range(x0, x1 + 1):
            path = fetch(f'https://s3.amazonaws.com/elevation-tiles-prod/terrarium/{ZOOM}/{tx}/{ty}.png',
                         CACHE / 'terrarium' / f'{ZOOM}_{tx}_{ty}.png')
            rgb = np.asarray(Image.open(io.BytesIO(path.read_bytes())).convert('RGB'), dtype=np.float64)
            row.append(rgb[..., 0] * 256 + rgb[..., 1] + rgb[..., 2] / 256 - 32768)
        rows.append(np.hstack(row))
    dem = np.vstack(rows)
    n = dem.shape[0] // (y1 - y0 + 1)
    lons = np.array([tile_lon(x0 + (i + 0.5) / n) for i in range(dem.shape[1])])
    lats = np.array([tile_lat(y0 + (j + 0.5) / n) for j in range(dem.shape[0])])
    return dem, lons, lats


def contours(dem, lons, lats):
    """The contours every STEP metres, smoothed a little (the tiles' grain is not the ground's) and thinned to what
    the sheet can show"""
    smooth = ndimage.gaussian_filter(dem, 1.3)
    xs = np.array([km(lon, LAT0)[0] for lon in lons])
    ys = np.array([km(LON0, lat)[1] for lat in lats])
    gen = contourpy.contour_generator(xs, ys, smooth, line_type='Separate')
    out = []
    lo, hi = int(smooth.min() // STEP + 1) * STEP, int(smooth.max() // STEP) * STEP
    for level in range(lo, hi + 1, STEP):
        for line in gen.lines(level):
            if len(line) < 6:
                continue
            ls = LineString(line).simplify(0.012)
            if ls.length < 0.25:                 # a knoll's last ring, smaller than the sheet's pen
                continue
            pts = list(ls.coords)
            out.append({'h': level, 'i': level % INDEX == 0, 'd': path_of(pts), 'b': bbox(pts)})
    return out


def path_of(pts) -> str:
    """An SVG path in relative steps, to two decimals (10 m)"""
    x0, y0 = pts[0]
    parts = [f'M{x0:.2f} {y0:.2f}l']
    px, py = round(x0, 2), round(y0, 2)
    steps = []
    for x, y in pts[1:]:
        x, y = round(x, 2), round(y, 2)
        if (x, y) == (px, py):
            continue
        steps.append(f'{x - px:.2f} {y - py:.2f}'.replace('.00', '').replace('-0 ', '0 '))
        px, py = x, y
    return parts[0] + ' '.join(steps)


def summits(dem, lons, lats, radius_px: int = 6):
    """The DEM's tops: a point higher than everything within radius_px"""
    peak = ndimage.maximum_filter(dem, size=2 * radius_px + 1)
    js, iis = np.nonzero((dem == peak) & (dem > 0))
    return [(lons[i], lats[j], float(dem[j, i])) for j, i in zip(js, iis)]


# ---------- OpenStreetMap ----------

def osm():
    s, w, n, e = REGION['south'], REGION['west'], REGION['north'], REGION['east']
    box = f'({s},{w},{n},{e})'
    query = (f'[out:json][timeout:180];('
             f'way["railway"~"^(rail|disused|abandoned|narrow_gauge)$"]{box};'
             f'way["highway"~"^(primary|secondary|tertiary|unclassified)$"]{box};'
             f'way["waterway"~"^(river|stream|canal)$"]{box};'
             f'way["natural"="water"]{box};relation["natural"="water"]{box};'
             f'node["place"~"^(town|village|hamlet|isolated_dwelling|locality|neighbourhood)$"]{box};'
             f'node["natural"~"^(peak|hill|saddle)$"]{box};'
             f'node["railway"~"^(station|halt)$"]{box};'
             f');out geom;')
    path = fetch('https://overpass-api.de/api/interpreter', CACHE / f'osm_{REGION["key"]}.json', query)
    return json.loads(path.read_text(encoding='utf-8'))['elements']


def fold(s: str) -> str:
    return ''.join(c for c in unicodedata.normalize('NFD', s.lower()) if unicodedata.category(c) != 'Mn')


def geonames():
    rows = []
    for country in ('HR', 'BA'):                 # the Una is the border at Dvor and Kostajnica
        with zipfile.ZipFile(GEONAMES / f'{country}.zip') as z:
            for line in z.read(f'{country}.txt').decode('utf-8').splitlines():
                f = line.split('\t')
                lat, lon = float(f[4]), float(f[5])
                if REGION['west'] <= lon <= REGION['east'] and REGION['south'] <= lat <= REGION['north']:
                    rows.append({'name': f[1], 'fc': f[6], 'code': f[7], 'lat': lat, 'lon': lon,
                                 'ele': int(f[16] or f[15] or 0)})
    return rows


# ---------- the sheet's features ----------

ROAD_CLASS = {'primary': 1, 'secondary': 2, 'tertiary': 3, 'unclassified': 4}
# what came after the war: the reservoirs and the power plants' canals
LATER_WATER = ('reservoir', 'basin', 'pond', 'canal', 'wastewater')
PLACE_RANK = {'town': 1, 'village': 1, 'hamlet': 2, 'neighbourhood': 3, 'isolated_dwelling': 3, 'locality': 3}


def line_of(geom):
    return [km(p['lon'], p['lat']) for p in geom]


def bbox(pts):
    xs, ys = [p[0] for p in pts], [p[1] for p in pts]
    return [round(min(xs), 2), round(min(ys), 2), round(max(xs), 2), round(max(ys), 2)]


def features(els, gn):
    rail, roads, rivers, lakes, places, peaks = [], [], [], [], {}, []
    lines = ('rail', 'disused', 'abandoned') if REGION.get('old_rail') else ('rail',)
    for e in els:
        t = e.get('tags', {})
        if e['type'] == 'way' and t.get('railway') in lines:
            pts = list(LineString(line_of(e['geometry'])).simplify(0.004).coords)
            rail.append({'d': path_of(pts), 'tunnel': t.get('tunnel') == 'yes', 'b': bbox(pts)})
        elif e['type'] == 'way' and t.get('highway') in ROAD_CLASS:
            pts = list(LineString(line_of(e['geometry'])).simplify(0.006).coords)
            roads.append({'d': path_of(pts), 'c': ROAD_CLASS[t['highway']], 'b': bbox(pts)})
        elif e['type'] == 'way' and t.get('waterway') in ('river', 'stream') and (t.get('name') or t['waterway'] == 'river'):
            pts = list(LineString(line_of(e['geometry'])).simplify(0.006).coords)
            rivers.append({'name': t.get('name', ''), 'big': t['waterway'] == 'river', 'd': path_of(pts), 'b': bbox(pts)})
        elif t.get('natural') == 'water' and t.get('water') not in LATER_WATER and e['type'] == 'way':
            pts = line_of(e['geometry'])
            if len(pts) >= 4:
                lakes.append({'name': t.get('name', ''), 'd': path_of(pts) + 'z', 'b': bbox(pts)})
        elif e['type'] == 'node' and t.get('place') in PLACE_RANK and t.get('name'):
            x, y = km(e['lon'], e['lat'])
            # a town's name lettered as a town only on the town or village itself, not on a hamlet of the same name
            # (OSM has a hamlet Udbina by Vrebac, 21 km from the town)
            town = t['name'] in REGION['towns'] and t['place'] in ('city', 'town', 'village')
            rank = 0 if town else PLACE_RANK[t['place']]
            places[(t['name'], round(x, 1), round(y, 1))] = {'name': t['name'], 'x': round(x, 3), 'y': round(y, 3), 'r': rank}
        elif e['type'] == 'node' and t.get('natural') == 'peak' and t.get('name') and t.get('ele'):
            try:
                h = round(float(t['ele'].replace(',', '.')))
            except ValueError:
                continue
            x, y = km(e['lon'], e['lat'])
            peaks.append({'name': t['name'], 'x': round(x, 3), 'y': round(y, 3), 'h': h})
    for name, lon, lat, kind in REGION.get('jna', ()):
        x, y = km(lon, lat)
        places[(name, round(x, 1), round(y, 1))] = {'name': name, 'x': round(x, 3), 'y': round(y, 3), 'r': PLACE_RANK[kind]}
    # a lake the books name that OSM draws as no shape: a small mark at its place
    for g in gn:
        if g['fc'] == 'H' and g['code'] == 'LK' and g['name'] == 'Jezero Begovac':
            x, y = km(g['lon'], g['lat'])
            lakes.append({'name': 'jezero', 'd': f'M{x - 0.14:.2f} {y:.2f}a0.14 0.08 0 1 0 0.28 0a0.14 0.08 0 1 0-0.28 0z',
                          'b': [round(x - 0.14, 2), round(y - 0.08, 2), round(x + 0.14, 2), round(y + 0.08, 2)]})
    # the stations the book's fights were at, which OSM leaves out
    stations = []
    for g in gn:
        if g['fc'] == 'S' and g['code'] in ('RSTN', 'RSTP', 'RSTPQ'):
            x, y = km(g['lon'], g['lat'])
            name = g['name'].replace('Lička Jesenica', 'Jesenica')
            stations.append({'name': name, 'x': round(x, 3), 'y': round(y, 3)})
    return rail, roads, rivers, lakes, sorted(places.values(), key=lambda p: (p['r'], p['name'])), peaks, stations


def write(dem, lons, lats, els):
    gn = geonames()
    lines = contours(dem, lons, lats)
    rail, roads, rivers, lakes, places, peaks, stations = features(els, gn)
    # a line the thinning left a single point draws nothing (and an SVG path of one point is an error)
    lines, rail, roads, rivers = ([x for x in group if not x['d'].endswith('l')] for group in (lines, rail, roads, rivers))
    x0, y0 = km(REGION['west'], REGION['north'])
    x1, y1 = km(REGION['east'], REGION['south'])
    out = [
        '// Generated by scripts/make_battalion_map.py: elevation from the AWS Terrain Tiles (EU-DEM, produced using',
        '// Copernicus data funded by the European Union, and SRTM), the railway, roads, rivers, lakes, hamlets and',
        '// peaks from OpenStreetMap (ODbL, (c) OpenStreetMap contributors), the stations from GeoNames (CC BY 4.0).',
        '// Do not edit by hand: change the script and run it. Kilometres from the region\'s middle, x east, y south.',
        '',
        f'export const REGION = {json.dumps({"key": REGION["key"], "lon0": LON0, "lat0": LAT0, "kx": KX, "ky": KY, "bounds": [round(x0, 2), round(y0, 2), round(x1, 2), round(y1, 2)]})}',
        f'export const CONTOUR_STEP = {STEP}',
        f'export const CONTOURS: {{ h: number; i: boolean; d: string; b: number[] }}[] = {json.dumps(lines, ensure_ascii=False, separators=(",", ":"))}',
        f'export const RAIL: {{ d: string; tunnel: boolean; b: number[] }}[] = {json.dumps(rail, separators=(",", ":"))}',
        f'export const ROADS: {{ d: string; c: number; b: number[] }}[] = {json.dumps(roads, separators=(",", ":"))}',
        f'export const RIVERS: {{ name: string; big: boolean; d: string; b: number[] }}[] = {json.dumps(rivers, ensure_ascii=False, separators=(",", ":"))}',
        f'export const LAKES: {{ name: string; d: string; b: number[] }}[] = {json.dumps(lakes, ensure_ascii=False, separators=(",", ":"))}',
        f'export const PLACES: {{ name: string; x: number; y: number; r: number }}[] = {json.dumps(places, ensure_ascii=False, separators=(",", ":"))}',
        f'export const PEAKS: {{ name: string; x: number; y: number; h: number }}[] = {json.dumps(peaks, ensure_ascii=False, separators=(",", ":"))}',
        f'export const STATIONS: {{ name: string; x: number; y: number }}[] = {json.dumps(stations, ensure_ascii=False, separators=(",", ":"))}',
        '',
    ]
    out_path = OUT_DIR / f'{REGION["key"]}.ts'
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    out_path.write_text('\n'.join(out), encoding='utf-8')
    print(f'{out_path.name}: {out_path.stat().st_size / 1e6:.1f} MB; {len(lines)} contours, {len(rail)} rail, {len(roads)} roads, '
          f'{len(rivers)} rivers, {len(lakes)} lakes, {len(places)} places, {len(peaks)} peaks, {len(stations)} stations')


if __name__ == '__main__':
    args = sys.argv[1:]
    if args and args[0] == '--kote':
        use(args[1])
        lon0, lat0 = float(args[2]), float(args[3])
        radius = float(args[4]) if len(args) > 4 else 1.5
        dem, lons, lats = elevation()
        near = []
        for lon, lat, h in summits(dem, lons, lats, 4):
            d = math.hypot((lon - lon0) * KX, (lat - lat0) * KY)
            if d <= radius:
                near.append((h, d, lon, lat))
        for h, d, lon, lat in sorted(near, reverse=True)[:25]:
            print(f'{lon:.4f} {lat:.4f} {h:5.0f} m  {d:.2f} km')
    else:
        for key in args or list(REGIONS):
            use(key)
            dem, lons, lats = elevation()
            write(dem, lons, lats, osm())
