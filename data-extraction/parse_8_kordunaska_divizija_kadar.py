"""
Parser: 8. kordunaška divizija (brigade code 60) — its command, a second list.

Source: "Osma kordunaška udarna divizija", Zbornik Historijskog arhiva u Karlovcu, knj. 9 (znaci.org 00003/571.pdf, PDF
        pp. 799-812, book pp. 762-775), Ignjatije Perić, "Pregled komandnog kadra Osme udarne divizije"  →
        website/public/pdfs/8-kordunaska-divizija-kadar.pdf: the commanders, political commissars and chiefs of staff
        of the division, the commanders, commissars, their deputies and the chiefs of staff of its brigades, and the
        commanders and commissars of their battalions, a table under each staff and duty, given name first:
    Red. broj   IME I PREZIME   Bio na dužnosti od   do   Napomena
    1.          Vlado Cetković  21. 11. 1942.        decembra 1943.   Narodni heroj, poginuo 1944. g. kao komandant 8. korpusa.
The Karlovačka brigade's staff (a duty and a name a line) and the Muslimanska brigade's (March-May 1945; its
battalions' commanders and commissars run on) are typed from the page. A man in several posts is one record with
each; the table's cells are read by their column (relative to the row numbers' column, which moves from page to page).
The text layer loses carons on capitals ("Cetković", "Sumonja", "Stab"), which come back from the corpus. Two men the
table says went over to the Chetniks (Đuro Šušnjar, Milan Basta) get no record. The fallen are the unit's first list
(IDs from 1); these get IDs from 10001.
"""
import re
import sys
from pathlib import Path

import pdfplumber

import parse_8_kordunaska_divizija as k8
from _parser_scaffold import _record, run_parser
from pdf_coords import viewer_words

PDF = 'website/public/pdfs/8-kordunaska-divizija-kadar.pdf'
SOURCE = Path(__file__).parent / '.cache' / 'znaci_photos' / 'books' / '00003_571.pdf'   # znaci.org 00003/571.pdf
FIRST_PAGE, LAST_PAGE = 799, 812
TITLE = 'Pregled komandnog kadra Osme udarne divizije'
# the staffs' headings, and the brigade a battalion's heading belongs to
STAFFS = {'Štab Osme udarne divizije': 'Štab divizije', 'Štab Prve udarne brigade': 'Prva udarna brigada',
          'Štab Druge udarne brigade': 'Druga udarna brigada', 'Štab Treće udarne brigade': 'Treća udarna brigada'}
# the text layer's slips in names, read from the page and the book's other pages
NAME_FIXES = {'Sumonja': 'Šumonja', 'Moj sije': 'Mojsije', 'Os to ja': 'Ostoja', 'Potkraj ac': 'Potkrajac', 'šušnjar': 'Šušnjar',
              'Mušan Miljković': 'Dušan Miljković', 'Sime Balen': 'Šime Balen', 'Ilija-Ico': 'Ilija'}
NICKNAMES = {'Ilija Kosanović': 'Ico'}                     # "Ilija-Ico Kosanović"
WENT_OVER = {('Šušnjar', 'Đuro'), ('Basta', 'Milan')}      # "Prešao u četnike 1944.", "prešao četnicima"
NUMBER = re.compile(r'^(?:\d{1,2}|U)\.$')                  # "U." is the text layer's 11.
# the Karlovačka brigade's staff, a duty and a name a line: (unit, duty, given, surname, note)
KARLOVACKA = [('Karlovačka brigada', 'komandant', 'Franjo', 'Molek', 'poginuo kao komandant brigade 1944. godine'),
              ('Karlovačka brigada', 'komesar', 'Petar', 'Erdeljac', 'umro 1976. godine'),
              ('Karlovačka brigada', 'zamjenik komesara', 'Rafko', 'Tabor', ''),
              ('Karlovačka brigada', 'operativni oficir', 'Nikola', 'Oreščanin', 'poginuo u toku NOR-a'),
              ('Karlovačka brigada, Prvi bataljon', 'komandant', 'Joža', 'Bestić', 'poginuo na Žumberku'),
              ('Karlovačka brigada, Prvi bataljon', 'komesar', 'Dane', 'Gašparević', ''),
              ('Karlovačka brigada, Drugi bataljon', 'komandant', 'Bruno', 'Belavić', ''),
              ('Karlovačka brigada, Drugi bataljon', 'komesar', 'Joža', 'Kasumčić', 'poginuo 1944. godine'),
              ('Karlovačka brigada, Treći bataljon', 'komandant', 'Ivan', 'Graho', ''),
              ('Karlovačka brigada, Treći bataljon', 'komesar', 'Stanko', 'Rudman', ''),
              ('Karlovačka brigada, Četvrti bataljon', 'komandant', 'Sulejman', 'Vasarac', 'poginuo poslije rata'),
              ('Karlovačka brigada, Četvrti bataljon', 'komesar', 'Ivan', 'Zunac', 'poginuo u toku rata na Žumberku')]
# the Muslimanska brigade's: (unit, duty, given, surname, from, to, note)
MB = 'Muslimanska brigada'
MUSLIMANSKA = [(MB, 'komandanti brigade', 'Zuhdija', 'Zalić', 'početkom marta 1945.', '23. marta 1945.', 'Umro poslije rata'),
               (MB, 'komandanti brigade', 'Tana', 'Ahmetović', '24. 3. 1945.', 'početkom aprila 1945.', 'Poginuo kod Rakovice'),
               (MB, 'komandanti brigade', 'Šulja', 'Vascarac', 'početkom aprila 1945.', 'konca rata', 'Umro poslije rata'),
               (MB, 'politički komesari brigade', 'Rasim', 'Delić', 'početkom marta 1945.', '23. 3. 1945.', 'Poginuo u Bihaću'),
               (MB, 'politički komesari brigade', 'Ismet', 'Arnautović', '24. 3. 1945.', 'konca rata', ''),
               (MB, 'zamjenici političkih komesara', 'Ćamil', 'Salihodžić', 'početkom marta 1945.', '23. 3. 1945.', 'Poginuo u Bihaću'),
               (MB, 'zamjenici političkih komesara', 'Bajazid', 'Bakalović', '25. 3. 1945.', 'konca rata', 'Pukovnik u penziji'),
               (MB, 'zamjenici komandanta brigade', 'Hasica', 'Veljačić', 'početkom marta 1945.', '', 'Poginuo kod Rakovice'),
               (MB, 'zamjenici komandanta brigade', 'Dušan', 'Tepšić', '10. 4. 1945.', 'konca rata', ''),
               (MB, 'operativni oficir brigade', 'Ahmet', 'Milović', 'početkom marta 1945.', 'konca rata', ''),
               (MB, 'komandanti bataljona', 'Bego', 'Seferagić', '', '', ''), (MB, 'komandanti bataljona', 'Avdo', 'Siljić', '', '', ''),
               (MB, 'komandanti bataljona', 'Ahmo', 'Hodžić', '', '', ''), (MB, 'komandanti bataljona', 'Ćazim', 'Suljić', '', '', ''),
               (MB, 'komesari bataljona', 'Fuad', 'Redžić', '', '', ''), (MB, 'komesari bataljona', 'Izet', 'Omanović', '', '', ''),
               (MB, 'komesari bataljona', 'Hamdija', 'Zuljević', '', '', ''), (MB, 'komesari bataljona', 'Mustafa', 'Hadžisevdić', '', '', '')]
PRINTED = {'Delić': 'Delie'}                               # the page's spelling, to find the name's words
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


def cells(text_lines: list[str]) -> str:
    text = ''
    for ln in text_lines:
        if text.endswith('-') and ln[:1].islower():                           # "zarob-" / "ljen"
            text = text[:-1] + ln
        elif text.endswith('-') and ln[:1] == '-':                            # "general-" / "-major"
            text = text + ln.lstrip('-')
        else:
            text = (text + ' ' + ln).strip()
    text = re.sub(r'(\w)\s+-\s*-?(?=[a-zčćžšđ])', r'\1-', text)              # "general -" / "-major", "general - -major"
    return re.sub(r'\s+\.', '.', text).lstrip('.')                           # "1945 .", ".Narodni heroj"


def add_carons(word: str, field: str) -> str:
    """The corpus's spelling where the text layer lost a caron ("Cetković", "Sapić"), never one that takes a caron away
    or changes one ("Zjača", "Bučan" stay)."""
    best = k8.respell(word, field)
    if len(best) != len(word) or any(a != b and not (a in 'cszCSZ' and b in 'čćšžČĆŠŽ') for a, b in zip(word, best)):
        return word
    return best


def name_of(words: list[str]) -> tuple[str, str, str]:
    """'Vlado Cetković' -> ('Ćetković', 'Vlado', ''); 'Miloš Madžar-Lošo' keeps its hyphen, as the book prints it."""
    name = ' '.join(words).replace('- ', '-')
    for a, b in NAME_FIXES.items():
        name = name.replace(a, b)
    given, _, last = name.partition(' ')
    given, last = add_carons(given, 'first_name'), add_carons(last, 'last_name')
    return last, given, NICKNAMES.get(f'{given} {last}', '')


def finish(p: dict) -> None:
    last, given, nick = name_of(p['name'])
    p.update(last=last, given=given, nick=nick)
    frm, to, note = (re.sub(r'\bU\.', '11.', cells(p[k])).replace('1S43', '1943').replace('Zumberk', 'Žumberk')
                     for k in ('from', 'to', 'note'))
    m = re.match(r'^(.*\d{4}\.)(\d{1,2}\.)$', frm)                             # "15. 11. 1942.15." / "12. 1942."
    if m:
        frm, to = m.group(1), f'{m.group(2)} {to}'
    to = re.sub(r'^do\s+', '', to)
    when = ' '.join(x for x in (f'od {frm}' if frm else '', f'do {to}' if to else '') if x)
    p['text'] = ', '.join(x for x in (p['unit_head'], p['duty'], when) if x).rstrip('.') + (f'. {note[:1].upper()}{note[1:].rstrip(".")}' if note else '')


def read_table(pdf) -> None:
    unit_head, unit, duty, post = 'Štab Osme udarne divizije', 'Štab divizije', 'komandanti divizije', None   # page 1's headings stand above the table's
    for n, page in enumerate(pdf.pages, 1):
        rows = rows_of(viewer_words(page))
        nums = [r[0] for r in rows if NUMBER.match(r[0]['text']) and len(r) > 2 and r[1]['text'][:1].isupper()]
        if not nums:
            continue
        nx = sorted(w['x0'] for w in nums)[len(nums) // 2]
        for r in rows:
            text = ' '.join(w['text'] for w in r)
            if re.match(r'^[SŠ]tab Karlovačke', text):                         # the typed part (read_typed)
                return
            if n == 1 and r[0]['top'] < 580 or re.fullmatch(r'\d{3}|\d+ Zbornik 9( \d+)?', text):
                continue
            if NUMBER.match(r[0]['text']) and r[0]['x0'] < nx + 10 and len(r) > 1:     # "9.", "10." (flush right), a heading never
                post = {'unit': unit, 'unit_head': unit_head, 'duty': duty, 'name': [], 'from': [], 'to': [], 'note': [],
                        'page': n, 'words': []}
                POSTS.append(post)
                ws = r[1:]
            elif r[0]['x0'] < nx - 3:                                        # a heading
                post = None
                head = text.replace('Stab ', 'Štab ').replace('štab a', 'štaba').replace(' «', '«').rstrip("'")
                if head.endswith(':'):
                    duty = head[:-1][:1].lower() + head[1:-1]
                elif head in STAFFS:
                    unit_head, unit = head, STAFFS[head]
                else:                                                         # "Prvi bataljon Prve udarne brigade"
                    brigade = unit.split(',')[0]
                    unit = unit_head = f"{brigade}, {re.sub(r' Prve udarne brigade$', '', head)}"
                continue
            else:
                ws = r
            if post is None:
                continue
            col = {'name': [], 'from': [], 'to': [], 'note': []}
            for w in ws:
                k = 'name' if w['x0'] < nx + 112 else 'from' if w['x0'] < nx + 165 else 'to' if w['x0'] < nx + 215 else 'note'
                col[k].append(w)
            if col['name']:
                post['name'] += [w['text'] for w in col['name']]
                if post['page'] == n:
                    post['words'] += col['name']
            for k in ('from', 'to', 'note'):
                if col[k]:
                    post[k].append(' '.join(w['text'] for w in col[k]))


def find_words(page_words: list[dict], given: str, last: str, after: float) -> list[dict]:
    """The name's words on the page, the first after the section's top."""
    folded = [k8.fold(w['text'].strip(',.')) for w in page_words]
    for i, w in enumerate(page_words):
        if w['top'] > after and folded[i] == k8.fold(last) and i and folded[i - 1] == k8.fold(given):
            return [page_words[i - 1], w]
        if w['top'] > after and folded[i] == k8.fold(given) and i + 1 < len(page_words) and folded[i + 1] == k8.fold(last):
            return [w, page_words[i + 1]]
    for i, w in enumerate(page_words):                                 # "Hadžisevdić Mustafa", "Zunac,"
        if w['top'] > after and folded[i] == k8.fold(last):
            return [w]
    raise ValueError(f'{given} {last} not on the page')


def read_typed(pdf) -> None:
    n = LAST_PAGE - FIRST_PAGE
    ws = [w for r in rows_of(viewer_words(pdf.pages[n - 1])) for w in r]
    top = next(w['top'] for w in ws if w['text'] == 'Karlovačke')
    for unit, duty, given, last, note in KARLOVACKA:
        POSTS.append({'unit': unit, 'unit_head': 'Štab Karlovačke brigade' + (unit.partition(',')[2] and f', {unit.partition(", ")[2]}'),
                      'duty': duty, 'name': [given, last], 'from': [], 'to': [], 'note': [note] if note else [],
                      'page': n, 'words': find_words(ws, given, last, top)})
    for unit, duty, given, last, frm, to, note in MUSLIMANSKA:
        page = n if last in ('Zalić', 'Ahmetović', 'Vascarac') else n + 1
        pws = ws if page == n else [w for r in rows_of(viewer_words(pdf.pages[page - 1])) for w in r]
        POSTS.append({'unit': unit, 'unit_head': 'Štab muslimanske brigade', 'duty': duty, 'name': [given, last],
                      'from': [frm] if frm else [], 'to': [to] if to else [], 'note': [note] if note else [],
                      'page': page, 'words': find_words(pws, given, PRINTED.get(last, last), top if page == n else 0)})


def extract(pdf_path: str, start_page: int, end_page: int | None) -> list[dict]:
    k8.corpus()
    with pdfplumber.open(pdf_path) as pdf:
        read_table(pdf)
        read_typed(pdf)
    for p in POSTS:
        finish(p)
    kept = [p for p in POSTS if (p['last'], p['given']) not in WENT_OVER]
    POSTS[:] = kept
    return [{'text': '§§post' + str(i), 'x': round(p['words'][0]['x0'], 1), 'y': round(p['words'][0]['top'], 1),
             'page': p['page']} for i, p in enumerate(POSTS)]


def parse(text: str) -> dict:
    p = POSTS[int(text[6:])]
    rec = _record(p['last'], p['given'], '', '')
    rec['_post'] = int(text[6:])
    return rec


def men(soldiers: list[dict]) -> list[dict]:
    out, seen = [], {}
    for s in soldiers:
        p = POSTS[s['_post']]
        key = (p['last'], p['given'])
        man = seen.get(key)
        if man is None:
            man = seen[key] = s
            s['_posts'], s['_nicks'], s['_rects'] = [], [], []
            s['unit_detail'] = p['unit']
            out.append(s)
        man['_posts'].append(p['text'])
        if p['nick'] and p['nick'] not in man['_nicks']:
            man['_nicks'].append(p['nick'])
        if p['page'] == man['pdf_page'] and p['words']:
            ws = p['words']
            man['_rects'].append([round(min(w['x0'] for w in ws), 1), round(min(w['top'] for w in ws), 1),
                                  round(max(w['x1'] for w in ws), 1), round(max(w['bottom'] for w in ws), 1)])
    for s in out:
        s['additional_info'] = '; '.join([f'zvani {n}' for n in s['_nicks']] + [f"{TITLE}: {'; '.join(s['_posts'])}."])
        r = s['_rects']
        s['pdf_x'], s['pdf_y'], s['pdf_x_end'], s['pdf_y_end'] = r[0]
        if len(r) > 1:
            s['pdf_rects'] = r
        s['full_name'] = f"{s['last_name']} {s['first_name']}"
        for k in ('_post', '_posts', '_nicks', '_rects'):
            s.pop(k)
    return out


if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    if not Path(PDF).exists():
        cut_pdf()
    run_parser(pdf_path=PDF, brigade_code=60, output_path=sys.argv[1] if len(sys.argv) > 1 else 'website/public/8-kordunaska-divizija-soldiers.json',
               extract_fn=extract, entry_start_re=re.compile(r'^§§'), parse_entry_fn=parse, post_fn=men,
               id_start=10001, keep_other_sources=True)
