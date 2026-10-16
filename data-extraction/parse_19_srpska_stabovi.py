"""
Parser: 19. srpska brigada (brigade code 73) — its staffs, a second list in the unit's PDF.

Source: Predrag Pejčić, "19. srpska brigada", "Pregled sastava užeg dela Štaba 19. brigade i štabova bataljona"
        (book pp. 613-614, the last two pages of website/public/pdfs/19-srpska.pdf, its pp. 201-202), prepared by
        the brigade's veterans' section. Cyrillic; under the brigade staff and each battalion, a duty after a dash and
        its holders run on, given name first, a nickname after the surname, a note in brackets:
    - команданти: Миодраг Новаковић Џуџа; Димитрије Писковић Трнавац;
    - помоћници комесара: Светислав Поповић Тиле (уједно партијски руководилац 25. српске дивизије); ...
znaci re-typeset the book from its OCR, which reads Ђ as Б ("Бурђа", "Борђе") and Д, Л or С as А at a word's start
("Атојковић"); a name the unit's records don't know is read back where one of those readings is a record of the unit.
A man in several posts is one record with each; his box is around his name at each post on his first post's page.
The fallen and survivors are the unit's first list (IDs from 1); these get IDs from 10001.
"""
import json
import re
import sys
from pathlib import Path

import pdfplumber

from _parser_scaffold import _record, cyrillic_to_latin, run_parser
from pdf_coords import viewer_words

PDF = 'website/public/pdfs/19-srpska.pdf'
FIRST_PAGE, LAST_PAGE = 201, 202
TITLE = 'Pregled sastava užeg dela Štaba 19. brigade i štabova bataljona'
POSTS: list = []
# read from the page against the other units' records: "Borđe" is no name, Đukić Aleksa and Stojković Radomir are
WORDS = {'Borđe': 'Đorđe', 'Bukić': 'Đukić', 'Atojković': 'Stojković'}


def page_lines(page) -> list[list[dict]]:
    rows: list = []
    for w in sorted(viewer_words(page), key=lambda w: (w['top'], w['x0'])):
        w['text'] = cyrillic_to_latin(w['text'])
        row = next((r for r in rows if abs(r[0]['top'] - w['top']) <= 3), None)
        (rows.append([w]) if row is None else row.append(w))
    return [sorted(r, key=lambda w: w['x0']) for r in sorted(rows, key=lambda r: r[0]['top'])]


def read_posts(pdf_path: str) -> None:
    unit = duty = ''
    buf: list = []

    def flush():
        tokens, cur, depth = [], [], 0
        for w in buf:
            t = w['text']
            depth += t.count('(') - t.count(')')
            end = depth == 0 and re.search(r'[,;:.]$', t)
            cur.append({**w, 'text': t.rstrip(',;:.') if end else t})
            if end:
                tokens.append(cur)
                cur = []
        if cur:
            tokens.append(cur)
        for tok in tokens:
            text = ' '.join(w['text'] for w in tok).strip()
            note = ''
            m = re.search(r'\(([^)]*)\)\s*$', text)
            if m:
                note, text = m.group(1).strip(), text[:m.start()].strip()
                tok = [w for w in tok if not w['text'].startswith('(')][:len(text.split())]
            if text:
                POSTS.append({'unit': unit, 'duty': duty, 'name': text, 'note': note, 'page': tok[0]['page'], 'words': tok})
        buf.clear()

    with pdfplumber.open(pdf_path) as pdf:
        for n in range(FIRST_PAGE, LAST_PAGE + 1):
            stop = False
            for row in page_lines(pdf.pages[n - 1]):
                for w in row:
                    w['page'] = n
                t = ' '.join(w['text'] for w in row).strip()
                if re.match(r'^\d+"?\)\s*Pregled', t) or stop:                  # the footnote
                    stop = True
                    continue
                if re.fullmatch(r'\d{3}', t) or t.startswith('PREGLED') or t.startswith('19. BRIGADE'):
                    continue
                if t.startswith('Štab 19.') or re.fullmatch(r'\d\. bataljon', t):
                    flush()
                    unit = 'Štab brigade' if t.startswith('Štab') else t
                    continue
                m = re.match(r'^-\s*([^:]+?):\s*', t)
                if m:                                                        # "- komandanti: Miodrag Novaković ..."
                    flush()
                    duty = m.group(1).replace('zamenicn', 'zamenici')
                    k = next(i for i, w in enumerate(row) if ':' in w['text'])
                    row = row[k + 1:]
                if buf and buf[-1]['text'].endswith('-') and row and row[0]['text'][:1].islower():
                    last = buf.pop()
                    row = [{**row[0], 'text': last['text'][:-1] + row[0]['text'], 'split': last}] + row[1:]
                buf.extend(row)
            flush()


def extract(pdf_path: str, start_page: int, end_page: int | None) -> list[dict]:
    read_posts(pdf_path)
    first = [p['words'][0].get('split', p['words'][0]) for p in POSTS]
    return [{'text': '§§post' + str(i), 'x': round(f['x0'], 1), 'y': round(f['top'], 1), 'page': p['page']}
            for i, (p, f) in enumerate(zip(POSTS, first))]


def corpus() -> set:
    return {(s['last_name'], s['first_name']) for s in json.load(open('website/public/19-srpska-soldiers.json', encoding='utf-8'))
            if not s['soldier_id'].startswith('007301')}


KNOWN: set = set()


def read_back(word: str, given: bool, other: str) -> str:
    """Б for Ђ, А for Д, Л or С at a word's start, ћ for ђ: a reading the unit's records hold."""
    cands = [word]
    if word[:1] == 'B':
        cands.append('Đ' + word[1:])
    if word[:1] == 'A':
        cands += [x + word[1:] for x in ('D', 'L', 'S')]
    cands += [c.replace('ć', 'đ') for c in cands if 'ć' in c[:-2]]
    for c in cands:
        if ((other, c) if given else (c, other)) in KNOWN:
            return c
    return word


def parse(text: str) -> dict:
    p = POSTS[int(text[6:])]
    words = p['name'].split()
    title = ''
    if words[0] in ('dr', 'dr.'):
        title, words = 'dr.', words[1:]
    given, last, nick = words[0], (words[1] if len(words) > 1 else '?'), ' '.join(words[2:])
    given, last = WORDS.get(given, given), WORDS.get(last, last)
    given2 = read_back(given, True, read_back(last, False, given))
    last = read_back(last, False, given2)
    given = read_back(given, True, last)
    rec = _record(last, given, '', '')
    rec['_post'], rec['_nick'], rec['_title'] = int(text[6:]), nick, title
    return rec


def rects(words: list[dict]) -> list[list[float]]:
    lines: dict = {}
    for w in words:
        for part in ([w['split'], w] if 'split' in w else [w]):
            box = lines.setdefault(round(part['top']), [part['x0'], part['top'], part['x1'], part['bottom']])
            box[0], box[1] = min(box[0], part['x0']), min(box[1], part['top'])
            box[2], box[3] = max(box[2], part['x1']), max(box[3], part['bottom'])
    return [[round(v, 1) for v in b] for b in lines.values()]


def men(soldiers: list[dict]) -> list[dict]:
    out, seen = [], {}
    for s in soldiers:
        key = (s['last_name'], s['first_name'])
        man = seen.get(key)
        if man is None:
            man = seen[key] = s
            s['_posts'], s['_nicks'], s['_rects'] = [], [], []
            s['unit_detail'] = POSTS[s['_post']]['unit']
            out.append(s)
        p = POSTS[s['_post']]
        man['_posts'].append(f"{p['unit']}, {p['duty']}" + (f" ({p['note']})" if p['note'] else ''))
        if s['_nick'] and s['_nick'] not in man['_nicks']:
            man['_nicks'].append(s['_nick'])
        man['_title'] = man['_title'] or s['_title']
        if p['page'] == man['pdf_page']:
            man['_rects'] += rects(p['words'])
    for s in out:
        notes = ([s['_title']] if s['_title'] else []) + [f'zvani {n}' for n in s['_nicks']]
        s['additional_info'] = '; '.join(notes + [f"{TITLE}: {'; '.join(s['_posts'])}"])
        r = s['_rects']
        s['pdf_x'], s['pdf_y'], s['pdf_x_end'], s['pdf_y_end'] = r[0]
        if len(r) > 1:
            s['pdf_rects'] = r
        s['full_name'] = f"{s['last_name']} {s['first_name']}".strip()
        for k in ('_post', '_nick', '_title', '_posts', '_nicks', '_rects'):
            s.pop(k)
    return out


if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    KNOWN |= corpus()
    run_parser(pdf_path=PDF, brigade_code=73, output_path=sys.argv[1] if len(sys.argv) > 1 else 'website/public/19-srpska-soldiers.json',
               start_page=FIRST_PAGE, end_page=LAST_PAGE, extract_fn=extract, entry_start_re=re.compile(r'^§§'),
               parse_entry_fn=parse, post_fn=men, id_start=10001, keep_other_sources=True)
