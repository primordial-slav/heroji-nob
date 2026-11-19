"""The resolved places that are an area, not a settlement: a region, a mountain, a river, a valley, an island
(data-extraction/places/areas.json: GeoNames id -> [class, code, name]), so that scripts/record_sources.py reads a
place of death inside one as no other place ("Kozara" and Bosanska Dubica at its foot, "Neretva" and Jablanica). The
kinds come from GeoNames (geonames.org, CC BY 4.0) through our local places tool's output, quality/places/places.json
(quality/places/gazetteer.py), for every place data-extraction/places/resolved.json names.

Run it after the gazetteer writes resolved.json anew (python quality/places/gazetteer.py --site):
    python scripts/area_places.py            # counts by kind
    python scripts/area_places.py --write    # write data-extraction/places/areas.json
"""
from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path

from safe_write import write_text

ROOT = Path(__file__).resolve().parent.parent
PLACES = ROOT / 'quality' / 'places' / 'places.json'
RESOLVED = ROOT / 'data-extraction' / 'places' / 'resolved.json'
OUT = ROOT / 'data-extraction' / 'places' / 'areas.json'


def main():
    sys.stdout.reconfigure(encoding='utf-8')
    ap = argparse.ArgumentParser()
    ap.add_argument('--write', action='store_true')
    ap.add_argument('--places', default=str(PLACES), help="the places tool's output (default quality/places/places.json)")
    args = ap.parse_args()
    wanted = {int(g) for g in json.loads(RESOLVED.read_text(encoding='utf-8'))['places']}
    areas = {}
    for r in json.loads(Path(args.places).read_text(encoding='utf-8'))['rows']:
        g = r.get('gid')
        if g in wanted and r.get('kind') and r['kind'] != 'P' and str(g) not in areas:
            areas[str(g)] = [r['kind'], r.get('code') or '', r.get('name') or '']
    print(f'{len(areas)} areas of {len(wanted)} resolved places:',
          ', '.join(f'{k}.{c} {n}' for (k, c), n in Counter((v[0], v[1]) for v in areas.values()).most_common(15)))
    if args.write:
        doc = {'about': 'The places of data-extraction/places/resolved.json that are an area, not a settlement (GeoNames, '
                        'geonames.org, CC BY 4.0): id -> [feature class (A land, H water, L region, T terrain), feature '
                        'code (MTS a mountain range, STM a river ...), name]. Written by scripts/area_places.py from the '
                        'local places tool\'s output; read by scripts/record_sources.py.',
               'areas': dict(sorted(areas.items(), key=lambda kv: int(kv[0])))}
        write_text(OUT, json.dumps(doc, ensure_ascii=False, indent=1))
        print('written', OUT)


if __name__ == '__main__':
    main()
