"""
Each soldier's set of embroidered frames (scripts/make_vez_frames.py): the set of the nationality his record prints
where it is one of the minorities' or the foreigners' (Jews, Albanians, Slovaks, Czechs, Rusyns, Ukrainians, Russians,
Italians, Germans and Austrians, Hungarians), else the set of the part of the land he was born in, else none (the
site then uses the neutral set). The site picks the frame within the set by his name. The part is ours alone: no
record carries it and the site shows nothing of it; the files hold set numbers only.

The part: the birthplace's place as GeoNames resolved it (data-extraction/places/resolved.json, the key
scripts/build_relations.py gives it) or, unresolved, the seat of its municipality, goes to the land GeoNames puts it
in (Vojvodina apart from the rest of Serbia; Kosovo; Macedonia) and within the land to the part of the nearest of
the towns PARTS lists. data-extraction/places/vez_regions.json keeps that for every place and seat: it is written
where the GeoNames cache is (data-extraction/.cache/map1941/geonames/, local) and read elsewhere.

Writes website/data/vez-sets.json (soldier id -> set number, the neutral left out; the record dialog gets a shard of
it with its place files, app/lib/placeFiles.ts) and website/app/data/railVez.json (the same for the home page's
margin portraits, data/wartimePortraits.ts). Run after build_relations.py, and after make_vez_frames.py changed the
sets:
    python scripts/build_vez.py              # counts
    python scripts/build_vez.py --write
"""
from __future__ import annotations

import argparse
import glob
import io
import json
import math
import re
import sys
import zipfile
from collections import Counter, defaultdict
from pathlib import Path

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
sys.path.insert(0, str(Path(__file__).parent))
import build_relations as br  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
GEO = ROOT / 'data-extraction' / '.cache' / 'map1941' / 'geonames'
RESOLVED = ROOT / 'data-extraction' / 'places' / 'resolved.json'
REGIONS = ROOT / 'data-extraction' / 'places' / 'vez_regions.json'
SETS = ROOT / 'data-extraction' / 'places' / 'vez_sets.json'
OUT = ROOT / 'website' / 'data' / 'vez-sets.json'
RAIL = ROOT / 'website' / 'app' / 'data' / 'railVez.json'
WARTIME = ROOT / 'website' / 'app' / 'data' / 'wartimePortraits.ts'

# the nationality a record prints (folded) -> its set
NATIONALITY = [
    (r'^(jevrej|zidov)', 'jevreji'), (r'^(albanac|albanka|siptar)', 'albanci'), (r'^slovak', 'slovaci'),
    (r'^ceh', 'cesi'), (r'^rusin', 'rusini'), (r'^ukrajin', 'ukrajinci'), (r'^rus(kinja)?$', 'rusi'),
    (r'^(talijan|italijan)', 'italijani'), (r'^(nijem|njem|nemac|nemica|austrijan)', 'nemci'), (r'^(madjar|madar)', 'madjari'),
]

# The parts of each land with parts: the towns (lat, lon) whose nearest decides it
PARTS = {
    'si': {
        'si-gorenjska': [(46.24, 14.36), (46.43, 14.06), (46.17, 14.31), (46.34, 14.17), (46.36, 14.31), (46.23, 14.61),
                         (46.05, 14.51), (46.51, 15.08), (46.54, 14.97), (46.59, 15.02), (45.96, 14.66), (46.13, 14.60)],
        'si-primorska': [(46.00, 14.03), (45.96, 13.65), (46.18, 13.73), (45.78, 14.21), (45.71, 13.87), (45.55, 13.73),
                         (45.89, 13.91), (45.79, 14.36), (45.57, 14.24), (46.24, 13.58)],
        'si-dolenjska': [(45.80, 15.17), (45.57, 15.19), (45.65, 15.31), (45.64, 14.86), (45.74, 14.73), (45.90, 15.02),
                         (45.96, 15.49), (45.90, 15.59), (45.86, 15.01)],
        'si-stajerska': [(46.55, 15.65), (46.24, 15.27), (46.42, 15.87), (46.66, 16.17), (46.56, 16.45), (46.52, 16.20),
                         (46.39, 15.57), (46.36, 15.11), (46.15, 15.05), (46.15, 15.23), (46.22, 15.60)],
    },
    'hr': {
        'hr-lika': [(44.55, 15.37), (44.74, 15.71), (44.30, 15.85), (44.56, 15.97), (44.87, 15.24), (44.53, 15.77),
                    (44.65, 15.38), (45.00, 15.13), (44.87, 15.70)],
        'hr-kordun': [(45.11, 15.59), (45.32, 15.70), (45.35, 15.86), (45.19, 15.62), (45.25, 15.68), (45.49, 15.55),
                      (45.27, 15.23), (45.08, 15.36), (45.45, 15.50)],
        'hr-banija': [(45.34, 16.09), (45.44, 16.28), (45.07, 16.37), (45.22, 16.54), (45.30, 15.97)],
        'hr-zagora': [(44.04, 16.20), (44.03, 15.61), (43.86, 16.15), (43.70, 16.64), (43.91, 16.40), (43.45, 17.22),
                      (44.20, 15.68), (43.20, 17.37)],
        'hr-dalmacija': [(44.12, 15.23), (43.73, 15.89), (43.51, 16.44), (43.30, 17.02), (43.17, 16.44), (44.45, 15.06),
                         (43.06, 16.18), (42.96, 17.13), (43.44, 16.69), (43.52, 16.25), (43.38, 16.55), (43.94, 15.45)],
        'hr-dubrovnik': [(42.65, 18.09), (42.58, 18.22), (43.05, 17.65), (43.05, 17.43), (42.84, 17.70)],
        'hr-slavonija': [(45.55, 18.69), (45.29, 18.80), (45.16, 18.02), (45.34, 17.68), (45.83, 17.38), (45.59, 17.22),
                         (45.44, 17.19), (45.26, 17.38), (45.35, 19.00), (45.31, 18.41), (45.49, 18.09), (45.54, 17.88),
                         (45.70, 17.70), (45.08, 18.70), (45.26, 17.20)],
        'hr-zagorje': [(45.81, 15.98), (46.16, 15.88), (46.30, 16.34), (46.38, 16.43), (46.16, 16.83), (45.90, 16.84),
                       (46.02, 16.54), (46.09, 16.07), (45.80, 15.71), (45.67, 15.65), (45.96, 16.24), (46.25, 16.62),
                       (46.04, 17.07)],
        'hr-posavina': [(45.48, 16.37), (45.48, 16.78), (45.71, 16.08), (45.71, 16.39), (45.57, 16.94), (45.75, 16.62),
                        (45.57, 16.63), (45.34, 16.98), (45.58, 16.21)],
        'hr-istra': [(44.87, 13.85), (45.24, 13.94), (45.33, 14.44), (45.40, 14.80), (45.17, 14.69), (44.99, 14.90),
                     (45.09, 14.12), (45.41, 13.97), (45.08, 13.64), (45.23, 13.59), (45.34, 14.31), (45.03, 14.57),
                     (45.13, 14.79), (45.37, 15.08)],
    },
    'ba': {
        'ba-krajina': [(44.77, 17.19), (44.98, 16.71), (44.77, 16.67), (44.53, 16.78), (44.42, 17.08), (44.37, 16.38),
                       (44.55, 16.37), (45.18, 16.81), (44.62, 17.37), (45.14, 17.25), (44.34, 17.27), (44.05, 16.85),
                       (44.18, 16.36), (44.28, 17.08), (45.05, 16.38), (44.91, 17.30), (44.87, 17.66), (44.72, 17.32),
                       (44.49, 17.38), (45.21, 16.54)],
        'ba-cazin': [(44.81, 15.87), (44.97, 15.94), (45.18, 15.81), (45.05, 16.03), (44.88, 16.15)],
        'ba-hercegovina': [(43.34, 17.81), (42.71, 18.34), (43.26, 18.11), (43.17, 18.53), (42.88, 18.43), (43.08, 17.96),
                           (43.20, 17.55), (43.65, 17.96), (43.12, 17.68), (43.83, 17.01), (43.99, 17.28), (43.72, 17.23),
                           (43.47, 17.33), (43.38, 17.59), (43.82, 17.61), (43.66, 17.76), (42.95, 18.09), (42.92, 17.62)],
        'ba-srednja': [(43.86, 18.41), (44.20, 17.91), (44.23, 17.66), (43.99, 18.18), (44.13, 18.12), (44.16, 18.33),
                       (44.06, 17.45), (43.96, 17.89), (43.94, 18.08), (44.10, 17.88), (44.16, 17.79), (44.14, 17.40),
                       (43.94, 17.59), (43.82, 18.20), (43.95, 18.27), (43.67, 18.45), (43.82, 18.57), (44.43, 18.04),
                       (44.45, 18.15), (44.13, 18.58), (44.02, 18.26)],
        'ba-tuzla': [(44.54, 18.68), (44.76, 19.21), (44.73, 18.08), (44.87, 18.81), (44.70, 18.31), (44.64, 18.84),
                     (45.03, 18.69), (44.98, 17.91), (44.61, 17.86), (44.55, 18.10), (44.96, 18.30), (45.14, 18.01),
                     (45.01, 18.33), (45.06, 18.47), (44.44, 18.87), (44.45, 18.65), (44.54, 18.53), (44.71, 18.49),
                     (44.41, 18.53), (44.23, 18.69), (44.69, 18.99), (44.61, 17.99)],
        'ba-istok': [(43.51, 18.78), (43.78, 19.29), (43.80, 19.00), (43.94, 18.80), (44.18, 18.94), (44.10, 19.30),
                     (43.50, 18.45), (43.67, 18.98), (43.56, 19.07), (44.08, 18.95), (44.39, 19.10), (44.19, 19.33),
                     (43.62, 19.37), (44.17, 19.08), (44.30, 18.86)],
    },
    'me': {
        'me-stara': [(42.39, 18.92), (42.44, 19.26), (42.77, 18.94), (42.55, 19.11), (42.25, 19.09), (42.36, 19.02)],
        'me-brda': [(42.82, 19.52), (42.73, 19.79), (42.96, 19.10), (43.15, 19.12), (43.15, 18.84), (42.96, 19.58), (42.62, 19.49)],
        'me-boka': [(42.42, 18.77), (42.45, 18.53), (42.29, 18.84), (42.43, 18.70), (42.10, 19.09), (42.51, 18.70)],
        'sandzak': [(43.36, 19.36), (43.04, 19.75), (42.84, 20.17), (42.60, 19.94), (42.84, 19.87), (42.56, 19.83)],
        'albanci': [(41.93, 19.22), (42.36, 19.33)],
    },
    'rs': {
        'rs-sumadija': [(44.01, 20.91), (44.82, 20.46), (43.72, 20.69), (43.98, 21.26), (44.66, 20.93), (44.03, 20.46),
                        (44.31, 20.56), (44.44, 20.70), (44.38, 20.26), (44.25, 20.68), (43.86, 21.41), (43.93, 21.37),
                        (44.23, 21.19), (43.62, 21.00), (44.37, 20.96), (44.65, 20.20)],
        'rs-zapad': [(43.86, 19.85), (44.27, 19.89), (44.75, 19.69), (44.53, 19.22), (43.75, 19.72), (43.85, 20.04),
                     (43.75, 20.10), (43.58, 20.23), (44.00, 19.91), (43.89, 20.35), (43.97, 19.57), (44.19, 19.37),
                     (44.37, 19.36), (44.46, 20.07), (44.25, 20.08), (43.86, 20.14), (44.84, 19.48)],
        'rs-istok': [(43.90, 22.28), (43.57, 22.26), (44.23, 22.53), (44.07, 22.10), (44.62, 21.19), (44.38, 21.42),
                     (44.48, 21.67), (43.83, 21.96), (44.42, 21.94), (44.61, 22.61), (44.09, 21.44), (44.76, 21.52),
                     (44.65, 21.63), (44.20, 21.79), (43.64, 21.87)],
        'rs-jug': [(43.32, 21.90), (43.15, 22.59), (43.00, 21.95), (42.55, 21.90), (43.23, 21.59), (43.14, 21.27),
                   (43.58, 21.33), (43.54, 21.71), (42.97, 22.13), (43.02, 22.78), (43.07, 22.41), (43.22, 22.31),
                   (42.69, 22.17), (42.81, 22.30), (42.46, 21.77), (42.31, 21.65), (42.92, 21.73), (42.84, 21.58),
                   (43.29, 21.29), (43.38, 21.03), (43.18, 21.71), (43.46, 21.05)],
        'sandzak': [(43.14, 20.51), (43.27, 20.00), (42.99, 20.34), (43.39, 19.65), (43.58, 19.53), (43.46, 19.81)],
    },
    'vo': {
        'vo-srem': [(44.97, 19.61), (45.00, 19.82), (45.05, 20.08), (44.98, 20.16), (45.13, 19.23), (45.10, 19.86),
                    (44.91, 19.97), (45.20, 19.93), (45.21, 19.72)],
        'vo-banat': [(45.38, 20.39), (44.87, 20.64), (45.12, 21.30), (45.83, 20.47), (45.11, 20.62), (45.08, 20.97),
                     (44.90, 21.42), (45.60, 20.13), (45.37, 20.77), (44.75, 20.97), (45.05, 20.43), (45.48, 20.55),
                     (45.67, 20.61), (45.23, 21.12), (46.04, 20.10), (45.94, 20.14)],
        'vo-backa': [(45.25, 19.84), (46.10, 19.67), (45.77, 19.11), (45.25, 19.39), (45.36, 19.59), (45.61, 19.53),
                     (45.57, 19.64), (45.62, 20.03), (45.93, 20.08), (45.21, 20.29), (45.41, 19.88), (45.67, 18.98),
                     (45.51, 19.26), (45.39, 19.24), (45.81, 19.63), (45.80, 20.13), (46.07, 20.06), (45.37, 20.06),
                     (45.55, 19.79), (45.71, 19.67)],
    },
}
ONE_SET = {'mk': 'mk', 'xk': 'rs-kosovo'}
# the parts a birthplace may name by the region alone ("Melenci, Banat"); Posavina and Krajina are on both sides
REGION_WORDS = {'lika': 'hr-lika', 'kordun': 'hr-kordun', 'banija': 'hr-banija', 'slavonija': 'hr-slavonija',
                'zagorje': 'hr-zagorje', 'dalmacija': 'hr-dalmacija', 'istra': 'hr-istra', 'gorski kotar': 'hr-istra',
                'boka': 'me-boka', 'sumadija': 'rs-sumadija', 'srem': 'vo-srem', 'banat': 'vo-banat', 'backa': 'vo-backa',
                'sandzak': 'sandzak', 'kosovo': 'rs-kosovo', 'metohija': 'rs-kosovo', 'semberija': 'ba-tuzla',
                'hercegovina': 'ba-hercegovina', 'makedonija': 'mk'}
# the names of the time for towns GeoNames knows by today's, and the towns abroad whose people were Slovenes
OLD_NAMES = {'titograd': 'podgorica', 'ivangrad': 'berane', 'titovo uzice': 'uzice', 'titov veles': 'veles',
             'titova korenica': 'korenica', 'titov drvar': 'drvar', 'titova mitrovica': 'mitrovica',
             'kosovska mitrovica': 'mitrovica', 'bosanski novi': 'novi grad', 'bosanska dubica': 'kozarska dubica',
             'bosanska gradiska': 'gradiska', 'bosanski samac': 'samac', 'bosanski brod': 'brod',
             'bosanska kostajnica': 'kostajnica', 'titov vrbas': 'vrbas'}
ABROAD = {'trst': 'si-primorska', 'trieste': 'si-primorska', 'gorica': 'si-primorska', 'gorizia': 'si-primorska'}
ABBREVIATIONS = [(r'^d\. ?', ('donji ', 'donja ', 'donje ')), (r'^g\. ?', ('gornji ', 'gornja ', 'gornje ')),
                 (r'^bos\. ?', ('bosanski ', 'bosanska ', 'bosansko ')), (r'^hrv\. ?', ('hrvatska ', 'hrvatski ')),
                 (r'^sl\. ?', ('slavonski ', 'slavonska ')), (r'^n\. ?', ('novi ', 'nova ', 'novo ')),
                 (r'^v\. ?', ('veliki ', 'velika ', 'veliko ')), (r'^m\. ?', ('mali ', 'mala ', 'malo '))]


def readings(word: str) -> list[str]:
    """a folded place name as printed and as GeoNames may know it: the abbreviations spelled out, the old names"""
    out = [word]
    river = re.match(r'^(.+?) (?:na|pri|ob|ponad) \w+$', word)       # "Priboj na Limu", "Šempeter pri Gorici"
    if river:
        out.append(river.group(1))
    for pattern, full in ABBREVIATIONS:
        if re.match(pattern, word):
            out += [re.sub(pattern, f, word) for f in full]
    return out + [OLD_NAMES[w] for w in list(out) if w in OLD_NAMES]


def land_of(cc: str, a1: str) -> str | None:
    cc = cc.lower()
    if cc == 'rs':
        return 'vo' if a1 == 'VO' else 'rs'
    return cc if cc in PARTS or cc in ONE_SET else None


def part_of(land: str, lat: float, lon: float) -> str:
    if land in ONE_SET:
        return ONE_SET[land]
    best = None
    for name, towns in PARTS[land].items():
        for la, lo in towns:
            d = (la - lat) ** 2 + ((lo - lon) * math.cos(math.radians(la))) ** 2
            if best is None or d < best[0]:
                best = (d, name)
    return best[1]


def regions(wanted: set[str]) -> dict:
    """{places: GeoNames id -> part, seats: folded name of a town or seat of administration -> part, names: the
    same for any place}, a name only where every town (or place) of it lies in one part, and only the names the
    birthplaces print; from the GeoNames cache where it is, else as last written"""
    if not GEO.exists():
        return json.loads(REGIONS.read_text(encoding='utf-8'))
    resolved = json.loads(RESOLVED.read_text(encoding='utf-8'))['places']
    places, seats, names = {}, defaultdict(set), defaultdict(set)
    for path in sorted(glob.glob(str(GEO / '*.zip'))):
        cc = Path(path).name[:2]
        for line in io.TextIOWrapper(zipfile.ZipFile(path).open(f'{cc}.txt'), encoding='utf-8'):
            f = line.rstrip('\n').split('\t')
            land = land_of(cc, f[10])
            if not land:
                continue
            lat, lon = float(f[4]), float(f[5])
            if f[0] in resolved:
                places[f[0]] = part_of(land, lat, lon)
            if f[6] == 'P':
                town = f[7].startswith('PPLA') or f[7] == 'PPLC' or int(f[14] or 0) > 5000
                for name in {br.fold(f[1]), br.fold(f[2])} & wanted:
                    names[name].add(part_of(land, lat, lon))
                    if town:
                        seats[name].add(part_of(land, lat, lon))
    one = lambda table: {k: next(iter(v)) for k, v in sorted(table.items()) if len(v) == 1}
    return {'about': 'Each resolved place, and each name of a town (seats) or any place (names) the birthplaces print '
                     'whose towns or places all lie in one part, by the part of the land, for the embroidered frames '
                     '(scripts/build_vez.py); read where the GeoNames cache is missing.',
            'places': dict(sorted(places.items())), 'seats': one(seats), 'names': one(names)}


def nationality(s: dict) -> str | None:
    e = br.fold(s.get('ethnicity') or '')
    for pattern, name in NATIONALITY:
        if re.search(pattern, e):
            return name
    return None


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--write', action='store_true')
    args = ap.parse_args()

    names = [name for name, _ in json.loads(SETS.read_text(encoding='utf-8'))['sets']]
    number = {name: i for i, name in enumerate(names)}
    files, recs = br.load()
    raws = Counter(s['birth_place'].strip() for _, s in recs if s.get('birth_place'))
    places = br.Places(raws)
    keyed, _ = places.keys(recs)
    keyed, _ = br.by_resolved_place(files, recs, keyed)
    reg = regions({w for r in raws for seg in places.seg[r] for w in readings(br.fold(seg))})

    def by_name(raw: str) -> str | None:
        """the part a birthplace names: its municipality before its village, a town's name before any place's, else
        a region it names"""
        segs = [w for seg in reversed(places.seg.get(raw) or []) for w in readings(br.fold(seg))]
        for table in ('seats', 'names'):
            for w in segs:
                if w in ABROAD:
                    return ABROAD[w]
                if reg[table].get(w):
                    return reg[table][w]
        words = br.fold(raw)
        return next((part for word, part in REGION_WORDS.items() if re.search(rf'\b{word}\b', words)), None)

    out, how, alias = {}, Counter(), {}
    for fi, s in recs:
        sid = s['soldier_id']
        for o in s.get('other_sources') or []:
            if o.get('soldier_id') and o['soldier_id'] != sid:
                alias.setdefault(o['soldier_id'], sid)
        part = nationality(s)
        if part:
            how['nationality'] += 1
        else:
            r = (s.get('birth_place') or '').strip()
            key = keyed.get((fi, r))
            if key and key[0] == 'place':
                part = reg['places'].get(str(key[1]))
            if not part and r:
                part = by_name(r)
            how['place' if part else 'unknown' if r else 'no birthplace'] += 1
        if part and part != 'neutralni':
            out[sid] = number[part]
    sets_count = Counter(names[n] for n in out.values())
    print(f'soldiers {len(recs)}: {dict(how)}')
    print('by set:', ', '.join(f'{k} {v}' for k, v in sets_count.most_common()))

    wartime = re.findall(r"'(\d{10})'", WARTIME.read_text(encoding='utf-8'))
    rail = {i: out[alias.get(i, i)] for i in wartime if alias.get(i, i) in out}
    print(f'margin portraits {len(wartime)}, with a set {len(rail)}:',
          ', '.join(f'{k} {v}' for k, v in Counter(names[n] for n in rail.values()).most_common()))

    if args.write:
        if GEO.exists():
            REGIONS.write_text(json.dumps(reg, ensure_ascii=False, indent=0) + '\n', encoding='utf-8')
        OUT.parent.mkdir(parents=True, exist_ok=True)
        OUT.write_text(json.dumps(dict(sorted(out.items())), separators=(',', ':')) + '\n', encoding='utf-8')
        RAIL.write_text(json.dumps(dict(sorted(rail.items())), separators=(',', ':')) + '\n', encoding='utf-8')
        print(f'wrote {OUT.relative_to(ROOT)} ({OUT.stat().st_size / 1e6:.1f} MB), {RAIL.relative_to(ROOT)}')


if __name__ == '__main__':
    main()
