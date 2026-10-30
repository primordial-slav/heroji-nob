#!/usr/bin/env python3
"""Checks of the structured fields against the entries they were read from.

A field the reader stored can be a word it took for a number: "komandir voda i čete" gave the sub-unit "i četa" (the
conjunction "i", "and"), "v četi" the Slovene preposition, "Ljubljana-Vič" "Vi četa" (2026-10-28, Miočinović Stevo of
the Kalnički odred). Each check is a small function of a record that returns its problems, a list of
(field, kind, note); to add one, write the function and list it in CHECKS. Nothing is changed: the problems are
printed by kind with samples and written to data-extraction/.cache/field_checks.json (local), and
apply_corrections.py runs the checks on every unit it writes.

    python scripts/check_fields.py                       # every unit: counts and samples
    python scripts/check_fields.py --brigade 58 --sample 30
    python scripts/check_fields.py --check unit_numbers --kind other_number
"""
from __future__ import annotations

import argparse
import collections
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(Path(__file__).resolve().parent))
REPORT = ROOT / 'data-extraction' / '.cache' / 'field_checks.json'

# ── unit_numbers: a sub-unit's number is printed in the entry as a number ──────────────────────────────────────────
# The field's parts: "2. četa", "1. bataljon", "3. vod", "IV bataljon" (before standardize_fields writes it in
# figures), and the words read as numbers ("i četa", "v četi")
KINDS = {
    'četa': r'(?:čet[aeiu]\w*|č\b\.?)',
    'bataljon': r'(?:bataljon\w*|batalj\b\.?|bat\b\.?)',
    'vod': r'(?:vod(?:a|u|om|i)?)(?![\w])',
    'desetina': r'(?:desetin\w*)',
}
ROMAN = {'I': 1, 'II': 2, 'III': 3, 'IV': 4, 'V': 5, 'VI': 6, 'VII': 7, 'VIII': 8, 'IX': 9, 'X': 10, 'XI': 11, 'XII': 12,
         'XIII': 13, 'XIV': 14, 'XV': 15, 'XVI': 16, 'XVII': 17, 'XVIII': 18, 'XIX': 19, 'XX': 20}
ORDINALS = {'prv': 1, 'drug': 2, 'treć': 3, 'tretj': 3, 'četvrt': 4, 'četrt': 4, 'pet': 5, 'šest': 6, 'sedm': 7,
            'osm': 8, 'devet': 9, 'deset': 10, 'jedanaest': 11, 'dvanaest': 12}
FIELD_PART = re.compile(r'^(?:(\d{1,2})\.|(?-i:(i|v))(?=\s)|([IVXivx]{1,5})\.?)\s(?:\S+\s)?(četa|bataljon|vod|desetina)$')
# the text's numbers: a figure, a Roman numeral written as one (capitals, or small letters with a dot: the scan's
# "i. čete"), an ordinal word; never a word glued to the unit ("Vič"), nor the small "i" and "v" of the language
_NUM = (r'(?<![\w.])(?:(\d{1,2})\.?\s?'
        r'|((?-i:[IVX]{1,5}(?=\.?\s|\.|(?i:bataljon|bat\.|čet|vod|desetin))|[IVX][IVXivx]{1,4}(?=\.?\s)|[ivx]{1,4}[IVX][IVXivx]{0,3}(?=\.?\s)|[ivx]{1,4}(?=\.)))\.?\s?'
        r'|(' + '|'.join(ORDINALS) + r')(?:a|e|i|o|u|oj|og|oga|om|ome|ega|em|ih)\s)')
# a word the reader took for a number: the language's "i" and "v", or a word's last letters before the unit's
# first ("Vič", "Ivič": "Vi" and "č")
_WORD = r'(?:(?<![\w.])(?-i:[iv])\s|(?<=[\w])(?-i:[IVXivx]{1,4})\.?\s?)'
# between the number and the unit: the battalion's name in brackets ("3. (viškog) bataljona"), its kind and district
# ("I udarnog mosorskog bataljona"), never another unit ("17. brigade č")
_BETWEEN = (r'(?:\([^)]{1,30}\)\s)?'
            r'(?:(?!(?:brigad|bataljon|bat\b|čet|vod|desetin|divizij|odred|korpus))[a-zčćžšđ]+\s){0,2}')


def roman(text: str) -> int | None:
    return ROMAN.get(text.upper())


def text_numbers(text: str, kind: str) -> list[tuple[int, bool]]:
    """the numbers the text prints with that kind of unit ("2. četa", "5. makedonski bataljon"; the first of
    "1. in 3. četa", "1. i 2. bataljona" too), each with whether it is his here: not another brigade's battalion
    ("6. beogradskog bataljona 1. proleterske brigade") nor the Posavski odred's "V bataljonu bio do 5. 11. 1941",
    a sentence's first word, "u" """
    out = [(int(m.group(1)), True) for m in re.finditer(r'(?<![\w.])(\d{1,2})\.\s?(?:i|in|ili|,|-|–|—)\s?(?=\d{1,2}\.\s?'
                                                          + _BETWEEN + KINDS[kind] + ')', text, re.I)]
    for m in re.finditer(_NUM + _BETWEEN + KINDS[kind], text, re.I):
        if m.group(1):
            n = int(m.group(1))
        elif m.group(2):
            n = roman(m.group(2))
        else:
            n = ORDINALS[m.group(3).lower()]
        if n is None:
            continue
        mine = not (re.match(r'\s+(?:\d{1,2}\.|(?:' + '|'.join(ORDINALS) + r')\w*)\s+[\w.]+\s+(?:[\w.]+\s+)?brigad',
                             text[m.end():], re.I) or (
            m.group(2) in ('V', 'I') and re.search(r'(?:^|[.;:!?])\s*$', text[:m.start()])
            and re.search(r'[ui]$', m.group(0))))
        out.append((n, mine))
    return out


def texts_of(s: dict) -> list[str]:
    """the record's own entry and the unit's other books merged into it (where its fields are read from)"""
    out = [s.get('additional_info') or '']
    out += [o.get('additional_info') or '' for o in s.get('other_sources') or []
            if not o.get('unit_file') and not o.get('ref_book')]
    return [t for t in out if t]


def unit_numbers(s: dict) -> list[tuple[str, str, str]]:
    value = s.get('unit_detail')
    if not value:
        return []
    texts = texts_of(s)
    problems = []
    for part in value.split(', '):
        m = FIELD_PART.match(part.strip())
        if not m:
            continue
        figure, word, rom, kind = m.groups()
        if word:
            problems.append(('unit_detail', 'word', f'"{part}": the word "{word}", not a number'))
            continue
        n = int(figure) if figure else roman(rom)
        if n is None:
            problems.append(('unit_detail', 'not_a_number', f'"{part}"'))
            continue
        numbers = [x for t in texts for x in text_numbers(t, kind)]
        if any(x == n for x, _ in numbers):
            continue
        printed = [x for x, mine in numbers if mine]
        glued = any(re.search(_WORD + KINDS[kind], t) for t in texts)
        if printed:
            # a record that holds the unit's other books may have the field from a list's heading (the line-up at
            # Rudo by company), and its books then give the companies he was in otherwise
            k = 'books_differ' if len(texts) > 1 else 'other_number'
            problems.append(('unit_detail', k,
                             f'"{part}": the entry prints {", ".join(sorted({f"{x}. {kind}" for x in printed}))}'))
        elif glued and rom:
            problems.append(('unit_detail', 'glued', f'"{part}": letters of a word, not a number'))
    return problems


# ── the checks of 2026-10-30 (the user's "do all of it" after the survey of the units' records) ───────────────────────
FALLEN = {'poginuo', 'streljan', 'ubijen', 'nestao', 'obešen', 'strijeljan', 'umro od rana'}
CENSUS_PARTS = tuple(f'01{n}' for n in range(31, 39))       # 131-138: the census's typed columns
# the checks of 2026-10-30 read the units' records only: Borci drugih jedinica and the census's parts are written anew
# by build_ostali_borci.py (their fixes go there, not in corrections.json), and the Spomenica's children are on the
# site by the user's decision
NOT_UNITS = ('0122',) + CENSUS_PARTS


def year_of(value) -> int | None:
    m = re.search(r'(?<!\d)(1[89]\d\d)(?!\d)', str(value or ''))
    return int(m.group(1)) if m else None


def life_dates(s: dict) -> list[tuple[str, str, str]]:
    """a birth after the death, a child (born after 1932, or dead before twelve: mostly a year the scan misread), a
    fall after the war ("poginuo 1955": a postwar death or a misread year)"""
    if s['soldier_id'].startswith(NOT_UNITS):
        return []
    born, died = year_of(s.get('birth_year')), year_of(s.get('death_date'))
    out = []
    if born and died and born > died:
        out.append(('birth_year', 'born_after_death', f'born {born}, died {died}'))
    elif born and (born > 1932 or (died and died - born < 12)):
        out.append(('birth_year', 'child', f'born {born}' + (f', died {died}' if died else '')))
    if died and died > 1945 and (s.get('death_type') or '') in FALLEN and not s.get('death_after_war'):
        out.append(('death_date', 'after_war', f"{s.get('death_type')} {s.get('death_date')}"))
    return out


# what a place of death keeps that tidy_death_place can't cut: a unit, a duty, a date, the bio's words
NOT_PLACE = re.compile(r'brigad|bataljon|\bčet[ia]\b|komandir|komesar|\bborac\b|heroj|\d{1,2}\.\s?\d|\bposle\b|\bnakon\b', re.I)


def death_place(s: dict) -> list[tuple[str, str, str]]:
    v = s.get('death_place') or ''
    if not v or s['soldier_id'].startswith(NOT_UNITS):
        return []
    return [('death_place', 'not_a_place', f'"{v}"')] if NOT_PLACE.search(v) else []


NAME_ODD = re.compile(r'[0-9|\\/<>{}\[\]_=+*#@^"]')
INNER_CAPITAL = re.compile(r'[a-zčćžšđ][A-ZČĆŽŠĐ]')


def names(s: dict) -> list[tuple[str, str, str]]:
    """a given name of one or two letters ("Čamdžić Vladimir Va", "Mirković Matu A"), the scan's characters in a name
    ("Hrp08tan", "Sla\\ >o"), a capital inside one ("KOiTIĆ", "STTiVO")"""
    if s['soldier_id'].startswith(NOT_UNITS):
        return []
    out = []
    first, last = s.get('first_name') or '', s.get('last_name') or ''
    if first and len(first) <= 2 and not first.endswith('.') and first not in ('Bo', 'Đi', 'Li', 'Yu'):
        out.append(('first_name', 'short_given', f'"{first}"'))
    for field, v in (('last_name', last), ('first_name', first)):
        if NAME_ODD.search(v):
            out.append((field, 'odd_char', f'"{v}"'))
        elif INNER_CAPITAL.search(v) and not re.match(r'(?:Mc|Mac|De|Di|La|Le|Van|Von|O)[A-Z]', v):
            out.append((field, 'inner_capital', f'"{v}"'))
    return out


# the next soldier glued into a bio: his heading in capitals after a sentence's end, outside the book's notes in brackets
# ("... Bio u 3. bataljonu. ĆEKO STANKO ili SLAVKO. U NOB-u 1942."); not an abbreviation
GLUED_HEADING = re.compile(r'[.;]\s+(?!(?:NOB|NOV|NOVJ|NOR|NOO|NOP|KPJ|SKOJ|SSSR|JNA|SFRJ|SUBNOR|KNOJ|OZNA|UDB|AVNOJ|ZAVNOH|'
                           r'AFŽ|USAOJ|NDH|MSB|VPB|CK|PK|OK|SK|MK|RAF|USA|SAD|NARODNI|POGINUO|POGINULA|UMRO|RCEV)\b)[A-ZČĆŽŠĐ]{3,}(?:-[A-ZČĆŽŠĐ]{3,})?\s+'
                           r'(?:\(?[A-ZČĆŽŠĐ][a-zčćžšđ]+\)?\s+)?[A-ZČĆŽŠĐ]{3,}\b')


def glued(s: dict) -> list[tuple[str, str, str]]:
    if s['soldier_id'].startswith(NOT_UNITS):
        return []
    t = re.sub(r'\([^)]*\)', '', s.get('additional_info') or '')
    m = GLUED_HEADING.search(t)
    return [('additional_info', 'glued_entry', f'"…{t[max(0, m.start() - 30):m.end() + 30]}…"')] if m else []


# the rule of 2026-10-14: no record for one who went over to the enemy, betrayed or was shot as a deserter or traitor;
# one who deserted and came back, or came over to us, stays. These words only find the entries to read.
# his own act only: "izdajnik" in the books is mostly the enemy ("okupatora i domaćih izdajnika"), and "prebegao u
# Italiju" a Jew fleeing the Ustaše
_THEM = r'(?:četnik|ustaš|neprijatelj|domobran|nedić|ljotić|Nijemc|Nemc|Njemc|belogard|bal\w+\s+kom|okupator)\w*'
DESERTER = re.compile(r'\b(?:dezertir\w*|dezerter\w*|(?:prebeg|prebjeg|preš|pobeg|pobjeg)\w*\s+(?:k|u|na\s+stranu|kod)\s+'
                      + _THEM + r'|(?:postao|postala)\s+(?:agent|četnik|ustaš|domobran|špijun|doušnik)\w*|agent\w*\s+'
                      r'Gestap\w*|(?:streljan|strijeljan)\w*\s+(?:kao\s+(?:dezerter|izdajnik|špijun|petokolonaš|neprijatelj)|'
                      r'zbog\s+(?:dezert|izdaj|samovolj|napuštanj|kukavič|pljačk|silovanj|slabosti|špijun|kolebanj))\w*|'
                      r'kao\s+izdajnik\w*|izdao\s+(?:je\s+)?(?:drugove|jedinic|partizan|bazu|logor|sklonište|partijsk))', re.I)


def deserter(s: dict) -> list[tuple[str, str, str]]:
    if s['soldier_id'].startswith(NOT_UNITS):
        return []
    texts = [s.get('additional_info') or ''] + [o.get('additional_info') or '' for o in s.get('other_sources') or []]
    for t in texts:
        m = DESERTER.search(t)
        if m:
            return [('record', 'deserter', f'"…{t[max(0, m.start() - 40):m.end() + 60]}…"')]
    return []


CHECKS = [
    ('unit_numbers', unit_numbers),
    ('life_dates', life_dates),
    ('death_place', death_place),
    ('names', names),
    ('glued', glued),
    ('deserter', deserter),
]


def same_entry_twice(soldiers: list[dict]) -> list[tuple[dict, str, str, str]]:
    """one unit's two records of one name and the same text: the same man twice (a man the book prints in two of its
    units, the 1. bokeljska's roster entering a man again in each company he was moved to), or a page the scan
    repeats; each record after the first"""
    first, out = {}, []
    for s in soldiers:
        t = (s.get('additional_info') or '').strip()
        if not t or s['soldier_id'].startswith(NOT_UNITS):
            continue
        key = (s.get('full_name'), t)
        if key in first:
            out.append((s, 'record', 'same_entry_twice', f"= {first[key]['soldier_id']}"))
        else:
            first[key] = s
    return out


UNIT_CHECKS = [
    ('duplicates', same_entry_twice),
]

# answers kept so a case is not raised again: the review page (scripts/review_fields.py) writes them, and its --write
# turns 'fix', 'delete' and 'merge' into corrections
DECISIONS = ROOT / 'field_decisions.json'


def load_decisions() -> dict:
    if not DECISIONS.exists():
        return {}
    return {d['key']: d for d in json.loads(DECISIONS.read_text(encoding='utf-8'))}


def case_key(check: str, kind: str, sid: str, field: str) -> str:
    return f'{check}:{kind}:{sid}:{field}'


def answered(decisions: dict, check: str, kind: str, s: dict, field: str, note: str) -> bool:
    """an answer holds while what it answered is unchanged: the field's value, or the note for a record's case"""
    d = decisions.get(case_key(check, kind, s['soldier_id'], field))
    return bool(d) and d.get('answer') != 'unsure' and d.get('value') == case_value(s, field, note)


def case_value(s: dict, field: str, note: str) -> str:
    return note if field == 'record' else str(s.get(field) or '')


def run(units: dict, only: str | None = None, kind: str | None = None, all_cases: bool = False) -> dict:
    """units: data file name -> its records. Returns {check: {kind: [(soldier_id, file, field, note), ...]}}; the
    cases answered already are left out unless all_cases"""
    decisions = {} if all_cases else load_decisions()
    found: dict = {}

    def add(check, s, name, field, k, note):
        if (kind and k != kind) or answered(decisions, check, k, s, field, note):
            return
        found.setdefault(check, {}).setdefault(k, []).append((s['soldier_id'], name, field, note))
    for name, soldiers in units.items():
        for s in soldiers:
            for check, fn in CHECKS:
                if only and check != only:
                    continue
                for field, k, note in fn(s):
                    add(check, s, name, field, k, note)
        for check, fn in UNIT_CHECKS:
            if not only or check == only:
                for s, field, k, note in fn(soldiers):
                    add(check, s, name, field, k, note)
    return found


def describe(found: dict) -> str:
    parts = [f'{check} ' + ', '.join(f'{k} {len(rows)}' for k, rows in sorted(kinds.items()))
             for check, kinds in sorted(found.items())]
    return '; '.join(parts) if parts else 'nothing'


def entry_of(s: dict) -> dict:
    """what the review page shows of a record (scripts/review_fields.py): its name, text and place on the page, and its
    other books' entries"""
    def where(e):
        if not e.get('pdf_file') or not e.get('pdf_page'):
            return {}
        x0 = e.get('pdf_x_left', e.get('pdf_x')) or 0
        y0 = e.get('pdf_y') or 0
        return {'pdf_file': e['pdf_file'], 'pdf_page': e['pdf_page'],
                'box': [round(x0, 1), round(y0, 1), round(e.get('pdf_x_end') or x0 + 260, 1),
                        round(e.get('pdf_y_end') or y0 + 12, 1)], **({'rects': e['pdf_rects']} if e.get('pdf_rects') else {})}
    return {'name': s.get('full_name') or '', 'text': (s.get('additional_info') or '')[:1200], **where(s),
            **({'source_url': s['source_url']} if s.get('source_url') else {}),
            'fields': {k: s[k] for k in ('last_name', 'middle_name', 'fathers_name', 'first_name', 'birth_year', 'birth_place',
                                         'death_type', 'death_date', 'death_place', 'unit_detail') if s.get(k)},
            'other': [{'name': o.get('name') or '', 'text': (o.get('additional_info') or '')[:500], **where(o),
                       **({'book': o.get('ref_book') or o.get('unit_file')} if o.get('ref_book') or o.get('unit_file') else {})}
                      for o in (s.get('other_sources') or [])[:4]]}


def write_report(found: dict, units: dict | None = None) -> None:
    """the problems found, with what the review page shows of each record, kept with those of the units this run
    didn't read"""
    old = {}
    if REPORT.exists():
        try:
            old = json.loads(REPORT.read_text(encoding='utf-8'))
        except ValueError:
            old = {}
    files = set(units or ())
    rows = [r for r in old.get('problems', []) if units is not None and r['file'] not in files]
    by_id = {s['soldier_id']: s for soldiers in (units or {}).values() for s in soldiers}
    for check, kinds in found.items():
        for k, items in kinds.items():
            for sid, f, fld, note in items:
                s = by_id.get(sid, {'soldier_id': sid})
                row = {'check': check, 'kind': k, 'soldier_id': sid, 'file': f, 'field': fld, 'note': note,
                       'key': case_key(check, k, sid, fld), 'value': case_value(s, fld, note), **entry_of(s)}
                twin = re.match(r'= (\d{10})', note)
                if twin and twin.group(1) in by_id:
                    row['twin'] = {'soldier_id': twin.group(1), **entry_of(by_id[twin.group(1)])}
                rows.append(row)
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(json.dumps({'problems': sorted(rows, key=lambda r: (r['check'], r['kind'], r['soldier_id']))},
                                 ensure_ascii=False, indent=1), encoding='utf-8')


def main():
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    from name_utils import BRIGADE_CONFIGS          # noqa: E402
    from cleanup_text_fields import live_json_files  # noqa: E402

    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--brigade', type=int, nargs='+')
    ap.add_argument('--check', choices=[n for n, _ in CHECKS + UNIT_CHECKS])
    ap.add_argument('--kind')
    ap.add_argument('--sample', type=int, default=8)
    args = ap.parse_args()
    live, units = live_json_files(), {}
    for code, cfg in sorted(BRIGADE_CONFIGS.items()):
        if (args.brigade and code not in args.brigade) or cfg['json_file'] not in live:
            continue
        path = ROOT / 'website' / 'public' / cfg['json_file']
        units[cfg['json_file']] = json.loads(path.read_text(encoding='utf-8'))
    found = run(units, args.check, args.kind)
    by_id = {s['soldier_id']: s for soldiers in units.values() for s in soldiers}
    for check, kinds in sorted(found.items()):
        for k, rows in sorted(kinds.items()):
            per_file = collections.Counter(f for _, f, _, _ in rows)
            print(f'\n{check} / {k}: {len(rows)}  ({", ".join(f"{f} {n}" for f, n in per_file.most_common(6))})')
            for sid, f, field, note in rows[:args.sample]:
                info = (by_id[sid].get('additional_info') or '')[:150]
                print(f'   {sid}  {by_id[sid].get("full_name")}: {note}\n      {info}')
    if not args.check and not args.kind:
        write_report(found, units)
    print(f'\n{describe(found)}')


if __name__ == '__main__':
    main()
