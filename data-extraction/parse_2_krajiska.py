"""
Parser: 2. Krajiška NOU udarna brigada (brigade code 24).

Source: Milorad Gončin — "DRUGA KRAJIŠKA NARODNOOSLOBODILAČKA UDARNA BRIGADA", chapter "Spisak poginulih i
        umrlih boraca i rukovodilaca u toku NOR-a" (book pp. 409-477)
        znaci.org/00001/133_15.pdf  →  website/public/pdfs/2-krajiska.pdf
Single column, Latin. p. 1 the chapter title, p. 2 the introduction (1,565 fallen and died), pp. 3-65 the list,
pp. 66-70 the book's table of contents and imprint.
    ADAMOVIĆ Pere JANKO, rođen 1922., u Volaru, Prijedor, Srbin, zemljoradnik, u NOB od 1941., ...
    ADAMOVIĆ Marka MITAR- MIĆO, rođen 1916., ...                          (a nickname after a dash)
Continuation lines are indented ~26pt (_margin_entries). The scan crops the left edge of every even page, so
their surnames lose one or two first letters, sometimes replaced by specks ("NTONIĆ", "iLIĆIĆ", ")KIC");
restore_cropped rebuilds them from the alphabetical order and the surnames the corpus knows.
Pages 58-59 repeat 56-57 (another scan) and are skipped.
"""
import json
import re
from collections import Counter, defaultdict
from pathlib import Path

from _margin_entries import MarginEntries, lone_names_to_given, split_leading_aliases
from _parser_scaffold import repair_lj_ocr, restore_diacritics, run_parser

U = 'A-ZČĆŽŠĐ'
me = MarginEntries()
RESCANNED = {58, 59}         # pp. 58-59 are a second scan of pp. 56-57


def _other_units() -> tuple[Counter, Counter]:
    last, first = Counter(), Counter()
    for f in Path('website/public').glob('*soldiers.json'):
        if f.name != '2-krajiska-soldiers.json':        # not this book's own earlier output
            for s in json.loads(f.read_text(encoding='utf-8')):
                last[s['last_name']] += 1
                first[s['first_name']] += 1
                first[s.get('middle_name') or ''] += 1
    return last, first


LAST, FIRST = _other_units()


def keep_line(ln: dict) -> bool:
    t = ln['text'].strip()
    if re.fullmatch(r'[\W\d]{1,6}', t) or ln['page'] in RESCANNED:
        return False
    key = (ln.get('file'), ln['page'])
    if ln['page'] % 2 == 0 and ln['x'] <= me.left[key] + me.margin_tol:
        t = re.sub(rf'^[^{U}\s]{{1,3}}(?=[{U}]{{2}})', '', t)          # specks where letters were cropped
        t = re.sub(rf'^[^{U}\s]{{1,3}}([{U}])(?=[{U}]{{2}})', r'\1', t)
    # a surname the OCR split: "KA URIN Ostoje LUKA", "ZA VIŠA Nikole MILAN", "TIPO VIĆ Hasan"
    m = re.match(rf'^([{U}]{{2,4}}) ([{U}]{{2,}})(?=[\s,])', t)
    if m and (LAST[(m.group(1) + m.group(2)).capitalize()] or m.group(2) in ('VIĆ', 'VIC', 'IĆ', 'IC')):
        t = m.group(1) + m.group(2) + t[m.end():]
    t = re.sub(rf'([{U}]{{2,}})- ([{U}]{{2,}})', r'\1 - \2', t)      # "MITAR- MIĆO"
    ln['text'] = t
    return me.mark(ln)


def fix_given(soldiers: list[dict]) -> list[dict]:
    """Given and father names the OCR spaced out or misread: "MILO RAD", "BORIVO JE", "SA VAN" (joined when the
    joined name is known), "Ornerà" (rn for m, a stray accent)."""
    for s in soldiers:
        for k in ('first_name', 'middle_name'):
            v = (s.get(k) or '').translate(str.maketrans('àèäëòìù', 'aeaeoiu'))
            words = v.split()
            if len(words) == 2 and FIRST[(words[0] + words[1]).capitalize()] > 5 * FIRST[v]:
                v = (words[0] + words[1]).capitalize()
            if v and not FIRST[v] and 'rn' in v and FIRST[v.replace('rn', 'm')]:
                v = v.replace('rn', 'm')
            s[k] = v
        s['fathers_name'] = s['middle_name']
        s['full_name'] = ' '.join(x for x in (s['last_name'], s.get('middle_name') or '', s['first_name']) if x)
    return soldiers


ALPHABET = ['A', 'B', 'C', 'Č', 'Ć', 'D', 'Đ', 'DŽ', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'LJ', 'M', 'N', 'NJ', 'O',
            'P', 'R', 'S', 'Š', 'T', 'U', 'V', 'Z', 'Ž']


def _fold(w: str) -> tuple:
    """The book's collation: DŽ, LJ, NJ are letters; C < Č < Ć; Đ before DŽ (Đoković, then Džakulović)."""
    w, key = w.upper(), []
    while w:
        two = w[:2] if w[:2] in ALPHABET else None
        ch = two or w[0]
        key.append(ALPHABET.index(ch) if ch in ALPHABET else 99)
        w = w[len(ch):]
    return tuple(key)


def restore_cropped(soldiers: list[dict]) -> list[dict]:
    """Even pages lost the first letter(s) of each surname. The list is alphabetical, so the full surname sorts
    between the last ones on the page before and the first ones on the page after (both uncropped); the most
    common known surname that ends with what is left and fits there wins, else the only single letter that
    keeps the order. Otherwise the remnant stays as printed."""
    corpus = Counter(LAST)
    odd = [s for s in soldiers if s['pdf_page'] % 2]
    corpus.update(s['last_name'] for s in odd)
    letters = [a.capitalize() for a in ALPHABET]
    by_suffix = defaultdict(list)
    for w in corpus:
        by_suffix[w.lower()[-3:]].append(w)
    by_page: dict[int, list[tuple]] = {}
    for s in odd:
        by_page.setdefault(s['pdf_page'], []).append(_fold(s['last_name']))
    n = 0
    for s in soldiers:
        p = s['pdf_page']
        if p % 2 or not s['last_name']:
            continue
        # the middle of the last / first three entries, so that one garbled surname can't move the bound
        prev_p = max((q for q in by_page if q < p), default=None)
        next_p = min((q for q in by_page if q > p), default=None)
        before = by_page[prev_p][-3:] if prev_p else [()]
        after = by_page[next_p][:3] if next_p else [(99,)]
        lo, hi = sorted(before)[len(before) // 2], sorted(after)[len(after) // 2]
        crop = s['last_name']
        if len(crop) > 2 and crop[1] == crop[0].lower():    # the cut letter read twice: "Ššokčanić"
            crop = crop[1:].capitalize()
        if crop != s['last_name'] or corpus[crop] and lo <= _fold(crop) <= hi:    # not (or no longer) cropped
            if crop != s['last_name']:
                s['last_name'] = crop
                s['full_name'] = ' '.join(x for x in (crop, s.get('middle_name') or '', s['first_name']) if x)
            continue
        # a known surname that ends with what is left (or with all but a damaged first letter), 1-3 letters longer
        known = []
        for tail in {crop.lower(), crop[1:].lower() if len(crop) > 3 else crop.lower()}:
            for w in by_suffix.get(tail[-3:], ()):
                if w.lower().endswith(tail) and 1 <= len(w) - len(tail) <= 3 and lo <= _fold(w) <= hi:
                    known.append((corpus[w], tail == crop.lower(), -(len(w) - len(tail)), w))
        best = None
        if known:
            best = max(known)[3]
        elif not lo <= _fold(crop) <= hi:          # else a single letter, when the page's range allows only one
            single = {a + crop.lower() for a in letters if lo <= _fold(a + crop.lower()) <= hi}
            best = single.pop().capitalize() if len(single) == 1 else None
        best = best or crop
        if best != s['last_name']:
            s['last_name'] = best
            s['full_name'] = ' '.join(x for x in (best, s.get('middle_name') or '', s['first_name']) if x)
            n += 1
    print(f'  cropped surnames restored: {n}')
    return soldiers


def name_counts():
    first, last = Counter(), Counter()
    for f in ('prva-proleterska-soldiers.json', 'soldiers.json', '13-proleterska-soldiers.json', '6-krajiska-soldiers.json'):
        for s in json.load(open('website/public/' + f, encoding='utf-8')):
            first[s['first_name']] += 1
            last[s['last_name']] += 1
    return first, last


def post(soldiers: list[dict]) -> list[dict]:
    soldiers = split_leading_aliases(repair_lj_ocr(restore_diacritics(soldiers)))
    return fix_given(restore_cropped(lone_names_to_given(soldiers, *name_counts())))


if __name__ == '__main__':
    run_parser(
        pdf_path='website/public/pdfs/2-krajiska.pdf',
        brigade_code=24,
        output_path='website/public/2-krajiska-soldiers.json',
        start_page=3,
        end_page=65,
        layout='single',
        script='latin',
        entry_start_re=me.entry_start,
        parse_entry_fn=me.parse_entry,
        line_filter=keep_line,
        prepare_fn=me.prepare,
        post_fn=post,
    )
