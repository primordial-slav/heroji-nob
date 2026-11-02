"""
Whole lines of an entry that its text lacks, read from the entry's own box on the page and put back.

Parsers dropped a line for a page number or for junk (a line that is a year alone, "1944."; a line of a word or two), so
an entry can end on "poginuo", "NOP-u pristupio" or "u KPO od". Each line of the entry's box is held against its text
(both folded, Cyrillic in Latin); a line the text holds in no part, after the first line it does hold, is lost.

Years alone (the last line, or the last two of a span) go in from every book. A longer line goes in from the books listed
in TEXT_LINES, whose boxes were read one by one: elsewhere such a line is as often the next man's, a heading or a table's
column. A line that opens like an entry (a surname in capitals) never goes in: a box can run over a man who was left out.

Run: python scripts/restore_lost_lines.py [--sample N]; --write START appends the edits to corrections.json from that id.
The books across units' entries aren't corrected there: --entries writes those lines to their entries files.
"""
import collections, json, random, re, sys
from difflib import SequenceMatcher
from multiprocessing import Pool
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / 'scripts'))
sys.path.insert(0, str(ROOT / 'data-extraction'))
sys.stdout.reconfigure(encoding='utf-8')
import entry_boxes as EB
from name_utils import BRIGADE_CONFIGS

LAT = dict(zip('абвгдђежзијклмнопрстћуфхцчш', 'abvgdđežzijklmnoprstćufhcčš'))
LAT.update({'љ': 'lj', 'њ': 'nj', 'џ': 'dž'})
FOLD = str.maketrans('čćžšđ', 'cczsd')
CAP = 'A-ZČĆŽŠĐА-ШЂЉЊЋЏЈ'
NUMBER = re.compile(r'^\W*\d{1,4}\W*$')
YEAR = re.compile(r'^\W*(19\d\d)\W*$')
HEADING = re.compile(rf'^\W*(?:\d{{1,4}}\W+)?[{CAP}]{{3,}}')
# tables, and lists whose text the parser puts together: a line of the box is no line of the text
NOT_LINES = {'kozjanski-odred.pdf', '53-srednjobosanska-divizija.pdf', '18-slavonska.pdf', 'cazinska-krajina-pali-borci.pdf',
             '7-crnogorska-omladinska.pdf', '4-brigada-slavonije.pdf', '1-zagorska.pdf', '34-divizija.pdf', '22-divizija.pdf',
             'zene-vi-korpus-poginule.pdf', 'zene-1-dalmatinska.pdf', 'zene-11-dalmatinska.pdf', 'osjecka-zene.pdf',
             'turopoljsko-posavski-odred.pdf', 'krizani-v-boju-za-svobodo.pdf', '9-srpska.pdf', '1-2-prekomorska.pdf',
             '5-prekomorska.pdf', '4-prekomorska.pdf', 'imotska-krajina-pali-borci.pdf', 'vinodolska-selca.pdf',
             'hrvatsko-zagorje-1981.pdf', 'artilerija-9-korpusa.pdf', 'moste-polje-spomenica-1941.pdf', '32-divizija.pdf',
             'prva-proleterska-garibaldi.pdf', 'prva-vojvodjanska.pdf'}
TEXT_LINES = {'12-srpska.pdf', '8-crnogorska.pdf', 'druga-licka-spisak.pdf', '19-srpska.pdf', 'mosorski-odred.pdf', 'mosorski-odred-2.pdf',
              'cacanski-kraj-pali.pdf', '5-vojvodjanska.pdf', 'crnogorski-bataljon.pdf', 'ljubljanska-brigada.pdf', '1-kosovsko-metohijska.pdf'}
# the pages of a book whose lines are read; the 1. kosovsko-metohijska's lists of joiners run on with men of their own
FROM_PAGE = {'1-kosovsko-metohijska.pdf': 25}
# boxes that hold another man's words, read one by one
NOT_THESE = {'0167001590', '0004003235', '0004003243', '0038000313', '0148001456', '0003000646'}
LONG_BOXES = {'mosorski-odred.pdf', 'mosorski-odred-2.pdf'}
OCR_WORDS = {'todine': 'godine', 'aodine': 'godine', 'goline': 'godine', 'Todine': 'Godine'}


def folded(text):
    """The letters and digits of a text, folded, and the place in the text each came from."""
    out, where = [], []
    for i, c in enumerate(text):
        for ch in LAT.get(c.lower(), c.lower()):
            ch = ch.translate(FOLD)
            if ch.isascii() and ch.isalnum():
                out.append(ch)
                where.append(i)
    return ''.join(out), where


def latin(line):
    """A line of the page as the entries print it: Latin, the OCR's л> and н> for љ and њ."""
    line = line.replace('\u00ad', '-')
    line = re.sub(r'([ЛлНн])>', lambda m: {'Л': 'Љ', 'л': 'љ', 'Н': 'Њ', 'н': 'њ'}[m.group(1)], line)
    line = re.sub(r'Ј1', 'Л', line)
    out = ''
    for c in line:
        l = LAT.get(c.lower())
        out += c if l is None else (l.capitalize() if c.isupper() else l)
    return re.sub(r'\s+', ' ', out).strip()


def box_lines(page, x):
    x0 = x.get('pdf_x_left') if x.get('pdf_x_left') is not None else x.get('pdf_x')
    y0, x1, y1 = x.get('pdf_y'), x.get('pdf_x_end'), x.get('pdf_y_end')
    if None in (x0, y0, x1, y1):
        return []
    best = []
    for col in page.get('columns', []):
        inside = [ln for ln in col if ln['top'] >= y0 - 2.5 and (ln['top'] + ln['bottom']) / 2 < y1
                  and x0 - 12 <= (ln['x0'] + ln['x1']) / 2 <= x1 + 12]
        if len(inside) > len(best):
            best = inside
    return sorted(best, key=lambda l: (l['top'], l['x0']))


def check(job):
    pdf, items = job
    pages = EB.PageCache().pages(pdf, sorted({i['pdf_page'] for i in items}))
    res = []
    for x in items:
        page = pages.get(x['pdf_page'])
        lines = box_lines(page, x) if page else []
        if len(lines) < 2:
            continue
        E, where = folded(x['text'])
        if len(E) < 3:
            continue
        B, spans = '', []
        for ln in lines:
            f = folded(ln['text'])[0]
            spans.append((len(B), len(B) + len(f)))
            B += f
        blocks = [b for b in SequenceMatcher(None, B, E, autojunk=False).get_matching_blocks() if b.size >= 3]
        if not blocks:
            continue
        hit = [False] * len(B)
        for b in blocks:
            if b.size >= 4 or len(E) < 8:
                hit[b.a:b.a + b.size] = [True] * b.size
        name = {folded(t)[0] for t in re.split(r'[\s\-–—,.()]+', x['nm']) if t}
        lost = []
        for li, (a, z) in enumerate(spans):
            if z == a or a < blocks[0].a or sum(hit[a:z]) / (z - a) > 0.2:
                continue
            raw = lines[li]['text']
            toks = [folded(t)[0] for t in raw.split()]
            if toks and sum(1 for t in toks if t in name or any(SequenceMatcher(None, t, n).ratio() > 0.75 for n in name)) >= 0.6 * len(toks):
                continue
            before = [b for b in blocks if b.a + b.size <= z]
            e_at = before[-1].b + before[-1].size if before else 0
            lost.append(dict(line=raw, li=li, pos=where[e_at - 1] + 1 if e_at else 0, tail=not any(b.a >= z for b in blocks)))
        if lost:
            res.append(dict(x, pdf=pdf, lost=lost, n=len(lines)))
    return res


def fits(r):
    """The lost lines of an entry that go in."""
    pdf, lost = r['pdf'], r['lost']
    if r['id'] in NOT_THESE:
        return []
    lost = [l for l in lost if not (NUMBER.match(l['line']) and not YEAR.match(l['line']))]
    if lost and all(YEAR.match(l['line']) and l['tail'] for l in lost) and len(lost) <= 2:
        return lost
    if pdf not in TEXT_LINES or r['pdf_page'] < FROM_PAGE.get(pdf, 0) or len(lost) > (8 if pdf in LONG_BOXES else 3):
        return []
    for l in lost:
        if HEADING.match(l['line']) or not re.search(r'[^\W\d_]{3}|19\d\d', l['line']):
            return []
    return lost


def splice(text, ls, read):
    """The text with its lost lines put back, each after what the text holds before it."""
    groups = collections.defaultdict(list)
    for l in ls:
        groups[l['pos']].append(read(l['line']))
    out, last = '', 0
    for pos in sorted(groups):
        add = re.sub(r'(?<=[^\W\d_])[-\u00ad]\s+(?=[^\W\d_])', '', ' '.join(groups[pos]))
        rest = text[pos:]
        head = text[last:pos]
        if re.fullmatch(r'\W*|\W*[^\W\d_]{1,2}\W*', rest):            # the end of the text, or a speck after it
            comma = rest.strip().startswith(',')
            # the parser closed the entry on the word before: "marta." + "1942;" is "marta 1942."; a date's own dot stays
            dot = '.' if rest.strip().startswith('.') and (re.search(r'\d$', head.rstrip()) or add[:1].isupper()) else ''
            sep = ',' if comma else dot
            add = re.sub(r'[;,:]+$', '', add)
            if (rest.strip().startswith('.') or re.search(r'[;,:]$', groups[pos][-1])) and not add.endswith('.'):
                add += '.'
            out += re.sub(r'[-\u00ad]$', '', head) + add if re.search(r'[^\W\d_][-\u00ad]$', head) else head.rstrip() + sep + ' ' + add
            last = len(text)
            continue
        add = re.sub(r'[;,:]+$', '', add) if rest[:1] in ',;:' else add
        if add.endswith('.') and rest[:1] == '.':
            add = add[:-1]
        out += re.sub(r'[-\u00ad]$', '', head) + add if re.search(r'[^\W\d_][-\u00ad]$', head) else head.rstrip() + ' ' + add
        if rest[:1] not in ' ,.;:':
            out += ' '
        last = pos
    return out + text[last:]


def main():
    by = collections.defaultdict(list)
    words = collections.Counter()
    for code, cfg in sorted(BRIGADE_CONFIGS.items()):
        if 131 <= code <= 138:
            continue
        p = ROOT / 'website/public' / cfg['json_file']
        if not p.exists():
            continue
        for s in json.loads(p.read_text(encoding='utf-8')):
            for k, e in enumerate([s] + [o for o in s.get('other_sources', ()) if not o.get('ref_book') and not o.get('unit_file')]):
                f, pg = e.get('pdf_file'), e.get('pdf_page')
                t = (e.get('additional_info') or '').strip()
                words.update(re.findall(r'[^\W\d_]{4,}', t))
                if not f or not pg or e.get('pdf_y') is None or f in EB.INLINE_ENTRIES or f in NOT_LINES or pg in EB.INLINE_PAGES.get(f, ()) or e.get('pdf_rects'):
                    continue
                if not (ROOT / 'website/public/pdfs' / f).exists():
                    continue
                by[f].append(dict(id=e['soldier_id'], rec=s['soldier_id'], unit=code, nm=(e.get('full_name') or e.get('name') or '') + ' ' + (e.get('middle_name') or ''),
                                  text=t, pdf_page=int(pg), **{k2: e.get(k2) for k2 in ('pdf_x', 'pdf_x_left', 'pdf_y', 'pdf_x_end', 'pdf_y_end')}))
    known = {w for w, n in words.items() if n >= 3}
    common = [w for w, n in words.items() if n >= 30]
    by_first = collections.defaultdict(list)
    for w in common:
        by_first[w[0].lower()].append(w)

    def read(line):
        """A Cyrillic line's slips in the words the entries know: "aprila" for "аирила"."""
        cyr = bool(re.search('[А-Яа-яЂђЉљЊњЋћЏџЈј]', line))
        t = latin(line)
        if not cyr:
            return t
        t = re.sub(r'[^\W\d_]+', lambda m: OCR_WORDS.get(m.group(0), m.group(0)), t)

        def fix(m):
            w = m.group(0)
            if w in known or len(w) < 4:
                return w
            best = max(by_first.get(w[0].lower(), ()), key=lambda c: SequenceMatcher(None, w.lower(), c.lower()).ratio(), default=None)
            if best and SequenceMatcher(None, w.lower(), best.lower()).ratio() >= 0.8 and len(best) >= len(w) - 1:
                return best if w[0].islower() == best[0].islower() else (best.capitalize() if w[0].isupper() else best.lower())
            return w
        return re.sub(r'[^\W\d_]+', fix, t)

    with Pool(8) as pool:
        found = [r for part in pool.imap_unordered(check, sorted(by.items(), key=lambda kv: -len(kv[1]))) for r in part]
    # a line that recurs in a book is a running head
    seen = collections.Counter((r['pdf'], folded(l['line'])[0]) for r in found for l in r['lost'])
    out = []
    for r in found:
        r['lost'] = [l for l in r['lost'] if YEAR.match(l['line']) or seen[(r['pdf'], folded(l['line'])[0])] < 4 or len(l['line']) <= 12]
        ls = fits(r)
        if ls:
            out.append(dict(r, use=ls, new=splice(r['text'], ls, read)))
    print(len(found), 'entries lack a line;', len(out), 'go in')
    print(collections.Counter(r['pdf'] for r in out).most_common(60))
    yrs = sum(1 for r in out if all(YEAR.match(l['line']) for l in r['use']))
    print('years alone', yrs, 'longer', len(out) - yrs, 'in 122', sum(1 for r in out if r['unit'] == 122))
    if '--sample' in sys.argv:
        n = int(sys.argv[sys.argv.index('--sample') + 1])
        random.seed(11)
        book = collections.defaultdict(list)
        for r in out:
            book[r['pdf']].append(r)
        for pdf, v in sorted(book.items(), key=lambda kv: -len(kv[1])):
            print(f'--- {pdf}: {len(v)}')
            longer = [r for r in v if not all(YEAR.match(l['line']) for l in r['use'])]
            years = [r for r in v if all(YEAR.match(l['line']) for l in r['use'])]
            for r in random.sample(longer, min(n, len(longer))) + random.sample(years, min(2, len(years))):
                print('  ', r['id'], r['nm'][:24], f"p{r['pdf_page']}", '| was ...', r['text'][-48:], '| now ...', r['new'][-(48 + sum(len(l['line']) for l in r['use'])):])
    if '--write' in sys.argv:
        start = int(sys.argv[sys.argv.index('--write') + 1])
        P = ROOT / 'corrections.json'
        corr = json.loads(P.read_text(encoding='utf-8'))
        assert not [c for c in corr if c['id'] >= start]
        units = [r for r in out if r['unit'] != 122]
        add = [{'id': start + i, 'action': 'edit', 'soldier_id': r['id'], 'fields': {'additional_info': r['new']},
                'reason': f"Lines the parser dropped, on the entry's page ({r['pdf']}, p. {r['pdf_page']}): \"{' / '.join(l['line'] for l in r['use'])[:80]}\""}
               for i, r in enumerate(units)]
        P.write_text(json.dumps(corr + add, ensure_ascii=False, indent=2), encoding='utf-8')
        print('written', len(add), start, start + len(add) - 1)
    if '--entries' in sys.argv:
        Path(sys.argv[sys.argv.index('--entries') + 1]).write_text(json.dumps([r for r in out if r['unit'] == 122], ensure_ascii=False), encoding='utf-8')


if __name__ == '__main__':
    main()
