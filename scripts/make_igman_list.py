"""
The Igmanci: the men of the Prva proleterska who crossed Igman on the night of 27-28 January 1942, as far as the
brigade's own books tell them (2026-10-30, the user's wish), for the local page /mapa/igman.

Who was in the column comes from Miloš Vuksanović's monograph (znaci 00003/382, book pp. 33-34 and 39-41): the 1.
bataljon in the vanguard, the 2., the 5. and the brigade's sanitet, the 3. as rear guard, with the brigade's staff. Not
in it: the 4. bataljon, the 2. bataljon's 3. četa and the 5. bataljon's Užička četa (its 3. četa), who had gone with the
Vrhovni štab to Jahorina on 16-18 January, and the 6. bataljon, at Foča from 26 January. The 6. bataljon's Posavska
četa was with the 5. at Pjenovac and the book doesn't name it in the column: its men are listed apart, as probable.
Each man's battalion and company is his place in the line-up at Rudo on 21 December 1941 (the same book, "Borci
brigade na dan njenog osnivanja", read again by parse_prva_proleterska_rudo.py into a scratch file and matched to the
site's records by the entry's place on the page); men who fell before the march (Pjenovac and Bijele Vode on 21
January) are left out. A man who came to the brigade after Rudo is listed only where an entry of his names Igman.

    python scripts/make_igman_list.py           # writes website/app/(sr)/mapa/igman/igman.json
"""
from __future__ import annotations

import json
import re
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / 'scripts'))
sys.path.insert(0, str(ROOT / 'data-extraction'))
sys.stdout.reconfigure(encoding='utf-8')

DATA = ROOT / 'website' / 'public' / 'prva-proleterska-soldiers.json'
RUDO_PDF = 'prva-proleterska-stroj-u-rudom.pdf'
SCRATCH = ROOT / 'data-extraction' / '.cache' / 'igman' / 'rudo.json'
OUT = ROOT / 'website' / 'app' / '(sr)' / 'mapa' / 'igman' / 'igman.json'
# each man's line in the record dialog (lib/warEvents.ts), merged into his record by scripts/prepare-data.ts
EVENTS = ROOT / 'website' / 'data' / 'events' / 'prva-proleterska-soldiers.json'
SECTION_EVENT = {'štab brigade': 'stab', 'brigadni sanitet': 'sanitet', 'sanitetsko odjeljenje': 'odeljenje',
                 'hirurška ekipa': 'hirurska', 'posavska četa, 6. bataljon': 'posavska'}


def event_of(section: str | None, named: bool) -> dict:
    """the record's Igman event (website/app/lib/types.ts, WarEvent): where he stood, and whether that is sure (his
    company certainly in the column, or an entry of his names the march: the user's decision of 2026-10-30); the
    Posavska četa, which the book doesn't name in the column, is 'most likely'"""
    e: dict = {'e': 'igman', 'sure': True}
    if section in SECTION_EVENT:
        e['s'] = SECTION_EVENT[section]
        e['sure'] = section not in PROBABLE or named
    elif section:
        m = re.fullmatch(r'(\d)\. četa, (\d)\. bataljon', section)
        if m:
            e['c'], e['b'] = int(m.group(1)), int(m.group(2))
        else:
            b = re.search(r'(\d)\. bataljon$', section)
            if b and section.startswith('štab bataljona'):
                e['s'], e['b'] = 'bstab', int(b.group(1))
            elif b and section.startswith('bataljonski sanitet'):
                e['s'], e['b'] = 'bsanitet', int(b.group(1))
    return e

# the column of 27 January 1942, by the line-up's sections; (battalion, company) or the brigade's own sections
BRIGADE_SECTIONS = {'štab brigade', 'brigadni sanitet', 'sanitetsko odjeljenje', 'hirurška ekipa'}
LEFT_BEHIND = {'3. četa, 2. bataljon', '3. četa, 5. bataljon'}       # with the Vrhovni štab on Jahorina
PROBABLE = {'posavska četa, 6. bataljon'}
GROUPS = [('stab', 'Štab i sanitet brigade'), ('1', '1. bataljon (prethodnica)'), ('2', '2. bataljon, bez 3. čete'),
          ('5', '5. bataljon, bez Užičke čete'), ('3', '3. bataljon (zaštitnica)'),
          ('posavska', 'Posavska četa 6. bataljona, sa 5. bataljonom'), ('kasnije', 'Došli posle Ruda')]
# where the men fell before the march (the offensive of January 1942 on Romanija), for a death dated by month alone
BEFORE = re.compile(r'Pjenov|Bijel\w* Vod|Romanij|Sjenic|Pajtov|Dabravin|Pediš|Knežin|Sokol|Olov|Vlasenic|Ploč|Rogatic|'
                    r'Han.?Pijes|Podromanij|Gajev|Pusto Selo|Rakov\w* Nog|Dobrodol|Vražić', re.I)
AFTER = re.compile(r'Igman|Foč|Presjenic|Kalinovik|Ulog|Goražd|Trnov|Jahorin', re.I)
# words about the march itself: "Igmanski marš", "Igmanac", frostbite (a bare "Igman" can be where he fell later: the
# census's "poginuo 1943. u NOBu, Igman")
# (nor the Igmanska četa or the Igmanski partizanski odred, nor frost on Čvrsnica in 1943)
NAMES_IGMAN = re.compile(r'Igmansk\w*\s+marš|Igmanac|Igmanc\w*|promrz\w*[^.;]{0,60}Igman|Igman[^.;]{0,60}promrz', re.I)
# a death after the march, as an entry tells it: in Foča in 1942 (the field's date can be another book's: Pijade
# Avram), of frostbite (Barjamović Jovan, at Trnovo on the way)
DIED_IN_FOCA = re.compile(r'umr\w*[^.;]{0,30}1942[^.;]{0,15}u Foč\w*|u Foč\w*[^.;]{0,30}(?:tetanus|poslij?e Igmansk)|'
                          r'umr\w*[^;]{0,45}?od promrzlin', re.I)
FALLEN = {'poginuo', 'streljan', 'strijeljan', 'ubijen', 'obešen', 'nestao', 'umro od rana'}


def rudo_sections() -> dict:
    """the line-up's entries, by their place on the page, with their section ("2. četa, 1. bataljon")"""
    if not SCRATCH.exists():
        import parse_prva_proleterska_rudo as R
        from _parser_scaffold import run_parser
        R.corpus()
        SCRATCH.parent.mkdir(parents=True, exist_ok=True)
        run_parser(pdf_path=f'website/public/pdfs/{RUDO_PDF}', brigade_code=1, output_path=str(SCRATCH), start_page=1,
                   end_page=None, layout='single', entry_start_re=re.compile(r'^§'), parse_entry_fn=R.parse,
                   prepare_fn=R.prepare, line_filter=R.keep, post_fn=R.post, asterisk_marks_death=True,
                   id_start=200001, keep_other_sources=False)
    out = {}
    for r in json.loads(SCRATCH.read_text(encoding='utf-8')):
        out[(r['pdf_page'], round(r['pdf_y']))] = r.get('unit_detail') or ''
    return out


def group_of(section: str) -> str | None:
    if section in BRIGADE_SECTIONS:
        return 'stab'
    if section in PROBABLE:
        return 'posavska'
    if section in LEFT_BEHIND:
        return None
    m = re.search(r'(\d)\. bataljon$', section)
    return m.group(1) if m and m.group(1) in '1235' else None


def death(s: dict):
    """(year, month, day) of the record's death, None where it gives none"""
    v = s.get('death_date') or ''
    m = re.fullmatch(r'(?:(\d\d)(?:[-/]\d\d)?\.)?(\d\d)\.(\d{4})', v)
    if m:
        return int(m.group(3)), int(m.group(2)), int(m.group(1)) if m.group(1) else None
    y = re.search(r'(1[89]\d\d)', v)
    return (int(y.group(1)), None, None) if y else None


def before_march(s: dict) -> bool:
    if (s.get('death_type') or '') in ('ranjen', 'zarobljen'):
        return False
    d = death(s)
    if not d:
        return False
    year, month, day = d
    if year < 1942:
        return True
    if year > 1942 or month is None or month > 1:
        return False
    if day is not None:
        return day <= 27
    where = f"{s.get('death_place') or ''} {s.get('additional_info') or ''}"
    return bool(BEFORE.search(where)) and not AFTER.search(s.get('death_place') or '')


def fate(s: dict) -> str:
    """what became of him after the march: 'rat' fell or died later in the war, 'posle' died after it, 'ziv' no death
    in the war (he lived through it, as far as the books say)"""
    kind, d = s.get('death_type') or '', death(s)
    if s.get('death_after_war') or (d and d[0] > 1945):
        return 'posle'
    if kind in FALLEN or (kind == 'umro' and (not d or d[0] <= 1945)) or (kind.startswith('umr') and d and d[0] <= 1945):
        return 'rat'
    return 'ziv'


def texts(s: dict) -> list[str]:
    return [s.get('additional_info') or ''] + [o.get('additional_info') or '' for o in s.get('other_sources') or []]


def main():
    sections = rudo_sections()
    soldiers = json.loads(DATA.read_text(encoding='utf-8'))
    groups = {k: [] for k, _ in GROUPS}
    marks: dict[str, list[str]] = {}
    fates: dict[str, str] = {}
    events: dict[str, list[dict]] = {}
    left_out = Counter()
    for s in soldiers:
        entries = [s] + list(s.get('other_sources') or [])
        section = None
        for e in entries:
            if e.get('pdf_file') == RUDO_PDF and e.get('pdf_page') is not None:
                section = sections.get((e['pdf_page'], round(e['pdf_y'])))
                if section is not None:
                    break
        named = any(NAMES_IGMAN.search(t) for t in texts(s))
        if section is None:
            if named and not before_march(s):
                groups['kasnije'].append(s['soldier_id'])
            else:
                continue
        else:
            g = group_of(section)
            if g is None:
                left_out['not in the column'] += 1
                continue
            if before_march(s):
                left_out['fell before the march'] += 1
                continue
            groups[g].append(s['soldier_id'])
        m = []
        if named:
            m.append('igman')                       # an entry of his names Igman or frostbite
        d = death(s)
        if (d and d[0] == 1942 and d[1] in (2, 3) and re.search(r'Foč', s.get('death_place') or '')
                and (s.get('death_type') or '') not in FALLEN - {'umro od rana'}) or any(DIED_IN_FOCA.search(t) for t in texts(s)):
            m.append('foca')                        # died in Foča after the march (the tetanus of February 1942)
        if m:
            marks[s['soldier_id']] = m
        fates[s['soldier_id']] = fate(s)
        events[s['soldier_id']] = [event_of(section, named)]
    total = sum(len(v) for v in groups.values())
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps({'groups': [{'key': k, 'title': t, 'ids': groups[k]} for k, t in GROUPS if groups[k]],
                               'marks': marks, 'fates': fates}, ensure_ascii=False, indent=1) + '\n', encoding='utf-8')
    print('later: ' + ', '.join(f'{k} {n}' for k, n in Counter(fates.values()).items()))
    EVENTS.parent.mkdir(parents=True, exist_ok=True)
    EVENTS.write_text(json.dumps(events, ensure_ascii=False, separators=(',', ':')) + '\n', encoding='utf-8')
    print(f"wrote {EVENTS.relative_to(ROOT)}: {sum(e[0]['sure'] for e in events.values())} sure, "
          f"{sum(not e[0]['sure'] for e in events.values())} most likely")
    print(f'{total} men: ' + ', '.join(f'{t} {len(groups[k])}' for k, t in GROUPS))
    print(f"marked: named Igman or frostbite {sum('igman' in v for v in marks.values())}, "
          f"died in Foča Feb-Mar 1942 {sum('foca' in v for v in marks.values())}; left out: {dict(left_out)}")
    print(f'wrote {OUT.relative_to(ROOT)}')


if __name__ == '__main__':
    main()
