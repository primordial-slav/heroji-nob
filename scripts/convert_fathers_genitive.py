"""
Generate corrections converting fathers' names still in the genitive to the nominative.

The books print "PETROVIĆ Marka Jovan" (Jovan, son of Marko). normalize_all_json.py
converts the father's name with a small, conservative dictionary, so most stay
genitive. Here the nominative is chosen from the data itself: candidate forms
(Miloša->Miloš, Marka->Marko, Petra->Petar, Nikole->Nikola, Đure->Đuro,
Mileta->Mile, or unchanged) are scored by how often each occurs as a soldier's
first name, in the same brigade first (regional forms differ: "Pere" is Pero in
Lika, Pera in Vojvodina), then across all brigades. No clear winner -> unchanged.
Units whose config says fathers_name_form 'possessive' also get possessives converted
(Omerov->Omer, Mujin->Mujo, Alijin->Alija).

middle_name keeps the printed (genitive) form; only fathers_name changes.

Usage:
    python scripts/convert_fathers_genitive.py            # dry run: mapping + stats
    python scripts/convert_fathers_genitive.py --write    # append corrections
    python scripts/apply_corrections.py --apply
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8', errors='replace')
sys.path.insert(0, str(Path(__file__).parent))
from name_utils import BRIGADE_CONFIGS  # noqa: E402
from cleanup_text_fields import live_json_files  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
CONSONANT = set('bcčćdđfghjklmnprsštvzž')
NAME = re.compile(r'^[A-ZČĆŽŠĐ][a-zčćžšđ]+$')
MIN_COUNT = 3       # candidate must occur at least this often as a first name
DOMINANCE = 2.0     # and at least this many times more often than the runner-up

# Reviewed by hand: forms the corpus can't decide. (corrected printed form or None, nominative)
OVERRIDES = {
    'Pavia': ('Pavla', 'Pavle'),            # OCR of "Pavla" in the source PDFs' text layer
    'Zivojina': ('Živojina', 'Živojin'),    # OCR dropped the diacritic
    'Kuzmana': (None, 'Kuzman'), 'Ranisava': (None, 'Ranisav'), 'Gligora': (None, 'Gligor'),
    'Aranđela': (None, 'Aranđel'), 'Šćepana': (None, 'Šćepan'), 'Nikodina': (None, 'Nikodin'),
    'Ignjatija': (None, 'Ignjatije'), 'Aleksija': (None, 'Aleksije'),
    'Isaila': (None, 'Isailo'), 'Mikaila': (None, 'Mikailo'),
    'Ćetka': (None, 'Ćetko'), 'Trivka': (None, 'Trivko'), 'Vica': (None, 'Vice'),
}


def candidates(g: str) -> set[str]:
    c = {g}
    if g.endswith('a'):
        stem = g[:-1]
        c |= {stem, stem + 'o', stem + 'e'}
        if len(stem) >= 3 and stem[-1] in CONSONANT and stem[-2] in CONSONANT:
            c.add(stem[:-1] + 'a' + stem[-1])          # Petra -> Petar, Aleksandra -> Aleksandar
        if g.endswith('ta') and len(g) > 4:
            c.add(g[:-2])                               # Mileta -> Mile, Radeta -> Rade
    elif g.endswith('e'):
        stem = g[:-1]
        c |= {stem + 'o', stem + 'a'}                   # Đure -> Đuro, Nikole -> Nikola
    elif g.endswith(('ov', 'ev')):                      # possessive: Omerov -> Omer, Petrov -> Petar
        stem = g[:-2]
        c |= {stem, stem + 'o', stem + 'e'}
        if len(stem) >= 3 and stem[-1] in CONSONANT and stem[-2] in CONSONANT:
            c.add(stem[:-1] + 'a' + stem[-1])
    elif g.endswith('in'):                              # possessive: Mujin -> Mujo, Alijin -> Alija, Ibrin -> Ibro
        stem = g[:-2]
        c |= {stem + 'a', stem + 'o', stem + 'e', stem}
    return c


def pick(g: str, local: Counter, overall: Counter, rare: bool = False) -> str | None:
    # Forms seen only a handful of times get a stricter, corpus-wide test
    tests = [(overall, 10, 3.0)] if rare else [(local, MIN_COUNT, DOMINANCE), (overall, MIN_COUNT, DOMINANCE)]
    for counts, min_count, dominance in tests:
        scored = sorted(((counts[c], c) for c in candidates(g)), reverse=True)
        (best_n, best), (second_n, _) = scored[0], (scored[1] if len(scored) > 1 else (0, None))
        if best_n >= min_count and best_n >= dominance * max(second_n, 1):
            return best
    return None


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--write', action='store_true', help='append corrections to corrections.json')
    ap.add_argument('--brigade', type=int, help='convert only this unit (the counts still come from all units)')
    args = ap.parse_args()

    live = live_json_files()
    brigades = {code: json.loads((ROOT / 'website' / 'public' / c['json_file']).read_text(encoding='utf-8'))
                for code, c in sorted(BRIGADE_CONFIGS.items()) if c['json_file'] in live}
    first_names = {code: Counter(s['first_name'] for s in d if NAME.match(s['first_name'] or '')) for code, d in brigades.items()}
    overall = sum(first_names.values(), Counter())

    corrections_path = ROOT / 'corrections.json'
    corrections = json.loads(corrections_path.read_text(encoding='utf-8'))
    next_id = max(c['id'] for c in corrections) + 1

    form_counts = Counter(s.get('fathers_name') for d in brigades.values() for s in d)
    new, mapping, undecided = [], Counter(), Counter()
    for code, soldiers in brigades.items():
        if not BRIGADE_CONFIGS[code].get('has_fathers_name') or BRIGADE_CONFIGS[code].get('fathers_name_form') == 'nominative':
            continue
        if args.brigade and code != args.brigade:
            continue
        # books that print some fathers as possessives ("Omerov", "Mujin") as well as genitives
        endings = ('a', 'e', 'ov', 'ev', 'in') if BRIGADE_CONFIGS[code].get('fathers_name_form') == 'possessive' \
            else ('a', 'e')
        for s in soldiers:
            g = s.get('fathers_name') or ''
            if g != (s.get('middle_name') or '') or not NAME.match(g) or not g.endswith(endings):
                continue
            fields = {}
            if g in OVERRIDES:
                printed, nom = OVERRIDES[g]
                if printed:
                    fields['middle_name'] = printed
            else:
                nom = pick(g, first_names[code], overall, rare=form_counts[g] <= 3)
            if nom is None:
                undecided[g] += 1
                continue
            if nom == g:
                continue
            mapping[(g, nom)] += 1
            fields.update({'fathers_name': nom, 'birth_year': s.get('birth_year', '')})
            reason = f"Father's name genitive -> nominative: {g} -> {nom}"
            if 'middle_name' in fields:
                reason += f" (OCR: printed form is {fields['middle_name']})"
            new.append({'id': next_id + len(new), 'action': 'edit', 'soldier_id': s['soldier_id'],
                        'fields': fields, 'reason': reason})

    print(f'{len(new)} records to convert, {len(mapping)} distinct forms; {sum(undecided.values())} left undecided ({len(undecided)} forms)')
    print('\nMost frequent conversions:')
    for (g, n), k in mapping.most_common(60):
        print(f'  {k:4d}  {g:12s} -> {n}')
    print('\nMost frequent undecided:', ', '.join(f'{g} ({k})' for g, k in undecided.most_common(30)))

    if args.write and new:
        corrections_path.write_text(json.dumps(corrections + new, ensure_ascii=False, indent=2), encoding='utf-8')
        print(f"\nAppended corrections {new[0]['id']}-{new[-1]['id']}")
    elif new:
        print('\nDry run. Use --write to append these corrections.')


if __name__ == '__main__':
    main()
