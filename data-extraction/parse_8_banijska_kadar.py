"""
Parser: 8. banijska brigada (brigade code 45) — its command, a third list.

Source: Ljuban Đurić, *Osma banijska NOU brigada* (znaci.org 00003/383, its PDF pp. 241-243, book pp. 244-246)
        →  website/public/pdfs/8-banijska-kadar.pdf: "Pregled komandnog kadra u štabu brigade i komandama
        bataljona", the brigade staff, its Politodjel and the staffs of its five battalions, a duty and its men run on,
        given name first, what he was called after the surname:
    Komandanti: Stanko Bjelajac Ćane, Rade Grmuša Rara, Sava Miočinović,
    Janko Zebić.
        A star after a name marks the book's note on the list, not the man. A man in several posts is one record with
        each; his box is around his name at each post on his first post's page. Borci Sutjeske is the unit's first list
        (IDs from 1), the fallen from 10001; these get IDs from 20001.
"""
import re
import sys
from pathlib import Path

import pdfplumber

import parse_8_kordunaska_divizija as k8
from _parser_scaffold import _record, run_parser
from parse_2_dalmatinska_stabovi import rows_of
from pdf_coords import viewer_words

PDF = 'website/public/pdfs/8-banijska-kadar.pdf'
UNIT = 'website/public/8-banijska-soldiers.json'
SOURCE = Path(__file__).parent / '.cache' / 'znaci_photos' / 'books' / '00003_383.pdf'   # znaci.org 00003/383.pdf
PAGES = range(241, 244)
TITLE = 'Pregled komandnog kadra 8. banijske brigade'
BATS = {'prvi': 1, 'drugi': 2, 'treći': 3, 'četvrti': 4, 'peti': 5}
WORDS = [(r'\bkomandanti\b', 'komandant'), (r'\bkomesari\b', 'komesar'), (r'\bzamjenici\b|\bzemjenik\b', 'zamjenik'),
         (r'\bnačelnici\b', 'načelnik'), (r'\boficiri\b', 'oficir'), (r'\bintendanti\b', 'intendant'),
         (r'\breferenti\b', 'referent'), (r'\bsekretari\b', 'sekretar'), (r'\bomladinski rukovodioci\b', 'omladinski rukovodilac'),
         (r'^rukovodioci\b', 'rukovodilac'), (r'^članovi ?politodjela\b', 'član'), (r' brigade$', '')]
FIX = {'Medie': 'Medić', 'Sukrija': 'Šukrija', 'Zivko': 'Živko', 'Debeljek': 'Debeljak',   # the text layer's slips,
       'Radenović': 'Rađenović'}                                         # read from the page
# printed surname first, or a double surname: the words -> (given, surname, nick)
ITEMS = {('Joka', 'Ignjatija'): ('Ignjatija', 'Joka', ''), ('Vera', 'Cvetković', 'Majer'): ('Vera', 'Cvetković-Majer', '')}
LABEL = re.compile(r'^([A-ZČĆŽŠĐ][a-zčćžšđ]+(?: ?[a-zčćžšđA-Z-]+){0,2}):\s*(.*)$')
POSTS: list = []


def cut_pdf() -> None:
    from pypdf import PdfReader, PdfWriter
    r, w = PdfReader(str(SOURCE)), PdfWriter()
    for i in PAGES:
        w.add_page(r.pages[i - 1])
    with open(PDF, 'wb') as f:
        w.write(f)


def singular(label: str) -> str:
    t = label.strip()
    t = t[:1].lower() + t[1:]
    for p, d in WORDS:
        t = re.sub(p, d, t)
    return t


def read_posts(pdf_path: str) -> None:
    with pdfplumber.open(pdf_path) as pdf:
        lines = [(n, r) for n, page in enumerate(pdf.pages, 1)
                 for r in rows_of([{**w, 'page': n} for w in viewer_words(page)])]
    unit, of, duty, run = 'Štab brigade', 'brigade', '', []
    groups = []                                                          # (unit, of, duty, words)

    def close():
        if duty and run:
            groups.append((unit, of, duty, list(run)))

    for n, r in lines:
        t = ' '.join(w['text'] for w in r)
        if t.startswith('Pregled komandnog') or t == 'i komandama bataljona':
            continue
        b = re.match(r'^(Prvi|Drugi|Treći|Četvrti|Peti) bataljon$', t)
        if t in ('Štab brigade', 'Politodjel brigade') or b:
            close()
            duty, run = '', []
            if b:
                k = BATS[b.group(1).lower()]
                unit, of = f'{k}. bataljon', f'{k}. bataljona'
            else:
                unit, of = t, 'brigade' if t == 'Štab brigade' else 'Politodjela brigade'
            continue
        if t.startswith('(') and duty == '':                             # the battalion's time ("(od septembra 1943.")
            of = f"{of} {t.replace(' - ', ' — ').rstrip('.')}"
            continue
        m = LABEL.match(t.replace('Komesari:Dušan', 'Komesari: Dušan').replace('Članovipolitodjela', 'Članovi politodjela'))
        if m:
            close()
            duty, run = singular(m.group(1)), []
            k = len(m.group(1).split())
            run = r[k:] if not r[k - 1]['text'].endswith(':') or len(r) > k else []
            if r[0]['text'] in ('Komesari:Dušan', 'Članovipolitodjela:'):
                run = r[1:] if r[0]['text'] == 'Članovipolitodjela:' else [{**r[0], 'text': 'Dušan'}] + r[1:]
            continue
        run += r
    close()
    for unit_, of_, duty_, ws in groups:
        post = f'{duty_} {of_}' if duty_ not in ('rukovodilac', 'član') else f'{duty_} Politodjela brigade'
        for item in items(ws):
            texts = [FIX.get(x['text'].strip(',.;*"\' '), x['text'].strip(',.;*"\' ')) for x in item]
            texts = [x for x in texts if x]
            title = 'dr' if texts[:1] == ['dr'] else ''
            texts = texts[1:] if title else texts
            extra = ' '.join(x for x in texts if x.startswith('('))
            texts = [x for x in texts if not x.startswith('(')]
            father = next((x for x in texts if re.fullmatch(r'[A-ZČĆŽŠĐ]', x)), '')   # "Milan I. Cvetojević"
            texts = [x for x in texts if x != father]
            father = father + '.' if father else ''
            if not texts:
                continue                                                 # a star or a quote mark alone
            if not all(re.fullmatch(r'[A-ZČĆŽŠĐ][a-zčćžšđ]+', x) for x in texts):
                print(f'  not a name: {texts!r}')
                continue
            if len(texts) == 4:                                          # "Nikola Kreća Rade Bomeštar.": two men
                for g, l in ((texts[0], texts[1]), (texts[2], texts[3])):
                    POSTS.append({'given': g, 'last': l, 'nick': '', 'father': '', 'title': '', 'note': '', 'post': post,
                                  'unit': unit_, 'page': item[0]['page'], 'words': item})
                continue
            given, last, nick = ITEMS.get(tuple(texts)) or ((texts[0], texts[1], ' '.join(texts[2:])) if len(texts) > 1
                                                            else ('', texts[0], ''))
            if extra == '(Talijan)':                                     # "Giloramo (Talijan)": a given name
                given, last = '', texts[0]
            POSTS.append({'given': given, 'last': last, 'nick': nick, 'father': father, 'title': title,
                          'note': 'Talijan' if extra == '(Talijan)' else '', 'post': post, 'unit': unit_,
                          'page': item[0]['page'], 'words': item})


def items(ws: list[dict]) -> list[list[dict]]:
    out, cur = [], []
    for w in ws:
        t = w['text']
        if t in ('i', '"', '-'):
            continue
        cur.append(w)
        if re.search(r'[,.;]\*?$|\*$', t) and not re.fullmatch(r'[A-ZČĆŽŠĐ]\.', t):
            out.append(cur)
            cur = []
    if cur:
        out.append(cur)
    return out


def extract(pdf_path: str, start_page: int, end_page: int | None) -> list[dict]:
    k8.corpus()
    read_posts(pdf_path)
    return [{'text': '§§post' + str(i), 'x': round(p['words'][0]['x0'], 1), 'y': round(p['words'][0]['top'], 1),
             'page': p['page']} for i, p in enumerate(POSTS)]


def parse(text: str) -> dict:
    p = POSTS[int(text[6:])]
    rec = _record(p['last'], p['given'], p['father'], '')
    rec['_post'] = int(text[6:])
    return rec


def men(soldiers: list[dict]) -> list[dict]:
    out, seen = [], {}
    for s in soldiers:
        p = POSTS[s['_post']]
        key = (k8.fold(p['last']), k8.fold(p['given']))
        man = seen.get(key)
        if man is None:
            man = seen[key] = s
            s['_posts'], s['_nicks'], s['_rects'], s['_notes'] = [], [], [], []
            s['unit_detail'] = p['unit']
            out.append(s)
        if p['father'] and not man.get('middle_name'):
            man['middle_name'] = p['father']
        if p['post'] not in man['_posts']:
            man['_posts'].append(p['post'])
        if p['nick'] and p['nick'] not in man['_nicks']:
            man['_nicks'].append(p['nick'])
        for x in (p['title'], p['note']):
            if x and x not in man['_notes']:
                man['_notes'].append(x)
        if p['page'] == man['pdf_page']:
            for line in rows_of(p['words']):                            # a name broken over two lines
                man['_rects'].append([round(min(w['x0'] for w in line), 1), round(min(w['top'] for w in line), 1),
                                      round(max(w['x1'] for w in line), 1), round(max(w['bottom'] for w in line), 1)])
    for s in out:
        s['additional_info'] = '; '.join(s['_notes'] + [f'zvani {n}' for n in s['_nicks']]
                                         + [f"{TITLE}: {'; '.join(s['_posts'])}."])
        r = s['_rects']
        s['pdf_x'], s['pdf_y'], s['pdf_x_end'], s['pdf_y_end'] = r[0]
        if len(r) > 1:
            s['pdf_rects'] = r
        s['full_name'] = ' '.join(x for x in (s['last_name'], s['middle_name'], s['first_name']) if x)
        for k in ('_post', '_posts', '_nicks', '_rects', '_notes'):
            s.pop(k)
    return out


if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    if not Path(PDF).exists():
        cut_pdf()
    run_parser(pdf_path=PDF, brigade_code=45, output_path=sys.argv[1] if len(sys.argv) > 1 else UNIT,
               extract_fn=extract, entry_start_re=re.compile(r'^§§'), parse_entry_fn=parse, post_fn=men,
               id_start=20001, keep_other_sources=True)
