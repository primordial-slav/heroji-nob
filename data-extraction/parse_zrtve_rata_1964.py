"""
The fallen partisans of the federal census of the war's dead, "Žrtve rata 1941-1945" (popis iz 1964, as published by
the Museum of Genocide Victims, Beograd): one volume per republic and province, village by village, every one of the
war's dead with father, birth year, nationality, the year, circumstance and place of death, and the census number.
A book across units: it names no unit.

Only the fighters are read: "poginuo / umro ... u NOBu" (fell or died in the NOB) and "kao zarobljenik prip. NOV i POJ"
(killed as a captured partisan). The civilians, the camps' dead, the April war's soldiers and the rest stay out, as in
every book on the site.

Layout (born-digital, a clean text layer): two columns; the page header gives the općina and the village the page
starts in; a village's name stands over its entries in bold italic; each entry is one or two lines ending in the
ten-digit census number:
    Marković (Rade) Tomo, rođen 1888. Crnogorac, poginuo 1942. u NOBu, Zec Planina (2936007006)
"rođeno ... poginulo" (neuter) where the sex is not known. The father is printed in the nominative ("Nn" = not known), a birth year of 9999 is not known.

Source: https://www.muzejgenocida.rs/wp-content/uploads/2024/03/<Vol>.pdf (also on pod2.stat.gov.rs), cached in
data-extraction/.cache/zrtve_rata_1964/ (git-ignored). Output: data-extraction/zrtve-rata/zrtve-rata-1964-<vol>-entries.json,
one file per volume, IDs <prefix><6 digits> in the volume's order (prefixes 9020-9027: see VOLUMES).

Usage:
    python data-extraction/parse_zrtve_rata_1964.py            # every volume
    python data-extraction/parse_zrtve_rata_1964.py crg mak    # some volumes
    python data-extraction/parse_zrtve_rata_1964.py --stats    # counts only, nothing written
"""
from __future__ import annotations

import json
import re
import sys
from collections import Counter
from pathlib import Path

import fitz

sys.stdout.reconfigure(encoding='utf-8')
HERE = Path(__file__).resolve().parent
CACHE = HERE / '.cache' / 'zrtve_rata_1964'
OUT = HERE / 'zrtve-rata'
URL = 'https://www.muzejgenocida.rs/wp-content/uploads/2024/03/{}.pdf'

# volume key -> (file, ID prefix, title)
VOLUMES = {
    'slo': ('Slo', '9020', 'Žrtve rata 1941-1945: SR Slovenija'),
    'hrv': ('Hrv', '9021', 'Žrtve rata 1941-1945: SR Hrvatska'),
    'bih': ('BiH', '9022', 'Žrtve rata 1941-1945: SR Bosna i Hercegovina'),
    'crg': ('Crg', '9023', 'Žrtve rata 1941-1945: SR Crna Gora'),
    'mak': ('Mak', '9024', 'Žrtve rata 1941-1945: SR Makedonija'),
    'srb': ('Srb', '9025', 'Žrtve rata 1941-1945: SR Srbija (bez pokrajina)'),
    'kos': ('Kos', '9026', 'Žrtve rata 1941-1945: Kosovo i Metohija'),
    'voj': ('Voj', '9027', 'Žrtve rata 1941-1945: Vojvodina'),
}

FIGHTER = ('u NOBu', 'u NORu', 'kao zarobljenik prip. NOV i POJ')
# the census's circumstances of death, longest first, so "prilikom borbi ili bombardovanja" wins over "prilikom borbi"
HOW = sorted(['u NOBu', 'u NORu', 'u direktnom teroru', 'prilikom borbi ili bombardovanja', 'prilikom bombardovanja',
              'prilikom borbi', 'u logoru', 'kod kuće', 'u zatvoru', 'nepoznato', 'u aprilskom ratu 1941 god.',
              'kao zarobljeni pripadnik VKJ', 'kao zarobljenik prip. NOV i POJ', 'pri deportaciji',
              'u masovnom pokolju', 'na prinudnom radu', 'u izbeglištvu', 'od posledica'], key=len, reverse=True)
ENTRY = re.compile(r'^(?P<last>.+?) \((?P<father>[^()]*)\) (?P<first>[^,]+?),+ (?P<born>rođen[ao]?) (?P<by>\d{4})\. '
                   r'(?P<rest>.*) \((?P<rid>[0-9A-Za-z]{10}|M\d{7})\)$')
# the fate's verb as printed: poginuo, umro, ubijen, nestao, streljan, zaklan, obešen, spaljen, in any gender
FATE = re.compile(r'^(?P<nat>[^,]*?), (?P<verb>[^\W\d_]+)'
                  r'(?: od (?P<who>[^\d,]+?))? (?P<dy>\d{4})\.? ?(?P<tail>.*)$')
# the census number ends an entry ("5033s00105" too; the Croatian volume's "M0007763", whose entries were read glued to
# the next one's until 2026-10-30: "Danon (Nn) Moise" in the place of death of the fighter before him)
END = re.compile(r'\((?:[0-9A-Za-z]{10}|M\d{7})\)\s*$')


def birthplace(village: str, opstina: str) -> str:
    """The entry's village and općina as one birthplace: "Arbnež, Bar"; the village alone where it is the općina. A
    district of Belgrade is Belgrade (the census heads them "Beograd-Stari Grad" under "Opština BEOGRAD STARI GRAD",
    and cuts the longer ones, "Beograd-Čukarica i Rakovi", "Beograd-Palilula i Karabu"); the parts it numbers of one
    village ("Donje Selište 1", "Donje Selište 2") are that village; and its "Vodžovac" is Voždovac (2026-10-21)"""
    if village.startswith('Beograd-'):
        return 'Beograd'
    village = re.sub(r'\s+\d+$', '', village)
    opstina = opstina.replace('Vodžovac', 'Voždovac')
    return village if village == opstina else ', '.join(x for x in (village, opstina) if x)


def title_case(s: str) -> str:
    """"BELI MANASTIR" -> "Beli Manastir", "AJDOVŠČINA" -> "Ajdovščina", "HERCEG-NOVI" -> "Herceg-Novi" """
    return re.sub(r'[^\W\d_]+', lambda m: m.group(0)[0].upper() + m.group(0)[1:].lower(), s.strip())


def lines_of(page) -> list[tuple[float, float, str, str, float]]:
    """(column, y, font, text, size) of each line, in reading order: the left column down, then the right"""
    out = []
    for b in page.get_text('dict')['blocks']:
        for l in b.get('lines', []):
            spans = [s for s in l['spans'] if s['text'].strip()]
            if not spans:
                continue
            x0, y0 = l['bbox'][0], l['bbox'][1]
            text = ''.join(s['text'] for s in l['spans']).strip()
            col = 0 if x0 < page.rect.width / 2 - 10 else 1
            out.append((col, y0, spans[0]['font'], text, spans[0]['size']))
    return sorted(out, key=lambda t: (t[0], round(t[1], 1)))


def read_volume(key: str) -> tuple[list[dict], Counter]:
    file, prefix, title = VOLUMES[key]
    doc = fitz.open(CACHE / f'{file}.pdf')
    fates: Counter = Counter()
    entries: list[dict] = []
    opstina, village = '', ''
    buf, buf_page, buf_village, buf_opstina = '', 0, '', ''
    for pno in range(doc.page_count):
        page = doc[pno]
        for col, y, font, text, size in lines_of(page):
            italic = 'Italic' in font
            bold = 'Bold' in font
            # the running header and footer
            if y < 42 or y > page.rect.height - 50:
                if italic and text.startswith('opština '):
                    opstina = title_case(text[len('opština '):])
                continue
            if bold and text.startswith('Opština '):
                opstina = title_case(text[len('Opština '):])
                continue
            if bold and italic and size >= 9.5:
                village = text.strip()
                continue
            if not buf:
                buf_page, buf_village, buf_opstina = pno + 1, village, opstina
            buf = f'{buf} {text}'.strip() if buf else text
            if END.search(buf):
                e = parse(buf, fates)
                if e:
                    e.update(page=buf_page, village=buf_village, opstina=buf_opstina)
                    entries.append(e)
                buf = ''
    doc.close()
    out = []
    for e in entries:
        born_in = birthplace(e['village'], e['opstina'])
        father = '' if e['father'].lower() in ('nn', 'n.n.', 'n', '') else e['father']
        out.append({
            'soldier_id': '',
            'name': f"{e['last']} ({e['father']}) {e['first']}",
            'last_name': e['last'], 'first_name': e['first'], 'nick': '', 'fathers_name': father,
            'birth_year': '' if e['by'] == '9999' else e['by'],
            'born_in': born_in, 'ethnicity': e['nat'],
            'death_year': e['dy'], 'death_place': '' if e['place'].lower() in ('nepoznato', '') else e['place'],
            'woman': e['born'] == 'rođena',
            'survived': False,
            'additional_info': entry_text(e),
            'census_id': e['rid'],
            'book_title': title,
            'source_url': f"{URL.format(file)}#page={e['page']}",
            'source_page': e['page'],
        })
    return numbered(out, prefix, OUT / f'zrtve-rata-1964-{key}-entries.json'), fates


def numbered(entries: list[dict], prefix: str, path: Path) -> list[dict]:
    """IDs <prefix><6 digits> in the volume's order, the entries the last run wrote keeping theirs (references and
    Ostali borci's records hold them): an entry read since (one that had been glued to another) gets the next free
    number after the last"""
    if not path.exists():
        for i, e in enumerate(entries, 1):
            e['soldier_id'] = f'{prefix}{i:06d}'
        return entries
    old = json.loads(path.read_text(encoding='utf-8'))
    key = lambda e: (e['last_name'], e['first_name'], e['fathers_name'], e['birth_year'], e['born_in'])
    j, fresh = 0, []
    for e in entries:
        if j < len(old) and key(old[j]) == key(e):
            e['soldier_id'] = old[j]['soldier_id']
            j += 1
        else:
            fresh.append(e)
    assert j == len(old), f'{path.name}: entry {old[j]["soldier_id"]} not read again'
    last = max((int(o['soldier_id'][4:]) for o in old), default=0)
    for n, e in enumerate(fresh, last + 1):
        e['soldier_id'] = f'{prefix}{n:06d}'
    return entries


def parse(raw: str, fates: Counter) -> dict | None:
    """One printed entry -> its parts, or None when it is not a fighter's"""
    raw = re.sub(r'\s+', ' ', raw).strip()
    m = ENTRY.match(raw)
    if not m:
        fates['(unread)'] += 1
        return None
    f = FATE.match(m.group('rest'))
    if not f:
        fates['(no fate)'] += 1
        return None
    tail = f.group('tail').strip()
    how = next((h for h in HOW if tail.startswith(h)), None)
    if how is None:
        how, _, place = tail.partition(', ')
    else:
        place = tail[len(how):].lstrip(', ').strip()
    fates[how] += 1
    if how not in FIGHTER:
        return None
    # "Bari           italija": the census pads a place and its country
    place = re.sub(r'\s{2,}', ', ', place).strip(' ,')
    # the entry after the birth: the birth itself is written out with the village (see entry_text)
    text = f"{f.group('nat')}, {f.group('verb')}" \
           f"{' od ' + f.group('who') if f.group('who') else ''} {f.group('dy')}. {how}" \
           f"{', ' + place if place else ''}"
    return {'last': m.group('last').strip(), 'father': m.group('father').strip(), 'first': m.group('first').strip(),
            'born': m.group('born'), 'by': m.group('by'), 'nat': f.group('nat').strip(), 'dy': f.group('dy'),
            'how': how, 'place': place, 'rid': m.group('rid'), 'text': text}


def entry_text(e: dict) -> str:
    """The entry as the dialog shows it: the census line with the village it stands under put after the birth year,
    "rođen 1888, Arbnež (Bar). Crnogorac, poginuo 1942. u NOBu, Zec Planina" ("Bar." where the village is the
    općina's town; "rođen (godina nepoznata), ..." for the census's 9999)"""
    village, opstina = e['village'], e['opstina']
    where = village if not opstina or village == opstina else f'{village} ({opstina})' if village else opstina
    year = '(godina nepoznata)' if e['by'] == '9999' else e['by']
    birth = f"{e['born']} {year}" + (f', {where}' if where else '')
    return f"{birth}. {e['text']}"


def main():
    args = [a for a in sys.argv[1:] if not a.startswith('--')]
    stats = '--stats' in sys.argv
    keys = args or list(VOLUMES)
    OUT.mkdir(exist_ok=True)
    total = 0
    for key in keys:
        entries, fates = read_volume(key)
        dead = sum(fates.values())
        total += len(entries)
        print(f"{key}: {dead:,} dead read, {len(entries):,} fighters "
              f"({fates['u NOBu']:,} u NOBu, {fates['kao zarobljenik prip. NOV i POJ']:,} captured), "
              f"unread {fates['(unread)']}, no fate {fates['(no fate)']}")
        odd = [(k, v) for k, v in fates.most_common() if k not in HOW and not k.startswith('(')]
        if odd:
            print('   circumstances not in HOW:', odd[:12])
        if not stats:
            path = OUT / f'zrtve-rata-1964-{key}-entries.json'
            # one entry a line: compact, and a re-run's diff shows the entries that changed
            lines = ',\n'.join(json.dumps(e, ensure_ascii=False, separators=(',', ':')) for e in entries)
            path.write_text(f'[\n{lines}\n]\n', encoding='utf-8')
            print(f'   wrote {path.relative_to(HERE.parent)} ({path.stat().st_size // 1024:,} KB)')
    print(f'fighters in all: {total:,}')


if __name__ == '__main__':
    main()
