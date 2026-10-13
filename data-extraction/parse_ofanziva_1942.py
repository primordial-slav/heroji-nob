"""
Ofanziva proleterskih brigada u leto 1942. (Mišo Leković, 1965; znaci.org 00001/183, its chapter 183_15.pdf) →
website/public/pdfs/ofanziva-1942-poginuli.pdf: a book across units, its entries added to the records of the soldiers
it describes (see scripts/match_references.py), as the hero books are, but with the scan on the site.

"Spisak boraca 1, 2, 3. i 4. proleterske brigade poginulih i nestalih u toku ofanzive ka zapadnoj Bosni (24. VI — 30.
IX 1942)", book pp. 698-711 (PDF pp. 1-14), one column, by brigade and battalion under centred headings:
    Cerović Anka, 1924, Tušinja kod Boana, domaćica, član Skoja, pogi-
nula u Šćitu, kod Prozora, 14. jula 1942.
The first line of an entry stands indented. The 4. proleterska's 1., 2. and 3. bataljon give the age ("24 godine")
instead of the year of birth; the year the matcher compares is 1942 less the age. The footnote under the title (p. 1)
is not read.

The brigades are the site's units: 1. proleterska (1), 2. proleterska (39), 3. proleterska sandžačka (5), 4. proleterska
crnogorska (40); each entry carries its brigade's code in `units`, which the matcher weighs as agreement.

Output: data-extraction/znaci/ofanziva-1942-poginuli-entries.json (IDs 9006xxxxxx, in the book's order), with the fields
the matcher reads (last_name, first_name, birth_year, born_in, death_year, death_date as ISO, units) and the entry's
place on the page and its box (pdf_file, pdf_page, pdf_x, pdf_y and the box fields of entry_boxes.py).

Usage: python data-extraction/parse_ofanziva_1942.py [--sample N]
"""
from __future__ import annotations

import json
import random
import re
import sys
from pathlib import Path

import pdfplumber

sys.stdout.reconfigure(encoding='utf-8')
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent / 'scripts'))
import entry_boxes  # noqa: E402
from extract_life_events import iso, parse_when  # noqa: E402
from pdf_coords import viewer_words  # noqa: E402

PDF = 'ofanziva-1942-poginuli.pdf'
OUT = HERE / 'znaci' / 'ofanziva-1942-poginuli-entries.json'
PREFIX = '9006'
BRIGADES = {'1': 1, '2': 39, '3': 5, '4': 40}       # "N. PROLETERSKA BRIGADA" -> the site's unit code
U, L = 'A-ZČĆŽŠĐ', 'a-zčćžšđ'
DEATH = re.compile(r'\b(poginu[ol]a?|nesta[ol]a?|podlegl?[ao]?|umr[lo]a?|streljan[a]?|ubijen[a]?)\b', re.I)
DATE = re.compile(r'(?:(?:početkom|krajem|sredinom)\s+)?(?:\d{1,2}(?:/\d{1,2})?[.,]?\s*)?'
                  r'(?:januara|februara|marta|aprila|maja|juna|jula|avgusta|septembra|oktobra|novembra|decembra)\s+19\d\d')


FOLD = str.maketrans('ČĆŽŠĐ', 'CCZSD')
# znaci.org re-typeset the book from its OCR, so the page shows the text layer's slips: o and e read as c ("Nedcljko",
# "Pcpivoda"), i as ";" or "l" ("M;lorad"), ć as e ("Mieunović"), "ić" as "ie" ("Ružičie"), K as R ("Rarlovanović"),
# "im" as "hn" ("Shno"), d as đ ("Milorađ"), Đ as D ("Doković")
SUBS = [('c', 'o'), ('c', 'e'), (';', 'i'), ('e', 'ć'), ('e', 'č'), ('ie', 'ić'), ('ei', 'el'), ('a', 'o'), ('R', 'K'),
        ('h', 'i'), ('n', 'm'), ('ii', 'ti'), ('l', 'i'), ('i', 'l')]
# a letter the page prints may stand for these: a caron or an accent it lost, or a d it gave a stroke
LOST = {'C': 'ČĆ', 'D': 'Đ', 'S': 'Š', 'Z': 'Ž', 'Đ': 'D'}
KEEP = {'Ambrozie'}                     # read two ways (Ambrozić, Ambrožič): left as printed
_spell = {'last': {}, 'first': {}}       # folded upper-case name -> Counter of the site's spellings


def corpus() -> None:
    from collections import Counter
    for f in (HERE.parent / 'website' / 'public').glob('*soldiers.json'):
        for s in json.loads(f.read_text(encoding='utf-8')):
            for part, key in (('last', 'last_name'), ('first', 'first_name')):
                w = (s.get(key) or '').upper()
                if w:
                    _spell[part].setdefault(w.translate(FOLD), Counter())[w] += 1


def known(w: str, part: str) -> tuple[int, str]:
    """How often the site spells a name of these letters, and the spelling it uses most that the page's letters allow:
    the same letters, or one with a caron the page lost ("Duričić" = Đuričić) or a d it printed with a stroke
    ("Milorađ"); never another accent for one the page prints (Čorac stays Čorac)."""
    v = w.upper()
    c = _spell[part].get(v.translate(FOLD))
    if not c:
        return 0, ''
    if c.get(v, 0) >= 2:                                                  # a spelling the site has once may be a slip too
        return sum(c.values()), v
    fits = [s for s, _ in c.most_common() if len(s) == len(v) and all(a == b or b in LOST.get(a, '') for a, b in zip(v, s))]
    return (sum(c.values()), fits[0]) if fits else (0, '')


def repair(w: str, part: str) -> str:
    """A name the site doesn't know, read back as the spelling it knows best among the text layer's slips (one or two
    of them); a name the site has in other letters ("Milorađ", "Duričić") takes its usual spelling."""
    if _spell[part].get(w.upper().translate(FOLD), {}).get(w.upper(), 0) >= 2 or w in KEEP:
        return w
    n, best = known(w, part)
    if n >= 3:
        return title(best)
    seen, frontier = {w}, [w]
    for _ in range(2):
        nxt = []
        for v in frontier:
            for a, b in SUBS:
                i = v.find(a)
                while i >= 0:
                    c = v[:i] + b + v[i + len(a):]
                    if c not in seen:
                        seen.add(c)
                        nxt.append(c)
                    i = v.find(a, i + 1)
        frontier = nxt
    # a slip read back to a spelling the site has letter for letter goes first
    scored = [(best == v.upper(), n, best) for v in seen - {w} for n, best in [known(v, part)] if n >= 3]
    return title(max(scored)[2]) if scored else w


def title(name: str) -> str:
    return '-'.join(p.title() for p in name.split('-'))


def lines_of(page) -> list[dict]:
    """The page's text lines, top to bottom: text, x0, x1, top."""
    rows: list[list[dict]] = []
    for w in sorted(viewer_words(page, keep_blank_chars=False), key=lambda w: (w['top'], w['x0'])):
        if rows and abs(rows[-1][0]['top'] - w['top']) <= 3:
            rows[-1].append(w)
        else:
            rows.append([w])
    out = []
    for r in rows:
        r.sort(key=lambda w: w['x0'])
        out.append({'text': ' '.join(w['text'] for w in r), 'x0': r[0]['x0'], 'x1': r[-1]['x1'],
                    'top': min(w['top'] for w in r)})
    return out


def read() -> list[dict]:
    entries, brigade, battalion = [], None, None
    with pdfplumber.open(HERE.parent / 'website' / 'public' / 'pdfs' / PDF) as pdf:
        for pno, page in enumerate(pdf.pages, 1):
            lines = lines_of(page)
            body = [ln for ln in lines if ln['x1'] - ln['x0'] > 120]
            margin = min(ln['x0'] for ln in body)
            for ln in lines:
                t, indent = ln['text'].strip(), ln['x0'] - margin
                if t.startswith('*') or re.fullmatch(r'[.,]?\d{3}', t):
                    if t.startswith('*'):
                        break                                        # the footnote runs to the page's end
                    continue
                m = re.fullmatch(r'(\d)\.\s*PROLETERSKA BRIGADA', t)
                if m:
                    brigade, battalion = m.group(1), None
                    continue
                if indent > 60 and re.fullmatch(rf'(?:\d\.\s*)?[{U}{L}. ]+', t) and len(t) < 40:
                    if brigade:
                        battalion = t                                # "1. bataljon"
                    continue
                if not brigade:
                    continue                                         # the list's title
                if 15 < indent < 60 and re.match(rf'[{U}]', t):              # p. 4's first line stands 48 pt in
                    entries.append({'lines': [t], 'pdf_page': pno, 'pdf_x': round(ln['x0'], 1),
                                    'pdf_y': round(ln['top'], 1), 'brigade': brigade, 'battalion': battalion})
                elif entries and entries[-1]['pdf_page'] in (pno, pno - 1):
                    entries[-1]['lines'].append(t)
    return entries


def join(lines: list[str]) -> str:
    text = lines[0]
    for ln in lines[1:]:
        if re.search(rf'[{L}]-$', text) and re.match(rf'[{L}]', ln):
            text = text[:-1] + ln                                    # "pogi-" / "nula"
        else:
            text += ' ' + ln
    return re.sub(r'\s+', ' ', text).strip()


def parse(e: dict, n: int) -> dict:
    text = join(e['lines'])
    text = re.sub(r'^([^,.]+)\.\s(?=\d)', r'\1, ', text)              # "Jančić Petar. 1912", "Stanojević Mirko. 20 godina"
    name, info = (text.split(',', 1) + [''])[:2]
    info = info.strip()
    name = re.sub(rf'(?<=[{L}]) (?=[{L}]+$)', '', name.strip())            # "Popović Drago je": the text layer's gap
    words = name.split()
    last, first = repair(words[0], 'last'), ' '.join(repair(w, 'first') for w in words[1:])
    rec = {'soldier_id': f'{PREFIX}{n:06d}', 'name': ' '.join([last, first]).strip(), 'last_name': last,
           'first_name': first, 'nick': '', 'fathers_name': ''}
    if rec['name'] != name:
        rec['printed'] = name
    m = re.match(r'(1[89]\d\d)\b', info)
    age = re.match(r'(\d{2})\s+godin[aeu]\b', info)
    rec['birth_year'] = m.group(1) if m else str(1942 - int(age.group(1))) if age else ''
    # the birthplace: what stands between the year (or the age) and the trade, "Dapsice, kod Ivangrada"
    rest = info[m.end() if m else age.end() if age else 0:].lstrip(' ,.')
    d = DEATH.search(info)
    parts = [p.strip() for p in rest.split(',')]
    born = []
    for p in parts:
        if not p or not re.match(rf'(?:kod\s+)?[{U}]', p) or DEATH.match(p) or re.match(r'(?:član|kandidat)', p):
            break
        born.append(p)
    rec['born_in'] = ', '.join(born) if born and (not d or rest.find(born[0]) < rest.find(d.group(0))) else ''
    when = DATE.search(info[d.start():]) if d else None
    parsed = parse_when(when.group(0).replace('/', '-')) if when else None
    rec['death_year'] = '1942'
    rec['death_date'] = iso(parsed[0]) if parsed else ''
    rec['units'] = [BRIGADES[e['brigade']]]
    rec['additional_info'] = info
    rec['unit'] = f"{e['brigade']}. proleterska brigada" + (f", {e['battalion']}" if e['battalion'] else '')
    rec.update(pdf_file=PDF, pdf_page=e['pdf_page'], pdf_x=e['pdf_x'], pdf_y=e['pdf_y'])
    return rec


def main():
    corpus()
    raw = read()
    recs = [parse(e, i) for i, e in enumerate(raw, 1)]
    stats = entry_boxes.fill_boxes(recs)
    OUT.parent.mkdir(exist_ok=True)
    OUT.write_text(json.dumps(recs, ensure_ascii=False, indent=1), encoding='utf-8')
    by = {}
    for r in recs:
        by[r['unit'].split(',')[0]] = by.get(r['unit'].split(',')[0], 0) + 1
    print(f'{len(recs)} entries -> {OUT.relative_to(HERE.parent)}; {by}')
    print(f"boxes: {entry_boxes.describe(stats, stats['boxed'])}")
    print(f"no birth year: {sum(not r['birth_year'] for r in recs)}, no birthplace: {sum(not r['born_in'] for r in recs)}, "
          f"no death date: {sum(not r['death_date'] for r in recs)}, no given name: {sum(not r['first_name'] for r in recs)}")
    if '--sample' in sys.argv:
        random.seed(5)
        for r in random.sample(recs, int(sys.argv[sys.argv.index('--sample') + 1])):
            print(f"  {r['name']!r} {r['birth_year']} [{r['born_in']}] {r['death_date']} | {r['unit']} | p{r['pdf_page']}")
            print(f"      {r['additional_info']}")


if __name__ == '__main__':
    main()
