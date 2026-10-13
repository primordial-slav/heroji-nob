"""
Choose the pairs to write for the 1964 census of the war's dead (Žrtve rata 1941-1945, one book per republic and
province, data-extraction/zrtve-rata/zrtve-rata-1964-<vol>-entries.json) from the matches
scripts/match_references.py grades (--json, one file per volume), for match_references.py --only.

The census gives every fallen partisan his father, birth year, village, year and place of death, but no unit, so:
    sure pairs, as the matcher grades them (the father and one more, or birth year and birthplace);
    likely pairs where two of birth year, birthplace, year of death and place of death agree ("Đorđević (Krsta)
        Vojislav, rođen 1915, Kamenica (Niš), poginuo 1945, Špionica" and the record's "rođen 1915. u Nišu, poginuo
        6. aprila 1945. u selo Špionica"), when the pairing is the only one both ways: the entry fits no other record,
        and no other census entry fits the record.
A likely pair with one thing in common (the year of death alone, the birth year alone) is left out: the census holds
180,000 fighters, and the same name and year are often two men.

Usage:
    python scripts/select_census_references.py pairs.txt matches_slo.json matches_hrv.json ...
The output's third column says why (match_references.py --only puts it in the reason).
"""
from __future__ import annotations

import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')
FACTS = {'birth year', 'birthplace', 'death year', 'death place'}


def main():
    out, files = sys.argv[1], sys.argv[2:]
    matches = [m for f in files for m in json.loads(Path(f).read_text(encoding='utf-8'))]
    by_ref, by_record = defaultdict(set), defaultdict(set)
    for m in matches:
        by_ref[m['ref']].add(m['record'])
        by_record[m['record']].add(m['ref'])
    sure_refs = {m['ref'] for m in matches if m['grade'] == 'sure'}
    chosen, why = [], Counter()
    for m in matches:
        if m['grade'] == 'sure':
            chosen.append((m['record'], m['ref'], 'census:sure'))
            why['sure'] += 1
        elif m['grade'] == 'likely' and m['ref'] not in sure_refs and len(FACTS & set(m['agree'])) >= 2:
            if len(by_ref[m['ref']]) == 1 and len(by_record[m['record']]) == 1:
                chosen.append((m['record'], m['ref'], 'census:' + '+'.join(sorted(FACTS & set(m['agree']))).replace(' ', '_')))
                why['likely, two facts, unique'] += 1
            else:
                why['likely left out: not unique'] += 1
    Path(out).write_text(''.join(f'{a} {b} {c}\n' for a, b, c in sorted(set(chosen))), encoding='utf-8')
    print(f'{len(set(chosen))} pairs, {len({b for _, b, _ in chosen})} entries, {len({a for a, _, _ in chosen})} records; '
          f'{dict(why)}')


if __name__ == '__main__':
    main()
