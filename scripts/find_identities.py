"""
Find the soldiers the site shows more than once, take the pairs the matchers' rules are sure of, and put the
doubtful ones before a person, once.

A pair is one of three kinds:
    merge       two records of one unit (two of its books, or two lists of one book): one record
                (find_source_duplicates.matches; its 'sure' are taken)
    link        records of one man in two units: both stay, each shows the other's entries
                (find_source_duplicates.across_units; its 'sure' are taken)
    reference   an entry of a book across units and a unit's record
                (rematch_references.rematch: each book's own rule)
Every pair the rules take on their own is taken ('auto'); the plausible rest go to the review queue, most likely
first. The answers (here with --answer, or in the viewer, scripts/review_identities.py) are kept in
identity_decisions.json, so no pair is offered twice:
    same        the pair becomes its correction on the next --write
    different   the pair is never taken nor offered again; a link or reference already made is taken off
                (a merge already made is listed, to be undone by hand: its record is gone from the unit's file)
    unsure      left out of the queue to decide; listed in the viewer's own tab ('Not sure'), with who was unsure
                and why, until someone else answers it; offered again with the rest with --unsure
Each answer keeps both names: if a re-parse moves the ids, an answer whose names no longer fit is ignored (and listed).
The queue (data-extraction/.cache/identities/queue.json) also holds a sample of the pairs already made ('check'), for
spot checks; a 'different' there takes the pair off as above.

identity_decisions.json was seeded with the pairs that corrections.json once held and that were removed by hand
(by: "history"): a link, merge or reference a session took off is the answer 'different' that had nowhere to be kept.

Usage:
    python scripts/find_identities.py                      # dry run: what would be taken; writes the queue
    python scripts/find_identities.py --write              # append the corrections, take off the 'different' ones
    python scripts/find_identities.py --write --start N    # ... from correction id N (default: after the highest
                                                           # below 200000, this project's sessions' own range)
    python scripts/find_identities.py --answer KEY same|different|unsure [--note TEXT] [--by NAME]
Then run the pipeline: apply_corrections.py --apply, and rebuild Ostali borci (see CLAUDE.md) when references changed.
"""
from __future__ import annotations

import argparse
import datetime
import json
import os
import random
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8', errors='replace')
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / 'scripts'))
import find_source_duplicates as F  # noqa: E402
import match_references as M  # noqa: E402
import rematch_references as R  # noqa: E402
from name_utils import BRIGADE_CONFIGS, OSTALI_CODES  # noqa: E402

DECISIONS = ROOT / 'identity_decisions.json'
CACHE = ROOT / 'data-extraction' / '.cache' / 'identities'
QUEUE = CACHE / 'queue.json'
ANSWERS = ('same', 'different', 'unsure')
CHECK_SAMPLE = 60                   # pairs already made, offered for spot checks each run
WEIGHT = {'father': 3, 'birthplace': 3, 'death place': 3, 'death day': 3, 'unit': 2, 'hero on the site': 2, 'duty': 2,
          'birth year': 1, 'death year': 1, 'father initial': 1}

# A unit's lists of its staffs and commands (the id's unit code and list number): their entries give a name and a post,
# its rolls often a name and little more, so a pair of them is mostly 'name' (the only one of the name in each list,
# nothing more to go on). Such a pair is taken when the two put him in the same battalion (in a division: the same
# brigade); else it goes to review.
STAFF_LISTS = {
    '000303', '000701', '001302', '002001', '003520', '003603', '003604', '004003', '004502', '005001', '005201',
    '005302', '005801', '006001', '006101', '006201', '006301', '006401', '006501', '006701', '007101', '007301',
    '007901', '008101', '008301', '009401', '009701', '009901', '010001', '010301', '010402', '012901', '014802',
    '016701', '016801',
}
ROMAN = {'i': 1, 'ii': 2, 'iii': 3, 'iv': 4, 'v': 5, 'vi': 6, 'vii': 7, 'viii': 8, 'ix': 9, 'x': 10}
BATTALION = re.compile(r'\b(\d{1,2}|[ivx]{1,4})\.?\s*(?:bataljon\w*|bat\.)', re.I)
QUOTED = re.compile(r'[»„“"]([^«“”"]{3,60})[«“”"]')
NOT_A_NAME = {'brigada', 'brigade', 'brigadi', 'udarna', 'udarne', 'udarni', 'bataljon', 'bataljona', 'divizija',
              'divizije', 'stab', 'staba', 'proleterska', 'proleterske', 'narodnooslobodilacka', 'partizanski',
              'partizanskog', 'odred', 'odreda', 'zastitna', 'cete', 'komanda', 'prateca', 'pratece'}


def is_staff(s: dict) -> bool:
    return s['soldier_id'][:6] in STAFF_LISTS


def sub_units(s: dict) -> tuple[set[int], set[str]]:
    """The battalions a record puts him in ("4. bataljon", "3. č. 2. bat.", "II bataljon") and the words of the
    brigades it names (from its unit and the names in quotes: »Braća Radić«, „Franjo Ogulinac Seljo“)."""
    texts = [s.get('unit_detail') or '', s.get('additional_info') or '']
    texts += [t for o in s.get('other_sources', ()) if not o.get('ref_book') and not o.get('unit_file')
              for t in (o.get('unit_detail') or '', o.get('additional_info') or '')]
    battalions = set()
    for t in texts:
        for m in BATTALION.finditer(t):
            n = m.group(1).lower()
            battalions.add(int(n) if n.isdigit() else ROMAN.get(n, 0))
    names = [s.get('unit_detail') or ''] + [q for t in texts for q in QUOTED.findall(t)]
    words = {F.fold(w) for n in names for w in re.findall(r'\w{5,}', n)} - NOT_A_NAME
    if re.search(r'štab\w*\s+(?:\d+\.\s*)?divizij', s.get('unit_detail') or '', re.I):
        words.add('the division staff')
    return battalions - {0}, words


def plain_fighter(s: dict) -> bool:
    """The roll calls him a borac (as the 11. dalmatinska's "borac 3. č. 2. bat." does): against a post in a staff list
    that is another man as often as his rise, so the pair goes to review."""
    return F.fold(s.get('rank') or '') == 'borac' or bool(re.match(r'\W*bor[ae]c\b', s.get('additional_info') or '', re.I))


def same_sub_unit(a: dict, b: dict, division: bool) -> bool:
    """A staff entry and a roll entry in the same battalion (a division's: in the same brigade), the roll not calling
    him a plain fighter."""
    roll = b if is_staff(a) else a
    if plain_fighter(roll):
        return False
    (ba, wa), (bb, wb) = sub_units(a), sub_units(b)
    if division:
        return bool(wa & wb)
    return bool(ba & bb)


# ---------------------------------------------------------------- the answers

def key(kind: str, a: str, b: str, book: str = '') -> str:
    """merge:keep:merged, link:lower:higher, reference:book:record:entry"""
    if kind == 'link':
        a, b = sorted((a, b))
    return f'reference:{book}:{a}:{b}' if kind == 'reference' else f'{kind}:{a}:{b}'


def parse_key(k: str) -> tuple[str, str, str, str]:
    parts = k.split(':')
    return (parts[0], parts[2], parts[3], parts[1]) if parts[0] == 'reference' else (parts[0], parts[1], parts[2], '')


def load_decisions() -> dict[str, dict]:
    if not DECISIONS.exists():
        return {}
    return {d['key']: d for d in json.loads(DECISIONS.read_text(encoding='utf-8'))}


def save_answer(k: str, answer: str, a_name: str, b_name: str, by: str, note: str = '') -> dict:
    """Keep one answer (the last given for a pair wins). The file is re-read right before writing: the viewer and
    this script may both write."""
    if answer not in ANSWERS and answer != 'clear':
        raise ValueError(answer)
    kind, a, b, book = parse_key(k)
    decisions = load_decisions()
    if answer == 'clear':
        decisions.pop(k, None)
        d = {'key': k, 'answer': None}
    else:
        d = {'key': k, 'kind': kind, 'a': a, 'b': b, **({'book': book} if book else {}), 'a_name': a_name,
             'b_name': b_name, 'answer': answer, 'by': by, 'date': datetime.date.today().isoformat(),
             **({'note': note} if note else {})}
        decisions[k] = d
    tmp = DECISIONS.with_suffix('.json.tmp')
    tmp.write_text(json.dumps(sorted(decisions.values(), key=lambda x: x['key']), ensure_ascii=False, indent=1),
                   encoding='utf-8')
    os.replace(tmp, DECISIONS)
    return d


# ---------------------------------------------------------------- what the viewer shows of each side

def sources_titles() -> tuple[dict, dict]:
    """sources.ts: the book's title by its PDF and by its id."""
    text = (ROOT / 'website' / 'app' / 'data' / 'sources.ts').read_text(encoding='utf-8')
    by_pdf, by_id = {}, {}
    for block in re.split(r'\n\s*\{\s*\n', text):
        i = re.search(r"\bid:\s*'([^']+)'", block)
        t = re.search(r"\btitle:\s*(['\"`])(.+?)\1,?\s*\n", block)
        p = re.search(r"\bpdfPath:\s*'([^']+)'", block)
        if i and t:
            by_id[i.group(1)] = t.group(2)
            if p:
                by_pdf[p.group(1).rsplit('/', 1)[-1]] = t.group(2)
    return by_pdf, by_id


TITLES_PDF, TITLES_ID = {}, {}


def where(s: dict) -> dict | None:
    """The entry's place on a page of a PDF on the site: file, page, its box (viewer coordinates), the lines' boxes."""
    if not s.get('pdf_file') or not s.get('pdf_page'):
        return None
    x0 = s.get('pdf_x_left', s.get('pdf_x')) or 0
    y0 = s.get('pdf_y') or 0
    return {'file': s['pdf_file'], 'page': s['pdf_page'],
            'box': [round(x0, 1), round(y0, 1), round(s.get('pdf_x_end') or x0 + 260, 1), round(s.get('pdf_y_end') or y0 + 12, 1)],
            **({'rects': s['pdf_rects']} if s.get('pdf_rects') else {}),
            'title': TITLES_PDF.get(s['pdf_file'], s['pdf_file'])}


def facts(s: dict) -> dict:
    when = s.get('death_date') or s.get('death_year') or ''
    iso = re.fullmatch(r'(\d{4})-(\d\d)-(\d\d)', when)
    if iso:                                                         # the books' entries: 1944-12-26 as 26. 12. 1944
        when = f'{int(iso.group(3))}. {int(iso.group(2))}. {iso.group(1)}'
    out = {'father': s.get('fathers_name') or s.get('middle_name') or '', 'born': s.get('birth_year') or '',
           'birthplace': s.get('birth_place') or s.get('born_in') or '',
           'death': ' '.join(x for x in (s.get('death_type') or '', when) if x),
           'death place': s.get('death_place') or '', 'rank': s.get('rank') or '', 'in unit': s.get('unit_detail') or s.get('unit') or ''}
    return {k: v for k, v in out.items() if v}


def record_side(s: dict) -> dict:
    code = int(s['soldier_id'][:4])
    more = []
    for o in s.get('other_sources', ()):
        title = (TITLES_ID.get(o['ref_book'], o['ref_book']) if o.get('ref_book') else
                 BRIGADE_CONFIGS.get(int(o['soldier_id'][:4]), {}).get('name', '') + ' (link)' if o.get('unit_file') else
                 TITLES_PDF.get(o.get('pdf_file'), o.get('pdf_file') or ''))
        more.append({'id': o.get('soldier_id'), 'name': o.get('name'), 'info': o.get('additional_info') or '',
                     'title': title, 'pdf': where(o), 'url': o.get('source_url')})
    return {'id': s['soldier_id'], 'unit': BRIGADE_CONFIGS[code]['name'], 'name': s.get('full_name') or '',
            'info': s.get('additional_info') or '', 'facts': facts(s), 'pdf': where(s), 'url': s.get('source_url'),
            'more': more}


def entry_side(e: dict, book: str) -> dict:
    title = e.get('book_title') or TITLES_ID.get(book) or TITLES_PDF.get(e.get('pdf_file'), book)
    page = f", p. {e['source_page']}" if e.get('source_page') else ''
    return {'id': e['soldier_id'], 'unit': f'{title}{page}', 'name': e.get('name') or '', 'info': e.get('additional_info') or '',
            'facts': facts(e), 'pdf': where(e), 'url': e.get('source_url'), 'more': []}


def merged_side(o: dict) -> dict:
    """A merged record's entry, as its keeper holds it."""
    return {'id': o.get('soldier_id'), 'unit': TITLES_PDF.get(o.get('pdf_file'), o.get('pdf_file') or ''),
            'name': o.get('name') or '', 'info': o.get('additional_info') or '', 'facts': {}, 'pdf': where(o),
            'url': o.get('source_url'), 'more': []}


def score(agree, clash) -> int:
    return sum(WEIGHT.get(a, 1) for a in agree) - 3 * len(clash)


def unsure_items(units, decisions) -> list[dict]:
    """The pairs answered 'unsure', for a person to look at again (the viewer's 'Not sure' tab): who was unsure and
    why in the note. An answer whose record is gone (merged away) or holds another name now (a re-parse) is left out."""
    recs = {s['soldier_id']: s for soldiers in units.values() for s in soldiers}
    entries, out = {}, []
    for k, d in decisions.items():
        if d['answer'] != 'unsure':
            continue
        a = recs.get(d['a'])
        if not a or (d.get('a_name') and M.fold(a.get('full_name')) != M.fold(d['a_name'])):
            continue
        if d['kind'] == 'reference':
            book = d.get('book') or ''
            if book not in entries:
                path = M.entries_path(book)
                entries[book] = ({e['soldier_id']: e for e in json.loads(path.read_text(encoding='utf-8'))}
                                 if path.exists() else {})
            e = entries[book].get(d['b'])
            if not e:
                continue
            b_side = entry_side(e, book)
        else:
            b = recs.get(d['b'])
            if not b or (d.get('b_name') and M.fold(b.get('full_name')) != M.fold(d['b_name'])):
                continue
            b_side = record_side(b)
        note = f"{d.get('by') or 'someone'} was not sure" + (f": {d['note']}" if d.get('note') else '')
        out.append({'key': k, 'kind': d['kind'], 'a': record_side(a), 'b': b_side, 'grade': 'not sure', 'agree': [],
                    'clash': [], 'note': note, 'score': 0, 'by': d.get('by') or ''})
    out.sort(key=lambda x: (x['kind'] != 'merge', x['kind'] != 'link', x['key']))
    return out


# ---------------------------------------------------------------- finding the pairs

def units_on_site() -> dict[int, list[dict]]:
    """The units' records as their own books give them (record_sources.own_only: not what they borrowed)"""
    from record_sources import own_only
    units_ts = (ROOT / 'website' / 'app' / 'data' / 'units.ts').read_text(encoding='utf-8')
    return {code: [own_only(s) for s in json.loads((ROOT / 'website' / 'public' / cfg['json_file']).read_text(encoding='utf-8'))]
            for code, cfg in sorted(BRIGADE_CONFIGS.items())
            if f"'/{cfg['json_file']}'" in units_ts and code not in OSTALI_CODES}


def components(links: list[tuple[str, str]]) -> dict[str, str]:
    """Records joined by links, each to its group's first id (a pair inside a group is linked already)."""
    parent = {}

    def find(x):
        parent.setdefault(x, x)
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x
    for a, b in links:
        ra, rb = find(a), find(b)
        if ra != rb:
            parent[max(ra, rb)] = min(ra, rb)
    return {x: find(x) for x in parent}


def list_order(s: dict, rank: dict) -> tuple:
    """Which of a unit's records keeps its id when entries merge: the one of the list the unit names first."""
    if s.get('pdf_file'):
        r = rank.get(s['pdf_file'], 99)
    else:
        # a web page that is the unit's first list (1. dalmatinska, Mačvanski odred) keeps its records; a later
        # one (3. krajiška's roll of 1942) gives way to the scanned books, so their records keep their ids
        r = 200 if 'biblioteka.poreklo.rs' in (s.get('source_url') or '') else \
            (-1 if s.get('source_url') and s['soldier_id'][4:6] == '00' else 99)
    return r, F.list_index(s), s['soldier_id']


def merged_lists(s: dict) -> set[str]:
    """The lists a record's entries come from: its own and those of the entries merged into it."""
    return {F.list_of(s)} | {F.list_of(o) for o in s.get('other_sources', ()) if not o.get('ref_book') and not o.get('unit_file')}


def merge_groups(sure: list[dict], rank: dict, refs_of: dict, portraits: set):
    """A unit's sure pairs, joined into groups (a man in three lists is two pairs; one record may be the sure match of
    records in two other lists). A group is taken, every other record merged into the one of the list the unit names
    first, when its records come from different lists (their merged entries too: a record that holds an entry of the
    other's list already is a man printed twice, or a merge gone wrong), no two of them disagree on anything, no two
    hold different entries of one book across units, and no two have a portrait. Else its pairs go to review.
    Returns ([(keep, gone, why, agree)], [(pair, note)])."""
    by_id = {}
    for p in sure:
        by_id[p['keep']['soldier_id']] = p['keep']
        by_id[p['merge']['soldier_id']] = p['merge']
    group_of = components([(p['keep']['soldier_id'], p['merge']['soldier_id']) for p in sure])
    groups = defaultdict(list)
    for p in sure:
        groups[group_of[p['keep']['soldier_id']]].append(p)

    def order(s):
        return list_order(s, rank)
    taken, tangled = [], []
    for pairs in groups.values():
        members = sorted({x for p in pairs for x in (p['keep']['soldier_id'], p['merge']['soldier_id'])},
                         key=lambda i: order(by_id[i]))
        recs = [by_id[i] for i in members]
        trouble = ''
        lists = [merged_lists(s) for s in recs]
        if any(lists[i] & lists[j] for i in range(len(recs)) for j in range(i + 1, len(recs))):
            trouble = 'one of them holds an entry of the other’s list already'
        elif any(F.evidence(recs[i], recs[j])[1] for i in range(len(recs)) for j in range(i + 1, len(recs))):
            trouble = 'three or more records, and two of them disagree'
        elif any(set(refs_of[x]) & set(refs_of[y]) and any(refs_of[x][b] != refs_of[y].get(b, refs_of[x][b]) for b in refs_of[x])
                 for i, x in enumerate(members) for y in members[i + 1:]):
            trouble = 'they hold different entries of one book across units'
        elif sum(x in portraits for x in members) > 1:
            trouble = 'each has a portrait'
        if trouble:
            tangled += [(p, trouble) for p in pairs]
            continue
        keep = recs[0]
        direct = {(p['keep']['soldier_id'], p['merge']['soldier_id']): p for p in pairs}
        direct.update({(b, a): p for (a, b), p in list(direct.items())})
        for gone in recs[1:]:
            p = direct.get((keep['soldier_id'], gone['soldier_id']))
            agree = p['agree'] if p else F.evidence(keep, gone)[0]
            why = f"Same soldier in {F.list_of(keep)} and {F.list_of(gone)}" + ('' if p else ' (through another of its lists)')
            taken.append((keep, gone, why, agree))
    return taken, tangled


def find_pairs(units, corr, decisions, log=print):
    """auto: [(kind, a, b, book, why, agree)]; review: queue items; stale: answers whose names no longer fit."""
    recs = {s['soldier_id']: s for soldiers in units.values() for s in soldiers}
    answered = {k: d for k, d in decisions.items()}
    blocked = {k for k, d in answered.items() if d['answer'] in ('different', 'unsure')}
    auto, review = [], []

    def offer(kind, a_side, b_side, k, grade, agree, clash, note):
        review.append({'key': k, 'kind': kind, 'a': a_side, 'b': b_side, 'grade': grade, 'agree': list(agree),
                       'clash': list(clash), 'note': note or '', 'score': score(agree, clash)})

    # merges, unit by unit
    merges = Counter()
    refs_of = defaultdict(dict)                         # record -> {book: entry}: the references it holds
    for c in corr:
        if c['action'] == 'reference':
            refs_of[c['soldier_id']][c['ref_book']] = c['ref_id']
    portraits = set(json.loads((ROOT / 'website' / 'app' / 'data' / 'portrait-index.json').read_text(encoding='utf-8')))
    for code, soldiers in units.items():
        rank = F.list_rank(code)
        division = 'divizij' in BRIGADE_CONFIGS[code]['name'].lower()
        sure = []
        for p in F.matches(soldiers, rank):
            a, b = p['keep']['soldier_id'], p['merge']['soldier_id']
            k = key('merge', a, b)
            if k in answered:
                continue
            if p['grade'] == 'sure':
                sure.append(p)
            elif p['grade'] == 'name' and is_staff(p['keep']) != is_staff(p['merge']):
                if same_sub_unit(p['keep'], p['merge'], division):
                    p['agree'] = ['unit']
                    sure.append(p)
                    merges['staff by unit'] += 1
                else:
                    offer('merge', record_side(p['keep']), record_side(p['merge']), k, 'name', [], [],
                          'a staff list and a roll: the only one of the name in each, nothing more to go on')
                    merges['review'] += 1
                    merges['staff, name only'] += 1
            elif p['agree'] and (len(p['agree']) >= 2 or not p['clash']) and score(p['agree'], p['clash']) >= 2:
                offer('merge', record_side(p['keep']), record_side(p['merge']), k, p['grade'], p['agree'], p['clash'],
                      p.get('note') or ('the books name different fathers' if 'father' in p['clash'] else ''))
                merges['review'] += 1
        taken, tangled = merge_groups(sure, rank, refs_of, portraits)
        for keep, gone, why, agree in taken:
            auto.append(('merge', keep['soldier_id'], gone['soldier_id'], '', why, agree, gone.get('full_name')))
        for p, note in tangled:
            offer('merge', record_side(p['keep']), record_side(p['merge']), key('merge', p['keep']['soldier_id'],
                  p['merge']['soldier_id']), p['grade'], p['agree'], p['clash'], note)
        merges['auto'] += len(taken)
        merges['review'] += len(tangled)
    log(f'merges: {dict(merges)}')

    # links across units
    linked = components([(c['soldier_id'], c['link_id']) for c in corr if c['action'] == 'link'])
    links = Counter()
    for p in F.across_units(units):
        a, b = p['keep']['soldier_id'], p['merge']['soldier_id']
        k = key('link', a, b)
        if k in answered or (a in linked and linked.get(a) == linked.get(b)):
            continue
        if p['grade'] == 'sure':
            auto.append(('link', a, b, '', f"Same soldier in {F.unit_name(p['keep']['_unit'])} and "
                                           f"{F.unit_name(p['merge']['_unit'])}", p['agree'], p['merge'].get('full_name')))
            links['auto'] += 1
        elif len(p['agree']) >= 2 and len(p['clash']) <= 1 and score(p['agree'], p['clash']) >= 3:
            offer('link', record_side(p['keep']), record_side(p['merge']), k, p['grade'], p['agree'], p['clash'],
                  p.get('note', ''))
            links['review'] += 1
    log(f'links: {dict(links)}')

    # references, book by book
    index = defaultdict(list)
    for s in recs.values():
        index[(M.fold(s.get('last_name')), M.fold(s.get('first_name')))].append(s)
    ref_blocked = {(d.get('book'), d['a'], d['b']) for k, d in answered.items() if d['kind'] == 'reference'}
    CACHE.mkdir(parents=True, exist_ok=True)
    new, _, rev = R.rematch(index, recs, corr, CACHE, blocked=ref_blocked, log=lambda *_: None)
    entries = {}

    def entry(book, ref):
        if book not in entries:
            entries[book] = {e['soldier_id']: e for e in json.loads(M.entries_path(book).read_text(encoding='utf-8'))}
        return entries[book][ref]
    for p in new:
        auto.append(('reference', p['record'], p['ref'], p['book'],
                     f"{p['record_name']} is the {p['ref_name']} of the book"
                     + (f"; same {', '.join(p['agree'])}" if p['agree'] else '')
                     + (f"; {p['why']}" if p['why'] else ''), p['agree'], p['ref_name']))
    for f in rev:
        k = key('reference', f['record'], f['ref'], f['book'])
        if k in answered:
            continue
        offer('reference', record_side(recs[f['record']]), entry_side(entry(f['book'], f['ref']), f['book']), k,
              f.get('grade', ''), f.get('agree', []), f.get('clash', []), f.get('note', ''))
    log(f"references: {{'auto': {len(new)}, 'review': {len(rev)}}}")

    # an answer 'same' not made yet is taken; one whose names don't fit the records any more is stale
    stale = []
    made = made_keys(corr)
    into = {c['merge_id']: c['soldier_id'] for c in corr if c['action'] == 'merge'}

    def home(i):
        """The record that holds an entry now: its own, or the one it was merged into (merges of merges followed)."""
        seen = set()
        while i not in recs and i in into and i not in seen:
            seen.add(i)
            i = into[i]
        return i
    for k, d in answered.items():
        if d['answer'] != 'same' or k in made or (d['kind'] == 'merge' and home(d['a']) == home(d['b'])):
            continue
        a_now = recs.get(d['a'], {}).get('full_name')
        if d['kind'] == 'reference':
            b_now = (entry(d['book'], d['b']) if M.entries_path(d['book']).exists() else {}).get('name')
        elif d['kind'] == 'merge':
            b_now = recs.get(d['b'], {}).get('full_name')
        else:
            b_now = recs.get(d['b'], {}).get('full_name')
        if a_now != d['a_name'] or b_now != d['b_name']:
            stale.append(d)
            continue
        auto.append((d['kind'], d['a'], d['b'], d.get('book', ''), f"answered 'same' by {d['by']} ({d['date']})"
                     + (f": {d['note']}" if d.get('note') else ''), [], d['b_name']))
    return group_merges(auto, recs), review, stale


def group_merges(auto: list[tuple], recs: dict) -> list[tuple]:
    """Merges that share a record are one man in several entries: answers 'same' on two pairs of a man printed in three
    lists (Živković Ivana Jere: the roster, Borci Sutjeske, Dalmatinci), or twice in one list and twice in another
    (Rašeta Milana Nikola). The whole group goes into one record, the one of the list the unit names first; else the
    second merge of a record already merged finds nothing."""
    merges = [x for x in auto if x[0] == 'merge' and x[1] in recs and x[2] in recs]
    group_of = components([(x[1], x[2]) for x in merges])
    groups = defaultdict(list)
    for x in merges:
        groups[group_of[x[1]]].append(x)
    out = [x for x in auto if not (x[0] == 'merge' and x[1] in recs and x[2] in recs)]
    for xs in groups.values():
        keepers, gone = {x[1] for x in xs}, [x[2] for x in xs]
        if len(keepers) == 1 and len(set(gone)) == len(gone) and not keepers & set(gone):
            out += xs                                                   # one record and the entries merged into it
            continue
        ids = {i for x in xs for i in (x[1], x[2])}
        rank = F.list_rank(int(next(iter(ids))[:4]))
        members = sorted((recs[i] for i in ids), key=lambda s: list_order(s, rank))
        why = '; '.join(sorted({x[4] for x in xs}))
        out += [('merge', members[0]['soldier_id'], s['soldier_id'], '', why + f' (one man in {len(members)} entries)',
                 sorted({a for x in xs for a in x[5]}), s.get('full_name')) for s in members[1:]]
    return out


def made_keys(corr) -> dict[str, dict]:
    out = {}
    for c in corr:
        if c['action'] == 'merge':
            out[key('merge', c['soldier_id'], c['merge_id'])] = c
        elif c['action'] == 'link':
            out[key('link', c['soldier_id'], c['link_id'])] = c
        elif c['action'] == 'reference':
            out[key('reference', c['soldier_id'], c['ref_id'], c['ref_book'])] = c
    return out


def spot_checks(units, corr, decisions, n=CHECK_SAMPLE) -> list[dict]:
    """A sample of the pairs already made, for the viewer's 'check' tab: half of it from what this script took last,
    the rest from all the others."""
    recs = {s['soldier_id']: s for soldiers in units.values() for s in soldiers}
    rng = random.Random(datetime.date.today().isoformat())
    made = [(k, c) for k, c in made_keys(corr).items() if k not in decisions and c['soldier_id'] in recs]
    stamps = sorted({m.group(0) for _, c in made for m in [re.search(r'found by find_identities\.py, [\d-]+', c.get('reason', ''))] if m})
    last = [x for x in made if stamps and stamps[-1] in x[1].get('reason', '')]
    books = {}
    out, seen = [], set()
    for pool, quota in ((rng.sample(last, min(len(last), n)), n // 2), (rng.sample(made, min(len(made), n * 3)), n)):
        for k, c in pool:
            if len(out) >= quota:
                break
            if k in seen:
                continue
            seen.add(k)
            a = recs[c['soldier_id']]
            if c['action'] == 'merge':
                o = next((o for o in a.get('other_sources', ()) if o.get('soldier_id') == c['merge_id']), None)
                b = merged_side(o) if o else None
            elif c['action'] == 'link':
                b = record_side(recs[c['link_id']]) if c['link_id'] in recs else None
            else:
                if c['ref_book'] not in books:
                    path = M.entries_path(c['ref_book'])
                    books[c['ref_book']] = ({x['soldier_id']: x for x in json.loads(path.read_text(encoding='utf-8'))}
                                            if path.exists() else {})
                e = books[c['ref_book']].get(c['ref_id'])
                b = entry_side(e, c['ref_book']) if e else None
            if b:
                out.append({'key': k, 'kind': c['action'], 'a': record_side(a), 'b': b, 'grade': 'made', 'agree': [],
                            'clash': [], 'note': c.get('reason', ''), 'score': 0, 'made': c['id']})
    return out


# ---------------------------------------------------------------- writing

def next_id(corr, start=None) -> int:
    if start:
        return start
    return max(c['id'] for c in corr if c['id'] < 200000) + 1


def repoint(corr: list[dict], gone_to: dict[str, str], names: dict[str, str]) -> Counter:
    """Records merged away: what pointed at them points at the record they went into. A book's entry it held goes to
    the keeper (unless the keeper holds it too), its links too (link_name the keeper's name), and the entries merged
    into it earlier are merged into the keeper. Edits by its id stay: apply_corrections edits a merged entry's text."""
    done = Counter()
    refs = {(c['soldier_id'], c['ref_book'], c['ref_id']) for c in corr if c['action'] == 'reference'}
    books = {(c['soldier_id'], c['ref_book']) for c in corr if c['action'] == 'reference'}
    links = {frozenset((c['soldier_id'], c['link_id'])) for c in corr if c['action'] == 'link'}
    drop = set()
    for c in corr:
        if c['action'] == 'reference' and c['soldier_id'] in gone_to:
            keep = gone_to[c['soldier_id']]
            if (keep, c['ref_book'], c['ref_id']) in refs:
                drop.add(c['id'])
            elif (keep, c['ref_book']) in books:
                print(f"  reference {c['id']}: {keep} holds another entry of {c['ref_book']} already; "
                      f"{c['ref_id']} left on {c['soldier_id']}, merged away")
                done['reference left'] += 1
                continue
            else:
                books.add((keep, c['ref_book']))
                refs.add((keep, c['ref_book'], c['ref_id']))
                c['soldier_id'] = keep
            done['reference'] += 1
        elif c['action'] == 'link' and (c['soldier_id'] in gone_to or c['link_id'] in gone_to):
            a, b = gone_to.get(c['soldier_id'], c['soldier_id']), gone_to.get(c['link_id'], c['link_id'])
            if a == b or frozenset((a, b)) in links:
                drop.add(c['id'])
            else:
                links.add(frozenset((a, b)))
                c['soldier_id'], c['link_id'] = a, b
                if b in names:
                    c['link_name'] = names[b]
            done['link'] += 1
        elif c['action'] == 'merge' and c['soldier_id'] in gone_to:
            c['soldier_id'] = gone_to[c['soldier_id']]
            done['merge'] += 1
    corr[:] = [c for c in corr if c['id'] not in drop]
    return done


def strays(units, corr) -> dict[str, str]:
    """Links and references that point at a record merged away since they were made (a second book's merges written
    after them): its id -> the record it went into, following merges of merges. apply_corrections skips them, so the
    entry shows nowhere."""
    ids = {s['soldier_id'] for soldiers in units.values() for s in soldiers}
    into = {c['merge_id']: c['soldier_id'] for c in corr if c['action'] == 'merge'}
    out = {}
    for c in corr:
        for f in ('soldier_id', 'link_id'):
            # (and a merge into a record that a later merge took away: its entry came along, the keeper holds it)
            i = c.get(f) if c['action'] in ('link', 'reference', 'merge') else None
            if not i or i in ids or int(i[:4]) in OSTALI_CODES:
                continue
            k, seen = i, set()
            while k not in ids and k in into and k not in seen:
                seen.add(k)
                k = into[k]
            if k in ids:
                out[i] = k
    return out


def move_portraits(gone_to: dict[str, str]) -> int:
    """A portrait of a record merged away goes to the record it went into (merge_groups keeps groups with two out)."""
    path = ROOT / 'website' / 'app' / 'data' / 'portrait-index.json'
    index = json.loads(path.read_text(encoding='utf-8'))
    folder = ROOT / 'website' / 'public' / 'portreti'
    moved = 0
    for gone, keep in gone_to.items():
        if gone not in index or keep in index:
            continue
        e = index.pop(gone)
        for suffix in ('', '-v'):
            src = folder / f'{gone}{suffix}.jpg'
            if src.exists():
                os.replace(src, folder / f'{keep}{suffix}.jpg')
        for k in ('f', 'v'):
            if e.get(k):
                e[k] = e[k].replace(gone, keep)
        index[keep] = e
        moved += 1
    for e in index.values():
        if e.get('same') in gone_to:
            e['same'] = gone_to[e['same']]
    if moved:
        # as extract_book_portraits.py writes it: sorted, a key a line, no indent
        path.write_bytes(json.dumps(dict(sorted(index.items())), ensure_ascii=False, indent=0).encode('utf-8'))
        # (and the hand-checked pairings in extract_book_portraits.py, so a re-run finds the record)
        for ts in [ROOT / 'website' / 'app' / 'data' / n for n in ('wartimePortraits.ts', 'family.ts', 'portraits.ts')] + [
                ROOT / 'scripts' / 'extract_book_portraits.py']:
            text = ts.read_text(encoding='utf-8')
            new = re.sub(r'\b\d{10}\b', lambda m: gone_to.get(m.group(0), m.group(0)), text)
            if new != text:
                ts.write_text(new, encoding='utf-8')
    return moved


def write(auto, decisions, corr, units, start=None) -> None:
    made = made_keys(corr)
    names = {s['soldier_id']: s.get('full_name') or '' for soldiers in units.values() for s in soldiers}
    stamp = f'; found by find_identities.py, {datetime.date.today().isoformat()}'
    gone_to = {b: a for kind, a, b, *_ in auto if kind == 'merge' and key('merge', a, b) not in made}
    new, seen = [], set()
    for kind, a, b, book, why, agree, b_name in auto:
        if kind == 'link':                              # a record merged away in this run: its keeper
            a, b = gone_to.get(a, a), gone_to.get(b, b)
            b_name = names.get(b, b_name)
        k = key(kind, a, b, book)
        if k in made or k in seen or (kind == 'link' and a == b):
            continue
        seen.add(k)
        same = (f"; same {', '.join(agree)}" if agree else '') + ('' if why.startswith('answered') else stamp)
        if kind == 'merge':
            new.append({'action': 'merge', 'soldier_id': a, 'merge_id': b, 'merge_name': b_name, 'reason': why + same})
        elif kind == 'link':
            new.append({'action': 'link', 'soldier_id': a, 'link_id': b, 'link_name': b_name, 'reason': why + same})
        else:
            new.append({'action': 'reference', 'soldier_id': gone_to.get(a, a), 'ref_book': book, 'ref_id': b,
                        'ref_name': b_name, 'reason': why + ('' if why.startswith('answered') else stamp)})
    # 'different': a link or reference made by a script is taken off; a merge is listed
    drop, undo = set(), []
    for k, d in decisions.items():
        if d['answer'] == 'different' and k in made:
            c = made[k]
            if c['action'] == 'merge':
                undo.append(c)
            else:
                drop.add(c['id'])
    first = next_id(corr, start)
    taken = {c['id'] for c in corr}
    ids = [first + i for i in range(len(new))]
    if any(i in taken for i in ids):
        sys.exit(f'ids from {first} are taken: pass --start')
    out = [c for c in corr if c['id'] not in drop]
    moved = repoint(out, {**strays(units, out), **gone_to}, names)
    out += [{'id': i, **c} for i, c in zip(ids, new)]
    tmp = M.CORRECTIONS.with_suffix('.json.tmp')
    tmp.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding='utf-8')
    os.replace(tmp, M.CORRECTIONS)
    print(f"appended {len(new)} corrections {dict(Counter(c['action'] for c in new))}"
          + (f' ({ids[0]}-{ids[-1]})' if ids else '') + f', took off {len(drop)}; pointed at the keeper: {dict(moved)}; '
          f'portraits moved: {move_portraits(gone_to)}')
    for c in undo:
        print(f"  merge {c['id']} ({c['soldier_id']} <- {c['merge_id']} {c['merge_name']}) answered 'different': undo by hand")


def names_of(k: str) -> tuple[str, str]:
    """The names a pair's records (or the book's entry) hold now: for an answer to a pair that is not in the queue
    (one made already, or one found by reading)."""
    kind, a, b, book = parse_key(k)

    def record(i):
        cfg = BRIGADE_CONFIGS.get(int(i[:4]))
        path = ROOT / 'website' / 'public' / cfg['json_file'] if cfg else None
        if not path or not path.exists():
            return ''
        hit = next((s for s in json.loads(path.read_text(encoding='utf-8')) if s['soldier_id'] == i), None)
        return hit.get('full_name') or '' if hit else ''
    if kind == 'reference':
        path = M.entries_path(book)
        e = next((x for x in json.loads(path.read_text(encoding='utf-8')) if x['soldier_id'] == b), None) if path.exists() else None
        return record(a), (e or {}).get('name', '')
    return record(a), record(b)


def main():
    global TITLES_PDF, TITLES_ID
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--write', action='store_true', help='append the corrections and take off the pairs answered different')
    ap.add_argument('--start', type=int, help='the first correction id to give')
    ap.add_argument('--unsure', action='store_true', help="offer the pairs answered 'unsure' again")
    ap.add_argument('--answer', nargs=2, metavar=('KEY', 'ANSWER'), help='keep an answer: same, different, unsure, clear')
    ap.add_argument('--note', default='')
    ap.add_argument('--by', default='claude')
    args = ap.parse_args()
    if args.answer:
        k, answer = args.answer
        queue = json.loads(QUEUE.read_text(encoding='utf-8')) if QUEUE.exists() else {}
        item = next((x for x in queue.get('review', []) + queue.get('check', []) if x['key'] == k), None)
        names = (item['a']['name'], item['b']['name']) if item else names_of(k)
        if not all(names) and answer != 'clear':
            sys.exit(f'{k}: no such records (or entry)')
        print(json.dumps(save_answer(k, answer, *names, args.by, args.note), ensure_ascii=False))
        return

    TITLES_PDF, TITLES_ID = sources_titles()
    decisions = load_decisions()
    if args.unsure:
        decisions = {k: d for k, d in decisions.items() if d['answer'] != 'unsure'}
    units = units_on_site()
    corr = json.loads(M.CORRECTIONS.read_text(encoding='utf-8'))
    auto, review, stale = find_pairs(units, corr, decisions)
    review.sort(key=lambda x: (-x['score'], x['kind'], x['key']))
    checks = spot_checks(units, corr, decisions)
    unsure = [] if args.unsure else unsure_items(units, decisions)
    CACHE.mkdir(parents=True, exist_ok=True)
    QUEUE.write_text(json.dumps({'made': datetime.datetime.now().isoformat(timespec='seconds'), 'review': review,
                                 'check': checks, 'unsure': unsure}, ensure_ascii=False), encoding='utf-8')
    kinds = Counter(x[0] for x in auto)
    print(f'links and references at records merged away since (pointed at their keeper on --write): '
          f'{len(strays(units, corr))}')
    print(f"auto: {dict(kinds)}; review: {dict(Counter(x['kind'] for x in review))}; checks: {len(checks)}; "
          f"answers: {dict(Counter(d['answer'] for d in load_decisions().values()))}")
    for d in stale:
        print(f"  stale answer {d['key']} ({d['a_name']} / {d['b_name']}): the ids hold other names now")
    # two records answered 'different' that links join through a third (Šarić Jure: each linked to the Mosor odred's)
    linked = components([(c['soldier_id'], c['link_id']) for c in corr if c['action'] == 'link'])
    for k, d in decisions.items():
        if d['answer'] == 'different' and d['kind'] == 'link' and d['a'] in linked and linked.get(d['a']) == linked.get(d['b']):
            print(f"  {k} ({d['a_name']} / {d['b_name']}) answered 'different', but links join them through another record")
    (CACHE / 'auto.json').write_text(json.dumps(auto, ensure_ascii=False, indent=1), encoding='utf-8')
    if args.write:
        write(auto, load_decisions(), corr, units, args.start)


if __name__ == '__main__':
    main()
