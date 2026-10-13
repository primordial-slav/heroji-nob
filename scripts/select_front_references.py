"""
Choose the pairs to write for a book across units that lists the fallen of one front by unit and prints little more
than the name (Tmušić's Sremski front: "Poginuli borci <the brigade>: 1. Aćimović M. Čedomir, 2. ..."), for
match_references.py --only.

An entry goes to a record of the same name (surname and given name, or the nickname) in the entry's unit (`units`),
with nothing that disagrees as scripts/match_references.py weighs it (another father, another year of death), when the
record has him fall on that front:
    father      the father's initial the book prints agrees;
    months      the record's death, to the month, lies in the front's months (`window`, from - to, YYYY-MM);
    year        the record gives only the year, one of the front's (`death_years`);
    place       the record's place of death, or the words after its death, name a place of the front (`FRONTS`);
    Gončin      the record already carries the entry of another list of the same front's fallen (`also_lists`);
never a record whose death, to the month, lies outside the front's months, nor one of a man who lived ("Živi", "umro
1967", a list of survivors without a death). An entry that two records of its unit fit (two men of the name, both
killed on the front: Petrović Dragoljub six times in the 1. proleterska) is left out, unless only one agrees on the
father; so is a record that two entries fit.

Usage:
    python scripts/select_front_references.py sremski-front-poginuli pairs.txt [--sample N]
    python scripts/match_references.py sremski-front-poginuli --only pairs.txt
"""
from __future__ import annotations

import json
import random
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, str(Path(__file__).parent))
import extract_structured_fields as structured  # noqa: E402
from extract_life_events import parse_when  # noqa: E402
from find_source_duplicates import LIST_FATE  # noqa: E402
from match_references import entries_path, evidence, fold  # noqa: E402

# each book: its front's months, the other lists of the same front's fallen, and the front's places (folded word
# beginnings, long enough not to be a name: "sid" only as a word, Šid; no "otok", an island in Dalmatia's books, no
# "mitrovic", Kosovska Mitrovica too)
FRONTS = {
    'sremski-front-poginuli': {
        'window': ('1944-10', '1945-04'),
        'also_lists': ('u-rovovima-srema-poginuli',),
        'places': (
            'srem', 'srijem', 'tovarnik', 'ilinc', 'batrovc', 'batrovac', 'lipovac', 'lipovc', 'spacv', 'bapsk',
            'novakbapsk', 'mohov', 'ilok', 'sarengrad', 'opatovac', 'opatovc', 'lovas', 'sotin', 'vukovar', 'negoslav',
            'orolik', 'nijemc', 'nijemac', 'nemac', 'nemc', 'podgradj', 'apsev', 'djeletov', 'deletov', 'slakov',
            'komletin', 'vinkov', 'mirkovc', 'mirkovac', 'privlak', 'nustar', 'jarmin', 'bogdanovc', 'svinjarev',
            'tompojev', 'miklusev', 'adasev', 'gibarac', 'gibarc', 'kukujev', 'erdevik', 'bacinc', 'bacinac',
            'berkasov', 'bingul', 'divos', 'morovic', 'visnjicev', 'jamen', 'martinc', 'martinac', 'lacarak',
            'lacark', 'bosut', 'molovin', 'neštin', 'nestin', 'vizic', 'susek', 'strosinc', 'dobrinc', 'dobrinac',
            'suljam', 'ilaca', 'ilaci', 'ilacu', 'sidsk', 'banovci', 'banovac', 'rajevo selo', 'cerin', 'cerna',
            'ostrovo', 'ostrova', 'ostrovu', 'grabovo', 'grabova', 'grabovu', 'spajinsk', 'berak', 'beraka',
            'bokšic', 'matora', 'kuzmin', 'sremsk', 'fruskogor', 'fruska gor', 'vrdnik', 'irig', 'ruma', 'rume', 'rumi',
            'jarak', 'hrtkov', 'platicev', 'klenak', 'grgurev', 'kusk', 'ljuba', 'ljubi', 'ljube'),
        'words': ('sid', 'sida', 'sidu', 'sidom'),
    },
}
MONTHS = {'jan': 1, 'feb': 2, 'mar': 3, 'apr': 4, 'maj': 5, 'jun': 6, 'jul': 7, 'avg': 8, 'aug': 8, 'sep': 9,
          'okt': 10, 'nov': 11, 'dec': 12, 'sij': 1, 'velj': 2, 'ozuj': 3, 'trav': 4, 'svib': 5, 'lip': 6, 'srp': 7,
          'kol': 8, 'ruj': 9, 'list': 10, 'stud': 11, 'pros': 12}
ROMAN = {'I': 1, 'II': 2, 'III': 3, 'IV': 4, 'V': 5, 'VI': 6, 'VII': 7, 'VIII': 8, 'IX': 9, 'X': 10, 'XI': 11, 'XII': 12}
DIED = re.compile(r'\b(?:pogin\w*|pog\.|umr\w*|umro|umrla|ubijen\w*|nesta[ol]\w*|streljan\w*|strijeljan\w*|'
                  r'podlegao|podlegla|preminu\w*)', re.I)
LIVED = re.compile(r'\b(?:Živi|živi u|posle rata|poslije rata|nakon rata|penziji|umro 19[5-9]\d|umrla 19[5-9]\d)\b')


def when(text: str) -> tuple[int, int] | None:
    """(year, month) of the first date in the text, month 0 when it gives only the year"""
    m = re.search(r'\b(\d{1,2})(?:/\d{1,2})?\s*[./]\s*(\d{1,2}|[IVX]{1,4})\s*[./]\s*(19\d\d)', text)
    if m:
        mon = ROMAN.get(m.group(2)) if not m.group(2).isdigit() else int(m.group(2))
        if mon and 1 <= mon <= 12:
            return int(m.group(3)), mon
    m = re.search(r'\b([a-zčćžšđ]{3,})\w*\s+(19\d\d)', text, re.I)
    if m:
        key = fold(m.group(1))
        mon = next((v for k, v in MONTHS.items() if key.startswith(k)), None)
        if mon:
            return int(m.group(2)), mon
    m = re.search(r'\b(19[34]\d)\b', text)
    return (int(m.group(1)), 0) if m else None


def record_death(s: dict) -> tuple[tuple[int, int] | None, str]:
    """When the record has him die (from the field, else the words after a death in its text) and the words after it"""
    texts = [s.get('additional_info') or ''] + [o.get('additional_info') or '' for o in s.get('other_sources', ())
                                                if not o.get('ref_book')]
    after = ' '.join(t[m.end():m.end() + 90] for t in texts for m in [DIED.search(t)] if m)
    w = parse_when(s['death_date']) if s.get('death_date') else None
    if w and w[0][0]:
        return (w[0][0], w[0][1] or 0), after
    return (when(after) if after else None), after


def main():
    book, out = sys.argv[1], sys.argv[2]
    front = FRONTS[book]
    lo, hi = (tuple(int(x) for x in d.split('-')) for d in front['window'])
    years = {lo[0], hi[0]}
    refs = json.loads(entries_path(book).read_text(encoding='utf-8'))
    units = {c for r in refs for c in r.get('units', ())}
    index = defaultdict(list)
    for code, (_, soldiers) in structured.load_live().items():
        if code in units:
            for s in soldiers:
                index[(code, fold(s.get('last_name')), fold(s.get('first_name')))].append(s)

    def on_front(s: dict) -> list[str] | None:
        """Why the record has him fall on the front ([] when it says nothing of it), None when it rules him out"""
        text = s.get('additional_info') or ''
        if LIVED.search(text) or (LIST_FATE.get(s.get('pdf_file')) == 'lived' and not DIED.search(text)):
            return None
        died, after = record_death(s)
        why = []
        if died:
            if died[1]:
                if not lo <= died <= hi:
                    return None
                why.append('months')
            elif died[0] in years:
                why.append('year')
            else:
                return None
        words = fold(' '.join([s.get('death_place') or '', after])).split()
        if any(w.startswith(p) for w in words for p in front['places']) or set(words) & set(front['words']):
            why.append('place')
        if any(o.get('ref_book') in front['also_lists'] for o in s.get('other_sources', ())):
            why.append('Gončin')
        return why

    fits = defaultdict(list)                      # entry -> [(record, why)]
    for ref in refs:
        names = {fold(ref['first_name'])} | ({fold(ref['nick'])} if ref.get('nick') else set())
        for code in ref.get('units', ()):
            for n in names:
                for s in index.get((code, fold(ref['last_name']), n), []):
                    agree, clash = evidence(ref, s)
                    if [c for c in clash if c != 'father?']:
                        continue
                    why = on_front(s)
                    if why is None:
                        continue
                    if 'father' in agree:
                        why = ['father'] + why
                    if why:
                        fits[ref['soldier_id']].append((s, why))
    chosen, left = {}, Counter()
    for rid, fs in fits.items():
        if len(fs) > 1:
            with_father = [f for f in fs if 'father' in f[1]]
            if len(with_father) == 1:
                fs = with_father
            else:
                left['two records of the unit fit'] += 1
                continue
        chosen[rid] = fs[0]
    by_record = Counter(s['soldier_id'] for s, _ in chosen.values())
    for rid in [r for r, (s, _) in chosen.items() if by_record[s['soldier_id']] > 1]:
        del chosen[rid]
        left['a record two entries fit'] += 1
    Path(out).write_text(''.join(f"{s['soldier_id']} {rid} front:{'+'.join(why)}\n"
                                 for rid, (s, why) in sorted(chosen.items())), encoding='utf-8')
    kinds = Counter('+'.join(why) for s, why in chosen.values())
    print(f'{len(refs)} entries; {len(chosen)} pairs written to {out}; left out: {dict(left)}')
    for k, v in kinds.most_common():
        print(f'  {v:5d}  {k}')
    if '--sample' in sys.argv:
        n = int(sys.argv[sys.argv.index('--sample') + 1])
        random.seed(3)
        byid = {r['soldier_id']: r for r in refs}
        for rid, (s, why) in random.sample(sorted(chosen.items()), n):
            print(f"  {byid[rid]['name']} [{byid[rid]['unit'][:20]}] -> {s['full_name']} {s['soldier_id']} {why} | "
                  f"{(s.get('additional_info') or '')[:100]}")


if __name__ == '__main__':
    main()
