"""
Parser: 12. dalmatinska (1. otočka) NOU brigada (brigade code 50) — "Spisak poginulih boraca i rukovodilaca".

Source: Nikola Anić, "Dvanaesta dalmatinska udarna brigada (Prva otočka)", the chapter "Napomene i spisak
        poginulih" (znaci.org 00001/80_7.pdf)  →  website/public/pdfs/12-dalmatinska.pdf, pages 35-48 (book pp. 353-366)
One column, Latin. The fallen are run on, entry after entry, separated by semicolons, under a heading for each
battle that gives its date:
    POGINULI U BORBI PROTIV USTAŠA U SUĆURJU NA HVARU,
    22. RUJNA 1943.
    Jeličić Ante Matin, borac, pog. 22. 9. na položaju Pomrvica, Sućuraj; Jeličić Mate Nikole, borac, ...
Surname, given name, the father as a possessive ("Matin", "Jurjev") or in the genitive ("Nikole", "pok. Ivana"; pok.
= his late father), the duty, "iz" the village, the death ("pog. 22. 9." — the year is the heading's). Notes of
the author run on among them ("Svi su rođeni u Sućurju ..."), footnotes are in smaller type. The last section,
"Ostalo", lists four names the author could not confirm as the brigade's.
Each soldier gets his own box on the page (the words of his entry, a box per line: pdf_rects); entry_boxes.py
leaves these alone (INLINE_ENTRIES). The death date takes the heading's year where the entry gives none.

    python data-extraction/parse_12_dalmatinska.py [--items]
"""
from __future__ import annotations

import glob
import json
import re
import sys
from collections import Counter
from pathlib import Path

import pdfplumber

sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(Path(__file__).parent.parent))
from _parser_scaffold import _record  # noqa: E402
from pdf_coords import viewer_words  # noqa: E402
from scripts.name_utils import genitive_to_nominative  # noqa: E402
from scripts.soldier_id_utils import assign_ids_to_soldiers  # noqa: E402

PDF = 'website/public/pdfs/12-dalmatinska.pdf'
OUT = 'website/public/12-dalmatinska-soldiers.json'
CODE = 50
FIRST, LAST = 35, 48

U, L = 'A-ZČĆŽŠĐ', 'a-zčćžšđ'
DATE = re.compile(r'(?<![\d.])(\d{1,2})(?:[.,]\s*|\s+)(\d{1,2})\.(?:\s*(19[34]\d)\.?)?')   # "2. 12.", "2, 12.", "19 4."
DEATH = re.compile(r'\b(?:pog\.?|(?:poginu[ol]a?|umr[ol]a?|ubijen[a]?|strijeljan[a]?|nestao|nestala|nastradao)\b)', re.I)
# Surname[-Surname] Given [Father | pok. Father] — the entry's name, before its first comma (or "iz", or a period)
LX = L + 'àáâäèéëìíîïòóôöùúûü'                # the scan's accents ("Mióo") and foreign names (Jüngling)
NAME = re.compile(rf'^([{U}][{LX}\']+(?:-[{U}][{LX}]+)?)(?:\s*\(((?:ili\s+)?[{U}][{LX}]+\??):?\))?'
                  rf'\s+([{U}][{LX}]+|[{U}]\.)'
                  rf'(?:\s+(pok\.\s+)?([{U}][{LX}]+|[{U}]\.))?(?:\s*\(([^)]*)\))?(?=\s*(?:,|\.|;|\s+iz\b|\s+sa\b|$))')


def read_lines() -> list[dict]:
    """Body lines of the list (no footnotes, page numbers), in reading order, with their words."""
    out = []
    with pdfplumber.open(PDF) as pdf:
        for pn in range(FIRST, LAST + 1):
            words = [w for w in viewer_words(pdf.pages[pn - 1], extra_attrs=['size']) if w['size'] >= 9]
            lines: list[list[dict]] = []
            for w in sorted(words, key=lambda w: (w['top'], w['x0'])):
                if lines and abs(lines[-1][0]['top'] - w['top']) < 4:
                    lines[-1].append(w)
                else:
                    lines.append([w])
            page_lines = []
            for ws in lines:
                ws.sort(key=lambda w: w['x0'])
                for w in ws:
                    w['page'] = pn
                text = ' '.join(w['text'] for w in ws)
                if re.fullmatch(r'[\d\W]+', text):
                    continue                                             # page number
                page_lines.append({'page': pn, 'x': ws[0]['x0'], 'words': ws, 'text': text})
            # the page's left margin (it differs between odd and even pages): a paragraph's first line is indented
            margin = Counter(round(ln['x'] / 3) * 3 for ln in page_lines).most_common(1)[0][0] if page_lines else 0
            for ln in page_lines:
                ln['indent'] = ln['x'] > margin + 10
            out.extend(page_lines)
    return out


def is_heading(text: str) -> bool:
    letters = [c for c in text if c.isalpha()]
    return len(letters) >= 6 and sum(c.isupper() for c in letters) / len(letters) > 0.8


def tokens(lines: list[dict]) -> list[dict]:
    """The words of the entries in reading order; headings and sub-headings ("Ostalo:") as boundaries carrying
    the heading's text. A word broken at a line end ("Iva-" + "na") is one token."""
    toks: list[dict] = []
    heading_lines: list[str] = []
    started = False
    for ln in lines:
        text = ln['text']
        # a heading's second line, often only its date: "22. RUJNA 1943."
        letters = [c for c in text if c.isalpha()]
        cont = heading_lines and letters and sum(c.isupper() for c in letters) / len(letters) > 0.8
        if is_heading(text) or cont:
            if not started and text.startswith('S P I S'):
                continue
            if not heading_lines or toks and not toks[-1].get('boundary'):
                toks.append({'boundary': True, 'heading': ''})
                heading_lines = []
            heading_lines.append(text)
            toks[-1]['heading'] = ' '.join(heading_lines)
            started = True
            continue
        heading_lines = []
        if not started:
            continue                                                     # the list's title and its subtitle
        if text.endswith(':') and len(text) < 40:
            toks.append({'boundary': True, 'heading': None, 'sub': text.rstrip(':')})
            continue
        for k, w in enumerate(ln['words']):
            prev = toks[-1] if toks else None
            if (k == 0 and prev and not prev.get('boundary') and prev['line_end'] and prev['text'].endswith('-')
                    and len(prev['text']) > 1 and w['text'][:1].isalpha()):
                prev['text'] = (prev['text'][:-1] if w['text'][:1].islower() else prev['text']) + w['text']
                prev['words'].append(w)
                prev['line_end'] = len(ln['words']) == 1
                continue
            # "i to:Deplano": a colon glued to the name after it ends what comes before
            head, colon, tail = w['text'].partition(':')
            if colon and tail[:1].isupper():
                toks.append({'text': head + ':', 'words': [w], 'line_end': False, 'para': k == 0 and ln['indent']})
                toks.append({'text': ':', 'words': [], 'line_end': False})
                toks.append({'text': tail, 'words': [w], 'line_end': k == len(ln['words']) - 1})
                continue
            toks.append({'text': w['text'], 'words': [w], 'line_end': k == len(ln['words']) - 1,
                         'para': k == 0 and ln['indent']})
    return toks


def items(toks: list[dict]) -> list[dict]:
    """Entries: the words between semicolons; a paragraph (an indented line) ends one too. Each entry carries the
    heading (battle and date) and sub-heading it is under."""
    out, cur, heading, sub = [], [], '', ''

    def close():
        nonlocal cur
        if cur:
            out.append({'toks': cur, 'heading': heading, 'sub': sub})
        cur = []

    for t in toks:
        if t.get('boundary'):
            close()
            if t.get('heading') is not None:
                heading, sub = t['heading'], ''
            else:
                sub = t['sub']
            continue
        # a new paragraph: an indented line that starts with a capital after a sentence's end (justified lines that
        # start with a date or a bracket can look indented too)
        if t.get('para') and cur and cur[-1]['text'].endswith(('.', ':')) and t['text'][:1].isupper():
            close()
        if t['text'] in (';', ':'):
            close()
            continue
        cur.append(t)
        if t['text'].endswith(';'):
            t['text'] = t['text'][:-1]
            close()
        elif t['text'].endswith(':') and len(cur) > 3 and DATE.search(' '.join(x['text'] for x in cur)):
            t['text'] = t['text'][:-1]                                     # "pog. 3. 12. kod Vrbnika: Knežević ..."
            close()
    close()
    return out


_last_year = ['']


def heading_year(heading: str) -> str:
    """The heading's year; a heading without one ("ŠOLTE, 23. I 24. RUJNA") is in the year of the one before it, the
    list being in the order of the battles."""
    years = re.findall(r'19[34]\d', heading)
    if years:
        _last_year[0] = years[-1]
    return years[-1] if years else _last_year[0]


def boxes(words: list[dict]) -> dict:
    page = words[0]['page']
    segs: list[list[dict]] = []
    for w in words:
        if w['page'] != page:
            break
        if segs and abs(segs[-1][-1]['top'] - w['top']) < 4:
            segs[-1].append(w)
        else:
            segs.append([w])
    rects = [[round(min(w['x0'] for w in s), 1), round(min(w['top'] for w in s), 1),
              round(max(w['x1'] for w in s), 1), round(max(w['bottom'] for w in s), 1)] for s in segs]
    out = {'pdf_file': Path(PDF).name, 'pdf_page': page, 'pdf_x': rects[0][0], 'pdf_y': rects[0][1],
           'pdf_x_end': max(r[2] for r in rects), 'pdf_y_end': max(r[3] for r in rects)}
    left = min(r[0] for r in rects)
    if left < rects[0][0]:
        out['pdf_x_left'] = left
    if len(rects) > 1:
        out['pdf_rects'] = rects
    return out


_first: Counter = Counter()
_dalmatian: Counter = Counter()


def corpus() -> None:
    for f in glob.glob('website/public/*soldiers.json'):
        if not f.replace('\\', '/').endswith(OUT.split('/')[-1]):
            for s in json.load(open(f, encoding='utf-8')):
                _first[s['first_name']] += 1
    for f in ('2-dalmatinska-soldiers.json', '4-splitska-soldiers.json'):
        for s in json.load(open(f'website/public/{f}', encoding='utf-8')):
            _dalmatian[s['first_name']] += 1


def nominative(father: str) -> str:
    """The father's name: from a possessive ("Matin" → Mate, "Franin" → Frane, "Jurjev" → Juraj, "Marjanov" →
    Marjan) or a genitive ("Nikole" → Nikola, "Ivana" → Ivan), the form most common as a given name."""
    if not father or father.endswith('.'):
        return father
    father = {'Pavia': 'Pavla'}.get(father, father)                   # the scan reads "vl" as "vi"
    cands = {father, genitive_to_nominative(father)}
    if father.endswith('ina'):
        stem = father[:-3]                                                # a woman's "Antina", "Matina"
        cands |= {stem + 'e', stem + 'a', stem + 'o'}
    if father.endswith('in'):
        stem = father[:-2]
        cands |= {stem + 'e', stem + 'a', stem + 'o', stem}
    if re.search(r'[eo]v$', father):
        stem = father[:-2]
        cands |= {stem, stem + 'o', stem + 'a'}
        if stem.endswith('j'):
            cands.add(stem[:-1] + 'aj')                                   # Jurjev → Juraj
    if father.endswith('a'):
        cands |= {father[:-1], father[:-1] + 'o', father[:-1] + 'e'}
        if father.endswith('ja') and father[-3] not in 'aeiou':
            cands.add(father[:-2] + 'aj')                                 # Jurja → Juraj
    if father.endswith('e'):
        cands |= {father[:-1] + 'a', father[:-1] + 'o'}
    # by the Dalmatian books first: Mate, Ante, Šime stay so (the corpus at large says Mato)
    counts = _dalmatian if any(_dalmatian[c] for c in cands) else _first
    best = max(cands, key=lambda c: (counts[c], c == father))
    return best if counts[best] else father


TEXT_FIXES = {'Jerk ovi ć Torna': 'Jerković Toma', 'Jo<sip': 'Josip', '(Kilezović:)': '(Kilezović)', 'Mióo': 'Mićo',
              'Müovan': 'Milovan'}
# an entry the author put inside a sentence of his own: "... još se nalazi i bolničarka Mikulić Ana Antina. iz ..."
IN_PROSE = re.compile(rf'^U spisku poginulih još se nalazi i bolničarka (?=Mikulić)')


def record(item: dict) -> dict | None:
    words = [w for t in item['toks'] for w in t['words']]
    text = ' '.join(t['text'] for t in item['toks']).strip()
    text = re.sub(r'\s+([,.;])', r'\1', text)
    for a, b in TEXT_FIXES.items():
        text = text.replace(a, b)
    if IN_PROSE.match(text):
        text = IN_PROSE.sub('', text).replace('Antina. iz', 'Antina, bolničarka iz', 1)
    m = NAME.match(text)
    if not m:
        return None
    last, other_last, given, late, father, alias = m.groups()
    if given.endswith('.') and father and not father.endswith('.'):
        given, father = father, ''                                         # not expected; keep the name readable
    rest = text[m.end():].lstrip(' ,.')
    notes = []
    if other_last:
        notes.append('ili ' + re.sub(r'^ili\s+', '', other_last).rstrip('?'))   # "Tomazini (Tomašić)": another reading
    if alias:
        notes.append(f'ili {alias}')                                       # "Ftalis (Fleis)": another reading
    if father and father.endswith('.') and len(father) == 2:
        pass                                                               # "Ugrinović D." — an initial
    info = '; '.join(notes + [rest]) if rest else '; '.join(notes)
    father = {'Pavia': 'Pavla'}.get(father, father)                       # the scan reads "vl" as "vi"
    rec = _record(last, given, father or '', info)
    rec['fathers_name'] = nominative(father or '')
    # the death: its date with the heading's year where the entry gives none
    d = DEATH.search(rest)
    if d:
        dm = DATE.search(rest, d.end())
        if dm:
            day, month, year = dm.groups()
            year = year or heading_year(item['heading'])
            rec['death_date'] = f'{int(day)}. {int(month)}. {year}'.strip()
    rec.update(boxes(words))
    return rec


def main():
    corpus()
    lines = read_lines()
    its = items(tokens(lines))
    if '--items' in sys.argv:
        for it in its:
            print(it['heading'][:40], '|', it['sub'], '|', ' '.join(t['text'] for t in it['toks'])[:150])
        return
    soldiers, skipped = [], []
    prev = None
    for it in its:
        r = record(it)
        piece = ' '.join(t['text'] for t in it['toks'])
        if not r and prev and not prev[1]['additional_info'] and piece[:1].islower():
            # "Zlatar Petar; borac, prateći vod ...": a semicolon misprinted after the name
            comma = {'text': ',', 'words': []}
            joined = {'toks': prev[0]['toks'] + [comma] + it['toks'], 'heading': prev[0]['heading'], 'sub': prev[0]['sub']}
            rj = record(joined)
            if rj:
                soldiers[-1] = rj
                prev = (joined, rj)
                continue
        if r:
            soldiers.append(r)
            prev = (it, r)
        else:
            skipped.append(piece[:120])
    soldiers.sort(key=lambda s: (s['last_name'].lower(), s['first_name'].lower()))
    soldiers = assign_ids_to_soldiers(soldiers, CODE, 1)
    Path(OUT).write_text(json.dumps(soldiers, ensure_ascii=False, indent=2), encoding='utf-8')
    print(f'{len(soldiers)} soldiers → {OUT}; {len(skipped)} pieces without a name:')
    for s in skipped:
        print('   ', s)


if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    main()
