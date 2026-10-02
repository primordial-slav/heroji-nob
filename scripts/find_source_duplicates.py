"""
Find soldiers printed in more than one of a unit's lists (two books, or two lists in one book), and propose
`merge` corrections that make them one entry (see apply_corrections.apply_merge).

A list is a PDF, or a page range of one (LISTS below), or a web page (source_url). Two records of different lists
are the same soldier when surname and given name agree (diacritics, dj/đ and case aside) and nothing else
disagrees: the father (as printed or in the nominative), the birth year (a year apart is allowed: books count
differently), the birthplace and the place of death (a word in common), the year of death, whether he fell or
lived to the end of the war, and a duty both name (komandir čete). Each match is graded:

  sure      the names agree, something else agrees too (father, birth year or place, death year or place),
            nothing disagrees,
            and neither record has another candidate
  name      the names agree and nothing disagrees, but nothing else confirms it either (one list prints
            father, birth or death) and neither record has another candidate
  likely    at least two things agree and fewer disagree (a misread birthplace, a year apart in the death
            date), the fathers don't differ (brothers and cousins share names), neither record has another
            candidate, and both fell (or neither says)
  review    anything else worth a look: several candidates, more disagreement, one who lived to the end of
            the war and one who fell, a given name a letter apart (Radoslav / Radosav)

The record of the list the unit names first (units.ts pdfFiles order) keeps its id; the other is merged into it.

Across units (--across) the same is done for records of the same name in two units' books, stricter (sure: two
things or more agree, nothing disagrees); those become `link` corrections, which keep both records and show each
the other's entries (apply_corrections.apply_links).

Usage:
    python scripts/find_source_duplicates.py --brigade 30                  # print the matches
    python scripts/find_source_duplicates.py --across --write sure         # link soldiers found in two units
    python scripts/find_source_duplicates.py --brigade 30 --write sure     # append the sure ones as merges
    python scripts/find_source_duplicates.py --brigade 3 --write sure,likely --min-agree 2   # fallen vs survivors
    python scripts/find_source_duplicates.py --brigade 30 --json out.json  # every match, for review
"""
import argparse
import json
import os
import re
import sys
import unicodedata
from collections import defaultdict
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8', errors='replace')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from name_utils import BRIGADE_CONFIGS  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
CORRECTIONS = ROOT / 'corrections.json'

# PDFs that hold more than one list: {pdf_file: [(first page, list name), ...]}
LISTS = {
    '16-slavonska-omladinska.pdf': [(1, 'poginuli'), (34, 'Pokuplje i Žumberak'), (38, 'rukovodioci')],
    '4-splitska-brigada.pdf': [(1, 'poginuli'), (23, 'preživjeli')],
    'cankarjeva.pdf': [(1, 'seznam'), (33, 'padli')],
    'gubceva.pdf': [(1, 'seznam'), (38, 'padli')],
    'dvanajsta.pdf': [(1, 'padli'), (5, 'seznam')],
    'gradnikova.pdf': [(1, 'padli'), (11, 'drugi')],
    'istrski-odred.pdf': [(1, 'seznam'), (23, 'padli')],
    'zapadnodolenjski-odred.pdf': [(1, 'seznam'), (8, 'padli')],
    'braciceva.pdf': [(1, 'padli'), (25, 'preziveli')],
    '1-slovenska-artilerijska.pdf': [(1, 'starešine'), (5, 'topničarji'), (16, 'padli')],
    'artilerija-9-korpusa.pdf': [(1, 'borci'), (9, 'padli')],
    '19-srpska.pdf': [(1, 'poginuli'), (62, 'preziveli')],
    '22-srpska.pdf': [(1, 'poginuli'), (24, 'preziveli')],
    '12-vojvodjanska.pdf': [(1, 'spisak'), (34, 'poginuli')],
    '4-vojvodjanska.pdf': [(1, 'pripadnici 7. 10. 1943'), (32, 'poginuli')],
    '1-kosovsko-metohijska.pdf': [(1, 'bataljoni'), (16, 'iz Porečja'), (19, 'od Junika'), (25, 'poginuli'), (31, 'ranjeni')],
    '21-srpska.pdf': [(1, 'poginuli'), (29, 'preziveli'), (80, 'borili su se')],
    '14-hercegovacka.pdf': [(1, 'spisak'), (33, 'poginuli')],
    '7-srpska.pdf': [(1, 'maj 1944'), (12, 'poginuli')],
    '15-srpska.pdf': [(1, 'spisak'), (13, 'poginuli'), (17, 'ranjeni')],
    '1-konjicka.pdf': [(1, 'pali'), (5, 'ratni spisak')],
    'karlovacka.pdf': [(1, 'na dan formiranja'), (23, 'poginuli')],
    '4-sandzacka.pdf': [(1, 'poginuli'), (11, 'ranjeni')],
    'tomsiceva-4.pdf': [(1, '1943-1944'), (49, '1944-1945')],
}


def fold(text: str) -> str:
    """'Đurđević' -> 'djurdjevic', 'Djurdjević' -> 'djurdjevic': lowercase, no diacritics, đ as dj."""
    t = (text or '').lower().replace('đ', 'dj')
    t = ''.join(c for c in unicodedata.normalize('NFD', t) if not unicodedata.combining(c))
    return re.sub(r'[^a-z]', '', t)


def list_index(s: dict) -> int:
    """Which of its PDF's lists (LISTS) the record is in."""
    pages = [first for first, _ in LISTS.get(s.get('pdf_file'), ())]
    return sum(1 for first in pages[1:] if (s.get('pdf_page') or 0) >= first)


def list_of(s: dict) -> str:
    f = s.get('pdf_file')
    if not f:
        return (s.get('source_url') or '').split('#')[0]
    return f'{f} ({LISTS[f][list_index(s)][1]})' if f in LISTS else f


def list_rank(code: int) -> dict:
    """units.ts pdfFiles order: the unit's own list first."""
    text = (ROOT / 'website' / 'app' / 'data' / 'units.ts').read_text(encoding='utf-8')
    json_file = BRIGADE_CONFIGS[code]['json_file']
    m = re.search(r"dataFile: '/" + re.escape(json_file) + r"',\s*pdfFiles: \[([^\]]*)\]", text)
    files = re.findall(r"'/pdfs/([^']+)'", m.group(1)) if m else []
    return {f: i for i, f in enumerate(files)}


def year(text: str) -> int | None:
    m = re.search(r'1[89]\d\d', text or '')
    return int(m.group()) if m else None


# words that name no place: "kod", "selo", "Pakrac" is a place but the district repeats for everyone in a list
NOT_PLACE = {'kod', 'selo', 'selu', 'sela', 'grad', 'gradu', 'opcina', 'kotar', 'srez', 'oblast', 'okolina', 'blizu'}


def places(text: str) -> set[str]:
    """'Gornja Sumetlica, Pakrac' -> {'gornj', 'sumet', 'pakra'}: word stems, so cases and diacritics don't matter."""
    words = re.findall(r'\w{4,}', (text or '').lower())
    return {fold(w)[:5] for w in words if fold(w) not in NOT_PLACE}


QUALIFIERS = {'v': 'vel', 'vel': 'vel', 'velik': 'vel', 'veliki': 'vel', 'velika': 'vel', 'veliko': 'vel', 'm': 'mal',
              'mal': 'mal', 'mali': 'mal', 'mala': 'mal', 'malo': 'mal', 'g': 'gor', 'gor': 'gor', 'gornji': 'gor',
              'gornja': 'gor', 'gornje': 'gor', 'd': 'don', 'donji': 'don', 'donja': 'don', 'donje': 'don'}


def village(text: str) -> tuple[str, set[str]]:
    """'V. Ivanča, Mladenovac' -> ('vel', {'ivan'}): the place before the district, Gornja/Donja/Velika/Mala apart."""
    first = re.split(r',|\(| [-—–] ', (text or '').lower())[0]
    words = [fold(w) for w in re.findall(r'\w+', first)]
    qualifier = next((QUALIFIERS[w] for w in words if w in QUALIFIERS), '')
    return qualifier, {w[:4] for w in words if len(w) >= 4 and w not in QUALIFIERS and w not in NOT_PLACE}


def same_place(a: str, b: str) -> bool | None:
    """True: the same village; False: different places; None: only the district is shared (one names the village,
    the other only its district), or there is nothing to compare."""
    (qa, va), (qb, vb) = village(a), village(b)
    if not (va and vb):
        return None
    if va & vb:
        return not (qa and qb and qa != qb)              # Velika Ivanča is not Mala Ivanča
    return None if places(a) & places(b) else False


SURVIVED = re.compile(r'kraj rata (?:je )?do[cč]ekao|pre[zž]ivio|\bživ(?:i|e)?\b|demobili|umro (?:je )?(?:posle|poslije|nakon) rata', re.I)


# lists of only the fallen, or only those who lived to the end of the war: every entry's fate, said or not
LIST_FATE = {
    'druga-licka-spisak.pdf': 'fell', 'druga-licka-sjecanja-poginuli.pdf': 'fell', 'druga-licka-sjecanja-prezivjeli.pdf': 'lived',
    '17-slavonska-poginuli.pdf': 'fell', '17-slavonska-prezivjeli.pdf': 'lived',
    'treca-proleterska-poginuli-knj3.pdf': 'fell', '3-krajiska-proleterska.pdf': 'fell', 'druga-proleterska.pdf': 'fell',
    '6-krajiska.pdf': 'fell', '6-krajiska-prezivjeli.pdf': 'lived',
    '12-krajiska-poginuli.pdf': 'fell', '12-krajiska-prezivjeli.pdf': 'lived',
    'cankarjeva.pdf (seznam)': 'lived', 'cankarjeva.pdf (padli)': 'fell',          # a list of a PDF (LISTS) by its name
    'gubceva.pdf (seznam)': 'lived', 'gubceva.pdf (padli)': 'fell',
    'dvanajsta.pdf (seznam)': 'lived', 'dvanajsta.pdf (padli)': 'fell',
    'gradnikova.pdf (padli)': 'fell',
    'istrski-odred.pdf (padli)': 'fell',
    'zapadnodolenjski-odred.pdf (padli)': 'fell',
    'braciceva.pdf (padli)': 'fell', 'braciceva.pdf (preziveli)': 'lived',
    '1-slovenska-artilerijska.pdf (topničarji)': 'lived', '1-slovenska-artilerijska.pdf (padli)': 'fell',
    'artilerija-9-korpusa.pdf (borci)': 'lived', 'artilerija-9-korpusa.pdf (padli)': 'fell',
    '19-srpska.pdf (poginuli)': 'fell', '19-srpska.pdf (preziveli)': 'lived',
    '22-srpska.pdf (poginuli)': 'fell', '22-srpska.pdf (preziveli)': 'lived',
    '12-vojvodjanska.pdf (poginuli)': 'fell',
    '4-vojvodjanska.pdf (poginuli)': 'fell',
    '21-srpska.pdf (poginuli)': 'fell', '21-srpska.pdf (preziveli)': 'lived',
    '14-hercegovacka.pdf (poginuli)': 'fell',
    '7-srpska.pdf (poginuli)': 'fell',
    '15-srpska.pdf (poginuli)': 'fell',
    '1-konjicka.pdf (pali)': 'fell',
    'karlovacka.pdf (poginuli)': 'fell',
    '4-sandzacka.pdf (poginuli)': 'fell',
}
# Borci Sutjeske: "krajem rata komandir čete" (his duty when the war ended) and a death after the war ("Umro 1982.")
SURVIVED_SUTJESKA = re.compile(r'(?<!poginuo )(?<!poginula )\bkrajem rata\b(?! (?:je )?(?:pogin|umr|nesta))'
                               r'|\bumr(?:o|la)\s+(?:je\s+)?(?:(?:\d{1,2}\.\s*)?[\w.]+\s+)?(?:19[5-9]\d|194[6-9])', re.I)


def fate(s: dict) -> str:
    if s.get('pdf_file') in LIST_FATE:
        return LIST_FATE[s['pdf_file']]
    if list_of(s) in LIST_FATE:
        return LIST_FATE[list_of(s)]
    info = ' '.join([s.get('additional_info') or ''] + [o.get('additional_info') or '' for o in s.get('other_sources', ())])
    if SURVIVED.search(info) or SURVIVED_SUTJESKA.search(info):
        return 'lived'
    if s.get('death_type') or re.search(r'\b(?:po\w?gin|umr|strelj|strijelj|nestao|nestala)', info):     # "Pojginuo"
        return 'fell'
    return ''


DUTY = re.compile(r'\b(komandant|komandir|komesar|na[cč]elnik|zamjeni|zameni|pomo[cć]ni|delegat)\w*', re.I)
LEVEL = re.compile(r'^\W*(?:\S+\s+){0,3}?\(?(brigad|bataljon|[cč]et)', re.I)
SAME_DUTY = {'pomocn': 'zamjen', 'zameni': 'zamjen'}       # "zamjenik (pomoćnik) komesara" = "pomoćnik komesara"


def duties(s: dict) -> set:
    """('komand', 'cet') for "komandir čete", "komandir 2. čete"; ('komesa', 'bat') and ('zamjen', 'bat') for
    "pomoćnik komesara 4. bataljona": each duty and the level that follows it, from the rank and the bios."""
    text = ' '.join([s.get('rank') or '', s.get('additional_info') or ''] + [o.get('additional_info') or '' for o in s.get('other_sources', ())])
    found = set()
    for m in DUTY.finditer(text):
        level = LEVEL.match(text[m.end():m.end() + 40])
        if level:
            duty = fold(m.group(1))[:6]
            found.add((SAME_DUTY.get(duty, duty), fold(level.group(1))[:3]))
    return found


def evidence(a: dict, b: dict) -> tuple[list[str], list[str]]:
    """What agrees and what disagrees between two records of the same name."""
    agree, clash = [], []
    fa = {fold(a.get('fathers_name')), fold(a.get('middle_name'))} - {''}
    fb = {fold(b.get('fathers_name')), fold(b.get('middle_name'))} - {''}
    if fa and fb:
        # the same name in another case (Nikole / Nikola), an initial (N. / Nikole), a letter misread (Cije / Cvije)
        same = fa & fb or any(x[:4] == y[:4] or (min(len(x), len(y)) >= 4 and one_letter_apart(x, y))
                               for x in fa for y in fb)
        initial = any(min(len(x), len(y)) == 1 and x[0] == y[0] for x in fa for y in fb)
        if same:
            agree.append('father')
        elif initial:
            agree.append('father initial')               # weaker: "M." for Milan or Marko
        else:
            clash.append('father')
    ya, yb = year(a.get('birth_year')), year(b.get('birth_year'))
    if ya and yb:
        (agree if abs(ya - yb) <= 1 else clash).append('birth year')
    for field, label in (('birth_place', 'birthplace'), ('death_place', 'death place')):
        same = same_place(a.get(field), b.get(field))
        if same is not None:
            (agree if same else clash).append(label)
    ya, yb = year(a.get('death_date')), year(b.get('death_date'))
    if ya and yb:
        (agree if ya == yb else clash).append('death year')
    fa, fb = fate(a), fate(b)
    if fa and fb and fa != fb:
        clash.append('one lived')
    if duties(a) & duties(b):                       # a duty both name (a list of leaders gives nothing else)
        agree.append('duty')
    return agree, clash


def one_letter_apart(a: str, b: str) -> bool:
    """Radoslav / Radosav, Milisav / Milosav, Budo / Buda: one letter added, dropped or changed."""
    if abs(len(a) - len(b)) > 1:
        return False
    i = 0
    while i < min(len(a), len(b)) and a[i] == b[i]:
        i += 1
    return a[i + 1:] == b[i + 1:] or a[i:] == b[i + 1:] or a[i + 1:] == b[i:]


def matches(soldiers: list[dict], rank: dict) -> list[dict]:
    by_name = defaultdict(list)
    by_surname = defaultdict(list)
    for s in soldiers:
        by_name[(fold(s['last_name']), fold(s['first_name']))].append(s)
        by_surname[fold(s['last_name'])].append(s)
    pairs = {}

    def consider(a, b, how):
        if list_of(a) == list_of(b) or a is b:
            return
        # a list published only as a web page (1. Dalmatinska) is the unit's own list: it comes first
        ra = rank.get(a.get('pdf_file'), -1 if a.get('source_url') else 99)
        rb = rank.get(b.get('pdf_file'), -1 if b.get('source_url') else 99)
        if (rb, list_index(b), b['soldier_id']) < (ra, list_index(a), a['soldier_id']):
            a, b = b, a
        key = (a['soldier_id'], b['soldier_id'])
        if key not in pairs:
            agree, clash = evidence(a, b)
            pairs[key] = {'keep': a, 'merge': b, 'how': how, 'agree': agree, 'clash': clash}

    for group in by_name.values():
        for i, a in enumerate(group):
            for b in group[i + 1:]:
                consider(a, b, 'name')
    # a given name that differs slightly, with the father or birth year agreeing
    for group in by_surname.values():
        for i, a in enumerate(group):
            for b in group[i + 1:]:
                ga, gb = fold(a['first_name']), fold(b['first_name'])
                if ga != gb and min(len(ga), len(gb)) >= 4 and one_letter_apart(ga, gb):
                    agree, clash = evidence(a, b)
                    if agree and not clash:
                        consider(a, b, 'given name differs')
    # each record's candidates in each other list: one, or one that agrees where all the others disagree
    sides = defaultdict(list)
    for p in pairs.values():
        sides[(p['keep']['soldier_id'], list_of(p['merge']))].append(p)
        sides[(p['merge']['soldier_id'], list_of(p['keep']))].append(p)

    def chosen(p, group):
        """The only candidate; the only one that agrees where the others disagree; or clearly the best: nothing
        disagrees, two things or more agree, and more than with any other candidate."""
        others = [q for q in group if q is not p]
        return (not others or (p['agree'] and not p['clash'] and all(q['clash'] for q in others))
                or (len(p['agree']) >= 2 and not p['clash'] and all(len(q['agree']) < len(p['agree']) for q in others)))

    def printed_twice(group):
        """The other list prints the soldier twice (both entries agree on two things or more, nothing disagrees):
        both merge into the one record."""
        return len(group) > 1 and all(len(q['agree']) >= 2 and not q['clash'] for q in group)

    for p in pairs.values():
        keep_side = sides[(p['keep']['soldier_id'], list_of(p['merge']))]
        merge_side = sides[(p['merge']['soldier_id'], list_of(p['keep']))]
        # the keeping list printing him twice: the entry goes to the first of them (the other stays as printed)
        first = printed_twice(merge_side) and p is min(merge_side, key=lambda q: q['keep']['soldier_id'])
        alone = (chosen(p, keep_side) or printed_twice(keep_side)) and (chosen(p, merge_side) or first)
        if p['how'] == 'name' and alone and not p['clash']:
            p['grade'] = 'sure' if p['agree'] else 'name'
        elif (alone and len(p['agree']) >= 2 and len(p['agree']) > len(p['clash'])
              and not {'one lived', 'father'} & set(p['clash'])):
            p['grade'] = 'likely'
        elif alone and len(p['agree']) >= 4 and p['clash'] == ['father']:
            p['grade'] = 'likely'           # born the same year in the same village, fell the same year in the same place
            p['note'] = 'the books name different fathers'
        else:
            p['grade'] = 'review'
        if not alone:
            p['note'] = 'several candidates'
        elif len(keep_side) > 1:
            p['note'] = 'printed twice'
    return sorted(pairs.values(), key=lambda p: (p['grade'], p['keep']['soldier_id']))


def show(p: dict) -> str:
    k, m = p['keep'], p['merge']
    ev = ', '.join([f"+{x}" for x in p['agree']] + [f"-{x}" for x in p['clash']]) or 'names only'
    return (f"{p['grade']:6s} {k['soldier_id']} {k['full_name']} ({k.get('birth_year') or '?'}, {list_of(k)})"
            f"  <-  {m['soldier_id']} {m['full_name']} ({m.get('birth_year') or '?'}, {list_of(m)})"
            f"  [{p['how']}; {ev}{'; ' + p['note'] if p.get('note') else ''}]")


def across_units(units: dict[int, list[dict]]) -> list[dict]:
    """Records of the same name in different units, graded like matches() but stricter: a soldier who served in
    two units is linked (both records stay), so only 'sure' (two things or more agree, nothing disagrees, the
    only candidate in that unit or clearly the best) and 'review'."""
    by_name = defaultdict(list)
    for code, soldiers in units.items():
        for s in soldiers:
            s['_unit'] = code
            if fold(s['last_name']) and fold(s['first_name']):
                by_name[(fold(s['last_name']), fold(s['first_name']))].append(s)
    pairs = []
    for group in by_name.values():
        if len({s['_unit'] for s in group}) < 2:
            continue
        for i, a in enumerate(group):
            for b in group[i + 1:]:
                if a['_unit'] != b['_unit']:
                    a, b = (a, b) if a['_unit'] < b['_unit'] else (b, a)
                    agree, clash = evidence(a, b)
                    pairs.append({'keep': a, 'merge': b, 'how': 'name', 'agree': agree, 'clash': clash})
    sides = defaultdict(list)
    for p in pairs:
        sides[(p['keep']['soldier_id'], p['merge']['_unit'])].append(p)
        sides[(p['merge']['soldier_id'], p['keep']['_unit'])].append(p)

    def chosen(p, group):
        others = [q for q in group if q is not p]
        return not others or all(len(q['agree']) < len(p['agree']) or q['clash'] for q in others)

    for p in pairs:
        alone = (chosen(p, sides[(p['keep']['soldier_id'], p['merge']['_unit'])])
                 and chosen(p, sides[(p['merge']['soldier_id'], p['keep']['_unit'])]))
        # a common name with an initial and a year is not enough: a place or the father's name must agree too
        strong = {'birthplace', 'death place', 'father'} & set(p['agree'])
        p['grade'] = 'sure' if alone and len(p['agree']) >= 2 and strong and not p['clash'] else 'review'
        if not alone:
            p['note'] = 'several candidates'
    return sorted(pairs, key=lambda p: (p['grade'], p['keep']['soldier_id']))


def append(new: list[dict]) -> tuple[int, int]:
    """Append to corrections.json, re-read right before writing (other sessions append too)."""
    corr = json.loads(CORRECTIONS.read_text(encoding='utf-8'))
    have = {(c['soldier_id'], c.get('merge_id') or c.get('link_id')) for c in corr if c['action'] in ('merge', 'link')}
    new = [c for c in new if (c['soldier_id'], c.get('merge_id') or c.get('link_id')) not in have]
    start = max(c['id'] for c in corr) + 1
    for i, c in enumerate(new):
        c['id'] = start + i
    tmp = CORRECTIONS.with_suffix('.json.tmp')
    tmp.write_text(json.dumps(corr + new, ensure_ascii=False, indent=2), encoding='utf-8')
    os.replace(tmp, CORRECTIONS)
    return start, len(new)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--brigade', type=int, help="find a unit's soldiers printed in two of its lists (merges)")
    ap.add_argument('--across', action='store_true', help="find soldiers printed in two units' books (links)")
    ap.add_argument('--write', help='grades to append as merge corrections, e.g. "sure" or "sure,name"')
    ap.add_argument('--only', help='file of "keep_id merge_id" lines: append exactly these (reviewed) matches')
    ap.add_argument('--min-agree', type=int, default=0,
                    help='write only matches where this many things agree (2 for a list of the fallen against one of survivors)')
    ap.add_argument('--reason', default='', help='text for the corrections\' reason (the lists are named anyway)')
    ap.add_argument('--json', help='write every match here, for review')
    args = ap.parse_args()

    if args.across:
        return main_across(args)
    cfg = BRIGADE_CONFIGS[args.brigade]
    soldiers = json.loads((ROOT / 'website' / 'public' / cfg['json_file']).read_text(encoding='utf-8'))
    found = matches(soldiers, list_rank(args.brigade))
    grades = defaultdict(int)
    for p in found:
        grades[p['grade']] += 1
        print(show(p))
    print(f"\n{cfg['name']}: {len(soldiers)} records, {len(found)} matches {dict(grades)}")

    if args.json:
        Path(args.json).write_text(json.dumps([{**{k: v for k, v in p.items() if k not in ('keep', 'merge')},
                                                'keep': p['keep'], 'merge': p['merge']} for p in found],
                                               ensure_ascii=False, indent=2), encoding='utf-8')
    chosen = []
    if args.write:
        want = set(args.write.split(','))
        chosen = [p for p in found if p['grade'] in want and len(p['agree']) >= args.min_agree]
    if args.only:
        ids = {tuple(ln.split()[:2]) for ln in Path(args.only).read_text(encoding='utf-8').splitlines() if ln.strip()}
        chosen += [p for p in found if (p['keep']['soldier_id'], p['merge']['soldier_id']) in ids and p not in chosen]
    if chosen:
        new = [{'id': 0, 'action': 'merge', 'soldier_id': p['keep']['soldier_id'], 'merge_id': p['merge']['soldier_id'],
                'merge_name': p['merge']['full_name'],
                'reason': f"Same soldier in {list_of(p['keep'])} and {list_of(p['merge'])}"
                          + (f"; same {', '.join(p['agree'])}" if p['agree'] else '') + (f'. {args.reason}' if args.reason else '')}
               for p in chosen]
        start, n = append(new)
        print(f"Appended {n} merge corrections from id {start}")


def unit_name(code: int) -> str:
    return BRIGADE_CONFIGS[code]['name']


def main_across(args):
    units_ts = (ROOT / 'website' / 'app' / 'data' / 'units.ts').read_text(encoding='utf-8')
    units = {code: json.loads((ROOT / 'website' / 'public' / cfg['json_file']).read_text(encoding='utf-8'))
             for code, cfg in sorted(BRIGADE_CONFIGS.items()) if f"'/{cfg['json_file']}'" in units_ts}
    found = across_units(units)
    grades = defaultdict(int)
    for p in found:
        grades[p['grade']] += 1
        k, m = p['keep'], p['merge']
        ev = ', '.join([f"+{x}" for x in p['agree']] + [f"-{x}" for x in p['clash']]) or 'names only'
        print(f"{p['grade']:6s} {k['soldier_id']} {k['full_name']} ({k.get('birth_year') or '?'}, {unit_name(k['_unit'])})"
              f"  ~  {m['soldier_id']} {m['full_name']} ({m.get('birth_year') or '?'}, {unit_name(m['_unit'])})"
              f"  [{ev}{'; ' + p['note'] if p.get('note') else ''}]")
    print(f"\nAcross units: {len(found)} matches {dict(grades)}")
    chosen = [p for p in found if args.write and p['grade'] in set(args.write.split(','))]
    if args.only:
        ids = {tuple(ln.split()[:2]) for ln in Path(args.only).read_text(encoding='utf-8').splitlines() if ln.strip()}
        chosen += [p for p in found if (p['keep']['soldier_id'], p['merge']['soldier_id']) in ids and p not in chosen]
    if chosen:
        new = [{'id': 0, 'action': 'link', 'soldier_id': p['keep']['soldier_id'], 'link_id': p['merge']['soldier_id'],
                'link_name': p['merge']['full_name'],
                'reason': f"Same soldier in {unit_name(p['keep']['_unit'])} and {unit_name(p['merge']['_unit'])}"
                          + (f"; same {', '.join(p['agree'])}" if p['agree'] else '') + (f'. {args.reason}' if args.reason else '')}
               for p in chosen]
        start, n = append(new)
        print(f"Appended {n} link corrections from id {start}")


if __name__ == '__main__':
    main()
