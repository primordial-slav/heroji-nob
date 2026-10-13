"""
Parser: Mostarski bataljon (brigade code 125).

Source: Enver Ćemalović, "Mostarski bataljon" (znaci.org 00001/182), the chapter "Borci Mostarskog bataljona"
        (182_6.pdf → website/public/pdfs/mostarski-bataljon.pdf, book pp. 329-392), three lists of bios:
    "Borci Konjičkog bataljona (septembar 1941 — juni 1942)": the battalion was the Konjički bataljon until the
        conference on Tisovica of 21 June 1942 named it Mostarski, "što je u stvari bio od svog osnutka";
    "Borci Mostarskog bataljona (juni 1942 — juni 1943)", in the 10. hercegovačka brigada from late 1942;
    "Borci Mostarskog bataljona u Mostarskom partizanskom odredu (juni 1943 — maj 1944)".
Each man is printed once, in the list of the period he joined in (find_source_duplicates.py, with the lists in its
LISTS, finds no man in two). Before the lists, p. 2
names the battalions' fighters in the Spanish Civil War and their narodni heroji, names only: all of them have a bio
in the lists, so those two short lists are not read.
Two columns, Latin, each entry hanging (its first line some 26pt left of the lines under it), the given name first:
    ALEKSANDAR M. ALAGIĆ, rođen 1923, Gospić, đak, član SKOJ-a od 1940. i KPJ od 1942, u Bataljonu od oktobra 1941,
    komandir voda, poginuo na Borcima kod Konjica februara 1943;
    IBRAHIM IBRICA J. ALIKALFIĆ, ...   ALBERT L. ALTARAC ĆIN, ...   Inž. FAZLIJA I. ALIKALFIĆ, ...
The father's initial ("M.", "Dž.") stands before the surname; a nickname stands after the given name or after the
surname. The list's section goes to unit_detail.
"""
import re

import pdfplumber

from _parser_scaffold import _record, extract_lines_two_column, repair_lj_ocr, restore_diacritics, run_parser
from pdf_coords import viewer_offset

U, L = 'A-ZČĆŽŠĐ', 'a-zčćžšđ'
CAPS = rf'[{U}][{U}\-]*'
INITIAL = rf'(?:[{U}][{L}]?|Dž|Lj|Nj)\.'
SECTIONS = [('KONJIČKOG BATALJONA', 'Konjički bataljon (septembar 1941 — juni 1942)'),
            ('MOSTARSKOG BATALJONA U MOSTARSKOM', 'Mostarski bataljon u Mostarskom partizanskom odredu (juni 1943 — maj 1944)'),
            ('MOSTARSKOG BATALJONA', 'Mostarski bataljon (juni 1942 — juni 1943)')]
_left: dict = {}
COLUMN_SPLIT = 220      # the left column's lines start at x 99-155, the right column's at 290-330


def headings(pdf_path: str) -> list[tuple[int, float, float, str]]:
    """(page, top, bottom, section) of each list's heading, read across the full page width"""
    out = []
    with pdfplumber.open(pdf_path) as pdf:
        for n, page in enumerate(pdf.pages, 1):
            dx, dy = viewer_offset(page)
            lines = page.extract_text_lines(strip=True, return_chars=False)
            for i, ln in enumerate(lines):
                t = ' '.join(x['text'] for x in lines[i:i + 3])
                m = re.match(r'^BORCI (KONJIČKOG|MOSTARSKOG) (?:I MOSTARSKOG )?BATALJONA', ln['text'] + ' ' + (lines[i + 1]['text'] if i + 1 < len(lines) else ''))
                if not m or not ln['text'].startswith('BORCI'):
                    continue
                period = re.search(r'\((?:SEPTEMBAR|JUNI)[^)]*\)', t)
                section = next((s for key, s in SECTIONS if key in t.replace('\n', ' ')), None) if period else None
                end = next(x for x in lines[i:i + 4] if x['text'].startswith('(')) if period else lines[i + 1]
                out.append((n, ln['top'] - dy - 2, end['bottom'] - dy + 2, section))
    return out


def extract(pdf_path: str, start: int, end: int | None) -> list[dict]:
    heads = headings(pdf_path)
    lines = extract_lines_two_column(pdf_path, start, end, 'auto')
    out, section = [], None
    events = sorted(heads)
    # reading order is page, column, line; a heading across both columns starts a section in each column below it
    for page in sorted({l['page'] for l in lines}):
        page_heads = [h for h in events if h[0] == page]
        for col in (0, 1):
            for ln in [l for l in lines if l['page'] == page and (l['x'] > COLUMN_SPLIT) == bool(col)]:
                for h in page_heads:
                    if h[1] <= ln['y'] <= h[2]:
                        break
                else:
                    current = section
                    for h in page_heads:
                        if ln['y'] > h[2]:
                            current = h[3]
                    if current:
                        ln['section'] = current
                        out.append(ln)
                    continue
        # the section that runs on to the next page
        if page_heads:
            section = page_heads[-1][3]
    return out


def page_number(t: str) -> bool:
    return bool(re.fullmatch(r'[\d\W]{1,5}', t))


def measure(lines: list[dict]) -> None:
    for ln in lines:
        t = ln['text'].strip()
        if re.match(rf'^(?:Inž\.|dr|Dr)?\s*[{U}]{{2,}}', t) and not page_number(t):
            key = (ln['page'], ln['x'] > COLUMN_SPLIT)
            _left[key] = min(_left.get(key, 10 ** 6), ln['x'])


def keep(ln: dict) -> bool:
    t = ln['text'].strip()
    if page_number(t):
        return False
    if ln['page'] == 63 and ln['y'] > 345:
        return False                                     # the author's note under the last list ("Mada se dugo ...")
    if len(t) <= 2:
        return False                                     # a speck read as a letter ("I", p. 18)
    t = re.sub(r'^\.\s+(?=[A-ZČĆŽŠĐ]{2,})', '', t)                              # ". JUSUF A. JERKOVIĆ": a speck
    new = (ln['x'] < _left.get((ln['page'], ln['x'] > COLUMN_SPLIT), 0) + 12
           and bool(re.match(r'^(?:(?:Inž|dr|Dr)\.?\s+)?(?:[A-ZČĆŽŠĐ]{2,}|(?:\.\s?){3,}[A-ZČĆŽŠĐ])', t)))
    tag = {s: str(i) for i, (_, s) in enumerate(SECTIONS)}[ln['section']]
    ln['text'] = (f'§x§{tag}§ ' if new else '') + t
    return True


def parse_entry(text: str) -> dict:
    m = re.match(r'^§x§(\d)§\s*', text)
    section = SECTIONS[int(m.group(1))][1] if m else ''
    text = text[m.end():] if m else text
    # in the capitals the scan reads I as l or 1 ("ClSlĆ"), Ž as 2 ("HAD2IOMEROVIĆ")
    text = re.sub(rf'(?<=[{U}])[l1](?=[{U}])|(?<=[{U}])l(?=[{U}]?\b)', 'I', text)
    text = re.sub(rf'(?<=[{U}])2(?=[{U}])', 'Ž', text)
    text = re.sub(rf'([{U}]{{2,}})-([{U}]{{1,5}})\b', r'\1\2', text)        # "ALIKAL-FIĆ" broken over two lines
    # the name ends at its comma, or a semicolon or full stop the scan put there ("HASANBEGOVIČ. Rođena 1924")
    end = re.search(r'[,;]|\.(?=\s*[Rr]o-?\s?đen)|\s+(?=[Rr]o-?\s?đen)', text)
    head, info = (text[:end.start()], text[end.end():].strip()) if end else (text, '')
    info = re.sub(r'\s*\S*[¥®£ß]\S*', '', info)                              # a line the scan made into symbols
    words = head.split()
    title = ''
    if words and re.fullmatch(r'(?:Inž|inž|dr|Dr)\.?', words[0]):
        title = words.pop(0)
    nick = []
    if 'zvani' in words:                                                    # "MUHAMED zvani »PEGAMBER«"
        z = words.index('zvani')
        nick, words = [w.strip('»«') for w in words[z + 1:]], words[:z]
    # the initial in capitals ("LJ.", "DZ."), O read as 0, H as II
    words = [{'0.': 'O.', 'II.': 'H.', 'DZ.': 'Dž.', 'DŽ.': 'Dž.', 'LJ.': 'Lj.', 'NJ.': 'Nj.'}.get(w, w) for w in words]
    # dots for a name the book doesn't know: ". . . MONTILJO", "NEDA ...."
    dots = [i for i, w in enumerate(words) if re.fullmatch(r'\.+', w)]
    if dots:
        known = [w for w in words if not re.fullmatch(r'\.+', w)]
        given, last = ('', known[-1]) if dots[0] == 0 else (known[0], '…')
        father, rest = '', known[1:] if dots[0] else known[:-1]
        nick = nick + (rest if dots[0] else [])
        k = None
    else:
        k = next((i for i, w in enumerate(words) if re.fullmatch(INITIAL, w)), None)
    if dots:
        pass
    elif k is not None and k + 1 < len(words):
        given, nick, father = words[0], nick + words[1:k], words[k]
        last, nick = words[k + 1], nick + words[k + 2:]
    else:
        given, father = words[0] if words else '', ''
        last, nick = ((words[1], nick + words[2:]) if len(words) > 1 else ('…', nick))
    info = re.sub(r'^ro-?\s*đen', 'rođen', info).rstrip(' ;') + ';'
    info = info[:-1] + '.' if info.endswith(';') else info
    pre = []
    if nick:
        pre.append('zvani ' + ' '.join(nick).title())
    if title:
        pre.append(title.lower().rstrip('.') + '.')
    if pre:
        info = '; '.join(pre) + '; ' + info
    rec = _record(last, given, father, info)
    rec['unit_detail'] = section
    return rec


def post(soldiers: list[dict]) -> list[dict]:
    return repair_lj_ocr(restore_diacritics(soldiers))


if __name__ == '__main__':
    run_parser(
        pdf_path='website/public/pdfs/mostarski-bataljon.pdf',
        brigade_code=125,
        output_path='website/public/mostarski-bataljon-soldiers.json',
        start_page=2,
        end_page=63,
        extract_fn=extract,
        script='latin',
        entry_start_re=re.compile(r'^§x§'),
        parse_entry_fn=parse_entry,
        line_filter=keep,
        prepare_fn=measure,
        post_fn=post,
    )
