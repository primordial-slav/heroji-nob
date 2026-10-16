"""
Parser: 3. primorsko-goranska brigada (brigade code 99) — its staffs, a second list.

Source: Bogdan Mamula, "Treća primorsko-goranska brigada", Prilog broj 2, "Spisak članova Štaba brigade, štabova
        bataljona i starješina samostalnih jedinica" (znaci.org 00001/122_5.pdf, PDF pp. 8-14, book pp. 227-233, just
        before the list of its officers and company medics and of its fallen on the site)  →
        website/public/pdfs/3-primorsko-goranska-stabovi.pdf.
Under the brigade staff (a duty a heading), its attached units and each battalion (a duty with a colon), each holder
of a post with the time he held it and how it ended, given name first, the surname and a nickname in capitals:
    Komandanti
    Gojko TRBOVIĆ ĆOŠAN, od formiranja do 8. novembra 1943. godine
    Komandiri: Božo GRKINIĆ i Stevo MILEUSNIĆ
    Zamjenici komandanata i operativni oficiri: Franjo ČOR, zamjenik od formiranja brigade do pogibije ...
A man in several posts is one record with each; his box is around his name at each post on his first post's page.
The officers and medics and the fallen are the unit's first list (IDs from 1); these get IDs from 10001.
"""
import re
import sys
from pathlib import Path

import pdfplumber

from _parser_scaffold import _record, run_parser
from pdf_coords import viewer_words

PDF = 'website/public/pdfs/3-primorsko-goranska-stabovi.pdf'
SOURCE = Path(__file__).parent / '.cache' / 'znaci_photos' / 'books' / '00001_122_5.pdf'   # znaci.org 00001/122_5.pdf
FIRST_PAGE, LAST_PAGE = 8, 14
TITLE = 'Spisak članova Štaba brigade, štabova bataljona i starješina samostalnih jedinica'
U, L = 'A-ZČĆŽŠĐ', 'a-zčćžšđ'
# the text layer's slips, read from the page and the list of officers after it
WORDS = [('KAD AK', 'KADAK'), ('SAB AN', 'ŠABAN'), ('ORLO VIĆ', 'ORLOVIĆ'), ('ORLOVIC', 'ORLOVIĆ'), ('Bozo ', 'Božo '),
         ('Duro ', 'Đuro '), ('Đmitar', 'Dmitar'), ('Đorde ', 'Đorđe '), ('GRGZRIĆ', 'GRGURIĆ'), ('PLECAŠ', 'PLEĆAŠ'),
         ('Ivan, PULJANIĆ', 'Ivan PULJANIĆ'), ('KNEŽEVIĆ^', 'KNEŽEVIĆ,'), ('SVARC', 'ŠVARC'), ('godine^', 'godine'),
         ('IVOŠEVIĆ LAZIĆ', 'IVOŠEVIĆ-LAZIĆ'), ('Milka MARIC', 'Milka MARIĆ'), ('RA- JAČIĆ', 'RAJAČIĆ'),
         ('Filipe Contte dr Rafaelle', 'Contte FILIPE RAFAELLE'), ('Cicognoni Terze Guerinno', 'Guerinno CICOGNONI TERZE'),
         ('Martin ROŠIĆ - Franjo MIČIĆ', 'Martin ROŠIĆ, Franjo MIČIĆ'), ('DOJČ ACO', 'DOJČ ACO')]
UNITS = {'Štab brigade': 'Štab brigade', 'Samostalne jedinice': 'Samostalne jedinice', 'Prvi bataljon': 'Prvi bataljon',
         'Drugi bataljon': 'Drugi bataljon', 'Treći bataljon': 'Treći bataljon', 'Četvrti bataljon': 'Četvrti bataljon',
         'Peti bataljon': 'Peti bataljon'}
SUBUNITS = {'Sanitetski vod', 'Higijeničarke', 'Intendantura', 'Kancelarija štaba', 'Prateća četa', 'Četa za vezu',
            'Pionirski vod', 'Izviđački vod'}
NAME = re.compile(rf'(?<![{U}{L}])([{U}][{L}]+(?:\s+[{U}]\.)?)\s+([{U}]{{2,}}(?:-[{U}]{{2,}})?(?:\s+[{U}]{{2,}})*)(?![{L}])')
LABEL = re.compile(rf'(?:^|(?<=\s))([{U}][{L}]+(?:\s+[{L}]+){{0,6}}|komandiri):\s*')
POSTS: list = []


def cut_pdf() -> None:
    from pypdf import PdfReader, PdfWriter
    r, w = PdfReader(str(SOURCE)), PdfWriter()
    for i in range(FIRST_PAGE - 1, LAST_PAGE):
        w.add_page(r.pages[i])
    with open(PDF, 'wb') as f:
        w.write(f)


def page_lines(page) -> list[list[dict]]:
    rows: list = []
    for w in sorted(viewer_words(page), key=lambda w: (w['top'], w['x0'])):
        row = next((r for r in rows if abs(r[0]['top'] - w['top']) <= 3), None)
        (rows.append([w]) if row is None else row.append(w))
    return [sorted(r, key=lambda w: w['x0']) for r in sorted(rows, key=lambda r: r[0]['top'])]


def read_posts(pdf_path: str) -> None:
    """Each duty's text as one stream of words across its lines, so a name broken over a line is still one."""
    unit, sub, duty = '', '', ''
    stream: list = []                                                        # (word dict) since the last heading

    def flush():
        nonlocal duty
        if not stream:
            return
        text, spans = '', []
        for w in stream:
            if text:
                text += ' '
            spans.append((len(text), len(text) + len(w['text']), w))
            text += w['text']
        for a, b in WORDS:                                                   # same length or not: re-find words after
            text = text.replace(a, b)
        text = re.sub(r'\?\?f\)', '', text)

        def words_at(i: int, j: int) -> list:
            ws, pos = [], 0
            for w in stream:                                                 # by the words' order, not their offsets
                k = text.find(w['text'][:3], pos)
                if k < 0:
                    continue
                if i <= k < j:
                    ws.append(w)
                pos = k + 1
            return ws

        pieces, last = [], 0
        for m in LABEL.finditer(text):
            if NAME.match(text, m.start()):
                continue
            pieces.append((last, m.start(), None))
            pieces.append((m.start(), m.end(), m.group(1)))
            last = m.end()
        pieces.append((last, len(text), None))
        for a, b, label in pieces:
            if label:
                duty = label[:1].upper() + label[1:]
                continue
            seg = text[a:b]
            names = list(NAME.finditer(seg))
            for i, m in enumerate(names):
                end = names[i + 1].start() if i + 1 < len(names) else len(seg)
                detail = re.sub(r'\s*\bi$', '', seg[m.end():end].strip(' ,')).strip(' ,.')
                ws = words_at(a + m.start(), a + m.end()) or stream[:1]
                POSTS.append({'unit': unit, 'sub': sub, 'duty': duty, 'given': m.group(1), 'caps': m.group(2).split(),
                              'detail': detail, 'page': ws[0]['page'], 'words': ws})
        stream.clear()

    with pdfplumber.open(pdf_path) as pdf:
        for n, page in enumerate(pdf.pages, 1):
            for row in page_lines(page):
                text = ' '.join(w['text'] for w in row).strip()
                if re.fullmatch(r'\?\?f\)|\d{3}|Prilog broj 2', text) or text.startswith('Spisak članova')                         or text in ('štabova bataljona i starješina', 'samostalnih jedinica'):
                    continue
                if text in UNITS or text == 'Štabovi bataljona':
                    flush()
                    unit, sub, duty = UNITS.get(text, unit), '', ''
                    continue
                if text in SUBUNITS:
                    flush()
                    sub, duty = text, ''
                    continue
                if re.fullmatch(rf'[{U}][{L}]+(?:\s+[{L}]+)*', text) and not NAME.search(text):
                    flush()
                    duty = text                                              # "Komandanti", "Zamjenici komandanta"
                    continue
                for w in row:
                    w['page'] = n
                if stream and stream[-1]['text'].endswith('-') and row[0]['text'][:1].islower():
                    last = stream.pop()                                      # "RA-" / "JAČIĆ" is handled by WORDS
                    row = [{**row[0], 'text': last['text'][:-1] + row[0]['text']}] + row[1:]
                stream.extend(row)
            flush()


def extract(pdf_path: str, start_page: int, end_page: int | None) -> list[dict]:
    read_posts(pdf_path)
    return [{'text': '§§post' + str(i), 'x': round(p['words'][0]['x0'], 1), 'y': round(p['words'][0]['top'], 1),
             'page': p['page']} for i, p in enumerate(POSTS)]


def parse(text: str) -> dict:
    p = POSTS[int(text[6:])]
    given = p['given']
    initial = ''
    m = re.match(rf'^([{U}][{L}]+)\s+([{U}]\.)$', given)
    if m:
        given, initial = m.group(1), m.group(2)
    last = p['caps'][0].title()
    nick = ' '.join(c.title() for c in p['caps'][1:])
    rec = _record(last, given, initial, '')
    rec['fathers_name'] = ''                                                 # an initial is no father's name
    rec['_post'], rec['_nick'] = int(text[6:]), nick
    return rec


def post_text(p: dict) -> str:
    where = ', '.join(x for x in (p['unit'], p['sub']) if x)
    duty = p['duty'][:1].lower() + p['duty'][1:] if p['duty'] else ''
    return ', '.join(x for x in (where, duty, p['detail'].rstrip('.')) if x)


def men(soldiers: list[dict]) -> list[dict]:
    """One record a man; one name with two nicknames is two men (Gostović Mile Crni and Mile Mali)."""
    nicks: dict = {}
    for s in soldiers:
        if s['_nick']:
            nicks.setdefault((s['last_name'], s['first_name']), set()).add(s['_nick'])
    two = {k for k, v in nicks.items() if len(v) > 1}
    out, seen = [], {}
    for s in soldiers:
        key = (s['last_name'], s['first_name']) + ((s['_nick'],) if (s['last_name'], s['first_name']) in two else ())
        man = seen.get(key)
        if man is None:
            man = seen[key] = s
            s['_posts'], s['_nicks'], s['_rects'] = [], [], []
            p = POSTS[s['_post']]
            s['unit_detail'] = ', '.join(x for x in (p['unit'], p['sub']) if x)
            out.append(s)
        p = POSTS[s['_post']]
        man['_posts'].append(post_text(p))
        if s['_nick'] and s['_nick'] not in man['_nicks']:
            man['_nicks'].append(s['_nick'])
        man['middle_name'] = man['middle_name'] or s['middle_name']
        if p['page'] == man['pdf_page']:
            ws = p['words']
            man['_rects'].append([round(min(w['x0'] for w in ws), 1), round(min(w['top'] for w in ws), 1),
                                  round(max(w['x1'] for w in ws), 1), round(max(w['bottom'] for w in ws), 1)])
    for s in out:
        notes = [f'zvani {n}' for n in s['_nicks']]
        s['additional_info'] = '; '.join(notes + [f"{TITLE}: {'; '.join(s['_posts'])}"])
        r = s['_rects']
        s['pdf_x'], s['pdf_y'], s['pdf_x_end'], s['pdf_y_end'] = r[0]
        if len(r) > 1:
            s['pdf_rects'] = r
        s['full_name'] = f"{s['last_name']} {s['first_name']}".strip()
        for k in ('_post', '_nick', '_posts', '_nicks', '_rects'):
            s.pop(k)
    return out


if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    if not Path(PDF).exists():
        cut_pdf()
    run_parser(pdf_path=PDF, brigade_code=99, output_path=sys.argv[1] if len(sys.argv) > 1 else 'website/public/3-primorsko-goranska-soldiers.json',
               extract_fn=extract, entry_start_re=re.compile(r'^§§'), parse_entry_fn=parse, post_fn=men,
               id_start=10001, keep_other_sources=True)
