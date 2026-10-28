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


CHECKS = [
    ('unit_numbers', unit_numbers),
]


def run(units: dict, only: str | None = None, kind: str | None = None) -> dict:
    """units: data file name -> its records. Returns {check: {kind: [(soldier_id, file, field, note), ...]}}"""
    found: dict = {}
    for name, soldiers in units.items():
        for s in soldiers:
            for check, fn in CHECKS:
                if only and check != only:
                    continue
                for field, k, note in fn(s):
                    if kind and k != kind:
                        continue
                    found.setdefault(check, {}).setdefault(k, []).append((s['soldier_id'], name, field, note))
    return found


def describe(found: dict) -> str:
    parts = [f'{check} ' + ', '.join(f'{k} {len(rows)}' for k, rows in sorted(kinds.items()))
             for check, kinds in sorted(found.items())]
    return '; '.join(parts) if parts else 'nothing'


def write_report(found: dict, units: dict | None = None) -> None:
    """the problems found, kept with those of the units this run didn't read"""
    old = {}
    if REPORT.exists():
        try:
            old = json.loads(REPORT.read_text(encoding='utf-8'))
        except ValueError:
            old = {}
    files = set(units or ())
    rows = [r for r in old.get('problems', []) if units is not None and r['file'] not in files]
    for check, kinds in found.items():
        for k, items in kinds.items():
            rows += [{'check': check, 'kind': k, 'soldier_id': sid, 'file': f, 'field': fld, 'note': note}
                     for sid, f, fld, note in items]
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(json.dumps({'problems': sorted(rows, key=lambda r: (r['check'], r['kind'], r['soldier_id']))},
                                 ensure_ascii=False, indent=1), encoding='utf-8')


def main():
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    from name_utils import BRIGADE_CONFIGS          # noqa: E402
    from cleanup_text_fields import live_json_files  # noqa: E402

    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--brigade', type=int, nargs='+')
    ap.add_argument('--check', choices=[n for n, _ in CHECKS])
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
        write_report(found, units if args.brigade else None)
    print(f'\n{describe(found)}')


if __name__ == '__main__':
    main()
