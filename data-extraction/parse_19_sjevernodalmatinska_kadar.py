"""
Parser: 19. sjevernodalmatinska divizija (brigade code 79) — its command, Politodjel and narodni heroji, a second list.

Source: Dragutin Grgurević, "Devetnaesta sjevernodalmatinska divizija" (znaci.org 00003/575.pdf, PDF pp. 244-256,
        book pp. 240-252, before its fallen on the site)  →  website/public/pdfs/19-sjevernodalmatinska-kadar.pdf:
    "Pregled komandnog kadra 19. divizije od formiranja do kraja rata": the commanders and political commissars of the
    division and of its 5., 6., 7. and 14. brigade, two columns, a name and under it how long he held the post:
        Ivos Šime
          Od formiranja do 20. XI 1943.
    the members of its Politodjel and the brigades' 1943-1945, given name first, run on ("Zdenka Šegvić, Vladan
    Bojanić, ..."); and the narodni heroji who served in it, a page each, the heading "BABIĆ Trifuna PETAR" over a
    summary (birth, trade, KPJ, NOB, the day proclaimed, his duties in the division) and his life, of which the summary
    is kept (the page has the rest).
A man in several posts, or in the table and among the heroes, is one record with each; the footnotes on how two men
died go to their posts. znaci re-typeset the book from its OCR, so the page shows its slips ("KOB" for NOB, "SRJ" for
SKJ, "Gli 8 e" for Gliše, "Kupresanin"); the heroes' headings are typed from the page. The fallen are the unit's first
list (IDs from 1); these get IDs from 10001.
"""
import re
import sys
from pathlib import Path

import pdfplumber

from _parser_scaffold import _record, run_parser
from pdf_coords import viewer_words

PDF = 'website/public/pdfs/19-sjevernodalmatinska-kadar.pdf'
SOURCE = Path(__file__).parent / '.cache' / 'znaci_photos' / 'books' / '00003_575.pdf'   # znaci.org 00003/575.pdf
FIRST_PAGE, LAST_PAGE = 244, 256
TABLE = 'Pregled komandnog kadra 19. divizije od formiranja do kraja rata'
POLITODJEL = 'Članovi Politodjela u diviziji i brigadama od 1943. do 1945. godine'
HEROES = 'Narodni heroji Jugoslavije, pripadnici 19. sjevernodalmatinske divizije'
U, L = 'A-ZČĆŽŠĐ', 'a-zčćžšđ'
SPLIT = {1: 315, 2: 285}                 # the table's two columns
FOOT_TOP = 640                           # the footnotes under the table and the Politodjel
# the heroes' headings, read from the page: (surname, father, given name, what he was called), and the father
HERO_NAMES = {5: ('Babić', 'Trifuna', 'Petar', ''), 6: ('Damjanović', 'Đure', 'Danilo', 'Danić'),
              7: ('Kuprešanin', 'Nikole', 'Milan', ''), 8: ('Opačić', 'Andrije', 'Stevan', ''),
              9: ('Opačić', 'Gliše', 'Stevan', ''), 10: ('Parmač', 'Ante', 'Stanko', ''),
              11: ('Popović', 'Jovana', 'Tomica', ''), 12: ('Radaković', 'Trifuna', 'Ilija', ''),
              13: ('Šakić', 'Ljubomira', 'Milan', 'Mićun')}
FATHERS = {'Trifuna': 'Trifun', 'Đure': 'Đuro', 'Nikole': 'Nikola', 'Andrije': 'Andrija', 'Gliše': 'Gliša',
           'Ante': 'Ante', 'Jovana': 'Jovan', 'Ljubomira': 'Ljubomir'}
# the table's names that are a hero's under another form, and the slips of the text layer
NAMES = {('Kupresanin', 'Milan'): ('Kuprešanin', 'Milan', ''), ('Šakić', 'Mićun'): ('Šakić', 'Milan', 'Mićun'),
         ('Ivos', 'Šime'): ('Ivas', 'Šime', ''), ('Bulat', 'Živojin Žiki'): ('Bulat', 'Živojin', 'Žiki')}
WORDS = [('godne', 'godine'), ('proglasen', 'proglašen'), ('SRJ', 'SKJ'), ('KOB', 'NOB'), ('Glan ', 'Član '),
         ('Roden', 'Rođen'), ('ža ', 'za ')]
# the footnotes on the men (the page's 3, 5 and 6)
FOOTNOTES = {('Bursać', 'Dušan'): 'Poginuo u borbama za oslobođenje Rijeke, u svibnju 1945.',
             ('Božović', 'Slavko'): 'Ubijen u zasjedi od ostataka ustaških bandi kod Plitvičkih jezera neposredno '
                                    'poslije rata. Tada je bio komesar divizije.',
             ('Čanković', 'Marko'): 'Poginuo 24. siječnja 1944. kao član Politodjela 5. brigade kod sela Lišane '
                                    '(Bukovica), gdje su njega i poručnika Miloša Uzelca ustaše sačekale u zasjedi '
                                    'i obojicu ubile.'}
POSTS: list = []


def cut_pdf() -> None:
    from pypdf import PdfReader, PdfWriter
    r, w = PdfReader(str(SOURCE)), PdfWriter()
    for i in range(FIRST_PAGE - 1, LAST_PAGE):
        w.add_page(r.pages[i])
    with open(PDF, 'wb') as f:
        w.write(f)


def rows_of(words: list[dict]) -> list[list[dict]]:
    rows: list = []
    for w in sorted(words, key=lambda w: (w['top'], w['x0'])):
        row = next((r for r in rows if abs(r[0]['top'] - w['top']) <= 3), None)
        (rows.append([w]) if row is None else row.append(w))
    return [sorted(r, key=lambda w: w['x0']) for r in sorted(rows, key=lambda r: r[0]['top'])]


def join(lines: list[str]) -> str:
    text = ''
    for ln in lines:
        text = text[:-1] + ln if text.endswith('-') and ln[:1].islower() else (text + ' ' + ln).strip()
    for a, b in WORDS:
        text = text.replace(a, b)
    return text


def duty_of(head: str) -> tuple[str, str]:
    """'KOMANDANT 14. »BUKOVAČKE« BRIGADE' -> ('komandant 14. »Bukovačke« brigade', '14. »Bukovačka« brigada')."""
    duty = re.sub(r'»(\w)(\w*)«', lambda m: '»' + m.group(1) + m.group(2).lower() + '«', head.lower())
    duty = re.sub(r'»(\w)', lambda m: '»' + m.group(1).upper(), duty)
    unit = re.search(r'(\d+\.(?: »\w+«)?) brigade', duty)
    if unit is None:
        return duty, 'Štab divizije'
    unit = unit.group(1).replace('ačke«', 'ačka«')
    return duty, ('14. »Bukovačka«' if unit == '14.' else unit) + ' brigada'


def name_of(last: str, given: str) -> tuple[str, str, str]:
    return NAMES.get((last, given), (last, given, ''))


def read_table(pdf, n: int) -> None:
    ws = [w for w in viewer_words(pdf.pages[n - 1]) if 300 < w['top'] < FOOT_TOP or n > 1 and w['top'] < FOOT_TOP]
    for side in (lambda w: w['x0'] < SPLIT[n], lambda w: w['x0'] >= SPLIT[n]):
        head, heads, post = '', False, None
        for r in rows_of([w for w in ws if side(w)]):
            text = ' '.join(w['text'] for w in r)
            if re.search(rf'[{U}]{{3}}', text) and not re.search(rf'[{L}]', text):   # "KOMANDANT 5. BRIGADE", "BRIGADE"
                head = (head + ' ' + text).strip() if heads else text
                heads = True
                continue
            heads = False
            clean = [re.sub(r'\d+$', '', w['text']) for w in r]                  # "Dušan3": a footnote's mark
            if 2 <= len(r) <= 3 and clean[0] != 'Od' and all(re.fullmatch(rf'[{U}][{L}]+', w) for w in clean):
                last, given, nick = name_of(clean[0], ' '.join(clean[1:]))
                duty, unit = duty_of(head)
                post = {'unit': unit, 'duty': duty, 'last': last, 'given': given, 'nick': nick, 'father': '',
                        'lines': [], 'page': n, 'words': r, 'section': TABLE}
                POSTS.append(post)
            elif post is not None:
                post['lines'].append(re.sub(r'(?<=[a-zčćžšđ.])\d$', '', text))   # "divizije4"
    for p in POSTS:
        if p['page'] == n and 'text' not in p:
            dates = join(p['lines'])
            dates = dates[:1].lower() + dates[1:]
            p['text'] = f"{p['duty']}, {dates}".rstrip('.')
            if (p['last'], p['given']) in FOOTNOTES:
                p['text'] += '. ' + FOOTNOTES[(p['last'], p['given'])].rstrip('.')


def read_politodjel(pdf, n: int) -> None:
    ws = [w for w in viewer_words(pdf.pages[n - 1]) if 205 < w['top'] < 400]            # the names, not the footnotes
    words = [w for r in rows_of(ws) for w in r]
    names, cur = [], []
    for w in words:
        t = re.sub(r'\d+$', '', w['text'].replace(',5', ',').replace(',6', ','))
        if t == 'i':                                                         # "Vrbica Migo i Ilija Mugoša."
            names.append(cur) if cur else None
            cur = []
            continue
        cur.append(w)
        if t.endswith((',', '.')) or len(cur) == 2 and w is words[-1]:
            names.append(cur)
            cur = []
    for ws_ in names:
        given, last = (re.sub(r'[\d,.]+$', '', w['text']) for w in ws_[:2])
        if (given, last) == ('Vrbica', 'Migo'):                               # printed surname first; the 6. brigade's list: Migo Vrbica
            given, last = last, given
        text = 'član Politodjela'
        if (last, given) in FOOTNOTES:
            text += '. ' + FOOTNOTES[(last, given)].rstrip('.')
        POSTS.append({'unit': 'Politodjel', 'duty': 'član Politodjela', 'last': last, 'given': given, 'nick': '',
                      'father': '', 'text': text, 'page': n, 'words': ws_, 'section': POLITODJEL})


def read_hero(pdf, n: int) -> None:
    rows = rows_of(viewer_words(pdf.pages[n - 1]))
    keep = [rows[0]]
    for r in rows[1:]:
        if r[0]['top'] - keep[-1][0]['top'] > 25 and len(keep) > 1:          # the gap before his life
            break
        keep.append(r)
    last, father, given, nick = HERO_NAMES[n]
    text = join([' '.join(w['text'] for w in r) for r in keep[1:]])
    POSTS.append({'unit': '', 'duty': '', 'last': last, 'given': given, 'nick': nick, 'father': father,
                  'text': 'narodni heroj; ' + text.rstrip('.'), 'page': n, 'words': [w for r in keep for w in r],
                  'section': HEROES})


def extract(pdf_path: str, start_page: int, end_page: int | None) -> list[dict]:
    with pdfplumber.open(pdf_path) as pdf:
        read_table(pdf, 1)
        read_table(pdf, 2)
        read_politodjel(pdf, 3)
        for n in HERO_NAMES:
            read_hero(pdf, n)
    return [{'text': '§§post' + str(i), 'x': round(p['words'][0]['x0'], 1), 'y': round(p['words'][0]['top'], 1),
             'page': p['page']} for i, p in enumerate(POSTS)]


def parse(text: str) -> dict:
    p = POSTS[int(text[6:])]
    rec = _record(p['last'], p['given'], p['father'], '')
    rec['_post'] = int(text[6:])
    if p['father']:
        rec['fathers_name'] = FATHERS[p['father']]
    return rec


def men(soldiers: list[dict]) -> list[dict]:
    """One record a man: a hero's table posts go to him unless two heroes have his name (the two Stevan Opačićs)."""
    heroes = {}
    for p in POSTS:
        if p['father']:
            heroes.setdefault((p['last'], p['given']), []).append(p['father'])
    out, seen = [], {}
    for s in soldiers:
        p = POSTS[s['_post']]
        name = (p['last'], p['given'])
        key = name + ((p['father'],) if len(heroes.get(name, ())) > 1 else ())
        man = seen.get(key)
        if man is None:
            man = seen[key] = s
            s['_sections'], s['_nicks'], s['_rects'] = {}, [], []
            s['unit_detail'] = p['unit']
            out.append(s)
        if p['father'] and not man['middle_name']:
            man['middle_name'], man['fathers_name'] = p['father'], FATHERS[p['father']]
        if not man.get('unit_detail') and p['unit']:
            man['unit_detail'] = p['unit']
        man['_sections'].setdefault(p['section'], []).append(p['text'])
        if p['nick'] and p['nick'] not in man['_nicks']:
            man['_nicks'].append(p['nick'])
        if p['page'] == man['pdf_page']:
            ws = p['words'] if p['section'] != TABLE else [w for w in p['words']]
            man['_rects'].append([round(min(w['x0'] for w in ws), 1), round(min(w['top'] for w in ws), 1),
                                  round(max(w['x1'] for w in ws), 1), round(max(w['bottom'] for w in ws), 1)])
    for s in out:
        parts = [f"{title}: {'; '.join(texts)}" for title, texts in s['_sections'].items()]
        s['additional_info'] = '; '.join([f'zvani {n}' for n in s['_nicks']] + ['. '.join(parts) + '.'])
        r = s['_rects']
        s['pdf_x'], s['pdf_y'], s['pdf_x_end'], s['pdf_y_end'] = r[0]
        if len(r) > 1:
            s['pdf_rects'] = r
        s['full_name'] = ' '.join(x for x in (s['last_name'], s['middle_name'], s['first_name']) if x)
        for k in ('_post', '_sections', '_nicks', '_rects'):
            s.pop(k)
    return out


if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    if not Path(PDF).exists():
        cut_pdf()
    run_parser(pdf_path=PDF, brigade_code=79, output_path=sys.argv[1] if len(sys.argv) > 1 else 'website/public/19-sjevernodalmatinska-soldiers.json',
               extract_fn=extract, entry_start_re=re.compile(r'^§§'), parse_entry_fn=parse, post_fn=men,
               id_start=10001, keep_other_sources=True)
