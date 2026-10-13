"""
Choose the pairs to write for a book across units that lists soldiers by place (the Karlovac kotar volumes: village
and općina headings, the fallen and the holders of the spomenica 1941), from the matches scripts/match_references.py
grades (--json). The chosen pairs go to a file for match_references.py --only.

    sure pairs, as the matcher grades them;
    likely pairs whose village agrees and so does the day of death, or the place of death: a place named after the
        death in the book's entry ("Poginuo na Udbini", "u Kuljanima kod Banja Luke") that the record names too, not the
        towns of the book's općine (every record of the area names them), nor his own village ("Poginuo u Kruškovcu",
        "iz Kruškovca"), nor a region ("Dalmacija", "Srijem");
    never a fallen fighter's entry against a record of a man who lived: one from a list of survivors that names no
        death (find_source_duplicates.LIST_FATE: Druga lička's "Živi u Kolutu"), or one that has him alive after the war
        ("Umro posle rata u Apatinu", "Pukovnik u penziji");
    never a record that two entries of one list match (two men of one name: "Čanak Nikole Mane" twice in Široka Kula).
Pairs checked by hand and found wrong are given as record:ref after the output file and left out.

Usage:
    python scripts/match_references.py hak-14-donji-lapac --json m.json
    python scripts/select_place_references.py m.json hak-14-donji-lapac pairs.txt [record:ref ...]
    python scripts/match_references.py hak-14-donji-lapac --only pairs.txt
The likely pairs taken are printed, the book's death against the record's, for a look before writing.
"""
from __future__ import annotations

import glob
import json
import re
import sys
from collections import defaultdict
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, str(Path(__file__).parent))
from find_source_duplicates import LIST_FATE  # noqa: E402
from match_references import entries_path, fold  # noqa: E402

CAP = r'[A-ZČĆŽŠĐ][a-zčćžšđ]{3,}'
DEATH = re.compile(r'\b(?:pogin\w*|ubil\w*|ubijen\w*|strijelja\w*|umr\w*|nesta\w*|zaklal\w*|likvidir\w*)\b', re.I)
DIED = re.compile(r'\b(?:pogin\w*|poginu\w*|umr\w*|ubijen\w*|ubil\w*|strijelja\w*|streljan\w*|nesta\w*)', re.I)
# words after a death that name no place, and regions too wide to agree on
STOP = {fold(w)[:4] for w in (
    'kotar', 'opcina', 'kasnije', 'clan', 'borac', 'komandir', 'komesar', 'brig', 'bataljona', 'skoja', 'ustase',
    'nijemci', 'cetnici', 'talijani', 'srbin', 'hrvat', 'lika', 'licki',
    # the towns of Lika that so many records name ("kod Gospića") that a death there tells two men apart from nothing
    'gospic', 'medak', 'perusic', 'smiljan', 'karlobag', 'kosinj', 'pazariste',
    'dalmacija', 'bosna', 'bosni', 'srijem', 'srem', 'kordun', 'banija', 'slavonija', 'hrvatska', 'srbija')}


def words(text: str) -> set:
    return {fold(w)[:4] for w in re.findall(CAP, text)}


def main():
    matches = json.load(open(sys.argv[1], encoding='utf-8'))
    book, out = sys.argv[2], sys.argv[3]
    drop = {tuple(x.split(':')) for x in sys.argv[4:]}
    ents = {e['soldier_id']: e for e in json.loads(entries_path(book).read_text(encoding='utf-8'))}
    opcine = {w for e in ents.values() for w in words(e['born_in'].split(',')[-1])}
    recs = {s['soldier_id']: s for fn in glob.glob('website/public/*soldiers.json')
            for s in json.load(open(fn, encoding='utf-8'))}

    def place_agrees(f) -> bool:
        e, s = ents[f['ref']], recs[f['record']]
        text = e['additional_info'].split(':', 1)[-1]
        m = DEATH.search(text)
        if not m:
            return False
        home = words(e['born_in'] + ' ' + e['additional_info'].split(':')[0])
        died_at = words(text[m.end():m.end() + 80]) - STOP - opcine - home
        record = ' '.join([s.get('additional_info') or '', s.get('death_place') or ''] +
                          [o.get('additional_info') or '' for o in s.get('other_sources', ()) if not o.get('ref_book')])
        return bool(died_at & words(record))

    def lived(s) -> bool:
        text = s.get('additional_info') or ''
        return ((LIST_FATE.get(s.get('pdf_file')) == 'lived' and not DIED.search(text))
                or bool(re.search(r'\b(?:Živi|živi u|posle rata|poslije rata|nakon rata|penziji)\b', text)))

    chosen = []
    for f in matches:
        if (f['record'], f['ref']) in drop:
            continue
        if ents[f['ref']].get('list') == 'Pali borci' and lived(recs[f['record']]):
            continue
        if f['grade'] == 'sure':
            chosen.append(f)
        elif f['grade'] == 'likely' and 'birthplace' in f['agree'] and ('death day' in f['agree'] or place_agrees(f)):
            chosen.append(dict(f, grade='likely+place'))
    by_rec = defaultdict(list)
    for f in chosen:
        by_rec[(f['record'], ents[f['ref']].get('list'))].append(f)
    ambiguous = {(f['record'], f['ref']) for v in by_rec.values() if len(v) > 1 for f in v}
    chosen = [f for f in chosen if (f['record'], f['ref']) not in ambiguous]
    pairs = sorted({(f['record'], f['ref']) for f in chosen})
    Path(out).write_text(''.join(f'{a} {b}\n' for a, b in pairs), encoding='utf-8')
    grades = defaultdict(int)
    for f in chosen:
        grades[f['grade']] += 1
    print(f'{len(pairs)} pairs, {len({b for _, b in pairs})} entries, {len({a for a, _ in pairs})} records; '
          f'{dict(grades)}; {len(ambiguous)} left out as ambiguous')
    for f in (f for f in chosen if f['grade'] == 'likely+place'):
        print(' ', f['ref_name'], '|', f['record'], f['record_name'], f['agree'], '|',
              ents[f['ref']]['additional_info'][-60:], '||', (recs[f['record']].get('additional_info') or '')[:70])


if __name__ == '__main__':
    main()
